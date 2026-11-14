"""Offline checks for executable documentation; never download or contact a GPU."""
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
DOCS = ('README.md', 'docs/setup-spark.md')
MEASURED_SHA256 = '52a71857941ddf787cad1ca8dd38c4643f2bd1263ec2f6ddff7647f63eb6e5d4'


def read(name):
    return (ROOT / name).read_text()


def snippet(name, tag):
    match = re.search(r"<<'" + tag + r"'[^\n]*\n(.*?)\n" + tag + r"(?:\n|$)", read(name), re.S)
    if not match:
        raise AssertionError('Missing documented example ' + tag)
    return match.group(1)


def run_example(source, root):
    # Only stdlib/file examples are executed; route their fixed user paths to fixtures.
    return subprocess.run([sys.executable, '-B', '-c', source.replace('/srv/pico', str(root))],
                          cwd=root, text=True, capture_output=True)


class ReaderDocsTests(unittest.TestCase):
    def test_published_measurements_and_labels_unchanged(self):
        text = read('README.md')
        measured = text[text.index('## Measured performance\n'):text.index('## Quality\n')]
        self.assertEqual(hashlib.sha256(measured.encode()).hexdigest(), MEASURED_SHA256)

    def test_every_bash_block_is_syntactically_valid(self):
        for name in DOCS:
            blocks = re.findall(r'```bash\n(.*?)\n```', read(name), re.S)
            self.assertGreater(len(blocks), 5)
            for number, block in enumerate(blocks):
                with self.subTest(document=name, block=number):
                    result = subprocess.run(['bash', '-n'], input=block, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_network_configuration_precedes_neighbor_probes(self):
        text = read('docs/setup-spark.md')
        blocks = re.findall(r'```bash\n(.*?)\n```', text, re.S)
        configuration = next(b for b in blocks if 'sudo ip address replace' in b)
        self.assertNotIn('ping -I', configuration)
        self.assertTrue(any('ping -I' in b for b in blocks[blocks.index(configuration) + 1:]))
        self.assertIn('Complete this block on all four', text)

    def test_python_examples_compile(self):
        for name, tags in [('README.md', ('MODELS', 'ANSWER', 'PNG', 'IMAGE', 'VISION')),
                           ('docs/setup-spark.md', ('CHECK', 'LISTS', 'DESTINATIONS', 'CAPACITY', 'SPACE', 'RANK'))]:
            for tag in tags:
                with self.subTest(document=name, tag=tag):
                    compile(snippet(name, tag), name + ':' + tag, 'exec')

    def test_local_document_links_resolve(self):
        for name in DOCS:
            for target in re.findall(r'\]\(([^)]+)\)', read(name)):
                if '://' in target:
                    continue
                filename, _, anchor = target.partition('#')
                path = (ROOT / name).parent / filename if filename else ROOT / name
                self.assertTrue(path.exists(), (name, target))
                if anchor:
                    headings = re.findall(r'^#+ (.+)$', path.read_text(), re.M)
                    slugs = {re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings}
                    self.assertIn(anchor, slugs, (name, target))

    def test_major_guided_steps_have_verification(self):
        for name in DOCS:
            steps = re.findall(r'^#{2,3} (\d+)\. [^\n]+\n(.*?)(?=^#{2,3} \d+\.|\Z)', read(name), re.M | re.S)
            self.assertGreaterEqual(len(steps), 7)
            for number, body in steps:
                self.assertIn('**Verify', body, (name, number))

    def test_inputs_and_startup_are_explicit(self):
        setup = read('docs/setup-spark.md')
        for value in ('must stop if any value is unknown', '/srv/pico/ports.env', '/srv/pico/nodes.txt',
                      'four distinct destinations match', "grep -nE '^[^#]*REPLACE_'", 'sha256sum -c SHA256SUMS',
                      '192 * 2**30', 'pico-ring-check', '--rank "$RANK" correct', 'rank ${RANK}: passed;'):
            self.assertIn(value, setup)
        text = read('README.md')
        for value in ('ON by default, alpha 0.75, layers 1–39', '--steering glp39',
                      '`--steering off` on every rank', 'within 120 seconds', 'pico-rollback',
                      '/srv/pico/rollback-image-id.txt', 'no previous serving version'):
            # Wrapped prose is treated as words, not an exact line-break contract.
            self.assertIn(value, text.replace('**', '').replace('\n', ' '))

    def test_png_and_image_request_examples_match(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for tag in ('PNG', 'IMAGE'):
                result = run_example(snippet('README.md', tag), root)
                self.assertEqual(result.returncode, 0, result.stderr)
            data = (root / 'example.png').read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            chunks = {}
            pos = 8
            while pos < len(data):
                size = struct.unpack('>I', data[pos:pos + 4])[0]
                kind = data[pos + 4:pos + 8]
                payload = data[pos + 8:pos + 8 + size]
                crc = struct.unpack('>I', data[pos + 8 + size:pos + 12 + size])[0]
                self.assertEqual(crc, zlib.crc32(kind + payload) & 0xffffffff)
                chunks[kind] = payload
                pos += 12 + size
            self.assertEqual(struct.unpack('>IIBBBBB', chunks[b'IHDR']), (64, 64, 8, 2, 0, 0, 0))
            self.assertEqual(zlib.decompress(chunks[b'IDAT']), (b'\0' + bytes((255, 0, 0)) * 64) * 64)
            request = json.loads((root / 'image-request.json').read_text())
            url = request['messages'][0]['content'][1]['image_url']['url']
            self.assertEqual(base64.b64decode(url.split(',', 1)[1]), data)
            self.assertEqual(request['model'], 'deepseek-v4.1-flash')
            self.assertEqual(request['max_tokens'], 512)

    def test_response_parsers_accept_valid_fixtures_and_reject_errors(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'models.json').write_text(json.dumps({'data': [
                {'id': 'deepseek-v4.1-flash', 'max_model_len': 1048576}]}))
            (root / 'text-response.json').write_text(json.dumps({'choices': [
                {'message': {'content': 'Hello.'}}]}))
            (root / 'image-response.json').write_text(json.dumps({'choices': [
                {'message': {'content': 'A red square.'}}]}))
            for tag in ('MODELS', 'ANSWER', 'VISION'):
                result = run_example(snippet('README.md', tag), root)
                self.assertEqual(result.returncode, 0, result.stderr)
            (root / 'image-response.json').write_text(json.dumps({'error': 'fixture rejection'}))
            self.assertNotEqual(run_example(snippet('README.md', 'VISION'), root).returncode, 0)

    def test_per_rank_transfer_lists_and_hashes_use_only_matching_assets(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            model = root / 'bundle/model'; model.mkdir(parents=True)
            (root / 'work/deploy').mkdir(parents=True)
            names = ['engram_hashmap.bin', 'config.json', 'tokenizer.json']
            for rank in range(4):
                names += [f'rank{rank}.dsw', f'engram-l1-r{rank}of4.bin', f'engram-l14-r{rank}of4.bin']
            hashes = {}
            for name in names:
                payload = name.encode()
                (model / name).write_bytes(payload)
                hashes[name] = hashlib.sha256(payload).hexdigest()
            (model / 'asset-hashes.json').write_text(json.dumps({'sha256': hashes}))
            result = run_example(snippet('docs/setup-spark.md', 'LISTS'), root)
            self.assertEqual(result.returncode, 0, result.stderr)
            for rank in range(4):
                listed = (root / f'work/deploy/rank{rank}.files').read_text().splitlines()
                self.assertEqual({n for n in listed if n.startswith('rank')}, {f'rank{rank}.dsw'})
                self.assertEqual({n for n in listed if n.startswith('engram-l')},
                                 {f'engram-l1-r{rank}of4.bin', f'engram-l14-r{rank}of4.bin'})
                for line in (root / f'work/deploy/rank{rank}.sha256').read_text().splitlines():
                    sha, name = line.split('  ', 1)
                    self.assertEqual(sha, hashes[name])


if __name__ == '__main__':
    unittest.main()
