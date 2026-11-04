"""Current read-only handoff/UI/source integrity verifier; never train or open TEST."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/reorganization'

# Notebook revision preserves historical records at versioned archive paths.
# The current verifier checks both the archived receipts and active notebooks.
_notebook_checkpoint=ROOT/'docs/notebook_revision/v1/checkpoint.json'
if _notebook_checkpoint.exists() and json.loads(_notebook_checkpoint.read_text())['status']=='COMPLETE':
    import runpy
    runpy.run_path(str(ROOT/'scripts/verify_notebooks_inline.py'),run_name='__main__')
    raise SystemExit(0)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
failures=[];counts={}
for phase in [1,2,3]:
    handoff=load(DOCS/f'phase{phase}_handoff.json')
    assert handoff['status']=='COMPLETE'
    for r in handoff['files']:
        path=(ROOT/r['path']).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or path.stat().st_size!=r['bytes'] or sha(path)!=r['sha256']:
            failures.append(r['path'])
    counts[str(phase)]=len(handoff['files'])
for build in load(DOCS/'phase3/build_verification.json')['projects']:
    for r in build['frontend_source']+build['dist']:
        if sha(ROOT/r['path'])!=r['sha256']:failures.append(r['path'])
for project in ['tieuluan1','tieuluan2','tieuluan3']:
    release=load(ROOT/project/'web/deploy/release.json')
    if sha(ROOT/release['archive']['path'])!=release['archive']['sha256']:failures.append(release['archive']['path'])
    for r in release['source_python']:
        if sha(ROOT/r['path'])!=r['sha256']:failures.append(r['path'])
checkpoint=load(DOCS/'checkpoint.json')
assert checkpoint['status']=='COMPLETE' and checkpoint['completed_phases']==[1,2,3]
assert checkpoint['active_phase'] is None and checkpoint['active_processes']==[]
print(json.dumps({'status':'FAIL' if failures else 'PASS','handoff_files':counts,'current_frontend_and_serving_sources':'verified','failures':failures,'scope':'sealed handoffs/current UI and serving source/archive integrity; original scientific full read-back is the sealed Phase3 receipt','training_steps':0,'scientific_TEST_forward':0},ensure_ascii=False))
raise SystemExit(bool(failures))
