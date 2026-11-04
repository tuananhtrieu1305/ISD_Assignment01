"""Preserve active r8 prompt/UI sources before adding a shared source policy."""
from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parents[2]
target=P/'provenance/before_source_policy_r9'
assert not (target/'preservation.json').exists(),'Do not overwrite the r8 archive'
paths=list((P/'notebooks').glob('*.ipynb'))+list((P/'web/backend/project01_llm_v2').glob('*.py'))
paths+=list((P/'web/frontend/src').glob('*'))+list((P/'web/frontend/dist').rglob('*'))
paths+=[P/'artifacts/llm_v2/phase2/source_exports.json',P/'docs/llm_v2/architecture.md',P/'AGENTS.md',P.parent/'docs/final_project01/llm_v2/checkpoint.json']
rows=[]
for source in paths:
    if not source.is_file():continue
    relative=source.relative_to(P) if source.is_relative_to(P) else Path('root_docs/checkpoint.json')
    dest=target/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    digest=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
    rows.append({'path':source.relative_to(P.parent).as_posix(),'archive':dest.relative_to(P.parent).as_posix(),'sha256':digest})
(target/'preservation.json').write_text(json.dumps({'revision':'source-verification-r9','files':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preserved':len(rows),'API_calls':0}))
