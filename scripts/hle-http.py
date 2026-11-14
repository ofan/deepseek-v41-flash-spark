#!/usr/bin/env python3
"""Client-only HLE transport; unchanged vendored prompts and LLM scoring.

Datasets and answer text belong in a private directory outside this checkout.
No engine, route, steering, clock or session-management API is called.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / 'vendor/hle-evaluator'
HLE_REVISION = '5a81a4c7271a2a2a312b9a690f0c2fde837e4c29'
HLE_SOURCE = 'https://huggingface.co/datasets/cais/hle'
DEFAULT_CONCURRENCY = 1
DEFAULT_MAX_TOKENS = 262144


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def private_directory(path):
    p = Path(path).expanduser().resolve()
    if p == ROOT or ROOT in p.parents:
        raise ValueError('Dataset and raw answers must be outside the public checkout')
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    p.chmod(0o700)
    return p


def verify_evaluator():
    info = json.loads((EVALUATOR / 'SOURCE.json').read_text())
    for name, expected in info['files_sha256'].items():
        if file_digest(EVALUATOR / name) != expected:
            raise ValueError('Evaluator source hash mismatch: ' + name)
    return info


def load_hle():
    verify_evaluator()
    sys.path.insert(0, str(EVALUATOR / 'eval'))
    from common.loader import load_bench
    return load_bench('hle')


def stage(args):
    """Download the pinned official parquet; filter only using the existing predicate."""
    dest = private_directory(args.directory)
    record = {'source': HLE_SOURCE, 'revision': HLE_REVISION,
              'split': 'test', 'checked_at': utc(), 'status': 'not_staged',
              'actual_total_samples': None, 'actual_text_samples': None}
    headers = {}
    if token := os.environ.get(args.hf_token_env):
        headers['Authorization'] = 'Bearer ' + token
    url = HLE_SOURCE + f'/resolve/{HLE_REVISION}/data/test-00000-of-00001.parquet'
    partial = dest / 'hle-test.parquet.partial'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
            record['http_status'] = r.status
            with partial.open('wb') as f:
                while chunk := r.read(1024 * 1024):
                    f.write(chunk)
        parquet = dest / 'hle-test.parquet'
        partial.replace(parquet)
    except urllib.error.HTTPError as exc:
        record.update(http_status=exc.code, status='access_failed',
                      error='Official dataset access denied; obtain authorization under its access terms.'
                      if exc.code in (401, 403) else 'Official dataset download failed.')
        write_json(dest / 'dataset-provenance.json', record)
        raise RuntimeError(f'Official HLE dataset HTTP {exc.code}; no dataset staged') from None
    except Exception:
        record.update(status='download_failed', error='Download interrupted; no dataset staged.')
        write_json(dest / 'dataset-provenance.json', record)
        raise RuntimeError('Official HLE dataset download interrupted') from None
    import pyarrow.parquet as pq
    bench = load_hle()
    table = pq.ParquetFile(parquet)
    total = text = 0
    ids = set()
    target = dest / 'hle-text.jsonl'
    temp = dest / 'hle-text.jsonl.partial'
    with temp.open('w', encoding='utf-8') as out:
        for batch in table.iter_batches(batch_size=128):
            for row in batch.to_pylist():
                total += 1
                if bench._has_image(row):
                    continue
                item = {'id': row['id'], 'question': row['question'], 'answer': row['answer'],
                        'category': row.get('category') or row.get('raw_subject') or 'unknown'}
                if any(not isinstance(item[k], str) or not item[k] for k in ('id', 'question', 'answer')):
                    raise ValueError('Invalid official dataset fields')
                if item['id'] in ids:
                    raise ValueError('Duplicate official dataset ID')
                ids.add(item['id'])
                out.write(json.dumps(item, ensure_ascii=False) + '\n')
                text += 1
    if not text:
        raise ValueError('Official text subset is empty')
    temp.replace(target)
    record.update(status='staged', actual_total_samples=total, actual_text_samples=text,
                  actual_image_samples=total-text, parquet_sha256=file_digest(parquet),
                  text_jsonl_sha256=file_digest(target),
                  selection='Unchanged eval/hle/bench.py _has_image(row) is false; source order retained',
                  fields='id, question and answer unchanged; category retained for grouping')
    write_json(dest / 'dataset-provenance.json', record)
    print(json.dumps(record), flush=True)
    return 0


def payload(record, index, args):
    # Exact existing build_messages output: no added system or evaluation prompts.
    return {'model': args.model, 'messages': record['messages'],
            'temperature': 1.0, 'top_p': 1.0, 'seed': index,
            'max_tokens': args.max_tokens, 'reasoning_effort': 100,
            'chat_template_kwargs': {'thinking': True, 'reasoning_effort': 100},
            'stream': True, 'stream_options': {'include_usage': True}}


class ProtocolError(RuntimeError):
    pass


def consume_sse(lines, cancelled, deadline):
    """Separate reasoning from final content; require explicit terminal and usage events."""
    content, reasoning = [], []
    finish = request_id = None
    usage = None
    done = False
    fields = []

    def event(data):
        nonlocal finish, request_id, usage, done
        if data == '[DONE]':
            done = True
            return
        obj = json.loads(data)
        if obj.get('error'):
            raise ProtocolError('Server reported an error event')
        request_id = obj.get('id') or request_id
        if obj.get('usage') is not None:
            usage = obj['usage']
        choices = obj.get('choices', [])
        if len(choices) > 1:
            raise ProtocolError('Expected exactly one sample')
        for choice in choices:
            if choice.get('index', 0) != 0:
                raise ProtocolError('Unexpected sample index')
            delta = choice.get('delta', {})
            if delta.get('tool_calls'):
                raise ProtocolError('Tool call returned in a no-tools benchmark')
            for field, target in [('content', content), ('reasoning_content', reasoning)]:
                if delta.get(field) is not None:
                    if not isinstance(delta[field], str):
                        raise ProtocolError('Non-text completion field')
                    target.append(delta[field])
            if choice.get('finish_reason') is not None:
                finish = choice['finish_reason']

    for raw in lines:
        if cancelled.is_set():
            raise RuntimeError('Benchmark paused for production contention')
        if time.monotonic() > deadline:
            raise TimeoutError('Per-request wall deadline exceeded')
        line = raw.decode('utf-8', errors='strict') if isinstance(raw, bytes) else raw
        if not line:
            if fields:
                event('\n'.join(fields))
                fields = []
            if done:
                break
        elif line.startswith('data:'):
            fields.append(line[5:].lstrip(' '))
    if fields and not done:
        event('\n'.join(fields))
    if not done or finish not in ('stop', 'length') or not isinstance(usage, dict):
        raise ProtocolError('Incomplete stream, invalid finish reason or missing usage')
    if any(not isinstance(usage.get(k), int) or usage[k] < 0
           for k in ('prompt_tokens', 'completion_tokens')) or usage['completion_tokens'] == 0:
        raise ProtocolError('Missing/invalid token accounting')
    return {'raw_text': ''.join(content), 'reasoning_text': ''.join(reasoning),
            'finish_reason': finish, 'usage': usage, 'request_id': request_id}


class LoadGuard:
    """External read-only observer returns external_active, excluding this adapter."""
    def __init__(self, command, timeout, cancelled):
        self.command, self.timeout, self.cancelled = command, timeout, cancelled
        self.done = threading.Event()
        self.responses = set()
        self.lock = threading.Lock()
        self.high_samples = 0
        self.observations = self.max_external_active = 0
        self.reason = None

    def sample(self):
        proc = subprocess.run(shlex.split(self.command), capture_output=True, timeout=10, check=True)
        n = json.loads(proc.stdout)['external_active']
        if type(n) is not int or n < 0:
            raise ValueError('Invalid load observer count')
        self.observations += 1
        self.max_external_active = max(self.max_external_active, n)
        return n

    def wait(self):
        end = time.monotonic() + self.timeout
        while self.sample():
            if time.monotonic() > end or self.cancelled.wait(5):
                raise RuntimeError('Paused: production load did not drain within the client wait budget')
        if self.cancelled.is_set():
            raise RuntimeError('Paused: load observer requested stop')

    def abort(self, reason):
        self.reason = self.reason or reason
        self.cancelled.set()
        with self.lock:
            for response in list(self.responses):
                response.close()

    def monitor(self):
        while not self.done.wait(5):
            try:
                self.high_samples = self.high_samples + 1 if self.sample() >= 4 else 0
                if self.high_samples >= 3:
                    self.abort('At least four external requests observed for three consecutive load samples')
                    return
            except Exception:
                self.abort('Load observer failed; stopped closed')
                return


def checkpoint_rows(path, records):
    rows = {}
    by_id = {r['task_id']: i for i, r in enumerate(records)}
    if path.exists():
        lines = path.read_text().splitlines()
        for line in lines:
            row = json.loads(line)  # Torn JSONL is an error, never silently discarded.
            task = row['task_id']
            if (task not in by_id or task in rows or row['sample_idx'] != 0
                    or row['seq_seed'] != by_id[task] or row['finish_reason'] not in ('stop', 'length')
                    or not isinstance(row['raw_text'], str) or row['num_output_tokens'] < 1):
                raise ValueError('Invalid, unknown or duplicate checkpoint row')
            rows[task] = row
    return rows


def validate_dataset(data_file, provenance_file):
    provenance = json.loads(Path(provenance_file).read_text())
    if (provenance.get('status') != 'staged' or provenance.get('source') != HLE_SOURCE
            or provenance.get('revision') != HLE_REVISION
            or provenance.get('text_jsonl_sha256') != file_digest(data_file)):
        raise ValueError('Official dataset provenance/hash mismatch')
    bench = load_hle()
    problems = bench.load(data_file)
    if any(p.has_image for p in problems) or not problems or len(problems) != provenance['actual_text_samples']:
        raise ValueError('Expected complete official text-only subset, without images')
    return bench.build_records(problems), provenance


def frozen_judge():
    # Freeze the existing scorer's model and destination before any generation.
    for key in ('EVAL_JUDGE_BASE_URL', 'EVAL_JUDGE_API_KEY', 'EVAL_JUDGE_MODEL'):
        if not os.environ.get(key):
            raise ValueError('Missing judge configuration: ' + key)
    return {'model': os.environ['EVAL_JUDGE_MODEL'],
            'base_url_sha256': digest(os.environ['EVAL_JUDGE_BASE_URL'].rstrip('/').encode()),
            'temperature': 1.0, 'top_p': 0.95, 'max_tokens': 65536}


def generate(args):
    import requests
    if not 1 <= args.concurrency <= 4:
        raise ValueError('Client concurrency must be 1..4; default is 1')
    if args.pause_timeout <= 0 or args.request_deadline <= 0:
        raise ValueError('Client wait and request deadlines must be positive')
    if args.max_tokens < 1 or args.server_max_tokens < args.max_tokens:
        raise ValueError('Requested budget exceeds verified server output cap; no silent clamping allowed')
    dest = private_directory(args.out_dir)
    records, provenance = validate_dataset(args.data_file, args.provenance)
    source = verify_evaluator()
    judge = frozen_judge()
    config = {'bench': 'hle', 'n_sample': 1, 'temperature': 1.0, 'top_p': 1.0,
              'reasoning_effort': 100, 'max_len': 1048576, 'max_tokens': args.max_tokens,
              'verified_server_max_tokens': args.server_max_tokens,
              'model_name': args.model, 'concurrency': args.concurrency,
              'per_request_deadline_seconds': args.request_deadline,
              'dataset_sha256': provenance['text_jsonl_sha256'], 'dataset_revision': HLE_REVISION,
              'expected_tasks': len(records), 'steering': {'vector': 'GLP-39', 'alpha': 0.75, 'layers': '1-39'},
              'evaluator_commit': source['commit'], 'adapter_sha256': file_digest(__file__),
              'endpoint_sha256': digest(args.base_url.rstrip('/').encode()),
              'frozen_judge': judge,
              'transport': 'Chat Completions streaming; server-rendered template; no tools',
              'settings_verification': 'Operator must verify live steering, output cap and model before invocation'}
    meta_path = dest / 'meta.json'
    if meta_path.exists():
        old = json.loads(meta_path.read_text())
        if any(old.get(k) != v for k, v in config.items()):
            raise ValueError('Resume configuration differs; use a new private run directory')
    else:
        write_json(meta_path, dict(config, data_file=str(Path(args.data_file).resolve()), started_at=utc()))
    raw_path = dest / 'raw_rank000.jsonl'
    complete = checkpoint_rows(raw_path, records)
    pending = [(i, r) for i, r in enumerate(records) if r['task_id'] not in complete]
    cancelled = threading.Event()
    guard = LoadGuard(args.load_command, args.pause_timeout, cancelled)
    watcher = threading.Thread(target=guard.monitor, daemon=True)
    raw_lock = threading.Lock()
    key = os.environ.get(args.api_key_env, '')
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key

    def one(item):
        index, record = item
        guard.wait()
        start = time.monotonic()
        response = requests.post(args.base_url.rstrip('/') + '/chat/completions',
                                 headers=headers, json=payload(record, index, args),
                                 stream=True, timeout=(10, 30))
        with guard.lock:
            guard.responses.add(response)
        try:
            if response.status_code != 200:
                # Retain evidence locally; never print bodies, endpoints or exception URLs.
                write_json(dest / ('http-error-' + str(index) + '.json'),
                           {'task_index': index, 'status': response.status_code,
                            'request_id': response.headers.get('x-request-id'),
                            'body_sha256': digest(response.content)})
                raise RuntimeError('Generation HTTP ' + str(response.status_code))
            d = consume_sse(response.iter_lines(), cancelled, start + args.request_deadline)
            if cancelled.is_set():
                raise RuntimeError('Generation cancelled; partial sample not checkpointed')
            row = {'task_id': record['task_id'], 'sample_idx': 0, 'seq_seed': index,
                   'prompt_len': d['usage']['prompt_tokens'],
                   'num_output_tokens': d['usage']['completion_tokens'],
                   'finish_reason': d['finish_reason'], 'raw_text': d['raw_text'],
                   'reasoning_sha256': digest(d['reasoning_text'].encode()),
                   'content_sha256': digest(d['raw_text'].encode()),
                   'request_id': d['request_id'] or response.headers.get('x-request-id'),
                   'elapsed_seconds': time.monotonic()-start, 'usage': d['usage']}
            with raw_lock:
                with raw_path.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
                    f.flush()
                    os.fsync(f.fileno())
                complete[record['task_id']] = row
                print(json.dumps({'completed': len(complete), 'expected': len(records),
                                  'task_index': index, 'finish_reason': row['finish_reason']}), flush=True)
        finally:
            with guard.lock:
                guard.responses.discard(response)
            response.close()

    watcher.start()
    error = None
    try:
        # Bounded submission: at most one wave, not the entire dataset, is queued.
        with concurrent.futures.ThreadPoolExecutor(args.concurrency) as pool:
            for start in range(0, len(pending), args.concurrency):
                wave = [pool.submit(one, x) for x in pending[start:start+args.concurrency]]
                try:
                    for f in concurrent.futures.as_completed(wave):
                        f.result()
                except BaseException:
                    guard.abort('One generation failed; stopped the client wave')
                    raise
    except BaseException as exc:
        error = type(exc).__name__  # Do not publish arbitrary exception text.
    finally:
        guard.done.set()
        watcher.join(timeout=12)
        write_json(dest / 'generation-state.json',
                   {'checked_at': utc(), 'completed': len(complete), 'expected': len(records),
                    'coverage_complete': len(complete) == len(records), 'error_type': error,
                    'stop_reason': guard.reason, 'load_samples': guard.observations,
                    'max_external_active': guard.max_external_active})
    return 1 if error or len(complete) != len(records) else 0


def score(args):
    """Call the unmodified scorer only after full task coverage; do not weaken its judge."""
    dest = private_directory(args.out_dir)
    meta = json.loads((dest / 'meta.json').read_text())
    data = args.data_file or meta['data_file']
    records, _ = validate_dataset(data, args.provenance)
    rows = checkpoint_rows(dest / 'raw_rank000.jsonl', records)
    if len(rows) != len(records):
        raise ValueError('Refusing to score incomplete HLE coverage')
    if list(dest.glob('raw_rank*.jsonl')) != [dest / 'raw_rank000.jsonl']:
        raise ValueError('Unexpected rank outputs')
    verify_evaluator()
    if meta.get('frozen_judge') != frozen_judge():
        raise ValueError('Judge differs from the configuration frozen before generation')
    command = [sys.executable, '-B', str(EVALUATOR / 'eval/score.py'), '--out-dir', str(dest),
               '--data-file', str(data), '--judge', 'llm', '--judge-concurrency', str(args.judge_concurrency)]
    rc = subprocess.run(command, check=False).returncode
    if rc:
        return rc
    summary = json.loads((dest / 'summary.json').read_text())
    if (not summary['coverage_complete'] or summary.get('judge_unparsed', 0)
            or summary.get('judge_verdict_unparsed', 0) or summary.get('invalid_rollouts', 0)):
        raise ValueError('Do not publish: incomplete coverage, invalid outputs or unparsed judge replies')
    return 0


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('stage', help='Stage the pinned official gated dataset outside the checkout')
    s.add_argument('--directory', required=True)
    s.add_argument('--hf-token-env', default='HF_TOKEN')
    s.set_defaults(fn=stage)
    r = sub.add_parser('run', help='Generate complete text-only subset, with checkpoint/resume')
    r.add_argument('--base-url', required=True, help='Your server base URL ending in /v1')
    r.add_argument('--model', required=True)
    r.add_argument('--api-key-env', default='HLE_API_KEY')
    r.add_argument('--data-file', required=True)
    r.add_argument('--provenance', required=True)
    r.add_argument('--out-dir', required=True)
    r.add_argument('--concurrency', type=int, default=DEFAULT_CONCURRENCY)
    r.add_argument('--max-tokens', type=int, default=DEFAULT_MAX_TOKENS)
    r.add_argument('--server-max-tokens', type=int, required=True, help='Verified live output cap; never inferred')
    r.add_argument('--request-deadline', type=float, default=7200)
    r.add_argument('--pause-timeout', type=float, default=300)
    r.add_argument('--load-command', required=True, help='Read-only observer printing JSON external_active; no shell')
    r.set_defaults(fn=generate)
    s = sub.add_parser('score', help='Unchanged existing LLM grader, no exact-match substitution')
    s.add_argument('--out-dir', required=True)
    s.add_argument('--data-file')
    s.add_argument('--provenance', required=True)
    s.add_argument('--judge-concurrency', type=int, default=1)
    s.set_defaults(fn=score)
    return p


def main():
    # Private raw files and dataset files never inherit permissive creation modes.
    os.umask(0o077)
    args = parser().parse_args()
    try:
        return args.fn(args)
    except Exception as exc:
        # Exception types only: HTTP libraries can embed credential-bearing URLs.
        print(json.dumps({'status': 'stopped', 'error_type': type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
