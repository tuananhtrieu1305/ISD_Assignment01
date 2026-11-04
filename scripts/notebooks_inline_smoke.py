"""Execute inline definitions in fresh pinned IPython processes, no train/TEST."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/notebook_revision/v1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def worker(project,notebook):
    from IPython.core.interactiveshell import InteractiveShell
    shell=InteractiveShell.instance()
    document=load(ROOT/project/notebook)
    for i,cell in enumerate(document['cells']):
        if cell['cell_type']!='code':continue
        result=shell.run_cell(''.join(cell['source']),store_history=False)
        if result.error_before_exec or result.error_in_exec:raise RuntimeError(f'Cell{i}: '+str(result.error_before_exec or result.error_in_exec))
    assert shell.user_ns.get('RUN_TRAINING') is False
    assert shell.user_ns.get('RUN_TEST') is False
    assert not ('torch' in sys.modules and 'tensorflow' in sys.modules)
    print('INLINE_SMOKE_PASS')
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',action='store_true');parser.add_argument('--worker-project',dest='project');parser.add_argument('--worker-notebook',dest='notebook');args=parser.parse_args()
    if args.worker:return worker(args.project,args.notebook)
    previous=load(OUT/'execution.json')['runs'] if (OUT/'execution.json').exists() else []
    reused={(r['project'],r['path'],r['framework'],r['sha256']):r for r in previous if r['status']=='PASS'}
    runs=[]
    for project in load(OUT/'manifest.json')['projects']:
        name=project['project']
        if name in {'A01','A02','A03','agent01'}:continue # original training notebook; no authorized RunAll
        for entry in project['notebooks']:
            frameworks=entry.get('supported_frameworks',[entry['framework']])
            if name in {'tieuluan2','tieuluan3'} and not any(t in entry['path'] for t in ['ML','CNN','RNN']):frameworks=['torch']
            for framework in frameworks:
                key=(name,entry['path'],framework,sha(ROOT/name/entry['path']))
                if key in reused:runs.append(reused[key]);print('REUSE',*key[:3],flush=True);continue
                started=time.monotonic()
                command=['bash',str(ROOT/'scripts/run_assignment.sh'),framework,'--project',name,'--cpu','--script','scripts/notebooks_inline_smoke.py','--worker','--worker-project',name,'--worker-notebook',entry['path']]
                result=subprocess.run(command,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=300)
                row={'project':name,'path':entry['path'],'framework':framework,'sha256':key[-1],'status':'PASS' if result.returncode==0 and 'INLINE_SMOKE_PASS' in result.stdout else 'FAIL','elapsed_seconds':time.monotonic()-started,'stdout_tail':result.stdout[-7000:],'stderr_tail':result.stderr[-12000:],'training_steps':0,'scientific_TEST_forward':0}
                runs.append(row);(OUT/'execution.json').write_text(json.dumps({'status':'IN_PROGRESS','runs':runs},ensure_ascii=False,indent=2)+'\n')
                print(row['status'],name,entry['path'],framework,flush=True)
                if row['status']!='PASS':print(row['stdout_tail'],row['stderr_tail'],flush=True);raise SystemExit(1)
    (OUT/'execution.json').write_text(json.dumps({'status':'PASS','runs':runs,'training_steps':0,'scientific_TEST_forward':0},ensure_ascii=False,indent=2)+'\n')
    print('All fresh IPython executions PASS',len(runs),flush=True)
if __name__=='__main__':main()
