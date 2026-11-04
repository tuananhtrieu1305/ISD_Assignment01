"""Serve from only published project files in a temporary clone; no old runtime/data."""
from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'web/backend'))
from project01_core.transport import create_app

def main():
    with tempfile.TemporaryDirectory() as folder:
        clone=Path(folder)/'project01'
        for name in ['web/backend/project01_core','web/frontend/dist','notebooks','artifacts/package/v1']:
            shutil.copytree(PROJECT/name,clone/name)
        for name in ['artifacts/phase2/source_exports.json','artifacts/phase2/summary.json','datasets/demo_profiles.json','datasets/profile_schema.json']:
            target=clone/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PROJECT/name,target)
        client=create_app(clone).test_client()
        assert client.get('/ready').status_code==200
        assert b'<html' in client.get('/').data
        examples=client.get('/api/v1/examples').json
        result=client.post('/api/v1/assist',json={'mode':'combined','question':'Explain physical activity and diabetes.','language':'en','profile':examples['profiles'][0]['profile'],'variant':'P2'})
        assert result.status_code==200 and result.json['status']=='answered'
        assert result.json['risk'] and result.json['knowledge']['answer']
        report={'status':'PASS','old_tieuluan3_files_present':False,'old_runtime_view_required':False,'ready':200,'frontend':200,'combined_response':200,'model_and_RAG_executed':True,'input_scope':'TRAIN demo + development topic, not evaluation','cloud_deployed':False}
        (PROJECT/'artifacts/phase2/clean_serving_check.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))

if __name__=='__main__':main()
