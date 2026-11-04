# GENERATED from notebooks/02_Diabetes_Multi_Agent.ipynb; source SHA256 2a59b41c84c78dcd055b0feb8373d79862f8c4fa92a3eebf2084438c18c221ab
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
"""Flask comparison jobs; keys stay server-side, health never calls Gemini."""

from pathlib import Path

from collections import defaultdict,deque

import asyncio,json,os,threading,time,uuid

from flask import Flask,jsonify,request,send_from_directory

from pydantic import ValidationError

from .agents import AgenticRuntime,RiskAgent

from .provider import ProviderUnavailable,atomic_json,read_json

from .schemas import CompareRequest

from .evaluation import resume_branch,summarize_saved

def create_app(project_root=None,allow_api=False):
    root=Path(project_root or Path(__file__).resolve().parents[3])
    app=Flask(__name__,static_folder=None);app.config['MAX_CONTENT_LENGTH']=16*1024
    busy=threading.BoundedSemaphore(1);rates=defaultdict(deque)
    jobs=root/'artifacts/llm_v2/jobs';jobs.mkdir(parents=True,exist_ok=True)
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
    @app.get('/api/v2/examples')
    def examples():
        return jsonify(questions=[{'title':'Vận động và đường huyết','question':'Vận động có ích gì cho cân nặng và đường huyết?'},
                                  {'title':'Kiểm tra chiều quan hệ','question':'Bệnh thận có làm tăng nguy cơ tiểu đường không?'}],
                       profiles=read_json(root/'datasets/demo_profiles.json')['profiles'],schema=read_json(root/'datasets/profile_schema.json'))
    @app.get('/api/v2/summary')
    def summary():return jsonify(summarize_saved(root))
    @app.post('/api/v2/risk')
    def risk():
        try:
            data=request.get_json()
            if not isinstance(data,dict) or set(data)!={'profile'}:raise ValueError('profile required')
            return jsonify(RiskAgent(root).run(data['profile']))
        except (ValueError,TypeError,KeyError):return error('invalid_profile','Cần đủ21 field hợp lệ; không tự điền field thiếu.',422)
    def execute(path):
        state=read_json(path)
        try:
            runtime=AgenticRuntime(root,allow_api)
            state.update(status='running',error=None);atomic_json(path,state)
            async def run():
                for variant in ['llm_direct','agentic_rag']:
                    if variant in state['results']:continue
                    def progress(stage):state['progress']=stage;atomic_json(path,state)
                    progress('LLM trực tiếp' if variant=='llm_direct' else 'Hệ đa agent + RAG')
                    result=await resume_branch(runtime,variant,state['question'],'web:'+state['id'],state.get('profile'),progress)
                    state['results'][variant]=result;atomic_json(path,state)
            asyncio.run(run());state['status']='complete';state['progress']='Đã hoàn tất hai nhánh'
        except ProviderUnavailable as exc:
            state['status']='waiting_quota' if exc.code in {'waiting_quota','waiting_minute','claim_waiting_quota'} else 'failed'
            state['error']={'code':exc.code,'message':str(exc)}
        except (ValueError,OSError,KeyError,asyncio.TimeoutError) as exc:
            state['status']='failed';state['error']={'code':type(exc).__name__,'message':'Lượt xử lý chưa hoàn tất. Chi tiết đã giữ để kiểm tra, không tạo câu trả lời giả.'}
        finally:
            if state['status']!='waiting_quota':state['profile']=None
            atomic_json(path,state);busy.release()
    @app.post('/api/v2/compare')
    def compare():
        if not request.is_json:return error('content_type','Dùng application/json.',415)
        try:
            data=CompareRequest.model_validate(request.get_json())
            if data.mode not in {'knowledge','combined'}:raise ValueError('mode')
            if data.profile is not None:RiskAgent(root).run(data.profile)
        except (ValidationError,ValueError,TypeError):return error('invalid_request','Kiểm tra câu hỏi/phạm vi và21 field nếu có hồ sơ.',422)
        if not allow_api:return error('live_disabled','Live API chưa được bật ở backend.',503)
        if not busy.acquire(blocking=False):return error('busy','Một lượt so sánh đang chạy. Chờ hoàn tất trước lượt mới.',429)
        job_id=str(uuid.uuid4());path=path_for(job_id)
        atomic_json(path,{'id':job_id,'status':'queued','question':data.question,'profile':data.profile,
                          'results':{},'progress':'Đang chờ','created_at':time.time(),'error':None})
        threading.Thread(target=execute,args=(path,),daemon=True).start()
        return jsonify(id=job_id,status='queued'),202
    @app.get('/api/v2/jobs/<job_id>')
    def job(job_id):
        path=path_for(job_id)
        if path is None or not path.exists():return error('not_found','Không tìm thấy lượt chạy.',404)
        data=read_json(path);data.pop('profile',None)
        return jsonify(data)
    @app.post('/api/v2/jobs/<job_id>/resume')
    def resume(job_id):
        path=path_for(job_id)
        if path is None or not path.exists():return error('not_found','Không tìm thấy lượt chạy.',404)
        if read_json(path)['status']!='waiting_quota':return error('not_resumable','Chỉ tiếp tục lượt đang chờ quota.',409)
        if not busy.acquire(blocking=False):return error('busy','Đã có lượt chạy.',429)
        threading.Thread(target=execute,args=(path,),daemon=True).start();return jsonify(id=job_id,status='queued'),202
    @app.get('/api/v2/development')
    def development():
        folder=root/'artifacts/llm_v2/phase2/development'
        return jsonify(mode='saved_development_not_new_live_call',rows=[read_json(p) for p in sorted(folder.glob('*.json')) if 'results' in read_json(p)])
    @app.route('/',defaults={'path':''})
    @app.route('/<path:path>')
    def frontend(path):
        if path.startswith('api/'):return error('not_found','API không tồn tại.',404)
        folder=root/'web/frontend/dist';candidate=(folder/path).resolve()
        if path and candidate.is_relative_to(folder.resolve()) and candidate.is_file():return send_from_directory(folder,path)
        if (folder/'index.html').exists():return send_from_directory(folder,'index.html')
        return jsonify(project='project01',frontend='Build React trước khi mở giao diện',health='/health')
    return app

