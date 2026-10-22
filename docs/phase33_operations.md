# Phase33 — sử dụng Model Lab React V3

Entry point `apps/web/src/App.tsx` → `src/v3/App.tsx`. UI cũ được giữ làm tham chiếu,
không còn active; snapshot trước sửa tại artifacts/manifests/phase33/web_before.zip.
Style sáng/xanh lam từ web cũ được giữ, nhưng source mới tách theo chức năng,
không import stylesheet V2 nặng hoặc API V2. Không train/TEST từ giao diện.

## Chạy local (hai terminal PowerShell tại C:\DATA\assign)

Terminal1 — backend CPU:

```powershell
.\scripts\run_api_v3.ps1 -Mode cpu -Port 5000 -Distribution Ubuntu
```

Nếu cần native GPU, thay cpu bằng local_gpu: Keras/TensorFlow và PyTorch/CUDA
trong2venv đã khóa; scratch vẫn CPU. UI chỉ đọc actual_backend/device từ API.
Không đổi backend bằng request phía trình duyệt, không Keras fallback âm thầm.

Terminal2 — frontend:

```powershell
.\scripts\run_web_v3.ps1 -Action dev
```

Mở http://localhost:5173. Dừng từng terminal bằng Ctrl+C. Nếu port đã dùng,
wrapper báo lỗi thay vì tự chuyển port (CORS phụ thuộc origin chính xác).
Backend vẫn là runtime Ubuntu/user tuananh; không Python Windows/doctor cũ.

Nếu chưa có runtime frontend/dependency trên máy mới:

```powershell
.\scripts\bootstrap_web_v3.ps1
.\scripts\run_web_v3.ps1 -Action install
.\scripts\run_web_v3.ps1 -Action install:browsers
```

Node22.23.4 portable được khóa checksum chính thức, nằm trong .local, không cài
hệ thống. npm cache/Chromium cũng trong .local; node_modules nằm ở apps/web,
đều ignored. Wrapper khôi phục PATH/cache/browser env của shell sau khi xong.
Không thay uv.lock, Python venv hoặc metadata môi trường GPU. Browser chỉ cần
cho E2E; xem web bình thường không cần cài Playwright browser.

## Điều hướng và demo

Tổng quan/ML/CNN/RNN–LSTM/KG–RAG/Multi-Agent, mỗi chương3dataset. Ch2–6 có các mục
Dữ liệu, Hợp hàm & lý thuyết, Chạy so sánh, Kết quả đã lưu, Triển khai; Ch1 chỉ
case study lịch sử, không giả training. RNN/LSTM toggle giữ dataset/section.
URL ví dụ: `/rnn?dataset=ch4_gold_pink_sheet&family=lstm&section=run`.
Refresh/back/forward giữ lựa chọn; sai dataset/family/section có cảnh báo/reset.

Trong Chạy so sánh, dùng Mẫu TRAIN hoặc sửa input. Tabular có fields, CNN nhận
PNG/JPEG<=4,5MB (backend còn kiểm pixel/MIME/schema), chuỗi dùng ma trận JSON theo
thứ tự mẫu, QA dùng tiếng Anh từ nguồn, agent giữ record ID từ mẫu. Không nhập
bệnh án/secret hoặc dữ liệu cá nhân. Ch6 là ID-bound, không hỏi đáp tự do/LLM.
Ch5 demo compact khác benchmark lịch sử; Wikidata chỉ browser,5QA unavailable
là đúng thiết kế, không model failure cần tuning hoặc benchmark thứ ba.

Một nút gửi mọi implementation trong cùng job/input; worker thực thi tuần tự.
Tên scratch/keras/pytorch chỉ cách train weights. API CPU phục vụ cả3 bằng NumPy
portable, **không** timing native Keras/PyTorch. Mỗi slot có backend/device/hash.
Inference batch1 không accuracy, p95 hoặc kết luận chất lượng. Kết quả thuộc job
đã gửi; nếu sửa form hoặc refresh, form có thể khác input cũ — kiểm input hash
và bấm Chạy để tạo kết quả mới. Không lưu input riêng tư trong sessionStorage.

Job và capability ở sessionStorage theo API origin/dataset/family. Token24byte
random hex48 chỉ gửi header, không URL/log/localStorage; refresh chỉ GET, không
re-POST. Đây không phải hệ tài khoản/JWT. TTL30phút/queue32/ephemeral; nếu hết hạn
hoặc redeploy, tạo job mới. Không chia sẻ token, screenshot HAR hoặc debug headers.
Client không tự retry POST sau lỗi; GET có nút thử lại, không tạo training/job kép.

## Đọc kết quả khoa học

Kết quả đã lưu chỉ đọc metric/tables frozen; chọn split/seed/metric/unit/horizon.
Deployment vẫn seed42 cố định, selector kết quả không chọn lại model theo TEST.
Null hiển thị Không có số đo, không0. Power RNN/Torch/s17 giữ null training cost;
qualityn3/costn2, failed seal cũ nguyên vẹn. Metric âm ở bảng đầy đủ, không cắt mất
trên chart trục0. Mean/std ba seed và bảng đầy đủ có trong artifact gốc kèm SHA.
KG/Agent JSON gốc giữ cấu trúc/domain/scope, CSV lọc theo dataset/domain trước hiển
thị; không gộp USD/index/kW/horizon. Citation URL cấp dataset/container như nguồn
đã khóa, không bịa URL riêng từng chunk. Agent timeline cho node parents/outcome,
duration0 chưa đo riêng không0ms; message là tool I/O, không chain-of-thought.

## Build, kiểm chứng và deploy

```powershell
.\scripts\run_web_v3.ps1 -Action build
.\scripts\run_web_v3.ps1 -Action preview
```

Preview chỉ kiểm build local, không production server. Build nghiệm thu local API
127.0.0.1:5000 được chụp riêng dist/phase33, không ghi đè snapshot đã khóa.
Để deploy, xem deploy/web-v3/README.md: Static Site root apps/web, URL API HTTPS
trong VITE_API_BASE_URL lúc build, CORS backend đúng frontend và rewrite
`/* → /index.html`. VITE_* là public, không đặt secret. Chưa cloud deploy/tạo
service/push/upgrade trả phí; Blueprint backend/root cũ không bị sửa.

Sau nghiệm thu, chỉ kiểm hash:

```powershell
.\scripts\check_phase33.ps1 -Distribution Ubuntu
```

Không chạy lại writer vào tên acceptance cũ. Unit fixtures/saved TRAIN smoke không
là training/TEST mới. E2E Chromium desktop/mobile emulation, Axe không full WCAG
certification/Safari/Firefox/device thật. Pytest fixture_only trong unit log là
ca ErrorBoundary cố ý, không lỗi browser production. Trạng thái phát hành thật
ở artifacts/manifests/phase33/verification.json/checkpoint.json.

TDD/security/frontend/e2e skills đã dẫn đến guard URL/token/upload/escape, test
native-fetch/abort/race, cải thiện contrast và mobile JSON; không audit Git history
hoặc đảm bảo mọi phụ thuộc tương lai an toàn. npm audit là snapshot thời điểm chạy.
