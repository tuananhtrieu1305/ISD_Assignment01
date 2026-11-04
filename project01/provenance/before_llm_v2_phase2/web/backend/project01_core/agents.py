# GENERATED from notebooks/02_Diabetes_Multi_Agent.ipynb; source SHA256 78ed406f7ed41d3e6087036a6b9b09da14f8b12dbf65f8cc0b3a8ec744c1a180
# Edit the notebook, then run scripts/notebook_source.py export.
"""Five bounded roles; action traces, real tools, evidence checks and hard process deadline."""

import copy

import math

import multiprocessing as mp

import time

import uuid

from project01_core.foundation import LIMITATION, digest, focus_terms, plain, probability, tokenize, validate_profile

VARIANTS=('P0','P1','P2')

def validate_request(request):
    if not isinstance(request,dict) or set(request)-{'mode','question','profile','language'}:raise ValueError('Unexpected request fields')
    if request.get('mode') not in {'knowledge','numeric','combined'}:raise ValueError('Unknown mode')
    if request.get('language','en') not in {'en','vi'}:raise ValueError('Unknown language')
    question=request.get('question','')
    if not isinstance(question,str) or not 1<=len(question.strip())<=500 or any(ord(c)<32 for c in question):raise ValueError('Question must be 1–500 plain-text characters')
    profile=request.get('profile')
    if profile is not None and (not isinstance(profile,dict) or len(profile)>21):raise ValueError('Invalid profile object')
    return {**request,'language':request.get('language','en')}

def policy_reason(question):
    normalized=plain(question)
    refused=['ignore all','ignore your','ignore previous','guaranteed cure','cure for all','guaranteed profitable','recommend a guaranteed','insulin dose','antibiotic dose','personal insulin','issue a diagnosis','diagnose me','chan doan cho toi','ke don','lieu insulin','lieu thuoc','bo qua quy tac','tiet lo bi mat','reveal secrets']
    if any(term in normalized for term in refused):return 'request_outside_academic_scope'
    if any(term in normalized for term in ['price of gold','investment','apartment price','sale price','gia vang','gia nha','football']):return 'non_diabetes_domain'
    return None

def plan_request(request):
    return {'need_risk':request['mode'] in {'numeric','combined'},'need_knowledge':request['mode'] in {'knowledge','combined'},'mode':request['mode'],'policy':policy_reason(request['question'])}

def verify_outputs(runtime,request,risk,knowledge):
    """Separate numeric consistency, citation integrity and heuristic claim support."""
    errors=[];checks={};want=plan_request(request)
    if risk is not None:
        score=risk.get('score')
        correct=isinstance(score,(int,float)) and math.isfinite(score) and 0<=score<=1
        correct=correct and math.isclose(score,probability(risk['logit']),rel_tol=1e-6,abs_tol=1e-6)
        correct=correct and risk['profile_sha256']==digest(request['profile']) and risk['model_sha256']==runtime.model_hash
        checks['numeric_consistency']=bool(correct)
        if not correct:errors.append('numeric_mismatch')
    if knowledge is not None:
        evidence={row['chunk_id']:row for row in knowledge['evidence']}
        integrity=True
        for key,row in evidence.items():
            original=runtime.chunks.get(key)
            integrity=integrity and original is not None and original['text']==row['text'] and original['document_id']==row['document_id']
        checks['citation_integrity']=bool(integrity)
        cited=[evidence.get(key) for key in knowledge['citations']]
        support=bool(knowledge['answer'] and cited and all(row is not None for row in cited))
        focus=focus_terms(knowledge['query_normalized'])
        for row in cited:
            if row is None:continue
            support=support and knowledge['answer'] in row['text']
            support=support and (not focus or len(focus&set(tokenize(knowledge['answer'])))>=max(1,math.ceil(len(focus)*0.5)))
        checks['verbatim_focused_claim_support']=bool(support)
        if not integrity:errors.append('citation_integrity')
        if not support:errors.append('insufficient_or_unsupported_evidence')
    if want['need_risk'] and risk is None:checks['numeric_available']=False
    if want['need_knowledge'] and knowledge is None:checks['knowledge_available']=False
    return {'status':'passed' if not errors else 'rejected','checks':checks,'errors':errors,'support_method':'verbatim span + topic-token heuristic; not expert semantic entailment'}

def compose_answer(status,risk,knowledge,validation,errors,variant):
    sections=[]
    if risk is not None:
        sections.append({'title':'Đầu ra mô hình khảo sát','text':f"Score {risk['score']:.6f}; lớp {risk['class_id']}: {risk['class_name']}. Không phải xác suất mắc mới đã hiệu chuẩn."})
    if knowledge and knowledge['answer']:
        sections.append({'title':'Bằng chứng truy hồi · tiếng Anh','text':knowledge['answer']})
    if validation and not validation['valid']:
        sections.append({'title':'Cần bổ sung hồ sơ','text':'Thiếu: '+', '.join(validation['missing'])+'; sai: '+', '.join(validation['invalid']+validation['extra'])})
    if errors:sections.append({'title':'Giới hạn xử lý','text':'; '.join(errors)})
    return {'status':status,'sections':sections,'variant':variant,'limitation':LIMITATION,'synthesis':'verified_sections' if variant=='P2' else 'unverified_tool_outputs'}

def assist_inline(runtime,request,variant='P2',*,fault=None,deadline_seconds=30):
    request=validate_request(request)
    if variant not in VARIANTS:raise ValueError('Unknown variant')
    if fault not in {None,'missing_index','model_unavailable','citation_not_supporting','altered_numeric_value','deadline','empty_retrieval','transient'}:raise ValueError('Undeclared internal fault')
    start=time.perf_counter();deadline=start+deadline_seconds;trace=[];calls=0;errors=[]
    request_id='p01_'+uuid.uuid4().hex
    def event(agent,tool,started,output,outcome='ok'):
        trace.append({'node_id':f'n{len(trace)+1}','agent':agent,'tool':tool,'parent_ids':[trace[-1]['node_id']] if trace else [],'duration_ms':(time.perf_counter()-started)*1000,'outcome':outcome,'output':output})
    def tool_call(agent,name,function):
        nonlocal calls
        for attempt in range(2):
            if calls>=8 or time.perf_counter()>=deadline:raise TimeoutError('request_budget')
            tick=time.perf_counter();calls+=1
            if fault=='transient' and attempt==0:
                event(agent,name,tick,{'error':'transient','attempt':attempt},'error');continue
            value=function();event(agent,name,tick,{'result_sha256':digest(value),'attempt':attempt},'ok');return value
        raise RuntimeError('Tool retry budget exceeded')
    tick=time.perf_counter();plan=plan_request(request)
    event('Coordinator' if variant!='P0' else 'Direct','plan_request',tick,plan)
    risk=None;knowledge=None;validation=None;verification={'status':'not_run','checks':{}}
    if plan['policy']:
        errors.append(plan['policy']);status='refused'
    else:
        if fault=='deadline':time.sleep(deadline_seconds+0.3)
        if plan['need_risk']:
            tick=time.perf_counter();validation=validate_profile(request.get('profile'),runtime.schema)
            event('Risk Agent','validate_profile',tick,validation,'ok' if validation['valid'] else 'clarification')
            if validation['valid']:
                if fault=='model_unavailable':errors.append('model_unavailable')
                else:risk=tool_call('Risk Agent','predict_cdc',lambda:runtime.predict(request['profile']))
        if plan['need_knowledge']:
            if fault=='missing_index':errors.append('index_unavailable')
            else:
                knowledge=tool_call('Knowledge Agent','retrieve_medical',lambda:runtime.retrieve(request['question'],request['language']))
                if fault=='empty_retrieval':knowledge.update(answer='',citations=[],evidence=[],ranked_chunk_ids=[])
        if fault=='altered_numeric_value' and risk:risk['score']=0.99 if risk['score']<0.5 else 0.01
        if fault=='citation_not_supporting' and knowledge and knowledge['answer']:
            wrong=next(row for row in knowledge['evidence'] if knowledge['answer'] not in row['text']) if any(knowledge['answer'] not in r['text'] for r in knowledge['evidence']) else None
            if wrong:knowledge['citations']=[wrong['chunk_id']]
            else:knowledge['answer']='Unsupported universal cure claim.'
        if variant=='P2':
            tick=time.perf_counter();verification=verify_outputs(runtime,request,risk,knowledge)
            event('Verifier','check_outputs',tick,verification,'ok' if verification['status']=='passed' else 'rejected')
            if 'insufficient_or_unsupported_evidence' in verification['errors']:
                tick=time.perf_counter();event('Verifier','request_more_evidence',tick,{'remaining_loops':0,'reason':'missing_focused_support'})
                knowledge=tool_call('Knowledge Agent','retrieve_medical_expanded',lambda:runtime.retrieve(request['question'],request['language'],True))
                if fault=='empty_retrieval':knowledge.update(answer='',citations=[],evidence=[],ranked_chunk_ids=[])
                tick=time.perf_counter();verification=verify_outputs(runtime,request,risk,knowledge)
                event('Verifier','check_outputs_after_retrieval',tick,verification,'ok' if verification['status']=='passed' else 'rejected')
            if 'numeric_mismatch' in verification['errors']:risk=None;errors.append('numeric_mismatch_rejected')
            if any(e in verification['errors'] for e in ['citation_integrity','insufficient_or_unsupported_evidence']):
                errors.append('unsupported_knowledge_rejected')
                if knowledge:knowledge['answer']='';knowledge['citations']=[]
        if validation and not validation['valid']:status='clarification' if not knowledge or not knowledge['answer'] else 'partial'
        elif errors:status='unavailable' if not risk and not(knowledge and knowledge['answer']) else 'partial'
        elif plan['need_knowledge'] and not(knowledge and knowledge['answer']):status='insufficient_evidence' if risk is None else 'partial'
        else:status='answered'
    tick=time.perf_counter();answer=compose_answer(status,risk,knowledge,validation,errors,variant)
    event('Reporter' if variant=='P2' else 'Direct','compose',tick,{'status':status,'section_count':len(answer['sections'])})
    if time.perf_counter()>deadline:raise TimeoutError('request_budget')
    return {'request_id':request_id,'variant':variant,'status':status,'risk':risk,'knowledge':knowledge,'profile_validation':validation,'verification':verification,'answer':answer,'errors':errors,'trace':trace,'tool_calls':calls,'retrieval_loops':sum(node['tool']=='retrieve_medical_expanded' for node in trace),'latency_ms':(time.perf_counter()-start)*1000,'limitations':[LIMITATION],'input_sha256':digest(request)}

def _child_send(connection,runtime,request,variant,fault,deadline_seconds):
    try:connection.send({'result':assist_inline(runtime,request,variant,fault=fault,deadline_seconds=deadline_seconds)})
    except Exception as exc:connection.send({'error':type(exc).__name__})
    finally:connection.close()

def assist(runtime,request,variant='P2',*,fault=None,deadline_seconds=30):
    """Hard deadline with terminate/join; no lingering tool process after timeout."""
    validate_request(request)
    if not 0<deadline_seconds<=30:raise ValueError('Invalid deadline')
    if variant not in VARIANTS:raise ValueError('Invalid variant')
    started=time.perf_counter();context=mp.get_context('fork');parent,child=context.Pipe(duplex=False)
    process=context.Process(target=_child_send,args=(child,runtime,copy.deepcopy(request),variant,fault,deadline_seconds))
    process.start();child.close()
    response=None
    try:
        if parent.poll(max(0,deadline_seconds-(time.perf_counter()-started))):
            try:response=parent.recv()
            except EOFError:response=None
    finally:
        parent.close()
        if process.is_alive():process.terminate()
        process.join(timeout=1)
        if process.is_alive():process.kill();process.join()
    elapsed=(time.perf_counter()-started)*1000
    if response and 'result' in response:
        result=response['result'];result['latency_ms']=elapsed;result['worker_terminated']=not process.is_alive();return result
    timeout=response is None or response.get('error')=='TimeoutError'
    return {'request_id':'p01_'+uuid.uuid4().hex,'variant':variant,'status':'timeout' if timeout else 'unavailable','risk':None,'knowledge':None,'profile_validation':None,'verification':{'status':'not_run','checks':{}},'answer':{'status':'timeout' if timeout else 'unavailable','sections':[],'limitation':LIMITATION},'errors':['deadline' if timeout else 'worker_error'],'trace':[],'trace_status':'not_received','tool_calls':None,'retrieval_loops':None,'latency_ms':elapsed,'worker_terminated':not process.is_alive(),'limitations':[LIMITATION],'input_sha256':digest(request)}

