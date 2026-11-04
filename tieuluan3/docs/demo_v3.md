# Demo tiểu luận AI V3

## Mở bản tiểu luận

File nộp: `releases/v3/Tieu_luan_AI_6_chuong.docx`.
PDF đối chiếu: `releases/v3/Tieu_luan_AI_6_chuong_QA.pdf`.
Kiểm tra `releases/v3/release_manifest.json` có status PASS trước khi dùng bản phát hành.
Bìa giữ thông tin A06 theo xác nhận của người dùng. Mục lục/danh mục có liên kết nội bộ;
Word mặc định cần Ctrl+click. Navigation Pane dùng Heading 1–3.

## Chạy giao diện trên máy hiện tại

Mở hai terminal PowerShell tại `C:\DATA\assign`.

Terminal 1:

```powershell
.\scripts\run_api_v3.ps1 -Mode cpu -Port 5000 -Distribution Ubuntu
```

Terminal 2:

```powershell
.\scripts\run_web_v3.ps1 -Action dev
```

Mở `http://localhost:5173`. API JSON ở `http://localhost:5000/health` và `/ready`.
Ctrl+C từng terminal để dừng. Không mở hai API cùng port. Không dùng Python Windows,
distro Ubuntu-24.04/home anhca cũ hoặc bootstrap/doctor cũ ghi đè evidence GPU.

Chế độ CPU chạy NumPy portable trên ba bộ weights đã train độc lập. Tên scratch/Keras/
PyTorch là nguồn huấn luyện, không có nghĩa ba framework native đang chạy CPU.
Muốn demo native GPU local, đổi `-Mode cpu` thành `-Mode local_gpu`; Keras/TensorFlow
và PyTorch chạy trong hai venv WSL riêng, scratch vẫn CPU. Không train từ web.
Xem `docs/phase32_operations.md`, `docs/phase33_operations.md` khi cần cài Node/dependency
trên máy khác; không tự tạo môi trường Python mới không khóa.

## Kịch bản trình bày 8–12 phút

1. Tổng quan: sáu chương, mỗi chương ba nguồn hoặc task view. Ch1 là case study lịch sử,
   ImageNet chỉ metadata, không có model/ảnh local giả.
2. ML → Ames/CDC → Dữ liệu: đọc nguồn, kích cỡ, phân bố và mẫu; chuyển Hợp hàm để giải thích
   đầu ra bước trước là đầu vào bước sau; chọn Chạy so sánh, dùng mẫu TRAIN rồi chạy cả ba.
3. CNN → IDRiD/EuroSAT/CIFAR-10: cùng ảnh cho ba checkpoint, đọc xác suất và actual backend/
   device. Không gọi xác suất là accuracy hoặc dùng ảnh võng mạc để chẩn đoán.
4. RNN–LSTM → vàng/BIS/điện: đổi family, giữ dataset; giải thích lookback/horizon/đơn vị và
   sáu lớp học được. Run-all chỉ chạy ba implementation của family đã chọn trên một window.
5. KG–RAG → MedQuAD/FinQA: dùng mẫu tiếng Anh, xem B0–B4, citation và từ chối. Wikidata
   là browser cấu trúc; năm slot QA unavailable là đúng, không benchmark QA thứ ba.
6. Multi-Agent: dùng record ID trong mẫu; xem A0/A1/A2, DAG và message hành động. Đây là
   điều phối xác định, không LLM hay chain-of-thought. Verifier kiểm integrity không chứng minh
   nội dung y khoa/tài chính đúng.
7. Kết quả đã lưu: tách metric TEST lịch sử với job demo mới và với timing HTTP. Neural serving
   cố định seed42, selector kết quả không thay checkpoint theo TEST.

Không nhập bệnh án, dữ liệu cá nhân, API key hoặc secret. Không chia sẻ capability token,
HAR/debug URL. Job TTL30phút, storage ephemeral; refresh đọc job cũ, không tự infer lại.

## Render: sẵn cấu hình, chưa cloud deploy V3

Blueprint backend compact ở `deploy/v3/`, Static Site ở `deploy/web-v3/`; hướng dẫn chuẩn
trong `docs/phase32_operations.md` và `docs/phase33_operations.md`.
Phải dùng URL API HTTPS thật cho VITE_API_BASE_URL lúc build, CORS exact origin, SPA rewrite,
health/readiness và kiểm RAM/job trên service thực. Giữ một Gunicorn worker theo thiết kế queue;
không train GPU trên Render, không tự scale nhiều replica. Build local trỏ127.0.0.1 không
được dùng nguyên cho người xem trên Internet.

Phase35 đã kiểm production build React và 23 ca E2E local trên compact API bundle ở Linux
ext4, dùng môi trường đã khóa hiện có. Không phải cài mới CPU-only sạch, kiểm tải/SLA hoặc
bằng chứng đã deploy lên tài khoản Render. Không có thao tác cloud hay thay đổi tài khoản.

## Kiểm tra và chỉnh sửa về sau

```powershell
.\scripts\run_docs_v3.ps1 -Module scripts.phase35_release -Arguments @('--stage','verify')
```

Lệnh chỉ đọc hash bản phát hành và khóa cha, không chạy train/TEST. Khi hash sai, dừng và
đối chiếu; không sửa lock cho khớp. Muốn sửa nội dung đã khóa phải tạo revision mới.
Danh mục Word là các dòng đã dựng với REF/PAGEREF native và số trang cache đã kiểm;
F9 có thể cập nhật số trang, nhưng không tự thêm tiêu đề mới như trường TOC tự sinh.
Thay nội dung cần build/render/QA revision lại; không Save As đè bản khóa.
Hash/command/code để sao chép nên lấy từ manifest/source, không từ Word vì chuỗi dài có
zero-width break nhằm dàn trang.

Lưu ý minh bạch: hai lần probe Word đầu đã đặt Options.UpdateLinksAtOpen=False mà chưa
lưu giá trị trước; tùy chọn Word của máy có thể còn tắt. Script hiện tại đã bỏ thao tác đó;
không tự đoán giá trị để đổi lại. Nếu bạn vốn bật tự cập nhật liên kết khi mở Word, hãy
kiểm tra lại tùy chọn này. File DOCX và nội dung người dùng không bị lưu lại bởi probe.
