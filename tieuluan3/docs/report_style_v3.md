# Quy tắc lý thuyết và trình bày V3

Người đọc mục tiêu: sinh viên biết lập trình và toán đại cương. Viết câu ngắn,
thuật ngữ tiếng Việt kèm tên Anh lần đầu; đủ ý, không viết như giáo trình chứng minh.

## Khuôn một mục kiến thức

1. Dùng để làm gì? Một bài toán cụ thể.
2. Trực giác bằng lời, không mở đầu bằng ký hiệu.
3. Một input/output ví dụ có thật hoặc ghi rõ synthetic.
4. Sơ đồ luồng đơn giản và shape tại các bước quan trọng.
5. Vai trò từng thành phần; liên hệ implementation bằng signature/function ID.
6. Công thức tối thiểu nếu không có sẽ khó hiểu code.
7. Kết quả được đánh giá bằng gì? Hạn chế và trường hợp không nên dùng.

Ví dụ RNN: “Mỗi bước đọc thêm một quan sát và cập nhật phần tóm tắt lịch sử”.
Ví dụ LSTM: “Bộ nhớ có các cổng quyết định phần nào giữ, ghi thêm và đưa ra ngoài”.
Sau trực giác mới đưa phép cập nhật cần để đọc code scratch. Không nói cổng LSTM
là ba layer độc lập để đủ yêu cầu độ sâu.

## Checklist cho từng công thức

- [ ] Có câu hỏi cụ thể mà công thức giúp trả lời; không chỉ để trang trí.
- [ ] Có `why_needed`, `plain_explanation` và ví dụ số hoặc tensor shape.
- [ ] Mọi ký hiệu có tên, ý nghĩa, kích cỡ/đơn vị khi liên quan.
- [ ] Có mapping tới code/function contract hoặc metric đang sử dụng.
- [ ] Người đọc hiểu được vai trò bằng lời trước khi đọc biểu thức.
- [ ] Không suy diễn vi phân nhiều bước trong chương chính.
- [ ] Nếu chỉ phục vụ kiểm chứng chi tiết: chuyển phụ lục kỹ thuật và đặt cross-reference.

Danh sách công thức có thể cần: dự đoán Dense/activation, loss, optimizer update,
convolution, recurrent state, các cổng/cell state LSTM, metric thật sự báo cáo.
Không phải yêu cầu phải chèn tất cả. Hợp hàm `F = f_L ∘ ... ∘ f_1` được giải thích
một lần và luôn có “đầu vào → các bước xử lý → đầu ra”. Với RNN/LSTM, sơ đồ phải
phân biệt chiều thời gian với chiều tầng.

## Một bảng giải thích hàm

Function ID; signature; mục đích; input/output + shape; tham số học được; edge case;
mapping scratch/Keras/PyTorch; công thức nullable. Nếu `formula` không null, schema
bắt buộc expression/symbols/why_needed/plain_explanation/example. Không đưa toàn
bộ code training vào thân chương; trích phần cốt lõi, link source đầy đủ trong repo.

## Dữ liệu, kết quả và hình

Mỗi data card có link, license/citation, bytes/logical size, schema, 3–5 mẫu
input/output đại diện, phân bố, missing/imbalance, nhận xét và giới hạn. Ảnh y khoa
không nhận diện người; metadata không có không được suy đoán. Ch1 ImageNet dùng
metadata/hình minh họa có nguồn, không tạo thống kê local khi không tải full.

Mỗi bảng/hình có caption, đơn vị, dataset/split/track/seed/device và artifact ref.
Phân biệt số công bố, số đo local, synthetic fixture, validation và TEST. Không
gộp kết quả khác track hoặc dùng ví dụ schema làm kết quả thực nghiệm. Undefined
metric viết “không xác định” với lý do. Ch5 dùng metric đã khóa, không “cập nhật”
bằng lần chạy mới. Nhận xét phải dựa vào số, có cả kết quả âm/failure/limitation.

## Style DOCX và budget

Tái sử dụng hệ heading, caption, font và giọng mẫu V2/A06 khi chuyển builder ở 34–35.
Trang bìa/mục lục/danh mục hình-bảng/tài liệu tham khảo/cross-reference phải liên tục.
Không ghi đè V2. Outline và budget nằm trong `report/outline_v3.json`; không tự
thêm chương deploy. Cuối Ch2–6 chỉ mô tả ngắn: đóng gói, demo/API, CPU/GPU, hạn chế
và artifact version; hướng dẫn vận hành dài đặt README/phụ lục.

## Kiểm tra biên tập ở Phase 34–35

- Mỗi mục trả lời “dùng để làm gì?”, “dữ liệu đi qua thế nào?”, “đánh giá ra sao?”.
- Mỗi công thức qua checklist; mọi thuật ngữ/ký hiệu lần đầu được giải thích.
- Mọi số liệu/citation/link truy nguồn được; không còn placeholder hoặc claim chưa đo.
- RNN và LSTM đều đủ lý thuyết, code ba loại và kết quả, không chỉ đổi tiêu đề Ch4.
- Multi-agent là Ch6 riêng; Agent Ch5 chỉ là cầu nối ngắn.
- Render từng trang, kiểm tra overflow/orphan/table/image/caption và độ đọc code.
