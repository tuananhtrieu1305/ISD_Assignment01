"""Freeze implementation/config before the one-pass new evaluation."""
from pathlib import Path
import hashlib
import json
import sys

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parent
sys.path.insert(0,str(PROJECT/'scripts'))
from notebook_source import export,source_hash

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    destination=PROJECT/'artifacts/phase2/freeze.json'
    if destination.exists():raise RuntimeError('Already frozen; preserve original and declare a revision to change source')
    export(check=True)
    import nbformat
    notebooks=[]
    for path in sorted((PROJECT/'notebooks').glob('*.ipynb')):
        document=load(path);nbformat.validate(nbformat.from_dict(document))
        notebooks.append({'path':path.relative_to(PROJECT).as_posix(),'notebook_source_sha256':source_hash(document)})
    assert len(notebooks)==3
    assert load(PROJECT/'artifacts/phase2/index_parity.json')['status']=='PASS'
    assert load(PROJECT/'artifacts/phase2/pretest.json')['status']=='PASS'
    assert load(PROJECT/'artifacts/phase2/ui/verification.json')['status']=='PASS'
    for row in load(PROJECT/'datasets/benchmark/protocol_lock.json')['files']:assert sha(PROJECT/row['path'])==row['sha256']
    files=[*list((PROJECT/'web/backend/project01_core').glob('*.py')),*list((PROJECT/'artifacts/package/v1').glob('*')),*list((PROJECT/'datasets/benchmark').glob('*.json')),PROJECT/'artifacts/phase2/source_exports.json',PROJECT/'scripts/notebook_source.py',PROJECT/'scripts/experiment.py',PROJECT/'scripts/freeze_phase2.py',PROJECT/'tests/test_pipeline.py']
    record={'version':'project01.evaluation-freeze.1','files':[{'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files) if p.is_file()],'notebooks':notebooks,'pretest':'artifacts/phase2/pretest.json','development_results':'artifacts/phase2/development/r2/results','evaluation_cases':40,'variants':['P0','P1','P2'],'evaluation_runs_before_freeze':0,'no_old_TEST_replay':True}
    destination.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print('Frozen',len(record['files']),'files; evaluation remains unclaimed')

if __name__=='__main__':main()
