"""Record the simplified demo without touching model data, old outputs or API ledger."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,hashlib,json
P=Path(__file__).resolve().parents[2];ROOT=P.parent
OUT=P/'artifacts/llm_v2/phase2/development/four_agent_r11'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
baseline=load(P/'provenance/before_four_agent_r11/preservation.json');archives={}
for row in baseline['files']:
    target=ROOT/row['archive'];assert sha(target)==row['sha256']
    archives[(row['path'],row['sha256'])]=target
resolved=[]
for row in load(P/'artifacts/llm_v2/phase2/development/semantic_verifier_r10/source_manifest.json')['source_files']:
    active=ROOT/row['path'];target=active if active.is_file() and sha(active)==row['sha256'] else archives.get((row['path'],row['sha256']))
    assert target and sha(target)==row['sha256'],row['path']
    resolved.append({**row,'resolved':target.relative_to(ROOT).as_posix()})
save(OUT/'r10_preservation_resolver.json',{'status':'PASS','files':resolved,'old_receipts_changed':False})
def classes(path,names):
    tree=ast.parse(path.read_text(encoding='utf-8'));return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names}
old=P/'provenance/before_four_agent_r11/web/backend/project01_llm_v2';active=P/'web/backend/project01_llm_v2'
assert classes(old/'agents.py',['SemanticVerifier','CodeVerifier'])==classes(active/'agents.py',['SemanticVerifier','CodeVerifier'])
assert classes(old/'generation.py',['PromptBuilder','BaseGenerator','GeminiGenerator'])==classes(active/'generation.py',['PromptBuilder','BaseGenerator','GeminiGenerator'])
for name in ['backend_verification.json','pipeline_verification.json','ui_verification.json']:assert load(OUT/name)['status']=='PASS'
config=P/'docs/llm_v2/runtime_config.json';value=load(config);value['config_version']='llm-v2-four-agent-r11'
value['pipeline']['agent_roles']=['Coordinator','Knowledge Agent','Reporter','Verifier Agent'];value['pipeline']['input_schema']='question_only';save(config,value)
plan=ROOT/'FINAL_PROJECT01_LLM_V2_EXECUTION_PLAN.md';text=plan.read_text(encoding='utf-8');first,rest=text.split('\n',1)
note='\n**Override r11 mới nhất:** người dùng bỏ Risk Agent/hồ sơ khỏi demo; pipeline chỉ4agent Coordinator→Knowledge→Reporter→Verifier, vẫn4generation/cặp do VerifierGemini. UI một sơ đồ duy nhất, câu hỏi chỉinput+nút, tabKGthay tabđánhgiá. GraphSVGlocal lấy35node/35assertion có kiểmnguồn, khôngNeo4j/APIextract. Model/dataset/kết quả cũ giữ lịch sử, không tham gia request mới. Đọc `project01/docs/llm_v2/FOUR_AGENT_R11.md`. Phần5vai trò/Risk mặc định trong r10 bên dưới là lịch sử.\n'
if '**Override r11 mới nhất:**' not in text:plan.write_text((first+'\n'+note+rest).replace('Phiên bản 2.5 —','Phiên bản 2.6 —',1),encoding='utf-8')
path=ROOT/'docs/final_project01/llm_v2/checkpoint.json';state=load(path);state['plan_version']='2.6'
state['current_step']='Phase2 IN_PROGRESS. Four-agent r11 removes Risk/profile from active question-only API and UI. One canonical four-role pipeline; evaluation tab replaced by interactive source-backed KG35nodes/35assertions. Existing Gemini generation/verifier logic retained, four-generation budget unchanged. Offline10backend/20UI/six-stage mock pipeline PASS with zero model API calls. User restarts8031 backend and Ctrl+F5. Held-out/freeze/Phase3 remain unstarted.'
state['phase2_progress']['four_agent_r11']={'status':'PASS_OFFLINE_NO_API','runtime_revision':'four-agent-r11',
    'guide':'project01/docs/llm_v2/FOUR_AGENT_R11.md','agent_roles':value['pipeline']['agent_roles'],'input':'question_only',
    'Risk_active':False,'generation_calls_per_comparison':4,'graph_nodes':35,'graph_assertions':35,
    'backend_checks':10,'UI_checks':20,'new_generation_API_calls':0,'new_embedding_API_calls':0,'user_backend_needs_restart':True}
state['phase2_progress']['resume_steps']=[
    'Read FOUR_AGENT_R11.md. Active runtime four-agent-r11 accepts only question; no Risk, no automatic TRAIN profile.',
    'User restarts8031 backend and Ctrl+F5. UI has question, answer, one4agent-flow and knowledge-graph tabs.',
    'Keep existing Gemini semantic Verifier and shared source policy. Four generation per pair; embeddings separate. Do not call API automatically.',
    'Model/profile/history outputs remain preserved, but are not active inputs. Old revision jobs must not resume under new prompts.',
    'Graph is read-only reviewed mini-KG from source, not a new LLM extraction. Do not add Neo4j or extra services.',
    'Freeze/evaluation/Phase3 remain unfinished; hiding the evaluation UI does not mark evaluation complete.'
]
state['api_execution_policy']['current_request']='USER_REQUESTED_QUESTION_ONLY_FOUR_AGENTS_AND_LIGHTWEIGHT_KG_R11_OFFLINE_ONLY'
state['last_updated']=datetime.now(timezone(timedelta(hours=7))).isoformat();save(path,state)
files=[*list((P/'notebooks').glob('*.ipynb')),*list(active.glob('*.py')),*list((P/'web/frontend/src').glob('*')),
       *list((P/'web/frontend/dist').rglob('*')),config,P/'docs/llm_v2/FOUR_AGENT_R11.md',P/'docs/llm_v2/architecture.md']
save(OUT/'source_manifest.json',{'revision':'four-agent-r11','source_files':[{'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)} for f in files if f.is_file()],
    'generation_verifier_AST_unchanged_from_r10':True,'new_generation_API_calls':0,'new_embedding_API_calls':0,'live_quality_validated':False})
print(json.dumps({'status':'PASS','preserved_files':len(baseline['files']),'r10_pins_resolved':len(resolved),'generation_and_verifier_unchanged':'AST_PASS','API_calls':0}))
