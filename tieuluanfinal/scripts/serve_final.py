"""One local integrated site; two existing isolated Python environments, no installs."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
FINAL=ROOT/'tieuluanfinal'
AGENT=FINAL/'web/agent'
TORCH=Path('/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python')


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def scientific_worker(port):
    print('Final: verifying and staging the pinned Ch1–5 serving bundle...',flush=True)
    helper=load_module(FINAL/'scripts/render_v3.py','final_scientific_stage')
    spec=json.loads((FINAL/'web/deploy/release.json').read_text())
    runtime=helper.stage_bundle(FINAL/'web/deploy/api-bundle-r1.zip',spec,
                               FINAL/'web/.runtime/scientific-baseline-r1')
    os.environ.update(helper.runtime_environment(runtime))
    os.environ['AI_JOB_DB']=str(FINAL/'web/.runtime/scientific-jobs.db')
    sys.path.insert(0,str(runtime));os.chdir(runtime)
    print('Final: importing Ch1–5 API from verified local bundle...',flush=True)
    from web_entry import app
    app.run(host='127.0.0.1',port=port,threaded=True,debug=False,use_reloader=False)


def agent_worker(port,live):
    sys.path.insert(0,str(AGENT/'web/backend'))
    from project01_llm_v2.transport import create_app
    create_app(AGENT,allow_api=live).run(host='127.0.0.1',port=port,threaded=True,debug=False,use_reloader=False)


def integrated_app(science_port,agent_port):
    from flask import Flask,request,Response,send_from_directory,abort
    from http.client import HTTPConnection
    app=Flask('tieuluanfinal',static_folder=None)
    app.config['MAX_CONTENT_LENGTH']=6_400_000

    def proxy(port,path=None):
        connection=HTTPConnection('127.0.0.1',port,timeout=20)
        try:
            headers={k:v for k,v in request.headers if k.lower() not in {'host','connection','content-length','accept-encoding'}}
            headers['Host']=request.host
            connection.request(request.method,path or request.full_path.rstrip('?'),body=request.get_data(),headers=headers)
            upstream=connection.getresponse();payload=upstream.read()
            response=Response(payload,status=upstream.status)
            for key,value in upstream.getheaders():
                if key.lower() not in {'connection','transfer-encoding','content-length','server','date','content-type'}:response.headers[key]=value
            response.headers['Content-Type']=upstream.getheader('Content-Type','application/json')
            return response
        except OSError:
            return {'error':{'message':'Backend chưa sẵn sàng. Thử tải lại sau ít giây.'}},503
        finally:connection.close()

    @app.route('/api/v2/<path:route>',methods=['GET','POST','OPTIONS'])
    def agent_api(route):return proxy(agent_port)

    @app.route('/api/<path:route>',methods=['GET','POST','OPTIONS','HEAD'])
    def scientific_api(route):
        # The old Chapter6 endpoint remains in its immutable archive, never exposed
        # as the final paper's active pipeline.
        if 'agent' in route.lower():abort(410)
        if request.method=='POST' and route=='v3/comparisons':
            payload=request.get_json(silent=True)
            if isinstance(payload,dict) and payload.get('chapter')==6:abort(410)
        return proxy(science_port)

    @app.get('/health')
    @app.get('/ready')
    def science_status():return proxy(science_port)

    @app.get('/multi-agent/ready')
    @app.get('/multi-agent/health')
    def agent_status():return proxy(agent_port,'/'+request.path.rsplit('/',1)[-1])

    @app.get('/multi-agent/')
    @app.get('/multi-agent/<path:path>')
    def agent_files(path='index.html'):
        if path.startswith('.') or '..' in Path(path).parts:abort(404)
        return send_from_directory(AGENT/'web/frontend/dist',path)

    @app.get('/')
    @app.get('/<path:path>')
    def site(path='index.html'):
        if path.startswith('.') or '..' in Path(path).parts:abort(404)
        folder=FINAL/'web/frontend/dist'
        if (folder/path).is_file():return send_from_directory(folder,path)
        if Path(path).suffix:abort(404)
        return send_from_directory(folder,'index.html')
    return app


def launch(port,live):
    ports=[port,port+1,port+2]
    for value in ports:
        with socket.socket() as sock:sock.bind(('127.0.0.1',value))
    # Shared accounting prevents two local frontends resetting the API budget.
    os.environ.setdefault('GEMINI_STATE_ROOT',str(ROOT/'project01/artifacts/llm_v2/runtime'))
    os.environ['WEB_ORIGIN']=f'http://127.0.0.1:{port},http://localhost:{port}'
    os.environ['AI_CORS_ORIGINS']=os.environ['WEB_ORIGIN']
    if live and not os.environ.get('GEMINI_API_KEY'):
        for path in [FINAL/'.env',ROOT/'project01/.env']:
            if path.is_file():
                for line in path.read_text().splitlines():
                    key,_,value=line.partition('=')
                    if key.strip()=='GEMINI_API_KEY':os.environ['GEMINI_API_KEY']=value.strip().strip('"\'')
                if os.environ.get('GEMINI_API_KEY'):break
    children=[]
    try:
        children.append(subprocess.Popen([str(TORCH),'-B',__file__,'--worker','science','--port',str(port+1)],env=os.environ.copy()))
        children.append(subprocess.Popen([sys.executable,'-B',__file__,'--worker','agent','--port',str(port+2)]+(['--live'] if live else []),env=os.environ.copy()))
        for _ in range(240):
            if any(p.poll() is not None for p in children):raise RuntimeError('A backend exited during startup')
            ready=True
            for value in ports[1:]:
                with socket.socket() as sock:
                    sock.settimeout(.2)
                    if sock.connect_ex(('127.0.0.1',value))!=0:ready=False
            if ready:break
            time.sleep(.5)
        else:raise TimeoutError('Backend startup timeout')
        print(f'Open http://127.0.0.1:{port} ; Ch6 /agents ; Ctrl+C stops these workers only.',flush=True)
        integrated_app(port+1,port+2).run(host='127.0.0.1',port=port,threaded=True,debug=False,use_reloader=False)
    finally:
        for process in children:
            if process.poll() is None:process.terminate()
        for process in children:
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.kill();process.wait()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8040)
    parser.add_argument('--worker',choices=['science','agent'])
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if not 1024<=args.port<=65533:parser.error('Port outside allowed range')
    if args.worker=='science':scientific_worker(args.port)
    elif args.worker=='agent':agent_worker(args.port,args.live)
    else:launch(args.port,args.live)
