#!/usr/bin/env python3
"""Retain the inherited runtime license in a fresh, audited supplemental layer.

Only for the fresh allowlist OCI artifact, never as a cleanup of legacy layers.
"""
import argparse,gzip,hashlib,io,json,tarfile,importlib.util
from pathlib import Path

def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def add(oci,license,tag,dependencies=()):
    blobs=oci/'blobs/sha256';idx=json.loads((oci/'index.json').read_text());md=idx['manifests'][0]['digest']
    raw=(blobs/md[7:]).read_bytes();assert sha(raw)==md;m=json.loads(raw)
    assert len(m['layers'])==1, 'Only a fresh single-layer core is accepted'
    raw=(blobs/m['config']['digest'][7:]).read_bytes();assert sha(raw)==m['config']['digest'];c=json.loads(raw)
    assert len(c['history'])==1 and c['history'][0]['created_by']=='Explicit runtime allowlist and generic-path engine rebuild'
    spec=importlib.util.spec_from_file_location('runtime_assembler',Path(__file__).with_name('assemble-runtime.py'));pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
    dependency_files=0
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w',format=tarfile.PAX_FORMAT) as tf:
        t=tarfile.TarInfo('opt/package/notices/runtime-base-LICENSE');t.size=len(license);t.mode=0o644;t.uid=t.gid=t.mtime=0;tf.addfile(t,io.BytesIO(license))
        t=tarfile.TarInfo('usr/lib/ld-linux-aarch64.so.1');t.type=tarfile.SYMTYPE;t.linkname='aarch64-linux-gnu/ld-linux-aarch64.so.1';t.mode=0o777;t.uid=t.gid=t.mtime=0;tf.addfile(t)
        for archive_entry in dependencies:
            archive,namespace=archive_entry if isinstance(archive_entry,tuple) else (archive_entry,'')
            namespace='' if namespace in ('','.') else pack.name_safe(namespace)+'/'
            with tarfile.open(archive,'r|*') as source:
                for member in source:
                    name=pack.name_safe(member.name);target=pack.PACKAGE+namespace+name
                    if not pack.selected(target,supplemental=True):continue
                    if not (member.isdir() or member.isfile()):raise ValueError('Linked/special dependency member refused')
                    t=tarfile.TarInfo(target);t.mode=member.mode & 0o777;t.uid=t.gid=t.mtime=0
                    if member.isdir():t.type=tarfile.DIRTYPE;tf.addfile(t)
                    else:
                        t.size=member.size
                        with source.extractfile(member) as stream:tf.addfile(t,stream)
                        dependency_files+=1
    tar=buf.getvalue();gz=gzip.compress(tar,compresslevel=1,mtime=0);ld=sha(gz);(blobs/ld[7:]).write_bytes(gz)
    c['rootfs']['diff_ids'].append(sha(tar));c['history'].append({'created':c['created'],'created_by':'Generic loader, declared PyTorch dependencies and runtime license'})
    raw=json.dumps(c,separators=(',',':')).encode();cd=sha(raw);(blobs/cd[7:]).write_bytes(raw)
    m['config']['digest']=cd;m['config']['size']=len(raw);m['layers'].append({'mediaType':'application/vnd.oci.image.layer.v1.tar+gzip','digest':ld,'size':len(gz)})
    raw=json.dumps(m,separators=(',',':')).encode();md=sha(raw);(blobs/md[7:]).write_bytes(raw)
    idx['manifests'][0].update(digest=md,size=len(raw));idx['manifests'][0]['annotations']['org.opencontainers.image.ref.name']=tag
    (oci/'index.json').write_text(json.dumps(idx)+'\n')
    return {'manifest_digest':md,'config_digest':cd,'tag':tag,'layer_count':2,'license_layer_digest':ld,'dependency_files':dependency_files,'license_sha256':sha(license),'layer_bytes':sum(x['size'] for x in m['layers'])}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--oci',type=Path,required=True);p.add_argument('--license',type=Path,required=True);p.add_argument('--tag',required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--dependency-tars',type=Path);a=p.parse_args()
    result=add(a.oci,a.license.read_bytes(),a.tag,[(p,p.parent.relative_to(a.dependency_tars).as_posix()) for p in sorted(a.dependency_tars.rglob('*.tar'))] if a.dependency_tars else ());a.receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
