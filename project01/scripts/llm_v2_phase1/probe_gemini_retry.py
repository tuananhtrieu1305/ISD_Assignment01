"""One declared development retry on the other approved free model; retain timeout receipt."""
from pathlib import Path
from datetime import datetime,timezone
import json
import time
import urllib.request
import urllib.error

PROJECT=Path(__file__).resolve().parents[2]
TARGET=PROJECT/'artifacts/llm_v2/phase1/gemini_preflight_retry1.json'

def main():
    if TARGET.exists():raise RuntimeError('Retry already claimed; do not repeat')
    previous=json.loads((TARGET.parent/'gemini_preflight.json').read_text())
    assert previous['status']=='FAILED' and previous.get('local_error_type')=='TimeoutError'
    assert 'gemini-2.5-flash' in previous['available_text_models']
    key=next(line.partition('=')[2].strip().strip('\"\'') for line in (PROJECT/'.env').read_text().splitlines() if line.partition('=')[0].strip()=='GEMINI_API_KEY')
    receipt={'date':datetime.now(timezone.utc).isoformat(),'model':'gemini-2.5-flash','reason':'First model timed out; one bounded development retry on another documented standard free-tier model before protocol/model freeze','generation_calls':1,'paid_budget_usd':0,'key_value_saved':False,'prior_timeout_retained':True}
    TARGET.write_text(json.dumps({**receipt,'status':'CLAIMED'},indent=2)+'\n')
    body={'contents':[{'role':'user','parts':[{'text':'Reply only with the JSON object {"ok":true}.'}]}],
      'generationConfig':{'temperature':0,'maxOutputTokens':64,'thinkingConfig':{'thinkingBudget':0},'responseMimeType':'application/json'}}
    req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',data=json.dumps(body).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
    started=time.perf_counter()
    try:
        with urllib.request.urlopen(req,timeout=80) as response:payload=json.load(response)
        output=''.join(part.get('text','') for item in payload.get('candidates',[]) for part in item.get('content',{}).get('parts',[]) if not part.get('thought'))
        assert json.loads(output)['ok'] is True
        receipt.update(status='PASS',usage=payload.get('usageMetadata',{}),model_version=payload.get('modelVersion'))
    except urllib.error.HTTPError as exc:
        try:body=json.loads(exc.read())
        except (ValueError,OSError):body={}
        receipt.update(status='API_REJECTED',http_status=exc.code,error_status=body.get('error',{}).get('status'))
    except (OSError,ValueError,AssertionError,urllib.error.URLError) as exc:receipt.update(status='FAILED',local_error_type=type(exc).__name__)
    receipt['latency_ms']=(time.perf_counter()-started)*1000
    TARGET.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':main()
