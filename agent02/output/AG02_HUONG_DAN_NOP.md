# Bài nộp Agent02

File chính để nộp là **agent02_D23CTPM01_TrieuTuanAnh.pdf** trong cùng thư mục này.
Báo cáo gồm 28 trang, đủ 10 câu hỏi, 14 bảng và 20 hình có giải thích. Thông tin
bìa: Triệu Tuấn Anh, B23DCCN053, lớp D23CTPM01; hình thức nộp cá nhân.

Đề yêu cầu một PDF và ghi hạn **23:30, thứ Năm ngày 29/10/2026**. Nộp qua kênh
thầy/lớp thông báo; tài liệu không ghi múi giờ. Bài chưa được tự động gửi lên LMS,
email hoặc bất kỳ dịch vụ nào.

DOCX cùng tên là bản sửa được để lưu và chỉnh khi cần. Notebook tại
`../notebooks/AG02_Code_and_Results.ipynb` có output thật. Gói
`AG02_Source_and_Notebook_r1.zip` chứa source và dữ liệu trình bày cần thiết; chỉ
gửi kèm nếu thầy yêu cầu. ZIP không chứa toàn bộ trajectory/checkpoint trung gian
hoặc môi trường chạy. Giữ workspace gốc để audit khoa học đầy đủ.

Các bước trước khi nộp:

1. Mở PDF chính, kiểm tra tên và thông tin bìa của mình.
2. Chọn đúng file PDF cuối trong thư mục `output`, tránh các candidate r1/r2/r3.
3. Tải lên kênh nộp bài của lớp và kiểm tra trạng thái nộp thành công.

Báo cáo đã được kiểm đủ 28 trang qua ảnh render. Word 16.0 trên máy hiện tại mở
DOCX ở chế độ chỉ đọc, nhận 28 trang và 14 bảng. PDF giữ bố cục đã nghiệm thu;
sửa DOCX hoặc dùng một bộ font khác có thể làm thay đổi phân trang.

`AG02_RELEASE_MANIFEST.json` ghi SHA256 và kích cỡ từng sản phẩm. Muốn đối chiếu,
dùng PowerShell từ thư mục gốc project:

```powershell
Get-FileHash -Algorithm SHA256 agent02_assignment/output/agent02_D23CTPM01_TrieuTuanAnh.pdf
```

Notebook Run All chỉ đọc kết quả đã khóa và hiển thị code/bảng/hình; không train
hoặc đánh giá cuối lại. Xem `../docs/phase09_reproduction.md` để dùng môi trường
WSL đã có. Mọi sửa sau phát hành cần phiên bản mới, giữ nguyên bản đã nộp.
