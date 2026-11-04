"""Read-only UI revision audit, resolving original Phase 2 UI to exact archives."""
from pathlib import Path
import hashlib
import json
import runpy

PROJECT=Path(__file__).resolve().parents[1]
REVISION=PROJECT/'artifacts/ui_revisions/results_flow_v1'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def check():
    old_receipt=load(PROJECT/'artifacts/phase2/acceptance.json')
    old_by_path={row['path']:row for row in old_receipt['files']}
    archives={}
    for row in load(REVISION/'preservation.json')['files']:
        assert old_by_path[row['path']]['sha256']==row['sha256']
        assert row['path'].startswith('web/frontend/'),row['path']
        target=(PROJECT/row['archived_path']).resolve()
        assert target.is_relative_to(PROJECT/'provenance/ui_before_results_flow_v1')
        assert sha(target)==row['sha256'],row['archived_path']
        archives[(PROJECT/row['path']).resolve()]=target
    verifier=PROJECT/'scripts/verify_phase2.py'
    assert sha(verifier)==old_by_path['scripts/verify_phase2.py']['sha256']
    namespace=runpy.run_path(str(verifier),run_name='historical_phase2_audit')
    def historical_sha(path):
        return sha(archives.get(path.resolve(),path))
    namespace['check'].__globals__['sha']=historical_sha
    historical=namespace['check']()
    assert historical['status']=='PASS'
    browser=load(REVISION/'browser_verification.json')
    assert browser['status']=='PASS' and browser['mocked'] is False
    assert len(browser['checks'])>=25 and not browser['errors']
    revision_receipt=REVISION/'release.json'
    if revision_receipt.exists():
        for row in load(revision_receipt)['files']:
            assert sha(PROJECT/row['path'])==row['sha256'],row['path']
    return {'status':'PASS','revision':'results_flow_v1','historical_phase2':historical,'original_UI_archives':len(archives),'browser_checks':len(browser['checks']),'scientific_code_changed':False,'evaluation_rerun':False,'model_or_historical_TEST_run':False}

if __name__=='__main__':
    print(json.dumps(check(),ensure_ascii=False))
