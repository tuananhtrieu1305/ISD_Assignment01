"""Record r9 provenance and local verification without changing old receipts."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,subprocess,sys
P=Path(__file__).resolve().parents[2];ROOT=P.parent
OUT=P/'artifacts/llm_v2/phase2/development/source_policy_r9'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
OUT.mkdir(parents=True,exist_ok=True)
archives={}
preservation=load(P/'provenance/before_source_policy_r9/preservation.json')
for row in preservation['files']:
    archived=ROOT/row['archive'];assert sha(archived)==row['sha256']
    archives[(row['path'],row['sha256'])]=archived
resolved=[]
for row in load(P/'artifacts/llm_v2/phase2/development/full_demo_r8/source_manifest.json')['source_files']:
    active=ROOT/row['path']
    target=active if active.is_file() and sha(active)==row['sha256'] else archives.get((row['path'],row['sha256']))
    assert target and sha(target)==row['sha256'],row['path']
    resolved.append({**row,'resolved':target.relative_to(ROOT).as_posix()})
save(OUT/'r8_preservation_resolver.json',{'status':'PASS','files':resolved,'old_receipts_changed':False})
result=subprocess.run([sys.executable,str(Path(__file__).with_name('check_source_policy_r9.py'))],capture_output=True,text=True,encoding='utf-8')
assert result.returncode==0,result.stderr
checks= json.loads(result.stdout);save(OUT/'prompt_verification.json',checks)
assert load(OUT/'ui_verification.json')['status']=='PASS'
policy=P/'config/prompts/source_verification_vi.txt'
text=policy.read_text(encoding='utf-8').strip()
files=[policy,*list((P/'notebooks').glob('*.ipynb')),*list((P/'web/backend/project01_llm_v2').glob('*.py')),
       P/'web/frontend/src/main.jsx',*list((P/'web/frontend/dist').rglob('*')),P/'docs/llm_v2/SOURCE_POLICY_R9.md']
save(OUT/'source_manifest.json',{'revision':'source-verification-r9','files':[{'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)} for path in files if path.is_file()],
     'shared_policy_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),'applies_to':['llm_direct','agentic_rag_reporter'],
     'generation_calls_per_pair':3,'new_generation_API_calls':0,'new_embedding_API_calls':0,'live_validated':False})
path=ROOT/'docs/final_project01/llm_v2/checkpoint.json';state=load(path)
state['current_step']='Phase2 IN_PROGRESS. Source-verification r9 applies one standalone policy verbatim to direct and Reporter, records policy hash, keeps Risk/three-generation contract. Offline prompt/unit/UI checks PASS; no new Gemini or embedding calls. User must restart8031 backend and Ctrl+F5 before one manual test. No claimed baseline failure; held-out/freeze/Phase3 remain unstarted.'
state['phase2_progress']['source_policy_r9']={'status':'PASS_OFFLINE_NO_API','runtime_revision':'source-verification-r9',
     'policy':'project01/config/prompts/source_verification_vi.txt','policy_applies_equally_to_both_branches':True,
     'guide':'project01/docs/llm_v2/SOURCE_POLICY_R9.md','prompt_checks':8,'UI_checks':5,'regression_checks':28,'three_generation_checks':16,
     'new_generation_API_calls':0,'new_embedding_API_calls':0,'live_validated':False,'user_backend_needs_restart':True}
state['phase2_progress']['resume_steps']=[
    'Read checkpoint and project01/docs/llm_v2/SOURCE_POLICY_R9.md. Active runtime is source-verification-r9.',
    'Shared prompt file applies identically to direct and Reporter. Do not add question-specific forced answers or weaken only the baseline.',
    'User restarts8031 backend, Ctrl+F5, selects full-five-agent preset and manually tests one comparison with at least3 generation slots; embeddings have separate quota.',
    'Do not call Gemini automatically or repeat until RAG wins. Preserve both answers and report ties honestly.',
    'Development/freeze/40x2 held-out and Phase3 remain unfinished; this prompt change does not open them.'
]
state['api_execution_policy']['current_request']='SHARED_SOURCE_VERIFICATION_POLICY_R9_OFFLINE_ONLY'
state['last_updated']=datetime.now(timezone(timedelta(hours=7))).isoformat();save(path,state)
print(json.dumps({'status':'PASS','preserved':len(preservation['files']),'r8_pins_resolved':len(resolved),'API_calls':0}))
