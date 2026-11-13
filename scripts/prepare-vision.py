#!/usr/bin/env python3
"""Stage vision from pinned PUBLIC checkpoint + fork. Plan-only unless --execute.

Uses the fork's exact range extractor; never reconverts text rank files.
Requires a separately acquired pinned checkpoint. Does not print tensor values.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from source_tree import verify_source

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def header(p):
    with p.open('rb') as f:
        raw=f.read(8)
        if len(raw)!=8:raise ValueError('Truncated safetensors header')
        n=struct.unpack('<Q',raw)[0]
        if not 2<=n<=16*1024*1024:raise ValueError('Unsafe header size')
        raw=f.read(n)
        if len(raw)!=n:raise ValueError('Truncated safetensors header')
    return raw,json.loads(raw)

def inventory(checkpoint,index):
    selected={n:s for n,s in index['weight_map'].items()
              if n.startswith(('vision.','aligner.')) or n in ('image_start','image_newline','image_end')}
    if len(selected)!=266:raise ValueError('Expected exactly 266 native vision tensors')
    heads={}
    for shard in sorted(set(selected.values())):
        if Path(shard).name!=shard:raise ValueError('Non-flat checkpoint shard name')
        heads[shard]=header(checkpoint/shard)
    tensors=[]
    for name,shard in sorted(selected.items()):
        h=heads[shard][1][name]
        if h['dtype']!='BF16':raise ValueError('Expected BF16 vision tensors')
        tensors.append(dict(name=name,shard=shard,dtype=h['dtype'],shape=h['shape'],data_offsets=h['data_offsets']))
    payload=sum(t['data_offsets'][1]-t['data_offsets'][0] for t in tensors)
    if payload!=970536960:raise ValueError('Unexpected vision payload size')
    return tensors,heads

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--checkpoint-revision',required=True)
    p.add_argument('--source',type=Path,default=ROOT/'work/source/engine')
    p.add_argument('--output',type=Path,default=ROOT/'bundle/vision')
    p.add_argument('--execute',action='store_true')
    a=p.parse_args();lock=json.loads((ROOT/'sources.lock.json').read_text())
    if a.checkpoint_revision!=lock['model_revision']:p.error('Wrong checkpoint revision')
    source=a.source.resolve();ck=a.checkpoint.resolve();out=a.output.resolve()
    tools=source/lock['source_directory']/'tools/vision'
    if not a.execute:
        print(json.dumps({'mode':'plan-only','source_commit':lock['engine_commit'],
            'checkpoint_revision':lock['model_revision'],'extractor':str(tools/'extract_pack.py'),
            'output':str(out),'expected_pack_sha256':lock['vision_pack_sha256'],
            'stages':['verify source','read checkpoint headers only','run exact pinned public range extractor if pack absent',
                      'verify full pack hash','stage publisher modules and fork helpers','write complete file-hash receipt']},indent=2))
        return
    if verify_source(source)!=lock['engine_commit']:p.error('Wrong pinned vision source')
    # Pre-obtained snapshot acquisition at pinned revision remains operator responsibility.
    out.mkdir(parents=True,exist_ok=True)
    receipt=out/'asset-hashes.json'
    if receipt.exists():p.error('Refusing an already receipted vision directory')
    pack=out/'vision.safetensors'
    if not pack.exists():
        inv,heads=inventory(ck,json.loads((ck/'model.safetensors.index.json').read_text()))
        staging=ROOT/'work/vision-headers'
        staging.mkdir(parents=True,exist_ok=True)
        for name,(raw,_) in heads.items():(staging/(name+'.header.json')).write_bytes(raw)
        ip=staging/'inventory.json';ip.write_text(json.dumps({'tensors':inv}))
        # Extractor fetches exact pinned HTTP206 tensor ranges, not the full model.
        subprocess.run(['python3',str(tools/'extract_pack.py'),'--inventory',str(ip),'--headers',str(staging),'--out',str(out)],check=True)
    if sha(pack)!=lock['vision_pack_sha256']:p.error('Pack is not byte-identical to qualified pack; do not bypass hash guard')
    (out/'inference').mkdir(exist_ok=True)
    for name in ('vision.py','image_processor.py'):
        shutil.copyfile(ck/'inference'/name,out/'inference'/name)
    shutil.copyfile(ck/'config.json',out/'config.json')
    for name in ('vision_encoder.py','image_io.py'):
        shutil.copyfile(tools/name,out/name)
    # Use only the compact pack; never retain the original full-model shard index here.
    raw,h=header(pack)
    names=[n for n in h if n!='__metadata__']
    if len(names)!=lock['vision_tensor_count']:p.error('Wrong compact pack tensor count')
    (out/'model.safetensors.index.json').write_text(json.dumps({'metadata':{'total_size':lock['vision_payload_bytes']},
        'weight_map':{n:'vision.safetensors' for n in names}},indent=2)+'\n')
    hashes={str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f!=receipt}
    receipt.write_text(json.dumps({'model':lock['model_repository'],'revision':lock['model_revision'],
        'engine_commit':lock['engine_commit'],'pack_sha256':lock['vision_pack_sha256'],'sha256':hashes},indent=2)+'\n')
    print('Exact pack verified; publisher code and fork helpers staged. No text weights rewritten.')

if __name__=='__main__':main()
