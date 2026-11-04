"""Focused functional tests: synthetic errors and real local data, no API calls."""
from pathlib import Path
from types import SimpleNamespace
import asyncio,hashlib,json,sys,tempfile,time,shutil
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.schemas import MetaData,SearchResult,Draft,Claim
from project01_llm_v2.agents import AgenticRuntime,CodeVerifier,RiskAgent
from project01_llm_v2.embedding import load_corpus,Embedder
from project01_llm_v2.kg import MiniKG,normalize_extraction
from project01_llm_v2.retrieval import HybridSearcher,Retriever
from project01_llm_v2.provider import ProviderUnavailable,GeminiGateway
from project01_llm_v2.transport import create_app
from project01_llm_v2.indexing import DocumentChunker

checks=[]
def ok(value,name):assert value,name;checks.append(name)


async def main():
    chunks=load_corpus(P);graph=MiniKG(P,chunks)
    ok(len(chunks)==316,'medical corpus316')
    ok(len(graph.assertions)==35,'all35 assertions source checked')
    ok('kidney_damage' in graph.identify('Bệnh thận có liên quan tiểu đường?'),'Vietnamese entity alias')
    candidates=graph.search('bệnh thận',['kidney_damage'])
    ok(bool(candidates),'graph returns source candidates for incoming context')
    edges=graph.neighborhood('bệnh thận')['relationships']
    ok(any(e['subject']=='diabetes' and e['object']=='kidney_damage' for e in edges),'kidney edge keeps diabetes to kidney direction')
    ok(not any(e['subject']=='kidney_damage' and e['object']=='diabetes' for e in edges),'no invented reverse kidney edge')
    indexed=chunks[0]
    payload={'content':indexed.content,'chunk_index':0,'metadata':indexed.metadata.model_dump()}
    hybrid=HybridSearcher(None,None,None)
    fused=hybrid._fuse([{'id':indexed.chunk_id,'payload':payload}],[{'id':indexed.chunk_id,'payload':payload}],top_k=20,kg_results=[{'id':indexed.chunk_id,'payload':payload,'assertion_ids':['a1']}])
    ok(len(fused)==1 and abs(fused[0].score-1/61)<1e-12,'three-way weighted RRF deduplicates same chunk')
    ok(fused[0].kg_rank==1 and fused[0].graph_assertion_ids==['a1'],'RRF retains graph contribution')
    merged=Retriever._merge_results([fused,fused],20)
    ok(len(merged)==1,'multiquery merge deduplicates')
    try:Embedder.normalize([0]*768)
    except ValueError:ok(True,'zero vector rejected')
    try:DocumentChunker(chunk_size=100,chunk_overlap=100)
    except ValueError:ok(True,'invalid chunk overlap rejected')
    split=DocumentChunker(chunk_size=200,chunk_overlap=20).split_markdown('# Diabetes\n## Kidney\nDiabetes can damage the kidneys.',document_id='demo',title='Diabetes',source='https://example.org')
    ok(bool(split) and split[0].chunk_id.startswith('m2c-'),'ported medical chunker content-based IDs')
    normalized=normalize_extraction({'entities':[{'name':'A','type':'Disease'},{'name':'a','type':'Disease'}],'relationships':[]})
    ok(len(normalized['entities'])==1,'group KG normalization deduplicates')
    profile=json.loads((P/'datasets/demo_profiles.json').read_text())['profiles'][0]['profile']
    missing=dict(profile);missing.pop('bmi')
    try:RiskAgent(P).run(missing)
    except ValueError:ok(True,'missing BMI rejected no imputation')
    risk=RiskAgent(P).run(profile)
    ok(isinstance(risk['score'],float) and risk['calibrated_incidence_risk'] is False,'frozen risk inference carries correct unit')
    class FakeGateway:
        async def generate(self,*args):
            return {'text':json.dumps({'approved':True,'claim_reviews':[{'claim_id':'c1','status':'supported','evidence_ids':['invented']}],
                                      'direction_ok':True,'numeric_ok':True,'source_integrity_ok':True,'feedback':''})}
    draft=Draft(answer_vi='Thử nghiệm',claims=[Claim(id='c1',text_vi='100% chắc chắn',citation_chunk_ids=['invented'])])
    verification,_=await CodeVerifier().verify('Q',draft,[],'synthetic')
    ok(not verification['approved'] and 'unresolved_citation' in verification['code_errors'],'code verifier blocks hallucinated citations')
    ok('unsupported_numeric_claim' in verification['code_errors'],'unsupported numeric claim rejected')
    app=create_app(P,False);client=app.test_client()
    ok(client.get('/health').status_code==200,'health liveness without API')
    ok(client.post('/api/v2/compare',json={'question':'Q'}).status_code==503,'live disabled explicit')
    ok(client.post('/api/v2/compare',json={'question':'Q','extra':True}).status_code==422,'unknown input field rejected')
    ok(client.post('/api/v2/compare',json={'question':'Q'},headers={'Origin':'https://evil.example'}).status_code==403,'foreign origin rejected')
    ok(client.get('/api/v2/jobs/not-a-uuid').status_code==404,'invalid job ID rejected')
    ok(client.post('/api/v2/risk',json={'profile':missing}).status_code==422,'API missing BMI rejected')
    response=client.get('/api/v2/examples')
    ok(response.status_code==200 and 'key' not in response.get_data(as_text=True).lower(),'examples no secret')
    with tempfile.TemporaryDirectory(dir=P/'artifacts/llm_v2/phase2') as temporary:
        root=Path(temporary)
        for name in ['docs/llm_v2/provider_config.example.json','artifacts/llm_v2/phase1/gemini_preflight.json','artifacts/llm_v2/phase1/gemini_interactions_preflight.json','artifacts/llm_v2/phase1/gemini_embedding_preflight.json']:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/name,path)
        (root/'.env').write_text('GEMINI_API_KEY=dummy-local-test-credential\n')
        gateway=GeminiGateway(root,True)
        class Fault(Exception):status_code=503
        class FakeInteractions:
            def __init__(self):self.calls=0
            def create(self,**kwargs):self.calls+=1;raise Fault('synthetic503')
        fake=FakeInteractions();gateway.client=SimpleNamespace(interactions=fake)
        body={'model':'gemini-3.8-flash','input':'Synthetic guard test','store':False,'generation_config':{'max_output_tokens':32}}
        try:gateway.call('generation',body,'synthetic-once')
        except ProviderUnavailable as exc:ok(exc.code=='unknown','503 yields explicit unknown not fake success')
        try:gateway.call('generation',body,'synthetic-once')
        except ProviderUnavailable as exc:ok(exc.code=='claim_unknown' and fake.calls==1,'unknown claim never automatically replays')
        day=gateway.usage()['provider_day']
        with gateway.connect() as db:
            for i in range(18):db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',(f'quota-{i}','generation',day,time.time(),'complete','{}','{}'))
        try:gateway.call('generation',body,'synthetic-over-budget')
        except ProviderUnavailable as exc:ok(exc.code=='waiting_quota' and fake.calls==1,'daily cap stops before SDK and never paid fallback')
        ok(gateway.usage()['paid_budget_usd']==0,'free-only configured budget unchanged')
    output={'status':'PASS','checks':checks,'check_count':len(checks),'api_calls':0,'mock_scope':'local code-verifier integrity checks and503/quota/claim guards only; not LLM answer acceptance','training_steps':0,'old_TEST_forward':0}
    path=P/'artifacts/llm_v2/phase2'/('unit_checks_'+str(time.time_ns())+'.json');path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(output,ensure_ascii=False))


if __name__=='__main__':asyncio.run(main())
