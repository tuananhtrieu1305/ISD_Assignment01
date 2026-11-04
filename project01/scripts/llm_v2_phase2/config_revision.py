from pathlib import Path
import json
P=Path(__file__).resolve().parents[2]
target=P/'docs/llm_v2/runtime_config.json'
if target.exists():raise RuntimeError('Revision already exists')
config=json.loads((P/'docs/llm_v2/provider_config.example.json').read_text())
config['config_version']='llm-v2-development-r2';config['queue']['request_timeout_seconds']=180
config['queue']['comparison_deadline_seconds']=1500
config['status']='DEVELOPMENT_NOT_HELD_OUT_FROZEN'
target.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
receipt={'revision':'development-r2','reason':'Real20-candidate rerank request hit90-second SDK timeout before any held-out evaluation',
         'original_call_id':'d203e69833611dba8ebe032b903e4cdbd2b6a1fb5cdaf733d0d3cd292b3abd17',
         'original_status':'unknown, provider consumption not recoverable, store=false',
         'old_timeout_seconds':90,'new_timeout_seconds':180,'new_comparison_deadline_seconds':1500,
         'new_rerank_claim_suffix':':rerank:r2','completed_direct_planner_and_embedding_calls_reused':True,
         'model_or_paid_budget_changed':False,'held_out_opened':False,
         'additional_change':'sort KG frontier for deterministic candidate ranks before freeze'}
(P/'artifacts/llm_v2/phase2/development/revision_r2.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('Development r2 declared; original timeout claim kept untouched')
