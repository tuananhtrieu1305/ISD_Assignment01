"""One user-requested Gemini 3 Flash diagnostic, no retries or pipeline change."""
from pathlib import Path
from datetime import datetime,timezone
import json,signal,sys,time

P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'web/backend'))
from google import genai
from google.genai import types
from project01_llm_v2.provider import GeminiGateway,atomic_json,digest

F=P/'artifacts/llm_v2/phase2/development/gemini3_flash_probe_v1'
target=F/'result.json'
if target.exists():raise RuntimeError('Probe already consumed; do not rerun')
model='gemini-3-flash-preview'
body={'model':model,'contents':'Reply with exactly OK.',
      'config':{'temperature':0,'max_output_tokens':256,'thinking_level':'low'},'endpoint':'v1beta/models/'+model+':generateContent'}
call_prefix='diagnostic:gemini-3-flash:20261102:v1'
identifier=digest({'id':call_prefix,'kind':'generation','body':body})
gateway=GeminiGateway(P,True)
client=genai.Client(api_key=gateway.key,http_options=types.HttpOptions(api_version='v1beta',timeout=45000,retry_options=types.HttpRetryOptions(attempts=0)))
receipt={'date':datetime.now(timezone.utc).isoformat(),'model_requested':model,'endpoint':body['endpoint'],
 'model_documentation':'https://ai.google.dev/gemini-api/docs/models/gemini-3-flash-preview',
 'request_adapter':'installed google-genai standard generateContent; no external tools',
 'call_id':identifier,'automatic_retry':False,'sdk_timeout_seconds':45,'wall_clock_limit_seconds':55,
 'paid_budget_usd':0,'pipeline_model_changed':False,'usage':None,'SDK_attempts':0,
 'pricing_source':'https://ai.google.dev/gemini-api/docs/pricing',
 'access_policy_source':'https://ai.google.dev/gemini-api/docs/models/gemini-3-flash-preview'}

def expired(*_):raise TimeoutError('Probe wall-clock limit')
signal.signal(signal.SIGALRM,expired);signal.alarm(55)
started=time.monotonic()
try:
    with gateway.exclusive():
        now=time.time();usage=gateway.usage();day=usage['provider_day']
        with gateway.connect() as db:
            assert not db.execute('SELECT 1 FROM calls WHERE id=?',(identifier,)).fetchone(),'Claim already exists'
            recent=db.execute("SELECT count(*) FROM calls WHERE kind='generation' AND created>?",(now-60,)).fetchone()[0]
        assert usage['generation_attempts']<18 and recent<4,'Conservative shared generation cap reached'
        with gateway.connect() as db:db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',
            (identifier,'generation',day,now,'claimed',json.dumps(body),None))
        logs=P/'artifacts/llm_v2/phase2/api_calls'
        atomic_json(logs/(identifier+'_claim.json'),{'call_id':identifier,'kind':'generation','created':now,'call_prefix':call_prefix,'request':body,'status':'claimed'})
        atomic_json(F/'claim.json',receipt|{'status':'claimed'})
        receipt['SDK_attempts']=1
        try:
            response=client.models.generate_content(model=model,contents=body['contents'],
                config=types.GenerateContentConfig(temperature=0,max_output_tokens=256,thinking_config=types.ThinkingConfig(thinking_level='low')))
            payload=response.model_dump(mode='json',exclude_none=True)
            text='\n'.join(part.get('text','') for candidate in payload.get('candidates',[])
                for part in candidate.get('content',{}).get('parts',[]) if not part.get('thought'))
            receipt.update(status='complete' if text.strip() else 'empty_response',reply=text,
                reply_matches_OK=text.strip()=='OK',usage=payload.get('usage_metadata'),model_returned=payload.get('model_version'))
            status='complete' if text.strip() else 'unknown'
            atomic_json(logs/(identifier+'_response.json'),{'call_id':identifier,'status':status,'response':receipt})
        except Exception as exc:
            code=getattr(exc,'status_code',getattr(exc,'code',None))
            status='waiting_quota' if code==429 else 'unknown'
            safe_message=str(exc).replace(gateway.key,'[REDACTED]')[:1500]
            receipt.update(status='API_REJECTED' if isinstance(code,int) else 'FAILED',http_status=code if isinstance(code,int) else None,
                error_type=type(exc).__name__,safe_error_message=safe_message)
            atomic_json(logs/(identifier+'_error.json'),{'call_id':identifier,'status':status,'error_type':type(exc).__name__,
                'http_status':receipt['http_status'],'safe_error_message':safe_message})
        finally:
            receipt['elapsed_seconds']=round(time.monotonic()-started,3)
            with gateway.connect() as db:db.execute('UPDATE calls SET status=?,response=? WHERE id=?',
                (status,json.dumps(receipt,ensure_ascii=False),identifier))
except Exception as exc:
    receipt.setdefault('status','LOCAL_STOPPED');receipt['local_error_type']=type(exc).__name__
finally:
    signal.alarm(0);receipt['elapsed_seconds']=round(time.monotonic()-started,3)
    atomic_json(target,receipt);client.close()
print(json.dumps(receipt,ensure_ascii=False))
