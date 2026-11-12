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
    'personal-home-path': re.compile(r'/(?:home|Users)/'),
    'access-secret': re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'special-token-string': re.compile(r'<[|｜]|place_'+'holder_mm_span|deepseek_'+'image'),
}

def problems(text):
    found=[name for name,rx in PATTERNS.items() if rx.search(text)]
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
    issues=[]; counts={'objects':len(rows),'blobs':0,'commits':0,'tags':0}
    for row in rows:
        oid,_,name=row.partition(' ')
        kind=subprocess.check_output(['git','-C',str(root),'cat-file','-t',oid],text=True).strip()
        if kind not in ('blob','commit','tag'):continue
        counts[{'blob':'blobs','commit':'commits','tag':'tags'}[kind]]+=1
        raw=subprocess.check_output(['git','-C',str(root),'cat-file',kind,oid])
        # All files in this source-only recipe must be inspectable text; no opaque payload exceptions.
        text=raw.decode('utf-8',errors='replace')
        for category in problems(text):
            issues.append({'object':oid,'kind':kind,'category':category})
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
        for kind in problems(text):
            issues.append((str(path.relative_to(ROOT)),kind))
    for name,kind in issues:
        print(name+': '+kind)
    print(f'Scanned {count} scaffold text files; {len(issues)} forbidden-content matches.')
    if args.history:
        counts,history_issues=history_problems(ROOT)
        print('Reachable Git history: '+json.dumps(counts,sort_keys=True))
        for row in history_issues:print(json.dumps(row,sort_keys=True))
        issues.extend(history_issues)
    return bool(issues)

if __name__=='__main__':
    sys.exit(main())
