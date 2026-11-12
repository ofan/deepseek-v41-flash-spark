"""Offline packaging safety tests; no GPU/serving/release qualification claim."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/name)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pack=load('assemble-runtime.py');audit=load('audit-runtime.py');bundle=load('prepare-bundle.py');notice=load('add-dependency-notice.py')

class PublicationTests(unittest.TestCase):
    def test_only_curated_app_members_survive(self):
        for p in ('opt/pico/profile.json','opt/pico/entrypoint.py','opt/spark-ds41f/candidate/vllm/scripts/serve.sh','root/.cache/pip/data','home/operator/trial','tmp/data','usr/local/lib/python3.12/dist-packages/vllm/model.py'):
            self.assertFalse(pack.selected(p),p)
        self.assertTrue(pack.selected('opt/pico/dsfront'))
        self.assertTrue(pack.selected('opt/pico/vision/vision.safetensors'))
    def test_remove_caches_tests_and_static_dev_files(self):
        for p in ('usr/lib/python3.12/test/test.py','usr/lib/python3.12/__pycache__/a.pyc',pack.PACKAGE+'torch/include/a.h',pack.PACKAGE+'torch/test/a.py',pack.PACKAGE+'torch/direct_url.json','usr/local/cuda-13.0/targets/sbsa-linux/lib/lib.a'):
            self.assertFalse(pack.selected(p),p)
    def test_retain_runtime_packages_and_notices(self):
        for p in (pack.PACKAGE+'torch/lib/libtorch.so',pack.PACKAGE+'nvidia/cu13/lib/libcudnn.so',pack.PACKAGE+'torch-2.13.dist-info/licenses/LICENSE','usr/share/doc/libc6/copyright'):
            self.assertTrue(pack.selected(p),p)
    def test_path_traversal_and_absolute_refused(self):
        for n in ('../outside','usr/../../outside','/etc/passwd'):
            with self.assertRaises(ValueError):pack.name_safe(n)
    def staged(self, layers, root):
        cache=root/'cache';cache.mkdir();out=root/'out';out.mkdir();manifest={'layers':[]}
        for members in layers:
            b=io.BytesIO()
            with tarfile.open(fileobj=b,mode='w:gz') as tf:
                for name,kind,value in members:
                    t=tarfile.TarInfo(name);t.mode=0o755
                    if kind=='file':t.size=len(value);tf.addfile(t,io.BytesIO(value))
                    else:t.type={'dir':tarfile.DIRTYPE,'symlink':tarfile.SYMTYPE,'link':tarfile.LNKTYPE}[kind];t.linkname=value;tf.addfile(t)
            raw=b.getvalue();d=hashlib.sha256(raw).hexdigest();(cache/d).write_bytes(raw)
            manifest['layers'].append({'digest':'sha256:'+d,'size':len(raw)})
        return pack.stage(manifest,cache,out),out
    def test_latest_version_not_historical_bytes(self):
        n='usr/bin/python3.12'
        with tempfile.TemporaryDirectory() as d:
            (state,r),out=self.staged([[(n,'file',b'old')],[(n,'file',b'new')]],Path(d))
            self.assertEqual(Path(state[n]['payload']).read_bytes(),b'new')
            self.assertFalse((out/n).exists())
    def test_whiteout_removes_member(self):
        with tempfile.TemporaryDirectory() as d:
            (state,r),_=self.staged([[('usr/bin/python3.12','file',b'x')],[('usr/bin/.wh.python3.12','file',b'')]],Path(d))
            self.assertFalse(state)
    def test_opaque_directory_removes_inherited_children_only(self):
        n='usr/lib/python3.12'
        with tempfile.TemporaryDirectory() as d:
            (state,r),_=self.staged([[(n+'/old.py','file',b'x')],[(n+'/.wh..wh..opq','file',b''),(n+'/new.py','file',b'y')]],Path(d))
            self.assertNotIn(n+'/old.py',state);self.assertIn(n+'/new.py',state)
    def test_escaping_symlink_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):self.staged([[('usr/bin/python3.12','symlink','../../../../outside')]],Path(d))
    def test_unresolved_hardlink_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):self.staged([[('usr/bin/python3.12','link','unselected/path')]],Path(d))
    def test_archive_path_cannot_write_through_symlink(self):
        n=pack.PACKAGE+'torch'
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):self.staged([[(n,'symlink','python3.11'),(n+'/x.py','file',b'x')]],Path(d))
            self.assertFalse((Path(d)/'out'/n).exists())
    def test_scan_binary_not_only_small_text(self):
        b=b'\x7fELF\0'+('/ho'+'me/operator/build').encode()
        self.assertIn('home-path',[h['kind'] for h in audit.scan(b)])
    def test_tensor_contents_remain_opaque(self):
        self.assertTrue(audit.OPAQUE.search('opt/package/vision/vision.safetensors'))
        self.assertFalse(audit.OPAQUE.search('opt/package/bin/dsgb10_rank'))
    def test_corrupted_source_blob_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'out').mkdir();(root/'cache').mkdir()
            (root/'cache'/('0'*64)).write_bytes(b'corrupt')
            with self.assertRaises(ValueError):pack.stage({'layers':[{'digest':'sha256:'+'0'*64,'size':7}]},root/'cache',root/'out')
    def test_blocked_runtime_refused_before_assets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'sources.lock.json').write_text('{}')
            r=root/'runtime.json';r.write_text(json.dumps({'privacy_verdict':'BLOCKED','unresolved_findings':1,'inherited_source_layers':0}))
            with patch.object(bundle,'ROOT',root),patch.object(sys,'argv',['prepare','--publication-runtime',str(r)]):
                with self.assertRaisesRegex(ValueError,'privacy gate'):bundle.main()
    def test_runtime_source_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'sources.lock.json').write_text(json.dumps({'engine_commit':'pinned'}))
            r=root/'runtime.json';r.write_text(json.dumps({'privacy_verdict':'CLEAN','unresolved_findings':0,'inherited_source_layers':0,'source_engine_commit':'other'}))
            with patch.object(bundle,'ROOT',root),patch.object(sys,'argv',['prepare','--publication-runtime',str(r)]):
                with self.assertRaisesRegex(ValueError,'source mismatch'):bundle.main()
    def test_supplement_not_usable_to_hide_old_layers(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);blobs=root/'blobs/sha256';blobs.mkdir(parents=True)
            raw=json.dumps({'layers':[{},{}]}).encode();h=hashlib.sha256(raw).hexdigest();(blobs/h).write_bytes(raw)
            (root/'index.json').write_text(json.dumps({'manifests':[{'digest':'sha256:'+h}]}))
            with self.assertRaisesRegex(AssertionError,'fresh single-layer'):notice.add(root,b'license','candidate')

    def test_candidate_receipts_agree_with_owner_waiver(self):
        r=json.loads((ROOT/'docs/publication-runtime.json').read_text())
        a=json.loads((ROOT/'docs/publication-audit.json').read_text())
        t=json.loads((ROOT/'docs/publication-transfer.json').read_text())
        self.assertEqual(r['manifest_digest'],a['manifest_digest'])
        self.assertEqual(r['manifest_digest'],t['manifest_digest'])
        self.assertEqual(r['config_digest'],a['config_digest'])
        self.assertEqual(r['privacy_verdict'],'CLEAN')
        self.assertTrue(r['publication_allowed'])
        self.assertFalse(r['visibility_changed'])
        self.assertEqual(r['unresolved_findings'],a['unresolved_file_count'])
        self.assertEqual(r['unresolved_findings'],0)
        self.assertEqual(r['waived_findings'],11)
        self.assertEqual(a['verdict'],'CLEARED_WITH_OWNER_WAIVERS')
        self.assertEqual(len(a['config_findings']),0)
        self.assertTrue(t['manifest_tag_and_digest_get_verified'])
        self.assertTrue(t['config_get_hash_verified'])
        self.assertTrue(t['all_blob_heads_verified'])
        self.assertEqual(t['package_visibility'],'private')
        self.assertTrue(t['repository_private'])

    def test_every_screening_file_has_one_adjudication(self):
        a=json.loads((ROOT/'docs/publication-audit.json').read_text())
        files={(l['digest'],f['path']) for l in a['layers'] for f in l['findings']}
        reviews=a['adjudications']
        self.assertEqual(len(reviews),len(files))
        self.assertEqual({(x['layer_digest'],x['path']) for x in reviews},files)
        self.assertEqual(sum(x['disposition']=='WAIVED' for x in reviews),11)
        self.assertEqual(sum(x['disposition']=='REVIEW' for x in reviews),0)
        for row in reviews:
            if row['disposition']=='WAIVED':
                self.assertEqual(row['original_disposition'],'REVIEW')
                self.assertEqual(row['waiver']['authorized_by'],'Ryan')
                self.assertEqual(row['waiver']['authorized_at'],'2026-11-11T23:58:00-05:00')
        self.assertEqual(sum(x['disposition']=='BENIGN_PATTERN' for x in reviews),31)

    def test_fresh_layers_match_transfer_and_runtime_receipts(self):
        r=json.loads((ROOT/'docs/publication-runtime.json').read_text())
        a=json.loads((ROOT/'docs/publication-audit.json').read_text())
        t=json.loads((ROOT/'docs/publication-transfer.json').read_text())
        self.assertEqual(r['inherited_source_layers'],0)
        layers={l['digest'] for l in a['layers']}
        self.assertEqual(layers,{r['core_layer'],r['supplement_layer']})
        self.assertEqual(len(layers),r['layer_count'])
        self.assertEqual(layers,{b['digest'] for b in t['blobs'] if b['digest']!=r['config_digest']})
        self.assertEqual(sum(b['size'] for b in t['blobs'] if b['digest'] in layers),r['compressed_layer_bytes'])

    def test_shared_package_visibility_does_not_expose_original(self):
        v=json.loads((ROOT/'docs/publication-visibility.json').read_text())
        self.assertEqual(v['package_visibility'],'private')
        self.assertTrue(v['repository_private'])
        self.assertEqual(v['distribution_verdict'],'BLOCKED_SHARED_PACKAGE_VISIBILITY')
        self.assertFalse(v['visibility_changed'])
        self.assertFalse(v['production_touched'])
        r=json.loads((ROOT/'docs/publication-runtime.json').read_text())
        for key,expected in [('candidate',r['manifest_digest']),('production_mirror',r['original_production_manifest_digest'])]:
            row=v['tags'][key]
            self.assertEqual(row['owner_manifest_get_status'],200)
            self.assertEqual(row['manifest_digest'],expected)
            self.assertTrue(row['anonymous_access_denied'])
        q=json.loads((ROOT/'docs/publication-verification.json').read_text())
        self.assertFalse(q['runtime_smoke']['publication_blocker'])
        self.assertFalse(q['gpu_acceptance_performed'])

    def test_no_retained_history_or_base_layer(self):
        text=(ROOT/'scripts/assemble-runtime.py').read_text()
        self.assertIn("source_inherited_layers=0",text)
        self.assertIn("'history':[{'created':STAMP",text)
        self.assertIn("steering_default='off'",(ROOT/'scripts/prepare-bundle.py').read_text())

if __name__=='__main__':unittest.main()
