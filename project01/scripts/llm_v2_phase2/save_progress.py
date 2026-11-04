"""Save an honest Phase2 checkpoint after provider failures; no API or freeze."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,sqlite3,sys,importlib.metadata
P=Path(__file__).resolve().parents[2];ROOT=P.parent;PH=P/'artifacts/llm_v2/phase2'


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    from project01_llm_v2.agents import AgenticRuntime
    from project01_llm_v2.kg import visualize_graph
    runtime=AgenticRuntime(P,False);assert runtime.readiness()['index_ready']
    visualize_graph(runtime.graph.neighborhood('Bệnh thận và tiểu đường'),P/'artifacts/llm_v2/kg/neighborhood_development_r3.html')
    with sqlite3.connect(P/'artifacts/llm_v2/runtime/calls.sqlite3') as db:
        rows=db.execute("SELECT id,kind,status,response FROM calls WHERE status!='historical'").fetchall()
    assert not any(r[2]=='claimed' for r in rows),'An API writer is still active; do not close checkpoint'
    counts=Counter((r[1],r[2]) for r in rows)
    errors=[{'call_id':identifier,'kind':kind,**json.loads(response or '{}')} for identifier,kind,status,response in rows if status!='complete']
    state_path=ROOT/'docs/final_project01/llm_v2/checkpoint.json';state=load(state_path)
    secret=next(line.partition('=')[2].strip().strip('\"\'') for line in (P/'.env').read_text().splitlines() if line.partition('=')[0].strip()=='GEMINI_API_KEY')
    scan_roots=[P/'notebooks',P/'web/backend/project01_llm_v2',P/'web/frontend/src',P/'docs/llm_v2',P/'artifacts/llm_v2',P/'scripts/llm_v2_phase2']
    scanned=0
    for directory in scan_roots:
        for path in directory.rglob('*'):
            if path.is_file() and path.suffix in {'.py','.json','.jsonl','.md','.jsx','.css','.txt','.ipynb','.html','.yaml'}:
                assert secret.encode() not in path.read_bytes(),path.name;scanned+=1
    units=sorted(PH.glob('unit_checks_*.json'),key=lambda p:p.stat().st_mtime)
    unit=load(units[-1]);assert unit['status']=='PASS'
    preservation=load(PH/'preservation_verification.json');assert preservation['status']=='PASS'
    exports=load(PH/'source_exports.json');assert len(exports['files'])==16
    clean=load(P/ load(PH/'clean_start_active.json')['receipt']);assert clean['status']=='PASS'
    assert not (PH/'freeze.json').exists()
    held_count=len(list((PH/'evaluation/results').glob('*.json')))
    assert held_count==0
    sourcefiles=[P/r['export'] for r in exports['files']]+list((P/'notebooks').glob('*.ipynb'))
    sourcefiles += list((P/'web/frontend/src').glob('*'))+[P/'web/backend/app.py',P/'docs/llm_v2/runtime_config.json',P/'environment/llm_v2/phase2/uv.lock']
    snapshot=P/'provenance/llm_v2_phase2_checkpoint_20261102';snapshot.mkdir(parents=True,exist_ok=True)
    source_records=[]
    for path in sourcefiles:
        if not path.is_file():continue
        destination=snapshot/path.relative_to(P);destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():assert sha(destination)==sha(path),'Checkpoint snapshot exists with different source; create new revision'
        else:destination.write_bytes(path.read_bytes())
        source_records.append({'path':path.relative_to(P).as_posix(),'archived_path':destination.relative_to(P).as_posix(),'sha256':sha(path)})
    save(PH/'source_checkpoint_20261102.json',{'status':'IN_PROGRESS_NOT_EVALUATION_FREEZE','files':source_records})
    stats={'status':'IN_PROGRESS','execution_state':'WAITING_PROVIDER','date':datetime.now(timezone.utc).isoformat(),
      'new_sdk_attempts':len(rows),'by_kind_and_status':[{'kind':k,'status':s,'count':n} for (k,s),n in sorted(counts.items())],
      'errors':errors,'source_modules':16,'notebooks':3,'old_pins_resolved':preservation['pins'],
      'index_chunks':316,'kg_assertions':35,'unit_checks':unit['check_count'],'unit_receipt':units[-1].relative_to(P).as_posix(),
      'layout_checks':6,'saved_result_ui_checks':8,'source_only_clean_start':'PASS',
      'full_live_RAG_answer':'NOT_COMPLETE','verifier_live_acceptance':'NOT_RUN','full_development_pairs_complete':0,
      'held_out_outputs':held_count,'evaluation_frozen':False,'secret_scanned_files':scanned,
      'paid_budget_usd':0,'billing_invoice_verified':False,'scientific_training_or_TEST_forward':0,
      'SDK_count_is_not_independently_verified_wire_HTTP_count':True,'local_workers_remaining':False,
      'installed_packages':len(list(importlib.metadata.distributions())),'python':sys.version.split()[0]}
    save(PH/'progress_20261102.json',stats)
    state.update(active_phase=2,next_phase=2,status='IN_PROGRESS',active_processes=[],
      current_step='Phase2 IN_PROGRESS / WAITING_PROVIDER: source/index/UI/isolated serving environment ready; real generation hit timeouts and HTTP503. No full RAG answer or held-out output; no freeze. All local workers stopped. Resume this phase only.',
      api_calls_this_plan=5+len(rows))
    state['phases']['2']['status']='IN_PROGRESS'
    state['phase2_progress']={k:v for k,v in stats.items() if k!='errors'}
    state['phase2_progress']['report']='docs/final_project01/llm_v2/phase2_report.md'
    state['phase2_progress']['source_checkpoint']='project01/artifacts/llm_v2/phase2/source_checkpoint_20261102.json'
    state['phase2_progress']['provider_errors']=errors
    state['phase2_progress']['generation_rerank_floor']=0.5
    state['phase2_progress']['timeout_seconds']=180
    state['phase2_progress']['deadline_seconds']=1500
    state['phase2_progress']['resume_steps']=[
       'Read plan/checkpoint/report and preserve all unknown claims; verify provider availability and remaining free quota with one bounded new recovery probe',
       'When provider is healthy, declare a new development claim revision (e.g. development-r4) in runner; keep old results/errors; do not reset SQLite or retry unknown claims under old IDs',
       'Complete the two declared development cases and inspect answers/claim support/direction and graph-to-source trace; fresh live UI/API acceptance still pending',
       'Only after development/pretest PASS: freeze current source/prompts/model/corpus/index/KG/evaluator, run40x2 once over multiple days, review/plot saved results',
       'Do not begin Phase3 or delete reference folder until Phase2 acceptance complete']
    state['api_usage_summary']['phase2_sdk_attempts']=len(rows)
    state['api_usage_summary']['count_unit_note']='api_calls_this_plan = Phase1 HTTP attempts5 + Phase2 logical SDK attempts; exact wire HTTP total not separately instrumented'
    state['evaluation'].update(status='NOT_OPENED_DEVELOPMENT_PROVIDER_FAILURE',model_outputs=0)
    state['reference_cleanup']['phase2_independence_check']='SOURCE_ONLY_API_RISK_KG_AND_REACT_BUILD_PASS; FRESH_LIVE_LLM_PENDING'
    state['pending_configuration']['key_probe_status']='PHASE1_PASS; PHASE2_PROVIDER_TIMEOUT_HTTP503'
    state['last_updated']=datetime.now(timezone.utc).isoformat()
    save(state_path,state)
    error_rows='\n'.join(f"- `{e['call_id']}`: {e.get('error_type')} / HTTP{e.get('http_status')}." for e in errors)
    report=f'''# Phase2 v2 — IN_PROGRESS / WAITING_PROVIDER

Ngày02/11/2026. **Chưa hoàn tất Phase2.** Code/index/UI đã triển khai; Gemini trả timeout/HTTP503 nên chưa có một câu trả lời RAG hoàn chỉnh. Không mở held-out hoặc freeze để lấy điểm khi development chưa đạt. Đã dừng mọi worker/server local của lượt này, không có queue chạy nền.

## Phần đã làm và kiểm

- Bảo toàn33 file notebook/web/README/runner cũ trước sửa;502 pin lịch sử resolve đúng archive,120 output P0/P1/P2 giữ nguyên;167 file handoffPhase1 khớp hash. Không train/TEST/evaluation cũ.
- Port core nhóm vào đúng3 notebook, export một chiều16 module `project01_llm_v2`. Bản đồ actual_reuse.json có45 symbol khớp AST và30 symbol được adapter; namespace và import mới không cần folder tham khảo/provenance. Cả7 helper inference CDC và predict giữ logic gốc, không load pickle retrieval cũ.
- Env serving WSL Python3.11.17 riêng,91 entry trong lock/88 package cài tương thích; kernel **Project01 Gemini serving (WSL3.11)**. Hai env GPU giữ nguyên. Notebook/plot tách dependency-group khỏi requirementsRender.
- Index mới đủ316 chunk, embedding-001/768 chiều/L2, cache/metadata/hash; KG35 assertion có nguồn và graph candidate đi vào RRF. Group cache/normalize/aggregate/PyVis đã port; seed curated đủ dùng nên chưa gọi extractor tự động. HTML graph hiện hành: `project01/artifacts/llm_v2/kg/neighborhood_development_r3.html`.
- Queue chung, durable call IDs/cache, lưu claim trước gửi, không tự replay unknown, cap18 generation/day, không paid fallback. Tắt SDK continuation/retry ẩn trong code hiện hành; ghi riêng SDK attempts và cache. API health không gọi LLM, `/ready` chỉ data/config và trạng thái call gần nhất.
- {unit['check_count']} kiểm tra chức năng PASS, API thật trong kiểm tra=0: RRF/KG/quote/vector, thiếuBMI, chặn citation/số bịa, schema/CORS, guard503/unknown/quota. Mock chỉ dùng tái hiện lỗi, không là nghiệm thu câu trả lời LLM.
-3 notebook chạy source với API/train/TEST/evaluation tắt, có output thật/đọc saved output;16 module source-export parity PASS.
- React build PASS; desktop/mobile layout6 check và saved partial-output8 check PASS, không mock. Hai thẻ câu trả lời đứng cạnh nhau, markdown được render dưới dạng text an toàn; nguồn/trace nằm dưới. Saved development giữ trạng thái lỗi và nhãn saved, không giả thành live/complete.
- Copy độc lập chỉ có project01: index/KG/Risk/Flask/WSGI PASS, network bị chặn, không key/provenance/folder tham khảo. React build trong copy PASS. Đây là **source-only proof**, chưa chứng minh fresh live RAG end-to-end.
- Đã chuẩn bị README/local/GitBash/kernel và blueprint2service Render CPU; chưa commit/push/deploy. Package/freeze phát hành cuối còn chờ live acceptance.

## API thật đã chạy

Phase2 có **{len(rows)} logical SDK attempt** (chi tiết theo kind/status ở progress_20261102.json). Đây không là lời khẳng định đã đo riêng mọi wire HTTP request. Embedding index và query chạy thành công. Generation đã có câu direct thật, query plan JSON thật và rerank JSON thật; Reporter còn lỗi, Verifier live chưa được nghiệm thu. **0/2 cặp development hoàn chỉnh;0/80 held-out output.**

Các lỗi giữ nguyên:
{error_rows}

Unknown sau timeout có thể đã xử lý ở provider; usage chưa biết, không điền0tokens. HTTP503 là lỗi provider được quan sát, không tự quy là hết quota hoặc thiếu key. Ngân sách trả phí0USD, không bật billing/đổi model/đổi key; chưa kiểm hóa đơn.

Developmentr2 tăng timeout90→180s, deadline1500s và giữ claim lỗi cũ; rerank:r2 đã trả JSON. R3 quan sát đúng câu đảo chiều: tất cả candidate chỉ0,1–0,4; đặt evidence gate≥0,5 trước held-out và Reporter80–120từ/tối đa3claim. Điểm này không là xác suất relevance đã hiệu chuẩn. Reporter ngắn hơn vẫn nhận503. Không coi threshold/guard code là chứng minh câu trả lời cuối đã đúng. Chưa kết luận nhánh nào thắng; direct development chưa được thẩm định lâm sàng.

## Tiếp tục đúng bước

Gõ **làm tiếp task đang dở** để tiếp Phase2. Đọc plan/checkpoint/report này, kiểm lại khả năng đáp ứng Gemini và quota free bằng một probe mới có giới hạn. Không tự gửi lại các claim unknown cũ hoặc xóa ledger. Khi API ổn, ghi revision development mới, dùng runner `--claim-revision development-r4` (chưa chạy) cho hai câu đã khai báo; giữ phiên cũ làm lịch sử. Code câu trả lời/prompt còn được sửa ở notebook trước freeze, cần lưu revision tương ứng.

Sau khi hai cặp development và fresh live API/UI đạt, khóa corpus/index/KG/model/prompt/code/evaluator/rubric rồi mới chạy40×2 theo journal nhiều ngày. Review ẩn nhánh và3 biểu đồ đã có code trong notebook03 nhưng **chưa sinh chart chất lượng vì chưa có80 output/review**. Không mở Phase3/DOCX hoặc xóa `RAG_KG_Tham_khao/` trong trạng thái này.

Checkpoint: `docs/final_project01/llm_v2/checkpoint.json`. Chi tiếtAPI: `project01/artifacts/llm_v2/phase2/api_calls/`. Source snapshot bảo toàn: `project01/provenance/llm_v2_phase2_checkpoint_20261102/`. Cách chạylocal: `project01/docs/llm_v2/RUN_LOCAL.md`. Secret scan{scanned} file PASS; key vẫn chỉ ở ignored.env.
'''
    (ROOT/'docs/final_project01/llm_v2/phase2_report.md').write_text(report,encoding='utf-8')
    print(json.dumps({k:v for k,v in stats.items() if k!='errors'},ensure_ascii=False))


if __name__=='__main__':
    sys.path.insert(0,str(P/'web/backend'));main()
