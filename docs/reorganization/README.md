# Bàn giao sắp xếp11 bài

Phase1 đã COMPLETE; Phase2–3 chưa bắt đầu. Kế hoạch ở
[`../../ASSIGN_REORGANIZATION_EXECUTION_PLAN.md`](../../ASSIGN_REORGANIZATION_EXECUTION_PLAN.md).
Trạng thái tiếp tục: [`checkpoint.json`](checkpoint.json).

| File | Dùng để làm gì |
|---|---|
| [phase1_report.md](phase1_report.md) | Kết quả, giới hạn và việc cần làm tiếp |
| [source_inventory.json](source_inventory.json) | Nguồn/full commit của11bài và phân loại notebook |
| [migration_map.json](migration_map.json) | Bản đồ80.818file cũ→mới có SHA256; chưa áp dụng |
| [dataset_catalog.json](dataset_catalog.json) |24nhóm dữ liệu, kích cỡ/schema/path/hash và chỗ còn thiếu |
| [dependency_audit.md](dependency_audit.md) | Quyết định chọn phiên bản và phụ thuộc cần giữ |
| [runtime_matrix.md](runtime_matrix.md) | Hai kernel hiện tại và vấn đề tương thích code cũ |
| [web_matrix.md](web_matrix.md) | Nội dung/hành vi và ca kiểm tra11web |
| [phase1_verification.json](phase1_verification.json) | Kiểm SHA256 payload và kiểm tĩnh |
| [live_preservation_receipt.json](live_preservation_receipt.json) |42.939file hiện hành giữ nguyên |
| [phase1_handoff.json](phase1_handoff.json) | Digest19file bàn giao; giữ nguyên ở Phase2 |

`staging/<bai>/` là nơi phục hồi source lịch sử, giữ đường dẫn Git gốc bên trong từng bài,
không phải cấu trúc cuối. Ví dụ `staging/A05/A05/notebooks/` là đúng ở giai đoạn này;
Phase2 dùng mapping để chuyển thành `A05/notebooks/`.

`backups/uncommitted_web_and_controls.zip` giữ cả payload ignored và nested Git metadata của
web Agent01; không đưa metadata đó vào `agent01/web/` sau này. Hai thư mục staging/backups
được ignore để tránh commit raw/ảnh lớn. Các manifest và hướng dẫn không bị ignore.

Không chạy lại các script producer Phase1 vào evidence đã bàn giao. Nếu phát hiện sai sót,
tạo revision và giữ bản cũ. Kiểm handoff hash là đọc-only; kiểm source sau relocation cần resolver
theo map, không dùng đường dẫn cũ để kết luận mất file. Phase2 không chạy lại training/TEST.
