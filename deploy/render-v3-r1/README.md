# Render V3 — cùng repository, hai service hiện có

Revision tích hợp deploy, không thay source khoa học, model, TEST seal hoặc khóa Phase22–35.
`render.yaml` ở root hiện mô tả V3; bản trước được giữ ở `render-v2-before.yaml`.
Không tạo service mới nếu đã có `isd-assignment01-api` và `isd-assignment01-web`.

## Những gì được commit

- `api-bundle.zip`: bản sao **nguyên byte** gói CPU Phase32/package_v2, 74.864.102 byte.
- `release.json`: SHA-256 ZIP, manifest, dependency lock và budget đã khóa.
- `scripts/render_v3.py`: staging, kiểm hash, cài đúng CPU dependency và chạy Gunicorn.
- Root `render.yaml`, `.gitignore`, tài liệu và test deploy mới.

ZIP chứa 808 payload file và `bundle_manifest.json`, tổng 88.165.986 byte sau giải nén.
Gói bao gồm 766 asset của registry, trong đó có checkpoint bị Git ignore ở repo phát triển.
Không cần force-add `artifacts/models/`, nới `.gitignore` toàn bộ model, hoặc dùng Git LFS.
Gói không chứa môi trường GPU, cache train, raw ảnh/bảng lớn hay tập prediction TEST đầy đủ.
Có **11 JSON snapshot Wikidata** bắt buộc cho structural browser, dù đường dẫn lịch sử
nằm dưới `data/raw/ch5/wikidata/`; chúng được giữ nguyên hash, không phải tải lại raw corpus.
Các bảng metric lịch sử allowlisted vẫn được dùng để hiển thị kết quả đã lưu.

ZIP được commit trực tiếp trong Git, không phải URL tải tùy ý hoặc LFS pointer.
Không chỉnh ZIP bằng tay: mọi member được kiểm path, count, size và SHA-256 trước khi dùng.
Runtime giải nén dưới `.render-v3/runtime-<hash>/` (ignored); không ghi đè source đang phát triển.
Không chạy train, evaluation TEST hoặc tải dataset lúc build/start/request.

## 1. Commit và push

Tại root repository, xem diff trước. Các lệnh chỉ đưa thay đổi deploy này vào commit:

```powershell
git add -- .gitignore render.yaml AGENTS.md scripts/render_v3.py tests/deploy deploy/render-v3-r1 docs/render_v3_r1_operations.md artifacts/manifests/render_v3_r1
git diff --cached --stat
git commit -m "fix: deploy V3 API and React from the same Render repository"
git push origin main
```

Nếu index đã có thay đổi khác, kiểm tra kỹ trước khi commit; không dùng `git add .` theo quán tính.
Không đưa `.env`, DB job, raw dataset, venv hoặc cache build vào commit. ZIP khoảng 75 MB,
nên lần push đầu có thể lâu hơn; kiểm tra file thật đã xuất hiện trên branch Render theo dõi.
Chưa có commit/push nào được tự thực hiện bởi bản sửa này.

## 2. Backend — thay cấu hình Dashboard **một lần**

Service `isd-assignment01-api`, repository hiện tại, branch `main`:

| Setting | Giá trị |
|---|---|
| Root Directory | **Để trống**, không phải `apps/api` |
| Build Command | `python -B scripts/render_v3.py build` |
| Start Command | `python -B scripts/render_v3.py start` |
| Health Check Path | `/health` |
| Auto-Deploy | `On Commit` |
| Instances / worker | Một instance; wrapper cố định một worker, hai HTTP thread |

Environment (giá trị public, không có secret):

```text
PYTHON_VERSION=3.11.17
NODE_VERSION=22.23.4
AI_SERVING_MODE=cpu
AI_CORS_ORIGINS=https://isd-assignment01-web.onrender.com
AI_TRUSTED_HOSTS=localhost,127.0.0.1,.onrender.com
AI_JOB_DB=/tmp/ai-paper-v3/jobs.db
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
PYTHONDONTWRITEBYTECODE=1
```

`WEB_ORIGIN`, `RATE_LIMIT_PER_MINUTE`, `AGENT_TIMEOUT_MS` là cấu hình V2, V3 không dùng.
Có thể bỏ chúng để tránh nhầm. Không tự đặt `PORT`; wrapper đọc giá trị Render cấp.
Không dùng lại `backend.app:app`, `apps.api.app:app`, `backend/requirements.txt`,
`uv sync` toàn bộ repo hoặc dependency GPU cho build Render.

Thay Settings thủ công xong, chọn **Clear build cache & deploy** cho lần chuyển V2→V3.
Commit root YAML **không tự đổi** cấu hình các service thủ công. Nếu đang quản lý bằng
Blueprint thì đồng bộ Blueprint hiện có sau khi xem thay đổi; không tạo Blueprint mới
một cách mù quáng vì có thể tạo thêm service. Hai Dashboard service hiện có là đủ.

## 3. Frontend

Service `isd-assignment01-web`, cùng repository/branch:

| Setting | Giá trị |
|---|---|
| Root Directory | `apps/web` |
| Build Command | `npm ci --no-fund --no-audit && npm run build` |
| Publish Directory | `dist` (không nhập lại tiền tố `apps/web/`) |
| Auto-Deploy | `On Commit` |
| Build Filters | Để trống, trừ khi đã chủ động thiết kế bộ lọc mới |

```text
NODE_VERSION=22.23.4
SKIP_INSTALL_DEPS=true
VITE_API_BASE_URL=https://isd-assignment01-api.onrender.com
```

Đặt Rewrite: `/*` → `/index.html`, action **Rewrite** (không Redirect).
Biến VITE public và được đóng vào JS lúc build: đổi URL phải rebuild, không có secret.
Nếu Dashboard còn CSP cũ, đồng bộ CSP V3 trong root YAML, đặc biệt `connect-src` đúng API
và style policy; không xóa toàn bộ security header để chữa lỗi giao diện.

## 4. Kiểm tra sau deploy

1. `/health` trả 200 chỉ xác nhận process sống.
2. `https://isd-assignment01-api.onrender.com/ready` phải 200 và components ready.
3. `/api/v3/chapters` trả sáu chương; `/api/v3/openapi.json` là contract V3.
4. Mở frontend, vào ML/CNN/RNN–LSTM/KG–RAG/Multi-Agent, chọn Mẫu TRAIN và chạy so sánh.
5. Refresh trực tiếp `/cnn` hoặc `/rnn` không 404; request trình duyệt không bị CORS.
6. Nếu 503 artifact hoặc hash mismatch, giữ log và kiểm commit/gói; không tắt hash check.

Serving CPU dùng NumPy portable cho weights được train riêng bằng scratch/Keras/PyTorch;
không phải native TensorFlow/PyTorch timing. Năm QA slot Wikidata unavailable là đúng thiết kế.
Ch5 demo compact khác benchmark; Ch6 là tác tử local deterministic, không LLM.

Free có cold start và filesystem ephemeral: job có thể mất khi sleep/restart/deploy.
Giữ budget CPU448MiB/deadline60s của API; đo local không bảo đảm mọi tác vụ vừa RAM Free.
Không có cloud deployment hoặc nâng gói trả phí nào được tự thực hiện.

## 5. Những lần push sau

React vẫn build từ `apps/web` trong commit mới. Model và backend khoa học đã khóa,
nên ZIP là bản runtime đã nghiệm thu, không phải cache tùy tiện. Mỗi build/start so
sánh các file Python thuộc runtime closure trong checkout với bản ZIP (chỉ chấp nhận
khác CRLF/LF do Git). Nếu source backend đổi, build **dừng với yêu cầu revision**,
không âm thầm chạy code cũ. Cập nhật backend/model cần gói revision mới + manifest
và test tương ứng; không train lại chỉ vì deploy hoặc sửa React.

## 6. Kiểm local, không cài thêm vào GPU env

Nghiệm thu revision:46 test PASS/0skip, coverage96,3134%combined (branch93,75%);
8 E2E PASS/0retry trên React production build local + **venv CPU-only riêng**.
26 CPU package cài mới bằng uv với `--require-hashes`, sau đó lệnh build pip/check
đúng như trên Render PASS; `pip check` PASS, không Torch/TensorFlow/Keras trong venv.
Production build đã kiểm với API HTTPS thật. Đây vẫn là kiểm local, không cloud/SLA.
Receipt: `artifacts/manifests/render_v3_r1/verification.json`; XML/coverage cùng thư mục.

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module scripts.render_v3 -ModuleArguments @('check')
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module pytest -ModuleArguments @('tests/deploy/test_render_v3_r1.py','-q')
```

`check` chỉ staging/hash/component audit, không inference. `build` có cài dependency:
**không chạy build trong venv GPU**. Chỉ dùng build trên Render hoặc CPU-only venv riêng
cài đúng hash lock. Không thay `uv.lock`, bootstrap/doctor cũ hoặc acceptance evidence đã khóa.

Nguồn chính thức: [Render monorepo](https://render.com/docs/monorepo-support),
[Deploys](https://render.com/docs/deploys), [Python version](https://render.com/docs/python-version),
[Static Sites](https://render.com/docs/static-sites), [Free](https://render.com/docs/free).
