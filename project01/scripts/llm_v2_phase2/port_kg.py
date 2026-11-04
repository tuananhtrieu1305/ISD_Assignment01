from pathlib import Path
import ast,json

P=Path(__file__).resolve().parents[2];F=Path(__file__).parent
document=json.loads((P/'provenance/group_rag_kg_source/chatbot/Extract_Graph.ipynb').read_text(encoding='utf-8'))
names={'load_extraction_cache','save_extraction_cache','clean_text_value','normalize_key','normalize_extraction','build_graph_payload'}
found={}
for cell in document['cells']:
    if cell['cell_type']!='code':continue
    source=''.join(cell['source'])
    try:tree=ast.parse(source)
    except SyntaxError:continue
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names:found[node.name]=ast.get_source_segment(source,node)
assert set(found)==names
text='from pathlib import Path\nimport json,re\nfrom .provider import atomic_json,digest,read_json\n\n'+'\n\n'.join(found.values())+'\n'+(F/'authoring/kg_extension.txt').read_text(encoding='utf-8')
ast.parse(text);target=F/'authoring/kg.py'
if target.exists():raise RuntimeError('Port exists')
target.write_text(text,encoding='utf-8');print('KG6 original functions ported + reviewed medical seed adapter')
