# AG02 Phase 8 — sửa một liên kết điều hướng

Sau khóa nội dung v1, kiểm tra đường dẫn phát hiện bảng đối chiếu Markdown dẫn tới
`phase 08/manuscript.md` thay vì `phase08/manuscript.md`. Hàm thêm khoảng trắng cho
văn xuôi đã tác động vào đích liên kết tương đối. File gốc đã khóa được giữ nguyên.

Bản hiện hành `report/question_evidence_matrix_r2.md` chỉ thay đúng một đích liên
kết; các câu, bảng, số đo, locator và bản thảo không đổi. Dùng bản r2 ở Phase 9.
JSON matrix tại `report/phase08/question_evidence_matrix.json` vốn đã đúng đường dẫn.

`verify_phase08_presentation_r2.py` kiểm 31 file khóa v1, phép thay byte duy nhất
và đủ 21 liên kết local: một link bản thảo, 20 link hình. Khóa revision ở
`evidence/phase08_presentation_r2/`. Không chạy lại train/final hoặc sửa compiler,
helper, kiểm thử, tài liệu hay số liệu đã khóa. 234 test và 101 phép đối chiếu số
học của nghiệm thu v1 vẫn áp dụng; sửa link không tạo thêm kiểm thử mô hình.

Kiểm chỉ đọc trong runtime cũ bằng module
`agent02_assignment.verify_phase08_presentation_r2`, không thêm `--seal`.
File `report/active_report.json` điều hướng tới bản thảo v1 và matrix r2; nó là
metadata mutable ngoài hai khóa. Chưa dựng hoặc kiểm trang DOCX/PDF ở Phase 8.
