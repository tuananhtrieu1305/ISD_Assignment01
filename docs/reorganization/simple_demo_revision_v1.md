# Demo đơn giản A01–A06 — revision 1, 03/11/2026

Yêu cầu: người dùng nhập thông tin, bấm kiểm tra và đọc kết quả. Bỏ JSON textarea, trình xem dữ liệu gốc, bảng metadata và biểu đồ huấn luyện khỏi luồng chính.

## Trạng thái từng bài

| Bài | Thao tác hiện hành | Kết quả |
|---|---|---|
| A01 | Nhập sáu thuộc tính tiểu đường hoặc sáu thuộc tính nhà | Năm mô hình chạy CPU trên input vừa nhập, kèm đồng thuận/khoảng giá |
| A02 | Nhập thuộc tính tiểu đường, nhà hoặc khách hàng | Năm mô hình ở hai bài đầu; sáu mô hình ở khách hàng |
| A03 | Nhập thuộc tính khách hàng, CDC hoặc nhà | Một Improved DNN đúng với registry backend hiện có |
| A04 | Chọn bài toán và chỉ số | So sánh kết quả tổng hợp đã lưu; chưa có dự đoán input mới |
| A05 | Chọn mẫu ảnh/CDC có output lưu sẵn | Bốn kiến trúc CNN trên cùng mẫu; hiển thị nhãn thật và từng dự đoán |
| A06 | Chọn khách hàng hoặc ngày dự báo | Keras/PyTorch; bài cổ phiếu có giá thực tế và baseline |

A04–A06 vẫn là replay theo quy tắc hiện hành. Muốn nhận ảnh, hồ sơ hoặc chuỗi mới và dự đoán thật ở ba bài này cần một revision serving riêng; sửa giao diện không tự tạo được endpoint model. Không giả lập kết quả cho input tùy ý.

Form A02 khách hàng và A03 dùng các thuộc tính chính; những thuộc tính ít dùng giữ mặc định từ fixture và có ghi số lượng dưới form. A03 giá nhà đưa bốn thuộc tính vốn null ra form, mặc định mặt tiền 5 m, đường vào 5 m, ba phòng ngủ, hai phòng tắm. Không sửa fixture khoa học gốc. CDC tuổi/thu nhập được ghi là nhóm, không giả định tuổi năm.

## Source và bảo toàn

- Entry point: `A01/web/index.html` đến `A06/web/index.html`.
- Giao diện dùng chung: `_shared/simple_demo/simple-demo.js` và `.css`, phục vụ qua route allowlist `/_demo-ui/` trong `scripts/web_app.py`.
- A05 bổ sung `web/demo-predictions.js` từ CSV dự đoán hiện có. Không tạo prediction mới.
- Chạy bằng `./scripts/run_web_gitbash.sh A01` trong Git Bash; thay tên bài để chuyển demo.
- Dùng runner ở root; static server chỉ trỏ vào một `web/` không phục vụ được asset dùng chung. Template Render static cũ không phải cấu hình triển khai của revision này. Chưa deploy.
- `release-reorg.json`, các receipt/lock cũ giữ nguyên. Index cũ tái tạo chính xác từ `_shared/web/index.html` bằng thay `__PROJECT__` với tên bài, UTF-8/LF. Verifier mới kiểm hash này theo từng release; các asset cũ khác giữ byte/hash trực tiếp. Không chạy lại producer lịch sử.
- Không sửa notebook, raw dataset, checkpoint, metric, prediction khoa học, kernel hay dependency. Không train, forward TEST, commit/push/deploy.

## Kiểm tra đã thực hiện

- `scripts/check_simple_assignment_demos.py`: form input/output, không textarea JSON, endpoint và baseline asset hashes.
- Syntax JavaScript: shared UI và A05 replay data PASS.
- A01 API thực: tiểu đường năm model và giá nhà năm model; E2E bấm form trả năm thẻ, có đồng thuận, không lỗi JavaScript. Receipt `artifacts/simple_demo_a01_e2e.json`.
- A02 API thực: tiểu đường năm, nhà năm, khách hàng sáu model.
- A03 API thực: ba bài toán Improved DNN. Giá nhà ban đầu HTTP 400 với null; input form đã điền hợp lệ trả HTTP 200, giá 8,536593272199418 tỷ đồng ở ví dụ đã kiểm.
- A04/A05/A06: browser kiểm toàn bộ tab, bấm xem output, đổi mẫu nếu có, không undefined/NaN, không lỗi JavaScript và không tràn ngang ở 390 px. Receipt `artifacts/simple_demo_a04_e2e.json` đến `a06_e2e.json`.
- Browser replay dùng HTML/JS/CSS/data thật đọc từ workspace và mock duy nhất `/health`; không gọi framework hay chạy model. Đây là kiểm UI, không phải kiểm WSL/server tích hợp mới.

Lượt kiểm WSL bổ sung bị sandbox từ chối quyền truy cập; yêu cầu nâng quyền sau đó không thực thi vì dịch vụ auto-review chạm giới hạn sử dụng. Vì vậy không nhận đã kiểm lại runner WSL cuối cùng cho A04–A06. Phần UI replay được kiểm độc lập bằng browser như mô tả trên; các API A01–A03 đã kiểm thành công trước đó.

Thiết kế dùng form và thẻ kết quả đơn giản; skill frontend-design được dùng để giữ bố cục đọc rõ ở desktop/mobile. Không áp dụng thêm dashboard hoặc phần trình bày huấn luyện vào luồng demo.
