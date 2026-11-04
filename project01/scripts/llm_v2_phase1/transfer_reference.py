"""Copy selected group source and record every omitted file without copying secrets/data."""
from pathlib import Path
import ast
import hashlib
import json
import re

PROJECT=Path(__file__).resolve().parents[2]
ROOT=PROJECT.parent
SOURCE=ROOT/'RAG_KG_Tham_khao/PTHTTM-RAG'
DEST=PROJECT/'provenance/group_rag_kg_source'
SECRET=re.compile(r'AIza[0-9A-Za-z_-]{20,}|AQ\.[0-9A-Za-z_-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{25,}')

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    target=DEST/'transfer_manifest.json'
    if target.exists():raise RuntimeError('Transfer already exists; verify/resume explicitly, never overwrite')
    snapshot=json.loads((ROOT/'docs/final_project01/llm_v2/reference_rag_kg_snapshot.json').read_text(encoding='utf-8-sig'))
    for row in snapshot['files']:
        assert sha((ROOT/row['path']).read_bytes())==row['sha256'],row['path']
    files=[];imports=[]
    for path in sorted(SOURCE.rglob('*')):
        if not path.is_file():continue
        relative=path.relative_to(SOURCE).as_posix()
        if '.git' in path.relative_to(SOURCE).parts:continue
        selected=(relative.startswith('chatbot/app/') and path.suffix=='.py') or relative in {
            'README.md','compose.yaml','chatbot/requirements.txt','chatbot/Extract_Graph.ipynb',
            'chatbot/tests/test_pipeline.py','chatbot/tests/test_observability.py',
            'frontend/README.md','frontend/app.js','frontend/styles.css','frontend/index.html'}
        if path.name.upper().startswith(('LICENSE','COPYING','NOTICE')):selected=True
        raw=path.read_bytes();row={'original_path':path.relative_to(ROOT).as_posix(),'original_sha256':sha(raw),'bytes':len(raw)}
        if not selected:
            row.update(disposition='omitted_non_runtime',reason='Legal data/index/graph, environment/credentials, deployment helper or unused asset; not needed by new core')
            files.append(row);continue
        text=raw.decode('utf-8-sig');output=raw;transforms=[]
        if path.suffix=='.ipynb':
            notebook=json.loads(text)
            for cell in notebook['cells']:
                if cell['cell_type']=='code':cell['outputs']=[];cell['execution_count']=None
                source=''.join(cell.get('source',[]))
                cleaned=SECRET.sub('[REDACTED_SECRET]',source)
                if cleaned!=source:cell['source']=cleaned.splitlines(keepends=True)
            notebook['metadata'].pop('widgets',None)
            output=(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n').encode('utf-8')
            transforms.append('Cleared execution outputs/counts and widget state; secret-pattern redaction if present')
        elif SECRET.search(text):
            output=SECRET.sub('[REDACTED_SECRET]',text).encode('utf-8');transforms.append('Redacted secret-like token')
        copied=DEST/relative;copied.parent.mkdir(parents=True,exist_ok=True);copied.write_bytes(output)
        assert sha(copied.read_bytes())==sha(output)
        row.update(disposition='copied',copied_path=copied.relative_to(ROOT).as_posix(),copied_sha256=sha(output),transforms=transforms)
        if path.suffix=='.py':
            tree=ast.parse(output.decode('utf-8-sig'))
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('app'):
                    module=DEST/'chatbot'/Path(*node.module.split('.'))
                    imports.append({'source':relative,'module':node.module,'target_relative':module.relative_to(DEST).as_posix()})
        files.append(row)
    for row in imports:
        path=DEST/row['target_relative'];assert path.with_suffix('.py').is_file() or (path/'__init__.py').is_file(),row
    manifest={'date':'2026-11-02','source_root':SOURCE.relative_to(ROOT).as_posix(),
              'destination':DEST.relative_to(ROOT).as_posix(),'files':files,'internal_imports':imports,
              'copied_count':sum(r['disposition']=='copied' for r in files),
              'omitted_count':sum(r['disposition']!='copied' for r in files),
              'source_modified':False,'reference_folder_deleted':False,'runtime_import_from_provenance_allowed':False}
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (DEST/'ATTRIBUTION.md').write_text('# Source nhóm tham khảo\n\nSource được người dùng cung cấp từ project nhóm PTHTTM-RAG. Chỉ lưu code cần kế thừa; bản KG notebook đã bỏ output. Không chuyển API key, Git, môi trường hoặc dữ liệu/index/graph pháp luật. Không tìm thấy LICENSE tại root; không tự gán license cho cả repository. Phase 2 port logic sang notebook project01, giữ mapping/diff và ghi rõ chỉnh sửa Gemini/y khoa. Các đường dẫn original trong manifest là provenance, không là runtime dependency.\n',encoding='utf-8')
    print(json.dumps({'copied':manifest['copied_count'],'omitted':manifest['omitted_count'],'internal_imports_resolved':len(imports),'source_modified':False}))

if __name__=='__main__':main()
