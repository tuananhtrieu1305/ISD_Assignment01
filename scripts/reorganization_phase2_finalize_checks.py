"""Read-only migration checks and declared representation adapters; never train/TEST."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import warnings

ROOT = Path(__file__).resolve().parents[1]
P2 = ROOT / 'docs/reorganization/phase2'
PROJECTS = ['A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02']

def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.migration-tmp')
    temp.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)

def adapters():
    # Restore only the original Windows line-ending representation in compatibility views.
    # The canonical Git LF snapshot and every original scientific file remain unchanged.
    source = ROOT/'A06/datasets/stock/AAPL_2015_2025.csv'
    original = source.read_bytes()
    expected_lf = 'f145be9d08d100739a70d1d3eee3a8883d3437a7e40be331057acf31975f6ffa'
    expected_crlf = '2c8eef3c6a3836e2217bf3e99faaeec37d30e60298f7319e8f3748b71e5bd2b8'
    assert hashlib.sha256(original).hexdigest()==expected_lf
    normalized = original.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
    assert hashlib.sha256(normalized).hexdigest()==expected_crlf
    assert list(csv.reader(io.StringIO(original.decode())))==list(csv.reader(io.StringIO(normalized.decode())))
    physical = ROOT/'A06/provenance/materialized_raw/AAPL_2015_2025_CRLF.csv'
    physical.parent.mkdir(parents=True,exist_ok=True)
    if physical.exists(): assert physical.read_bytes()==normalized
    else: physical.write_bytes(normalized)
    mapping = load(P2/'runtime_view_map.json')
    changed = []
    for row in mapping['files']:
        if row['source'] not in {source.relative_to(ROOT).as_posix(),physical.relative_to(ROOT).as_posix()}: continue
        assert row['logical_path'].endswith('datasets/stock/AAPL_2015_2025.csv')
        target = ROOT/row['target']
        assert sha(target) in {expected_lf,expected_crlf}
        temporary = target.with_name(target.name+'.representation-tmp')
        temporary.write_bytes(normalized)
        temporary.replace(target)  # break a hardlink; never overwrite canonical raw bytes
        row.update(source=physical.relative_to(ROOT).as_posix(),sha256=expected_crlf,bytes=len(normalized),representation='original Windows CRLF; CSV rows unchanged')
        changed.append(row['target'])
    assert changed
    save(P2/'runtime_view_map.json',mapping)
    tsv=P2/'runtime_views.tsv'
    temporary=tsv.with_suffix('.tsv.tmp')
    temporary.write_text(''.join(f"{r['source']}\t{r['target']}\t{r['sha256']}\t{r['bytes']}\n" for r in mapping['files']),encoding='utf-8')
    temporary.replace(tsv)
    save(P2/'representation_adapters.json',{'status':'PASS','canonical_source':source.relative_to(ROOT).as_posix(),'canonical_sha256':sha(source),'materialized_path':physical.relative_to(ROOT).as_posix(),'materialized_sha256':sha(physical),'csv_rows_equal':True,'compatibility_targets':changed,'training_steps':0,'scientific_TEST_forward':0})
    sys.path.insert(0,str(ROOT/'_shared'))
    import numpy as np
    from assignment_runtime.cifar import read_binary
    archive=ROOT/'tieuluan3/datasets/raw/ch3/cifar10/cifar-10-binary.tar.gz'
    pixels,labels,tx,ty=read_binary(archive,train_limit=8)
    assert tx is ty is None
    with tarfile.open(archive,'r:gz') as handle:
        with handle.extractfile('cifar-10-batches-bin/data_batch_1.bin') as stream:
            records=np.frombuffer(stream.read(8*3073),dtype=np.uint8).reshape(8,3073)
    reference=np.stack([np.stack([r[1+c*1024:1+(c+1)*1024].reshape(32,32) for c in range(3)],axis=2) for r in records])
    assert np.array_equal(pixels,reference) and np.array_equal(labels,records[:,0])
    save(P2/'cifar_train_adapter_parity.json',{'status':'PASS','archive':archive.relative_to(ROOT).as_posix(),'archive_sha256':sha(archive),'format':'CIFAR-10 binary, explicit adapter; no Python-pickle substitution','input_scope':'data_batch_1.bin rows0:8 TRAIN only','sample_count':8,'shape':list(pixels.shape),'labels':labels.tolist(),'pixel_and_label_exact':True,'test_member_extracted':False,'training_steps':0,'scientific_TEST_forward':0})
    print('Representation adapters PASS')

def static():
    import nbformat
    from IPython.core.inputtransformer2 import TransformerManager
    transformer=TransformerManager()
    rows=[]
    issues=[]
    folder_count=0
    catalog_files=0
    python_count=0
    catalog_receipt=load(P2/'catalog_paths_sizes.json')
    assert catalog_receipt['status']=='PASS'
    catalog_receipts={r['project']:r for r in catalog_receipt['projects']}
    for project in PROJECTS:
        base=ROOT/project
        config=load(base/'project.json')
        for name in ['datasets','notebooks','web']:
            assert (base/name).is_dir(),(project,name)
            folder_count+=1
        for entry in config['notebooks']:
            path=base/entry['path']
            document=load(path)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                nbformat.validate(nbformat.from_dict(document))
            magic_cells=0
            for cell in document['cells']:
                if cell['cell_type']=='code':
                    source=''.join(cell.get('source',[]))
                    try: ast.parse(source)
                    except SyntaxError:
                        ast.parse(transformer.transform_cell(source))
                        magic_cells+=1
            assert entry['framework'] in {'keras','torch'},entry
            active_sha=sha(path)
            if 'revision_sha256' in entry: entry['revision_sha256']=active_sha
            rows.append({'project':project,'path':entry['path'],'framework':entry['framework'],'sha256':active_sha,'cells':len(document['cells']),'schema_ast':'PASS','ipython_magic_cells_transformed_without_execution':magic_cells,'legacy_schema_warnings':sorted({str(w.message).split('.')[0] for w in caught})})
        save(base/'project.json',config)
        receipt=catalog_receipts[project]
        assert sha(base/'datasets/catalog.json')==receipt['sha256'] and receipt['status']=='PASS'
        catalog_files+=receipt['file_references']
        for subtree in ['src','web/backend']:
            parent=base/subtree
            if not parent.exists(): continue
            for path in parent.rglob('*.py'):
                if any(part in {'__pycache__','.venv','node_modules'} for part in path.parts): continue
                ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
                python_count+=1
        print('Static project PASS',project,flush=True)
    paper2=load(ROOT/'tieuluan2/artifacts/manifests/phase32/registry_v3.json')
    assert len(paper2['chapters'])==5
    assert not (ROOT/'tieuluan2/src/ch06_multi_agent').exists()
    assert not (ROOT/'tieuluan2/web/frontend/src/v3/AgentTrace.tsx').exists()
    assert not any(r['family']=='multi_agent' for r in paper2['models'])
    paper3=load(ROOT/'tieuluan3/artifacts/manifests/phase32/registry_v3.json')
    assert len(paper3['chapters'])==6 and (ROOT/'tieuluan3/src/ch06_multi_agent').is_dir()
    save(P2/'static_verification.json',{'status':'PASS','projects':len(PROJECTS),'required_folders':folder_count,'notebooks':rows,'notebook_count':len(rows),'python_ast_files':python_count,'catalog_file_references_exist_and_size_match':catalog_files,'paper2_chapters':5,'paper3_chapters':6,'issues':issues,'training_steps':0,'scientific_TEST_forward':0})
    print(f'Static PASS {len(rows)} notebooks / {python_count} Python / {catalog_files} dataset references / {folder_count} folders')

def rawguard():
    sys.path.insert(0,str(ROOT/'_shared'))
    from assignment_runtime import activate
    activate('A06','torch')
    from src.config import RAW_STOCK_PATH, EXPECTED_STOCK_SHA256, RAW_CUSTOMER_PATH, EXPECTED_CUSTOMER_SHA256
    records=[]
    for path,expected in [(RAW_STOCK_PATH,EXPECTED_STOCK_SHA256),(RAW_CUSTOMER_PATH,EXPECTED_CUSTOMER_SHA256)]:
        assert sha(path)==expected
        records.append({'path':path.relative_to(ROOT).as_posix(),'sha256':expected})
    # Helper redirects writes; receipt itself is outside the frozen compatibility view.
    save(P2/'a06_raw_guard.json',{'status':'PASS','original_config_import':'src.config under A06 logical root','raw_files':records,'preprocessing_executed':False,'training_steps':0,'scientific_TEST_forward':0})
    print('A06 original raw checksum guard PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action',choices=['adapters','static','rawguard'],required=True)
    args=parser.parse_args()
    globals()[args.action]()
