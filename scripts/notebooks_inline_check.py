"""Schema/AST and source coverage checks; all scientific originals remain read-only."""
from pathlib import Path
import ast
import hashlib
import json
import warnings
import nbformat
from IPython.core.inputtransformer2 import TransformerManager
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/notebook_revision/v1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=load(OUT/'manifest.json');rows=[]
for project in manifest['projects']:
    base=ROOT/project['project'];files=list((base/'notebooks').rglob('*.ipynb'))
    assert 1<=len(files)<=4,(project['project'],len(files))
    for path in files:
        doc=load(path)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');nbformat.validate(nbformat.from_dict(doc))
        module_cells={};code_count=0
        for cell in doc['cells']:
            if cell['cell_type']!='code':continue
            source=''.join(cell['source']);code_count+=1
            if source.startswith('%%inline_module '):
                directive,body=source.split('\n',1);parts=directive.split();ast.parse(body)
                assert 'read_text(' not in body or cell['metadata'].get('inline_module') # actual data/protocol source allowed
                module_cells.setdefault(parts[1],[]).append(body)
            else:ast.parse(TransformerManager().transform_cell(source))
        modules=doc.get('metadata',{}).get('notebook_revision',{}).get('embedded_modules',[])
        definitions=0
        for row in modules:
            original=ROOT/row['source'];assert sha(original)==row['sha256']
            source_tree=ast.parse(original.read_text(encoding='utf-8-sig'))
            embedded_tree=ast.parse('\n'.join(module_cells[row['module']]))
            old={n.name:n for n in source_tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))}
            new={n.name:n for n in embedded_tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))}
            assert old.keys()==new.keys(),row['module']
            for name,node in old.items():
                assert ast.dump(node,include_attributes=False)==ast.dump(new[name],include_attributes=False),(row['module'],name)
            definitions+=len(old)
        rows.append({'project':project['project'],'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'code_cells':code_count,'inline_modules':len(modules),'original_function_class_AST_matches':definitions,'schema':'PASS'})
for row in load(OUT/'backup.json')['files']:
    assert sha(ROOT/row['archived_path'])==row['sha256'],row['archived_path']
report={'status':'PASS','project_counts':{p['project']:len(p['notebooks']) for p in manifest['projects']},'notebook_count':len(rows),'notebooks':rows,'original_archived_files_verified':len(load(OUT/'backup.json')['files']),'training_steps':0,'scientific_TEST_forward':0}
(OUT/'static_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS',len(rows),'notebooks, max4/project;',sum(r['original_function_class_AST_matches'] for r in rows),'original definitions AST-identical')
