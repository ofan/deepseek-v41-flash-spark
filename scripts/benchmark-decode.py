#!/usr/bin/env python3
"""Short existing prose/code decode suite. Explicit endpoint required; no deployments."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time
import types
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/engine/ds41f-4xgx10-switchless/bench'))
import bench
import multistream

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True,help='Your direct frontend URL ending in /v1')
    p.add_argument('--model',default='deepseek-v4.1-flash')
    p.add_argument('--max-tokens',type=int,default=256)
    p.add_argument('--timeout',type=int,default=60)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if not 2<=a.max_tokens<=512 or not 1<=a.timeout<=120:p.error('Bounded runs only: 2..512 tokens and 1..120 seconds')
    original=bench.post_stream
    multistream.post_stream=lambda u,k,b:original(u,k,b,timeout=a.timeout)
    prompts=dict(bench.DECODE_PROMPTS)
    result={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'max_tokens':a.max_tokens,
            'repetitions':1,'prompt_sha256':{k:hashlib.sha256(prompts[k].encode()).hexdigest() for k in ('prose','code')},'configurations':[]}
    for kind in ('prose','code'):
        multistream.DECODE_PROMPTS={kind:prompts[kind]}
        for streams in (1,4,8,16):
            cfg=types.SimpleNamespace(url=a.url,key='',model=a.model,max_tokens=a.max_tokens)
            rows=multistream.http_streams(cfg,streams)
            if any(r['error'] or r['tokens']<2 for r in rows):
                raise RuntimeError('Stop on error or missing token usage; no further configurations run')
            stats=multistream.report(streams,rows)
            result['configurations'].append({'prompt_type':kind,'summary':stats,'requests':rows})
            a.out.write_text(json.dumps(result,indent=2)+'\n');time.sleep(2)
    result['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['errors']=0
    a.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
