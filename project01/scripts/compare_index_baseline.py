"""New query parity against original frozen index code; not old QA TEST execution."""
from pathlib import Path
import json
import os
import sys
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'project01'
sys.path.insert(0,str(ROOT/'tieuluan3/provenance/runtime/assign'))
import joblib
original={role:joblib.load(PROJECT/'artifacts/package/v1'/name) for role,name in [('sparse','kg_medical_bm25.joblib'),('dense','kg_medical_dense_lsa.joblib')]}
queries=['physical activity diabetes','kidney disease diabetes','diabetes retinopathy']
expected={(query,role):index.search(query,10) for query in queries for role,index in original.items()}
sys.path.insert(0,str(PROJECT/'web/backend'))
from project01_core.foundation import Runtime
runtime=Runtime(PROJECT/'artifacts/package/v1')
rows=[]
for query in queries:
    for role,index in [('sparse',runtime.sparse),('dense',runtime.dense)]:
        actual=index.search(query,10);baseline=expected[(query,role)]
        assert [p[0] for p in actual]==[p[0] for p in baseline]
        difference=max(abs(a[1]-b[1]) for a,b in zip(actual,baseline))
        assert difference<=1e-6
        rows.append({'query':query,'index':role,'top10_ids_match':True,'max_score_difference':difference})
out=PROJECT/'artifacts/phase2/index_parity.json'
out.write_text(json.dumps({'status':'PASS','queries':rows,'index_refit':False,'historical_QA_TEST_forward':0},indent=2)+'\n')
print('Original index / notebook export parity PASS',len(rows))
