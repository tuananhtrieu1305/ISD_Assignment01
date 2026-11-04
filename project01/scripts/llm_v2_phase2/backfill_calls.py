"""Export existing durable call rows with explicit backfill lineage, no new API call."""
from pathlib import Path
import json,sqlite3
P=Path(__file__).resolve().parents[2];folder=P/'artifacts/llm_v2/phase2/api_calls';folder.mkdir(parents=True,exist_ok=True)
with sqlite3.connect(P/'artifacts/llm_v2/runtime/calls.sqlite3') as db:rows=db.execute('SELECT id,kind,created,status,request,response FROM calls').fetchall()
count=0
for identifier,kind,created,status,request,response in rows:
    if status=='historical':continue
    path=folder/(identifier+'_claim.json')
    if not path.exists():
        path.write_text(json.dumps({'call_id':identifier,'kind':kind,'created':created,'request':json.loads(request),
                                   'status':'claimed','call_prefix':None,'backfilled_from_SQLite':True},ensure_ascii=False,indent=2)+'\n');count+=1
    path=folder/(identifier+('_response.json' if status=='complete' else '_error.json'))
    if status!='claimed' and not path.exists():
        path.write_text(json.dumps({'call_id':identifier,'status':status,'response':json.loads(response or '{}'),
                                   'backfilled_from_SQLite':True},ensure_ascii=False,indent=2)+'\n');count+=1
print(json.dumps({'exported':count,'new_API_calls':0}))
