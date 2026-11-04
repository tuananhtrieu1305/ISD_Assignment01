# Deploy React + Flask lên Render

Ứng dụng được tách thành hai service nhưng dùng chung một repository:

- `web/`: React + TypeScript + Vite, deploy dưới dạng Render Static Site.
- `backend/`: Flask + Gunicorn, deploy dưới dạng Render Web Service.
- `term_paper/`: runtime NumPy, model registry và các artifact đã khóa từ Chương 2–4.
- `render.yaml`: Blueprint tạo và nối hai service tự động.

## 1. Kiểm tra local

Từ thư mục gốc repository, mở hai terminal.

Yêu cầu local: Python 3.12 và Node.js 22.6 trở lên.

Backend:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pip install -r backend\requirements-dev.txt
& '.\backend\.venv\Scripts\python.exe' -m backend.app
```

Frontend:

```powershell
cd web
npm ci
npm run dev
```

Mở `http://localhost:5173`. API mặc định chạy tại `http://127.0.0.1:5000`.

Kiểm thử và build:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest backend\tests -q
cd web
npm test
npm run build
```

## 2. Các file bắt buộc phải có trên Git

Backend xác minh SHA-256 khi khởi động. Hãy commit toàn bộ thay đổi, đặc biệt là:

- `backend/`, `web/`, `render.yaml`;
- `term_paper/deployment/app/model_service.py` và `schemas.py`;
- `term_paper/src/scratch/{mlp,cnn,rnn}.py`;
- các model/preprocessor mà `MODEL_REGISTRY` tham chiếu trong `term_paper/artifacts/models/`;
- các manifest demo trong `term_paper/artifacts/manifests/ch3/` và `ch4/`;
- ba scaler trong `A06/models/preprocessing/` và ảnh EuroSAT demo được manifest tham chiếu.

Không commit `.env`, virtual environment, `node_modules` hay secret.

## 3. Tạo Blueprint trên Render

1. Đẩy repository lên GitHub/GitLab/Bitbucket.
2. Trong Render Dashboard, chọn **New → Blueprint**.
3. Kết nối repository và chọn file `render.yaml` ở thư mục gốc.
4. Nhấn **Apply**. Render sẽ tạo:
   - `ai-term-paper-api` — Flask/Gunicorn;
   - `ai-term-paper-web` — React static site.
5. Chờ cả hai service chuyển sang trạng thái live.

Blueprint tự truyền hostname backend vào `VITE_API_BASE_URL` khi build React, đồng thời truyền hostname frontend vào `WEB_ORIGIN` để CORS chỉ cho phép đúng site. Nếu đổi tên service trong YAML, phải đổi đồng thời trường `name` bên trong các khối `fromService`.

## 4. Smoke test sau deploy

Mở URL của Static Site rồi thử lần lượt nút **Nạp mẫu kiểm thử** ở ML, CNN và hai chế độ RNN. Có thể kiểm tra API riêng:

```powershell
Invoke-RestMethod https://<api-host>.onrender.com/health
Invoke-RestMethod https://<api-host>.onrender.com/api/models
```

`/health` phải trả `status: ok`, đủ bốn model và `hash_verified: true`. Gói free có thể ngủ khi không dùng nên request đầu tiên có thể chậm hơn các request sau.

## 5. Cấu hình thủ công nếu không dùng Blueprint

Backend Web Service:

- Runtime: Python
- Build: `pip install -r backend/requirements.txt`
- Start: `gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
- Health check: `/health`
- Environment: `PYTHON_VERSION=3.12.14`, `WEB_ORIGIN=https://<frontend-host>`

Frontend Static Site:

- Build: `cd web && npm ci && npm run build`
- Publish directory: `web/dist`
- Environment: `VITE_API_BASE_URL=https://<api-host>`
- Rewrite: `/*` → `/index.html`
