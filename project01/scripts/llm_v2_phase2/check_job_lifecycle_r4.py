"""Error-path regression checks only; no live API or answer-quality claims."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import asyncio, json, sys, tempfile, threading, time, uuid

P=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(P/'web/backend'))
from project01_llm_v2 import transport
from project01_llm_v2.provider import atomic_json, read_json, ProviderUnavailable

checks=[]
def check(value,name):
    assert value,name
    checks.append(name)

def until_finished(folder,identifier):
    path=folder/(identifier+'.json')
    for _ in range(200):
        try:row=read_json(path)
        except (FileNotFoundError,json.JSONDecodeError):time.sleep(.01);continue
        if row['status'] not in {'queued','running'}:
            handle=transport.JobJournal(folder).acquire(identifier)
            if handle is not None:
                transport.JobJournal.release(handle)
                return row
        time.sleep(.01)
    raise AssertionError('Worker did not finalize')

with tempfile.TemporaryDirectory(dir=P/'artifacts/llm_v2/phase2') as tmp:
    root=Path(tmp);folder=root/'artifacts/llm_v2/jobs'
    journal=transport.JobJournal(folder);identifier=str(uuid.uuid4());path=folder/(identifier+'.json')
    atomic_json(path,{'id':identifier,'status':'running','created_at':time.time()-300,'profile':{'demo':True},'results':{},'progress':'LLM trực tiếp'})
    original=path.read_bytes();lease=journal.acquire(identifier)
    check(journal.read(path)['status']=='running','active leased worker is not marked interrupted')
    journal.release(lease);row=journal.read(path)
    check(row['status']=='interrupted' and row['profile'] is None,'unleased orphan becomes interrupted and drops profile')
    backups=list((folder/'recovery_snapshots').glob('*.json'))
    check(len(backups)==1 and backups[0].read_bytes()==original,'orphan original bytes preserved before recovery')
    journal.read(path)
    check(len(list((folder/'recovery_snapshots').glob('*.json')))==1,'repeated GET never repeats recovery or generation')
    check(journal.acquire(identifier) is not None,'recovery releases worker lease')

    class Runtime:
        def __init__(self,*args):self.gateway=SimpleNamespace(observations=[])

    async def broken(runtime,variant,*args):
        raise RuntimeError('SECRET_DO_NOT_EXPOSE')
    with patch.object(transport,'AgenticRuntime',Runtime),patch.object(transport,'resume_branch',broken):
        app=transport.create_app(root,True);client=app.test_client()
        first=client.post('/api/v2/compare',json={'question':'Câu hỏi thử lỗi'})
        row=until_finished(folder,first.json['id'])
        check(row['status']=='failed' and row['error']['error_type']=='RuntimeError','unexpected worker exception becomes terminal failure')
        check('SECRET_DO_NOT_EXPOSE' not in json.dumps(row),'internal exception text not exposed')
        check('profile' not in client.get('/api/v2/jobs/'+row['id']).json,'GET never exposes local profile')
        check(client.post('/api/v2/jobs/'+row['id']+'/resume',json={}).status_code==409,'failed unknown request cannot be silently replayed')
        again=client.post('/api/v2/compare',json={'question':'Câu thử thứ hai'})
        check(again.status_code==202,'worker failure releases busy semaphore')
        until_finished(folder,again.json['id'])

    called=[]
    async def timeout(runtime,variant,*args):
        called.append(variant)
        runtime.gateway.observations.append({'error_type':'APITimeoutError','http_status':None,'latency_ms':180021,'call_id':'synthetic-timeout'})
        raise ProviderUnavailable('unknown','Synthetic provider fault')
    with patch.object(transport,'AgenticRuntime',Runtime),patch.object(transport,'resume_branch',timeout):
        client=transport.create_app(root,True).test_client()
        response=client.post('/api/v2/compare',json={'question':'Timeout thử'})
        row=until_finished(folder,response.json['id'])
        check(row['status']=='failed' and '180' in row['error']['message'],'Gemini timeout message includes measured wait')
        check(row['branch_states']=={'llm_direct':'failed','agentic_rag':'skipped'},'provider fault marks RAG not started rather than running')
        for _ in range(4):client.get('/api/v2/jobs/'+row['id'])
        check(called==['llm_direct'],'polling and provider failure never trigger another model call')
        check(row['results']=={},'provider timeout never fabricates an answer')

    async def partial(runtime,variant,*args):
        if variant=='llm_direct':return {'status':'complete','answer_vi':'SYNTHETIC_TRANSPORT_TEST_ONLY'}
        raise ProviderUnavailable('unknown','Synthetic rerank fault')
    with patch.object(transport,'AgenticRuntime',Runtime),patch.object(transport,'resume_branch',partial):
        client=transport.create_app(root,True).test_client()
        response=client.post('/api/v2/compare',json={'question':'Giữ kết quả đã xong'})
        row=until_finished(folder,response.json['id'])
        check('llm_direct' in row['results'] and 'agentic_rag' not in row['results'],'later RAG fault preserves completed direct result')

    entered=threading.Event();finish=threading.Event()
    async def waiting(runtime,variant,*args):
        entered.set()
        await asyncio.to_thread(finish.wait,2)
        raise ProviderUnavailable('waiting_quota','Synthetic quota fault')
    with patch.object(transport,'AgenticRuntime',Runtime),patch.object(transport,'resume_branch',waiting):
        client=transport.create_app(root,True).test_client()
        response=client.post('/api/v2/compare',json={'question':'Chờ quota thử'})
        assert entered.wait(2)
        row=client.get('/api/v2/jobs/'+response.json['id']).json
        check(row['status']=='running' and row['elapsed_seconds']>=0 and row['stage_elapsed_seconds']>=0,'live GET exposes elapsed/stage without interrupting worker')
        check(client.post('/api/v2/compare',json={'question':'Lượt trùng'}).status_code==429,'concurrent compare rejected while worker active')
        finish.set();row=until_finished(folder,response.json['id'])
        check(row['status']=='waiting_quota','quota pause remains distinct from unknown timeout')

receipt={'status':'PASS','checks':checks,'count':len(checks),'new_live_API_calls':0,
 'mock_scope':'job lifecycle, timeout/quota/runtime failures only; not LLM quality acceptance'}
out=P/'artifacts/llm_v2/phase2/development/job_lifecycle_r4'/('checks_'+str(time.time_ns())+'.json')
atomic_json(out,receipt)
print(json.dumps(receipt,ensure_ascii=False))
