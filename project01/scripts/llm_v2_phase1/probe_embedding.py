"""Single free-tier embedding preflight; not an index build or QA evaluation."""
from pathlib import Path
from datetime import datetime,timezone
import urllib.request
import urllib.error
import json
import math
import time

P=Path(__file__).resolve().parents[2]
T=P/'artifacts/llm_v2/phase1/gemini_embedding_preflight.json'


def main():
    if T.exists():raise RuntimeError('Embedding probe already claimed')
    key=next(line.partition('=')[2].strip().strip('\"\'') for line in (P/'.env').read_text().splitlines() if line.partition('=')[0].strip()=='GEMINI_API_KEY')
    receipt={'date':datetime.now(timezone.utc).isoformat(),'status':'CLAIMED','model':'gemini-embedding-001',
             'embedding_calls':1,'paid_budget_usd':0,'key_value_saved':False,
             'task_type':'RETRIEVAL_DOCUMENT','requested_dimensions':768,'input':'Public diabetes knowledge.',
             'documentation':'https://ai.google.dev/gemini-api/docs/embeddings'}
    T.write_text(json.dumps(receipt,indent=2)+'\n')
    body={'model':'models/gemini-embedding-001','content':{'parts':[{'text':'Public diabetes knowledge.'}]},
          'taskType':'RETRIEVAL_DOCUMENT','outputDimensionality':768}
    req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent',
        data=json.dumps(body).encode(),headers={'Content-Type':'application/json','x-goog-api-key':key})
    start=time.perf_counter()
    try:
        with urllib.request.urlopen(req,timeout=90) as response:payload=json.load(response)
        values=payload.get('embedding',{}).get('values',[])
        receipt.update(status='PASS' if len(values)==768 and all(math.isfinite(v) for v in values) and sum(v*v for v in values)>0 else 'INVALID_VECTOR',
                       returned_dimensions=len(values),vector_saved=False,usage=payload.get('usageMetadata'))
    except urllib.error.HTTPError as exc:
        receipt.update(status='API_REJECTED',http_status=exc.code)
    except (OSError,ValueError) as exc:receipt.update(status='FAILED',local_error_type=type(exc).__name__)
    receipt['latency_ms']=(time.perf_counter()-start)*1000
    T.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))


if __name__=='__main__':main()
