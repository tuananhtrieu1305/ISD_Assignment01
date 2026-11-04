# ADR 0001 — Một nguồn đặc tả, hai env backend

Trạng thái: ACCEPTED, 2026-10-17. Phạm vi: V3 Phase 22 trở đi.

## Bối cảnh

V2 source đã được dọn/migrate, nhưng notebook và builder lịch sử còn đường dẫn
cũ. GPU đã được kiểm tra ở Phase 21. Cần tránh tạo thêm bản sao notebook/venv.

## Quyết định

Kế hoạch V3 điều hành; SRS + protocol/outline/schemas là đặc tả triển khai. Source
`src/`, API/web `apps/`, notebooks mỏng `experiments/`, báo cáo `report/`. V2, raw
Ch5/config/metrics/TEST chỉ đọc. Giữ namespace bridge `term_paper` cho serialized artifacts.
WSL Ubuntu/Python 3.11.17 + uv lock; PyTorch CUDA và Keras/TensorFlow ở env riêng.
Backend/device thực ghi trong mọi run. Keras torch chỉ khi probe thật thất bại,
có log/deviation; không nhận là TensorFlow độc lập.

## Hệ quả và lựa chọn loại bỏ

Không dùng lại venv Windows/Anaconda hoặc copy thuật toán vào từng notebook.
Không tự compile framework/đổi driver hay cài dependency không khóa. Không rewrite
Git history để che worktree migration. Chưa di chuyển raw sang filesystem Linux
hoặc tạo bản sao dataset; Phase 23 quyết định storage có provenance trước tải.

## Kiểm chứng

Phase 21 manifest/lock vẫn khớp; phase22 schema audit resolve offline; preservation
verifier giữ V2/Ch5. Mọi đổi hợp đồng phải tăng version hoặc ghi deviation trước TEST.
