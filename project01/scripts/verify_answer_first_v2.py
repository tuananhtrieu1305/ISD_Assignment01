"""Read-only answer-first presentation revision; preserve both historical UI receipts."""
from pathlib import Path
import hashlib
import json
import runpy

PROJECT=Path(__file__).resolve().parents[1]
REVISION=PROJECT/'artifacts/ui_revisions/answer_first_v2'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def check():
    parent=load(PROJECT/'artifacts/ui_revisions/results_flow_v1/release.json')
    expected={row['path']:row['sha256'] for row in parent['files']}
    archive={}
    for row in load(REVISION/'preservation.json')['files']:
        assert expected[row['path']]==row['sha256']
        target=(PROJECT/row['archived_path']).resolve()
        assert target.is_relative_to(PROJECT/'provenance/ui_before_answer_first_v2')
        assert sha(target)==row['sha256'],row['archived_path']
        archive[(PROJECT/row['path']).resolve()]=target
    assert len(archive)==len(expected)
    verifier=PROJECT/'scripts/verify_results_flow_v1.py'
    assert sha(verifier)==expected['scripts/verify_results_flow_v1.py']
    namespace=runpy.run_path(str(verifier),run_name='historical_results_flow_v1')
    def historical_sha(path):
        return sha(archive.get(path.resolve(),path))
    namespace['check'].__globals__['sha']=historical_sha
    previous=namespace['check']()
    assert previous['status']=='PASS'
    browser=load(REVISION/'browser_verification.json')
    assert browser['status']=='PASS' and browser['mocked'] is False and not browser['errors']
    assert len(browser['checks'])>=30
    release=REVISION/'release.json'
    if release.exists():
        for row in load(release)['files']:
            assert sha(PROJECT/row['path'])==row['sha256'],row['path']
    return {'status':'PASS','revision':'answer_first_v2','parent_revision':previous,'archived_parent_files':len(archive),'browser_checks':len(browser['checks']),'final_answer_from_backend_sections':True,'backend_notebook_model_changed':False,'evaluation_rerun':False}

if __name__=='__main__':
    print(json.dumps(check(),ensure_ascii=False))
