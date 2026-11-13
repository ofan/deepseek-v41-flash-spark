"""Outside-user instructions and distribution safety; no network or GPU assertions."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
PUBLIC='ghcr.io/ofan/deepseek-v41-flash-spark-public'
DIGEST='sha256:bc042a4b33f56d8cbfcfac6f642f3ecf1f59c42ee7a9c26fed81fdfbae3bc979'
def read(name):return (ROOT/name).read_text()
def data(name):return json.loads(read(name))
spec=importlib.util.spec_from_file_location('release_scrub',ROOT/'scripts/check-scrub.py')
scrub=importlib.util.module_from_spec(spec);spec.loader.exec_module(scrub)
class PublicReleaseTests(unittest.TestCase):
    def test_runtime_matches_distribution_copy(self):
        r=data('docs/publication-runtime.json');p=data('docs/public-release.json')
        self.assertEqual(r['image'],p['image'])
        self.assertEqual(r['manifest_digest'],p['manifest_digest'])
        self.assertEqual(r['manifest_digest'],DIGEST)
        self.assertTrue(r['image'].startswith(PUBLIC+':'))
    def test_original_package_untouched_and_private(self):
        p=data('docs/public-release.json')
        old=p['anonymous_checks']['protected_predecessor']
        self.assertEqual(old['package_id'],16805256)
        self.assertEqual(old['visibility'],'private')
        self.assertFalse(old['anonymous_manifest_fetchable'])
        self.assertFalse(p['protected_original_package_modified'])
        self.assertFalse(p['production_touched'])
    def test_publication_verified_without_new_visibility_change(self):
        p=data('docs/public-release.json')
        self.assertEqual(p['public_release_verdict'],'PUBLIC_ANONYMOUS_READBACK_VERIFIED')
        self.assertFalse(p['repository']['private'])
        self.assertFalse(p['visibility_changed_this_update'])
        self.assertTrue(p['anonymous_checks']['candidate']['anonymous_manifest_fetchable'])
        self.assertEqual(p['anonymous_https_clone_exit_code'],0)
        self.assertNotIn('Publication is currently held',read('README.md'))
    def test_every_doc_image_url_is_distribution_only(self):
        import re
        for path in [ROOT/'README.md',*list((ROOT/'docs').glob('*'))]:
            if not path.is_file():continue
            for match in re.findall(r'ghcr\.io/[A-Za-z0-9_./-]+',path.read_text()):
                self.assertEqual(match,PUBLIC,str(path.relative_to(ROOT)))
    def test_quickstart_mounts_and_default_off(self):
        text=read('README.md')
        for required in [PUBLIC,DIGEST,'docker pull','docker run','--rank "$RANK"','--steering off',
                         '/opt/package/model','/etc/pico/fleet.conf','/var/lib/pico','--gpus all','--device /dev/infiniband']:
            self.assertIn(required,text)
    def test_qualification_honest_in_reader_docs(self):
        for name in ['README.md','docs/build.md','docs/benchmarks.md']:
            text=read(name).lower()
            self.assertIn('qualification',text)
            self.assertIn('pending',text)
    def test_readme_text_weights_not_bundled(self):
        text=read('README.md')
        self.assertIn('It does not contain the text rank files',text)
        self.assertIn('4 × NVIDIA DGX Spark / GB10',text)
    def test_no_private_artifact_fallback(self):
        text=read('scripts/stage-public-runtime.sh')+read('scripts/stage-qualified.sh')+read('scripts/build-image.sh')
        self.assertNotIn('deepseek-v41-flash-spark:',text)
        self.assertIn('/opt/package/bin/dsgb10_rank',text)
        self.assertIn('stage-public-runtime.sh',read('scripts/stage-qualified.sh'))
    def test_candidate_engine_not_original_binary(self):
        lock=data('sources.lock.json');r=data('docs/publication-runtime.json')
        self.assertEqual(lock['engine_binary_sha256'],r['engine_binary_sha256'])
        self.assertNotEqual(lock['production_engine_binary_sha256'],lock['engine_binary_sha256'])
    def test_fleet_template_uses_documented_keys_and_no_site_addresses(self):
        text=read('examples/fleet.conf.example')
        for n in range(4):
            for k in ['NEXT_IP0','NEXT_IP1','PREV_IP0','PREV_IP1','HOSTNAME','SSH','WEIGHTS','HASHMAP','ENGRAM','SPILL']:
                self.assertIn(f'RANK{n}_{k}=',text)
        for k in ['NEXT_DEV0','NEXT_DEV1','PREV_DEV0','PREV_DEV1','GID_INDEX']:
            self.assertIn(k+'=REPLACE_',text)
        self.assertEqual(scrub.problems(text),[])
    def test_pinned_converter_source_anonymously_available(self):
        p=data('docs/public-release.json')
        self.assertEqual(p['source_repository_anonymous_metadata_status'],200)
        self.assertEqual(p['pinned_source_readme_anonymous_status'],200)
    def test_history_scrub_detects_prior_deleted_secret(self):
        with tempfile.TemporaryDirectory() as d:
            def git(*a):return subprocess.check_output(['git','-C',d,*a],stderr=subprocess.DEVNULL)
            git('init','-q');git('config','user.name','Recipe Tests');git('config','user.email','tests@example.invalid')
            p=Path(d)/'old.txt';p.write_text('gh'+'p_'+'a'*25)
            git('add','old.txt');git('commit','-qm','fixture');p.unlink()
            git('add','-u');git('commit','-qm','delete fixture')
            counts,issues=scrub.history_problems(Path(d))
            self.assertGreater(counts['blobs'],0)
            self.assertTrue(any(i['category']=='access-secret' for i in issues))
            self.assertNotIn('value',issues[0])
