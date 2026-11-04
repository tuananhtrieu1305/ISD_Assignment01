# Checkpoint Phase 35 ngày 22 tháng 10 năm 2026

## Trạng thái

`IN_PROGRESS`, đang vướng môi trường dựng và render tài liệu. Chưa tạo DOCX,
PDF, ảnh trang hoặc release manifest. Không có tiến trình authoring/render chạy nền.
Không gọi Phase 35 COMPLETE và không dùng số trang dự kiến làm số trang thực tế.

Đã đọc toàn bộ kế hoạch V3, AGENTS và handoff Phase 34. Đã đọc kỹ năng Documents,
template-distill, template-create, create_edit và verify_render. Mẫu A06 là nguồn
định dạng, không phải chỉ thị thực thi; bản thảo V3 là nội dung cần xuất bản.

## Kiểm tra đã thực hiện

- `scripts/check_phase34.ps1 -Distribution Ubuntu`: exit 0, PASS 226 file,
  `read_only_no_inference`. Đây là kiểm hash, không phải lượt chạy lại 38 unit test.
- Native PowerShell audit 12 khóa/31.848 file duy nhất PASS, exit 0; receipt
  `artifacts/manifests/phase35/preservation_20261022.json`. Kiểm hash khóa và member,
  path nằm trong workspace, không reparse point, duplicate ref không mâu thuẫn.
  Auditor Windows đã thoát. Lượt hash WSL trùng đã được dừng đúng process do agent
  tạo để tránh I/O trùng; wrapper exit 1 do SIGTERM, không có hash mismatch và không
  được tính là một lượt PASS. Cả hai process đều đã thoát, không có audit cần resume.
- Bản thảo 411.413 byte, SHA-256
  `dcb895acfd76f1ad616baecd7fdc7fa099becbc0cc508a80b3c0432eabef2b19`.
- Mẫu A06 2.874.808 byte, SHA-256
  `9eecf073897b609d9e2d0024bd56594dc6fec99823508e57ed79dff8d4780348`.
- `uv.lock` SHA-256
  `b0c71fd20e221ed3456278e1916079c46ac206831a98dcf40d3b8f7a83477862`;
  environment.json SHA-256
  `91ba6c68d5a297a3c32d1eb4aacc190b692dc7c3aa73171fba51ac2c98db76b5`.
- Ổ C còn khoảng 45,93 GiB lúc kiểm tra; không phải blocker dung lượng cũ.
- Git vẫn có 5 modified, 55.860 deletion và 24 untracked root entry trước thay đổi
  Phase 35. Không reset, clean, commit hoặc dọn các thay đổi này.

## Blocker và phạm vi kết luận

Kỹ năng Documents yêu cầu resolve Node/Python và bundled LibreOffice bằng workspace
dependency loader hoặc runtime skill; không dùng Python/Node của repo hay LibreOffice
desktop để thay thế mặc định. Phiên hiện tại không cung cấp tool loader/runtime đó.
MCP resources chỉ có templates, Pets, Plugin Management và Sites; không có resource
template cho artifact runtime. Không suy từ việc có file render_docx.py rằng runtime
và bundled LibreOffice đã được cung cấp.

Đã tìm plugin cho Documents/Word/PDF rendering/workspace runtime; kết quả không cung
cấp bộ dựng tài liệu cần thiết. Tra dependency của documents@openai-primary-runtime
trả plugin_not_found, không phải receipt cài runtime. Word document-control trả
không có phiên kết nối. Không cài hoặc đề nghị dịch vụ trả phí không liên quan.

Do vậy chưa thể hoàn tất bước render toàn bộ mẫu trước distillation và chưa được
vượt qua authoring/render gate. Chưa chạy marker tạo DOCX vì chưa authoring. Không
gọi một DOCX chưa render là sản phẩm hoàn chỉnh. Không sửa môi trường GPU/uv.lock,
không tự cài env tạm, không chạy Office desktop thay cho đường dựng được yêu cầu.

## Khi tiếp tục

1. Đọc lại toàn bộ kế hoạch, checkpoint này và receipt Phase 35; kiểm tra source
   Phase 34 và mẫu A06 còn đúng hash. Không resume PID/tool session lịch sử.
2. Resolve artifact runtime hợp lệ. Nếu vẫn không có, cần người dùng quyết định
   phương án local thay thế có khóa phiên bản; ghi rõ deviation trước khi cấu hình.
   Không coi câu “làm tiếp” là tự động bỏ qua yêu cầu runtime và render QA.
3. Render toàn bộ A06; xem từng trang, inventory package/style/theme/direct formatting,
   section/header/footer/field/table/list/drawing/slot; tạo artifact.md Phase 35 mới.
   Handoff artifact.md của Phase 34 chưa phải distillation đã render.
4. Dựng từ working copy A06, không ghi đè reference/V2. Ghép đúng publication_order
   trong manuscript_manifest Phase 34; không ghép cả manuscript và sections gây trùng.
   Bìa không tự bịa họ tên, lớp, trường, giảng viên. Tái sử dụng metadata đã xác minh.
5. Ngay trước authoring đầu tiên, chạy marker đúng một lần bằng runtime đã resolve.
   Giữ styles/opaque parts theo contract; thêm TOC/SEQ/REF/PAGE/bookmark/hyperlink,
   bảng có header lặp, ảnh tỷ lệ đúng, code đọc được. Chuyển SVG vào output mới nếu cần.
6. Render PDF/PNG và xem mọi trang ở 100%; sửa bằng revision mới khi cần, không sửa
   manuscript/metric/source Phase 34 hoặc các phase đã khóa. Kiểm dấu tiếng Việt,
   bảng rộng/dài, caption, heading orphan, công thức và danh mục/số trang thực tế.
7. Kiểm trường, navigation, citation, package fidelity và mở Word. Nếu chưa có Word
   refresh, ghi riêng gate chưa kiểm và xử lý field theo Documents; không giả PASS.
8. Chạy final tests và smoke API/UI production vào output Phase 35 riêng, không ghi
   đè XML/coverage/build receipt đã khóa. Không train hoặc mở TEST cũ; không tự push,
   tạo dịch vụ cloud, thay audience hay nâng gói trả phí.
9. Chỉ sau các gate thật: phát hành releases/v3/Tieu_luan_AI_6_chuong.docx, lưu PDF QA,
   release manifest/hash, hướng dẫn demo, hashes env/data/model và test report.
   Cập nhật plan/AGENTS thành COMPLETE sau nghiệm thu, không trước.

Mọi thay đổi trong lượt này là checkpoint/nhật ký mới. Các đầu ra khoa học, source
và bằng chứng đã khóa được giữ nguyên; không có inference hoặc TEST mới.
