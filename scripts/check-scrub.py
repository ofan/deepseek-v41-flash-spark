#!/usr/bin/env python3
"""Scan tracked/scaffold text only; no network, serving calls or model inputs."""
from pathlib import Path
import argparse
import json
import subprocess
import re
import sys

ROOT=Path(__file__).resolve().parents[1]

PATTERNS = {
    'internal-domain': re.compile('lab'+r'\.tf', re.I),
    'internal-routing-reference': re.compile('llm'+'-proxy', re.I),
    'tailnet-domain': re.compile(r'\.'+'ts'+r'\.net', re.I),
    'credential-path': re.compile(r'(?:/run/'+r'secrets/|\.se'+r'crets/|\.s'+r'sh/|/gh/'+r'hosts\.yml)', re.I),
    'cloud-credential-path': re.compile(r'(?<!\\)(?:\.a'+r'ws/(?:credentials|config)|\.ku'+r'be/config|\.do'+r'cker/config\.json|\.net'+r'rc\b|\.config/gcl'+r'oud/)', re.I),
    'private-ipv6': re.compile(r'(?<![0-9a-f:])(?:fd|fc)[0-9a-f]{2}:[0-9a-f:]{4,}', re.I),
    'cloud-access-secret': re.compile(r'A'+'KIA[0-9A-Z]{16}|A'+'SIA[0-9A-Z]{16}'),
    'personal-home-path': re.compile(r'/(?:home|Users)/'),
    'access-secret': re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'special-token-string': re.compile(r'<[|｜]|place_'+'holder_mm_span|deepseek_'+'image'),
}

def problems(text, allow_protocol=False):
    found=[name for name,rx in PATTERNS.items() if rx.search(text) and not (allow_protocol and name=='special-token-string')]
    for value in re.findall(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])',text):
        o=[int(n) for n in value.split('.')]
        if any(n>255 for n in o):
            continue
        if (o[0]==10 or o[:2]==[192,168] or o[0]==172 and 16<=o[1]<=31
                or o[0]==100 and 64<=o[1]<=127):
            found.append('nonpublishable-network-address')
    return sorted(set(found))

def history_problems(root):
    rows=subprocess.check_output(['git','-C',str(root),'rev-list','--objects','--all'],text=True).splitlines()
    issues=[];counts={'objects':len(rows),'blobs':0,'commits':0,'tags':0}
    # One batched Git process avoids hundreds of shell/startup calls for vendored source.
    proc=subprocess.Popen(['git','-C',str(root),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for row in rows:
            oid,_,name=row.partition(' ')
            proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
            header=proc.stdout.readline().decode().split();kind=header[1];size=int(header[2])
            raw=proc.stdout.read(size);assert proc.stdout.read(1)==b'\n'
            if kind not in ('blob','commit','tag'):continue
            counts[{'blob':'blobs','commit':'commits','tag':'tags'}[kind]]+=1
            allow=kind=='blob' and (name.startswith('vendor/') or name.startswith('patches/'))
            for category in problems(raw.decode('utf-8',errors='replace'),allow_protocol=allow):
                issues.append({'object':oid,'kind':kind,'category':category})
    finally:
        proc.stdin.close();proc.stdout.close();proc.wait()
    counts['forbidden_matches']=len(issues)
    return counts,issues

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--history',action='store_true',help='Also inspect all reachable Git blobs/commit metadata without printing values')
    args=p.parse_args()
    issues=[]; count=0
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or any(p in {'.git','work','bundle','build','dist','__pycache__'} for p in path.relative_to(ROOT).parts):
            continue
        text=path.read_text()
        count+=1
        rel=path.relative_to(ROOT)
        for kind in problems(text,allow_protocol=rel.parts[0] in {'vendor','patches'}):
            issues.append((str(path.relative_to(ROOT)),kind))
    for name,kind in issues:
        print(name+': '+kind)
    print(f'Scanned {count} recipe/source text files; {len(issues)} forbidden-content matches.')
    if args.history:
        counts,history_issues=history_problems(ROOT)
        print('Reachable Git history: '+json.dumps(counts,sort_keys=True))
        for row in history_issues:print(json.dumps(row,sort_keys=True))
        issues.extend(history_issues)
    return bool(issues)

if __name__=='__main__':
    sys.exit(main())
