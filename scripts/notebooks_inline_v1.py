"""Notebook-first revision: archive originals, embed implementations, merge entry points."""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import textwrap

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/notebook_revision/v1'
PROJECTS=['A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02']
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):write(p,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.inline-tmp');temp.write_text(s,encoding='utf-8');temp.replace(p)
def md(s):return {'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)}
def code(s,**metadata):return {'cell_type':'code','metadata':metadata,'source':s.splitlines(keepends=True),'outputs':[],'execution_count':None}

BOOTSTRAP='''from pathlib import Path
import sys, os, types, __future__
from IPython.core.magic import register_cell_magic
REPO = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "ASSIGN_REORGANIZATION_EXECUTION_PLAN.md").exists())
sys.path.insert(0, str(REPO / "_shared"))
from assignment_runtime import activate
ACTIVE_FRAMEWORK = "keras" if ".venv-keras" in sys.executable else "torch"
_context = activate(PROJECT_NAME, ACTIVE_FRAMEWORK)
LOGICAL_ROOT = Path(_context["logical_root"])
RUN_EXPERIMENTS = False
RUN_TRAINING = False
RUN_TEST = False
# Kết quả của lượt chạy mới nằm ngoài notebooks/, không ghi vào artifact gốc.
import assignment_runtime as _paths
_paths._WRITE_CONTEXT["output"] = REPO / PROJECT_NAME / "artifacts/notebook_runs/inline_v1"
_paths._WRITE_CONTEXT["overlay"] = False
INLINE_MODULES = {}

def _notebook_package(name):
    if not name:
        return None
    if name not in INLINE_MODULES:
        parent, _, child = name.rpartition(".")
        package = _notebook_package(parent)
        module = types.ModuleType(name)
        module.__package__ = parent
        module.__path__ = []  # Không tìm implementation khác trong file .py.
        module.__file__ = str(LOGICAL_ROOT / (name.replace(".", "/") + "/__init__.py"))
        module.__dict__.update(ACTIVE_FRAMEWORK=ACTIVE_FRAMEWORK, RUN_TRAINING=False, RUN_TEST=False)
        INLINE_MODULES[name] = module
        sys.modules[name] = module
        if package is not None:
            setattr(package, child, module)
    return INLINE_MODULES[name]

@register_cell_magic
def inline_module(line, cell):
    """Chạy đúng code trong cell ở namespace riêng; không đọc code từ .py."""
    name, relative, scope = line.split()
    if scope != "both" and scope != ACTIVE_FRAMEWORK:
        return
    parent, _, child = name.rpartition(".")
    _notebook_package(parent)
    module = _notebook_package(name)
    module.__file__ = str(LOGICAL_ROOT / relative)
    module.__package__ = name if relative.endswith("/__init__.py") else parent
    compiled = compile(cell, "<notebook>/" + name, "exec", flags=__future__.annotations.compiler_flag, dont_inherit=True)
    exec(compiled, module.__dict__)
    module.__notebook_source__ = True

print({"bài": PROJECT_NAME, "kernel": ACTIVE_FRAMEWORK, "train": RUN_TRAINING, "TEST": RUN_TEST})
'''

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'backup.json').exists():raise RuntimeError('Revision already prepared; resume build/verify')
    records=[]
    for project in PROJECTS:
        base=ROOT/project;archive=base/'provenance/notebooks_before_inline_v1'
        archive.mkdir(parents=True,exist_ok=True)
        config=base/'project.json';shutil.copyfile(config,archive/'project.json')
        for path in (base/'notebooks').rglob('*'):
            if path.is_file():records.append({'path':path.relative_to(ROOT).as_posix(),'archived_path':(archive/'notebooks'/path.relative_to(base/'notebooks')).relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
        shutil.move(str(base/'notebooks'),str(archive/'notebooks'))
        (base/'notebooks').mkdir()
        records.append({'path':config.relative_to(ROOT).as_posix(),'archived_path':(archive/'project.json').relative_to(ROOT).as_posix(),'sha256':sha(config),'bytes':config.stat().st_size})
    runner=ROOT/'scripts/run_assignment.py'
    shutil.copyfile(runner,OUT/'run_assignment_before.py')
    records.append({'path':'scripts/run_assignment.py','archived_path':(OUT/'run_assignment_before.py').relative_to(ROOT).as_posix(),'sha256':sha(runner),'bytes':runner.stat().st_size})
    save(OUT/'backup.json',{'files':records,'date':'2026-11-01','original_scientific_files_modified':False})
    save(OUT/'checkpoint.json',{'status':'IN_PROGRESS','step':'prepared','next':'build embedded notebooks; validate source closure and kernels','training_steps':0,'scientific_TEST_forward':0})
    print('Original notebook tree/config archived:',len(records),'files',flush=True)

def original(project,path):return ROOT/project/'provenance/notebooks_before_inline_v1/notebooks'/path
def prior(project):return load(ROOT/project/'provenance/notebooks_before_inline_v1/project.json')

class FrameworkImports(ast.NodeTransformer):
    def visit_FunctionDef(self,node):return node
    def visit_AsyncFunctionDef(self,node):return node
    def visit_ClassDef(self,node):return node
    def wrap(self,node,root):
        scope='keras' if root in {'tensorflow','keras'} or '.keras_impl' in root or root.endswith(('.keras_customer','.keras_stock')) else 'torch' if root=='torch' or '.pytorch_impl' in root or root.endswith(('.pytorch_customer','.pytorch_stock')) else None
        if scope:
            # Mixed-framework drivers declare registries at module scope. Keep
            # inactive names explicit without importing the other GPU runtime.
            inactive=[]
            for alias in node.names:
                local=alias.asname or (alias.name.split('.')[0] if isinstance(node,ast.Import) else alias.name)
                inactive.append(ast.Assign(targets=[ast.Name(id=local,ctx=ast.Store())],value=ast.Constant(None)))
            return ast.copy_location(ast.If(test=ast.Compare(left=ast.Name(id='ACTIVE_FRAMEWORK',ctx=ast.Load()),ops=[ast.Eq()],comparators=[ast.Constant(scope)]),body=[node],orelse=inactive),node)
        return node
    def visit_ImportFrom(self,node):return self.wrap(node,node.module or '')
    def visit_Import(self,node):
        nodes=[]
        for name in node.names:nodes.append(self.wrap(ast.Import(names=[name]),name.name.split('.')[0]))
        return nodes

def transformed(source):
    original_tree=ast.parse(source)
    tree=FrameworkImports().visit(copy.deepcopy(original_tree));ast.fix_missing_locations(tree)
    if ast.dump(tree,include_attributes=False)==ast.dump(original_tree,include_attributes=False):return source
    return ast.unparse(tree)+'\n'

def module_scope(name,source):
    if '.keras_impl' in name or name.endswith(('.keras_customer','.keras_stock')):return 'keras'
    if '.pytorch_impl' in name or name.endswith(('.pytorch_customer','.pytorch_stock')):return 'torch'
    roots=set()
    for node in ast.parse(source).body:
        if isinstance(node,ast.Import):roots.update(n.name.split('.')[0] for n in node.names)
        if isinstance(node,ast.ImportFrom):roots.add((node.module or '').split('.')[0])
    if roots & {'tensorflow','keras'} and 'torch' not in roots:return 'keras'
    if 'torch' in roots and not roots & {'tensorflow','keras'}:return 'torch'
    return 'both'

def module_index(project,recipe,overlay):
    index={}
    for row in recipe:
        if row['project']!=project or not row['logical_path'].endswith('.py'):continue
        logical=row['logical_path']
        module_path=logical[len(project)+1:] if project in {'A05','A06'} and logical.startswith(project+'/') else logical
        name=module_path[:-3].replace('/','.')
        if name.endswith('.__init__'):name=name[:-9]
        if not name or not all(p.isidentifier() for p in name.split('.')):continue
        source=ROOT/overlay.get(row['target'],row['source'])
        index[name]={'path':source,'logical':logical}
    return index

def imports_for(name,source,index,*,top_only=False):
    tree=ast.parse(source);deps=set()
    nodes=tree.body if top_only else ast.walk(tree)
    package=name if index[name]['logical'].endswith('/__init__.py') else name.rpartition('.')[0]
    for node in nodes:
        if isinstance(node,ast.Import):
            deps.update(a.name for a in node.names if a.name in index)
        elif isinstance(node,ast.ImportFrom):
            module=node.module or ''
            if node.level:
                try:module=importlib.util.resolve_name('.'*node.level+module,package)
                except (ImportError,ValueError):continue
            if module in index:deps.add(module)
            deps.update(module+'.'+a.name for a in node.names if module+'.'+a.name in index)
    return deps-{name}

def inline_cells(index,seeds):
    sources={};closure=set();pending=list(seeds)
    while pending:
        name=pending.pop()
        if name in closure:continue
        if name not in index:raise KeyError('Missing module '+name)
        source=index[name]['path'].read_text(encoding='utf-8-sig')
        sources[name]=source;closure.add(name)
        pending.extend(imports_for(name,source,index)-closure)
    ordered=[];visiting=set();done=set()
    def visit(name):
        if name in done or name in visiting:return
        visiting.add(name)
        for dep in sorted(imports_for(name,sources[name],index,top_only=True)):
            if dep in closure:visit(dep)
        visiting.remove(name);done.add(name);ordered.append(name)
    for name in sorted(closure):visit(name)
    cells=[];records=[]
    for name in ordered:
        source=sources[name];scope=module_scope(name,source)
        cells.append(md(f'### `{name}`\n\nImplementation đầy đủ ở các cell ngay dưới: đọc imports, từng hàm/lớp rồi mới đến phần thực hành. '+('Kernel '+scope+'.\n' if scope!='both' else '\n')))
        tree=ast.parse(source);lines=source.splitlines(keepends=True)
        blocks=[];header=[]
        for node in tree.body:
            start=min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])-1
            chunk=''.join(lines[start:node.end_lineno])+'\n'
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                if header:blocks.append(('Thiết lập / hằng số',''.join(header)));header=[]
                blocks.append((node.name,chunk))
            else:header.append(chunk)
        if header:blocks.append(('Thiết lập / điểm vào',''.join(header)))
        for label,body in blocks:
            cells.append(md('#### '+label))
            cells.append(code(f"%%inline_module {name} {index[name]['logical']} {scope}\n"+transformed(body),inline_module=name,scope=scope,source_file=index[name]['path'].relative_to(ROOT).as_posix(),original_source_sha256=sha(index[name]['path'])))
        records.append({'module':name,'source':index[name]['path'].relative_to(ROOT).as_posix(),'sha256':sha(index[name]['path']),'scope':scope,'blocks':len(blocks)})
    return cells,records

def is_bootstrap(cell):
    s=''.join(cell.get('source',[]))
    return cell['cell_type']=='code' and ('_activate(' in s or 'activate(PROJECT_NAME' in s)

def append_original(cells,project,path,scope='both',run=False,seen=None):
    doc=load(original(project,path))
    cells.append(md('## Thực hành: '+Path(path).stem+'\n\nCode và output lịch sử được giữ để đối chiếu. `RUN_EXPERIMENTS=False` nên không tự tạo split/train/TEST hoặc ghi lại kết quả đã khóa.'))
    for cell in doc['cells']:
        if is_bootstrap(cell):continue
        copycell=copy.deepcopy(cell)
        s=''.join(cell.get('source',[]))
        if cell['cell_type']=='code':
            if seen is not None and hashlib.sha256(s.encode()).hexdigest() in seen:continue
            if seen is not None:seen.add(hashlib.sha256(s.encode()).hexdigest())
            condition='RUN_EXPERIMENTS'+(' and ACTIVE_FRAMEWORK == '+repr(scope) if scope!='both' else '')
            copycell['source']=('if '+condition+':\n'+textwrap.indent(s or 'pass\n','    ')).splitlines(keepends=True)
            copycell['execution_count']=None
            copycell['metadata']['historical_output']=True
        cells.append(copycell)

def result_cells(project,topic):
    if project=='A04':pattern='artifacts/pipeline04/**/metrics/*comparison.csv'
    elif project=='A05':pattern='results/metrics/*models.csv'
    elif project=='A06':pattern='results/metrics/*metrics.json'
    elif project=='tieuluan1':pattern=f'artifacts/metrics/{topic}*comparison*.csv'
    elif project in {'tieuluan2','tieuluan3'}:pattern='artifacts/metrics/phase26/*summary*.csv'
    else:return []
    # Only files that actually exist are listed; no inferred or regenerated numbers.
    root=ROOT/project
    candidates=list(root.glob(pattern))[:12]
    if project in {'tieuluan2','tieuluan3'}:candidates=[]
    if not candidates:return []
    paths=[p.relative_to(ROOT).as_posix() for p in candidates]
    return [md('## Kết quả gốc để đối chiếu\n\nCác file đã lưu được đọc nguyên trạng; không fit hoặc forward TEST mới.'),code('import json\nimport pandas as pd\nfrom IPython.display import display\nfor _relative in '+repr(paths)+':\n    _path = REPO / _relative\n    print(_relative)\n    if _path.suffix == ".csv": display(pd.read_csv(_path))\n    else: display(json.loads(_path.read_text()))\n')]

def publish(project,name,title,entries,index,seeds=(),topic=''):
    cells=[md('# '+title+'\n\nNotebook là nơi đọc và sửa toàn bộ implementation dưới đây: dữ liệu, mô hình, loss, optimizer, train/đánh giá. Không cần mở file `.py` để xem thuật toán. Các bản `.py` cũ giữ nguyên để bảo toàn backend/artifact.\n\n**Cách đọc:** khởi tạo → code từng hàm/lớp → thực hành theo dataset → kết quả. `%%inline_module` chỉ chạy code có ngay trong cell ở namespace riêng, không nạp implementation từ `.py`. Mỗi framework dùng kernel WSL riêng; code của cả hai vẫn hiện trong notebook. Mặc định không train/TEST lại.'),code('PROJECT_NAME = '+repr(project)+'\n'+BOOTSTRAP)]
    modules=[]
    if seeds:
        embedded,modules=inline_cells(index,list(seeds));cells+=embedded
    if project in {'tieuluan2','tieuluan3'} and any(r['module']=='src.common.backend_models' for r in modules):
        families=['rnn','lstm'] if 'RNN' in name else ['mlp','cnn'] if 'ML_CNN' in name else ['cnn'] if 'CNN' in name else ['mlp']
        cells += [md('## Chạy thử trực tiếp code vừa khai báo\n\nVí dụ tensor **synthetic** nhỏ, weights mới khởi tạo: kiểm forward của NumPy và framework trong kernel hiện tại. Không optimizer step, không train, không dùng dataset TEST; các số dưới đây không phải kết quả nghiên cứu.'),code('import numpy as np\nfrom src.common.model_core import build_plan, canonical_weights\nfrom src.common.numpy_engine import NumpyNetwork\nfrom src.common.backend_models import TorchBackend, KerasBackend\nfor _family in '+repr(families)+':\n    _shape = {"mlp": (3,), "cnn": (8,8,3), "rnn": (4,3), "lstm": (4,3)}[_family]\n    _plan = build_plan(_family, _shape, 2, tiny=True)\n    _weights = canonical_weights(_plan, 42)\n    _x = np.zeros((2, *_shape), dtype=np.float32)\n    _numpy = NumpyNetwork(_plan, _weights).forward(_x)\n    _native = (KerasBackend if ACTIVE_FRAMEWORK == "keras" else TorchBackend)(_plan, _weights, "cpu").predict(_x)\n    assert np.isfinite(_native).all() and np.allclose(_numpy, _native, atol=1e-4, rtol=1e-4)\n    print(_family, "synthetic forward", _native.shape, "max diff", float(np.max(np.abs(_numpy-_native))))\n')]
    seen=set()
    for path,scope in entries:append_original(cells,project,path,scope,seen=seen)
    cells+=result_cells(project,topic)
    cells.append(code('import inspect\n_notebook_defined = [(name, key) for name, mod in INLINE_MODULES.items() for key, obj in vars(mod).items() if inspect.isfunction(obj) and obj.__module__ == name]\nassert all(vars(INLINE_MODULES[name])[key].__code__.co_filename.startswith("<notebook>/") for name,key in _notebook_defined)\nprint({"module có code ngay trong notebook": sum(bool(getattr(m,"__notebook_source__",False)) for m in INLINE_MODULES.values()), "hàm inline":len(_notebook_defined), "train/TEST đã chạy":False})\n'))
    for i,cell in enumerate(cells):cell['id']=f'inline-v1-{i:05d}'
    framework='keras' if project=='A05' else 'torch'
    doc={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','language':'python','display_name':'Python3.11 WSL '+framework},'notebook_revision':{'version':'inline-v1','source_authority':'notebook code cells','embedded_modules':modules,'merged_from':[e[0] for e in entries],'default_train':False,'default_TEST':False}},'cells':cells}
    path=ROOT/project/'notebooks'/name;save(path,doc)
    return {'path':'notebooks/'+name,'framework':framework,'supported_frameworks':['torch','keras'] if project not in {'A05','agent01','agent02'} else [framework],'role':'read-only default; complete inline implementation and original experiment code','sha256':sha(path),'embedded_module_count':len(modules),'cells':len(cells)}

def build():
    assert (OUT/'backup.json').exists()
    recipe=load(ROOT/'docs/reorganization/phase2/runtime_view_map.json')['files']
    overlay={r['target']:r['source'] for r in load(ROOT/'docs/reorganization/phase3/runtime_source_overlay.json')['files']}
    manifest=[]
    for project in PROJECTS:
        config=prior(project);old=config['notebooks'];index=module_index(project,recipe,overlay);rows=[]
        if project in {'A01','A02','A03','agent01'}:
            for entry in old:
                source=original(project,entry['path'][len('notebooks/'):]);dst=ROOT/project/entry['path'];shutil.copyfile(source,dst)
                rows.append(dict(entry,sha256=sha(dst)))
        elif project=='A04':
            groups=[('01_Tabular_DNN.ipynb','A04 · DNN: tiểu đường, giá nhà và khách hàng',['customer_behavior','diabetes','house_price']),('02_MNIST_CNN.ipynb','A04 · CNN: MNIST',['mnist']),('03_CIFAR10_CNN.ipynb','A04 · CNN: CIFAR-10',['cifar10'])]
            for name,title,tasks in groups:
                entries=[(r['path'][len('notebooks/'):],r['framework']) for task in tasks for r in old if '/training/'+task+'_' in r['path']]
                rows.append(publish(project,name,title,entries,index))
        elif project=='A05':
            rows.append(publish(project,'01_CNN_Co_Ban_Va_So_Sanh.ipynb','A05 · CNN cơ bản và so sánh',[('01_CNN_Fundamentals.ipynb','keras'),('05_Model_Comparison.ipynb','keras')],index,['models.architectures']))
            for r in old[1:4]:
                name=Path(r['path']).name
                rows.append(publish(project,name,'A05 · '+name[:-6],[(name,'keras')],index,['models.architectures']))
        elif project=='A06':
            rows.append(publish(project,'01_RNN_Co_Ban.ipynb','A06 · RNN cơ bản: NumPy, Keras và PyTorch',[('01_RNN_Fundamentals.ipynb','torch'),('01_RNN_Fundamentals_Keras.ipynb','keras')],index))
            for tag,title,paths,seeds in [('02_Customer_Behavior.ipynb','A06 · Customer behavior — dữ liệu đến RNN',['02_Customer_Behavior_Data.ipynb','04_PyTorch_Customer_RNN.ipynb','06_Keras_Customer_RNN.ipynb'],['src.customer_pipeline','src.pytorch_customer','src.keras_customer']),('03_Stock_Price.ipynb','A06 · Stock — dữ liệu đến dự báo RNN',['03_Stock_Data.ipynb','05_PyTorch_Stock_RNN.ipynb','07_Keras_Stock_RNN.ipynb'],['src.stock_pipeline','src.pytorch_stock','src.keras_stock'])]:
                entries=[(p,'keras' if 'Keras' in p else 'torch' if 'PyTorch' in p else 'both') for p in paths]
                rows.append(publish(project,tag,title,entries,index,seeds))
            rows.append(publish(project,'04_So_Sanh_Framework.ipynb','A06 · So sánh Keras/PyTorch và baseline',[('08_Framework_Comparison.ipynb','both')],index,['src.framework_comparison']))
        elif project=='tieuluan1':
            for chapter,kind in [(2,'mlp'),(3,'cnn'),(4,'rnn')]:
                seeds=[f'term_paper.src.{f}.{kind}' for f in ['scratch','keras_impl','pytorch_impl']]+[f'term_paper.src.common.run_ch{chapter}_experiments']
                entries=[(Path(r['path']).name,'both') for r in old if f'ch{chapter}_' in r['path']]
                rows.append(publish(project,f'0{chapter-1}_{kind.upper()}_Day_Du.ipynb',f'Tiểu luận1 · Chương{chapter}: {kind.upper()} từ đầu đến cuối',entries,index,seeds,topic=f'ch{chapter}'))
        elif project in {'tieuluan2','tieuluan3'}:
            neural=['src.common.model_core','src.common.numpy_engine','src.common.backend_models','src.common.native_training','src.common.training_core']
            ml=neural+['src.ch02_ml.experiment','src.ch02_ml.training','src.ch02_ml.baselines']
            cnn=neural+['src.ch03_cnn.experiment','src.ch03_cnn.training','src.ch03_cnn.image_cache']
            rnn=neural+['src.ch04_rnn_lstm.experiment','src.ch04_rnn_lstm.training','src.ch04_rnn_lstm.phase29.experiment','src.ch04_rnn_lstm.phase29.training']
            rag=['src.ch05_knowledge_rag.service','src.ch05_knowledge_rag.runtime','src.ch05_knowledge_rag.structural']
            agents=['src.ch06_multi_agent.core','src.ch06_multi_agent.tools','src.ch06_multi_agent.executor','src.ch06_multi_agent.service','src.ch06_multi_agent.benchmark']
            groups=[('01_ML_CNN.ipynb','ML và CNN',['ch02_ml','ch03_cnn'],sorted(set(ml+cnn))),('02_RNN_LSTM.ipynb','RNN và LSTM',['ch04_rnn_lstm'],rnn),('03_Knowledge_RAG.ipynb','Knowledge Graph và RAG',['ch05_knowledge_rag'],rag),('04_Multi_Agent.ipynb','Hệ đa agent',['ch06_multi_agent'],agents)] if project=='tieuluan3' else [('01_ML.ipynb','Machine Learning',['ch02_ml'],ml),('02_CNN.ipynb','CNN',['ch03_cnn'],cnn),('03_RNN_LSTM.ipynb','RNN và LSTM',['ch04_rnn_lstm'],rnn),('04_Knowledge_RAG.ipynb','Knowledge Graph và RAG',['ch05_knowledge_rag'],rag)]
            for name,title,tags,seeds in groups:
                entries=[(r['path'][len('notebooks/'):],'both') for r in old if any('/'+t+'/' in r['path'] for t in tags)]
                rows.append(publish(project,name,project+' · '+title,entries,index,seeds))
        else:
            seeds=['agent02_assignment.code.'+name for name in ['controlled','training','augmented','pair_training','gold_regime','market_oracle','reference_adapter','reference_training','baseline_runs','sweep_runs','augmented_runs','baseline_analysis','phase06_analysis','phase07_analysis','report_assets']]
            rows.append(publish(project,'AG02_Code_and_Results.ipynb','Agent02 · Code đầy đủ và kết quả',[('AG02_Code_and_Results.ipynb','both')],index,seeds))
        assert 1<=len(rows)<=4,(project,len(rows))
        config['notebooks']=rows;config['notebook_revision']='inline-v1'
        save(ROOT/project/'project.json',config)
        manifest.append({'project':project,'notebooks':rows})
        print(project,len(rows),sum(r.get('embedded_module_count',0) for r in rows),'inline modules',flush=True)
    save(OUT/'manifest.json',{'projects':manifest,'source_code_location':'executable notebook cells','models_trained':False,'scientific_TEST_forward':0})
    save(OUT/'checkpoint.json',{'status':'IN_PROGRESS','step':'built','next':'schema/source coverage and fresh-kernel smoke; update web links/runner/docs','training_steps':0,'scientific_TEST_forward':0})

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','build']);args=parser.parse_args();globals()[args.action]()
