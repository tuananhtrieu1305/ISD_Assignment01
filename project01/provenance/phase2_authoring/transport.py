"""Local/Render Flask transport; only allowlisted JSON, no uploads or arbitrary tools."""
from collections import defaultdict, deque
from pathlib import Path
import os
import threading
import time

from flask import Flask, jsonify, request, send_from_directory

from project01_core.agents import VARIANTS, assist, validate_request
from project01_core.foundation import Runtime, file_sha, read_json

def create_app(project_root=None):
    root=Path(project_root or Path(__file__).resolve().parents[3])
    app=Flask(__name__,static_folder=None);app.config['MAX_CONTENT_LENGTH']=16*1024
    runtime=None;lock=threading.Lock();busy=threading.BoundedSemaphore(1);rates=defaultdict(deque)
    allowed={value.strip().rstrip('/') for value in os.environ.get('WEB_ORIGIN','http://127.0.0.1:5179,http://localhost:5179,http://127.0.0.1:8031,http://localhost:8031').split(',') if value.strip()}
    def get_runtime():
        nonlocal runtime
        with lock:
            if runtime is None:
                exports=read_json(root/'artifacts/phase2/source_exports.json')
                for row in exports['files']:
                    if file_sha(root/row['export'])!=row['sha256']:raise ValueError('Source export mismatch')
                runtime=Runtime(root/'artifacts/package/v1')
        return runtime
    @app.before_request
    def guard():
        origin=request.headers.get('Origin','').rstrip('/')
        if origin and origin not in allowed and origin!=request.host_url.rstrip('/'):
            return jsonify(error={'code':'origin_not_allowed','message':'Origin is not configured'}),403
        if request.method=='OPTIONS':return '',204
        if request.path=='/api/v1/assist':
            now=time.monotonic();address=request.remote_addr or 'local'
            if address not in rates and len(rates)>=1024:rates.clear()
            bucket=rates[address]
            while bucket and bucket[0]<now-60:bucket.popleft()
            if len(bucket)>=60:return jsonify(error={'code':'rate_limit','message':'Please retry shortly'}),429
            bucket.append(now)
    @app.after_request
    def headers(response):
        origin=request.headers.get('Origin','').rstrip('/')
        if origin in allowed:
            response.headers['Access-Control-Allow-Origin']=origin;response.headers['Vary']='Origin'
        response.headers['Access-Control-Allow-Methods']='GET,POST,OPTIONS'
        response.headers['Access-Control-Allow-Headers']='Content-Type'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Cache-Control']='no-store' if request.path.startswith('/api/') else 'no-cache'
        return response
    @app.errorhandler(413)
    def too_large(_):return jsonify(error={'code':'request_too_large','message':'JSON limit is 16 KiB'}),413
    @app.errorhandler(400)
    def malformed(_):return jsonify(error={'code':'invalid_json','message':'Expected a valid JSON object'}),400
    @app.get('/health')
    def health():return jsonify(status='ok',project='project01')
    @app.get('/ready')
    def ready():
        try:
            value=get_runtime();return jsonify(status='ready',chunks=len(value.chunks),graph_anchors=len(value.graph),backend='numpy_cpu')
        except (OSError,ValueError,ImportError,KeyError):return jsonify(status='unavailable',code='artifact_or_source_unavailable'),503
    @app.get('/api/v1/examples')
    def examples():
        return jsonify(profiles=read_json(root/'datasets/demo_profiles.json')['profiles'],schema=read_json(root/'datasets/profile_schema.json'),questions=[{'title':'Kiến thức · vận động','question':'Explain physical activity and diabetes.','language':'en','mode':'knowledge'},{'title':'Kết hợp model + kiến thức','question':'Explain physical activity and diabetes.','language':'en','mode':'combined'},{'title':'Tiếng Việt · phạm vi glossary','question':'Bệnh thận tiểu đường','language':'vi','mode':'knowledge'}])
    @app.get('/api/v1/results')
    def historical_results():
        path=root/'artifacts/phase2/summary.json'
        return jsonify(read_json(path) if path.exists() else {'status':'not_evaluated','rows':[]})
    @app.post('/api/v1/assist')
    def run_assist():
        if not request.is_json:return jsonify(error={'code':'content_type','message':'Use application/json'}),415
        document=request.get_json()
        if not isinstance(document,dict):return jsonify(error={'code':'invalid_request','message':'JSON object required'}),422
        document=dict(document);variant=document.pop('variant','P2')
        try:
            validate_request(document)
            if variant not in VARIANTS:raise ValueError('Unknown variant')
        except (ValueError,TypeError):return jsonify(error={'code':'invalid_request','message':'Check mode, question, language and profile fields'}),422
        if not busy.acquire(blocking=False):return jsonify(error={'code':'busy','message':'One CPU request at a time; retry shortly'}),429
        try:
            try:result=assist(get_runtime(),document,variant)
            except (OSError,ValueError,ImportError,KeyError):return jsonify(error={'code':'artifact_unavailable','message':'Verified local assets/source are unavailable'}),503
            return jsonify(result)
        finally:busy.release()
    @app.route('/',defaults={'path':''})
    @app.route('/<path:path>')
    def frontend(path):
        if path.startswith('api/'):
            return jsonify(error={'code':'not_found','message':'Unknown API route'}),404
        folder=root/'web/frontend/dist'
        candidate=(folder/path).resolve()
        if path and candidate.is_relative_to(folder.resolve()) and candidate.is_file():return send_from_directory(folder,path)
        if (folder/'index.html').exists():return send_from_directory(folder,'index.html')
        return jsonify(project='project01',frontend='Build frontend first; see README',health='/health',ready='/ready')
    return app
