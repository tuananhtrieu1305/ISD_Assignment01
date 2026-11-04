"""Declare Phase3, preserving original web/config bytes before revisions."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/reorganization'
P3=DOCS/'phase3'
P3.mkdir(exist_ok=True)
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,doc):path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if (P3/'declaration.json').exists():raise SystemExit('Already declared; resume from checkpoint instead')
handoff=load(DOCS/'phase2_handoff.json')
assert handoff['status']=='COMPLETE'
rows=[]
for row in load(DOCS/'phase2/canonical_map.json')['files']:
    target=row['target']
    if '/web/' not in target or target!=row['baseline_path']:continue
    original=ROOT/target
    preserved=ROOT/row['project']/'provenance/phase3_originals'/Path(target).relative_to(row['project'])
    preserved.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(original,preserved)
    assert digest(preserved)==row['sha256']
    rows.append({'original_baseline':target,'baseline_path':preserved.relative_to(ROOT).as_posix(),'sha256':row['sha256'],'bytes':row['bytes']})
root_config=ROOT/'render.yaml'
shutil.copyfile(root_config,P3/'render-before.yaml')
save(P3/'preservation_overrides.json',{'files':rows,'root_render_sha256':digest(root_config)})
save(P3/'declaration.json',{'phase':3,'date':'2026-10-31','parent_handoff_sha256':digest(DOCS/'phase2_handoff.json'),'web_originals_preserved':len(rows),'scope':'11web/local/build/Render config/gated cleanup','training_steps':0,'scientific_TEST_forward':0,'deploy_authorized':False})
checkpoint=load(DOCS/'checkpoint.json')
checkpoint.update(active_phase=3,next_phase=3,last_action='Phase3 declared, original web bytes preserved before edits.',next_action='Export static replay data, add web runners, build3React apps, test11web; cleanup only after preservation gates.')
checkpoint['phases']['3']['status']='IN_PROGRESS'
save(DOCS/'checkpoint.json',checkpoint)
print('Phase3 declared; preserved',len(rows),'web originals')
