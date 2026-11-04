"""Read-only FINAL verifier; archived dispatcher revision does not rewrite old receipts."""
from contextlib import redirect_stdout
from pathlib import Path
import copy
import hashlib
import io
import json
import runpy

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs/final_project01'

def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    preservation=load(DOCS/'preservation.json')
    archive={}
    for row in preservation['files']:
        path=(ROOT/row['archived_path']).resolve()
        assert path.is_relative_to(ROOT) and sha(path)==row['sha256']
        archive[(row['path'],row['sha256'])]=row['archived_path']
    old=ROOT/'scripts/verify_notebooks_inline.py'
    receipt=load(ROOT/'docs/notebook_revision/v1/handoff.json')
    pinned=next(r for r in receipt['files'] if r['path']==old.relative_to(ROOT).as_posix())
    assert sha(old)==pinned['sha256']
    namespace=runpy.run_path(str(old),run_name='historical_inline_verifier')
    original_load=namespace['load']
    def historical_load(path):
        document=original_load(path)
        if path==ROOT/'docs/notebook_revision/v1/handoff.json':
            document=copy.deepcopy(document)
            for row in document['files']:
                archived=archive.get((row['path'],row['sha256']))
                if archived:row['path']=archived
        return document
    namespace['main'].__globals__['load']=historical_load
    stream=io.StringIO()
    with redirect_stdout(stream):result=namespace['main']()
    historical=json.loads(stream.getvalue())
    assert not result and historical['status']=='PASS',historical
    assert 'FINAL_PROJECT01_EXECUTION_PLAN.md' in (ROOT/'AGENTS.md').read_text(encoding='utf-8')[:2200]
    checked=0
    inventory=DOCS/'baseline/inventory.json'
    if inventory.exists():
        for row in load(inventory)['files']:
            assert sha(ROOT/row['path'])==row['sha256'],row['path']
            checked+=1
    current=DOCS/'phase1_handoff.json'
    if current.exists():
        for row in load(current)['files']:
            assert sha(ROOT/row['path'])==row['sha256'],row['path']
            checked+=1
    print(json.dumps({'status':'PASS','historical_inline_and_REORG':historical,'final_baseline_and_handoff_records':checked,'dispatcher_archive_resolved':True,'training_steps':0,'historical_TEST_forward':0},ensure_ascii=False))

if __name__=='__main__':main()
