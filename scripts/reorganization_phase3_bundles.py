"""Build versioned serving-only bundles from trusted frozen inputs, no model execution."""
from pathlib import Path
import hashlib
import json
import re
import tomllib
import zipfile

ROOT=Path(__file__).resolve().parents[1]
P3=ROOT/'docs/reorganization/phase3'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
views=load(ROOT/'docs/reorganization/phase2/runtime_view_map.json')['files']
maps={p:{r['logical_path']:ROOT/r['source'] for r in views if r['project']==p} for p in ['tieuluan1','tieuluan2','tieuluan3']}
legacy_zip=ROOT/'tieuluan3/deploy/render-v3-r1/api-bundle.zip'
legacy_spec=load(ROOT/'tieuluan3/deploy/render-v3-r1/release.json')
assert sha(legacy_zip.read_bytes())==legacy_spec['archive']['sha256']
base_lock=(ROOT/'tieuluan3/deploy/v3/requirements-cpu.lock').read_text(encoding='utf-8')
cors=next(p for p in tomllib.loads((ROOT/'uv.lock').read_text())['package'] if p['name']=='flask-cors')
hashes=sorted({r['hash'] for r in [cors.get('sdist',{}),*cors.get('wheels',[])] if 'hash' in r})
assert hashes
paper1_lock=base_lock+'\nflask-cors=='+cors['version']+' '+ ' '.join('--hash='+h for h in hashes)+'\n'
releases=[]
for project in ['tieuluan1','tieuluan2','tieuluan3']:
    files={}
    if project in {'tieuluan2','tieuluan3'}:
        with zipfile.ZipFile(legacy_zip) as archive:
            for name in archive.namelist():
                if name=='bundle_manifest.json':continue
                if project=='tieuluan2' and re.search(r'ch06_|ch6_|phase31|agent_catalog|agent_taskset',name):continue
                # Mapped source is authoritative for the new five-chapter serving revision.
                if project=='tieuluan2' and name in maps[project]:files[name]=maps[project][name].read_bytes()
                else:files[name]=archive.read(name)
        for name in ['artifacts/manifests/phase32/registry_v3.json','artifacts/manifests/phase32/samples.json','apps/api/v3/pins.py']:
            files[name]=maps[project][name].read_bytes()
        files['web_entry.py']=b'from apps.api.v3.server import create_app\napp = create_app()\n'
        entry='web_entry:app'
        lock=base_lock
    else:
        allow=['backend/','term_paper/src/','term_paper/deployment/app/']
        for name,path in maps[project].items():
            if name.endswith('.py') and (name in {'term_paper/__init__.py'} or any(name.startswith(p) for p in allow)):
                files[name]=path.read_bytes()
        # Exactly four model/scaler groups from the immutable source registry.
        import ast
        service_source=maps[project]['term_paper/deployment/app/model_service.py'].read_text()
        tree=ast.parse(service_source)
        registry=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MODEL_REGISTRY' for t in n.targets))
        for record in registry.values():
            for name in [record['model'],*[p['path'] for p in record['preprocessors']]]:files[name]=maps[project][name].read_bytes()
        files['train_samples.json']=(ROOT/project/'web/deploy/train_samples.json').read_bytes()
        files['web_entry.py']=b'''import json\nfrom pathlib import Path\nfrom flask import jsonify, abort\nfrom backend.app import app\nSAMPLES=json.loads((Path(__file__).parent/'train_samples.json').read_text())\ndef train_demo(use_case):\n    if use_case not in SAMPLES: abort(404)\n    return jsonify(SAMPLES[use_case])\napp.view_functions['demo']=train_demo\n'''
        entry='web_entry:app';lock=paper1_lock
    files['deploy/v3/requirements-cpu.lock']=lock.encode()
    records=[{'path':name,'sha256':sha(body),'size_bytes':len(body)} for name,body in sorted(files.items())]
    manifest=(json.dumps({'files':records},sort_keys=True,indent=2)+'\n').encode()
    directory=ROOT/project/'web/deploy';directory.mkdir(exist_ok=True)
    archive_path=directory/'api-bundle-r1.zip'
    with zipfile.ZipFile(archive_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,body in sorted(files.items()):archive.writestr(name,body)
        archive.writestr('bundle_manifest.json',manifest)
    release={'project':project,'revision':'reorg-phase3-r1','entrypoint':entry,'archive':{'path':archive_path.relative_to(ROOT).as_posix(),'sha256':sha(archive_path.read_bytes()),'size_bytes':archive_path.stat().st_size},'manifest_sha256':sha(manifest),'file_count':len(files),'expanded_bytes':sum(len(b) for b in files.values()),'requirements_sha256':sha(lock.encode()),'training_steps':0,'scientific_TEST_forward':0,'source_python':[]}
    for record in records:
        name=record['path']
        if not name.endswith('.py') or name=='web_entry.py':continue
        path=maps[project].get(name)
        if path is None:raise ValueError('Missing source parity mapping: '+name)
        # Original bundle may normalize line endings; serialized artifacts are never normalized.
        if path.read_bytes().replace(b'\r\n',b'\n')!=files[name].replace(b'\r\n',b'\n'):raise ValueError('Source parity mismatch: '+name)
        release['source_python'].append({'logical_path':name,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes())})
    (directory/'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    releases.append({'project':project,'files':len(files),'zip_bytes':archive_path.stat().st_size,'release':str((directory/'release.json').relative_to(ROOT))})
    print('Bundle',project,len(files),archive_path.stat().st_size,flush=True)
(P3/'bundle_build.json').write_text(json.dumps({'status':'PASS','bundles':releases,'source_parity':'exact bytes or LF-normalized Python only; artifact bytes unchanged','training_steps':0,'scientific_TEST_forward':0},indent=2)+'\n')
