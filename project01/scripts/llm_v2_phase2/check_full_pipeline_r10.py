"""Real local TRAIN Risk/retrieval with four fake generation calls; no network."""
from pathlib import Path
from unittest.mock import patch
import asyncio,json,re,sys
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.agents import AgenticRuntime
from project01_llm_v2.embedding import load_corpus,index_fingerprint
from project01_llm_v2.kg import MiniKG
from project01_llm_v2.retrieval import HybridSearcher

QUESTION='Đi bộ có giúp tôi giảm hơn 50% nguy cơ tiểu đường không?'
OUT=P/'artifacts/llm_v2/phase2/development/semantic_verifier_r10'
class Gateway:
 def __init__(self):self.observations=[];self.prompts=[];self.config={'generation_model':'OFFLINE_TEST_DOUBLE','endpoint':'no-network'}
 def record(self,prompt,call_id):
  self.prompts.append(prompt);self.observations.append({'kind':'generation','call_id':call_id,'cache_status':'offline_test_double'})
 def usage(self):return {'generation_attempts':0}
 def call(self,kind,body,call_id):
  assert kind=='generation';self.record(body['input'],call_id)
  return {'text':json.dumps({'language':'vi','intent':'combined','queries':['walking more than 50 percent diabetes risk lifestyle weight loss DPP'],
      'entity_ids':['activity','type2'],'relation_direction':[],'scope':'diabetes'})}
 async def generate(self,prompt,call_id,tokens):
  self.record(prompt,call_id)
  if call_id.endswith(':direct'):value='OFFLINE TEST DOUBLE: not a live Gemini answer.'
  elif ':semantic-verifier:' in call_id:
   data=json.loads(prompt.split('INPUT_DATA_JSON:\n',1)[1]);draft=data['draft']
   value=json.dumps({'approved':True,'numeric_ok':True,'scope_ok':True,'answer_matches_claims':True,'corrected_draft':None,
     'feedback':'OFFLINE FIXTURE: provider review is mocked, not clinical evidence.',
     'claim_reviews':[{'claim_id':c['id'],'status':'supported','evidence_ids':c['citation_chunk_ids'],'reason_vi':'Offline test-double decision.'} for c in draft['claims']]})
  else:
   refs=re.findall(r'\[Nguồn (\d+)\] chunk_id=(\S+)',prompt);assert refs
   number,cid=refs[0]
   value=json.dumps({'answer_vi':f'OFFLINE FIXTURE: minh họa giải thích có nguồn và giới hạn của một chương trình kết hợp. [Nguồn {number}]',
      'claims':[{'id':'1','text_vi':'Offline placeholder claim, not a live answer.','citation_chunk_ids':[cid]}],
      'limitations':['Engineering fixture; generation and semantic judgment are mocked.']})
  return {'text':value,'cache_status':'offline_test_double'}
async def no_dense(self,query,top_k):return []
async def main():
 runtime=AgenticRuntime.__new__(AgenticRuntime);runtime.root=P;runtime.gateway=Gateway()
 runtime.chunks=load_corpus(P);runtime.folder=P/'artifacts/llm_v2/index'/index_fingerprint(runtime.chunks)
 runtime.graph=MiniKG(P,runtime.chunks);runtime.pipeline_trace=[];runtime.readiness=lambda:{'index_ready':True}
 profile=json.loads((P/'datasets/demo_profiles.json').read_text())['profiles'][0]
 with patch.object(HybridSearcher,'_dense_search',no_dense):
  direct=await runtime.direct(QUESTION,'offline-r10')
  rag=await runtime.rag(QUESTION,'offline-r10',profile['profile'])
 assert len(runtime.gateway.observations)==4
 assert rag['status']=='complete' and rag['generation_calls_contract']['comparison_total']==4
 assert [s['id'] for s in rag['pipeline_trace']]==['pre_retrieval','risk','retrieval','rerank','reporter','verifier','release']
 assert all(s['status']=='complete' for s in rag['pipeline_trace'])
 assert rag['verification']['provider']=='gemini_semantic_plus_local_integrity'
 assert rag['verification']['risk_integrity_ok'] and f"{rag['risk']['score']:.6f}" in rag['answer_vi']
 assert all('high_bp' not in prompt and 'income' not in prompt for prompt in runtime.gateway.prompts)
 row={'id':'offline-r10','question':QUESTION,'question_id':'offline-r10','status':'complete','saved':True,'claim_revision':'offline-r10',
  'results':{'llm_direct':direct,'agentic_rag':rag},'fixture':'GENERATION_AND_SEMANTIC_REVIEW_MOCKED_DENSE_DISABLED_NOT_QUALITY_EVIDENCE'}
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'offline_pipeline_fixture.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 receipt={'status':'PASS','all_seven_stages_complete':True,'Risk_inference':'real existing TRAIN profile',
  'score':rag['risk']['score'],'mock_generation_calls':4,'new_generation_API_calls':0,'new_embedding_API_calls':0,
  'raw_profile_sent_to_provider':False,'semantic_review_quality_validated':False,'dense_disabled':True}
 (OUT/'pipeline_verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(receipt))
asyncio.run(main())
