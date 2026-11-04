"""Prepare an isolated Chapter6 revision; never calls models or changes baseline."""
from pathlib import Path
from copy import deepcopy
import ast
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / 'tieuluanfinal'
P = ROOT / 'project01'
AGENT = FINAL / 'web/agent'
JOB = '56d62ac4-77f4-4cf8-a2e7-f01584c2e240'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def md(text):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': text.splitlines(keepends=True)}


def code(text):
    return {'cell_type': 'code', 'metadata': {}, 'source': text.splitlines(keepends=True), 'outputs': [], 'execution_count': None}


def prepare():
    assert (FINAL / 'docs/final_revision/baseline_copy.json').exists(), 'Wait for baseline copy'
    assert not AGENT.exists(), 'Refuse to overwrite prepared revision'
    provenance = FINAL / 'provenance/before_final_ch06'
    provenance.mkdir(parents=True, exist_ok=True)
    for path in ['notebooks/04_Multi_Agent.ipynb', 'project.json', 'README.md', 'AGENTS.md',
                 'web/frontend/src/v3/App.tsx', 'web/frontend/src/v3/catalog.ts']:
        src = FINAL / path
        target = provenance / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    # Self-contained serving package. Environments, secrets and mutable API ledgers
    # are deliberately shared at launch, not duplicated or reset.
    transfers = []
    for relative in ['datasets/llm_v2', 'docs/llm_v2', 'config', 'web/backend',
                     'web/frontend', 'artifacts/llm_v2/index', 'artifacts/llm_v2/kg',
                     'artifacts/llm_v2/phase1', 'provenance/group_rag_kg_source']:
        source = P / relative
        if not source.exists():
            continue
        for src in source.rglob('*'):
            if not src.is_file() or {'node_modules','__pycache__','.runtime','.venv'}.intersection(src.relative_to(P).parts) or src.name.startswith('.env'):
                continue
            target = AGENT / src.relative_to(P)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            digest = hashlib.sha256(src.read_bytes()).hexdigest()
            assert digest == hashlib.sha256(target.read_bytes()).hexdigest()
            transfers.append({'source': src.relative_to(ROOT).as_posix(), 'target': target.relative_to(FINAL).as_posix(), 'sha256': digest})
    for relative in ['environment/llm_v2/pyproject.toml', 'environment/llm_v2/uv.lock']:
        target = AGENT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(P / relative, target)
    evidence = FINAL / 'artifacts/final_ch06'
    evidence.mkdir(parents=True, exist_ok=True)
    shutil.copy2(P / f'artifacts/llm_v2/jobs/{JOB}.json', evidence / 'live_job_r11.json')
    save(FINAL / 'datasets/ch06_llm/catalog.json', {
        'corpus': '../../web/agent/datasets/llm_v2',
        'kg': '../../web/agent/artifacts/llm_v2/kg/seed_r2.json',
        'demo_output': '../../artifacts/final_ch06/live_job_r11.json',
        'note': 'Current question-only demo does not use CDC profiles or RiskAgent.'})
    notebooks = [load(P / 'notebooks' / name) for name in
                 ['01_Data_KB_RAG.ipynb','02_Diabetes_Multi_Agent.ipynb','03_Evaluation.ipynb']]
    boot = ''.join(notebooks[0]['cells'][1]['source'])
    boot = boot.replace("PROJECT=next(p for p in (Path.cwd(),*Path.cwd().parents) if (p/'docs/llm_v2/provider_config.example.json').exists())",
                        "REPOSITORY=next(p for p in (Path.cwd(),*Path.cwd().parents) if (p/'ASSIGN_REORGANIZATION_EXECUTION_PLAN.md').exists())\nFINAL=REPOSITORY/'tieuluanfinal'\nPROJECT=FINAL/'web/agent'")
    cells = [md('# Chương 6 Hệ đa tác tử và RAG cho kiến thức tiểu đường\n\n'
                'Bốn vai trò Coordinator → Knowledge → Reporter → Verifier. Code đầy đủ của pipeline nằm trong cell; '
                'backend là bản export một chiều. Không Risk Agent, không hồ sơ CDC. '
                'Run All chỉ nạp code và phân tích lượt Gemini đã lưu, không gọi API/train/TEST. '
                'Lượt minh họa thật: 03/11/2026, four-agent-r11, gemini-3-flash-preview. '
                'Đây là một ví dụ development, không phải benchmark chất lượng. '
                'Các module risk/analysis được giữ để tương thích source lịch sử, không tham gia đường hỏi đáp.'), code(boot)]
    for notebook in notebooks:
        for cell in notebook['cells'][2:]:
            source = ''.join(cell.get('source',[]))
            if cell['cell_type'] == 'code' and source.startswith('%%llm_v2_module '):
                if not source.split('\n',1)[-1].strip():continue
                revised = deepcopy(cell)
                revised['outputs'] = []; revised['execution_count'] = None
                if source.startswith('%%llm_v2_module project01_llm_v2.provider\n') and "self.folder=self.root/'artifacts/llm_v2/runtime'" in source:
                    source = source.replace("self.folder=self.root/'artifacts/llm_v2/runtime'", "self.folder=Path(os.environ.get('GEMINI_STATE_ROOT',str(self.root/'artifacts/llm_v2/runtime')))")
                    revised['source'] = source.splitlines(keepends=True)
                cells.append(revised)
            elif cell['cell_type'] == 'markdown' and not source.startswith('## Đọc') and not source.startswith('## Kết quả'):
                # Keep algorithm headings only; old live outputs are not relabelled.
                if source.startswith(('## ', '### ')) and not source.startswith('## Dữ liệu'):
                    cells.append(deepcopy(cell))
    cells += [md('## KQ1 Dữ liệu và phạm vi đồ thị\n\nĐếm từ corpus/KG thực; không gọi API. Mini-KG chỉ hỗ trợ một phần của kho tri thức.'), code('''from project01_llm_v2.embedding import load_corpus
from project01_llm_v2.kg import MiniKG
from IPython.display import display, Markdown, SVG
import json, hashlib
chunks = load_corpus(PROJECT)
kg = MiniKG(PROJECT, chunks)
stats = json.loads((PROJECT/'datasets/llm_v2/corpus_stats.json').read_text(encoding='utf-8'))
display({'chunks':len(chunks),'concepts':len(kg.entities),'source_checked_assertions':len(kg.assertions),'stats':stats,'new_API_calls':0})
display(kg.neighborhood('Bệnh thận và tiểu đường')['relationships'][:2])
'''), md('## KQ2 Câu hỏi và các bước đã chạy thật\n\nNạp nguyên trạng journal đã lưu. Bảng cho biết input/output chuyển giữa các bước, không phải chuỗi suy nghĩ nội tại của mô hình.'), code('''job_path = FINAL/'artifacts/final_ch06/live_job_r11.json'
job = json.loads(job_path.read_text(encoding='utf-8'))
assert job['runtime_revision']=='four-agent-r11' and job['status']=='complete'
traces = job['pipeline_traces']['agentic_rag']
display({'job_id':job['id'],'question':job['question'],'revision':job['runtime_revision'],'sha256':hashlib.sha256(job_path.read_bytes()).hexdigest()})
for stage in traces:
    output = stage['output']
    summary = {'stage':stage['id'],'owner':stage['owner'],'duration_ms':round(stage['duration_ms'],3),'calls':stage['calls']}
    for key in ['queries','candidate_count','kg_candidate_count','evidence_count','selected_chunk_ids','provider','status']:
        if key in output:summary[key]=output[key]
    display(summary)
'''), md('## KQ3 Thứ hạng và nguồn sau rerank\n\n20 ứng viên được chấm local, giữ 6 đoạn. Điểm là tín hiệu xếp hạng, không phải xác suất đúng. Hạng trước/sau có thể giống nhau; không suy rằng rerank luôn cải thiện.'), code('''rerank = next(s['output'] for s in traces if s['id']=='rerank')
display({'weights':rerank['weights'],'input':rerank['candidate_count'],'selected':rerank['evidence_count'],'API_calls':rerank['api_calls']})
for row in rerank['ranking'][:6]:display(row)
rag = job['results']['agentic_rag']
for i, row in enumerate(rag['evidence'],1):
    display({'source_number':i,'chunk_id':row['chunk_id'],'title':row['metadata']['title'],'source_url':row['metadata']['source'],'snapshot_url':row['metadata']['source_refs'][0]['snapshot_url']})
'''), md('## KQ4 Hai câu trả lời và Verifier\n\nOutput dưới đây được đọc nguyên văn từ lượt thật. Cần giữ điều kiện nhóm nguy cơ cao và can thiệp kết hợp; không đổi thành cam kết giảm nguy cơ cá nhân chỉ nhờ đi bộ.'), code('''for variant in ['llm_direct','agentic_rag']:
    row = job['results'][variant]
    display(Markdown('### '+variant+'\\n\\n'+row['answer_vi']))
    display({'latency_ms':row['latency_ms'],'citation_count':len(row['citations']),'status':row['status']})
display(rag['verification'])
display(Markdown('**Nhận xét:** Hai nhánh đều nhắc điều kiện kết hợp vận động, ăn uống và giảm cân. Pipeline truy được bằng chứng; baseline cũng có kiến thức liên quan. Câu mở đầu “Có ... giúp bạn” của pipeline vẫn dễ bị hiểu thành bảo đảm cá nhân, dù câu cuối đã nêu điều kiện. Verifier cùng model không loại bỏ hết lỗi diễn đạt. Một lượt minh họa chưa đủ kết luận bên nào chính xác hơn.'))
'''), md('## KQ5 Chi phí và thời gian của lượt minh họa\n\nCộng toàn bộ call của từng nhánh. Query embedding là quota riêng; cache không được tính thành call live mới. Thời gian chỉ của một lần chạy, không phải trung bình.'), code('''metrics=[]
for variant, row in job['results'].items():
    generation=[u for u in row.get('usage',[]) if u.get('kind')=='generation']
    embedding=[u for u in row.get('usage',[]) if u.get('kind')=='embedding']
    value={'variant':variant,'seconds':round(row['latency_ms']/1000,3),'generation_live':sum(u.get('sdk_calls',0) for u in generation if u.get('cache_status')=='live'),'generation_tokens':sum((u.get('usage') or {}).get('total_tokens',0) or 0 for u in generation),'embedding_live':sum(u.get('sdk_calls',0) for u in embedding if u.get('cache_status')=='live'),'embedding_cache':sum(u.get('cache_status')=='local_cache' for u in embedding),'citations':len(row['citations'])}
    metrics.append(value);display(value)
summary={'question':job['question'],'job_id':job['id'],'model':rag['model'],'revision':job['runtime_revision'],'metrics':metrics,'rerank_top6':rerank['ranking'][:6],'stages':[{'id':s['id'],'duration_ms':s['duration_ms'],'calls':s['calls']} for s in traces],'corpus_stats':stats,'new_API_calls':0,'new_training_steps':0,'new_TEST_forward':0}
out=FINAL/'artifacts/final_ch06/notebook_analysis.json'
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')
'''), md('## KQ6 Biểu đồ thời gian từng bước\n\nTrục ngang: giây; mỗi thanh là một stage của cùng lượt RAG. Reporter và Verifier chiếm phần lớn thời gian. Biểu đồ không gồm nhánh direct và không phải trung bình nhiều lần.'), code('''from html import escape
labels={'pre_retrieval':'Coordinator','retrieval':'Truy hồi','rerank':'Rerank local','reporter':'Reporter','verifier':'Verifier','release':'Phát hành'}
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="420" viewBox="0 0 1100 420"><rect width="1100" height="420" fill="white"/><g font-family="DejaVu Sans,Arial" font-size="22" fill="black"><text x="200" y="32">Thời gian từng bước của một lượt RAG (giây)</text>']
for index, stage in enumerate(traces):
    seconds=stage['duration_ms']/1000; y=65+index*48
    svg.append(f'<text x="10" y="{y+23}">{escape(labels[stage["id"]])}</text><rect x="215" y="{y}" width="{seconds*160:.2f}" height="29" fill="#555"/><text x="{225+seconds*160:.2f}" y="{y+23}">{seconds:.3f}</text>')
for x in range(6):svg.append(f'<text x="{210+x*160}" y="389">{x}</text>')
svg.append('<text x="1030" y="389">giây</text></g></svg>')
svg=''.join(svg); display(SVG(svg))
(FINAL/'artifacts/final_ch06/stage_latency.svg').write_text(svg,encoding='utf-8')
''')]
    for i,cell in enumerate(cells):
        cell['id'] = f'final-ch06-{i:04d}'
    notebook = {'nbformat':4,'nbformat_minor':5,'metadata':{
        'kernelspec':{'name':'project01-gemini-serving','display_name':'Project01 Gemini serving (WSL3.11)','language':'python'},
        'source_authority':'inline cells','revision':'final-ch06-r1'},'cells':cells}
    save(FINAL/'notebooks/04_Multi_Agent.ipynb', notebook)
    export_sources(notebook)
    # Ch1-5 algorithm cells remain byte-identical; only bootstrap selects the copy.
    config=load(FINAL/'project.json');config['project']='tieuluanfinal'
    for entry in config['notebooks'][:3]:
        path=FINAL/entry['path'];nb=load(path)
        source=''.join(nb['cells'][1]['source']).replace("PROJECT_NAME = 'tieuluan3'", "PROJECT_NAME = 'tieuluanfinal'")
        source=source.replace('from assignment_runtime import activate', 'import assignment_runtime as _final_runtime\nif PROJECT_NAME not in _final_runtime.PROJECTS:\n    _final_runtime.PROJECTS = (*_final_runtime.PROJECTS, PROJECT_NAME)\nfrom assignment_runtime import activate')
        nb['cells'][1]['source']=source.splitlines(keepends=True);save(path,nb)
        entry['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    config['notebooks'][3].update(sha256=hashlib.sha256((FINAL/'notebooks/04_Multi_Agent.ipynb').read_bytes()).hexdigest(), role='Full inline four-agent RAG/Gemini code and saved live output analysis', framework='gemini-serving')
    config['final_chapter6_revision']='four-agent-r11';save(FINAL/'project.json',config)
    catalog_path=FINAL/'datasets/catalog.json'
    original_catalog=catalog_path.read_text(encoding='utf-8')
    revised_catalog=original_catalog.replace('tieuluan3/','tieuluanfinal/')
    if revised_catalog!=original_catalog:
        (provenance/'datasets').mkdir(parents=True,exist_ok=True)
        (provenance/'datasets/catalog.json').write_text(original_catalog,encoding='utf-8')
        catalog_path.write_text(revised_catalog,encoding='utf-8')
    save(FINAL/'web/deploy/final_ch06_release_r1.json',{
        'revision':'final-ch06-r1','chapter6_source':'../agent/web/backend/project01_llm_v2',
        'chapter6_notebook':'../../notebooks/04_Multi_Agent.ipynb',
        'scientific_baseline_archive':'api-bundle-r1.zip',
        'scientific_baseline_archive_sha256':hashlib.sha256((FINAL/'web/deploy/api-bundle-r1.zip').read_bytes()).hexdigest(),
        'baseline_archive_scope':'Ch1–5 only; old agent API is not exposed by final gateway',
        'new_API_calls':0,'training_steps':0,'scientific_TEST_forward':0})
    # Replace only the Chapter6 rendered branch. Other chapter components untouched.
    app=FINAL/'web/frontend/src/v3/App.tsx'
    text=app.read_text(encoding='utf-8')
    text=text.replace('if (selection.error) return null;', 'if (selection.error || selection.chapter === 6) return null;')
    text=text.replace('<section className="v3-hero">', '{chapter.chapter === 6 ? <iframe title="Chương 6 · Hệ bốn agent và RAG" src="/multi-agent/" style={{width:"100%",height:"calc(100vh - 210px)",minHeight:720,border:0,display:"block"}} /> : <>\n        <section className="v3-hero">')
    text=text.replace('      </main>', '        </>}\n      </main>')
    app.write_text(text,encoding='utf-8')
    catalog=FINAL/'web/frontend/src/v3/catalog.ts'
    text=catalog.read_text(encoding='utf-8').replace('Chia công việc thành định tuyến, chuyên gia, kiểm chứng và báo cáo. So A0 trực tiếp, A1 thêm router và A2 thêm verifier/reporter trên cùng yêu cầu ID-bound.', 'Coordinator → Knowledge → Reporter → Verifier. So sánh Gemini trực tiếp với cùng Gemini có RAG và KG cho câu hỏi tiểu đường.')
    catalog.write_text(text,encoding='utf-8')
    save(FINAL/'docs/final_revision/project01_transfer.json', {'files':transfers,'source_notebooks':[str(p) for p in (P/'notebooks').glob('*.ipynb')], 'shared_runtime_only':'Existing WSL env; provider ledger shared by launcher via GEMINI_STATE_ROOT; key inherited in process only','new_API_calls':0})
    main=AGENT/'web/frontend/src/main.jsx'
    value=main.read_text(encoding='utf-8')
    value=value.replace("const data=await response.json();", "const data=await response.json();")
    value=value.replace('fetch(API+path,', "fetch(API+(['/'+ 'ready','/'+'health'].includes(path)?'/multi-agent'+path:path),")
    main.write_text(value,encoding='utf-8')
    scripts=FINAL/'scripts'
    (scripts/'run_web.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "$(uname -s)" == Linux* ]]; then
  exec "$TASK_ROOT/project01/environment/llm_v2/.venv/bin/python" -B "$TASK_ROOT/scripts/run_tieuluanfinal.py" --port "${1:-8040}" --live
fi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$TASK_ROOT/tieuluanfinal/scripts/run_web.ps1")" -Port "${1:-8040}"
''',encoding='utf-8')
    (scripts/'run_web.ps1').write_text('''[CmdletBinding()]
param([int]$Port=8040)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$linux=(& wsl.exe -d Ubuntu --exec wslpath -a $repo.Replace('\\','/')).Trim()
if($LASTEXITCODE -ne 0){throw 'Cannot resolve workspace in WSL Ubuntu'}
& wsl.exe -d Ubuntu --exec "$linux/project01/environment/llm_v2/.venv/bin/python" -B "$linux/scripts/run_tieuluanfinal.py" --port $Port --live
''',encoding='utf-8')
    (FINAL/'AGENTS.md').write_text('''# Tiểu luận final

Revision riêng theo yêu cầu ngày03/11/2026: copy tieuluan3, chỉ thay Chương6 bằng project01 four-agent-r11.
Không sửa ngược tieuluan3/project01 hoặc chạy train/TEST/evaluation/API để dựng báo cáo.
Ch1–5 giữ code khoa học; notebook chỉ đổi PROJECT_NAME để chọn bản sao.
Notebook04 chứa source đầy đủ, backend export bằng scripts/prepare_tieuluanfinal.py --export ở root.
Tối đa4notebook, bản cũ giữ trong provenance/before_final_ch06.
Web tích hợp chạy Git Bash: bash tieuluanfinal/scripts/run_web.sh; port8040.
Ch6 Gemini dùng env serving đã khóa, Ch1–5 dùng envTorch hiện có, không cài trộn dependency.
Sổ quota chia sẻ bằng GEMINI_STATE_ROOT, key chỉ kế thừa trong process; không copy.env.
DOCX bản gốc ngoài workspace chỉ đọc, giữ mọi phần ngoàiCh6 và navigation liên quan.
Không commit/push/deploy. Bằng chứng ở docs/final_revision và artifacts/final_ch06.
''',encoding='utf-8')
    (FINAL/'README.md').write_text('''# Tiểu luận final

Bản sao của tieuluan3. Chương1–5 và các scientific artifact cũ được giữ; Chương6 thay bằng hệ4agent Coordinator → Knowledge → Reporter → Verifier của project01 (four-agent-r11). Không Risk/hồ sơ.

## Chạy demo trong Git Bash

```bash
cd /c/DATA/assign
bash tieuluanfinal/scripts/run_web.sh
```

Mở http://127.0.0.1:8040, tab Multi-Agent tại /agents. Cần các port8040–8042 trống; Ctrl+C dừng đúng các worker launcher tạo. Nếu đổi port, ví dụ `bash tieuluanfinal/scripts/run_web.sh 8050`, hai port kế tiếp cũng phải trống.

Ch1–5 dùng serving bundle gốc đã pin trong bản sao, không train/TEST. Ch6 sử dụng source/config/corpus/index/KG đóng gói tại web/agent; không chạy implementation từ project01 hay folder tham khảo. Ch6 dùng lại môi trường WSL project01/environment/llm_v2/.venv và sổ quota project01/artifacts/llm_v2/runtime để không vô tình reset ngân sách. Key có thể đặt trong biến môi trường hoặc tieuluanfinal/.env; nếu chưa có, launcher đọc key hiện có ở project01/.env vào process mà không sao chép hay in giá trị.

Một cặp cần4generation request, query embedding dùng quota riêng. Mở trang/KG/health không gọi model. Không tự chạy thêm câu để tìm kết quả thắng.

## Notebook

- 01_ML_CNN.ipynb: code và kết quả Ch2–3 như tiểu luận3; hai kernel Torch/Keras đã có.
- 02_RNN_LSTM.ipynb: Ch4, hai kernel hiện có.
- 03_Knowledge_RAG.ipynb: Ch5 như tiểu luận3.
- 04_Multi_Agent.ipynb: full source Ch6 mới và các output KQ1–KQ6. Kernel WSL `/mnt/c/DATA/assign/project01/environment/llm_v2/.venv/bin/python`; Run All không gọi API/train/TEST.

Output Ch6 đọc từ lượt thật ngày03/11: artifacts/final_ch06/live_job_r11.json. Một lượt development, không phải benchmark held-out và không chứng minh pipeline luôn thắng.

## Báo cáo

File cuối: report/final/Tieu_Luan_AI_Final.docx, dựa trực tiếp trên DOCX người dùng gửi; chỉ đổiCh6 và các mục navigation củaCh6. Bản nguồn/bìa/Ch1–5/kết luận giữ nguyên. Bản notebookCh6 trước sửa ở provenance/before_final_ch06.

Build bằng toolchain Node22 đã có: từ root chạy `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tieuluanfinal/scripts/build_final_web.ps1`.

Bản local này chưa deploy cloud; root render.yaml vẫn trỏ bản tiểu luận3 hiện có. Không coi archiveCh6 cũ là pipelineGemini mới. Không copy venv/node_modules/secret; danh sách copy/hash trong docs/final_revision.
''',encoding='utf-8')
    (scripts/'build_final_web.ps1').write_text('''$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$node=Join-Path $repo '.local/node-v22.23.4-win-x64/node.exe'
$vite=Join-Path $repo 'node_modules/vite/bin/vite.js'
& $node $vite build "$repo/tieuluanfinal/web/frontend" --config "$repo/tieuluanfinal/web/frontend/vite.config.ts"
if($LASTEXITCODE -ne 0){throw 'Paper frontend build failed'}
& $node $vite build "$repo/tieuluanfinal/web/agent/web/frontend" --config "$repo/tieuluanfinal/web/agent/web/frontend/vite.config.js" --base /multi-agent/
if($LASTEXITCODE -ne 0){throw 'Agent frontend build failed'}
''',encoding='utf-8')
    print(json.dumps({'prepared':True,'transferred_files':len(transfers),'notebooks':len(list((FINAL/'notebooks').glob('*.ipynb'))),'algorithm_modules':16}))


def export_sources(nb=None):
    nb=nb or load(FINAL/'notebooks/04_Multi_Agent.ipynb')
    modules={}
    for cell in nb['cells']:
        source=''.join(cell['source'])
        if source.startswith('%%llm_v2_module '):
            head,body=source.split('\n',1);name=head.split()[-1].split('.')[-1]
            modules.setdefault(name,[]).append(body)
    rows=[]
    for name,bodies in modules.items():
        body=''.join(bodies);ast.parse(body)
        path=AGENT/'web/backend/project01_llm_v2'/f'{name}.py'
        text='# GENERATED from tieuluanfinal/notebooks/04_Multi_Agent.ipynb\n'+body
        path.write_text(text,encoding='utf-8')
        rows.append({'module':name,'sha256':hashlib.sha256(text.encode()).hexdigest()})
    save(FINAL/'docs/final_revision/ch06_exports.json', {'modules':rows,'source_authority':'notebook cells'})


if __name__=='__main__':
    import sys
    export_sources() if '--export' in sys.argv else prepare()
