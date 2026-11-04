# Render — cùng repository, chưa deploy

Template `render.yaml` dùng2 service:Python API và React Static Site. Phase2 không tạo service hoặc deploy cloud.

Trước commit, cần notebook sources, `web/backend/project01_core/`, `artifacts/package/v1/`, `artifacts/phase2/source_exports.json`, `artifacts/phase2/summary.json`, `datasets/demo_profiles.json`, `datasets/profile_schema.json` và frontend package-lock. Project `.gitignore` mở JSON nhỏ cần thiết, không cần ép add raw/venv. Package medical-only tự đủ serving, không cần dữ liệu tài chính hoặc runtime view cũ.

**API:** Root Directory để trống; Build `python -B project01/scripts/render.py build`; Start `python -B project01/scripts/render.py start`; health `/health`; Python3.11.17. `WEB_ORIGIN`=URL frontend thực tế; `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`. Gunicorn1worker/1thread, timeout40; pipeline có process deadline30.

**Frontend:** Root Directory `project01/web/frontend`; Build `npm ci --no-audit --no-fund && npm run build`; Publish Directory `dist`; Node22.23.4; `VITE_API_BASE_URL`=URL API thực tế. SPA rewrite `/*`→`/index.html`. Thay URL ví dụ bằng domain Render cấp. Đổi VITE env phải rebuild.

Mở `/health` để kiểm process, `/ready` để kiểm package/notebook/export parity, rồi URL **frontend** để xem UI. API root không có React khi API service không build frontend. Free service có thể cold-start; latency local không là số đo cloud.

Requirements CPU ở `../backend/requirements.txt`, không Torch/TF/GPU. Kiểm local không cài dependency:

```bash
/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python -B project01/scripts/render.py check
```

Không chạy stage `build` local để thay env hiện có; stage này dành build environment mới trên Render. Không seed notebook/refit index khi deploy. Đổi thuật toán sau freeze cần revision và đánh giá mới trước khi export/bundle lại.
