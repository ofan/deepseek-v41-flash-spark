#!/usr/bin/env python3
"""Repack an explicitly selected runtime into fresh OCI layers, never inherit history.

Reads validated OCI blobs; does not extract member paths, run image code, download
weights, authenticate, push, deploy, or change visibility. Payloads are opaque.
"""
import argparse
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import tarfile

PACKAGE = 'usr/local/lib/python3.12/dist-packages/'
PACKAGES = {'torch','numpy','numpy.libs','PIL','pillow.libs','safetensors',
            'sympy','mpmath','filelock','networkx','jinja2','markupsafe','fsspec',
            'typing_extensions.py','typing_inspection','nvidia'}
SUPPLEMENTAL_PACKAGES={'torchgen','yaml','_yaml','packaging','cuda','triton','setuptools','pkg_resources','_distutils_hack','distutils-precedence.pth'}
META = {'torch','numpy','pillow','safetensors','sympy','mpmath','filelock',
        'networkx','jinja2','markupsafe','fsspec','typing_extensions','typing_inspection'}
SUPPLEMENTAL_META={'pyyaml','packaging','triton','setuptools','cuda_bindings','cuda_pathfinder','cuda_toolkit'}
APP = {'opt/pico/dsfront':'opt/package/bin/dsfront',
       'opt/pico/vision-tools/vision_encoder.py':'opt/package/vision/vision_encoder.py',
       'opt/pico/vision-tools/image_io.py':'opt/package/vision/image_io.py',
       'opt/pico/vision/inference/vision.py':'opt/package/vision/inference/vision.py',
       'opt/pico/vision/inference/image_processor.py':'opt/package/vision/inference/image_processor.py',
       'opt/pico/vision/inference/config.json':'opt/package/vision/inference/config.json',
       'opt/pico/vision/model.safetensors.index.json':'opt/package/vision/model.safetensors.index.json',
       'opt/pico/vision/vision.safetensors':'opt/package/vision/vision.safetensors',
       'opt/pico/LICENSE':'opt/package/notices/engine-LICENSE'}
SOURCE = 'sha256:edb2bd48c5c146bd33c588bc8fcd0c79d3c3daf9b9084b69c6106ae345fd5fc9'
STAMP = '2026-11-11T00:00:00Z'

def digest(p):
    with Path(p).open('rb') as f:
        return 'sha256:'+hashlib.file_digest(f,'sha256').hexdigest()

def name_safe(name):
    # Archive namespaces are POSIX even on non-POSIX hosts.
    if name.startswith('/') or '..' in PurePosixPath(name).parts:
        raise ValueError('Unsafe archive member name')
    return str(PurePosixPath(name))

def selected(name, supplemental=False):
    """Allowlist runtime dependencies; do not copy inherited application/config trees."""
    if name in APP:
        return True
    p=PurePosixPath(name)
    if any(s in {'__pycache__','test','tests','benchmarks','examples','include','cmake'} for s in p.parts):
        return False
    if 'testing' in p.parts and not supplemental:
        return False
    if p.suffix in {'.pyc','.pyo','.a','.whl'} or p.name in {'direct_url.json'}:
        return False
    if name.startswith(PACKAGE):
        pkg=name[len(PACKAGE):].split('/')[0]
        normalized=pkg.split('-',1)[0].lower()
        return pkg in PACKAGES or supplemental and pkg in SUPPLEMENTAL_PACKAGES or pkg.endswith('.dist-info') and (normalized in META or normalized.startswith('nvidia_') or supplemental and normalized in SUPPLEMENTAL_META)
    if name.startswith(('usr/lib/aarch64-linux-gnu/','usr/lib/python3.12/')):
        return True
    if name.startswith('usr/local/cuda-13.0/targets/sbsa-linux/lib/') and '/stubs/' not in name:
        return True
    if name.startswith(('usr/share/zoneinfo/','etc/ssl/certs/')):
        return True
    if name.startswith('usr/share/doc/') and p.name in {'copyright','LICENSE','NOTICE','COPYING'}:
        return True
    return name in {'usr/bin/python3.12','usr/bin/ldd','usr/sbin/ldconfig.real','usr/sbin/ldconfig'}

def metadata(m):
    return {'mode':m.mode & 0o777,'kind':'file' if m.isfile() else 'symlink' if m.issym() else 'hardlink' if m.islnk() else 'directory',
            'link':m.linkname,'size':m.size}

def stage(manifest, cache, output):
    # All regular-file contents live under numeric names, never archive-supplied paths.
    spool=output/'spool';spool.mkdir(exist_ok=True)
    state={}; dropped=0; seq=0; verified=set()
    for ordinal,layer in enumerate(manifest['layers'],1):
        blob=cache/layer['digest'].split(':')[1]
        if layer['digest'] not in verified:
            if blob.stat().st_size!=layer['size'] or digest(blob)!=layer['digest']:
                raise ValueError('Source blob integrity check failed')
            verified.add(layer['digest'])
        inherited=set(state)
        with tarfile.open(blob,'r|*') as tf:
            for m in tf:
                name=name_safe(m.name)
                parent=posixpath.dirname(name);leaf=posixpath.basename(name)
                if leaf=='.wh..wh..opq':
                    for n in inherited:
                        if n==parent or n.startswith(parent+'/'):
                            state.pop(n,None)
                    continue
                if leaf.startswith('.wh.'):
                    target=posixpath.join(parent,leaf[4:])
                    for n in list(state):
                        if n==target or n.startswith(target+'/'):state.pop(n,None)
                    continue
                if not selected(name):dropped+=1;continue
                if not (m.isfile() or m.isdir() or m.issym() or m.islnk()):
                    raise ValueError('Special runtime member refused')
                # Replacing a non-directory also hides prior descendants.
                if not m.isdir() and state.get(name,{}).get('kind')=='directory':
                    for n in list(state):
                        if n.startswith(name+'/'):state.pop(n,None)
                row=metadata(m)
                if m.isfile():
                    seq+=1;p=spool/str(seq);h=hashlib.sha256()
                    with tf.extractfile(m) as src,p.open('wb') as dst:
                        while b:=src.read(4*1024*1024):dst.write(b);h.update(b)
                    if p.stat().st_size!=m.size:raise ValueError('Truncated member')
                    row.update(payload=str(p),sha256=h.hexdigest())
                elif m.islnk():
                    target=name_safe(m.linkname)
                    if target not in state or state[target]['kind']!='file':
                        raise ValueError('Unresolved runtime hardlink')
                    row=copy.deepcopy(state[target])
                elif m.issym():
                    resolved=posixpath.normpath(posixpath.join(parent,m.linkname)) if not m.linkname.startswith('/') else m.linkname.lstrip('/')
                    if resolved=='..' or resolved.startswith('../'):
                        raise ValueError('Escaping runtime symlink')
                state[name]=row
        print(json.dumps({'layer':ordinal,'selected_members':len(state)}),flush=True)
    for n in state:
        for parent in PurePosixPath(n).parents:
            if str(parent) in state and state[str(parent)]['kind']!='directory':
                raise ValueError('Runtime file beneath a non-directory')
    mapped={APP.get(n,n):r for n,r in state.items()}
    return mapped,{'verified_source_unique_layers':len(verified),'source_layer_occurrences':len(manifest['layers']),'discarded_source_members':dropped}

def add_bytes(state, output, name, data, mode=0o644):
    p=output/'spool'/('generated-'+hashlib.sha256(name.encode()).hexdigest());p.write_bytes(data)
    state[name]={'kind':'file','mode':mode,'link':'','size':len(data),'payload':str(p),'sha256':hashlib.sha256(data).hexdigest()}

def add_file(state,name,path,mode=0o644):
    state[name]={'kind':'file','mode':mode,'link':'','size':path.stat().st_size,'payload':str(path),'sha256':digest(path)[7:]}

def configure(state, output, recipe, engine, notice, vector=None):
    lock=json.loads((recipe/'sources.lock.json').read_text())
    if digest(Path(state['opt/package/bin/dsfront']['payload']))[7:]!=lock['frontend_binary_sha256']:
        raise ValueError('Frontend differs from qualified binary')
    if state['opt/package/vision/vision.safetensors']['sha256']!=lock['vision_pack_sha256']:
        raise ValueError('Vision pack differs from qualified asset')
    if vector is not None:
        if digest(vector)[7:]!=lock['optional_glp39_sha256']:raise ValueError('Unqualified vector')
        add_file(state,'opt/package/vectors/glp39.gguf',vector)
    add_file(state,'opt/package/bin/dsgb10_rank',engine,0o755)
    add_file(state,'opt/package/notices/engine-NOTICE',notice)
    add_file(state,'opt/recipe/entrypoint.py',recipe/'scripts/entrypoint.py',0o755)
    for n in ('LICENSE','NOTICE'):add_file(state,'opt/recipe/'+n,recipe/n)
    for p in sorted((recipe/'licenses').rglob('*')):
        if p.is_file():add_file(state,'opt/recipe/licenses/'+p.relative_to(recipe/'licenses').as_posix(),p)
    vision={n[len('opt/package/vision/'):]:r['sha256'] for n,r in state.items() if n.startswith('opt/package/vision/') and r['kind']=='file'}
    profile={k:lock[k] for k in ('engine_commit','frontend_commit','model_repository','model_revision')}
    profile.update(engine_sha256=digest(engine)[7:],frontend_sha256=lock['frontend_binary_sha256'],
                   vision_files_sha256=vision,vision_pack_sha256=lock['vision_pack_sha256'],steering_default='off',glp39_sha256=lock['optional_glp39_sha256'],
                   qualification='new source rebuild; GPU serving acceptance not rerun')
    add_bytes(state,output,'opt/package/profile.json',(json.dumps(profile,indent=2)+'\n').encode())
    # Do not inherit account files, network configuration, machine IDs or hosts.
    add_bytes(state,output,'etc/passwd',b'root:x:0:0:root:/nonexistent:/usr/bin/python3\n')
    add_bytes(state,output,'etc/group',b'root:x:0:\n')
    for n,t in {'usr/bin/python3':'python3.12','bin':'usr/bin','sbin':'usr/sbin','lib':'usr/lib','lib64':'usr/lib',
                'usr/local/cuda':'cuda-13.0','usr/local/cuda-13.0/lib64':'targets/sbsa-linux/lib'}.items():
        state[n]={'kind':'symlink','mode':0o777,'size':0,'link':t}
    for n in ['tmp','run','run/pico','var/lib/pico','opt/package/model','opt/package/vectors']:
        state[n]={'kind':'directory','mode':0o1777 if n=='tmp' else 0o755,'size':0,'link':''}
    return profile

def write_oci(state,output,receipt,tag):
    oci=output/'oci';blobs=oci/'blobs/sha256';blobs.mkdir(parents=True,exist_ok=True)
    tarpath=output/'runtime.tar'
    with tarfile.open(tarpath,'w',format=tarfile.PAX_FORMAT) as tf:
        parents=set()
        for name in state:
            p=PurePosixPath(name).parent
            while str(p)!='.':parents.add(str(p));p=p.parent
        for name in sorted(parents-state.keys()):
            t=tarfile.TarInfo(name);t.type=tarfile.DIRTYPE;t.mode=0o755;t.uid=t.gid=0;t.mtime=0;tf.addfile(t)
        for name,r in sorted(state.items()):
            t=tarfile.TarInfo(name);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
            if r['kind']=='file':
                t.size=r['size']
                with Path(r['payload']).open('rb') as f:tf.addfile(t,f)
            elif r['kind']=='symlink':t.type=tarfile.SYMTYPE;t.linkname=r['link'];tf.addfile(t)
            else:t.type=tarfile.DIRTYPE;tf.addfile(t)
    diff=digest(tarpath);gz=output/'runtime.tar.gz'
    with tarpath.open('rb') as src,gz.open('wb') as dst:
        with gzip.GzipFile(filename='',mode='wb',fileobj=dst,compresslevel=1,mtime=0) as z:shutil.copyfileobj(src,z,8*1024*1024)
    layer=digest(gz);shutil.copyfile(gz,blobs/layer[7:])
    env=['PATH=/usr/bin:/bin','PYTHONPATH='+('/'+PACKAGE).rstrip('/'),
         'PYTHONDONTWRITEBYTECODE=1','PYTHONUNBUFFERED=1','HOME=/nonexistent',
         'NVIDIA_VISIBLE_DEVICES=all','NVIDIA_DRIVER_CAPABILITIES=compute,utility',
         'LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/cuda/lib64:/usr/lib/aarch64-linux-gnu']
    config={'created':STAMP,'architecture':'arm64','os':'linux','config':{'User':'0:0','Env':env,
             'Entrypoint':['/usr/bin/python3','/opt/recipe/entrypoint.py'],'WorkingDir':'/opt/package',
             'ExposedPorts':{'8888/tcp':{}},'Labels':{'org.opencontainers.image.title':'Pico native vision runtime candidate',
             'org.opencontainers.image.source':'https://github.com/ofan/deepseek-v41-flash-spark',
             'org.opencontainers.image.description':'Sanitized source-rebuilt runtime; external text assets; steering off by default'}},
             'rootfs':{'type':'layers','diff_ids':[diff]},'history':[{'created':STAMP,'created_by':'Explicit runtime allowlist and generic-path engine rebuild'}]}
    raw=json.dumps(config,separators=(',',':')).encode();cd='sha256:'+hashlib.sha256(raw).hexdigest();(blobs/cd[7:]).write_bytes(raw)
    manifest={'schemaVersion':2,'mediaType':'application/vnd.oci.image.manifest.v1+json',
              'config':{'mediaType':'application/vnd.oci.image.config.v1+json','digest':cd,'size':len(raw)},
              'layers':[{'mediaType':'application/vnd.oci.image.layer.v1.tar+gzip','digest':layer,'size':gz.stat().st_size}]}
    raw=json.dumps(manifest,separators=(',',':')).encode();md='sha256:'+hashlib.sha256(raw).hexdigest();(blobs/md[7:]).write_bytes(raw)
    (oci/'oci-layout').write_text('{"imageLayoutVersion":"1.0.0"}\n')
    (oci/'index.json').write_text(json.dumps({'schemaVersion':2,'manifests':[{'mediaType':manifest['mediaType'],'digest':md,'size':len(raw),'annotations':{'org.opencontainers.image.ref.name':tag},'platform':{'os':'linux','architecture':'arm64'}}]})+'\n')
    inventory=[dict(path=n,**{k:v for k,v in r.items() if k!='payload'}) for n,r in sorted(state.items())]
    (output/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    receipt.update(manifest_digest=md,config_digest=cd,layer_digest=layer,layer_bytes=gz.stat().st_size,diff_id=diff,
                   rootfs_tar_bytes=tarpath.stat().st_size,selected_members=len(state),inventory_sha256=digest(output/'inventory.json'),tag=tag)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('manifest','cache','output','recipe','engine','engine-notice'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--tag',required=True);p.add_argument('--vector',type=Path);a=p.parse_args()
    if digest(a.manifest)!=SOURCE:raise ValueError('Unexpected source manifest')
    a.output.mkdir(parents=True,exist_ok=False)
    state,receipt=stage(json.loads(a.manifest.read_bytes()),a.cache,a.output)
    configure(state,a.output,a.recipe,a.engine,a.engine_notice,a.vector)
    (a.output/'state.json').write_text(json.dumps(state))
    receipt.update(source_manifest_digest=SOURCE,engine_sha256=digest(a.engine),new_engine_qualification_required=True,
                   visibility_changed=False,production_touched=False,source_inherited_layers=0)
    write_oci(state,a.output,receipt,a.tag)
if __name__=='__main__':main()
