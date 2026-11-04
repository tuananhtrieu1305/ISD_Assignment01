"""Record the small r8 follow-up and resolve old pins; never revise old receipts."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json

P=Path(__file__).resolve().parents[2];ROOT=P.parent
OUT=P/'artifacts/llm_v2/phase2/development/full_demo_r8'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
baseline=load(P/'provenance/before_full_demo_r8/preservation.json')
archives={}
for row in baseline['files']:
    path=ROOT/row['archive'];assert sha(path)==row['sha256']
    archives[(row['path'],row['sha256'].lower())]=path
resolved=[]
for row in load(P/'artifacts/llm_v2/phase2/development/three_generation_r7/source_manifest.json')['source_files']:
    active=ROOT/row['path']
    candidate=active if sha(active)==row['sha256'].lower() else archives.get((row['path'],row['sha256'].lower()))
    assert candidate is not None and sha(candidate)==row['sha256'].lower(),row['path']
    resolved.append({**row,'resolved':candidate.relative_to(ROOT).as_posix()})
save(OUT/'r7_preservation_resolver.json',{'status':'PASS','files':resolved,'historical_receipts_modified':False})

assert load(OUT/'offline_pipeline_verification.json')['status']=='PASS'
assert load(OUT/'ui_verification.json')['status']=='PASS'
chunks=[json.loads(line) for line in (P/'datasets/llm_v2/chunks.jsonl').read_text(encoding='utf-8').splitlines()]
target=next(row for row in chunks if row['chunk_id']=='m2c-39c6512524216aa32b22')
assert '58 percent over 3 years' in target['content'] and '15 pounds' in target['content']
save(OUT/'selection.json',{'question':'Đi bộ có giúp tôi giảm 58% nguy cơ tiểu đường không?',
    'profile_id':'row_0048946','profile_scope':'existing matched TRAIN',
    'basis':'DPP lifestyle-group result versus individual guarantee and walking-only interpretation',
    'source_chunk':target,'source_file_sha256':sha(P/'datasets/llm_v2/chunks.jsonl'),
    'new_generation_API_calls':0,'new_embedding_API_calls':0,'baseline_error_demonstrated':False,
    'held_out_opened':False,'selection_is_development_demo_not_quality_benchmark':True})

files=list((P/'notebooks').glob('*.ipynb'))+list((P/'web/backend/project01_llm_v2').glob('*.py'))
files+=list((P/'web/frontend/src').glob('*'))+list((P/'web/frontend/dist').rglob('*'))
files+=[P/'docs/llm_v2/architecture.md',P/'docs/llm_v2/DEMO_FULL_PIPELINE_R8.md']
save(OUT/'source_manifest.json',{'revision':'full-demo-r8','source_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in files if p.is_file()],
     'baseline_archive':'project01/provenance/before_full_demo_r8','notebooks':3,'exported_modules':16,
     'new_generation_API_calls':0,'new_embedding_API_calls':0,'live_Gemini_quality_validated':False})

path=ROOT/'docs/final_project01/llm_v2/checkpoint.json';state=load(path)
state['current_step']='Phase2 IN_PROGRESS. Full-demo r8 adds one short DPP58 question + complete TRAIN profile preset; real Risk output reaches Reporter and the composed draft is checked before release. Offline engineering checks PASS with zero Gemini/embedding calls; a fresh live pair has NOT been run. Restart user-owned backend before testing. Freeze/held-out/Phase3 remain unstarted.'
state['phase2_progress']['full_demo_r8']={'status':'PASS_OFFLINE_ENGINEERING_ONLY','runtime_revision':'full-demo-r8',
    'question':'Đi bộ có giúp tôi giảm 58% nguy cơ tiểu đường không?','profile_id':'row_0048946',
    'guide':'project01/docs/llm_v2/DEMO_FULL_PIPELINE_R8.md','report':'docs/final_project01/llm_v2/full_demo_r8_report.md',
    'verification':'project01/artifacts/llm_v2/phase2/development/full_demo_r8/offline_pipeline_verification.json',
    'new_generation_API_calls':0,'new_embedding_API_calls':0,'baseline_error_demonstrated':False,
    'user_backend_needs_restart':True,'generation_calls_per_comparison':3}
state['api_execution_policy']['current_request']='OFFLINE_KB_DEMO_SELECTION_AND_FULL_FIVE_ROLE_R8'
state['phase2_progress']['resume_steps']=[
    'Read checkpoint and full_demo_r8_report.md; runtime is full-demo-r8 with exactly3 generation calls.',
    'User restarts their8031 backend and Ctrl+F5. Preset Demo đủ5agent selects the DPP58 question and a full TRAIN profile.',
    'Do not call Gemini automatically. At most one explicitly requested live comparison after checking at least3 generation slots; query embedding quota is separate.',
    'Do not promise baseline failure or change prompts/repeat calls until RAG wins. Offline test is not live quality evidence.',
    'Freeze/40x2 held-out/Phase3 remain separate unfinished work.'
]
state['last_updated']=datetime.now(timezone(timedelta(hours=7))).isoformat()
save(path,state)
print(json.dumps({'status':'PASS','preserved_files':len(baseline['files']),'r7_pins_resolved':len(resolved),'API_calls':0,'phase2':'IN_PROGRESS'}))
