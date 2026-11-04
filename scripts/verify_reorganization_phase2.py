"""Read-only verification of Phase1/2 handoff files after reorganization."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/reorganization'
failures=[]
counts={}
for phase in [1,2]:
    document=json.loads((DOCS/f'phase{phase}_handoff.json').read_text(encoding='utf-8-sig'))
    assert document['status']=='COMPLETE'
    for row in document['files']:
        path=(ROOT/row['path']).resolve()
        if not path.is_relative_to(ROOT): raise ValueError('Unsafe evidence path')
        if not path.is_file():
            failures.append(row['path'])
            continue
        with path.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=row['sha256'] or path.stat().st_size!=row['bytes']:
            failures.append(row['path'])
    counts[str(phase)]=len(document['files'])
checkpoint=json.loads((DOCS/'checkpoint.json').read_text(encoding='utf-8-sig'))
assert checkpoint['completed_phases']==[1,2]
assert checkpoint['phases']['3']['status']=='NOT_STARTED'
assert checkpoint['active_phase'] is None and checkpoint['next_phase']==3
print(json.dumps({'status':'FAIL' if failures else 'PASS','handoff_files':counts,'failures':failures,'phase2':'COMPLETE','phase3':'NOT_STARTED','scientific_TEST_forward':0,'training_steps':0},ensure_ascii=False))
raise SystemExit(bool(failures))
