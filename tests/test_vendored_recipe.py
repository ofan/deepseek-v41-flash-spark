"""Local source, replay, safe disclosure and fresh-measurement provenance checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(filename):
    spec=importlib.util.spec_from_file_location(filename,ROOT/'scripts'/filename)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
source=load('source_tree.py');replay=load('verify-patches.py');scrub=load('check-scrub.py');bundle=load('prepare-bundle.py')
class VendoredRecipeTests(unittest.TestCase):
    def test_complete_source_inventory(self):
        self.assertEqual(source.verify_source(ROOT/'vendor/engine'),json.loads((ROOT/'sources.lock.json').read_text())['engine_commit'])
    def test_replay_all_changes(self):
        self.assertEqual(replay.verify(),(5,265))
    def test_separate_four_features_and_prerequisite(self):
        s=(ROOT/'patches/series').read_text().splitlines()
        self.assertEqual(len(s),5)
        for tag,name in zip(['cache-fidelity','glp-steering','dsml-parser','sampler-clamp','native-vision'],s):self.assertIn(tag,name)
    def test_cmake_fleet_dependency_included(self):
        for name in ['engine','upstream']:
            template=ROOT/'vendor'/name/'ds41f-4xgx10-switchless/fleet/homelab.conf'
            self.assertEqual(template.read_bytes(),(ROOT/'examples/fleet.conf.example').read_bytes())
            self.assertIn('REPLACE_',template.read_text())
    def test_tampered_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tree';shutil.copytree(ROOT/'vendor/engine',p)
            (p/'LICENSE').write_text('altered fixture')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):source.verify_source(p)
    def test_tampered_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tree';shutil.copytree(ROOT/'vendor/engine',p)
            m=p/'SOURCE.json';j=json.loads(m.read_text());j['source_commit']='other';m.write_text(json.dumps(j))
            with self.assertRaisesRegex(ValueError,'manifest differs'):source.verify_source(p)
    def test_added_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tree';shutil.copytree(ROOT/'vendor/engine',p);(p/'added').write_text('fixture')
            with self.assertRaisesRegex(ValueError,'unexpected'):source.verify_source(p)
    def test_executable_mode_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tree';shutil.copytree(ROOT/'vendor/engine',p);(p/'LICENSE').chmod(0o755)
            with self.assertRaisesRegex(ValueError,'mode mismatch'):source.verify_source(p)
    def test_staging_local_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,str(ROOT/'scripts/source_tree.py'),'--stage',d+'/source'],capture_output=True)
            self.assertEqual(p.returncode,0)
            for name in ['engine','frontend']:source.verify_source(Path(d)/'source'/name)
        text=(ROOT/'scripts/fetch-sources.sh').read_text()
        self.assertNotIn('git clone',text);self.assertIn('source_tree.py',text)
    def test_protocol_exception_does_not_hide_operator_disclosure(self):
        protocol='<'+'|'+'fixture'+'|'+'>'
        self.assertEqual(scrub.problems(protocol,allow_protocol=True),[])
        self.assertIn('special-token-string',scrub.problems(protocol))
        checks=[('internal-domain','test.'+'lab'+'.tf'),('personal-home-path','/ho'+'me/example/x'),
                ('access-secret','gh'+'p_'+'a'*25),('nonpublishable-network-address','.'.join(map(str,[10,1,2,3])))]
        for category,value in checks:self.assertIn(category,scrub.problems(protocol+value,allow_protocol=True))
    def test_extended_secret_and_network_scrub(self):
        for category,text in [('cloud-credential-path','.a'+'ws/credentials'),('cloud-access-secret','A'+'KIA'+'A'*16),('private-ipv6','fd'+'00:1234::1')]:
            self.assertIn(category,scrub.problems(text,allow_protocol=True))
        self.assertNotIn('cloud-credential-path',scrub.problems(r'\.a'+'ws/(?:credentials|config)'))
    def test_builders_use_local_source(self):
        for name in ['build-engine.sh','rebuild-publication-engine.sh']:
            s=(ROOT/'scripts'/name).read_text();self.assertIn('source_tree.py',s);self.assertNotIn('git -C',s)
    def test_benchmark_matrix_and_cap(self):
        r=json.loads((ROOT/'docs/benchmarks/2026-11-13-decode.json').read_text())
        rows=r['configurations'];self.assertEqual(len(rows),8)
        self.assertEqual({(x['prompt_type'],x['summary']['streams']) for x in rows},{(k,n) for k in ('prose','code') for n in (1,4,8,16)})
        self.assertEqual(sum(len(x['requests']) for x in rows),58)
        self.assertTrue(all(not v['error'] and v['tokens']==256 for x in rows for v in x['requests']))
        cap=json.loads((ROOT/'docs/benchmarks/2026-11-13-gpu-cap.json').read_text())
        self.assertEqual(len(cap['nodes']),4)
        for n in cap['nodes']:
            self.assertEqual(n['configured_graphics_clock_cap_mhz'],2200);self.assertTrue(n['cap_unit_active'])
            self.assertEqual(n['restarts'],0);self.assertFalse(n['oom_killed'])
    def test_prompt_hashes_match_included_builtins(self):
        sys.path.insert(0,str(ROOT/'vendor/engine/ds41f-4xgx10-switchless/bench'))
        import bench
        r=json.loads((ROOT/'docs/benchmarks/2026-11-13-decode.json').read_text())
        for kind in ('prose','code'):self.assertEqual(hashlib.sha256(bench.DECODE_PROMPTS[kind].encode()).hexdigest(),r['prompt_sha256'][kind])
    def test_independent_sanitization_inventory(self):
        d=json.loads((ROOT/'vendor/sanitization.json').read_text());self.assertEqual(d['files_changed'],len(d['changes']))
        self.assertGreater(d['files_changed'],0)
    def test_qualification_and_latency_not_hidden(self):
        s=(ROOT/'README.md').read_text()
        for text in ['qualification is pending','21.9','2,200 MHz','N/A','Stock fidelity','88 of 88','token for token']:self.assertIn(text,s)

class SourceBuildReceiptTests(unittest.TestCase):
    def fixture(self,root):
        # Reuse complete small synthetic bundles, never actual model tensors.
        from test_vision_recipe import BundleIntegrationTests
        b=BundleIntegrationTests().fixture(root)
        v=root/'vendor/engine';v.mkdir(parents=True);(v/'SOURCE.json').write_text('{}')
        (b/'bin/dsgb10_rank').write_bytes(b'local-source-fixture')
        hashes={k:hashlib.sha256((b/'bin'/n).read_bytes()).hexdigest() for k,n in [('engine_binary_sha256','dsgb10_rank'),('frontend_binary_sha256','dsfront')]}
        receipt=root/'build.json';receipt.write_text(json.dumps(dict(source_commit='engine-fixture',source_manifest_sha256=hashlib.sha256(b'{}').hexdigest(),**hashes)))
        return b,receipt
    def run_it(self,root,b,r):
        with patch.object(bundle,'ROOT',root),patch.object(sys,'argv',['prepare','--bundle',str(b),'--source-build-receipt',str(r)]):bundle.main()
    def test_valid_local_receipt_labels_unqualified(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b,r=self.fixture(root);self.run_it(root,b,r)
            p=json.loads((b/'profile.json').read_text());self.assertIn('LOCAL SOURCE BUILD',p['qualification']);self.assertEqual(p['steering_default'],'off')
    def test_wrong_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b,r=self.fixture(root);j=json.loads(r.read_text());j['source_manifest_sha256']='0'*64;r.write_text(json.dumps(j))
            with self.assertRaisesRegex(ValueError,'incorrect provenance'):self.run_it(root,b,r)
            self.assertFalse((b/'profile.json').exists())
    def test_wrong_local_binary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b,r=self.fixture(root);(b/'bin/dsgb10_rank').write_bytes(b'not-receipted')
            with self.assertRaisesRegex(ValueError,'hash-mismatched'):self.run_it(root,b,r)
if __name__=='__main__':unittest.main()
