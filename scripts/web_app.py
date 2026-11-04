"""Per-project local web entry point: static demos or original Python APIs, no training."""
from pathlib import Path
import argparse
import importlib
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_shared'))
from assignment_runtime import PROJECTS,activate

PORTS={p:8011+i for i,p in enumerate(PROJECTS)}

def create_app(project):
    if project not in PROJECTS:raise ValueError('Unknown project')
    from flask import Flask,request,send_file,abort,jsonify,Response
    app=Flask('assignment_web_'+project)
    app.config.update(MAX_CONTENT_LENGTH=6_400_000)
    web=ROOT/project/'web'
    frontend=web/'frontend/dist' if project.startswith('tieuluan') else web
    api=None
    if project in {'A01','A02','A03','tieuluan1','tieuluan2','tieuluan3'}:
        activate(project,'torch')
        if project in {'tieuluan2','tieuluan3'}:
            os.environ.setdefault('AI_JOB_DB',str(web/'.runtime/jobs.db'))
            module=importlib.import_module('apps.api.v3.server')
            api=module.create_app()
        else:
            api=importlib.import_module('backend.app').app

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['X-Frame-Options']='DENY'
        return response

    @app.route('/health',methods=['GET','HEAD'])
    @app.route('/ready',methods=['GET','HEAD'])
    @app.route('/api/<path:route>',methods=['GET','POST','OPTIONS','HEAD'])
    def api_route(route=None):
        if request.content_length and request.content_length>6_400_000:abort(413)
        if api:return Response.from_app(api.wsgi_app,request.environ)
        if request.path=='/health':return jsonify(status='ok',project=project,mode='saved_results',training=False)
        abort(404)

    if project=='tieuluan1':
        @app.get('/api/demo/<use_case>')
        def train_demo(use_case):
            import json
            samples=json.loads((web/'deploy/train_samples.json').read_text(encoding='utf-8'))
            if use_case not in samples:abort(404)
            return jsonify(samples[use_case])

    @app.get('/')
    @app.get('/<path:route>')
    def files(route='index.html'):
        if route.startswith('_demo-ui/'):
            asset=route.removeprefix('_demo-ui/')
            if asset not in {'simple-demo.js','simple-demo.css'}:abort(404)
            return send_file(ROOT/'_shared'/'simple_demo'/asset)
        parts=Path(route).parts
        if any(p.startswith('.') or p in {'reference_backend','reference_ui','legacy_runtime','backend','node_modules'} for p in parts):abort(404)
        path=(frontend/route).resolve()
        if not path.is_relative_to(frontend.resolve()) or path.is_symlink():abort(404)
        allowed={'.html','.js','.css','.json','.png','.jpg','.jpeg','.svg','.ico','.ipynb','.woff','.woff2'}
        if path.is_file() and path.suffix.lower() in allowed:return send_file(path)
        if project.startswith('tieuluan') and not Path(route).suffix:
            return send_file(frontend/'index.html')
        abort(404)

    return app

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,choices=PROJECTS)
    parser.add_argument('--port',type=int)
    args=parser.parse_args()
    port=args.port or PORTS[args.project]
    if not 1024<=port<=65535:parser.error('Port must be1024–65535')
    os.environ['CUDA_VISIBLE_DEVICES']='-1'
    os.environ.setdefault('AI_CORS_ORIGINS',f'http://localhost:{port},http://127.0.0.1:{port}')
    os.environ.setdefault('WEB_ORIGIN',f'http://localhost:{port},http://127.0.0.1:{port}')
    create_app(args.project).run(host='127.0.0.1',port=port,debug=False,use_reloader=False)

if __name__=='__main__':main()
