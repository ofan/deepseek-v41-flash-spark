#!/usr/bin/env python3
"""Verify and stage the in-repository, privacy-reviewed engine implementation."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
def verify_source(root):
    root=Path(root)
    trusted=json.loads((ROOT/'vendor/engine/SOURCE.json').read_text())
    got=json.loads((root/'SOURCE.json').read_text())
    if got!=trusted:raise ValueError('Source manifest differs from the pinned in-repository manifest')
    wanted=set(got['files'])
    for name,row in got['files'].items():
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe source path')
        p=root/rel
        if p.is_symlink() or any(q.is_symlink() for q in p.parents) or not p.is_file():raise ValueError('Missing or linked source')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Source hash mismatch: '+name)
        if bool(p.stat().st_mode & 0o111)!=row['executable']:raise ValueError('Source executable mode mismatch: '+name)
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='SOURCE.json'}
    if actual!=wanted:raise ValueError('Source tree has unexpected or missing files')
    return got['source_commit']
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--verify',type=Path);g.add_argument('--stage',type=Path)
    a=p.parse_args()
    if a.verify:print('Verified source '+verify_source(a.verify));return
    source=ROOT/'vendor/engine';verify_source(source)
    for name in ['engine','frontend']:
        if (a.stage/name).exists():p.error('Refusing existing source destination: '+name)
    for name in ['engine','frontend']:
        shutil.copytree(source,a.stage/name)
        verify_source(a.stage/name)
    print('Staged engine/frontend from pinned vendored source; no network fetch.')
if __name__=='__main__':main()
