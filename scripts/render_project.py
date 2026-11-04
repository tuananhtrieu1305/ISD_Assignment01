"""Render monorepo entry point; stage pinned CPU-only payload, verify source parity."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def helper():
    spec=importlib.util.spec_from_file_location('frozen_render_validator',ROOT/'tieuluan3/scripts/render_v3.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def stage(project,output=None):
    if project not in {'tieuluan1','tieuluan2','tieuluan3'}:raise ValueError('Unknown paper')
    release=json.loads((ROOT/project/'web/deploy/release.json').read_text())
    for row in release['source_python']:
        path=(ROOT/row['path']).resolve()
        if not path.is_relative_to(ROOT) or sha(path)!=row['sha256']:raise ValueError('Source changed; build a new versioned serving bundle: '+row['path'])
    output=output or ROOT/'.render-reorg'/project/release['archive']['sha256'][:16]
    return helper().stage_bundle(ROOT/release['archive']['path'],release,output),release
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['stage','check','build','start'])
    parser.add_argument('--project',choices=['tieuluan1','tieuluan2','tieuluan3'],default='tieuluan3')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if sys.version_info[:3]!=(3,11,17):parser.error('Use pinned Python3.11.17')
    runtime,release=stage(args.project,args.output)
    env=helper().runtime_environment(runtime)
    if args.action=='build':
        subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir','--require-hashes','-r',str(runtime/'deploy/v3/requirements-cpu.lock')],cwd=runtime,env=env,check=True)
    if args.action in {'check','build'}:
        code="import web_entry; c=web_entry.app.test_client(); r=c.get('/health'); assert r.status_code==200,r.json; print(r.status_code)"
        if args.project!='tieuluan1':code+="; r=c.get('/ready'); assert r.status_code==200,r.json; print(r.json['status'])"
        subprocess.run([sys.executable,'-B','-c',code],cwd=runtime,env=env,check=True,timeout=180)
    if args.action=='start':
        port=env.get('PORT','10000')
        if not re.fullmatch(r'[0-9]{1,5}',port) or not 1<=int(port)<=65535:raise ValueError('Invalid PORT')
        os.chdir(runtime)
        os.execvpe(sys.executable,[sys.executable,'-B','-m','gunicorn','--bind','0.0.0.0:'+port,'--workers','1','--threads','2','--timeout','120',release['entrypoint']],env)
    print(json.dumps({'status':'PASS','action':args.action,'project':args.project,'runtime':str(runtime),'training_steps':0,'scientific_TEST_forward':0}))
if __name__=='__main__':main()
