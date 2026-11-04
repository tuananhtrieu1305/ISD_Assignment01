# REORG Phase2 — COMPLETE (31/10/2026)

Đã đưa code vào 11 folder yêu cầu, đủ 33 thư mục datasets/notebooks/web. A01–A06 và tiểu luận1 lấy đúng nguồn Git Phase1; agent01/agent02 giữ source, báo cáo, output và hai web-demo chưa commit. Source V3 nằm trong tieuluan3; tiểu luận2 là revision Ch1–5, không có nhánh/menu/API multi-agent, vẫn giữ RNN–LSTM/KG–RAG. Tiểu luận3 giữ sáu chương.

## Bảo toàn

Đối chiếu SHA256/size **80,821 dòng file gốc** và **19 file Phase1 handoff** PASS. `canonical_map.json` phân biệt canonical revision với `baseline_path` bất biến. Notebook gốc/output, raw, checkpoint, metric, prediction, DOCX/PDF và seal vẫn giữ byte gốc. Không sửa seal, không train, không scientific TEST forward, không đổi env, không commit/push/deploy. Nested Git metadata Agent01 nằm trong provenance riêng, không thành submodule.

Layout tương thích có 145.483 alias tạo bằng hardlink/copy kiểm hash, không yêu cầu symlink/junction. Nó giữ tên module dùng bởi serialized artifact, gồm `term_paper` và `agent02_assignment`, trong khi entry point công khai dùng tên mới.

## Kiểm chứng

- 71 notebook chính schema/AST PASS; 374 Python AST PASS; 68,884 tham chiếu file dataset tồn tại/đúng kích thước.
- Run All 55 notebook kết quả/demo TRAIN/dry-run PASS; 16 notebook huấn luyện/EDA lịch sử kiểm tĩnh + checkpoint smoke riêng. Không gọi đây là đã train hoặc full Run All toàn bộ notebook huấn luyện.
- 14 helper test PASS; coverage tổng helper **87.40%**. Không suy rộng coverage này sang toàn bộ 11 bài.
- TypeScript `--noEmit` của React tiểu luận2 PASS với dependency cache đã có; Python lint migration helper, parser PowerShell và scoped `git diff --check` PASS. Build sản phẩm và E2E vẫn thuộc Phase3.
- Smoke riêng đủ 11 bài: A01/A02 năm model diabetes; A03 ba golden pipeline (sai số <1e-6); A04 năm checkpoint mỗi native framework; A05 12 Keras checkpoint; A06 hai RNN mỗi framework trên window TRAIN; tiểu luận1 bốn asset; AG02 70 input sealed; Agent01 maze/BFS; API tiểu luận2/3 readiness và fixture/TRAIN inference.
- CIFAR binary adapter parity pixel/nhãn chính xác trên tám ảnh TRAIN; canonical archive giữ hash. A06 Git LF/Windows CRLF có hàng CSV giống hệt; chỉ view dùng bản CRLF để thỏa guard cũ.
- Notebook CNN/RNN/LSTM tiểu luận dùng serving registry pin seed42 vì demo thí nghiệm cũ đòi Git HEAD lúc train. Đây là revision có khai báo; code/guard/lock cũ giữ nguyên. Backend demo thực tế NumPy CPU, không báo latency như native GPU.

## Các điều chỉnh đã ghi bằng chứng

Schema import tabular A04 cần PROJECT_ROOT ngoài nhánh train; A05 bỏ guard đường dẫn Anaconda ở revision notebook; A04/A06 tách notebook mixed-framework để không cài trộn env. Một archived AG02 notebook được phục hồi nguyên byte khi bootstrap ban đầu chọn nhầm. README dataset V3 gốc được phục hồi exact hash từ Git vào provenance; canonical catalog README là file mới. Lỗi phát triển/attempts giữ trong journal, receipt PASS cuối luôn gắn SHA revision hiện hành.

## Chạy và bàn giao

Xem [hướng dẫn kernel/lệnh chạy](phase2_runtime.md), README từng bài và [bản đồ repository](../repository_manifest.md). Hai env WSL hiện có được tái sử dụng; runner chọn interpreter/kernel và không cài dependency. `datasets/catalog.json` chỉ rõ đường dẫn thật; dữ liệu/checkpoint lớn ignored/local cần giữ khi chuyển máy. Metadata/manifest được version, payload không tự có trong clean checkout.

Source web đã đúng nơi; build/serve/E2E, sửa notebook download, Render entrypoint/bundle và dọn cache/source cũ thuộc **Phase3**. Không khẳng định 11 web đã nghiệm thu. Chưa dựng DOCX tiểu luận2. Legacy node_modules/dist ở apps/web, staging/backup vẫn được giữ đến gate Phase3. Lệnh tiếp theo: `làm phase 3`.
