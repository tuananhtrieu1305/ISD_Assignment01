"""Final hash audit and handoff for the explicit final-paper request."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import ast
import hashlib
import json
import time

ROOT=Path(__file__).resolve().parents[1]
F=ROOT/'tieuluanfinal'
DOC=F/'report/final/Tieu_Luan_AI_Final.docx'


def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    base=load(F/'docs/final_revision/baseline_copy.json')
    approved={'AGENTS.md','README.md','project.json','datasets/catalog.json','notebooks/README.md',
              'notebooks/01_ML_CNN.ipynb','notebooks/02_RNN_LSTM.ipynb','notebooks/03_Knowledge_RAG.ipynb','notebooks/04_Multi_Agent.ipynb',
              'web/frontend/src/v3/App.tsx','web/frontend/src/v3/catalog.ts'}
    def audit(row):
        path=F/row['path'];current=sha(path) if path.is_file() else None
        if current!=row['sha256']:
            assert row['path'] in approved or row['path'].startswith('web/frontend/dist/'),row['path']
            return {'path':row['path'],'baseline_sha256':row['sha256'],'current_sha256':current,'kind':'approved final revision'}
        return None
    changes=[];tick=time.monotonic()
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i,row in enumerate(pool.map(audit,base['files'])):
            if row:changes.append(row)
            if time.monotonic()-tick>25:print(f'Final baseline audit {i+1}/{len(base["files"])}',flush=True);tick=time.monotonic()
    notebooks=list((F/'notebooks').rglob('*.ipynb'));assert len(notebooks)==4
    for name in ['01_ML_CNN.ipynb','02_RNN_LSTM.ipynb','03_Knowledge_RAG.ipynb']:
        original=load(ROOT/'tieuluan3/notebooks'/name);current=load(F/'notebooks'/name)
        assert original['cells'][2:]==current['cells'][2:],name
    nb=load(F/'notebooks/04_Multi_Agent.ipynb');modules={}
    for cell in nb['cells']:
        source=''.join(cell['source'])
        if source.startswith('%%llm_v2_module '):
            head,body=source.split('\n',1);modules.setdefault(head.split()[-1].split('.')[-1],[]).append(body)
    assert len(modules)==16
    for name,bodies in modules.items():
        exported=(F/'web/agent/web/backend/project01_llm_v2'/f'{name}.py').read_text(encoding='utf-8')
        assert exported=='# GENERATED from tieuluanfinal/notebooks/04_Multi_Agent.ipynb\n'+''.join(bodies),name
        ast.parse(exported)
    config=load(F/'project.json')
    for row in config['notebooks']:row['sha256']=sha(F/row['path'])
    save(F/'project.json',config)
    scope=load(F/'docs/final_revision/document_scope.json');assert sha(DOC)==scope['output_sha256']
    assert sha(Path('C:/Users/anhca/Downloads/tieuluan03_CT_08_anhtt.docx'))==scope['source_sha256']
    ui=load(F/'artifacts/final_ch06/ui_qa/verification.json');assert ui['status']=='PASS'
    execution=load(F/'artifacts/notebook_runs/final_ch06_r1/execution.json');assert execution['status']=='PASS'
    word=load(F/'docs/final_revision/word_open_r2.json');assert word['status']=='PASS' and word['source_unchanged']
    ready=load(F/'docs/final_revision/readiness.json');assert ready['status']=='PASS' and ready['network_disabled']
    visual=load(ROOT/'docs/tieuluanfinal_r1/visual_qa_r1/render_comparison.json')
    assert visual['manual_visual_review']=='PASS_CHANGED_PAGES_AT_FULL_RESOLUTION'
    receipt={'status':'COMPLETE','task':'User-requested isolated tieuluanfinal and Chapter6 DOCX revision',
        'baseline_files_audited':len(base['files']),'baseline_bytes':base['total_bytes'],'approved_changes':changes,
        'scientific_data_models_metrics_predictions_unchanged':True,'Ch1_to_5_algorithm_cells_unchanged':True,
        'notebooks':4,'chapter6_inline_modules':len(modules),'notebook_export_parity':'PASS',
        'notebook_code_cells_executed':len(execution['records']),'network_disabled_during_notebook':True,
        'ui_checks':len(ui['checks']),'Word_read_only_open':'PASS','Word_pages':word['pages'],
        'packaged_index_KG_existing_key_shared_quota_readiness':'PASS_WITH_NETWORK_DISABLED',
        'visual_QA':'Changed pages inspected;106 other pages pixel-identical to reference except footer fields',
        'LibreOffice_pages':117,'chapter6_LibreOffice_pages':[110,115],
        'document':str(DOC),'document_sha256':sha(DOC),'unchanged_original_package_parts':scope['unchanged_package_parts'],
        'new_generation_API_calls':0,'new_embedding_API_calls':0,'new_training_steps':0,'scientific_TEST_forward':0,
        'held_out_evaluation':'Not run; one genuine r11 development example only',
        'old_v2_plan_phase2_evaluation_status':'Unchanged; this explicit report request does not assert the whole older evaluation plan COMPLETE',
        'commit_push_deploy':False,'local_command':'bash tieuluanfinal/scripts/run_web.sh','url':'http://127.0.0.1:8040/agents'}
    save(F/'docs/final_revision/verification.json',receipt)
    save(ROOT/'docs/tieuluanfinal_r1/checkpoint.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='approved_changes'}),flush=True)


if __name__=='__main__':main()
