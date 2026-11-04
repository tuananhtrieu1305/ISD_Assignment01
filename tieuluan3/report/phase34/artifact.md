# Handoff định dạng từ mẫu A06

Tham chiếu chỉ đọc: `releases/v2/references/A06_Assignment_Report.docx`.
Hash và XML cụ thể: `artifacts/manifests/phase34/reference_style_evidence.json`.
Đây là bằng chứng cấu trúc/văn bản, không phải distillation đã render đầy đủ.
Các font/cỡ dưới đây là định nghĩa style trong XML; direct formatting, theme và
run override chưa được kiểm kê đầy đủ. Không suy từ Normal rằng mọi đoạn nhìn thấy
đều dùng đúng font đó trước khi render reference ở Phase35.

Trang A4 portrait11906×16838twip; lề trên1247, phải/dưới/trái1134twip,
header/footer720twip. Một section trong XML tham chiếu; header/footer relationship
cần giữ khi dựng bản mới từ working copy, không sửa reference.

Normal: Calibri13pt, black, justify, firstLine454twip, after120twip,
line312 auto tức1,3 dòng. Heading1: Times New Roman15pt bold, màu1F4E79,
before200/after120twip, keepNext/keepLines. Heading2: Times New Roman13,5pt bold,
màu1F4E79. Caption: Times New Roman11pt bold italic, center, màu4F81BD,
before60/after160twip. Giữ style source-derived; không áp preset Letter hay heading
black của tài liệu không có mẫu. User đã yêu cầu theo mẫu nên mẫu được ưu tiên.

Văn bản hướng đến sinh viên biết lập trình/toán đại cương, câu đầy đủ và trực tiếp,
thuật ngữ giải thích trước khi dùng. Mạch ví dụ→shape→hàm→đo lường→giới hạn.
Không chép môi trường CPU/Conda hoặc số đo của A06 vào thực nghiệm V3.

Phase35 còn phải dùng dependency loader/bundled renderer được cung cấp, render
reference và xem mọi pattern; hoàn tất style/section/header/footer/table/field/package
inventory trước authoring DOCX. Lấy working copy reference khác tên, map sáu chương
và front matter; không ghi đè A06/V2. Mục lục/hình/bảng hiện chưa có số trang; không
điền số dự kiến thành số thật. TOC/SEQ/REF/PAGE cập nhật bằng đường kiểm chứng được,
rồi render và xem từng trang. Không coi các số trang budget trong plan là page count.
