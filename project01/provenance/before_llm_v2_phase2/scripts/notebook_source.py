"""Publish authored code to notebooks once; export only from notebook cells thereafter."""
from pathlib import Path
import argparse
import ast
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'project01'
BACKEND=PROJECT/'web/backend'
GROUPS={'01_Data_KB_RAG.ipynb':['foundation'],'02_Diabetes_Multi_Agent.ipynb':['agents','transport'],'03_Evaluation.ipynb':['evaluation']}

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def source_hash(document):
    return hashlib.sha256(json.dumps([(c['cell_type'],c['source']) for c in document['cells']],ensure_ascii=False).encode()).hexdigest()

BOOT='''from pathlib import Path
import sys, os, types, __future__
from IPython.core.magic import register_cell_magic
PROJECT=next(p for p in (Path.cwd(),*Path.cwd().parents) if (p/'datasets/assets.json').exists() and (p/'notebooks').exists())
sys.path.insert(0,str(PROJECT/'web/backend'))
os.environ['OPENBLAS_NUM_THREADS']='1'
RUN_TRAINING=False
RUN_TEST=False
RUN_EVALUATION=False
@register_cell_magic
def project_module(line,cell):
    name=line.strip()
    parent,_,child=name.rpartition('.')
    if parent not in sys.modules:
        package=types.ModuleType(parent);package.__path__=[str(PROJECT/'web/backend/project01_core')];sys.modules[parent]=package
    module=sys.modules.get(name)
    if module is None:
        module=types.ModuleType(name);module.__package__=parent;module.__file__=str(PROJECT/'web/backend'/Path(*name.split('.')).with_suffix('.py'));sys.modules[name]=module;setattr(sys.modules[parent],child,module)
    exec(compile(cell,'<project01-notebook>/'+name,'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),module.__dict__)
'''

def seed():
    if (PROJECT/'artifacts/phase2/freeze.json').exists():raise RuntimeError('Frozen source: create a declared revision before editing')
    descriptions={'foundation':'Dữ liệu, preprocessing, 6 Dense, sparse/LSA, KB/KG/fusion và trích xuất bằng chứng. Không fitting hoặc train lại.','agents':'Coordinator, Risk/Knowledge Agent, Verifier, Reporter; budget và process deadline.','transport':'API Flask nhận dữ liệu có kiểm schema; cùng pipeline notebook, không giả lập.','evaluation':'Evaluator, ghi output một lần, so sánh số, retrieval và plot; gold chỉ vào evaluator, không vào agent.'}
    def md(s):return {'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)}
    def code(s,**metadata):return {'cell_type':'code','metadata':metadata,'source':s.splitlines(keepends=True),'execution_count':None,'outputs':[]}
    for filename,names in GROUPS.items():
        cells=[md('# Project01 · '+filename[3:-6].replace('_',' ')+'\n\nCode thực nằm trực tiếp trong cell. Các module backend là export của những cell này; chỉnh thuật toán ở notebook rồi chạy `notebook_source.py export`. Notebook 01 chứa model/retrieval, 02 chứa agent/API, 03 chứa evaluator/plot. Không cần mở `.py` để xem implementation. `%%project_module` thực thi source trong cell ở namespace riêng; không đọc implementation từ file khác.\n\nMặc định không train, không TEST cũ, không tự chạy evaluation. Kết quả bên dưới là demo development hoặc đọc output đã lưu.'),code(BOOT)]
        for name in names:
            path=PROJECT/'artifacts/phase2/authoring'/(name+'.py')
            source=path.read_text(encoding='utf-8');lines=source.splitlines(keepends=True);tree=ast.parse(source)
            cells.append(md('## '+name+'\n\n'+descriptions[name]))
            for node in tree.body:
                start=min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])-1
                body=''.join(lines[start:node.end_lineno])+'\n'
                label=getattr(node,'name','Imports / thiết lập')
                if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):cells.append(md('### '+label))
                cells.append(code('%%project_module project01_core.'+name+'\n'+body,module='project01_core.'+name))
        if filename.startswith('01'):
            cells.extend([md('## Chạy thật: profile TRAIN và câu hỏi development\n\nScore là nhãn khảo sát lịch sử, không incidence risk. Evidence là trích đoạn corpus tiếng Anh.'),code("from project01_core.foundation import Runtime, read_json\nruntime=Runtime(PROJECT/'artifacts/package/v1')\nprofile=read_json(PROJECT/'datasets/demo_profiles.json')['profiles'][0]['profile']\ndisplay(runtime.predict(profile))\nretrieval=runtime.retrieve('physical activity diabetes')\ndisplay({'query':retrieval['query_normalized'],'answer':retrieval['answer'],'citations':retrieval['citations'],'graph_paths':len(retrieval['graph_paths'])})\n")])
        elif filename.startswith('02'):
            cells.extend([md('## Demo development: cả hai specialist + verifier + reporter\n\nKhông chạy bộ evaluation. Mẫu có nguồn TRAIN, query là development; trace chỉ ghi hành động/tool, không chain-of-thought.'),code("from project01_core.foundation import Runtime,read_json\nfrom project01_core.agents import assist\nruntime=Runtime(PROJECT/'artifacts/package/v1')\nprofile=read_json(PROJECT/'datasets/demo_profiles.json')['profiles'][0]['profile']\nrequest={'mode':'combined','question':'Explain physical activity and diabetes.','profile':profile,'language':'en'}\nresult=assist(runtime,request,'P2')\ndisplay(result['answer'])\ndisplay(result['trace'])\nassert result['risk'] is not None and result['knowledge'] is not None and result['tool_calls']<=8\n")])
        else:
            cells.extend([md('## Đọc kết quả đã lưu; không tự mở evaluation\n\nTask success không phải accuracy chẩn đoán; gold evidence chưa exhaustive. Hình và giải thích chỉ lấy từ saved outputs. Lượt evaluation chỉ chạy qua CLI sau khi freeze source.'),code("from project01_core.evaluation import read_results, summarize, plot_results\nfolder=PROJECT/'artifacts/phase2/evaluation'\nif (folder/'results').exists():\n    rows=read_results(folder/'results')\n    display(summarize(rows))\n    plot_results(rows,PROJECT/'report/figures')\n    from IPython.display import Image, display\n    for name in ['task_success.png','evidence_and_coverage.png','latency_tools.png']:\n        display(Image(filename=str(PROJECT/'report/figures'/name)))\nelse:\n    print('Chưa có evaluation; không tự chạy khi Run All.')\n")])
        for i,cell in enumerate(cells):cell['id']=f'project01-v2-{i:04}'
        save(PROJECT/'notebooks'/filename,{'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','language':'python','display_name':'WSL Python3.11 NumPy CPU'},'source_authority':'notebook cells','phase':2},'cells':cells})
    export()

def export(check=False):
    records=[]
    package=BACKEND/'project01_core';package.mkdir(parents=True,exist_ok=True)
    if not check:(package/'__init__.py').write_text('"""Exported from project01 notebooks; edit notebook cells, then export."""\n')
    for filename,names in GROUPS.items():
        document=load(PROJECT/'notebooks'/filename);fingerprint=source_hash(document)
        for name in names:
            bodies=[]
            for cell in document['cells']:
                source=''.join(cell['source'])
                if source.startswith('%%project_module project01_core.'+name+'\n'):bodies.append(source.split('\n',1)[1])
            assert bodies,name
            output='# GENERATED from notebooks/'+filename+'; source SHA256 '+fingerprint+'\n# Edit the notebook, then run scripts/notebook_source.py export.\n'+''.join(bodies)
            ast.parse(output);path=package/(name+'.py')
            if check:assert path.read_text(encoding='utf-8')==output,'Notebook/export drift: '+name
            else:path.write_text(output,encoding='utf-8')
            records.append({'module':name,'notebook':'notebooks/'+filename,'notebook_source_sha256':fingerprint,'export':path.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(output.encode()).hexdigest()})
    if not check:save(PROJECT/'artifacts/phase2/source_exports.json',{'files':records,'source_authority':'notebook cells'})
    print('Notebook/export parity PASS',len(records))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['seed','export','check']);args=parser.parse_args()
    if args.action=='seed':seed()
    else:export(check=args.action=='check')
