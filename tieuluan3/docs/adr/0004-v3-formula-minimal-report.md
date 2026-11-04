# ADR 0004 — Lý thuyết dễ hiểu nhưng không bỏ thuật toán cốt lõi

Trạng thái: ACCEPTED, 2026-10-17.

## Quyết định

Giữ văn phong/style mẫu V2/A06; khóa sáu chương trong `report/outline_v3.json`.
Deploy chỉ là mục ngắn cuối Ch2–6. Ch4 có RNN và LSTM thật, Ch5 giữ kết quả và
chuyển Agent thành cầu nối sang Ch6; không sửa nội dung cũ bằng cách đổi tiêu đề.

Trực giác/ví dụ/sơ đồ đi trước công thức. Chỉ giữ công thức phục vụ scratch hoặc
metric thật, có symbols/why_needed/plain_explanation/example trong function contract.
Chi tiết chứng minh/derivative dài đặt phụ lục. Hợp hàm luôn có sơ đồ bằng lời và
shape; từng hàm có mapping ba implementation. Một nguồn contract cho report và UI.

## Hệ quả

Budget trang là dự kiến, không nhồi code để đủ trang. Không bỏ loss/backward/cổng
LSTM cần thiết chỉ để ít toán. Không dùng synthetic schema fixture làm số liệu báo
cáo. DOCX chỉ build khi artifact thật có đủ provenance, render kiểm tra toàn bộ trang
và không ghi đè baseline. Thẩm định khả năng đọc hiểu vẫn cần review biên tập ở 34–35;
schema không tự chứng minh văn phong đã tốt.
