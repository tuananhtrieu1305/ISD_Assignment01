"""Synthetic provider adapter regressions; no external calls."""
from pathlib import Path
from types import SimpleNamespace
import asyncio,json,shutil,sys,tempfile,time
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.provider import GeminiGateway,ProviderUnavailable,atomic_json
from project01_llm_v2.schemas import Claim,Draft
from project01_llm_v2.agents import parse_json,AgenticRuntime
checks=[]
def ok(value,name):assert value,name;checks.append(name)

with tempfile.TemporaryDirectory(dir=P/'artifacts/llm_v2/phase2') as temp:
    root=Path(temp)
    for name in ['docs/llm_v2/runtime_config.json','artifacts/llm_v2/phase1/gemini_preflight.json','artifacts/llm_v2/phase1/gemini_interactions_preflight.json','artifacts/llm_v2/phase1/gemini_embedding_preflight.json']:
        out=root/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/name,out)
    (root/'.env').write_text('GEMINI_API_KEY=dummy-local-test-credential\n')
    gateway=GeminiGateway(root,True)
    class Models:
        finish='STOP'
        def __init__(self):self.calls=[]
        def generate_content(self,**kwargs):
            self.calls.append(kwargs)
            payload={'candidates':[{'content':{'parts':[{'thought':True,'text':'PRIVATE_THOUGHT_NOT_PERSISTED'},{'text':'{"answer_vi":"synthetic"}'}]},'finish_reason':self.finish}],
                     'usage_metadata':{'prompt_token_count':5,'candidates_token_count':3,'thoughts_token_count':2,'total_token_count':10},'model_version':'gemini-3-flash-preview'}
            return SimpleNamespace(model_dump=lambda **_:payload)
    fake=Models();gateway.client=SimpleNamespace(models=fake)
    row=asyncio.run(gateway.generate('Synthetic guard','unit:reporter:r3',768))
    config=fake.calls[0]['config']
    ok(fake.calls[0]['model']=='gemini-3-flash-preview','configured Gemini3 model reaches standard API adapter')
    ok(config.response_mime_type=='application/json','Reporter requests native JSON mode')
    ok(config.max_output_tokens==2048 and str(config.thinking_config.thinking_level).rsplit('.',1)[-1].lower()=='minimal','new thinking/output budget applied')
    ok(row['usage']['total_tokens']==10 and row['usage']['thought_tokens']==2,'provider usage normalized without inventing missing data')
    ok('PRIVATE_THOUGHT' not in json.dumps(row),'thought text filtered from persisted result')
    ok(row['endpoint']=='v1beta/generateContent' and row['finish_reasons']==['STOP'],'endpoint and finish reason recorded')
    again=asyncio.run(gateway.generate('Synthetic guard','unit:reporter:r3',768))
    ok(len(fake.calls)==1 and again['cache_status']=='local_cache','completed unchanged request reuses durable cache')
    fake.finish='MAX_TOKENS'
    try:asyncio.run(gateway.generate('Synthetic guard clipped','unit:reporter:r3:clipped',768))
    except ProviderUnavailable as exc:ok(exc.code=='output_incomplete','truncated output is never accepted as complete')
    ok(len(list((root/'artifacts/llm_v2/phase2/api_calls').glob('*_incomplete_response.json')))==1,'incomplete final text retained as diagnostic evidence')
    claim=Claim(id=1,text_vi='Synthetic',citation_chunk_ids=[])
    ok(claim.id=='1','integer claim label canonicalized without changing medical text')
    try:Claim(id=True,text_vi='Synthetic')
    except ValueError:ok(True,'boolean claim label rejected')
    original=json.loads((P/'artifacts/llm_v2/phase2/api_calls/49ca76b75c498f96e3ba558aaa0ed3ff6968262f0011c2a1afad26286b356291_response.json').read_text())['response']['text']
    draft=Draft.model_validate(parse_json(original))
    ok(draft.answer_vi==parse_json(original)['answer_vi'],'actual cached Reporter text remains byte-equivalent after ID schema conversion')
state=AgenticRuntime(P,False).readiness()
atomic_json(P/'artifacts/llm_v2/phase2/development/gemini3_switch_r5/readiness_snapshot.json',state)
ok(state['generation_model']=='gemini-3-flash-preview' and state['generation_endpoint']=='v1beta/generateContent','readiness advertises active model/endpoint without API')
out=P/'artifacts/llm_v2/phase2/development/gemini3_switch_r5'/('adapter_checks_'+str(time.time_ns())+'.json')
receipt={'status':'PASS','checks':checks,'count':len(checks),'new_live_API_calls':0,'mock_scope':'SDK payload routing/cache/error guards only, not clinical answer quality'}
atomic_json(out,receipt);print(json.dumps(receipt))
