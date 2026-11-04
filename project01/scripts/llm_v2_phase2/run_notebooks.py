"""Execute canonical cells with API/training/evaluation flags off; save outside notebooks."""
from pathlib import Path
import json,os,time,hashlib
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
P=Path(__file__).resolve().parents[2];os.chdir(P)
out=P/'artifacts/notebook_runs/llm_v2'/str(time.time_ns());out.mkdir(parents=True,exist_ok=True)
records=[]
for filename in ['01_Data_KB_RAG.ipynb','02_Diabetes_Multi_Agent.ipynb','03_Evaluation.ipynb']:
    canonical=P/'notebooks'/filename;before=hashlib.sha256(canonical.read_bytes()).hexdigest()
    notebook=json.loads(canonical.read_text())
    shell=InteractiveShell.instance();errors=[];count=0
    for cell in notebook['cells']:
        if cell['cell_type']!='code':continue
        with capture_output() as captured:result=shell.run_cell(''.join(cell['source']),store_history=False,silent=False)
        outputs=[]
        if captured.stdout:outputs.append({'output_type':'stream','name':'stdout','text':captured.stdout.splitlines(keepends=True)})
        if captured.stderr:outputs.append({'output_type':'stream','name':'stderr','text':captured.stderr.splitlines(keepends=True)})
        outputs += [{'output_type':'display_data','data':r.data,'metadata':r.metadata} for r in captured.outputs]
        cell['outputs']=outputs;cell['execution_count']=count+1
        if result.error_before_exec or result.error_in_exec:errors.append(type(result.error_before_exec or result.error_in_exec).__name__)
        count+=1
    assert not errors,(filename,errors)
    for flag in ['RUN_API','RUN_TRAINING','RUN_TEST','RUN_EVALUATION','ALLOW_PAID_API']:assert shell.user_ns[flag] is False
    records.append({'notebook':filename,'code_cells':count,'errors':errors,'api_calls':0,'mode':'source cells, offline defaults'})
    text=json.dumps(notebook,ensure_ascii=False,indent=2)+'\n';(out/filename).write_text(text)
    assert hashlib.sha256(canonical.read_bytes()).hexdigest()==before,'User notebook changed during execution; refuse to overwrite'
    canonical.write_text(text)
receipt={'status':'PASS','records':records,'kernel_python':__import__('sys').executable,'training_steps':0,'scientific_TEST_forward':0}
(out/'execution.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt))
