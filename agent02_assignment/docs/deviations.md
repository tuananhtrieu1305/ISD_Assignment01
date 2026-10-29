# Nhật ký điều chỉnh

## 24/10/2026 — plan v1.1 theo yêu cầu người dùng

Bổ sung U01: lý thuyết ngắn, đủ ý, dễ hiểu, chỉ công thức cần thiết.
Bổ sung U02: giải thích rõ mọi biểu đồ output. Không đổi mô hình, budget hoặc nguồn.
`evidence/planning_verification.json` vẫn giữ hash của plan v1.0 như chứng cứ lịch sử;
không sửa receipt cũ để khớp plan mới được người dùng yêu cầu.

## 24/10/2026 — notebook probe trên DrvFS

Attempt 1 thất bại trước khi khởi động kernel vì Jupyter đòi connection file mode 0600,
DrvFS báo 0677. Không tắt secure_write hoặc bật insecure writes. Attempt sau dùng
TemporaryDirectory riêng trên filesystem Linux cho connection/IPython/MPL cache và
xóa khi đóng kernel. Không cài environment/package mới, không chạy reference program.

Probe chỉ chạy hai cell kiểm interpreter và imports/NumPy. Cảnh báo TCP không mã hóa
của ipykernel được giữ công khai: kernel cục bộ tạm thời, không mở Jupyter server
công khai và không chứa dữ liệu cá nhân/credentials. Không gọi đây là cloud/network QA.
Process probe lỗi PID 910 đã được xác minh đúng command và gửi SIGTERM; không dừng
process ngoài task. Bằng chứng lỗi: `evidence/phase01/notebook_probe_attempt1.json`.

## Reference code

Giữ bản Python byte-identical của file thầy; không format/lint-fix reference để giữ
khả năng đối chiếu. Code mẫu có output mặc định tương đối `agent02_results`; không
chạy trực tiếp từ root. Phase 1 launcher chỉ inspect/preflight; runner train có
output path riêng và protocol chỉ được triển khai ở phase 2.
