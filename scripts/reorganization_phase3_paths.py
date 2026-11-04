"""Versioned source-location overlay after removal of inactive web/reference folders."""
from pathlib import Path
import hashlib
import json
import shutil
ROOT=Path(__file__).resolve().parents[1]
P3=ROOT/'docs/reorganization/phase3'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
canonical={}
for name in ['__init__.py','model_service.py','schemas.py','server.py']:
    old=f'tieuluan1/web/legacy_runtime/app/{name}'
    source=ROOT/f'tieuluan1/provenance/phase3_originals/web/legacy_runtime/app/{name}'
    destination=ROOT/f'tieuluan1/src/term_paper/deployment/app/{name}'
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():assert sha(destination)==sha(source)
    else:shutil.copyfile(source,destination)
    canonical[old]=destination.relative_to(ROOT).as_posix()
overrides={r['original_baseline']:r['baseline_path'] for r in load(P3/'preservation_overrides.json')['files']}
rows=[]
for r in load(ROOT/'docs/reorganization/phase2/runtime_view_map.json')['files']:
    source=r['source']
    if '/web/' not in source:continue
    project=source.split('/')[0]
    candidate=canonical.get(source) or overrides.get(source) or f'{project}/provenance/phase3_originals/'+source[len(project)+1:]
    path=ROOT/candidate
    if path.exists() and sha(path)==r['sha256'] and candidate!=source:
        rows.append({'target':r['target'],'original_source':source,'source':candidate,'sha256':r['sha256'],'bytes':r['bytes']})
    elif not (ROOT/source).exists():raise FileNotFoundError(source)
(P3/'runtime_source_overlay.json').write_text(json.dumps({'parent':'docs/reorganization/phase2/runtime_view_map.json','files':rows,'count':len(rows),'semantics':'source location only; logical target and original byte hash unchanged'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
release=ROOT/'tieuluan1/web/deploy/release.json'
doc=load(release)
changes=[]
for row in doc['source_python']:
    if row['path'] in canonical:
        old=row['path'];row['path']=canonical[old]
        assert sha(ROOT/row['path'])==row['sha256']
        changes.append({'from':old,'to':row['path'],'sha256':row['sha256']})
if changes:
    before=release.read_bytes()
    (release.parent/'release-r1-before-cleanup.json').write_bytes(before)
    doc['revision']='reorg-phase3-r2-source-paths'
    doc['parent_release_sha256']=hashlib.sha256(before).hexdigest()
    release.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P3/'post_cleanup_source_relocation.json').write_text(json.dumps({'status':'PASS','canonical_sources':canonical,'release_changes':changes,'runtime_overlays':len(rows),'bundle_archive_bytes_changed':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Source overlay:',len(rows),'aliases; paper1 canonical service files:',len(canonical))
