"""Export bounded TRAIN inputs for paper1 UI; no model forward or TEST extraction."""
from pathlib import Path
import base64
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_shared'))
from assignment_runtime import activate
activate('tieuluan1','torch')
import numpy as np
import pandas as pd
from term_paper.deployment.app.model_service import ModelService

logical=Path.cwd()
service=ModelService(logical)
samples={'diabetes':dict(service.demo('diabetes'),input_split='synthetic_fixture',sample_key='synthetic CDC21 fixture')}
keys=pd.read_csv(logical/'term_paper/artifacts/manifests/ch3/ch3_eurosat_subset_keys.csv')
relative=keys[keys['split']=='train'].iloc[0]['sample_key']
samples['eurosat']={'use_case':'eurosat','input':{'image_base64':base64.b64encode((logical/'A05'/relative).read_bytes()).decode()},'sample_key':relative,'input_split':'TRAIN'}
for case,dataset,scaler in [('customer','ch4_online_retail_customer_week',service.customer_scaler),('aapl','ch4_aapl_next_close',service.stock_feature_scaler)]:
    with np.load(logical/f'term_paper/artifacts/manifests/ch4/{dataset}_processed.npz',allow_pickle=False) as data:
        raw=scaler.inverse_transform(data['x_train'][0]).tolist()
        key=str(data['keys_train'][0])
    samples[case]={'use_case':case,'input':{'sequence':raw},'sample_key':key,'input_split':'TRAIN'}
out=ROOT/'tieuluan1/web/deploy/train_samples.json';out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(samples,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'docs/reorganization/phase3/paper1_train_samples.json').write_text(json.dumps({'status':'PASS','path':out.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'input_scopes':{k:v['input_split'] for k,v in samples.items()},'TEST_arrays_extracted':False,'model_forward':False},indent=2)+'\n')
print('Paper1 TRAIN samples exported, no forward')
