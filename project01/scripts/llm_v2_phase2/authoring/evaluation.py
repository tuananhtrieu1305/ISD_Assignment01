"""Single-claim held-out evaluation and saved-result analysis; never training."""
from pathlib import Path
from datetime import datetime,timezone
import asyncio,hashlib,json,os,random,time


def read_rows(path):return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]


def file_hash(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temporary.replace(path)


async def resume_branch(runtime,variant,question,call_prefix,profile=None,progress=None,deadline=900):
    from .provider import ProviderUnavailable
    started=time.monotonic();usage_start=len(runtime.gateway.observations);minute_retries=0
    while True:
        try:
            remaining=deadline-(time.monotonic()-started)
            if remaining<=0:raise ProviderUnavailable('timeout','Đã hết thời gian pipeline.')
            if variant=='llm_direct':task=runtime.direct(question,call_prefix)
            else:task=runtime.rag(question,call_prefix,profile,progress)
            result=await asyncio.wait_for(task,remaining)
            result['usage']=runtime.gateway.observations[usage_start:]
            result['latency_ms']=(time.monotonic()-started)*1000
            result['minute_retries']=minute_retries
            return result
        except ProviderUnavailable as exc:
            if exc.code=='waiting_minute' and minute_retries<2 and time.monotonic()-started+61<deadline:
                minute_retries+=1
                if progress:progress('Đợi quota theo phút · giữ bước đã hoàn tất')
                await asyncio.sleep(60)
                continue
            raise


def planned_order(questions):
    generator=random.Random(20261102);output=[]
    for index,case in enumerate(questions):
        variants=['llm_direct','agentic_rag']
        if index%2:variants.reverse()
        output.extend((case,variant) for variant in variants)
    generator.shuffle(output)
    return output


async def evaluate(root,max_new_outputs=None):
    from .agents import AgenticRuntime
    from .provider import ProviderUnavailable
    root=Path(root);phase=root/'artifacts/llm_v2/phase2'
    freeze=json.loads((phase/'freeze.json').read_text())
    if freeze['stage']!='HELD_OUT_FROZEN':raise ValueError('No approved freeze')
    for record in freeze['files']:
        if file_hash(root/record['path'])!=record['sha256']:raise ValueError('Frozen input drift: '+record['path'])
    questions=read_rows(root/'datasets/llm_v2/evaluation_v1/held_out_questions.jsonl')
    assert len(questions)==40
    folder=phase/'evaluation';folder.mkdir(parents=True,exist_ok=True)
    lock=folder/'runner.lock'
    import fcntl
    with lock.open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('One evaluation runner only')
        runtime=AgenticRuntime(root,allow_api=True);new=0
        for case,variant in planned_order(questions):
            identifier=case['id']+'_'+variant;output=folder/'results'/(identifier+'.json');claim=folder/'claims'/(identifier+'.json')
            if output.exists():continue
            if max_new_outputs is not None and new>=max_new_outputs:break
            state=json.loads(claim.read_text()) if claim.exists() else {'id':identifier,'freeze_id':freeze['freeze_id'],'created_at':datetime.now(timezone.utc).isoformat(),'state':'claimed'}
            if state['freeze_id']!=freeze['freeze_id']:raise ValueError('Claim freeze mismatch')
            if state['state'] in {'unknown','failed','complete'}:raise ValueError('Consumed claim without final output; require incident revision')
            save_json(claim,state)
            try:
                result=await resume_branch(runtime,variant,case['question_vi'],'evaluation:'+freeze['freeze_id']+':'+identifier)
                result['freeze_id']=freeze['freeze_id']
                models={r.get('model_returned') for r in result['usage'] if r.get('kind')=='generation'}
                if models!={freeze['model_returned']}:raise ValueError('Provider model/version drift')
                state['state']='complete'
            except ProviderUnavailable as exc:
                if exc.code in {'waiting_quota','waiting_minute','claim_waiting_quota'}:
                    state['state']='waiting_quota';state['reason']=exc.code;save_json(claim,state)
                    save_json(folder/'checkpoint.json',{'status':'WAITING_QUOTA','next_claim':identifier,'new_outputs_this_run':new,'models_changed':False})
                    return {'status':'WAITING_QUOTA','new_outputs':new,'next_claim':identifier}
                state['state']='failed';state['reason']=exc.code
                result={'variant':variant,'question':case['question_vi'],'status':'provider_error','answer_vi':'','error_code':exc.code,'usage':[],
                        'latency_ms':None,'freeze_id':freeze['freeze_id']}
            except (ValueError,asyncio.TimeoutError) as exc:
                state['state']='unknown';state['reason']=type(exc).__name__
                result={'variant':variant,'question':case['question_vi'],'status':'provider_error','answer_vi':'','error_code':type(exc).__name__,
                        'usage':[],'latency_ms':None,'freeze_id':freeze['freeze_id']}
            save_json(output,{'question_id':case['id'],'variant':variant,'repeat':1,'category':case['category'],'result':result,'created_at':datetime.now(timezone.utc).isoformat()})
            save_json(claim,state);new+=1
        count=len(list((folder/'results').glob('*.json')))
        status='OUTPUTS_COMPLETE_REVIEW_PENDING' if count==80 else 'IN_PROGRESS'
        save_json(folder/'checkpoint.json',{'status':status,'outputs':count,'new_outputs_this_run':new})
        return {'status':status,'outputs':count,'new_outputs':new}


def blinded_review_pack(root):
    root=Path(root);folder=root/'artifacts/llm_v2/phase2/evaluation'
    rows=[json.loads(p.read_text()) for p in sorted((folder/'results').glob('*.json'))]
    by_question={}
    for row in rows:by_question.setdefault(row['question_id'],[]).append(row)
    public=[];mapping=[]
    for i,(qid,group) in enumerate(sorted(by_question.items())):
        group=sorted(group,key=lambda r:r['variant'],reverse=bool(i%2))
        for label,row in zip(['A','B'],group):
            public.append({'question_id':qid,'label':label,'question':row['result']['question'],'answer_vi':row['result']['answer_vi'],
                           'scores':{'focus':None,'correctness':None,'completeness':None,'limits':None},'critical_error':None,'reviewer':None})
            mapping.append({'question_id':qid,'label':label,'variant':row['variant']})
    save_json(folder/'review_pack.json',{'scope':'assistant/manual review pending, branch names hidden; citations may reveal RAG','rows':public})
    save_json(folder/'review_mapping.json',mapping)
    return len(public)


def summarize_saved(root):
    root=Path(root);folder=root/'artifacts/llm_v2/phase2/evaluation'
    rows=[json.loads(p.read_text()) for p in sorted((folder/'results').glob('*.json'))]
    summary=[]
    for variant in ['llm_direct','agentic_rag']:
        selected=[r for r in rows if r['variant']==variant]
        summary.append({'variant':variant,'outputs':len(selected),'expected':40,
                        'complete':sum(r['result']['status']=='complete' for r in selected),
                        'errors':sum(r['result']['status']=='provider_error' for r in selected),
                        'quality_score':None,'quality_review':'pending','paid_budget_usd':0})
    return {'status':'not_complete' if len(rows)<80 else 'outputs_complete_review_pending','rows':summary,
            'historical_results_reused':False,'clinical_accuracy_claimed':False}
