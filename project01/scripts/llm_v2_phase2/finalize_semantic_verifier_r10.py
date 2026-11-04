"""Record r10 provenance/state; preserve previous jobs, API ledger and receipts."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json
P=Path(__file__).resolve().parents[2];ROOT=P.parent
OUT=P/'artifacts/llm_v2/phase2/development/semantic_verifier_r10'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archives={}
baseline=load(P/'provenance/before_semantic_verifier_r10/preservation.json')
for row in baseline['files']:
    archived=ROOT/row['archive'];assert sha(archived)==row['sha256']
    archives[(row['path'],row['sha256'])]=archived
plan_original=load(P/'provenance/before_semantic_verifier_r10/root_files/plan_preservation.json')
assert sha(ROOT/plan_original['archive'])==plan_original['sha256']
resolved=[]
for row in load(P/'artifacts/llm_v2/phase2/development/source_policy_r9/source_manifest.json')['files']:
    active=ROOT/row['path']
    target=active if active.is_file() and sha(active)==row['sha256'] else archives.get((row['path'],row['sha256']))
    assert target and sha(target)==row['sha256'],row['path']
    resolved.append({**row,'resolved':target.relative_to(ROOT).as_posix()})
save(OUT/'r9_preservation_resolver.json',{'status':'PASS','files':resolved,'old_receipts_modified':False})
for name in ['unit_verification.json','pipeline_verification.json','ui_verification.json']:
    assert load(OUT/name)['status']=='PASS'
assert sha(P/'datasets/llm_v2/chunks.jsonl')==load(P/'artifacts/llm_v2/phase2/development/full_demo_r8/selection.json')['source_file_sha256']
package=P/'artifacts/package/v1'
for row in load(package/'manifest.json')['files']:assert sha(package/row['path'])==row['sha256']
files=[*list((P/'notebooks').glob('*.ipynb')),*list((P/'web/backend/project01_llm_v2').glob('*.py')),
       *list((P/'web/frontend/src').glob('*')),*list((P/'web/frontend/dist').rglob('*')),
       P/'docs/llm_v2/runtime_config.json',P/'docs/llm_v2/SEMANTIC_VERIFIER_R10.md',
       P/'config/prompts/semantic_verifier_vi.txt',P/'config/prompts/source_verification_vi.txt']
save(OUT/'source_manifest.json',{'revision':'semantic-verifier-r10','source_files':[{'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)} for path in files if path.is_file()],
    'generation_calls_per_pair':4,'new_generation_API_calls':0,'new_embedding_API_calls':0,'live_semantic_quality_validated':False,
    'notebooks':3,'exported_modules':16,'matched_TRAIN_risk_inference_only':True,'corpus_and_package_hashes':'PASS'})
path=ROOT/'docs/final_project01/llm_v2/checkpoint.json';state=load(path)
state['plan_version']='2.5'
state['current_step']='Phase2 IN_PROGRESS. User-requested r10 adds one Gemini semantic Verifier call (four generation per pair), keeps citation/score integrity hard checks and permits same-call checked correction. Risk now defaults to complete TRAIN profile; combined missing profile is blocked before API. Offline14unit/28regression/13UI and seven-stage four-call engineering fixture PASS; no new Gemini/embedding request. Restart user backend before testing. Freeze/held-out/Phase3 remain unstarted.'
state['phase2_progress']['semantic_verifier_r10']={'status':'PASS_OFFLINE_NO_API','runtime_revision':'semantic-verifier-r10',
    'user_requested_gemini_verifier':True,'generation_calls_per_comparison':4,'generation_calls_rag':3,'risk_default':'existing matched TRAIN profile, all21fields',
    'unit_checks':14,'regression_checks':28,'ui_checks':13,'seven_stages_complete_in_offline_fixture':True,
    'new_generation_API_calls':0,'new_embedding_API_calls':0,'live_validated':False,
    'guide':'project01/docs/llm_v2/SEMANTIC_VERIFIER_R10.md','source_manifest':(OUT/'source_manifest.json').relative_to(ROOT).as_posix(),
    'user_backend_needs_restart':True,'actual_incident_job_read_only':'16c2b50c-6948-4bda-b96e-ddb77770c87b'}
state['phase2_progress']['resume_steps']=[
    'Read r10 guide and current checkpoint; r7-r9 three-call contract is historical, user explicitly requested Gemini verifier.',
    'User restarts8031 backend and Ctrl+F5. New runtime is semantic-verifier-r10; full-five-agent mode is on by default with complete TRAIN profile.',
    'One valid live comparison needs4generation slots, plus separate embedding quota. No automatic API acceptance or reruns until the pipeline wins.',
    'Verifier does one same-model semantic review/correction and local integrity recheck; no extra repair generation loop, no clinical-accuracy guarantee.',
    'Old waiting jobs must not resume under a new prompt/runtime; preserve all old results and API claims.',
    'Held-out/freeze/Phase3 remain unstarted. Estimate160generation for40pairs under the new4call contract.'
]
state['api_execution_policy']['current_request']='USER_REQUESTED_SEMANTIC_VERIFIER_AND_DEFAULT_FULL_PROFILE_R10_OFFLINE_ONLY'
state['api_execution_policy']['manual_demo_default']='One explicitly requested or user-triggered comparison; four generation slots, embeddings disclosed separately; no automatic request/retry.'
state['last_updated']=datetime.now(timezone(timedelta(hours=7))).isoformat();save(path,state)
print(json.dumps({'status':'PASS','originals_preserved':len(baseline['files']),'r9_pins_resolved':len(resolved),'corpus_and_model_package_hashes':'PASS','API_calls':0}))
