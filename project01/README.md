# Chạy project01 RAG + Gemini v2

**Phase2 đang thực hiện.** Code/index/UI đã chuẩn bị; development đang gặp Gemini timeout/HTTP503. Chưa freeze hoặc chạy held-out, chưa có chất lượng RAG+LLM được nghiệm thu. Xem `../docs/final_project01/llm_v2/phase2_report.md` và checkpoint để tiếp tục đúng bước.

Từ root `C:\DATA\assign`, sau khi semantic index được chuẩn bị đủ316 chunk:

```powershell
./project01/scripts/build_web.ps1
./project01/scripts/run_web.ps1
```

Mở **http://127.0.0.1:8031**. Git Bash dùng `bash project01/scripts/run_web.sh`; không chạy `.ps1` bằng Bash. Trong WSL dùng `bash project01/scripts/run_web.sh` hoặc gọi Python serving trực tiếp. Ctrl+C để dừng.

Key chỉ ở `project01/.env` (`GEMINI_API_KEY`), đã Git ignore; không nhập ở frontend. UI mặc định hỏi kiến thức, chạy LLM trực tiếp và hệ đa agent + RAG. Chờ câu trả lời rồi mở nguồn/KG/Verifier. Hồ sơ CDC là công cụ bổ sung, nút tính score không cần API; thiếu BMI/field khác sẽ bị từ chối, không tự điền.

**Quota user xác nhận:** Gemini3.8Flash5RPM/250kTPM/20RPD; app cap4RPM/18RPD. Một cặp thường cần5 call, có thể thêm sửa/kiểm chứng. Hết quota: job giữ câu/bước đã xong, bấm tiếp tục sau reset ngày provider America/Los_Angeles. Không đổi model/key để lách quota. Cache gắn nhãn riêng; xem development đã lưu không phải câu trả lời live mới. Ledger local không biết mọi call ngoài app; kiểm AI Studio trước phiên mới.

## Notebook và kernel

Chọn **Project01 Gemini serving (WSL3.11)**, interpreter:
`/mnt/c/DATA/assign/project01/environment/llm_v2/.venv/bin/python`.

01 chứa schema, queue/API SDK, inference CDC giữ nguyên, chunk/index/BM25/vector/query/RRF/rerank/KG. 02 chứa prompt/generator/group pipeline và năm vai trò/Verifier/Flask. 03 chứa claim journal/evaluator/review/summary. Full implementation có trong cell `%%llm_v2_module`; backend là export một chiều, không là nguồn chỉnh thuật toán. Import giữa notebook dùng export của các cell tương ứng. Mặc định API/evaluation/training/TEST đều tắt.

Sau sửa cell ở development:

```bash
project01/environment/llm_v2/.venv/bin/python -B project01/scripts/llm_v2_phase2/notebooks.py export
project01/environment/llm_v2/.venv/bin/python -B project01/scripts/llm_v2_phase2/notebooks.py check
```

Sau freeze không sửa trực tiếp input đã khóa. Hai env/kernel GPU cũ giữ nguyên.

## Runner và tiếp tục

Trong WSL từ root repository:

```bash
PY=project01/environment/llm_v2/.venv/bin/python
$PY -B project01/scripts/llm_v2_phase2/run.py inspect
$PY -B project01/scripts/llm_v2_phase2/run.py index
$PY -B project01/scripts/llm_v2_phase2/run.py development
```

Index và development dùng API free, có cache; không chạy đồng thời nhiều runner. `index` đã đủ thì chỉ báo ALREADY_COMPLETE. Development subset được khai báo trước trong selection.json, không tự đọc held-out. Evaluation chỉ chạy sau `freeze.json` hợp lệ;80 output phải đủ và review xong mới nghiệm thu Phase2. Tiếp tục bằng lệnh chat **“làm tiếp phase2”** hoặc **“làm tiếp task đang dở”** theo checkpoint, không chạy producer lịch sử/TEST cũ.

## Render — cấu hình chuẩn bị, chưa deploy

`web/deploy/render_llm_v2.yaml` mô tả hai service cùng repository. API root directory để trống, build bằng `project01/web/backend/requirements_llm_v2.txt`; Start dùng `gunicorn --chdir project01/web/backend app:app ...`. Frontend root directory `project01/web/frontend`, build `npm ci && npm run build`, publish `dist`. Key backend, `WEB_ORIGIN` là URL frontend; frontend chỉ có `VITE_API_BASE_URL` là URL API. Không đưa key vào VITE.

Phải mang corpus/chunk/seed/index/model nhỏ theo manifest package mới; không dùng bundle offline cũ thay thế. Render free filesystem có thể mất ledger/jobs khi redeploy/restart; evaluation nhiều ngày phải chạy local với journal bền, không coi Render là nơi lưu kết quả chính. Free CPU không cần Torch/TF/CUDA. `/health` chỉ liveness; `/ready` tách key/index/usage, không gọi LLM. Chưa commit/push/deploy trong phase này.
