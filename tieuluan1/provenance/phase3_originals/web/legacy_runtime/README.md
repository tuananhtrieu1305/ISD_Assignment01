# Phase 6 — ứng dụng inference tích hợp

> **Kiến trúc hiện tại:** giao diện public đã được chuyển sang React/Vite trong
> `../../web/`, API sang Flask/Gunicorn trong `../../backend/`, và cấu hình
> Render nằm tại `../../render.yaml`. Xem `../../RENDER_DEPLOY.md` để chạy hoặc
> deploy. Server thư viện chuẩn bên dưới được giữ làm bản tái lập Phase 6 ban
> đầu và làm nguồn cho model service/validation đã kiểm thử.

Ứng dụng cục bộ phục vụ bốn artifact NumPy đã khóa từ Chương 2–4 qua ba vùng sử dụng: diabetes tabular, EuroSAT CNN, và RNN Customer/AAPL. Server chỉ dùng thư viện chuẩn Python cho HTTP; phụ thuộc khoa học được ghim trong `requirements.txt`. Không có dữ liệu đầu vào nào được ghi xuống đĩa hoặc ghi vào log.

## Chạy cục bộ

Từ thư mục gốc workspace, dùng đúng môi trường đã huấn luyện artifact:

```powershell
& 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe' -m term_paper.deployment.app.server --host 127.0.0.1 --port 8000
```

Nếu tạo môi trường mới:

```powershell
python -m venv .venv-deploy
& '.\.venv-deploy\Scripts\python.exe' -m pip install -r term_paper/deployment/requirements.txt
& '.\.venv-deploy\Scripts\python.exe' -m term_paper.deployment.app.server --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000`. Nút “Nạp mẫu kiểm thử” cung cấp dữ liệu deterministic cho từng use case.

## API và schema

| Method | Endpoint | Dữ liệu | Kết quả chính |
|---|---|---|---|
| GET | `/health` | — | trạng thái, version và hash đã xác minh |
| GET | `/api/models` | — | model registry công khai |
| GET | `/api/demo/{diabetes|eurosat|customer|aapl}` | — | input demo deterministic |
| POST | `/api/predict/diabetes` | đúng 21 trường số | xác suất, class, threshold |
| POST | `/api/predict/eurosat` | `image_base64` PNG/JPEG ≤ 5 MB | top-3 class/confidence |
| POST | `/api/predict/customer` | `sequence` 8 × 5 | xác suất, class, threshold |
| POST | `/api/predict/aapl` | `sequence` 30 × 5 OHLCV | RNN và naive last-Close |

Ví dụ health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Server từ chối trường thừa, số không hữu hạn, shape sai, OHLC bất nhất, file không phải PNG/JPEG và request quá 7 MB. Lỗi validation trả HTTP 400 cùng thông báo tiếng Việt an toàn; lỗi nội bộ không trả stack trace.

## Kiểm thử

```powershell
& 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe' -m unittest discover -s term_paper/deployment/tests -v
& '.\term_paper\tools\verify_phase6.ps1'
```

Các test kiểm tra validation, security headers, demo → prediction và parity với prediction artifact của bốn mô hình. Tolerance là `1e-6` cho probability/classification và `1e-4` cho AAPL sau inverse scaling sang USD.

## Docker

Dockerfile dùng non-root user, health check và chỉ copy artifact cần thiết. Để tránh gửi toàn bộ workspace khoảng nhiều GB vào Docker daemon, thư mục `deployment/` là context chính và sáu thư mục nhỏ được truyền dưới dạng named build context (Docker BuildKit):

```powershell
docker build -f term_paper/deployment/Dockerfile `
  --build-context source=term_paper/src `
  --build-context models=term_paper/artifacts/models `
  --build-context ch3_manifest=term_paper/artifacts/manifests/ch3 `
  --build-context ch4_manifest=term_paper/artifacts/manifests/ch4 `
  --build-context a06_preprocessing=A06/models/preprocessing `
  --build-context eurosat_demo=A05/datasets/eurosat/EuroSAT_RGB/AnnualCrop `
  -t tieu-luan-ai:phase6 term_paper/deployment
docker run --rm -p 8000:8000 tieu-luan-ai:phase6
```

## Bảo mật và giới hạn

- Bind mặc định là `127.0.0.1`; không có authentication nên không nên expose trực tiếp ra Internet.
- CSP, `nosniff`, chống iframe, no-referrer, giới hạn payload và rate limit in-memory được bật.
- Chỉ load artifact có SHA-256 trùng registry; khởi động thất bại nếu hash lệch.
- Joblib/pickle chỉ an toàn với artifact tin cậy. Không nhận model upload từ người dùng.
- Diabetes là minh họa học thuật, không phải chẩn đoán y khoa. AAPL không phải khuyến nghị đầu tư.
- Public cloud: `OPTIONAL_PENDING_CREDENTIALS`; local và Docker là deliverable chính của Phase 6.
