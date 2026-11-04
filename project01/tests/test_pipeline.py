"""Development/synthetic integration tests; never read held-out evaluation cases."""
from pathlib import Path
import copy
import json
import math
import multiprocessing as mp
import shutil
import sys
import tempfile
import time
import unittest

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parent
sys.path.insert(0,str(PROJECT/'web/backend'))
from project01_core.foundation import Runtime, normalize_query, validate_profile
from project01_core.agents import assist, verify_outputs
from project01_core.transport import create_app

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime=Runtime(PROJECT/'artifacts/package/v1')
        cls.profile=json.loads((PROJECT/'datasets/demo_profiles.json').read_text())['profiles'][0]['profile']
    def request(self,mode='combined',question='Explain physical activity and diabetes.',profile=True):
        return {'mode':mode,'question':question,'language':'en','profile':copy.deepcopy(self.profile) if profile else None}
    def test_combined_five_roles_and_real_tools(self):
        out=assist(self.runtime,self.request())
        self.assertEqual(out['status'],'answered')
        self.assertTrue(out['knowledge']['answer']);self.assertIsNotNone(out['risk'])
        self.assertEqual({r['agent'] for r in out['trace']},{'Coordinator','Risk Agent','Knowledge Agent','Verifier','Reporter'})
        self.assertLessEqual(out['tool_calls'],8);self.assertTrue(out['worker_terminated'])
    def test_numeric_only(self):
        out=assist(self.runtime,self.request('numeric'))
        self.assertEqual(out['status'],'answered');self.assertIsNone(out['knowledge'])
    def test_source_query_changes_evidence(self):
        one=self.runtime.retrieve('physical activity diabetes');two=self.runtime.retrieve('kidney disease diabetes')
        self.assertNotEqual(one['ranked_chunk_ids'],two['ranked_chunk_ids'])
        self.assertTrue(one['graph_paths'])
        self.assertTrue(all(path[-1] in self.runtime.chunks for path in one['graph_paths'].values()))
    def test_missing_does_not_impute(self):
        req=self.request('numeric');req['profile'].pop('bmi')
        out=assist(self.runtime,req)
        self.assertEqual(out['status'],'clarification');self.assertIsNone(out['risk']);self.assertIn('bmi',out['profile_validation']['missing'])
    def test_invalid_values(self):
        for value in [True,float('nan'),float('inf'),-1,200,{},'25']:
            profile=copy.deepcopy(self.profile);profile['bmi']=value
            self.assertFalse(validate_profile(profile,self.runtime.schema)['valid'])
    def test_age_is_encoded_category(self):
        profile=copy.deepcopy(self.profile);profile['age']=60
        self.assertFalse(validate_profile(profile,self.runtime.schema)['valid'])
    def test_rejects_personal_dose_before_glossary(self):
        req=self.request('knowledge','Hãy kê đơn insulin cho tôi');req['language']='vi'
        self.assertEqual(assist(self.runtime,req)['status'],'refused')
    def test_bounded_vietnamese(self):
        query,mapping=normalize_query('Bệnh thận tiểu đường','vi',self.runtime.glossary)
        self.assertIn('kidney',query);self.assertTrue(mapping)
    def test_evidence_support_beyond_integrity(self):
        knowledge=self.runtime.retrieve('physical activity diabetes')
        knowledge['answer']='A fabricated cure for every disease.'
        check=verify_outputs(self.runtime,self.request('knowledge'),None,knowledge)
        self.assertTrue(check['checks']['citation_integrity'])
        self.assertFalse(check['checks']['verbatim_focused_claim_support'])
    def test_numeric_consistency(self):
        risk=self.runtime.predict(self.profile);risk['score']=.999
        self.assertFalse(verify_outputs(self.runtime,self.request('numeric'),risk,None)['checks']['numeric_consistency'])
    def test_transient_retry_is_bounded(self):
        out=assist(self.runtime,self.request(),fault='transient')
        self.assertEqual(out['status'],'answered');self.assertLessEqual(out['tool_calls'],8)
        self.assertTrue(any(r['outcome']=='error' for r in out['trace']))
    def test_timeout_really_reaps_worker(self):
        before={p.pid for p in mp.active_children()};started=time.perf_counter()
        out=assist(self.runtime,self.request(),fault='deadline',deadline_seconds=.05)
        self.assertEqual(out['status'],'timeout');self.assertTrue(out['worker_terminated']);self.assertLess(time.perf_counter()-started,1)
        self.assertEqual(before,{p.pid for p in mp.active_children()})
        self.assertIsNone(out['tool_calls'])
    def test_tampered_package_fails_before_unpickling(self):
        with tempfile.TemporaryDirectory() as directory:
            package=Path(directory)/'package';shutil.copytree(PROJECT/'artifacts/package/v1',package)
            (package/'kg_medical_bm25.joblib').write_bytes(b'not a trusted pickle')
            with self.assertRaises(ValueError):Runtime(package)
    def test_frozen_original_forward_parity(self):
        sys.path.insert(0,str(ROOT/'tieuluan3/provenance/runtime/assign'))
        from src.common.numpy_engine import NumpyNetwork
        from src.common.tensor_adapters import TensorAdapter
        import pandas as pd
        import numpy as np
        model=NumpyNetwork(self.runtime.config['plan'],self.runtime.weights)
        adapter=TensorAdapter(self.runtime.preprocessing)
        profiles=json.loads((PROJECT/'datasets/demo_profiles.json').read_text())['profiles']
        for sample in profiles:
            tensor=adapter.transform(pd.DataFrame([sample['profile']],columns=self.runtime.schema['feature_order']))
            logit=float(model.forward(tensor)[0,0]);expected=float(1/(1+np.exp(-np.clip(logit,-60,60))))
            self.assertTrue(math.isclose(self.runtime.predict(sample['profile'])['score'],expected,rel_tol=1e-6,abs_tol=1e-6))
    def test_api_ready_schema_and_validation(self):
        app=create_app(PROJECT);client=app.test_client()
        self.assertEqual(client.get('/health').status_code,200);self.assertEqual(client.get('/ready').status_code,200)
        self.assertEqual(client.post('/api/v1/assist',json={**self.request(),'fault':'deadline'}).status_code,422)
        self.assertEqual(client.post('/api/v1/assist',json=[]).status_code,422)
        self.assertEqual(client.post('/api/v1/assist',data='x',content_type='text/plain').status_code,415)
        self.assertEqual(client.post('/api/v1/assist',data='x'*18000,content_type='application/json').status_code,413)
        self.assertEqual(client.post('/api/v1/assist',json=self.request(),headers={'Origin':'https://bad.invalid'}).status_code,403)
        response=client.post('/api/v1/assist',json={**self.request(),'variant':'P2'})
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['status'],'answered')
    def test_missing_assets_ready_503(self):
        with tempfile.TemporaryDirectory() as directory:
            client=create_app(Path(directory)).test_client()
            self.assertEqual(client.get('/health').status_code,200);self.assertEqual(client.get('/ready').status_code,503)
    def test_notebook_drift_makes_api_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            clone=Path(directory)
            for folder in ['web/backend/project01_core','notebooks','artifacts/package/v1']:
                shutil.copytree(PROJECT/folder,clone/folder)
            (clone/'artifacts/phase2').mkdir(parents=True)
            shutil.copyfile(PROJECT/'artifacts/phase2/source_exports.json',clone/'artifacts/phase2/source_exports.json')
            notebook=clone/'notebooks/01_Data_KB_RAG.ipynb'
            document=json.loads(notebook.read_text());document['cells'][0]['source']=['Changed source'];notebook.write_text(json.dumps(document))
            self.assertEqual(create_app(clone).test_client().get('/ready').status_code,503)
    def test_evaluator_does_not_require_a_verifier_in_baseline(self):
        from project01_core.evaluation import judge_automatic
        case={'category':'fault','gold_evidence':[]}
        req=self.request();reference=self.runtime.predict(req['profile'])['score']
        for variant in ['P0','P1','P2']:
            result=assist(self.runtime,req,variant,fault='model_unavailable')
            self.assertTrue(judge_automatic(case,result,reference)['automatic_success'])

if __name__=='__main__':unittest.main()
