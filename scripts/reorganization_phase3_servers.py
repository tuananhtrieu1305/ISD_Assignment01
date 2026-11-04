"""Own a temporary11-server fleet for migration QA; stop all children on exit."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_shared'))
from assignment_runtime import PROJECTS
P3=ROOT/'docs/reorganization/phase3'
OUT=P3/'servers';OUT.mkdir(exist_ok=True)
children=[]
def stop(*args):raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop)
signal.signal(signal.SIGINT,stop)
try:
    for i,project in enumerate(PROJECTS):
        port=8011+i
        log=(OUT/(project+'.log')).open('w')
        child=subprocess.Popen([sys.executable,'-B',str(ROOT/'scripts/web_app.py'),'--project',project,'--port',str(port)],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','CUDA_VISIBLE_DEVICES':'-1'},stdout=log,stderr=subprocess.STDOUT)
        children.append((project,port,child,log))
    (P3/'active_servers.json').write_text(json.dumps({'owner_pid':os.getpid(),'servers':[{'project':p,'port':port,'pid':c.pid} for p,port,c,_ in children]},indent=2))
    for project,port,child,_ in children:
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            if child.poll() is not None:raise RuntimeError(project+' server exited; see log')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=2) as response:
                    assert response.status==200
                print('READY',project,port,flush=True);break
            except (OSError,AssertionError):time.sleep(.5)
        else:raise TimeoutError(project)
    print('ALL11 READY',flush=True)
    while True:
        if any(child.poll() is not None for _,_,child,_ in children):raise RuntimeError('QA child exited unexpectedly')
        time.sleep(1)
except KeyboardInterrupt:
    print('QA fleet stopping',flush=True)
finally:
    for _,_,child,_ in children:
        if child.poll() is None:child.terminate()
    for _,_,child,log in children:
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:child.kill();child.wait()
        log.close()
    (P3/'active_servers.json').write_text(json.dumps({'owner_pid':None,'servers':[],'status':'STOPPED'},indent=2))
