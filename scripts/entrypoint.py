#!/usr/bin/env python3
"""One rank per container; no SSH, auto-restart, fleet changes or fallback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

DEFAULT_MAX_OUTPUT_TOKENS = 262144
CONTEXT_TOKENS = 1048576

def output_budget(value):
    n = int(value)
    if not 1 <= n <= CONTEXT_TOKENS:
        raise argparse.ArgumentTypeError('Output budget must be 1..1048576 tokens')
    return n

STEER_VARS = ('WEIGHTLESS_STEER_PATH','WEIGHTLESS_STEER_ALPHA','WEIGHTLESS_STEER_LAYERS')

def steering_environment(parent, mode):
    env=dict(parent)
    for key in STEER_VARS:
        env.pop(key,None)
    # No lossy expert-rerouting shortcut in this lossless serving recipe.
    env.pop('DSGB10_OEA',None)
    if mode=='glp39':
        env.update(WEIGHTLESS_STEER_PATH='/opt/package/vectors/glp39.gguf',
                   WEIGHTLESS_STEER_ALPHA='0.75',
                   WEIGHTLESS_STEER_LAYERS=','.join(str(i) for i in range(1,40)))
    elif mode!='off':
        raise ValueError('Unknown steering mode')
    return env

def check(path, expected):
    with Path(path).open('rb') as stream:
        actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if not expected or actual!=expected:
        raise ValueError('Artifact hash mismatch: '+Path(path).name)

def command_plan(rank, fleet, listen, spill, vision=True, max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS):
    if rank not in range(4):
        raise ValueError('Rank must be 0..3')
    max_output_tokens=output_budget(max_output_tokens)
    socket='/run/pico/engine.sock'
    model='/opt/package/model'
    engine=['/opt/package/bin/dsgb10_rank','--fleet',fleet,'--rank',str(rank),
            '--mode','serve','--socket',socket,'--weights',f'{model}/rank{rank}.dsw',
            '--hashmap',model+'/engram_hashmap.bin','--shard1',f'{model}/engram-l1-r{rank}of4.bin',
            '--shard14',f'{model}/engram-l14-r{rank}of4.bin','--max-ctx','1048576',
            '--slots','16','--big-slots','0','--session-gib','3','--session-margin-gib','2',
            '--disk-gib','160','--disk-dir',spill,'--keep-gib','0',
            '--setenv','DSGB10_BUDGET=1','--setenv','DSGB10_DRAFT1=6',
            '--setenv','DSGB10_WIDE=64','--setenv','DSGB10_WIDE_COST=24,2.2,57,1.1']
    commands=[engine]
    if rank==0:
        commands.append(['/opt/package/bin/dsfront','serve','--listen',listen,'--engine-socket',socket,
                         '--tokenizer',model+'/tokenizer.json','--model-name','deepseek-v4.1-flash',
                         '--encoding','1017','--temperature','1','--top-p','1',
                         '--max-tokens',str(max_output_tokens),
                         '--session-cache-tokens','160000000'])
    if rank==0 and vision:
        commands[1].extend(['--vision-addr','127.0.0.1:18950'])
        commands.insert(0,['python3','/opt/package/vision/vision_encoder.py','--model','/opt/package/vision',
                           '--device','cuda','--host','127.0.0.1','--port','18950','--max-images','16'])
    return commands

def supervise(commands, env):
    children=[]
    stopping=False
    def stop(*_):
        nonlocal stopping
        stopping=True
        for child in children:
            if child.poll() is None:
                child.terminate()
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    failed=False
    try:
        for command in commands:
            if stopping:
                break
            children.append(subprocess.Popen(command,env=env))
        while not stopping:
            if any(c.poll() is not None for c in children):
                failed=True
                break
            time.sleep(0.25)
    finally:
        stop()
        deadline=time.monotonic()+90
        for child in children:
            try:
                child.wait(timeout=max(0.1,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    return 1 if failed else 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rank',type=int,choices=range(4),required=True)
    p.add_argument('--fleet',required=True)
    p.add_argument('--steering',choices=('off','glp39'),default='glp39',
                   help='GLP-39 ON by default (alpha 0.75, layers 1-39); off explicitly disables steering')
    p.add_argument('--max-output-tokens', type=output_budget, default=DEFAULT_MAX_OUTPUT_TOKENS,
                   help='Frontend default and cap for output tokens (262144); input plus output still fits 1048576 context')
    p.add_argument('--no-vision',action='store_true',help='Disable image side encoder/frontend ingress')
    p.add_argument('--listen',default='0.0.0.0:8888')
    p.add_argument('--spill',default='/var/lib/pico')
    a=p.parse_args()
    profile=json.loads(Path('/opt/package/profile.json').read_text())
    check('/opt/package/bin/dsgb10_rank',profile['engine_sha256'])
    check('/opt/package/bin/dsfront',profile['frontend_sha256'])
    if not a.no_vision and a.rank==0:
        for name,sha in profile['vision_files_sha256'].items():
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Unsafe vision path')
            check('/opt/package/vision/'+name,sha)
        check('/opt/package/vision/vision.safetensors',profile['vision_pack_sha256'])
    if a.steering=='glp39':
        check('/opt/package/vectors/glp39.gguf',profile.get('glp39_sha256'))
    if not Path(a.fleet).is_file():
        p.error('A site-specific fleet file must be supplied')
    Path('/run/pico').mkdir(parents=True,exist_ok=True)
    Path(a.spill).mkdir(parents=True,exist_ok=True)
    env=steering_environment(os.environ,a.steering)
    env.update(VISION_SDPA_OPT_IN='0',VISION_PRELOAD='1')
    return supervise(command_plan(a.rank,a.fleet,a.listen,a.spill,vision=not a.no_vision,max_output_tokens=a.max_output_tokens),env)

if __name__=='__main__':
    raise SystemExit(main())
