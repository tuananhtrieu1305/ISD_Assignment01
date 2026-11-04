"""Preserve active sources before v2 port; never copy secrets or environments."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil

P=Path(__file__).resolve().parents[2];ROOT=P.parent


def main():
    target=P/'provenance/before_llm_v2_phase2'
    if (target/'preservation.json').exists():raise RuntimeError('Already preserved; resume without repeating')
    for row in json.loads((ROOT/'docs/final_project01/llm_v2/phase1_handoff.json').read_text())['files']:
        with (ROOT/row['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],row['path']
    files=list((P/'notebooks').rglob('*.ipynb'))
    files += [p for p in (P/'web').rglob('*') if p.is_file() and not any(x in p.parts for x in ['node_modules','.runtime','__pycache__']) and not p.name.startswith('.env')]
    files += [P/'README.md',P/'scripts/run_web.ps1',P/'scripts/serve.py',P/'scripts/notebook_source.py']
    records=[]
    for path in sorted(set(files)):
        if not path.exists():continue
        rel=path.relative_to(P);dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        digest=hashlib.sha256(path.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
        records.append({'path':rel.as_posix(),'archived_path':dest.relative_to(P).as_posix(),'sha256':digest})
    target.mkdir(parents=True,exist_ok=True)
    (target/'preservation.json').write_text(json.dumps({'date':datetime.now(timezone.utc).isoformat(),'files':records},indent=2)+'\n')
    checkpoint=ROOT/'docs/final_project01/llm_v2/checkpoint.json';state=json.loads(checkpoint.read_text())
    state['active_phase']=2;state['phases']['2']['status']='IN_PROGRESS'
    state['current_step']='Phase2 started: originals preserved, porting group source into notebooks/export and installing isolated serving lock; no evaluation opened'
    checkpoint.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'preserved':len(records),'phase1_handoff':'PASS','phase2':'IN_PROGRESS'}))


if __name__=='__main__':main()
