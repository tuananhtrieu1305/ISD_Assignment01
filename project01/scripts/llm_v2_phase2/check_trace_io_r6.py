"""Focused r6 checks. All model responses are fixtures; this file must never call Gemini."""
from pathlib import Path
import asyncio,json,sys

P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'web/backend'))

from project01_llm_v2.agents import AgenticRuntime,PipelineRecorder
from project01_llm_v2.generation import CALIBRATION_POLICY
from project01_llm_v2.reranker import GeminiReranker
from project01_llm_v2.schemas import MetaData,SearchResult

checks=[]
def ok(value,name):
    assert value,name
    checks.append(name)

class FakeGateway:
    def __init__(self,text=''):
        self.text=text
        self.observations=[]
        self.config={'generation_model':'fixture-model'}
        self.prompts=[]
    async def generate(self,prompt,call_id,max_tokens):
        self.prompts.append((prompt,call_id,max_tokens))
        row={'text':self.text,'cache_status':'fixture','usage':{},'finish_reasons':['STOP']}
        self.observations.append(row)
        return row

async def main():
    progress=[]
    gateway=FakeGateway()
    recorder=PipelineRecorder(gateway,progress.append,[])
    recorder.begin('pre_retrieval','Pre-retrieval','Coordinator',{'question':'Q'})
    gateway.observations.append({'cache_status':'live'})
    recorder.finish({'queries':['Q','query 2']})
    recorder.skip('risk','Risk','Risk Agent','Không kèm hồ sơ')
    recorder.begin('rerank','Reranking','Knowledge Agent',{'candidate_count':2})
    error=RuntimeError('secret must not be copied')
    recorder.fail(error)
    ok([row['status'] for row in recorder.steps]==['complete','skipped','failed'],'stage status captured')
    ok(recorder.steps[0]['output']['queries']==['Q','query 2'],'stage output captured')
    ok(recorder.steps[0]['calls']=={'live':1,'cache':0},'stage call observation counted')
    ok('secret' not in json.dumps(recorder.steps,ensure_ascii=False),'exception message not exposed')
    ok(progress==['Pre-retrieval','Pre-retrieval','Risk','Reranking','Reranking'],'progress flushes begin and finish')

    meta=MetaData(document_id='d',title='Demo',source='https://example.org',section='S')
    results=[SearchResult(chunk_id=f'c{i}',content=f'content {i}',chunk_index=i,metadata=meta,
                          score=1/(60+i),dense_rank=i+1,sparse_rank=i+1,kg_rank=None)
             for i in range(3)]
    rerank_gateway=FakeGateway(json.dumps({'ranking':[{'id':'c2','score':0.9},{'id':'c0','score':0.4}]}))
    reranker=GeminiReranker(rerank_gateway,'fixture')
    kept=await reranker.rerank('Q',results,top_n=1)
    report=reranker.last_report
    rows={row['chunk_id']:row for row in report['ranking']}
    ok([row.chunk_id for row in kept]==['c2'],'threshold and model order preserved')
    ok(rows['c2']['model_rank']==1 and rows['c2']['selected'],'selected rerank output explicit')
    ok(rows['c0']['reason']=='below_threshold' and not rows['c0']['selected'],'below threshold reason explicit')
    ok(rows['c1']['model_rank'] is None and rows['c1']['rerank_score'] is None and rows['c1']['reason']=='not_proposed','unproposed is null not zero')

    direct_gateway=FakeGateway('Câu trả lời fixture')
    runtime=AgenticRuntime.__new__(AgenticRuntime)
    runtime.gateway=direct_gateway
    await runtime.direct('Một câu hỏi bất kỳ','fixture')
    prompt=direct_gateway.prompts[0][0]
    ok(CALIBRATION_POLICY in prompt,'shared calibration policy reaches direct branch')
    ok('Bệnh thận có làm tăng nguy cơ tiểu đường không?' not in CALIBRATION_POLICY,'calibration is not edge-case hard coded')
    ok('không mặc định trả lời mơ hồ' in CALIBRATION_POLICY,'clear supported answers remain allowed')

    print(json.dumps({'status':'PASS','checks':checks,'api_calls':0},ensure_ascii=False,indent=2))

if __name__=='__main__':
    asyncio.run(main())
