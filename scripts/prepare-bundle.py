#!/usr/bin/env python3
"""Fail closed: validate already-staged assets; never download or alter binaries."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(8*1024*1024), b''):
            h.update(part)
    return h.hexdigest()

def checked(path, expected):
    if path.is_symlink() or not path.is_file() or digest(path) != expected:
        raise ValueError('Missing, linked or hash-mismatched artifact: '+str(path.name))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, default=ROOT/'bundle')
    a=p.parse_args(); b=a.bundle.resolve()
    lock=json.loads((ROOT/'sources.lock.json').read_text())
    checked(b/'bin/dsgb10_rank',lock['engine_binary_sha256'])
    checked(b/'bin/dsfront',lock['frontend_binary_sha256'])
    receipt=json.loads((b/'model/asset-hashes.json').read_text())
    if (receipt.get('model'),receipt.get('revision'),receipt.get('engine_commit')) != (lock['model_repository'],lock['model_revision'],lock['engine_commit']):
        raise ValueError('Asset receipt has incorrect provenance')
    if receipt.get('all_conversion_commands_exit_zero') is not True:
        raise ValueError('Conversion/verification is incomplete')
    required={'config.json','tokenizer.json','engram_hashmap.bin'}
    required.update('rank%d.dsw'%i for i in range(4))
    required.update('engram-l%d-r%dof4.bin'%(layer,i) for i in range(4) for layer in (1,14))
    if not required <= receipt.get('sha256',{}).keys():
        raise ValueError('Missing rank, Engram or tokenizer hashes')
    for name, sha in receipt['sha256'].items():
        if Path(name).name != name:
            raise ValueError('Asset hash names must be flat relative filenames')
        checked(b/'model'/name,sha)
    if not (b/'notices/engine-NOTICE').is_file():
        raise ValueError('The authentic upstream engine NOTICE must be staged')
    vector=b/'vectors/glp39.gguf'
    if vector.exists():
        checked(vector,lock['optional_glp39_sha256'])
    profile={k:lock[k] for k in ('engine_commit','frontend_commit','model_repository','model_revision')}
    profile.update(engine_sha256=lock['engine_binary_sha256'], frontend_sha256=lock['frontend_binary_sha256'],
                   glp39_sha256=lock['optional_glp39_sha256'] if vector.exists() else None,
                   steering_default='off')
    (b/'profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    print('Profile written only after qualified binary and asset hash checks; no image built.')

if __name__=='__main__':
    main()
