#!/usr/bin/env python3
"""Replay the complete local patch series and compare every implementation byte."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
def verify():
    manifest=json.loads((ROOT/'patches/manifest.json').read_text())
    names=(ROOT/'patches/series').read_text().splitlines()
    if names!=[r['file'] for r in manifest['patches']]:raise ValueError('Patch series differs from manifest')
    with tempfile.TemporaryDirectory() as d:
        tree=Path(d)/'tree';shutil.copytree(ROOT/'vendor/upstream',tree)
        for row in manifest['patches']:
            patch=ROOT/'patches'/row['file']
            if hashlib.sha256(patch.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Patch digest mismatch')
            subprocess.run(['git','apply','--check',str(patch)],cwd=tree,check=True,capture_output=True)
            subprocess.run(['git','apply',str(patch)],cwd=tree,check=True,capture_output=True)
        target=ROOT/'vendor/engine'
        expected={str(p.relative_to(target)) for p in target.rglob('*') if p.is_file() and p.name!='SOURCE.json'}
        got={str(p.relative_to(tree)) for p in tree.rglob('*') if p.is_file() and p.name!='SOURCE.json'}
        if got!=expected:raise ValueError('Replayed file inventory mismatch')
        for name in expected:
            if (tree/name).read_bytes()!=(target/name).read_bytes():raise ValueError('Replayed byte mismatch: '+name)
            if bool((tree/name).stat().st_mode & 0o111)!=bool((target/name).stat().st_mode & 0o111):raise ValueError('Replayed executable mode mismatch: '+name)
    return len(names),len(expected)
if __name__=='__main__':
    n,f=verify();print(f'PASS: {n} patches reconstruct all {f} vendored production implementation files exactly.')
