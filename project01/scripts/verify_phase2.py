"""Read-only Phase 2 acceptance: hashes, saved-result math, lineage and source parity."""
from pathlib import Path
import copy
import hashlib
import json
import sys

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parent
sys.path.insert(0,str(PROJECT/'scripts'));sys.path.insert(0,str(PROJECT/'web/backend'))
from notebook_source import export,source_hash
from project01_core.evaluation import apply_support_reviews,case_request,judge_automatic,read_results,summarize
from project01_core.foundation import digest

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def check():
    export(check=True)
    phase=PROJECT/'artifacts/phase2';frozen=load(phase/'freeze.json')
    for row in frozen['files']:assert sha(PROJECT/row['path'])==row['sha256'],row['path']
    for row in frozen['notebooks']:assert source_hash(load(PROJECT/row['path']))==row['notebook_source_sha256']
    for row in load(PROJECT/'artifacts/phase1/complete.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    for row in load(phase/'phase1_drafts_backup.json')['files']:assert sha(ROOT/row['archived_path'])==row['sha256']
    assert load(phase/'pretest.json')['integration_tests']==18
    assert load(phase/'index_parity.json')['status']=='PASS'
    assert load(phase/'ui/verification_final.json')['status']=='PASS'
    assert len(load(phase/'ui/verification_final.json')['checks'])==18
    assert len(list((PROJECT/'notebooks').rglob('*.ipynb')))==3
    import nbformat
    for path in (PROJECT/'notebooks').glob('*.ipynb'):
        document=load(path);nbformat.validate(nbformat.from_dict(document))
        assert any(c.get('outputs') for c in document['cells'] if c['cell_type']=='code')
        assert not any(o.get('output_type')=='error' for c in document['cells'] for o in c.get('outputs',[]))
    cases={r['case_id']:r for r in load(PROJECT/'datasets/benchmark/evaluation.json')['cases']}
    rows=read_results(phase/'evaluation/results');raw=read_results(phase/'evaluation/raw_results')
    expected={(case,variant) for case in cases for variant in ['P0','P1','P2']}
    assert {(r['case_id'],r['variant']) for r in rows}==expected
    assert len(rows)==len(raw)==len(list((phase/'evaluation/claims').glob('*.json')))==120
    by_key={(r['case_id'],r['variant']):r for r in rows}
    recomputed=[]
    for row in raw:
        key=row['case_id']+'_'+row['variant'];case=cases[row['case_id']]
        claim=load(phase/'evaluation/claims'/(key+'.json'))
        assert claim['request_sha256']==digest(case_request(case))==row['result']['input_sha256']
        assert row['metrics']==judge_automatic(case,row['result'],row['reference_score'])
        assert row['result']['worker_terminated']
        assert row['result']['tool_calls'] is None or row['result']['tool_calls']<=8
        assert row['result']['retrieval_loops'] is None or row['result']['retrieval_loops']<=1
        derived=by_key[(row['case_id'],row['variant'])]
        assert derived['result']==row['result']
        assert sha(PROJECT/derived['derived_from']['path'])==derived['derived_from']['sha256']
        recomputed.append(copy.deepcopy(row))
    reviews=load(phase/'support_reviews.json');assert len(reviews['rows'])==54 and reviews['independent_human_review'] is False
    recomputed=apply_support_reviews(recomputed,reviews['rows'])
    for row in recomputed:assert row['metrics']==by_key[(row['case_id'],row['variant'])]['metrics']
    assert summarize(recomputed)==load(phase/'summary.json')
    assert load(phase/'active_process.json')['pid'] is None
    from PIL import Image
    for name in ['task_success.png','evidence_and_coverage.png','latency_tools.png']:
        with Image.open(PROJECT/'report/figures'/name) as image:image.verify()
    receipt=phase/'acceptance.json'
    if receipt.exists():
        for row in load(receipt)['files']:assert sha(PROJECT/row['path'])==row['sha256'],row['path']
    return {'status':'PASS','notebooks':3,'notebook_export_modules':4,'integration_tests':18,'browser_checks':18,'raw_outputs':120,'derived_outputs':120,'claims':120,'manual_assistant_reviews':54,'frozen_files':len(frozen['files']),'old_training_or_TEST_forward':0,'evaluation_reruns':0,'plots':3,'source_code_location':'notebook cells','cloud_deployment':'not_performed'}

if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False))
