import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import hashlib
import sys
ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
entry=load('vision_entry','entrypoint.py')
vision=load('prepare_vision','prepare-vision.py')
bundle=load('vision_bundle','prepare-bundle.py')
scrub=load('vision_scrub','check-scrub.py')

class VisionRecipeTests(unittest.TestCase):
    def test_production_lineage(self):
        lock=json.loads((ROOT/'sources.lock.json').read_text())
        self.assertEqual(lock['engine_commit'],lock['frontend_commit'])
        self.assertTrue(lock['engine_commit'].startswith('b7c3eb5'))
    def test_vision_default_on_rank_zero_only(self):
        self.assertEqual([len(entry.command_plan(i,'fleet','listener','spill')) for i in range(4)],[3,1,1,1])
    def test_encoder_model_layout(self):
        c=entry.command_plan(0,'fleet','listener','spill')[0]
        self.assertIn('/opt/package/vision/vision_encoder.py',c)
        self.assertEqual(c[c.index('--model')+1],'/opt/package/vision')
    def test_frontend_opt_in(self):
        c=entry.command_plan(0,'fleet','listener','spill')[-1]
        self.assertEqual(c[c.index('--vision-addr')+1],'127.0.0.1:18950')
    def test_no_image_flag_preserves_text_commands(self):
        c=entry.command_plan(0,'fleet','listener','spill',vision=False)
        v=entry.command_plan(0,'fleet','listener','spill')
        self.assertEqual(c[0],v[1])
        self.assertEqual(c[1],v[2][:-2])
    def test_streaming_hash_header_reader(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'pack'
            h=json.dumps({'tensor':{'dtype':'BF16','shape':[1],'data_offsets':[0,2]}}).encode()
            p.write_bytes(struct.pack('<Q',len(h))+h+b'xx')
            self.assertEqual(vision.header(p),(h,json.loads(h)))
    def test_header_allocation_bound(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad';p.write_bytes(struct.pack('<Q',2**40))
            with self.assertRaises(ValueError):vision.header(p)
    def test_truncated_header(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad';p.write_bytes(struct.pack('<Q',20)+b'{}')
            with self.assertRaises(ValueError):vision.header(p)
    def test_missing_native_tensors(self):
        with self.assertRaises(ValueError):vision.inventory(Path('.'),{'weight_map':{}})
    def test_runtime_is_digest_pinned(self):
        docker=(ROOT/'Dockerfile').read_text()
        self.assertIn(json.loads((ROOT/'sources.lock.json').read_text())['production_manifest_digest'],docker)
    def test_current_benchmarks_cite_current_evidence(self):
        text=(ROOT/'docs/benchmarks.md').read_text()
        for value in ('8,951','9,259','9,076','8,598','88.772','retrial-spark-only/REPORT.md'):
            self.assertIn(value,text)
    def test_pack_guard_is_production_sha(self):
        lock=json.loads((ROOT/'sources.lock.json').read_text())
        self.assertEqual(lock['vision_pack_sha256'],'b07abf470c4107ba3029fedb9de1fd8823a40041f99d0d278e536b06ed5bb446')


    def test_symlinked_parent_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);actual=root/'actual';actual.mkdir()
            (actual/'asset').write_bytes(b'fixture')
            (root/'linked').symlink_to(actual,target_is_directory=True)
            with self.assertRaises(ValueError):
                bundle.checked(root/'linked/asset',hashlib.sha256(b'fixture').hexdigest())
    def test_scrub_tailnet(self):
        self.assertIn('tailnet-domain',scrub.problems('machine.example.'+'ts'+'.net'))
    def test_scrub_credential_path(self):
        self.assertIn('credential-path',scrub.problems('/run/'+'secrets/example'))
    def test_negative_pack_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'pack';p.write_bytes(b'fixture')
            with self.assertRaises(ValueError):bundle.checked(p,'0'*64)

class BundleIntegrationTests(unittest.TestCase):
    def fixture(self,root):
        # Tiny non-model file fixtures for packaging/schema tests only.
        b=root/'bundle'
        def put(name):
            p=b/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'packaging-fixture')
            return hashlib.sha256(p.read_bytes()).hexdigest()
        engine=put('bin/dsgb10_rank');front=put('bin/dsfront');put('notices/engine-NOTICE')
        model_names=['config.json','tokenizer.json','engram_hashmap.bin']
        model_names += ['rank%d.dsw'%i for i in range(4)]
        model_names += ['engram-l%d-r%dof4.bin'%(l,i) for i in range(4) for l in (1,14)]
        mh={n:put('model/'+n) for n in model_names}
        vn=['vision.safetensors','config.json','model.safetensors.index.json','inference/vision.py','inference/image_processor.py','vision_encoder.py','image_io.py']
        vh={n:put('vision/'+n) for n in vn}
        lock=dict(engine_commit='engine-fixture',frontend_commit='engine-fixture',model_repository='model-fixture',
                  model_revision='revision-fixture',engine_binary_sha256=engine,frontend_binary_sha256=front,
                  vision_pack_sha256=vh['vision.safetensors'],optional_glp39_sha256='0'*64)
        (root/'sources.lock.json').write_text(json.dumps(lock))
        common=dict(model=lock['model_repository'],revision=lock['model_revision'],engine_commit=lock['engine_commit'])
        (b/'model/asset-hashes.json').write_text(json.dumps(dict(common,all_conversion_commands_exit_zero=True,sha256=mh)))
        (b/'vision/asset-hashes.json').write_text(json.dumps(dict(common,pack_sha256=lock['vision_pack_sha256'],sha256=vh)))
        return b
    def run_validator(self,root,b):
        with patch.object(bundle,'ROOT',root),patch.object(sys,'argv',['prepare-bundle','--bundle',str(b)]):
            bundle.main()
    def test_complete_bundle_writes_off_profile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);self.run_validator(root,b)
            profile=json.loads((b/'profile.json').read_text())
            self.assertEqual(profile['steering_default'],'off')
            self.assertIsNone(profile['glp39_sha256'])
            self.assertEqual(len(profile['vision_files_sha256']),7)
    def test_changed_vision_runtime_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root)
            (b/'vision/image_io.py').write_bytes(b'altered fixture')
            with self.assertRaises(ValueError):self.run_validator(root,b)
            self.assertFalse((b/'profile.json').exists())
    def test_incomplete_vision_receipt_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);p=b/'vision/asset-hashes.json'
            x=json.loads(p.read_text());del x['sha256']['inference/vision.py'];p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):self.run_validator(root,b)
    def test_wrong_vision_provenance_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);p=b/'vision/asset-hashes.json'
            x=json.loads(p.read_text());x['revision']='wrong-fixture';p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):self.run_validator(root,b)
    def test_vision_path_escape_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);p=b/'vision/asset-hashes.json'
            x=json.loads(p.read_text());x['sha256']['../escape']='0'*64;p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):self.run_validator(root,b)
    def test_wrong_binary_fails_before_profile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);(b/'bin/dsgb10_rank').write_bytes(b'wrong fixture')
            with self.assertRaises(ValueError):self.run_validator(root,b)
    def test_verified_old_conversion_lineage_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);p=b/'model/asset-hashes.json'
            x=json.loads(p.read_text());x['engine_commit']='original-converter-fixture'
            x['verification_engine_commit']='engine-fixture';p.write_text(json.dumps(x))
            self.run_validator(root,b)
    def test_wrong_text_verifier_commit_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);p=b/'model/asset-hashes.json'
            x=json.loads(p.read_text());x['verification_engine_commit']='wrong-fixture';p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):self.run_validator(root,b)
    def test_incomplete_text_conversion_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=self.fixture(root);p=b/'model/asset-hashes.json'
            x=json.loads(p.read_text());x['all_conversion_commands_exit_zero']=False;p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):self.run_validator(root,b)

if __name__=='__main__':unittest.main()
