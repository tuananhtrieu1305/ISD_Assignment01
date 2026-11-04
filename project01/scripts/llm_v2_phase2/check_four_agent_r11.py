"""Question-only API and real KG endpoint; no provider, Risk model or TEST call."""
from pathlib import Path
from unittest.mock import patch
import json,shutil,sys,tempfile
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.transport import create_app
from project01_llm_v2.agents import AgenticRuntime
checks=[]
def ok(value,name):assert value,name;checks.append(name)
class OfflineRuntime:
 def __init__(self,*args,**kwargs):pass
 def readiness(self):return {'status':'ready','usage':{'generation_attempts':15,'generation_cap':18}}

client=create_app(P,False).test_client()
with patch('project01_llm_v2.risk.FrozenRisk.predict',side_effect=AssertionError('Risk must not run')):
 response=client.get('/api/v2/knowledge-graph');ok(response.status_code==200,'KG endpoint works without an API key or provider call')
 data=response.json
 ok(len(data['nodes'])==35 and len(data['edges'])==35,'KG exposes the actual35nodes and35reviewed assertions')
 ids={n['id'] for n in data['nodes']}
 ok(all(e['source'] in ids and e['target'] in ids for e in data['edges']),'every KG edge has real endpoints')
 ok(all(e['quote'] and e['source_url'] and e['source_chunk_ids'] for e in data['edges']),'every edge retains quote and source provenance')
 ok(client.post('/api/v2/risk',json={'profile':{}}).status_code in {404,405},'Risk endpoint removed from active web API')
 ok(client.post('/api/v2/compare',json={'question':'Q','profile':{},'mode':'combined'}).status_code==422,'obsolete profile payload rejected explicitly')
 ok(client.post('/api/v2/compare',json={'question':'Q'}).status_code==503,'question-only request validates before live-disabled guard')
with tempfile.TemporaryDirectory() as temporary,patch('project01_llm_v2.transport.AgenticRuntime',OfflineRuntime),patch('project01_llm_v2.transport.threading.Thread'):
 response=create_app(temporary,True).test_client().post('/api/v2/compare',json={'question':'Q'})
 ok(response.status_code==429,'four-generation budget remains enforced without profiles')
source=(P/'web/backend/project01_llm_v2/agents.py').read_text(encoding='utf-8')
rag=source.split('async def rag(',1)[1].split('async def direct(',1)[0]
ok('RiskAgent(' not in rag and "recorder.skip('risk'" not in rag,'active RAG never calls or records a Risk stage')
ok("'agent_roles':['Coordinator','Knowledge Agent','Reporter','Verifier Agent']" in source,'readiness declares exactly four roles')
out=P/'artifacts/llm_v2/phase2/development/four_agent_r11';out.mkdir(parents=True,exist_ok=True)
(out/'graph_fixture.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
receipt={'status':'PASS','checks':checks,'new_generation_API_calls':0,'new_embedding_API_calls':0}
(out/'backend_verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
