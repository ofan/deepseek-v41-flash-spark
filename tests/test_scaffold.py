import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

entry=load('entry','entrypoint.py')
scrub=load('scrub','check-scrub.py')
bundle=load('bundle','prepare-bundle.py')

class ScaffoldTests(unittest.TestCase):
    def test_default_is_off(self):
        self.assertEqual(json.loads((ROOT/'sources.lock.json').read_text())['public_steering_default'],'off')
    def test_off_clears_inherited_steering(self):
        env={key:'inherited' for key in entry.STEER_VARS}
        self.assertFalse(set(entry.STEER_VARS)&entry.steering_environment(env,'off').keys())
    def test_off_preserves_unrelated_environment(self):
        self.assertEqual(entry.steering_environment({'CONTROL':'unchanged'},'off'),{'CONTROL':'unchanged'})
    def test_no_lossy_shortcut(self):
        self.assertNotIn('DSGB10_OEA',entry.steering_environment({'DSGB10_OEA':'1'},'off'))
    def test_on_alpha(self):
        self.assertEqual(entry.steering_environment({},'glp39')['WEIGHTLESS_STEER_ALPHA'],'0.75')
    def test_on_layers(self):
        self.assertEqual(entry.steering_environment({},'glp39')['WEIGHTLESS_STEER_LAYERS'],','.join(map(str,range(1,40))))
    def test_unknown_mode_refused(self):
        with self.assertRaises(ValueError):entry.steering_environment({},'unknown')
    def test_frontend_only_on_rank_zero(self):
        self.assertEqual([len(entry.command_plan(i,'fleet.conf','listener','spill')) for i in range(4)],[2,1,1,1])
    def test_all_ranks_use_own_assets(self):
        for i in range(4):
            command=entry.command_plan(i,'fleet.conf','listener','spill')[0]
            self.assertIn(f'/opt/package/model/rank{i}.dsw',command)
            self.assertIn(f'/opt/package/model/engram-l14-r{i}of4.bin',command)
    def test_rank_rejected(self):
        with self.assertRaises(ValueError):entry.command_plan(4,'fleet.conf','listener','spill')
    def test_frozen_settings(self):
        c=entry.command_plan(0,'fleet.conf','listener','spill')[0]
        for flag,value in [('--max-ctx','1048576'),('--slots','16'),('--session-gib','3'),('--disk-gib','160')]:
            self.assertEqual(c[c.index(flag)+1],value)
    def test_production_frontend_defaults(self):
        c=entry.command_plan(0,'fleet.conf','listener','spill')[1]
        for flag,value in [('--encoding','1017'),('--temperature','1'),('--top-p','1'),('--session-cache-tokens','160000000')]:
            self.assertEqual(c[c.index(flag)+1],value)
    def test_artifact_hash_success(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'artifact';p.write_bytes(b'fixture')
            bundle.checked(p,hashlib.sha256(b'fixture').hexdigest())
    def test_artifact_hash_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'artifact';p.write_bytes(b'fixture')
            with self.assertRaises(ValueError):bundle.checked(p,'0'*64)
    def test_artifact_symlink_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'artifact';p.write_bytes(b'fixture')
            q=Path(d)/'link';q.symlink_to(p)
            with self.assertRaises(ValueError):bundle.checked(q,hashlib.sha256(b'fixture').hexdigest())
    def test_scrub_detects_secret_shape(self):
        self.assertIn('access-secret',scrub.problems('gh'+'p_'+'a'*25))
    def test_scrub_detects_nonpublic_address(self):
        address='.'.join(map(str,[192,168,4,8]))
        self.assertIn('nonpublishable-network-address',scrub.problems(address))
    def test_required_documents(self):
        for name in ['README.md','LICENSE','NOTICE','Dockerfile','docs/benchmarks.md','docs/setup-spark.md','docs/steering.md','docs/build.md','docs/scaffold-report.md']:
            self.assertTrue((ROOT/name).is_file(),name)

if __name__=='__main__':
    unittest.main()
