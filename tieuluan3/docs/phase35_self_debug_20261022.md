# Phase35 — ghi nhận tự chẩn đoán và phục hồi có giới hạn

## Failure Capture

Mục tiêu: một DOCX sáu chương đúng source, không thay scientific locks/GPU runtime.
Lỗi cụ thể: test đầu thiếu module (RED dự kiến), metadata apt encoded URL/duplicate;
blank cover paragraph thiếu pPr; test bắt32caption chỉ có trong alt text; bibliography
có nhiều backslash; Word Quit yêu cầu PSReference; công thức LSTM82ký tự vẫn tràn.
Log/XML development_r1/r2 giữ nguyên, không gọi đó là nghiệm thu PASS.
Không lặp train/TEST. Có các log khá dài đã được giới hạn lại theo từng lỗi.

## Root-Cause Diagnosis

- Logic: ngưỡng wrap90không bắt công thức82ký tự nhưng rộng hơn vùng in.
- Source pattern: ảnh có caption alt khác ảnh có đoạn caption, Ch6 dùng strong/multiline.
  Ledger Ch6 chỉ giữ dòng đầu; không dùng ledger thay cho phần note đầy đủ của source.
- Interop: Quit nhận optional Variant by-ref; cleanup đầu tiên ngắt trước receipt.
  Word còn đúng một process automation ẩn, không có document. Không phải user Word.
- Scope: Options.UpdateLinksAtOpen là thiết lập ứng dụng không cần đổi để đọc tài liệu
  chỉ chứa embedded media và hyperlink. Hai probe đầu gán false; không lưu giá trị trước,
  nên không thể chứng minh khôi phục giá trị ban đầu. Không tự đoán giá trị để đảo lại.

## Recovery Action

- Giữ ứng viên cũ; sửa helper mới, thêm test đúng biểu thức thực, wrap55ký tự/left align.
- Defer caption khi ngay sau ảnh có caption thật (kể cả strong), giữ toàn bộ multiline note;
  chỉ lấy ledger cho ảnh thiếu đoạn caption. Không sửa Phase34 hoặc số liệu.
- Word dùng by-ref; cleanup try/finally riêng. Process23384 được xác minh commandline
  /Automation -Embedding, hidden, documents0 trước khi Quit không save. Không Stop-Process.
- Bỏ hẳn thao tác Options.UpdateLinksAtOpen khỏi script mới. Không khẳng định thiết lập
  người dùng đã hoàn nguyên khi không có before snapshot. Có thể vẫn đang false.
- Cache textpage một lần/trang để tránh đọc lại PDF nhiều trăm lần cho page-map.

## Agent Self-Debug Report

Kết quả hiện tại: Word16 mở r2 PASS203trang/144bảng, source hash giữ nguyên; process đã thoát.
46development test PASS trước sửa wrap thực. Render r3 phát hiện thêm overflow và marker
Markdown trong caption; r4 phải kiểm lại, chưa gọi final QA PASS.
Ngăn lặp: full-source integration, bookmark-span test, actual-expression wrap test;
không retry installer/rerun scientific TEST hay ghi đè receipt cũ để làm sạch log.
Follow-up: final render/visual QA/tests và báo rõ phạm vi Word read-only validation;
không gọi Word-open là kiểm tra hình ảnh mọi trang trong Word.

## Hậu kiểm trình bày và unit fixture cuối

R7 page22 cho thấy import SVG bằng PyMuPDF không áp dụng CSS class nên card đen.
Đã raster bằng Chromium offline có kiểm source hash; SVG gốc không đổi. R8 có hàng
bảng tách phần nhãn sang trang sau trong khi số nằm trang trước; bộ xuất thêm cantSplit
cho hàng thông thường, cho phép hàng rất dài chảy và không dùng exact height.
R10 page103/104 lộ hai fragment TeX của Ch5: chuyển hẹp sang OMML/Unicode trước parse,
có RED/GREEN riêng. R11 page132 còn escape tên Vrandečić/Krötzsch/Büttcher; chuẩn hóa
trình bày theo đúng tên nguồn, giữ nguyên bibliography Markdown và các phần đã khóa.

Ứng viên r12 đã xem đủ202trang:131trang đầu carry từ review thật chỉ sau khi từng PNG
khớp SHA-256;71trang cuối xem riêng. Không masking/footer-ignore hoặc suy ra PASS từ
contact sheet. Word16 read-only r12 PASS202trang, fields first error index0, hash giữ nguyên.

Final test r1 giữ79PASS/1FAIL: test mới hiểu sai write_once_json là phải lỗi ngay cả khi
evidence giống hệt. Hàm gốc thực tế idempotent với byte-identical, chỉ cấm nội dung khác.
Sửa fixture để kiểm cả idempotence không đổi bytes và từ chối stdout khác; không thay
guard, không nới threshold, không sửa bằng chứng cũ. Nghiệm thu r2 ghi file XML/coverage
mới; không dùng tên final_tests.xml thất bại làm báo cáo phát hành.

Production UI r1 có20PASS/3timeout khi API đọc full repo trên NTFS đồng thời audit hash.
Không kết luận nguyên nhân duy nhất khi chưa đo riêng. R2 dùng đúng compact deployment
bundle đã khóa trên Linux ext4,23/23PASS; không sửa API/UI hay tăng timeout test gốc.
Đây vẫn local smoke, không Render và không fresh CPU-only environment. Mọi lịch sử lỗi
được giữ trong artifact Phase35. Tùy chọn Word UpdateLinksAtOpen có thể còn false như
đã ghi ở phần trước; không giả đã hoàn nguyên hoặc tự đổi ngược khi thiếu before state.
