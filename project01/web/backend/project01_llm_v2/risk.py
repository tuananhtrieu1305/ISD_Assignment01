# GENERATED from notebooks/01_Data_KB_RAG.ipynb; source SHA256 515f97894ec39979a2ea46ea52794396e2226cc5a35f83d0ab9b45eda5090b51
# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.
from pathlib import Path

import hashlib,json,math

import numpy as np

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def file_sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def validate_profile(profile,schema):
    if not isinstance(profile,dict):return {'valid':False,'missing':schema['required'],'invalid':[],'extra':[]}
    missing=[k for k in schema['required'] if k not in profile or profile[k] is None]
    invalid=[]
    for name,value in profile.items():
        if name not in schema['limits']:continue
        bounds=schema['limits'][name]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not bounds[0]<=value<=bounds[1] or (name!='bmi' and value!=int(value)):
            invalid.append(name)
    extra=sorted(set(profile)-set(schema['required']))
    return {'valid':not(missing or invalid or extra),'missing':missing,'invalid':invalid,'extra':extra}

def transform_profile(profile,preprocessing):
    """Apply frozen train-only numeric statistics in canonical input order."""
    values=[]
    for name in preprocessing['input_columns']:
        rule=preprocessing['numeric'][name]
        values.append((float(profile[name])-rule['mean'])/rule['std'])
    return np.asarray([values],dtype=np.float32)

def mlp_forward(tensor,plan,weights):
    tensor=np.asarray(tensor,dtype=next(iter(weights.values())).dtype)
    if tensor.shape!=(1,21) or not np.isfinite(tensor).all():raise ValueError('Invalid model tensor')
    for step in plan['steps']:
        if step['kind']=='dense':tensor=tensor@weights[step['id']+'/w']+weights[step['id']+'/b']
        elif step['kind']=='activation':tensor=np.maximum(tensor,0)
        else:raise ValueError('Only frozen MLP plan supported')
    return float(tensor[0,0])

def probability(logit):return float(1/(1+np.exp(-np.clip(logit,-60,60))))

class FrozenRisk:
    def __init__(self,package):
        self.package=Path(package)
        manifest=read_json(self.package/'manifest.json')
        needed={'model.npz','preprocessing.json','profile_schema.json','model_config.json'}
        hashes={r['path']:r['sha256'] for r in manifest['files']}
        for name in needed:
            if file_sha(self.package/name)!=hashes[name]:raise ValueError('Frozen risk asset hash mismatch')
        self.schema=read_json(self.package/'profile_schema.json');self.preprocessing=read_json(self.package/'preprocessing.json')
        self.config=read_json(self.package/'model_config.json')
        with np.load(self.package/'model.npz',allow_pickle=False) as archive:self.weights={name:archive[name].copy() for name in archive.files}
        if self.preprocessing['input_columns']!=self.schema['feature_order']:raise ValueError('Feature order mismatch')
        self.model_hash=file_sha(self.package/'model.npz')

    def predict(self,profile):
            validation=validate_profile(profile,self.schema)
            if not validation['valid']:raise ValueError('Incomplete/invalid profile')
            logit=mlp_forward(transform_profile(profile,self.preprocessing),self.config['plan'],self.weights)
            score=probability(logit)
            return {'score':score,'class_id':int(score>0.5),'class_name':self.schema['class_names'][str(int(score>0.5))],'logit':logit,'model_sha256':self.model_hash,'profile_sha256':digest(profile),'unit':'historical_binary_model_score','calibrated_incidence_risk':False}

