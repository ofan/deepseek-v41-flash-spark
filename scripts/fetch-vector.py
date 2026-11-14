#!/usr/bin/env python3
"""Explicit optional GLP-39 acquisition; never run as part of build by default."""
import argparse
import hashlib
from pathlib import Path
import json
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
URL='https://huggingface.co/msuiche/DeepSeek-V4.1-Flash-1017-abliterated-cyber-GLP-39-L1-39-a0.75/resolve/main/glp.deepseek-v41-flash-1017-GLP-39-L1-39-a0.75.gguf'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    lock=json.loads((ROOT/'sources.lock.json').read_text())
    out=ROOT/'bundle/vectors/glp39.gguf'
    if not a.execute:
        print(json.dumps({'mode':'plan-only','url':URL,'sha256':lock['optional_glp39_sha256']}));return
    if out.exists():p.error('Refusing an existing vector')
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix('.partial')
    try:
        with urllib.request.urlopen(URL,timeout=60) as response,tmp.open('xb') as f:
            total=0
            while chunk:=response.read(1024*1024):
                total+=len(chunk)
                if total>64*1024*1024:raise ValueError('Unexpectedly large vector')
                f.write(chunk)
        with tmp.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=lock['optional_glp39_sha256']:raise ValueError('Wrong authentic vector hash')
        tmp.rename(out)
        print('Authentic GLP-39 verified. Default ON: alpha 0.75, layers 1-39; opt out with --steering off.')
    finally:
        if tmp.exists():tmp.unlink()

if __name__=='__main__':main()
