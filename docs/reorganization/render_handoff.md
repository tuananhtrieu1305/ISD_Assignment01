# Render sau khi sắp xếp source

Root `render.yaml` tiếp tục dành cho hai service hiện có **isd-assignment01-api** và **isd-assignment01-web**, phục vụ **tiểu luận3**. Chưa push/deploy hoặc sửa Dashboard trong REORG. Hai tiểu luận khác có template riêng trong `web/deploy/render.example.yaml`; tám demo nhỏ có `web/render.example.yaml` cho chế độ static replay.

## Đổi Settings một lần cho hai service hiện tại

| Trường | API | Web |
|---|---|---|
| Branch | main | main |
| Root Directory | để trống | `tieuluan3/web/frontend` |
| Build Command | `python -B scripts/render_project.py build --project tieuluan3` | `npm ci --no-fund --no-audit && npm run build` |
| Start Command | `python -B scripts/render_project.py start --project tieuluan3` | không có |
| Publish Directory | không có | `dist` |
| Health Check | `/health` | không có |
| Auto-Deploy | On Commit | On Commit |

API env: `PYTHON_VERSION=3.11.17`, `AI_SERVING_MODE=cpu`, `AI_CORS_ORIGINS=https://isd-assignment01-web.onrender.com`, `AI_TRUSTED_HOSTS=localhost,127.0.0.1,.onrender.com`, `AI_JOB_DB=/tmp/ai-paper-v3/jobs.db`, `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`. Web env: `NODE_VERSION=22.23.4`, `VITE_API_BASE_URL=https://isd-assignment01-api.onrender.com`. Đổi env Vite cần build lại UI.

Các lệnh chạy tính từ Root Directory; service không đọc được file bên ngoài Root Directory đó. Vì backend cần script ở root và source parity, để Root Directory API trống. Build filter tính từ repository root, xem các path trong YAML mới. Những quy tắc này theo [Render monorepo support](https://render.com/docs/monorepo-support).

YAML là cấu hình Blueprint, không tự sửa hai service được quản lý thủ công. Cần đổi Settings như bảng; nếu có Blueprint liên kết thì kiểm bản diff Blueprint trước khi sync. Tham khảo [Render Blueprint specification](https://render.com/docs/blueprint-spec). Shim `scripts/render_v3.py` vẫn chuyển lệnh API cũ sang entrypoint mới, nhưng không thay thế việc sửa Root Directory của web.

Sau khi commit/push và cấu hình xong, redeploy API rồi web. Kiểm `/health`200 và `/ready`200 ở API; mở **https://isd-assignment01-web.onrender.com** để xem giao diện. URL `...-api.onrender.com` dành cho JSON API. Chưa có kết quả kiểm production sau refactor; các bằng chứng Phase3 là local/build/đóng gói.

## Serving bundle và source parity

Mỗi tiểu luận có `web/deploy/release.json` và `api-bundle-r1.zip`. Lệnh build kiểm SHA archive/manifest/từng file và đối chiếu Python source trong repo trước khi stage runtime CPU. Thay backend source phải tạo deployment revision mới; không chỉ sửa code rồi để bundle cũ phục vụ. Runtime Render không cần raw dataset, training cache hoặc venv GPU. Ba bundle đã được kiểm từ source-only checkout với interpreter CPU hiện có, không chạy train/TEST.

Một số raw/checkpoint lớn vẫn là local-only hoặc bị ignore. Điều đó không chặn serving bundle đã đóng gói; muốn chạy notebook/train ở máy mới phải lấy đủ đúng snapshot theo datasets/catalog và manifest. Không dùng Git LFS pointer thay ZIP thật. Mỗi ZIP serving hiện nhỏ hơn100MiB; kiểm lại trước khi push.

Tiểu luận1 giữ warning sklearn1.9.1→1.9.0 của các preprocessor cũ, đã có từ trước migration; không re-fit/re-serialize để xóa warning. Tiểu luận2 không có Chương6, còn tiểu luận3 giữ Chương6. Free service có cold start và giới hạn bộ nhớ; local PASS không phải bằng chứng deploy production thành công.
