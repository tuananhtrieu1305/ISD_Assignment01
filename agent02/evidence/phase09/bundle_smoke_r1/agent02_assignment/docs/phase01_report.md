# Biên bản Agent02 phase 1

Ngày 24/10/2026, Asia/Bangkok. Phạm vi: chuẩn bị workspace và khóa nguồn,
không triển khai thuật toán mới hoặc chạy thí nghiệm RL.

## Đã thực hiện

- Đọc toàn bộ plan, checkpoint và quy tắc cục bộ trước khi làm.
- Cập nhật plan v1.1, AGENTS và requirements với U01/U02 theo lưu ý mới: lý thuyết
  ngắn/dễ hiểu, chỉ công thức cần, mọi biểu đồ phải được phân tích rõ.
- Chuẩn bị thư mục code/config/notebooks/data derived/artifacts/report/output riêng.
- Copy byte-identical 6 file nguồn; PDF và `.tex` gốc không thay đổi.
- Tạo `code/agent02_experiment.py` exact-byte, SHA-256
  `3d40be4edc925f83b403c0b7e71e7fff03dfe0dbed56f0895c192058a4865ca9`.
- Parse AST và compile: 966 dòng, 4 class, 12 function. Không exec/import reference.
  Đọc được defaults từ AST, không chạy dataclass hay main của chương trình thầy.
- Kiểm versions package đúng snapshot cũ trong Python 3.11.17, Ubuntu/tuananh.
- Notebook probe thực thi đủ 2 cell: đúng interpreter, NumPy 2.4.6, Matplotlib 3.11.2,
  array sum 6. Không biểu đồ, không training step, không scientific evaluation.
- Launcher PowerShell chỉ có preflight/inspect-reference, không cho chạy train sớm.
- README có lệnh cụ thể; chưa cài/nâng package, chưa chỉnh môi trường GPU/uv.lock.

## Kiểm thử

TDD: giữ `tests_red.xml` cho lỗi module chưa có; test trước implementation.
Nghiệm thu cuối: **29 test PASS, 0 skip** (`final_tests_r2.xml`).
Coverage statement+branch của **workspace.py**: **99,115044%**; 75 statement đều phủ,
38 branch với một nhánh chưa phủ. Không gán coverage này cho phase01 orchestrator,
notebook UI hoặc mô hình RL của thầy. Có integration CLI thực, source hash và
notebook execution checks, không có browser/web nên không cần Playwright.

Ruff source mới/tests PASS; reference nguyên byte được loại khỏi format/lint-fix.
PowerShell launcher được kiểm parser và chạy thực preflight/inspect-reference.

## Sự cố probe và xử lý

Lượt đầu lỗi secure_write: DrvFS không đáp ứng 0600 cho file kết nối Jupyter.
Đã giữ receipt lỗi, không nới bảo mật. Dùng thư mục tạm Linux riêng cho connection
và caches trong lượt sau, tự dọn khi kernel đóng. Probe thành công không thay env.
Probe cũ PID 910 không thoát sau SIGTERM; sau xác minh command/không có child,
đã dừng đúng PID bằng SIGKILL. Không tác động process khác.

Kernel cảnh báo TCP không mã hóa; đây chỉ là kernel cục bộ tạm thời, không server
công khai, không dữ liệu nhạy cảm. Không dùng probe làm bằng chứng security/cloud QA.

## Bảo toàn và giới hạn

Kiểm hash 7 đầu vào chọn trước trước/sau: CDC CSV, Ames TXT, Gold XLSX, MedQuAD README,
biên bản Phase31, notebook bài trước và uv.lock — đều không đổi. Đây là kiểm phạm vi
đã liệt kê, **không** tuyên bố audit lại toàn bộ hàng chục nghìn file khóa V3.
Sáu tài liệu gốc được kiểm lại qua preflight. Không train/tuning/TEST V3 hoặc bài trước.

Code thầy vẫn có default `agent02_results` tương đối. Không chạy trực tiếp;
phase 2 mới làm guarded runner và protocol. Chưa sinh kết quả kinh doanh/RL, chưa
thực hiện Gold calibration, chưa build PDF/DOCX.

Metadata nhóm/tên file nộp chưa xác nhận, không chặn phase code.
Bước tiếp theo: **làm AG02 phase 2** — environment, agents, protocol và test trước train.
