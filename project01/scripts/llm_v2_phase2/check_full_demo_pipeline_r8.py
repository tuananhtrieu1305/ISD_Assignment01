"""Offline integration: real TRAIN risk/BM25/KG/reranker/verifier, fake generation.

Dense search is explicitly disabled here to avoid even a query embedding API call.
This is engineering acceptance, not proof that Gemini will answer either branch well.
"""
from pathlib import Path
from unittest.mock import patch
import asyncio,json,re,sys,time

P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.agents import AgenticRuntime
from project01_llm_v2.embedding import load_corpus,index_fingerprint
from project01_llm_v2.kg import MiniKG
from project01_llm_v2.retrieval import HybridSearcher

QUESTION='Đi bộ có giúp tôi giảm 58% nguy cơ tiểu đường không?'
TARGET='m2c-39c6512524216aa32b22'
OUT=P/'artifacts/llm_v2/phase2/development/full_demo_r8'

class OfflineGateway:
    def __init__(self):
        self.observations=[];self.prompts=[]
        self.config={'generation_model':'OFFLINE_TEST_DOUBLE','endpoint':'no-network'}
    def usage(self):return {'generation_attempts':0}
    def call(self,kind,body,call_id):
        assert kind=='generation' and call_id.endswith(':strategy')
        self.prompts.append(body['input'])
        self.observations.append({'cache_status':'offline_test_double','kind':'generation'})
        return {'text':json.dumps({'language':'vi','intent':'combined','queries':['walking 58 percent diabetes prevention lifestyle weight loss DPP'],
                     'entity_ids':['activity','type2'],'relation_direction':[],'scope':'diabetes'})}
    async def generate(self,prompt,call_id,tokens):
        self.prompts.append(prompt)
        self.observations.append({'cache_status':'offline_test_double','kind':'generation'})
        if call_id.endswith(':direct'):return {'text':'OFFLINE TEST DOUBLE: no statement about actual Gemini quality.','cache_status':'offline_test_double'}
        sources=re.findall(r'\[Nguồn (\d+)\] chunk_id=(\S+)',prompt)
        ids=[cid for _,cid in sources]
        assert TARGET in ids,'DPP source not in sparse+KG rerank output; do not claim coverage'
        source_number=next(number for number,cid in sources if cid==TARGET)
        return {'text':json.dumps({'answer_vi':f'Kết quả 58% trong nguồn thuộc chương trình thay đổi lối sống và giảm cân trong 3 năm, không phải mức giảm bảo đảm do đi bộ riêng lẻ. [Nguồn {source_number}]',
             'claims':[{'id':'1','text_vi':'Nguồn mô tả giảm nguy cơ 58% trong 3 năm ở nhóm thay đổi lối sống và giảm cân.','citation_chunk_ids':[TARGET]}],
             'limitations':['OFFLINE INTEGRATION FIXTURE: Gemini generation mocked; not a live response.']},ensure_ascii=False)}

async def no_dense(self,query,top_k):return []

async def main():
    runtime=AgenticRuntime.__new__(AgenticRuntime)
    runtime.root=P;runtime.gateway=OfflineGateway();runtime.chunks=load_corpus(P)
    runtime.folder=P/'artifacts/llm_v2/index'/index_fingerprint(runtime.chunks)
    runtime.graph=MiniKG(P,runtime.chunks);runtime.pipeline_trace=[]
    runtime.readiness=lambda:{'index_ready':True}
    profile=json.loads((P/'datasets/demo_profiles.json').read_text())['profiles'][0]
    with patch.object(HybridSearcher,'_dense_search',no_dense):
        direct=await runtime.direct(QUESTION,'offline-r8')
        rag=await runtime.rag(QUESTION,'offline-r8',profile['profile'])
    stages=rag['pipeline_trace']
    assert [row['id'] for row in stages]==['pre_retrieval','risk','retrieval','rerank','reporter','verifier','release']
    assert all(row['status']=='complete' for row in stages)
    assert len(runtime.gateway.observations)==3
    assert rag['status']=='complete' and rag['verification']['risk_integrity_ok']
    assert f"{rag['risk']['score']:.6f}" in rag['answer_vi']
    assert 'high_bp' not in '\n'.join(runtime.gateway.prompts)
    retrieved=next(row['output'] for row in stages if row['id']=='retrieval')
    assert len(retrieved['graph']['relationships'])>0
    row={'question':QUESTION,'question_id':'offline-r8-demo','status':'complete','model':'OFFLINE_TEST_DOUBLE',
         'claim_revision':'offline-r8','results':{'llm_direct':direct,'agentic_rag':rag},
         'fixture':'ENGINEERING_TEST_ONLY_GENERATION_MOCKED_DENSE_DISABLED', 'saved':True}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'offline_pipeline_fixture.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    receipt={'status':'PASS','question':QUESTION,'profile_id':profile['id'],'profile_origin':'matched TRAIN, not TEST',
      'score':rag['risk']['score'],'stages':[{'id':s['id'],'status':s['status']} for s in stages],
      'retrieved':len(rag['retrieved']),'evidence':len(rag['evidence']),'kg_candidate_count':retrieved['kg_candidate_count'],
      'graph_relationships_found':len(retrieved['graph']['relationships']),
      'selected_DPP_source':TARGET,'generation_test_double_calls':3,'new_generation_API_calls':0,'new_embedding_API_calls':0,
      'dense_disabled_for_offline_test':True,'actual_Gemini_quality_validated':False}
    (OUT/'offline_pipeline_verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

asyncio.run(main())
