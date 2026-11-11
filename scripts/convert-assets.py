#!/usr/bin/env python3
"""Plan by default. Convert a pre-obtained pinned checkpoint; never download one."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--checkpoint-revision', required=True)
    p.add_argument('--source', type=Path, default=ROOT / 'work/source/engine')
    p.add_argument('--build', type=Path, default=ROOT / 'work/compiled/engine')
    p.add_argument('--output', type=Path, default=ROOT / 'bundle/model')
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    lock = json.loads((ROOT / 'sources.lock.json').read_text())
    if a.checkpoint_revision != lock['model_revision']:
        p.error('Checkpoint revision differs from the pinned production revision')
    ck, build, out = a.checkpoint.resolve(), a.build.resolve(), a.output.resolve()
    commands = []
    for rank in range(4):
        commands += [
            [str(build/'weights/dsw_convert'), '--ckpt', str(ck), '--rank', str(rank), '--out', str(out/f'rank{rank}.dsw')],
            [str(build/'weights/dsw_verify'), '--ckpt', str(ck), '--file', str(out/f'rank{rank}.dsw'), '--threads', '4'],
            [str(build/'engram/engram_pack'), str(ck), str(out), str(rank)],
        ]
    commands += [['python3', str(a.source.resolve()/lock['source_directory']/'engine/engram/py/make_hashmap_stdlib.py'), str(ck), str(out/'engram_hashmap.bin')]]
    if not a.execute:
        print(json.dumps({'mode':'plan-only', 'commands':commands}, indent=2))
        return
    head = subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'], text=True).strip()
    if head != lock['engine_commit']:
        p.error('Converter source is not the production engine commit')
    if subprocess.check_output(['git','-C',str(a.source),'status','--porcelain'], text=True).strip():
        p.error('Converter source is dirty')
    if out.exists():
        p.error('Refusing to overwrite an existing output directory')
    # Revision is operator-supplied provenance, not a substitute for verified HF snapshot acquisition.
    for f in ('config.json', 'tokenizer.json'):
        if not (ck/f).is_file():
            p.error('Required checkpoint metadata is absent')
    out.mkdir(parents=True)
    logs = ROOT / 'work/conversion-logs'
    logs.mkdir(parents=True, exist_ok=True)
    for i, command in enumerate(commands):
        with (logs/f'step-{i:02d}.log').open('wb') as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
    for name in ('config.json','tokenizer.json','tokenizer_config.json','generation_config.json','special_tokens_map.json'):
        if (ck/name).is_file():
            shutil.copyfile(ck/name, out/name)
    hashes = {f.name: sha(f) for f in sorted(out.iterdir()) if f.is_file()}
    receipt = {'model':lock['model_repository'], 'revision':lock['model_revision'], 'engine_commit':head,
               'all_conversion_commands_exit_zero':True, 'sha256':hashes}
    (out/'asset-hashes.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('All four ranks converted and verified; Engram tables materialized. See work/conversion-logs.')

if __name__ == '__main__':
    main()
