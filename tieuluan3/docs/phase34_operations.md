# Vận hành bản thảo Phase34

Nguồn hiện hành: `report/active_manuscript_v3.json`; bản đọc liền mạch:
`report/phase34/manuscript.md`. Source chương22–33 nguyên vẹn, tích hợp tạo file mới.
Publication_order trong manuscript_manifest chỉ rõ thứ tự front matter/danh mục/
Mở đầu/sáu chương/Kết luận/references/phụ lục. Không ghép cả manuscript và sections
vào cùng DOCX vì sẽ nhân đôi nội dung.

Sau release, chỉ kiểm hash:

```powershell
.\scripts\check_phase34.ps1 -Distribution Ubuntu
```

Không chạy build_phase34, prepare writers, coverage hoặc review writer vào tên đã
khóa. Chúng chỉ phục vụ phát triển trước release và từ chối ghi đè sau khóa. Nếu
phát hiện lỗi nội dung, tạo revision mới giữ bằng chứng/bản cũ; không thay metric,
TEST seal, checkpoint hoặc nguồn đã khóa để sửa cách trình bày.

Tooling34 là standard-library Markdown/JSON/AST reader; không model construction,
framework GPU import hoặc TEST forward. Runtime Python vẫn Ubuntu/user tuananh qua
run_experiment, không dùng Python Windows hoặc bootstrap/doctor cũ. Rerun integration
trước release chỉ viết lại output Markdown của chính Phase34, không phải tái đánh giá.

Các gate chưa làm: dựng DOCX/PDF, phân trang, cập nhật TOC/SEQ/REF/PAGE, render từng
trang, mở Word và cloud deploy thực. Source style A06 đã trích XML read-only; đây
không phải full template distillation đã render. Workspace dependency loader/bundled
renderer không có trong tool hiện hành; không tự gọi Office desktop hoặc cài env
tạm để coi gate đã đạt. Khi Phase35 bắt đầu, đọc documents skill hiện hành, resolve
runtime/bundled renderer hợp lệ và hoàn tất render gate trước khi giao Word.

Editor/assembler/auditor được unit/integration/end-to-end text audit với coverage
riêng ba module mới; đây không phải coverage toàn repo, model hoặc Word rendering.
XML RED/development/r1/r2 giữ làm lịch sử; chỉ acceptance-tests-r3.xml được cộng
nghiệm thu. Lint-r3.json và acceptance_coverage_r3.json là evidence active; xem
phase34_acceptance_revisions.md. Integration test r3 chỉ viết fixture tạm do test sở hữu.
Traceability ghi CONTENT_AND_PRIOR_EVIDENCE_LINKED, không khẳng định tất cả54yêu cầu
đã đạt end-to-end. Requirement DOCX/render deferred35, Render chỉ local evidence.

Không có tiến trình train/TEST/API/UI do Phase34 tạo. Nếu audit parent bị ngắt trước
receipt, kiểm đúng process prepare_phase34 trước khi chạy lại; không ghi đè receipt
đã có. Sau lock, scripts.verify_phase34 --stage verify-only là đường đọc an toàn.
