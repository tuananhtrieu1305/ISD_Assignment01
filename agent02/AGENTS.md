# Quy tắc agent02 sau migration

Kế hoạch đang hoạt động: `../ASSIGN_REORGANIZATION_EXECUTION_PLAN.md`; checkpoint ở `../docs/reorganization/checkpoint.json`. User đã cho phép REORG đổi path và dùng runtime WSL hiện có, thay các chỉ dẫn Anaconda/tên folder cũ trong lịch sử. Không train/TEST lại, không cài/nâng dependency hoặc sửa evidence/raw/checkpoint đã khóa.

Mã gốc/README/AGENTS và notebook cũ nằm trong provenance, còn `project.json` và README mô tả đường chạy mới. Runtime view là alias được tạo bằng hardlink hoặc copy có kiểm hash, không là bản source được chỉnh độc lập. Sửa code đã khóa cần revision và giữ original.

Không tự commit/push/deploy. Phần web tích hợp thuộc Phase3; không đổi nội dung/byte báo cáo đã nộp.
