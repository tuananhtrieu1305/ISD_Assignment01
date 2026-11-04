# GENERATED from notebooks/02_Diabetes_Multi_Agent.ipynb; source SHA256 63eb21ead1e8c67cc077fc4139eb2b771eb0f391309ad03f9d32a5661e81b956
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
"""Flask comparison jobs; keys stay server-side, health never calls Gemini."""

from pathlib import Path

from collections import defaultdict,deque

import asyncio,fcntl,hashlib,json,os,threading,time,uuid

from flask import Flask,jsonify,request,send_from_directory

from pydantic import ValidationError

from .agents import AgenticRuntime

from .provider import ProviderUnavailable,atomic_json,read_json

from .schemas import CompareRequest

from .evaluation import resume_branch

class JobJournal:
    """A process-held lease distinguishes live work from JSON left after a crash.

    Recovery preserves the original bytes; it never retries a provider claim.
    """
    def __init__(self,folder):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)

    def acquire(self,job_id):
        handle=(self.folder/(job_id+'.lease')).open('a')
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:handle.close();return None
        return handle

    @staticmethod
    def release(handle):
        if handle is not None:fcntl.flock(handle,fcntl.LOCK_UN);handle.close()

    def read(self,path):
        state=read_json(path)
        if state['status'] in {'queued','running'}:
            handle=self.acquire(state['id'])
            if handle is not None:
                try:
                    state=read_json(path)
                    if state['status'] in {'queued','running'}:
                        original=Path(path).read_bytes()
                        backup=self.folder/'recovery_snapshots'/(state['id']+'-'+hashlib.sha256(original).hexdigest()+'.json')
                        backup.parent.mkdir(parents=True,exist_ok=True)
                        if not backup.exists():backup.write_bytes(original)
                        state.update(status='interrupted',updated_at=time.time(),finished_at=time.time(),profile=None)
                        state['error']={'code':'worker_interrupted','message':'Backend đã dừng hoặc khởi động lại khi đang xử lý. Lượt cũ đã gián đoạn; không tự gửi lại request Gemini chưa rõ kết quả.'}
                        state['progress']='Lượt chạy bị gián đoạn'
                        state['branch_states']={v:('complete' if v in state.get('results',{}) else 'interrupted') for v in ['llm_direct','agentic_rag']}
                        atomic_json(path,state)
                finally:self.release(handle)
        end=state.get('finished_at',time.time())
        state['elapsed_seconds']=max(0,end-state['created_at'])
        state['stage_elapsed_seconds']=max(0,end-state.get('stage_started_at',state['created_at']))
        state['observed_at']=time.time()
        return state


def create_app(project_root=None,allow_api=False):
    root=Path(project_root or Path(__file__).resolve().parents[3])
    app=Flask(__name__,static_folder=None);app.config['MAX_CONTENT_LENGTH']=16*1024
    busy=threading.BoundedSemaphore(1);rates=defaultdict(deque)
    jobs=root/'artifacts/llm_v2/jobs';journal=JobJournal(jobs)
    allowed={o.strip().rstrip('/') for o in os.environ.get('WEB_ORIGIN','http://127.0.0.1:5179,http://localhost:5179,http://127.0.0.1:8031,http://localhost:8031').split(',') if o.strip()}
    def error(code,message,status):return jsonify(error={'code':code,'message':message}),status
    def path_for(job_id):
        try:uuid.UUID(job_id)
        except (ValueError,AttributeError):return None
        return jobs/(job_id+'.json')
    @app.before_request
    def guard():
        origin=request.headers.get('Origin','').rstrip('/')
        if origin and origin not in allowed and origin!=request.host_url.rstrip('/'):return error('origin_not_allowed','Origin chưa được cấu hình.',403)
        if request.method=='OPTIONS':return '',204
        if request.method=='POST':
            key=request.remote_addr or 'local';now=time.monotonic();bucket=rates[key]
            while bucket and bucket[0]<now-60:bucket.popleft()
            if len(bucket)>=6:return error('rate_limit','Tối đa6 yêu cầu thao tác/phút.',429)
            bucket.append(now)
    @app.after_request
    def headers(response):
        origin=request.headers.get('Origin','').rstrip('/')
        if origin in allowed:response.headers['Access-Control-Allow-Origin']=origin;response.headers['Vary']='Origin'
        response.headers['Access-Control-Allow-Methods']='GET,POST,OPTIONS'
        response.headers['Access-Control-Allow-Headers']='Content-Type'
        response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='same-origin'
        response.headers['Cache-Control']='no-store'
        return response
    @app.errorhandler(413)
    def too_large(_):return error('request_too_large','Giới hạn JSON16KiB.',413)
    @app.errorhandler(400)
    def malformed(_):return error('invalid_json','Cần JSON hợp lệ.',400)
    @app.get('/health')
    def health():return jsonify(status='ok',project='project01',revision='llm-v2')
    @app.get('/ready')
    def ready():
        try:
            state=AgenticRuntime(root,False).readiness();state['live_enabled']=allow_api
            return jsonify(state),200 if state['status']=='ready' else 503
        except (OSError,ValueError,ImportError,KeyError):return error('assets_unavailable','Dữ liệu hoặc cấu hình chưa sẵn sàng.',503)
    @app.get('/api/v2/knowledge-graph')
    def knowledge_graph():
        try:
            from .kg import MiniKG
            from .embedding import load_corpus
            graph=MiniKG(root,load_corpus(root))
            return jsonify(schema_version='knowledge-graph-r11',
                nodes=[{'id':n['id'],'label':n['name'],'type':n['type'],'aliases':n['aliases']} for n in graph.entities.values()],
                edges=[{'id':e['id'],'source':e['subject'],'target':e['object'],'relation':e['relation'],
                        'conditions':e.get('conditions',''),'polarity':e.get('polarity',''),
                        'quote':e['quote'],'source_chunk_ids':e['source_chunk_ids'],'source_url':e['source_url'],
                        'review_status':e['review']['status']} for e in graph.assertions],
                source='existing reviewed mini-KG used by retrieval',
                note='35 concept nodes and source-checked assertions; not all facts in the316-chunk KB or independent clinical review.',
                generation_API_calls=0,embedding_API_calls=0)
        except (OSError,ValueError,KeyError):return error('kg_unavailable','Chưa đọc được KG có kiểm nguồn.',503)
    def execute(path,lease):
        state=read_json(path);runtime=None;variant=None
        def persist():
            state['updated_at']=time.time();atomic_json(path,state)
        try:
            state.update(status='running',error=None);persist()
            runtime=AgenticRuntime(root,allow_api)
            async def run():
                nonlocal variant
                for variant in ['llm_direct','agentic_rag']:
                    if variant in state['results']:continue
                    state['current_branch']=variant;state['branch_states'][variant]='running'
                    def progress(stage):
                        if state.get('progress')!=stage:state['stage_started_at']=time.time()
                        state['progress']=stage
                        state.setdefault('pipeline_traces',{})['agentic_rag']=json.loads(json.dumps(getattr(runtime,'pipeline_trace',[])))
                        persist()
                    progress('LLM trực tiếp · chờ Gemini' if variant=='llm_direct' else 'Hệ đa agent + RAG')
                    result=await resume_branch(runtime,variant,state['question'],'web:'+state['id'],None,progress)
                    state['results'][variant]=result;state['branch_states'][variant]='complete';persist()
            asyncio.run(run());state['status']='complete';state['progress']='Đã hoàn tất hai nhánh'
        except ProviderUnavailable as exc:
            state['status']='waiting_quota' if exc.code in {'waiting_quota','waiting_minute','claim_waiting_quota'} else 'failed'
            state['error']={'code':exc.code,'message':str(exc)}
            observation=next((o for o in reversed(runtime.gateway.observations if runtime else []) if o.get('error_type')),None)
            if observation:
                state['error'].update({k:observation.get(k) for k in ['error_type','http_status','latency_ms','call_id']})
                if observation['error_type']=='APITimeoutError':
                    seconds=round(observation['latency_ms']/1000)
                    state['error']['message']=f'Gemini không trả kết quả trong khoảng {seconds} giây (timeout). Không tự gọi lại; kết quả xử lý tại provider chưa xác định.'
                elif observation.get('http_status')==503:
                    state['error']['message']='Gemini trả HTTP 503: dịch vụ hiện không xử lý được yêu cầu. Không tự gọi lại request này.'
        except Exception as exc:
            # Persist every ordinary worker failure, including SDK/runtime errors;
            # never expose an exception message, prompt, key or stack to the UI.
            state['status']='failed';state['error']={'code':'worker_error','error_type':type(exc).__name__,'message':'Bước xử lý bị lỗi nội bộ. Lượt đã dừng; không tự gửi lại request Gemini.'}
        finally:
            try:
                if state['status']!='waiting_quota':state['profile']=None;state['finished_at']=time.time()
                if variant and state['status']!='complete':state['branch_states'][variant]=state['status']
                if state['status'] not in {'complete','waiting_quota'}:
                    state['progress']='Đã dừng do lỗi'
                    for name,status in state['branch_states'].items():
                        if status=='pending':state['branch_states'][name]='skipped'
                state.setdefault('pipeline_traces',{})['agentic_rag']=json.loads(json.dumps(getattr(runtime,'pipeline_trace',[])))
                persist()
            finally:journal.release(lease);busy.release()
    @app.post('/api/v2/compare')
    def compare():
        if not request.is_json:return error('content_type','Dùng application/json.',415)
        try:
            data=CompareRequest.model_validate(request.get_json())
        except (ValidationError,ValueError,TypeError):return error('invalid_request','Chỉ nhận question (1–4096 ký tự); pipeline mới không nhận hồ sơ CDC.',422)
        if not allow_api:return error('live_disabled','Live API chưa được bật ở backend.',503)
        usage=AgenticRuntime(root,False).readiness()['usage']
        remaining=max(0,usage['generation_cap']-usage['generation_attempts'])
        if remaining<4:return error('insufficient_comparison_budget',f'Cần đủ4 generation request để hoàn tất hai nhánh; hiện chỉ còn {remaining}. Không tạo job dở dang.',429)
        if not busy.acquire(blocking=False):return error('busy','Một lượt so sánh đang chạy. Chờ hoàn tất trước lượt mới.',429)
        job_id=str(uuid.uuid4());path=path_for(job_id)
        lease=journal.acquire(job_id)
        atomic_json(path,{'id':job_id,'status':'queued','question':data.question,
                          'runtime_revision':'four-agent-r11',
                          'results':{},'branch_states':{'llm_direct':'pending','agentic_rag':'pending'},
                          'progress':'Đang chờ','created_at':time.time(),'error':None})
        try:threading.Thread(target=execute,args=(path,lease),daemon=True).start()
        except Exception:
            journal.release(lease);busy.release();raise
        return jsonify(id=job_id,status='queued'),202
    @app.get('/api/v2/jobs/<job_id>')
    def job(job_id):
        path=path_for(job_id)
        if path is None or not path.exists():return error('not_found','Không tìm thấy lượt chạy.',404)
        data=journal.read(path);data.pop('profile',None)
        return jsonify(data)
    @app.post('/api/v2/jobs/<job_id>/resume')
    def resume(job_id):
        path=path_for(job_id)
        if path is None or not path.exists():return error('not_found','Không tìm thấy lượt chạy.',404)
        previous=journal.read(path)
        if previous['status']!='waiting_quota':return error('not_resumable','Chỉ tiếp tục lượt đang chờ quota.',409)
        if previous.get('runtime_revision')!='four-agent-r11':return error('revision_mismatch','Lượt cũ dùng pipeline khác; giữ kết quả cũ, không tự gọi tiếp bằng prompt mới.',409)
        usage=AgenticRuntime(root,False).readiness()['usage']
        needed=3 if 'llm_direct' in previous['results'] else 4
        if usage['generation_cap']-usage['generation_attempts']<needed:return error('insufficient_comparison_budget',f'Cần còn ít nhất {needed} generation request để tiếp tục.',429)
        if not busy.acquire(blocking=False):return error('busy','Đã có lượt chạy.',429)
        lease=journal.acquire(job_id)
        if lease is None:busy.release();return error('busy','Lượt này đang có worker xử lý.',409)
        state=read_json(path);state.pop('finished_at',None)
        state['branch_states']={v:('complete' if v in state['results'] else 'pending') for v in ['llm_direct','agentic_rag']}
        atomic_json(path,state)
        try:threading.Thread(target=execute,args=(path,lease),daemon=True).start()
        except Exception:
            journal.release(lease);busy.release();raise
        return jsonify(id=job_id,status='queued'),202
    @app.get('/api/v2/development')
    def development():
        folder=root/'artifacts/llm_v2/phase2/development'
        return jsonify(mode='saved_development_not_new_live_call',rows=[read_json(p) for p in sorted([*folder.glob('*.json'),*folder.glob('**/development.json')]) if 'results' in read_json(p)])
    @app.route('/',defaults={'path':''})
    @app.route('/<path:path>')
    def frontend(path):
        if path.startswith('api/'):return error('not_found','API không tồn tại.',404)
        folder=root/'web/frontend/dist';candidate=(folder/path).resolve()
        if path and candidate.is_relative_to(folder.resolve()) and candidate.is_file():return send_from_directory(folder,path)
        if (folder/'index.html').exists():return send_from_directory(folder,'index.html')
        return jsonify(project='project01',frontend='Build React trước khi mở giao diện',health='/health')
    return app

