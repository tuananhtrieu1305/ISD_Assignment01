"""Read-only foundation audit; never invokes predictors, retrievers or evaluation."""
from pathlib import Path
import ast
import gzip
import hashlib
import json
import math
import warnings

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'project01'

def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def check():
    import nbformat
    inventory=load(ROOT/'docs/final_project01/baseline/inventory.json')
    for row in inventory['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    schema=load(PROJECT/'datasets/profile_schema.json')
    assets=load(PROJECT/'datasets/assets.json')
    corpus_name=next(name for name in assets['rag_files'] if name.endswith('chunks.jsonl.gz'))
    chunks={}
    with gzip.open(ROOT/assets['rag_files'][corpus_name]['path'],'rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['domain']=='medical':chunks[row['chunk_id']]=row
    partitions={split:load(PROJECT/f'datasets/benchmark/{split}.json')['cases'] for split in ['development','evaluation']}
    assert len(partitions['development'])==20 and len(partitions['evaluation'])==40
    summaries={}
    for split,rows in partitions.items():
        profiles=set();documents=set();texts=set();groups=set();counts={}
        for case in rows:
            assert case['split']==split and case['group_id'] not in groups
            groups.add(case['group_id']);counts[case['category']]=counts.get(case['category'],0)+1
            profile=case['profile']
            if profile is not None:
                assert set(profile)<=set(schema['feature_order'])
                for name,value in profile.items():
                    assert isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
                    assert schema['limits'][name][0]<=value<=schema['limits'][name][1],name
                full=set(profile)==set(schema['feature_order'])
                assert full==(case['category']!='missing')
                digest=hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest()
                assert case['profile_sha256']==digest
                assert digest not in profiles
                profiles.add(digest)
            for gold in case['gold_evidence']:
                source=chunks[gold['chunk_id']]
                assert source['text']==gold['evidence_text'] and source['document_id']==gold['document_id']
                assert hashlib.sha256(source['text'].encode()).hexdigest()==gold['text_sha256']
                documents.add(gold['document_id']);texts.add(gold['text_sha256'])
        summaries[split]={'profiles':profiles,'documents':documents,'texts':texts,'groups':groups,'counts':counts}
    for key in ['profiles','documents','texts','groups']:
        assert not summaries['development'][key]&summaries['evaluation'][key],key
    for record in load(PROJECT/'datasets/benchmark/protocol_lock.json')['files']:
        assert sha(PROJECT/record['path'])==record['sha256']
    notebooks=list((PROJECT/'notebooks').rglob('*.ipynb'))
    assert len(notebooks)==3
    for path in notebooks:
        document=load(path)
        with warnings.catch_warnings():
            warnings.simplefilter('error');nbformat.validate(nbformat.from_dict(document))
        for cell in document['cells']:
            if cell['cell_type']=='code':ast.parse(''.join(cell['source']))
    probe=load(PROJECT/'artifacts/phase1/probe.json')
    assert probe['status']=='PASS' and probe['model']['input_shape']==[1,21]
    assert probe['model']['dense_layers']==6 and probe['medical_chunks']==len(chunks)==762
    assert probe['medical_documents']==247 and probe['graph_anchors']==62
    assert probe['new_evaluation_runs']==0 and probe['historical_TEST_forward']==0 and probe['training_steps']==0
    assert probe['index_corpus_id_parity'] and probe['graph_chunk_parity']
    complete=PROJECT/'artifacts/phase1/complete.json'
    if complete.exists():
        for row in load(complete)['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    return {'status':'PASS','preserved_resources':len(inventory['files']),'notebooks':len(notebooks),'benchmark_counts':{s:r['counts'] for s,r in summaries.items()},'cross_split_profile_document_evidence_group_overlap':0,'gold_corpus_membership':'PASS','profile_bounds':'PASS','actual_kernel_probe':'PASS','training_steps':0,'historical_TEST_forward':0,'new_evaluation_runs':0}

if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False))
