"""Preserve r7 sources before the combined demo revision; never touch API/cache data."""
from pathlib import Path
import hashlib,json,shutil

P=Path(__file__).resolve().parents[2]
target=P/'provenance/before_full_demo_r8'
if (target/'preservation.json').exists():
    raise RuntimeError('Already preserved; do not overwrite the original revision')
files=list((P/'notebooks').glob('*.ipynb'))
files+=list((P/'web/backend/project01_llm_v2').glob('*.py'))
files+=list((P/'web/frontend/src').glob('*'))
files+=list((P/'web/frontend/dist').rglob('*'))
files+=[P/'artifacts/llm_v2/phase2/source_exports.json',P/'docs/llm_v2/architecture.md',P.parent/'docs/final_project01/llm_v2/checkpoint.json']
records=[]
for source in files:
    if not source.is_file():continue
    rel=source.relative_to(P) if source.is_relative_to(P) else Path('root_docs/checkpoint.json')
    destination=target/rel
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    assert hashlib.sha256(destination.read_bytes()).hexdigest()==sha
    records.append({'path':str(source.relative_to(P.parent)).replace('\\','/'),'archive':str(destination.relative_to(P.parent)).replace('\\','/'),'sha256':sha})
(target/'preservation.json').write_text(json.dumps({'revision':'full-demo-r8','files':records,'new_API_calls':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preserved':len(records),'new_API_calls':0}))
