# Phase 35 — hợp đồng trình bày tài liệu

## Nguồn và quyết định

Mẫu chỉ đọc: `releases/v2/references/A06_Assignment_Report.docx`, SHA-256
`9eecf073897b609d9e2d0024bd56594dc6fec99823508e57ed79dff8d4780348`.
Bản thảo khoa học là publication_order của Phase34; không sửa dữ liệu, số đo hay source đã khóa.
Người dùng xác nhận giữ nguyên Triệu Tuấn Anh/B23DCCN053/D23CTPM01,
PGS.TS Trần Đình Quế, Học viện Công nghệ Bưu chính Viễn thông, và thông tin học kỳ trên bìa.
Chỉ đổi nhãn ASSIGNMENT 06 thành TIỂU LUẬN MÔN HỌC, bổ sung tên chủ đề trong dòng trống.

## Distillation từ mẫu thực, không phải preset

Inventory: `artifacts/manifests/phase35/template_inventory.json`, 66 part, một section,
header rỗng, footer “Trang”, không field, không bảng Word, không OMML hay content control.
Các bảng/công thức cũ thực tế là ảnh. Reference đã render bằng helper Documents nguyên bản
tại `report/qa35/template-reference-r1/`: 32 trang, từng trang đã được xem ở 120 dpi.
Font PDF thực là Calibri cho body/heading/bìa (theme thắng khai báo TNR của heading),
không suy diễn font từ riêng styles.xml.

| Thành phần | Quy tắc kế thừa |
|---|---|
| Trang | A4 11906×16838 twip; top1247, bottom/left/right1134; footer/header720 |
| Body | Calibri13, justify, line1.3, firstLine454, after120 |
| Heading1/2/3 | Calibri15/13.5/13, xanh1F4E79/365F91; keepNext/keepLines |
| Bìa | Logo gốc, Calibri đậm16/22, metadata12; không thêm border trang trí |
| Caption | TNR11, đậm nghiêng xanh4F81BD, giữa, single line |
| Code | Consolas, single line, nền trắng, thụt trái; tăng từ9 lên10 để dễ đọc |
| Bảng mới native | Header xanh nhạt, chữ xanh đậm; grid mảnh; body10.5–11, wide tối thiểu9.5 |
| Footer | Giữ chữ Trang/TNR12; thêm PAGE/NUMPAGES thật |

Mọi pattern của 32 trang đã đối chiếu: 1 bìa; 2 mục lục; 3 danh mục hình;
4 danh mục bảng; 5–9 lý thuyết/bảng/mã; 10–11 plot/diagram; 12 gần trống;
13–14 bảng/plot; 15–17 công thức/kiến trúc/mã; 18–23 plot/kết quả/mã;
24 trống; 25–30 kết quả/giới hạn; 31 kết luận; 32 tài liệu tham khảo.
Trang12/24 trống, mục lục cache lỗi thời và footer thiếu số là lỗi quan sát được của mẫu,
không phải yếu tố phong cách cần tái tạo.

## Slot map và bảo toàn package

- Clone nguyên 15 paragraph bìa đầu tiên (bao gồm logo), chỉ thay title và một dòng trống.
- Thay body cũ sau bìa bằng front matter, mục lục, danh mục hình/bảng, 6 chương,
  kết luận, 43 tài liệu và 4 phụ lục đầy đủ từ Phase34.
- Giữ nguyên bytes mọi part gốc, trừ danh sách cho phép: document.xml,
  document.xml.rels, settings.xml, footer1.xml, styles.xml, [Content_Types].xml,
  docProps/core.xml và docProps/app.xml. Styles chỉ append định nghĩa V3;
  định nghĩa gốc và theme/numbering gốc phải giữ nguyên về cấu trúc/canonical XML.
- Giữ nguyên section geometry/header/footer relationship. Media cũ được giữ dù không dùng.
  Media V3 thêm tên/rId riêng, không đè asset cũ. Tables native, ảnh inline,
  caption SEQ cache, bookmark, REF/PAGEREF/internal link phải có đích thật.
- Mục lục/danh mục lấy page map từ PDF render, gắn PAGEREF và link tới bookmark;
  cache phải ổn định qua render cuối. Word updateFields bật; không LO save-as package.
- Trích dẫn [1]…[43] nối bookmark references; đường dẫn dataset/model contract được
  chuyển thành link phụ lục liên quan khi có đích, còn repo locator hiển thị đầy đủ.
- Chỉ chuẩn hóa escape LaTeX tên tác giả khi trình bày (Küttler, Rocktäschel,
  Léon, Jürgen, Łukasz); lưu ledger, không sửa bibliography gốc.
- Công thức cần thiết có OMML; inline shape/path/function vẫn monospace, không raster math.

## QA và runtime

Sai lệch được duyệt: `phase35.local-toolchain.1`, xem authorization. Doc venv riêng,
không thay GPU/uv.lock. Ubuntu LO rootless thất bại; TDF26.2.6.3 đã qua reference render.
PDF/PNG chỉ là bản QA, không gọi đó là Word desktop validation. Trước phát hành phải
kiểm từng trang cuối, package preservation, field/navigation, tests/coverage, production
smoke local và khả năng mở Word; chưa đạt thì Phase35 vẫn IN_PROGRESS.
