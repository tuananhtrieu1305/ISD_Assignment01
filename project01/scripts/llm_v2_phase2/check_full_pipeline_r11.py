"""Six execution stages, four roles, no Risk; mocked generation/dense disabled."""
from pathlib import Path
from unittest.mock import patch
import asyncio,json,re,sys
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.agents import AgenticRuntime
from project01_llm_v2.embedding import load_corpus,index_fingerprint
from project01_llm_v2.kg import MiniKG
from project01_llm_v2.retrieval import HybridSearcher
QUESTION='Đi bộ có giúp tôi giảm hơn 50% nguy cơ tiểu đường không?'
OUT=P/'artifacts/llm_v2/phase2/development/four_agent_r11'
class Gateway:
 def __init__(self):self.observations=[];self.config={'generation_model':'OFFLINE_TEST_DOUBLE','endpoint':'no-network'}
 def usage(self):return {'generation_attempts':0}
 def record(self,call_id):self.observations.append({'kind':'generation','call_id':call_id,'cache_status':'offline_test_double'})
 def call(self,kind,body,call_id):
  self.record(call_id)
  return {'text':json.dumps({'language':'vi','intent':'knowledge','queries':['walking diabetes risk reduction lifestyle DPP'],
   'entity_ids':['activity','type2'],'relation_direction':[],'scope':'diabetes'})}
 async def generate(self,prompt,call_id,tokens):
  self.record(call_id)
  if call_id.endswith(':direct'):value='OFFLINE FIXTURE: direct generation is mocked.'
  elif ':semantic-verifier:' in call_id:
   draft=json.loads(prompt.split('INPUT_DATA_JSON:\n',1)[1])['draft']
   value=json.dumps({'approved':True,'numeric_ok':True,'scope_ok':True,'answer_matches_claims':True,'corrected_draft':None,
     'feedback':'OFFLINE FIXTURE: semantic review mocked, not quality evidence.',
     'claim_reviews':[{'claim_id':c['id'],'status':'supported','evidence_ids':c['citation_chunk_ids'],'reason_vi':'Offline fixture.'} for c in draft['claims']]})
  else:
   source=re.findall(r'\[Nguồn (\d+)\] chunk_id=(\S+)',prompt)[0]
   value=json.dumps({'answer_vi':f'OFFLINE FIXTURE: câu trả lời minh họa từ evidence đã truy hồi. [Nguồn {source[0]}]',
      'claims':[{'id':'1','text_vi':'Offline fixture claim; not actual clinical content.','citation_chunk_ids':[source[1]]}],
      'limitations':['Engineering fixture; no live generation or dense query.']})
  return {'text':value,'cache_status':'offline_test_double'}
async def no_dense(self,query,top_k):return []
async def main():
 runtime=AgenticRuntime.__new__(AgenticRuntime);runtime.root=P;runtime.gateway=Gateway();runtime.chunks=load_corpus(P)
 runtime.folder=P/'artifacts/llm_v2/index'/index_fingerprint(runtime.chunks);runtime.graph=MiniKG(P,runtime.chunks)
 runtime.pipeline_trace=[];runtime.readiness=lambda:{'index_ready':True}
 with patch.object(HybridSearcher,'_dense_search',no_dense),patch('project01_llm_v2.risk.FrozenRisk.predict',side_effect=AssertionError('Risk must not run')):
  direct=await runtime.direct(QUESTION,'offline-r11');rag=await runtime.rag(QUESTION,'offline-r11')
 assert [s['id'] for s in rag['pipeline_trace']]==['pre_retrieval','retrieval','rerank','reporter','verifier','release']
 assert all(s['status']=='complete' for s in rag['pipeline_trace'])
 assert rag['status']=='complete' and len(runtime.gateway.observations)==4 and 'risk' not in rag
 assert all('profile_present' not in s.get('input',{}) for s in rag['pipeline_trace'])
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'offline_pipeline_fixture.json').write_text(json.dumps({'id':'offline-r11','runtime_revision':'four-agent-r11',
  'question':QUESTION,'status':'complete','results':{'llm_direct':direct,'agentic_rag':rag},
  'fixture':'ENGINEERING_ONLY_GENERATION_AND_SEMANTIC_REVIEW_MOCKED_DENSE_DISABLED'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 receipt={'status':'PASS','four_roles':True,'six_stages_complete':True,'Risk_calls':0,'mock_generation_calls':4,'new_generation_API_calls':0,'new_embedding_API_calls':0,'dense_disabled':True,'quality_validated':False}
 (OUT/'pipeline_verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(receipt))
asyncio.run(main())
