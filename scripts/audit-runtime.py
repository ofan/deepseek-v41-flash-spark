#!/usr/bin/env python3
"""Scan a new OCI artifact offline. Emit redacted findings, never matched values.

Does not authorize publication. Model/tensor/vocabulary contents remain opaque;
only their names, lengths and cryptographic hashes are recorded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

PATTERNS={
 'internal-domain':re.compile(rb'lab'+rb'\.tf\b',re.I),
 'tailnet-domain':re.compile(rb'\.ts'+rb'\.net\b',re.I),
 'internal-routing':re.compile(rb'llm'+rb'[-_]proxy',re.I),
 'home-path':re.compile(rb'/(?:home|Users)/[^\x00\s/\"\x27:<>]+'),
 'credential-value':re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----'),
 'credential-location':re.compile(rb'(?:\.'+rb'ssh/(?:id_[\w.-]+|authorized_keys|known_hosts)|\.aws/(?:credentials|config)|\.kube/config|\.docker/config\.json|\.git-credentials|\.netrc\b|run/secrets/)',re.I),
}
IPS=re.compile(rb'(?<![\w.])(?:10|172|192|100)\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![\w.])')
OPAQUE=re.compile(r'(?:\.(?:safetensors|gguf|dsw|pt|pth|npy|npz)|(?:^|/)(?:tokenizer|vocab|merges|special_tokens)[^/]*)$',re.I)

def scan(b):
    hits=[]
    for kind,rx in PATTERNS.items():
        for m in rx.finditer(b):hits.append({'kind':kind,'offset':m.start(),'match_sha256':hashlib.sha256(m.group()).hexdigest()})
    for m in IPS.finditer(b):
        a=list(map(int,m.group().split(b'.')))
        if all(x<256 for x in a) and (a[0]==10 or a[:2]==[192,168] or a[0]==172 and 16<=a[1]<=31 or a[0]==100 and 64<=a[1]<=127):
            hits.append({'kind':'private-address','offset':m.start(),'match_sha256':hashlib.sha256(m.group()).hexdigest()})
    return hits

def hsh(p):
    with p.open('rb') as f:return 'sha256:'+hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--oci',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--reuse-layer-report',type=Path,help='Reuse scan results only for identical verified layer blob digests');a=p.parse_args()
    index=json.loads((a.oci/'index.json').read_text());md=index['manifests'][0]['digest'];blobs=a.oci/'blobs/sha256'
    mp=blobs/md[7:];assert hsh(mp)==md;manifest=json.loads(mp.read_text());cp=blobs/manifest['config']['digest'][7:];assert hsh(cp)==manifest['config']['digest']
    report={'manifest_digest':md,'config_digest':hsh(cp),'config_findings':scan(cp.read_bytes()),'layers':[],
            'method':'Every path/link and all non-payload regular-file bytes, including ELF files; overlapping streaming chunks; no extraction or execution',
            'visibility_changed':False,'publication_allowed':False}
    reused={}
    if a.reuse_layer_report:
        prior=json.loads(a.reuse_layer_report.read_text())
        if prior.get('method')!=report['method']:raise ValueError('Incompatible prior scan method')
        reused={row['digest']:row for row in prior['layers']}
    for layer in manifest['layers']:
        bp=blobs/layer['digest'][7:];assert hsh(bp)==layer['digest'] and bp.stat().st_size==layer['size']
        if layer['digest'] in reused:
            row=dict(reused[layer['digest']],reused_from_manifest=prior['manifest_digest']);report['layers'].append(row);continue
        row={'digest':layer['digest'],'members':0,'regular_files_scanned':0,'opaque_payloads':[],'findings':[],'bytes_scanned':0}
        names=[]
        with tarfile.open(bp,'r|*') as t:
            for m in t:
                row['members']+=1;names.append(m.name)
                path_hits=scan((m.name+'\n'+m.linkname).encode())
                if m.name.startswith(('home/','root/','tmp/')) and m.isfile():path_hits.append({'kind':'unexpected-personal-or-temp-content'})
                if re.search(r'(^|/)(?:evidence|operations|\.ssh|\.aws|\.git)(?:/|$)',m.name):path_hits.append({'kind':'unexpected-operational-path'})
                if path_hits:row['findings'].append({'path':m.name,'where':'header','hits':path_hits})
                if not m.isfile():continue
                if OPAQUE.search(m.name):row['opaque_payloads'].append({'path':m.name,'bytes':m.size});continue
                row['regular_files_scanned']+=1
                hits=[];total=0;carry=b''
                with t.extractfile(m) as f:
                    while block:=f.read(4*1024*1024):
                        chunk=carry+block;start=total-len(carry)
                        for hit in scan(chunk):
                            offset=hit['offset']+start
                            if total==0 or offset+1024>=total:
                                hits.append(dict(hit,offset=offset))
                        total+=len(block);carry=chunk[-1024:]
                row['bytes_scanned']+=total
                if hits:
                    unique={(h['kind'],h['offset']):h for h in hits}
                    row['findings'].append({'path':m.name,'where':'content','hits':list(unique.values())})
        row['name_index_sha256']='sha256:'+hashlib.sha256(('\n'.join(names)+'\n').encode()).hexdigest();report['layers'].append(row)
    report['finding_file_count']=sum(len(l['findings']) for l in report['layers'])
    report['verdict']='BLOCKED' if report['finding_file_count'] or report['config_findings'] else 'NO_PATTERN_FINDINGS'
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('manifest_digest','verdict','finding_file_count')}))
if __name__=='__main__':main()
