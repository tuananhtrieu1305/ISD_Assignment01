"""Check packaged resources and existing key wiring with all network disabled."""
from pathlib import Path
import json
import os
import socket
import sys

ROOT=Path(__file__).resolve().parents[1]
AGENT=ROOT/'tieuluanfinal/web/agent'
sys.path.insert(0,str(AGENT/'web/backend'))
from project01_llm_v2.provider import load_key
from project01_llm_v2.agents import AgenticRuntime


def denied(*args,**kwargs):raise RuntimeError('Readiness check forbids network')


socket.create_connection=denied;socket.socket.connect=denied;socket.socket.connect_ex=denied
os.environ['GEMINI_STATE_ROOT']=str(ROOT/'project01/artifacts/llm_v2/runtime')
if not os.environ.get('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY']=load_key(ROOT/'tieuluanfinal') or load_key(ROOT/'project01')
runtime=AgenticRuntime(AGENT,False)
value=runtime.readiness()
assert value['status']=='ready' and value['index_ready'] and value['key_present']
assert value['runtime_revision']=='four-agent-r11' and len(value['agent_roles'])==4
assert value['chunks']==316 and value['kg_assertions']==35
assert value['generation_calls_per_comparison']==4
receipt={**value,'status':'PASS','network_disabled':True,'key_value_logged_or_copied':False,
         'new_generation_API_calls':0,'new_embedding_API_calls':0,'shared_quota_ledger':True}
(ROOT/'tieuluanfinal/docs/final_revision/readiness.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='usage'}))
