"""Final bounded endpoint compatibility probe using current Gemini Interactions docs."""
from pathlib import Path
from datetime import datetime,timezone
import json
import time
import urllib.request
import urllib.error

PROJECT=Path(__file__).resolve().parents[2]
TARGET=PROJECT/'artifacts/llm_v2/phase1/gemini_interactions_preflight.json'

def main():
    if TARGET.exists():raise RuntimeError('Compatibility probe already claimed')
    key=next(line.partition('=')[2].strip().strip('\"\'') for line in (PROJECT/'.env').read_text().splitlines() if line.partition('=')[0].strip()=='GEMINI_API_KEY')
    receipt={'date':datetime.now(timezone.utc).isoformat(),'model':'gemini-3.8-flash',
      'endpoint':'v1beta/interactions','documentation':'https://ai.google.dev/gemini-api/docs/interactions-overview',
      'reason':'Compatibility probe for current documented endpoint after generateContent timeout and old-model 404; final preflight attempt this turn',
      'generation_calls':1,'paid_budget_usd':0,'key_value_saved':False,'status':'CLAIMED'}
    TARGET.write_text(json.dumps(receipt,indent=2)+'\n')
    body={'model':'gemini-3.8-flash','input':'Return only the word OK.','store':False,
          'generation_config':{'temperature':0,'max_output_tokens':32,'thinking_level':'low'}}
    req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/interactions',data=json.dumps(body).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
    start=time.perf_counter()
    try:
        with urllib.request.urlopen(req,timeout=90) as response:payload=json.load(response)
        def collect(value):
            if isinstance(value,dict):
                return [v for k,v in value.items() if k in {'text','output_text'} and isinstance(v,str)]+[s for k,v in value.items() if k not in {'thought','thoughts','reasoning'} and not(k in {'text','output_text'} and isinstance(v,str)) for s in collect(v)]
            if isinstance(value,list):return [s for item in value for s in collect(item)]
            return []
        texts=collect(payload)
        receipt.update(status='PASS' if any('OK'==s.strip().strip('.!') for s in texts) else 'RESPONSE_NOT_CONFIRMED',
                       response_status=payload.get('status'),usage=payload.get('usage'),model_version=payload.get('model'),
                       response_keys=list(payload))
    except urllib.error.HTTPError as exc:
        try:body=json.loads(exc.read())
        except (ValueError,OSError):body={}
        error=body.get('error',{})
        receipt.update(status='API_REJECTED',http_status=exc.code,error_status=error.get('status'),
                       sanitized_error_message=str(error.get('message','')).replace(key,'[REDACTED]')[:350])
    except (OSError,ValueError,urllib.error.URLError) as exc:receipt.update(status='FAILED',local_error_type=type(exc).__name__)
    receipt['latency_ms']=(time.perf_counter()-start)*1000
    TARGET.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':main()
