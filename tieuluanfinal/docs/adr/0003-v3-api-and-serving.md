# ADR 0003 — Flask monolith, job polling và native backend có nhãn

Trạng thái: ACCEPTED, 2026-10-17. API implementation thuộc Phase 32.

## Quyết định

Giữ Python Flask, React và style nguồn hiện có; không thêm microservices/GraphQL
hoặc queue cloud. Định nghĩa `/api/v3` để không phá envelope/endpoint V2. Dùng
OpenAPI 3.1.1 + JSON Schema 2020-12 với refs local; snake_case body, resource URL
plural, bounded pagination, 202 job + polling/cancel/idempotency và lỗi có cấu trúc.

Framework adapter ở process/env riêng; run-all tuần tự cùng input hash để tránh
giữ ba framework trong VRAM. Job có slot cho mọi implementation kể cả failed/unavailable.
Input/file/artifact path không được chọn tool/command tùy ý; artifact hash mismatch
không làm process startup crash-loop. Public demo không có train/TEST/admin endpoint.

SQLite/working directory local đủ cho job metadata single-worker; khi restart,
running job chuyển failed với worker_restarted. Render disk ephemeral không cho
cam kết persistence qua redeploy. Nếu cần durable queue/store phải có ADR và quyền mới.

## Render và trade-off chưa được đo

Training offline GPU; deploy CPU inference từ checkpoint đã khóa, lazy-load/process
sequential. Không hứa cả TensorFlow và PyTorch native vừa RAM gói Render miễn phí.
Phase 32 đo memory/latency theo gói thật. Nếu phải chọn gói trả phí/hosting khác,
xin người dùng. Không tự thay bằng portable NumPy rồi ghi timing framework native.
Model chưa chạy được phải có trạng thái rõ, không giả dự đoán để đủ ba cột.

## Kiểm chứng

Phase 22 kiểm tra schema/reference/request/job completeness bằng synthetic fixtures.
Phase 32 triển khai API/security/integration/CPU-load tests; Phase 33 E2E deep-link,
run-all/partial failure/refresh. Không sửa app đang chạy trong Phase 22.
