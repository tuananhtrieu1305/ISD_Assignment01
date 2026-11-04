"""Preserve r9 before the user-requested four-generation verifier revision."""
from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parents[2];ROOT=P.parent
target=P/'provenance/before_semantic_verifier_r10'
assert not (target/'preservation.json').exists(),'Original r9 archive already exists'
files=list((P/'notebooks').glob('*.ipynb'))+list((P/'web/backend/project01_llm_v2').glob('*.py'))
files+=list((P/'web/frontend/src').glob('*'))+list((P/'web/frontend/dist').rglob('*'))
files+=[P/'docs/llm_v2/runtime_config.json',P/'docs/llm_v2/architecture.md',P/'AGENTS.md',ROOT/'AGENTS.md',
        ROOT/'docs/final_project01/llm_v2/checkpoint.json',P/'artifacts/llm_v2/phase2/source_exports.json']
rows=[]
for source in files:
    if not source.is_file():continue
    relative=source.relative_to(P) if source.is_relative_to(P) else Path('root_files')/source.relative_to(ROOT)
    dest=target/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    sha=hashlib.sha256(source.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==sha
    rows.append({'path':source.relative_to(ROOT).as_posix(),'archive':dest.relative_to(ROOT).as_posix(),'sha256':sha})
(target/'preservation.json').write_text(json.dumps({'revision':'semantic-verifier-r10','files':rows,'API_calls':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preserved':len(rows),'API_calls':0}))
