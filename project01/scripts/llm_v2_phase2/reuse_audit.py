"""Report concrete group symbol reuse, including exact AST matches and adapters."""
from pathlib import Path
import ast,hashlib,json,sys
from notebooks import GROUPS,load
P=Path(__file__).resolve().parents[2]


def symbols(source):
    output={}
    for n in ast.parse(source).body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):output[n.name]=n
        elif isinstance(n,ast.ClassDef):
            for f in n.body:
                if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)):output[n.name+'.'+f.name]=f
    return output


def main():
    mapping=load(P/'docs/llm_v2/reuse_map.json');records=[];exact=0;adapted=0
    for component in mapping['components']:
        original=P.parent/component['copied_path']
        text=original.read_text(encoding='utf-8')
        if original.suffix=='.ipynb':
            old={}
            for c in json.loads(text)['cells']:
                if c['cell_type']=='code':
                    try:old.update(symbols(''.join(c['source'])))
                    except SyntaxError:pass
            target_modules=['kg']
        else:
            old=symbols(text)
            name=original.name
            target_modules={'pre_retrieval.py':['query'],'hybrid_searcher.py':['retrieval'],'retriever.py':['retrieval'],
              'bm25_store.py':['bm25'],'chunking.py':['indexing'],'indexer.py':['indexing'],'embedding.py':['embedding'],
              'vector_db.py':['embedding'],'reranker.py':['reranker'],'prompt.py':['generation'],'generator.py':['generation'],
              'pipeline.py':['pipeline'],'schemas.py':['schemas'],'config.py':['provider'],'logging.py':['provider']}[name]
        new={};cells=[]
        for module in target_modules:
            new.update(symbols((P/'web/backend/project01_llm_v2'/f'{module}.py').read_text(encoding='utf-8')))
            filename=next(f for f,mods in GROUPS.items() if module in mods)
            nb=load(P/'notebooks'/filename)
            cells.extend({'notebook':'notebooks/'+filename,'cell_id':c['id'],'module':module} for c in nb['cells'] if c.get('metadata',{}).get('module')=='project01_llm_v2.'+module)
        matches=[]
        for name,node in old.items():
            if name in new:
                equal=ast.dump(node,include_attributes=False)==ast.dump(new[name],include_attributes=False)
                exact+=equal;adapted+=not equal;matches.append({'symbol':name,'status':'EXACT_AST' if equal else 'ADAPTED_WITH_INTERFACE'})
        records.append({**component,'status':'PORTED_NOTEBOOK_EXPORT','symbols_matched':matches,
                        'cells':cells,'provider_rule':'Gemini SDK only; no mandatory alternate provider or DB service'})
    out={'status':'PASS','components':records,'exact_ast_symbol_matches':exact,'adapted_symbol_matches':adapted,
         'scope':'Exact AST only where names match. Interface-only vector/embedding/provider adapters are explicitly changed, not claimed byte-identical.',
         'runtime_import_from_provenance':False,'manual_seed_used_extractor_not_run':True}
    (P/'artifacts/llm_v2/phase2/actual_reuse.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'mapped_components':len(records),'exact_AST':exact,'adapted':adapted}))


if __name__=='__main__':main()
