# REORG Phase3 — COMPLETE (31/10/2026)

Đã hoàn thiện11 web riêng, đủ33 folder datasets/notebooks/web. Sáu assignment có giao diện nhẹ theo style demo mê cung; hai demo agent giữ dữ liệu/trace/hình gốc. Ba tiểu luận giữ React/Python theo đúng phiên bản: tiểu luận1 bốn chương, tiểu luận2 năm chương, tiểu luận3 sáu chương.

## Kết quả và kiểm chứng

- 22 nhóm ca trình duyệt PASS/0failure trên11 web;22 screenshot desktop/mobile. Kiểm18 tab dataset assignment, link notebook, lỗi input, so sánh CPU A01–A03, replay24bước/va tường Agent01, replay20bước/ba regime/20hình Agent02 và các job ML/CNN/RNN/LSTM/KG–RAG/agent trên UI tiểu luận.
- Ba frontend `tsc --noEmit`/Vite production build PASS. Tiểu luận1 cài đúng71 dependency theo lock cũ sau khi cache offline thiếu một gói; không nâng version hoặc thay hai venv GPU. Cache Node V3 đã có được gom về root node_modules.
- 11 test routing/security helper PASS: chặn file nội bộ/path traversal, giới hạn request, proxy JSON, source integrity. Ruff F/E9, parser PowerShell và scoped diff check PASS. Không gọi coverage này là coverage toàn bộ11 project.
- Ba serving bundle CPU có release/manifest/SHA và source parity; cả ba PASS từ source-only checkout không có raw/training cache/runtime views. Kiểm trên Linux WSL với interpreter hiện có; lượt staging trên NTFS bị timeout được giữ riêng, không đổi guard/threshold để vượt kiểm tra.
- 80.821dòng file gốc và19file Phase1 handoff đối chiếu byte/hash PASS. 61file Phase2 handoff cũng giữ hash. Các thay đổi web có snapshot trước sửa, không sửa raw, checkpoint, prediction, metric, TEST seal hay báo cáo đã nộp.

## Những thay đổi cần biết

A01–A03 có inference/compare CPU qua backend gốc. A04–A06 trình bày lại số liệu/dự đoán đã lưu; nhãn replay và nguồn được ghi rõ. Không gắn việc mở trang với training hoặc native GPU inference. Tiểu luận3/2 vẫn giữ compare-all ba bộ weights, serving thực tế NumPy CPU.

Demo tiểu luận1 trước đây lấy ảnh/sequence TEST. Revision web nay nạp mẫu TRAIN hoặc fixture; code thí nghiệm gốc và artifact giữ nguyên. Bốn service module được đặt trong `tieuluan1/src/term_paper/deployment/app/`. Các cảnh báo sklearn1.9.1→1.9.0 cũ vẫn được giữ, không re-fit/re-serialize.

Sau cleanup, recipe runtime Phase2 giữ bất biến; overlay Phase3 chuyển307 source reference sang vị trí bảo toàn/canonical mới, không thay target logic hoặc byte. Materializer hiện hành là `scripts/materialize_assignment.py`. Không dùng riêng helper Phase2 cũ sau khi bỏ web/reference. Các runtime views đã có vẫn được giữ để chạy notebook.

## Cleanup và cấu hình Render

Đã dọn root apps/,dist/,.ruff_cache, staging Phase1, staging Render/clean-checkout, unit temp và web/reference_ui, reference_backend, legacy_runtime thừa. Script chỉ xóa sau gate và kiểm không target nào chứa baseline bất biến. Lịch sử build root dist gồm3.968file được lưu vào một archive provenance, read-back SHA từng thành viên PASS. Giữ Git root, cả hai môi trường, tool/cache đang dùng, raw/model/report/evidence, backup web chưa commit và nested Git metadata.

Root render.yaml mặc định phục vụ tiểu luận3, đã đổi build/start/rootDir/filter; template riêng có trong từng web. Hai service Dashboard thủ công cần đổi Settings một lần; YAML không tự sửa chúng. Có shim scripts/render_v3.py cho lệnh API cũ. **Chưa commit/push/deploy hoặc thao tác tài khoản Render.**

Chạy web: [hướng dẫn11 bài](phase3_runtime.md). Deploy về sau: [bàn giao Render](render_handoff.md). Bằng chứng tổng hợp: verification.json, final_inventory.json và phase3_handoff.json. Không có DOCX mới cho tiểu luận2 trong lần sắp xếp này.
