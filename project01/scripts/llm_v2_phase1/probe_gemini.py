"""One free-tier preflight, key in header only; no secret or raw error output."""
from pathlib import Path
from datetime import datetime,timezone
import json
import os
import re
import time
import urllib.error
import urllib.request

PROJECT=Path(__file__).resolve().parents[2]
OUTPUT=PROJECT/'artifacts/llm_v2/phase1/gemini_preflight.json'
BASE='https://generativelanguage.googleapis.com/v1beta/'

def main():
    if OUTPUT.exists():raise RuntimeError('Probe receipt already exists; inspect, do not spend quota again blindly')
    key=os.environ.get('GEMINI_API_KEY','').strip()
    env=PROJECT/'.env'
    if not key and env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            name,sep,value=line.partition('=')
            if sep and name.strip()=='GEMINI_API_KEY':key=value.strip().strip('\"\'')
    receipt={'date':datetime.now(timezone.utc).isoformat(),'provider':'Gemini Developer API',
      'tier':'free_only_user_confirmed','paid_budget_usd':0,'key_present':bool(key),
      'key_value_saved':False,'generation_calls':0,'list_calls':0,'model':None}
    def request(path,payload=None):
        req=urllib.request.Request(BASE+path,data=json.dumps(payload).encode() if payload is not None else None,
             headers={'x-goog-api-key':key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=40) as response:return json.load(response)
        except urllib.error.HTTPError as exc:
            try:body=json.loads(exc.read())
            except (ValueError,OSError):body={}
            error=body.get('error',{})
            # Never persist provider message: it can contain request/key material.
            receipt.update(status='API_REJECTED',http_status=exc.code,error_status=error.get('status'),
                           reason_codes=[r.get('reason') for r in error.get('details',[]) if isinstance(r,dict) and r.get('reason')])
            raise RuntimeError('Provider request rejected') from None
    try:
        if not key:raise RuntimeError('Missing backend key')
        started=time.perf_counter();receipt['list_calls']=1
        listing=request('models?pageSize=1000')
        available={r['name'].removeprefix('models/'):r for r in listing.get('models',[]) if 'generateContent' in r.get('supportedGenerationMethods',[])}
        receipt['available_text_models']=sorted(available)
        # Both candidates have a standard free tier in official pricing; no paid/preview fallback.
        selected=next((name for name in ['gemini-3.8-flash','gemini-2.5-flash'] if name in available),None)
        if selected is None:receipt['status']='NO_ALLOWED_FREE_MODEL';raise RuntimeError('No approved model listed')
        receipt['model']=selected
        config={'temperature':0,'maxOutputTokens':64,'responseMimeType':'application/json',
                'responseSchema':{'type':'OBJECT','properties':{'ok':{'type':'BOOLEAN'}},'required':['ok']}}
        if selected=='gemini-2.5-flash':config['thinkingConfig']={'thinkingBudget':0}
        receipt['generation_calls']=1
        response=request('models/'+selected+':generateContent',{'contents':[{'role':'user','parts':[{'text':'Return only {"ok":true}.'}]}],'generationConfig':config})
        text=''.join(part.get('text','') for candidate in response.get('candidates',[]) for part in candidate.get('content',{}).get('parts',[]) if not part.get('thought'))
        assert json.loads(text).get('ok') is True
        receipt.update(status='PASS',latency_ms=(time.perf_counter()-started)*1000,usage=response.get('usageMetadata',{}),
                       model_version=response.get('modelVersion'),billing_independently_verified=False,
                       quota_limits='Not exposed by this API; confirm actual RPM/TPM/RPD in AI Studio',quota_bypass=False)
    except (RuntimeError,ValueError,AssertionError,urllib.error.URLError,OSError) as exc:
        receipt.setdefault('status','FAILED');receipt['local_error_type']=type(exc).__name__
    OUTPUT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='available_text_models'}))

if __name__=='__main__':main()
