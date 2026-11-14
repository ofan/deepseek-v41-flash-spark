"""Offline adapter regression tests. Fixture strings are not evaluation prompts."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hle_http', ROOT / 'scripts/hle-http.py')
hle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hle)


def stream(content='fixture', finish='stop', done=True, usage=True):
    chunks = [{'id': 'fixture-id', 'choices': [{'index': 0, 'delta': {'reasoning_content': 'draft'}}]},
              {'choices': [{'index': 0, 'delta': {'content': content}}]},
              {'choices': [{'index': 0, 'delta': {}, 'finish_reason': finish}]}]
    if usage:
        chunks.append({'choices': [], 'usage': {'prompt_tokens': 4, 'completion_tokens': 3}})
    lines = []
    for chunk in chunks:
        lines.extend([('data: '+json.dumps(chunk, ensure_ascii=False)).encode(), b''])
    if done:
        lines.extend([b'data: [DONE]', b''])
    return lines


class HLEHttpTests(unittest.TestCase):
    def args(self, **kw):
        return argparse.Namespace(model='fixture-model', max_tokens=262144, **kw)

    def record(self):
        bench = hle.load_hle()
        # Not a benchmark question; test only the source's formatting API.
        return bench.build_records([bench.Problem('fixture-id', 'fixture', 'fixture')])[0]

    def staged(self, d):
        p = Path(d)
        data = p/'text.jsonl'
        data.write_text(json.dumps({'id': 'fixture-id', 'question': 'fixture', 'answer': 'fixture'})+'\n')
        provenance = p/'provenance.json'
        hle.write_json(provenance, {'source': hle.HLE_SOURCE, 'revision': hle.HLE_REVISION,
                                  'status': 'staged', 'text_jsonl_sha256': hle.file_digest(data),
                                  'actual_text_samples': 1})
        return data, provenance

    def raw(self):
        return {'task_id': 'fixture-id', 'sample_idx': 0, 'seq_seed': 0,
                'finish_reason': 'stop', 'raw_text': 'fixture', 'num_output_tokens': 1}

    def test_source_hash_inventory(self):
        source = hle.verify_evaluator()
        self.assertEqual(source['commit'], '774ce244b87cc0eb8d4b94ab9f5de2ab22049f01')
        self.assertEqual(source['license'], 'Apache-2.0')
        self.assertIn('eval/common/judge.py', source['files_sha256'])
        self.assertIn('eval/hle/bench.py', source['files_sha256'])

    def test_tampered_evaluator_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'SOURCE.json').write_text(json.dumps({'files_sha256': {'fixture.py': '0'*64}}))
            (p/'fixture.py').write_text('fixture')
            with patch.object(hle, 'EVALUATOR', p), self.assertRaisesRegex(ValueError, 'hash mismatch'):
                hle.verify_evaluator()

    def test_prompt_messages_are_existing_builder_output(self):
        rec = self.record()
        body = hle.payload(rec, 7, self.args())
        self.assertEqual(body['messages'], rec['messages'])
        self.assertEqual(len(body['messages']), 1)
        self.assertNotIn('tools', body)
        self.assertEqual((body['temperature'], body['top_p'], body['seed']), (1., 1., 7))
        self.assertEqual(body['reasoning_effort'], 100)
        self.assertEqual(body['max_tokens'], 262144)
        self.assertTrue(body['chat_template_kwargs']['thinking'])

    def test_judge_requires_explicit_configuration_without_recording_secret(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            hle.frozen_judge()
        with patch.dict(os.environ, {'EVAL_JUDGE_MODEL': 'fixture-judge', 'EVAL_JUDGE_BASE_URL': 'http://localhost/v1', 'EVAL_JUDGE_API_KEY': 'fixture'}):
            frozen = hle.frozen_judge()
        self.assertEqual(frozen['model'], 'fixture-judge')
        self.assertEqual(frozen['max_tokens'], 65536)
        self.assertNotIn('api_key', frozen)
        self.assertNotIn('base_url', frozen)

    def test_default_is_bounded_and_has_no_limit(self):
        p = hle.parser()
        args = p.parse_args(['run', '--base-url', 'http://localhost/v1', '--model', 'fixture',
                             '--data-file', 'fixture', '--provenance', 'fixture', '--out-dir', 'fixture',
                             '--server-max-tokens', '262144', '--load-command', 'fixture'])
        self.assertEqual(args.concurrency, 1)
        self.assertFalse(hasattr(args, 'limit'))
        self.assertEqual(args.max_tokens, 262144)

    def test_strict_stream_utf8_and_reasoning_separation(self):
        got = hle.consume_sse(stream('é漢'), threading.Event(), time.monotonic()+5)
        self.assertEqual(got['raw_text'], 'é漢')
        self.assertEqual(got['reasoning_text'], 'draft')
        self.assertEqual(got['request_id'], 'fixture-id')

    def test_incomplete_stream_rejected(self):
        for kw in [{'done': False}, {'usage': False}, {'finish': 'error'}]:
            with self.subTest(kw=kw), self.assertRaises(hle.ProtocolError):
                hle.consume_sse(stream(**kw), threading.Event(), time.monotonic()+5)

    def test_cancelled_stream_not_a_success(self):
        flag = threading.Event(); flag.set()
        with self.assertRaises(RuntimeError):
            hle.consume_sse(stream(), flag, time.monotonic()+5)

    def test_request_deadline(self):
        with self.assertRaises(TimeoutError):
            hle.consume_sse(stream(), threading.Event(), time.monotonic()-1)

    def test_tools_rejected(self):
        lines = [b'data: {"choices":[{"delta":{"tool_calls":[{}]}}]}', b'']
        with self.assertRaises(hle.ProtocolError):
            hle.consume_sse(lines, threading.Event(), time.monotonic()+5)

    def test_private_material_cannot_land_in_checkout(self):
        with self.assertRaises(ValueError):
            hle.private_directory(ROOT/'work/should-not-exist')

    def test_checkpoint_resume_and_duplicates(self):
        rec = [self.record()]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'raw.jsonl'
            self.assertEqual(hle.checkpoint_rows(p, rec), {})
            p.write_text(json.dumps(self.raw())+'\n')
            self.assertEqual(len(hle.checkpoint_rows(p, rec)), 1)
            p.write_text(p.read_text()*2)
            with self.assertRaises(ValueError):
                hle.checkpoint_rows(p, rec)

    def test_unknown_torn_and_error_checkpoints_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'raw.jsonl'
            for update in [{'task_id': 'unknown'}, {'seq_seed': 9}, {'finish_reason': 'error'}]:
                p.write_text(json.dumps(dict(self.raw(), **update))+'\n')
                with self.assertRaises(ValueError):
                    hle.checkpoint_rows(p, [self.record()])
            p.write_text('{')
            with self.assertRaises(json.JSONDecodeError):
                hle.checkpoint_rows(p, [self.record()])

    def test_dataset_provenance_and_complete_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            data, provenance = self.staged(d)
            records, _ = hle.validate_dataset(data, provenance)
            self.assertEqual(len(records), 1)
            data.write_text(data.read_text()+'\n')
            with self.assertRaisesRegex(ValueError, 'provenance/hash'):
                hle.validate_dataset(data, provenance)

    def test_output_budget_clamp_is_never_silent(self):
        args = self.args(concurrency=1, server_max_tokens=32768, pause_timeout=300, request_deadline=7200)
        with self.assertRaisesRegex(ValueError, 'output cap'):
            hle.generate(args)

    def test_gate_error_records_only_safe_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            err = urllib.error.HTTPError('https://huggingface.co/fixture', 403, 'Forbidden', {}, None)
            args = argparse.Namespace(directory=d, hf_token_env='FIXTURE_ABSENT_TOKEN')
            with patch.object(hle.urllib.request, 'urlopen', side_effect=err), self.assertRaises(RuntimeError):
                hle.stage(args)
            got = json.loads((Path(d)/'dataset-provenance.json').read_text())
            self.assertEqual(got['http_status'], 403)
            self.assertIsNone(got['actual_text_samples'])
            self.assertFalse((Path(d)/'hle-text.jsonl').exists())
            err.close()

    def test_stage_preserves_official_fields_and_filters_with_existing_predicate(self):
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            self.skipTest('Optional staging dependency pyarrow not installed')
        fixture = [
            {'id': 'a', 'question': ' fixture ', 'answer': ' fixture ', 'image': '', 'raw_subject': 'fixture'},
            {'id': 'b', 'question': 'fixture', 'answer': 'fixture', 'image': 'fixture-image', 'raw_subject': 'fixture'},
        ]
        sink = pa.BufferOutputStream()
        pq.write_table(pa.Table.from_pylist(fixture), sink)
        raw = sink.getvalue().to_pybytes()
        class Response(io.BytesIO):
            status = 200
        with tempfile.TemporaryDirectory() as d:
            args = argparse.Namespace(directory=d, hf_token_env='FIXTURE_ABSENT_TOKEN')
            with patch.object(hle.urllib.request, 'urlopen', return_value=Response(raw)), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(hle.stage(args), 0)
            meta = json.loads((Path(d)/'dataset-provenance.json').read_text())
            self.assertEqual((meta['actual_total_samples'], meta['actual_text_samples'], meta['actual_image_samples']), (2, 1, 1))
            row = json.loads((Path(d)/'hle-text.jsonl').read_text())
            self.assertEqual(row['question'], fixture[0]['question'])
            self.assertEqual(row['answer'], fixture[0]['answer'])
            self.assertEqual(meta['parquet_sha256'], hashlib.sha256(raw).hexdigest())

    def test_load_guard_pauses_and_fails_closed(self):
        guard = hle.LoadGuard('fixture', -1, threading.Event())
        with patch.object(guard, 'sample', return_value=1), self.assertRaises(RuntimeError):
            guard.wait()
        with patch.object(hle.subprocess, 'run', return_value=argparse.Namespace(stdout=b'{"external_active":-1}')):
            with self.assertRaises(ValueError):
                guard.sample()

    def test_one_external_request_aborts_immediately(self):
        guard=hle.LoadGuard('fixture',1,threading.Event())
        with patch.object(guard.done,'wait',return_value=False), patch.object(guard,'sample',return_value=1), patch.object(guard,'abort') as abort:
            guard.monitor()
        abort.assert_called_once()
        self.assertIn('Exclusive benchmark violated',abort.call_args.args[0])

    def test_generation_rejects_contamination_before_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            data,provenance=self.staged(d)
            args=self.args(concurrency=1,server_max_tokens=262144,out_dir=str(Path(d)/'run'),
                           data_file=str(data),provenance=str(provenance),request_deadline=5,
                           pause_timeout=1,load_command='fixture',api_key_env='FIXTURE_ABSENT_TOKEN',base_url='http://localhost/v1')
            class Response:
                status_code=200
                headers={}
                def iter_lines(self):return iter(stream())
                def close(self):pass
            with patch('requests.post',return_value=Response()), patch.object(hle.LoadGuard,'monitor'), patch.object(hle.LoadGuard,'sample',side_effect=[0,1]), patch.dict(os.environ,{'EVAL_JUDGE_MODEL':'fixture-judge','EVAL_JUDGE_BASE_URL':'http://localhost/v1','EVAL_JUDGE_API_KEY':'fixture'}):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertNotEqual(hle.generate(args),0)
            raw=Path(args.out_dir)/'raw_rank000.jsonl'
            self.assertTrue(not raw.exists() or not raw.read_text().strip())

    def test_no_serving_or_clock_mutations(self):
        s = (ROOT/'scripts/hle-http.py').read_text()
        for fragment in ['systemctl', 'docker restart', 'nvidia-smi', '/_/config', '/_/models/']:
            self.assertNotIn(fragment, s)

    def test_incomplete_coverage_never_reaches_judge(self):
        with tempfile.TemporaryDirectory() as d:
            data, provenance = self.staged(d)
            p = Path(d)/'run';p.mkdir()
            hle.write_json(p/'meta.json', {'data_file': str(data)})
            args = argparse.Namespace(out_dir=str(p), data_file=None, provenance=str(provenance))
            with patch.object(hle.subprocess, 'run') as run, self.assertRaisesRegex(ValueError, 'incomplete'):
                hle.score(args)
            run.assert_not_called()

    def test_generation_http_and_resume_without_resubmitting(self):
        with tempfile.TemporaryDirectory() as d:
            data, provenance = self.staged(d)
            args = self.args(concurrency=1, server_max_tokens=262144, out_dir=str(Path(d)/'run'),
                             data_file=str(data), provenance=str(provenance), request_deadline=5,
                             pause_timeout=1, load_command='fixture', api_key_env='FIXTURE_ABSENT_TOKEN',
                             base_url='http://localhost/v1')
            class Response:
                status_code = 200
                headers = {}
                def iter_lines(self): return iter(stream())
                def close(self): pass
            with patch('requests.post', return_value=Response()) as post, patch.object(hle.LoadGuard, 'sample', return_value=0), patch.dict(os.environ, {'EVAL_JUDGE_MODEL': 'fixture-judge', 'EVAL_JUDGE_BASE_URL': 'http://localhost/v1', 'EVAL_JUDGE_API_KEY': 'fixture'}):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(hle.generate(args), 0)
                    self.assertEqual(hle.generate(args), 0)
                self.assertEqual(post.call_count, 1)
                self.assertEqual(post.call_args.kwargs['json']['messages'], self.record()['messages'])
            state = json.loads((Path(args.out_dir)/'generation-state.json').read_text())
            self.assertTrue(state['coverage_complete'])
            args.max_tokens = 1
            with patch.dict(os.environ, {'EVAL_JUDGE_MODEL': 'fixture-judge', 'EVAL_JUDGE_BASE_URL': 'http://localhost/v1', 'EVAL_JUDGE_API_KEY': 'fixture'}), self.assertRaisesRegex(ValueError, 'Resume configuration'):
                hle.generate(args)

    def test_unchanged_hle_llm_judge_path(self):
        # Exercise the actual scorer, substituting only the network judge result.
        hle.load_hle()
        import common.judge as judge
        path = hle.EVALUATOR/'eval/score.py'
        spec = importlib.util.spec_from_file_location('fixture_hle_score', path)
        scorer = importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
        row = dict(self.raw(), correct=False)
        records = {'fixture-id': self.record()}
        verdict = {'judge_correct': True, 'judge_raw': 'fixture', 'judge_parsed': True}
        with patch.object(judge, 'judge_answers', return_value=[verdict]) as call, patch.object(judge, 'resolve_model', return_value='fixture-judge'):
            self.assertEqual(scorer._judge([row], records, 'hle', 'llm', 1), 'fixture-judge')
        self.assertEqual(call.call_args.kwargs, {'kind': 'hle', 'concurrency': 1})
        self.assertTrue(row['correct'])
        self.assertFalse(row['rule_correct'])
        with self.assertRaises(SystemExit):
            scorer._judge([], records, 'hle', 'rule', 1)


if __name__ == '__main__':
    unittest.main()
