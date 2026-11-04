"""Execute the final notebook's code/analysis only, with external network denied."""
from pathlib import Path
import hashlib
import json
import os
import socket
import sys
import time
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT=Path(__file__).resolve().parents[1]
FINAL=ROOT/'tieuluanfinal'
path=FINAL/'notebooks/04_Multi_Agent.ipynb'
os.chdir(FINAL)
nb=json.loads(path.read_text(encoding='utf-8'))
before=hashlib.sha256(path.read_bytes()).hexdigest()
shell=InteractiveShell.instance()


def blocked(*args,**kwargs):
    raise RuntimeError('Network disabled: saved-output notebook execution only')


socket.create_connection=blocked
socket.socket.connect=blocked
socket.socket.connect_ex=blocked
errors=[];records=[];count=0
for index,cell in enumerate(nb['cells']):
    if cell['cell_type']!='code':continue
    started=time.monotonic()
    with capture_output() as captured:
        result=shell.run_cell(''.join(cell['source']),store_history=False,silent=False)
    count+=1;outputs=[]
    if captured.stdout:outputs.append({'output_type':'stream','name':'stdout','text':captured.stdout.splitlines(keepends=True)})
    if captured.stderr:outputs.append({'output_type':'stream','name':'stderr','text':captured.stderr.splitlines(keepends=True)})
    outputs += [{'output_type':'display_data','data':o.data,'metadata':o.metadata} for o in captured.outputs]
    cell['outputs']=outputs;cell['execution_count']=count
    error=result.error_before_exec or result.error_in_exec
    records.append({'cell_index':index,'execution_count':count,'seconds':round(time.monotonic()-started,3),'output_count':len(outputs),'error':str(error) if error else None})
    if error:
        errors.append({'cell':index,'error':str(error)})
        print(captured.stdout,captured.stderr,flush=True)
        break
for flag in ['RUN_API','RUN_EVALUATION','RUN_TRAINING','RUN_TEST','ALLOW_PAID_API']:
    assert shell.user_ns.get(flag) is False,flag
out=FINAL/'artifacts/notebook_runs/final_ch06_r1'
out.mkdir(parents=True,exist_ok=True)
receipt={'status':'FAIL' if errors else 'PASS','records':records,'errors':errors,'kernel':sys.executable,
         'network_blocked':True,'new_API_calls':0,'training_steps':0,'scientific_TEST_forward':0}
(out/'execution.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
if errors:raise RuntimeError(errors)
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
text=json.dumps(nb,ensure_ascii=False,indent=2)+'\n'
(out/path.name).write_text(text,encoding='utf-8')
path.write_text(text,encoding='utf-8')
print(json.dumps({'status':'PASS','code_cells':count,'new_API_calls':0,'network_blocked':True}),flush=True)
