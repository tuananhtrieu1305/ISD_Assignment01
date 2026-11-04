"""Bounded web routing and deployment-source integrity tests on synthetic files."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[2]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
web=module('reorg_web','scripts/web_app.py')
render=module('reorg_render','scripts/render_project.py')

@pytest.fixture
def client(tmp_path,monkeypatch):
    root=tmp_path/'agent01/web';root.mkdir(parents=True)
    (root/'index.html').write_text('<h1>Demo</h1>')
    (root/'notebook.ipynb').write_text('{"cells":[]}')
    (tmp_path/'private.json').write_text('{"private":true}')
    monkeypatch.setattr(web,'ROOT',tmp_path)
    return web.create_app('agent01').test_client()

@pytest.mark.parametrize('route',['/.env','/backend/app.py','/reference_ui/package.json','/%2e%2e/%2e%2e/private.json','/private.json','/missing.js'])
def test_static_files_do_not_expose_private_or_missing_files(client,route):
    assert client.get(route).status_code==404

def test_static_replay_and_notebook_download(client):
    assert client.get('/').status_code==200
    assert json.loads(client.get('/notebook.ipynb').data)=={'cells':[]}
    assert client.get('/health').json['mode']=='saved_results'
    assert client.get('/ready').status_code==404
    assert client.get('/').headers['X-Content-Type-Options']=='nosniff'

def test_api_body_budget_before_proxy(client):
    assert client.post('/api/example',data=b'x'*6_400_001).status_code==413

def test_unknown_project_rejected_before_sources():
    with pytest.raises(ValueError):web.create_app('../outside')
    with pytest.raises(ValueError):render.stage('../outside')

def test_source_integrity_rejects_corrupt_copy_before_staging(tmp_path,monkeypatch):
    folder=tmp_path/'tieuluan2/web/deploy';folder.mkdir(parents=True)
    source=tmp_path/'model.py';source.write_text('original')
    (folder/'release.json').write_text(json.dumps({'source_python':[{'path':'model.py','sha256':'0'*64}]}))
    monkeypatch.setattr(render,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='Source changed'):render.stage('tieuluan2')


def test_api_proxy_preserves_json_and_spa_blocks_file_paths(tmp_path,monkeypatch):
    from flask import Flask,request,jsonify
    api=Flask('fake_pinned_api')
    @api.post('/api/input')
    def input_json():return jsonify(request.get_json())
    @api.get('/health')
    def health():return jsonify(status='ok')
    frontend=tmp_path/'tieuluan2/web/frontend/dist'
    frontend.mkdir(parents=True);(frontend/'index.html').write_text('<h1>Five chapters</h1>')
    monkeypatch.setattr(web,'ROOT',tmp_path)
    monkeypatch.setattr(web,'activate',lambda *args:None)
    monkeypatch.setattr(web.importlib,'import_module',lambda name:SimpleNamespace(create_app=lambda:api))
    app=web.create_app('tieuluan2');client=app.test_client()
    assert client.post('/api/input',json={'input':[1,2,3]}).json=={'input':[1,2,3]}
    assert client.get('/health').json['status']=='ok'
    assert client.get('/cnn').status_code==200
    assert client.get('/unknown.py').status_code==404
