import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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
    def test_default_is_glp39(self):
        self.assertEqual(json.loads((ROOT/'sources.lock.json').read_text())['public_steering_default'],'glp39')
    def launch(self, rank, flags=(), check_side_effect=None):
        profile=json.dumps(dict(engine_sha256='engine',frontend_sha256='frontend',
                                glp39_sha256='vector'))
        argv=['entrypoint','--rank',str(rank),'--fleet','fleet.conf','--no-vision',*flags]
        with patch('sys.argv',argv), patch.object(entry.Path,'read_text',return_value=profile), \
             patch.object(entry.Path,'is_file',return_value=True), patch.object(entry.Path,'mkdir'), \
             patch.object(entry,'check',side_effect=check_side_effect) as checked, \
             patch.object(entry,'supervise',return_value=0) as run:
            self.assertEqual(entry.main(),0)
        return checked,run
    def test_omitted_flag_enables_glp39_on_every_rank(self):
        for rank in range(4):
            with self.subTest(rank=rank):
                checked,run=self.launch(rank)
                checked.assert_any_call('/opt/package/vectors/glp39.gguf','vector')
                env=run.call_args.args[1]
                self.assertEqual(env['WEIGHTLESS_STEER_PATH'],'/opt/package/vectors/glp39.gguf')
                self.assertEqual(env['WEIGHTLESS_STEER_ALPHA'],'0.75')
                self.assertEqual(env['WEIGHTLESS_STEER_LAYERS'],','.join(map(str,range(1,40))))
    def test_explicit_off_skips_vector_and_clears_inherited_environment(self):
        with patch.dict(entry.os.environ,{key:'inherited' for key in entry.STEER_VARS}):
            for rank in range(4):
                checked,run=self.launch(rank,('--steering','off'))
                self.assertEqual(checked.call_count,2)
                self.assertFalse(set(entry.STEER_VARS)&run.call_args.args[1].keys())
    def test_default_refuses_missing_or_invalid_vector(self):
        for failure in (FileNotFoundError('Vector absent'),ValueError('Artifact hash mismatch')):
            def verify(path, expected):
                if path.endswith('glp39.gguf'):raise failure
            with self.subTest(failure=type(failure).__name__), self.assertRaises(type(failure)):
                self.launch(0,check_side_effect=verify)
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
        self.assertEqual([len(entry.command_plan(i,'fleet.conf','listener','spill',vision=False)) for i in range(4)],[2,1,1,1])
    def test_all_ranks_use_own_assets(self):
        for i in range(4):
            command=entry.command_plan(i,'fleet.conf','listener','spill',vision=False)[0]
            self.assertIn(f'/opt/package/model/rank{i}.dsw',command)
            self.assertIn(f'/opt/package/model/engram-l14-r{i}of4.bin',command)
    def test_rank_rejected(self):
        with self.assertRaises(ValueError):entry.command_plan(4,'fleet.conf','listener','spill')
    def test_frozen_settings(self):
        c=entry.command_plan(0,'fleet.conf','listener','spill',vision=False)[0]
        for flag,value in [('--max-ctx','1048576'),('--slots','16'),('--session-gib','3'),('--disk-gib','160')]:
            self.assertEqual(c[c.index(flag)+1],value)
    def test_production_frontend_defaults(self):
        c=entry.command_plan(0,'fleet.conf','listener','spill',vision=False)[1]
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
