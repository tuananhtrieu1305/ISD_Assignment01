"""Exercise the public notebook runner in real fresh Jupyter kernels."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/notebook_revision/v1'

def main():
    rows=[]
    for project,notebook,framework in [('A06','02_Customer_Behavior.ipynb','keras'),('tieuluan3','02_RNN_LSTM.ipynb','torch'),('agent02','AG02_Code_and_Results.ipynb','torch')]:
        result=subprocess.run(['bash',str(ROOT/'scripts/run_assignment.sh'),framework,'--project',project,'--cpu','--notebook','notebooks/'+notebook],cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=600)
        assert result.returncode==0,(project,result.stdout[-1000:],result.stderr[-3000:])
        output=Path(result.stdout.strip().splitlines()[-1])
        assert output.is_relative_to(ROOT/project/'artifacts/notebook_runs') and output.is_file()
        document=json.loads(output.read_text())
        assert not any(o.get('output_type')=='error' for c in document['cells'] for o in c.get('outputs',[]))
        rows.append({'project':project,'framework':framework,'source':'notebooks/'+notebook,'sha256':hashlib.sha256((ROOT/project/'notebooks'/notebook).read_bytes()).hexdigest(),'output':output.relative_to(ROOT).as_posix(),'status':'PASS'})
        print('Jupyter kernel PASS',project,framework,flush=True)
    (OUT/'kernel_check.json').write_text(json.dumps({'status':'PASS','runs':rows,'training_steps':0,'scientific_TEST_forward':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
