"""One bounded pre-freeze diagnostic request; never replay an unknown claim."""
from pathlib import Path
from types import SimpleNamespace
import json, signal, sys, time
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from google import genai
from google.genai import types
from project01_llm_v2.provider import GeminiGateway, ProviderUnavailable, atomic_json

out=P/'artifacts/llm_v2/phase2/development/job_lifecycle_r4/provider_probe.json'
if out.exists():raise RuntimeError('Diagnostic receipt exists; do not replay probe')
gateway=GeminiGateway(P,True)
client=genai.Client(api_key=gateway.key,http_options=types.HttpOptions(timeout=45000,retry_options=types.HttpRetryOptions(attempts=0)))
class BoundedInteractions:
    def create(self,**kwargs):
        kwargs['timeout']=45.0
        return client.interactions.create(**kwargs)
gateway.client=SimpleNamespace(interactions=BoundedInteractions())
def hard_deadline(*_):raise TimeoutError('Diagnostic wall-clock limit')
signal.signal(signal.SIGALRM,hard_deadline)
signal.alarm(55)
started=time.monotonic()
receipt={'purpose':'single minimal generation probe; no medical question, RAG or held-out evaluation',
 'generation_model':'gemini-3.8-flash','endpoint':'v1beta/interactions','sdk_timeout_seconds':45,
 'wall_clock_limit_seconds':55,'paid_budget_usd':0,'automatic_retry':False,'quota_before':gateway.usage()}
try:
    value=gateway.call('generation',{'model':'gemini-3.8-flash','input':'Reply with exactly OK.',
        'store':False,'generation_config':{'temperature':0,'thinking_level':'low','max_output_tokens':64}},
        'diagnostic:job-lifecycle-r4:20261102:minimal-OK')
    receipt.update(status='complete',reply_matches_OK=value['text'].strip()=='OK',usage=value.get('usage'),call_id=value['call_id'])
except ProviderUnavailable as exc:
    receipt.update(status='not_complete',code=exc.code)
except Exception as exc:
    receipt.update(status='not_complete',error_type=type(exc).__name__)
finally:
    signal.alarm(0)
    receipt.update(elapsed_seconds=round(time.monotonic()-started,2),observations=gateway.observations,quota_after=gateway.usage())
    atomic_json(out,receipt)
    client.close()
print(json.dumps(receipt,ensure_ascii=False))
