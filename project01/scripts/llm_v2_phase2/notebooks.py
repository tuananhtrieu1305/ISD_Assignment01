"""One-time publish, then export/check only. The algorithm source is notebook cells."""
from pathlib import Path
import ast,hashlib,json,sys

P=Path(__file__).resolve().parents[2];F=Path(__file__).parent
GROUPS={'01_Data_KB_RAG.ipynb':['schemas','provider','risk','embedding','bm25','indexing','query','kg','retrieval','reranker'],
        '02_Diabetes_Multi_Agent.ipynb':['generation','pipeline','agents','transport'],
        '03_Evaluation.ipynb':['evaluation','analysis']}

BOOT='''from pathlib import Path
import sys,types,__future__
from IPython.core.magic import register_cell_magic
PROJECT=next(p for p in (Path.cwd(),*Path.cwd().parents) if (p/'docs/llm_v2/provider_config.example.json').exists())
sys.path.insert(0,str(PROJECT/'web/backend'))
RUN_API=False
RUN_EVALUATION=False
RUN_TRAINING=False
RUN_TEST=False
ALLOW_PAID_API=False
@register_cell_magic
def llm_v2_module(line,cell):
    name=line.strip();parent,_,child=name.rpartition('.')
    if parent not in sys.modules:
        package=types.ModuleType(parent);package.__path__=[str(PROJECT/'web/backend'/parent)];sys.modules[parent]=package
    module=sys.modules.get(name)
    if module is None:
        module=types.ModuleType(name);module.__package__=parent;module.__file__=str(PROJECT/'web/backend'/Path(*name.split('.')).with_suffix('.py'))
        sys.modules[name]=module;setattr(sys.modules[parent],child,module)
    exec(compile(cell,'<project01-llm-v2-notebook>/'+name,'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),module.__dict__)
'''


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def source_hash(nb):return hashlib.sha256(json.dumps([(c['cell_type'],c['source']) for c in nb['cells']],ensure_ascii=False).encode()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def publish():
    if (P/'artifacts/llm_v2/phase2/source_exports.json').exists():raise RuntimeError('Published. Edit notebook cells and export, never rerun producer.')
    def md(s):return {'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)}
    def code(s,**meta):return {'cell_type':'code','metadata':meta,'source':s.splitlines(keepends=True),'execution_count':None,'outputs':[]}
    for filename,names in GROUPS.items():
        cells=[md('# Project01 · RAG + Gemini v2\n\nCode thuật toán đầy đủ nằm trong các cell bên dưới. 01: dữ liệu/index/KG/retrieval và inference CDC; 02: generation/agents/Verifier/API; 03: evaluation/analysis. Các import liên notebook dùng backend export của chính các cell này; không đọc implementation từ provenance hoặc folder nhóm. Sửa source tại notebook, chạy `scripts/llm_v2_phase2/notebooks.py export`; không sửa backend riêng.\n\nGiữ attribution project RAG/KG của nhóm; bảng nguồn/hàm/cell ở docs/llm_v2/reuse_map.json và artifacts/llm_v2/phase2/actual_reuse.json. Môi trường: WSL Python3.11 serving riêng, không cài vào env Torch/Keras. Mặc định RUN_API/RUN_EVALUATION/RUN_TRAINING/RUN_TEST đều False, ALLOW_PAID_API=False. Không Run All để train/TEST lịch sử.\n\nKernel chạy source hiện tại cần các dependency serving đã khóa. Nguồn MedQuAD lịch sử không thay lời khuyên lâm sàng hiện hành.'),code(BOOT)]
        for name in names:
            source=(F/'authoring'/(name+'.py')).read_text(encoding='utf-8');tree=ast.parse(source);lines=source.splitlines(keepends=True)
            cells.append(md('## '+name+'\n\nInput → xử lý → output theo docstring và từng hàm. Các đoạn source port giữ tên class/hàm của nhóm; extension cho Gemini/medical được ghi trong bản đồ port.'))
            for node in tree.body:
                start=min([node.lineno]+[n.lineno for n in getattr(node,'decorator_list',[])])-1
                text=''.join(lines[start:node.end_lineno])+'\n'
                if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):cells.append(md('### '+node.name))
                cells.append(code('%%llm_v2_module project01_llm_v2.'+name+'\n'+text,module='project01_llm_v2.'+name))
        if filename.startswith('01'):
            cells += [md('## Dữ liệu/KG đã chuẩn bị — không gọi API\n\nĐếm các assertion có nguồn; đồ thị runtime giữ chiều và câu trích. Semantic index được build qua CLI có quota, không tự build khi Run All.'),
                      code("from project01_llm_v2.embedding import load_corpus,index_fingerprint\nfrom project01_llm_v2.kg import MiniKG\nchunks=load_corpus(PROJECT)\ngraph=MiniKG(PROJECT,chunks)\ndisplay({'chunks':len(chunks),'entities':len(graph.entities),'assertions':len(graph.assertions),'index_fingerprint':index_fingerprint(chunks),'API_called':False})\ndisplay(graph.neighborhood('Bệnh thận và tiểu đường')['relationships'][:2])\n")]
        elif filename.startswith('02'):
            cells += [md('## Đọc development đã lưu — không giả là live\n\nNhìn answer_vi trước, rồi evidence/verification. Không tự gọi Gemini khi Run All. Cần bật RUN_API và dùng runner giữ quota nếu muốn gọi mới.'),
                      code("import json\nfolder=PROJECT/'artifacts/llm_v2/phase2/development'\nfor path in sorted(folder.glob('*.json')):\n    row=json.loads(path.read_text())\n    if 'results' in row:\n        display({'saved_development':path.name,'question':row['question']})\n        for variant,result in row['results'].items():display({'variant':variant,'answer_vi':result.get('answer_vi'),'status':result.get('status')})\n")]
        else:
            cells += [md('## Kết quả mới đã lưu\n\n40 câu×2 nhánh, một lần mỗi câu/nhánh sau freeze; lỗi vẫn trong mẫu số. Không dùng P0/P1/P2/82,5% cũ. Chất lượng phải được review, không suy từ HTTP200/độ dài câu trả lời. Chưa đủ80 output thì báo chưa xong, không tạo biểu đồ chất lượng giả.'),
                      code("from project01_llm_v2.evaluation import summarize_saved\ndisplay(summarize_saved(PROJECT))\n")]
        for i,c in enumerate(cells):c['id']=f'llm-v2-{filename[:2]}-{i:04}'
        save(P/'notebooks'/filename,{'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'project01-gemini-serving','display_name':'Project01 Gemini serving (WSL3.11)','language':'python'},'source_authority':'inline cells','revision':'llm-v2'},'cells':cells})
    export()


def export(check=False):
    folder=P/'web/backend/project01_llm_v2';folder.mkdir(parents=True,exist_ok=True);records=[]
    for filename,names in GROUPS.items():
        nb=load(P/'notebooks'/filename);fingerprint=source_hash(nb)
        for name in names:
            marker='%%llm_v2_module project01_llm_v2.'+name+'\n'
            bodies=[''.join(c['source']).split('\n',1)[1] for c in nb['cells'] if ''.join(c['source']).startswith(marker)]
            assert bodies,name
            output='# GENERATED from notebooks/'+filename+'; source SHA256 '+fingerprint+'\n# Edit notebook cells; export with scripts/llm_v2_phase2/notebooks.py export.\n'+''.join(bodies)
            ast.parse(output);path=folder/(name+'.py')
            if check:assert path.read_text(encoding='utf-8')==output,'Notebook/export drift '+name
            else:path.write_text(output,encoding='utf-8')
            records.append({'module':name,'notebook':'notebooks/'+filename,'source_sha256':fingerprint,'export':path.relative_to(P).as_posix(),'sha256':hashlib.sha256(output.encode()).hexdigest()})
    if not check:
        (folder/'__init__.py').write_text('"""One-way exports of full source in three project01 notebooks."""\n')
        (P/'artifacts/llm_v2/phase2').mkdir(parents=True,exist_ok=True)
        save(P/'artifacts/llm_v2/phase2/source_exports.json',{'files':records,'source_authority':'notebook cells'})
    print(json.dumps({'source_export_parity':'PASS','modules':len(records),'notebooks':len(GROUPS)}))


if __name__=='__main__':
    action=sys.argv[1]
    if action=='publish':publish()
    else:export(check=action=='check')
