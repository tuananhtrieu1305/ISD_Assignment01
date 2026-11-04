"""Derive a small medical-only serving package; never refit indexes or predictors."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'project01'

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def main():
    assets=load(PROJECT/'datasets/assets.json');folder=PROJECT/'artifacts/package/v1'
    if (folder/'manifest.json').exists():
        manifest=load(folder/'manifest.json')
        assert all(sha(folder/r['path'])==r['sha256'] for r in manifest['files'])
        print('Reuse verified package',manifest['package_bytes']);return
    folder.mkdir(parents=True,exist_ok=True)
    def checked(r):
        path=ROOT/r['path'];assert sha(path)==r['sha256'];return path
    for key,name in [('checkpoint','model.npz'),('config','model_config.json'),('preprocessing','preprocessing.json')]:shutil.copyfile(checked(assets['model'][key]),folder/name)
    for name in ['profile_schema.json','query_glossary.json']:shutil.copyfile(PROJECT/'datasets'/name,folder/name)
    for name in ['kg_medical_bm25.joblib','kg_medical_dense_lsa.joblib']:shutil.copyfile(checked(assets['rag_files'][name]),folder/name)
    rows=[]
    with gzip.open(checked(assets['rag_files']['kg_chunks.jsonl.gz']),'rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['domain']=='medical':rows.append(row)
    (folder/'medical_chunks.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
    with gzip.open(checked(assets['rag_files']['kg_graph_anchors.json.gz']),'rt',encoding='utf-8') as stream:graph=json.load(stream)['medical']
    save(folder/'medical_graph.json',graph);save(folder/'retrieval.json',assets['retrieval'])
    (folder/'ATTRIBUTION.md').write_text('MedQuAD by Asma Ben Abacha and contributors; CC BY 4.0. https://github.com/abachaa/MedQuAD/blob/master/LICENSE.txt\nDerived diabetes corpus, lexical anchor graph and index snapshot; filtered from the preserved package without changing text or index weights. Source commit 577bd37b96c02d1833b2c9eed2de9f96964e96cb.\nCDC BRFSS / UCI 891 / Alex Teboul dataset; upstream CC0 provenance retained in project01/datasets/catalog.json.\n',encoding='utf-8')
    files=[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(folder.iterdir()) if p.is_file()]
    manifest={'version':'project01.medical-package.1','files':files,'package_bytes':sum(r['bytes'] for r in files),'chunks':len(rows),'documents':len({r['document_id'] for r in rows}),'graph_anchors':len(graph),'source_corpus_sha256':assets['rag_files']['kg_chunks.jsonl.gz']['sha256'],'source_graph_sha256':assets['rag_files']['kg_graph_anchors.json.gz']['sha256'],'source_refs':assets,'indexes_refitted':False,'model_retrained':False,'finance_included':False}
    assert len(rows)==762 and len(graph)==62
    save(folder/'manifest.json',manifest)
    print('Packaged medical-only',manifest['package_bytes'],'bytes; 762 chunks, 62 anchors; no finance')

if __name__=='__main__':main()
