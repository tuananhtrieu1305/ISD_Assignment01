from pathlib import Path
import ast
from notebooks import P,load,save,export
F=Path(__file__).parent;path=P/'notebooks/03_Evaluation.ipynb';nb=load(path)
if any(c.get('metadata',{}).get('module')=='project01_llm_v2.analysis' for c in nb['cells']):raise RuntimeError('Already added')
text=(F/'authoring/analysis.py').read_text(encoding='utf-8');lines=text.splitlines(keepends=True)
nb['cells'].append({'id':'llm-v2-analysis-guide','cell_type':'markdown','metadata':{},'source':['## Review và biểu đồ từ saved outputs\n','Code dưới chỉ đọc80 output và review sau freeze. Không sinh điểm khi review còn thiếu. quality: điểm0–8; evidence: tỉ lệ hỗ trợ/Recall@6; latency_calls: giây vàSDK call mới, cache tách riêng. Không gọi LLM/TEST/train.']})
for i,node in enumerate(ast.parse(text).body):
    start=min([node.lineno]+[n.lineno for n in getattr(node,'decorator_list',[])])-1
    body=''.join(lines[start:node.end_lineno])+'\n'
    nb['cells'].append({'id':f'llm-v2-analysis-{i:03}','cell_type':'code','metadata':{'module':'project01_llm_v2.analysis'},
                        'source':('%%llm_v2_module project01_llm_v2.analysis\n'+body).splitlines(keepends=True),'outputs':[],'execution_count':None})
save(path,nb);export()
