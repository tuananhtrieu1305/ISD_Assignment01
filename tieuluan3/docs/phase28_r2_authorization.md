# Phase28 r2 — phạm vi được người dùng đồng ý

Ngày 18/10/2026, sau biên bản `docs/phase28_export_incident_v1.md`, người dùng trả lời
**“có”** cho đề xuất triển khai revision r2: kiểm xuất NumPy CPU bằng native CPU độc lập,
giữ nguyên rtol=1e-4/atol=1e-5, lưu cả kết quả GPU/CPU gốc và khôi phục lượt đang dở
mà không train lại. Không coi GPU/CPU FAIL là PASS.

Giữ nguyên 90 selection, 52 source, mọi config/split/scaler/weights đã khóa. Bổ sung
strict native-CPU receipt thống nhất cho 108 RNN. Scratch CPU là kiểm round-trip cùng
manual engine, không gọi nó là framework độc lập thứ tư.

Lượt Power PyTorch seed17 đã mất telemetry cuối của process: bản ghi recovery riêng
dùng null cho original train wall/RAM/VRAM và loại khỏi các aggregate chi phí tương ứng.
Đo process khôi phục được lưu riêng, không thay thế số đo train. Phase22 schema không sửa.
Được tính lại validation từ đúng best checkpoint đã chọn, không chọn lại epoch/tuning.

Với lượt tương lai, runner vẫn gọi nguyên hàm train đã pin. Nếu chỉ final export assert
thất bại, finalizer r2 được lấy các biến đã tính từ đúng frame của hàm frozen, kiểm lại
completed optimizer snapshot/checkpoint và giữ nguyên native GPU predictions/telemetry.
Các AssertionError ở forward/gradient/train không đi vào finalizer. Mọi lỗi đều giữ log.

Không có thêm optimizer update cho lượt orphan, không đổi train kernel/cuDNN, không
nới tolerance, không thay kiến trúc/backend. TEST vẫn chỉ thuộc Phase29; không đổi UI/DOCX.
