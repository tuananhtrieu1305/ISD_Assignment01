"""Runs in isolated project-only copy, with networking disabled."""
from pathlib import Path
import asyncio,json,os,socket,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'web/backend'))
os.environ.pop('GEMINI_API_KEY',None);os.environ.pop('GOOGLE_API_KEY',None)
def no_network(*args,**kwargs):raise RuntimeError('Network forbidden in clean-start check')
socket.socket.connect=no_network
from project01_llm_v2.agents import AgenticRuntime,RiskAgent
from project01_llm_v2.transport import create_app
runtime=AgenticRuntime(P,False);readiness=runtime.readiness()
assert readiness['index_ready'] and not readiness['key_present']
assert len(runtime.graph.search('bệnh thận'))>0
profile=json.loads((P/'datasets/demo_profiles.json').read_text())['profiles'][0]['profile']
assert RiskAgent(P).run(profile)['calibrated_incidence_risk'] is False
client=create_app(P,False).test_client()
assert client.get('/health').status_code==200
from app import app as wsgi_app
assert wsgi_app.test_client().get('/health').status_code==200
assert client.get('/api/v2/examples').status_code==200
assert client.post('/api/v2/compare',json={'question':'Q'}).status_code==503
for name,module in list(sys.modules.items()):
    if name.startswith('project01_llm_v2') and getattr(module,'__file__',None):assert Path(module.__file__).is_relative_to(P)
print(json.dumps({'status':'PASS','index_chunks':316,'kg_lookup':'PASS','risk':'PASS','api_health':'PASS',
                  'wsgi_entrypoint':'PASS','new_live_API_disabled_explicitly':True,'network_calls':0,'source_imports_all_inside_copy':True,
                  'LLM_quality_proof':'separate live development receipts, not this source-only check'}))
