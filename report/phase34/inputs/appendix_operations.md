# PHỤ LỤC C. HƯỚNG DẪN TÁI LẬP VÀ DEMO

## C.1. Môi trường và đường dẫn nguồn

Python dùng WSL distro Ubuntu, user tuananh, hai venv đã khóa; không Python Windows,
backend/.venv hoặc bootstrap/doctor của distro cũ. Code mô hình ở `src/common/`,
`src/ch02_ml/`, `src/ch03_cnn/`, `src/ch04_rnn_lstm/`, `src/ch05_knowledge_rag/`
và `src/ch06_multi_agent/`. Notebook V3 gọi các module này, không giữ bản thuật toán
khác. Dataset raw, cache, checkpoint và môi trường không phân phối lặp trong báo cáo.

Code scratch tự forward/loss/backward/BPTT/Adam bằng NumPy; native Keras giữ backend
TensorFlow độc lập và PyTorch dùng CUDA. Không đổi tên Keras trên PyTorch để gọi là
đường TensorFlow. Các demo CPU có actual_backend=numpy và actual_device=cpu, bất kể
weights được train bằng implementation nào. Khóa runtime và recovery có receipt riêng.

Kiểm tra sau phát hành là hash audit, không chạy train/TEST lại:

```powershell
.\scripts\check_phase29.ps1 -Distribution Ubuntu
.\scripts\check_phase30.ps1 -Distribution Ubuntu
.\scripts\check_phase31.ps1 -Distribution Ubuntu
.\scripts\check_phase32.ps1 -Distribution Ubuntu
.\scripts\check_phase33.ps1 -Distribution Ubuntu
```

Các wrapper cũ không nhận Distribution phải được đọc trước khi gọi trên runtime đã
khôi phục; có thể gọi đúng auditor module qua run_experiment với Distribution Ubuntu.
Không chạy producer/coverage vào evidence đã khóa và không tự sửa lock khi phát hiện
sai hash. Phần mềm hiện hành là source được pin trong manifest, không checkpoint
initialized ban đầu hoặc file có tên giống nhau trong thư mục legacy.

## C.2. Chạy giao diện local

Tại C:\DATA\assign, terminal PowerShell thứ nhất:

```powershell
.\scripts\run_api_v3.ps1 -Mode cpu -Port 5000 -Distribution Ubuntu
```

Terminal thứ hai:

```powershell
.\scripts\run_web_v3.ps1 -Action dev
```

Mở http://localhost:5173. Nếu cần native framework trên GPU local, dùng Mode local_gpu
cho API; scratch vẫn CPU. Không chạy hai API cùng port. Dừng từng terminal bằng Ctrl+C.
Máy mới cần bootstrap Node portable và npm install theo hướng dẫn vận hành web; không
phải cài lại Python/GPU để chỉ xem React. Không nhập bệnh án, khóa API hay dữ liệu riêng tư.

Mỗi job gửi một input cùng comparison group và giữ seed42 của neural serving. Capability
ngẫu nhiên chỉ ở sessionStorage và header; không chia sẻ token/URL debug/HAR. Refresh
khôi phục bằng GET, không tự tạo job mới; input form có thể khác input job đã lưu, nên
kiểm input hash trước diễn giải. TTL30phút và storage ephemeral không là hệ tài khoản.

## C.3. Render và trạng thái triển khai

Backend compact package và Blueprint ở `deploy/v3/`; Static Site Blueprint ở
`deploy/web-v3/`. Frontend build dùng public VITE_API_BASE_URL tại thời điểm build,
không đặt secret trong biến VITE. Khi public, cần API HTTPS, CORS chính xác frontend,
rewrite SPA về index.html và health/readiness thực. Build nghiệm thu local trỏ127.0.0.1
không được dùng nguyên để gọi API trên máy người xem khác.

Một worker HTTP và supervisor/job có giới hạn là cấu hình đã kiểm; không tăng replica
hoặc Gunicorn worker tùy ý khi SQLite và queue chưa được thiết kế phân tán. Không train
GPU trên Render. Số đo local gồm từng process trong phạm vi đã ghi, không bảo đảm RAM
gói cloud, SLA, bảo toàn job sau redeploy hoặc tải đồng thời ngoài budget.

Chưa có bằng chứng cloud deploy V3 hoặc kiểm Render header trong thực tế. Các hình web
ở hồ sơ nghiệm thu là Chromium local, không được chú thích thành site production.

## C.4. Đọc bằng chứng và các trường hợp ngoại lệ

Ch2–4 có matched track, seed và đơn vị riêng; các bảng mean/std không là kiểm định
thống kê. Ch4 giữ telemetry thiếu của Power RNN/PyTorch seed17: chất lượng đủ ba seed,
chi phí chỉ hai; original GPU→CPU FAIL và Power failed seal vẫn còn. Revision hoàn tất
schema từ prediction cũ không tăng số batch TEST hoặc cho phép infer lại claim đã dùng.

Ch5 giữ TEST count1 và output lịch sử. Demo KG không tự phục hồi metadata split/URL raw
từng chunk đã lược bỏ. Ch6 benchmark có template tổng hợp; parent TRAIN của predictor
không biến thành holdout mới. Tính đúng của receipt/citation không chứng minh quyết định
y khoa, tài chính hoặc quan hệ nhân quả. Những giới hạn này áp dụng cả khi trình diễn.
