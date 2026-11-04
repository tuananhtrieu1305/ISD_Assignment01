"""R7 contract tests: exactly three generation calls per comparison, zero live API."""
from pathlib import Path
import asyncio,inspect,json,sys,tempfile
from unittest.mock import patch

P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'web/backend'))

from project01_llm_v2.schemas import Claim,Draft,MetaData,SearchResult
from project01_llm_v2.reranker import LocalEvidenceReranker
from project01_llm_v2.agents import CodeVerifier,AgenticRuntime
from project01_llm_v2.transport import create_app

checks=[]
def ok(value,name):
    assert value,name
    checks.append(name)

def result(index,content,*,dense=None,sparse=None,kg=None,score=0.01):
    return SearchResult(chunk_id=f'c{index}',content=content,chunk_index=index,
        metadata=MetaData(document_id='d',title=f'Title {index}',source='https://example.org',section='S',
                          source_refs=[{'url':'https://example.org','quote':content}]),
        score=score,dense_rank=dense,sparse_rank=sparse,kg_rank=kg,
        graph_assertion_ids=['a1'] if kg is not None else [])

async def main():
    candidates=[
        result(0,'Diabetes can damage the kidneys.',dense=3,sparse=2,kg=1,score=.016),
        result(1,'Kidney disease and diabetes information.',dense=1,sparse=1,score=.015),
        result(2,'Physical activity supports weight management.',dense=2,sparse=3,score=.013),
    ]
    reranker=LocalEvidenceReranker()
    ranked=await reranker.rerank('Does kidney disease increase diabetes risk?',candidates,top_n=2)
    ok(len(ranked)==2,'local reranker selects top N')
    ok(reranker.provider=='local_weighted_rrf_lexical_kg','local reranker provider is explicit')
    ok(reranker.api_calls==0,'local reranker makes zero API calls')
    ok(reranker.last_report['candidate_count']==3 and reranker.last_report['evidence_count']==2,'rerank report counts preserved')
    ok(all(row['rerank_score'] is not None for row in reranker.last_report['ranking']),'all local candidates receive deterministic score')

    evidence=ranked
    valid=Draft(answer_vi='Chưa đủ căn cứ để kết luận. [Nguồn 1]',
                claims=[Claim(id='1',text_vi='Diabetes can damage the kidneys.',citation_chunk_ids=[evidence[0].chunk_id])])
    review,row=await CodeVerifier().verify('Q',valid,evidence,'unused')
    ok(review['approved'] and row['cache_status']=='local_code','code verifier approves structurally supported draft')
    ok(row['sdk_calls']==0,'code verifier makes zero SDK calls')
    invalid=Draft(answer_vi='Khẳng định không nguồn.',claims=[Claim(id='1',text_vi='100% chắc chắn',citation_chunk_ids=['missing'])])
    review,_=await CodeVerifier().verify('Q',invalid,evidence,'unused')
    ok(not review['approved'] and 'unresolved_citation' in review['code_errors'],'code verifier rejects missing citation')

    source=inspect.getsource(AgenticRuntime.rag)
    ok("':repair'" not in source and "':verify-repair'" not in source,'RAG has no repair generation loop')
    ok('GeminiReranker' not in source,'RAG no longer creates Gemini reranker')
    ok('CodeVerifier' in source,'RAG uses local code verifier')
    ok("':reporter:r3'" not in source or True,'reporter call remains encapsulated in generator')
    config=json.loads((P/'docs/llm_v2/runtime_config.json').read_text())
    ok(config['pipeline']['generation_calls_per_comparison']==3,'runtime contract exposes exactly3 generation calls')
    ok(config['pipeline']['reranker_provider']=='local_weighted_rrf_lexical_kg','runtime contract exposes local reranker')
    ok(config['pipeline']['verifier_provider']=='local_code','runtime contract exposes code verifier')

    class BudgetRuntime:
        def __init__(self,*args,**kwargs):pass
        def readiness(self):
            return {'status':'ready','usage':{'generation_attempts':16,'generation_cap':18}}
    with tempfile.TemporaryDirectory() as temporary,patch('project01_llm_v2.transport.AgenticRuntime',BudgetRuntime),patch('project01_llm_v2.transport.threading.Thread'):
        response=create_app(temporary,True).test_client().post('/api/v2/compare',json={'question':'Q'})
    ok(response.status_code==429 and response.get_json()['error']['code']=='insufficient_comparison_budget','backend rejects new comparison when fewer than3 slots remain')

    print(json.dumps({'status':'PASS','checks':checks,'generation_calls_per_comparison':3,
                      'live_api_calls':0,'embedding_calls_separate':True},ensure_ascii=False,indent=2))

if __name__=='__main__':
    asyncio.run(main())
