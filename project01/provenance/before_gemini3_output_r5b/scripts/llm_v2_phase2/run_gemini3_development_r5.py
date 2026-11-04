"""One declared development case; separate lineage from failed 3.8 attempts."""
from pathlib import Path
import asyncio,json,sys,time
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2.agents import AgenticRuntime
from project01_llm_v2.evaluation import resume_branch
from project01_llm_v2.provider import ProviderUnavailable,atomic_json

async def main():
    folder=P/'artifacts/llm_v2/phase2/development/gemini3_switch_r5'
    path=folder/'development.json'
    if path.exists():raise RuntimeError('Development already consumed; do not rerun')
    cases=[json.loads(line) for line in (P/'datasets/llm_v2/evaluation_v1/development_questions.jsonl').read_text().splitlines()]
    case=next(row for row in cases if row['id']=='v2-dev-05')
    runtime=AgenticRuntime(P,True)
    state={'question_id':case['id'],'question':case['question_vi'],'model':'gemini-3-flash-preview',
           'claim_revision':'gemini3-r5','results':{},'status':'running','held_out':False,'created_at':time.time()}
    atomic_json(path,state)
    def progress(stage):
        state['progress']=stage;atomic_json(path,state);print(stage,flush=True)
    try:
        for variant in ['llm_direct','agentic_rag']:
            progress(variant)
            state['results'][variant]=await resume_branch(runtime,variant,case['question_vi'],'gemini3-r5:'+case['id'],progress=progress,deadline=300)
            atomic_json(path,state)
        state['status']='complete'
    except ProviderUnavailable as exc:
        state.update(status=exc.code,error_type=type(exc).__name__)
    except Exception as exc:
        state.update(status='development_error',error_type=type(exc).__name__)
    finally:
        state['finished_at']=time.time();state['observations']=runtime.gateway.observations
        atomic_json(path,state)
    print(json.dumps({'status':state['status'],'model':state['model'],'question_id':case['id'],
        'elapsed_seconds':round(state['finished_at']-state['created_at'],2),
        'results':{v:{'status':r['status'],'answer_vi':r.get('answer_vi'),'citations':len(r.get('citations',[])),
                      'model':r.get('model'),'verification':r.get('verification')} for v,r in state['results'].items()},
        'error_type':state.get('error_type'),'saved_to':path.relative_to(P).as_posix()},ensure_ascii=False),flush=True)

if __name__=='__main__':asyncio.run(main())
