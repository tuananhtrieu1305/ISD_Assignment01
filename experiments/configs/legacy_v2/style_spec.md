# Quy chuẩn trình bày DOCX

Phiên bản 1.0, khóa ở Phase 1. Quy chuẩn được rút từ file mẫu `A06_Assignment_Report.docx` và điều chỉnh để tài liệu dài 60+ trang dễ đọc, chỉnh sửa và kiểm tra.

## 1. Khổ giấy và lề

| Thuộc tính | Giá trị khóa |
|---|---|
| Khổ giấy | A4 portrait, 21.0 × 29.7 cm |
| Lề trên | 2.25 cm |
| Lề dưới | 2.00 cm |
| Lề trái | 2.70 cm |
| Lề phải | 2.20 cm |
| Header | 0.90 cm tính từ mép |
| Footer | 0.80 cm tính từ mép |
| Gutter | 0 cm; chỉ tăng nếu giảng viên yêu cầu đóng gáy |

Các giá trị trên tương ứng gần nhất với section properties của DOCX mẫu: A4 `11906 × 16838` twips, margins `1531/1247/1276/1134` twips.

## 2. Kiểu chữ và đoạn văn

| Style | Font | Cỡ | Màu/định dạng | Spacing |
|---|---|---:|---|---|
| Normal | Times New Roman | 11.5 pt | `#1F2933`, canh đều | 1.5 dòng; after 5 pt |
| Title | Times New Roman | 21 pt | bold, `#17365D`, đường kẻ dưới `#4F81BD` | after 12 pt |
| Heading 1 | Times New Roman | 15 pt | bold, `#17365D` | before 10 pt; after 7 pt |
| Heading 2 | Times New Roman | 13 pt | bold, `#2F75B5` | before 8 pt; after 5 pt |
| Heading 3 | Times New Roman | 11.5 pt | bold, `#17365D` | before 6 pt; after 3 pt |
| Caption | Times New Roman | 10 pt | italic phần nhãn, màu body | before 4 pt; after 6 pt |
| Table text | Times New Roman | 9–10 pt | không nhỏ hơn 9 pt | single–1.15 |
| Code | Consolas | 9 pt | nền `#F3F6F8`, viền `#D9E2E8` | single |
| Header/footer | Times New Roman | 9 pt | `#5B6570` | single |

- Body dùng first-line indent 0.75 cm cho đoạn văn thường; đoạn ngay sau heading/caption không thụt đầu dòng.
- Không dùng nhiều dòng trống để tạo khoảng cách; spacing nằm trong style.
- Bật `keep_with_next` cho Heading 1–3 và caption; bật `keep_together` cho code block và bảng nhỏ.
- Widow/orphan control bật cho body. Không để heading ở cuối trang mà không có ít nhất hai dòng nội dung theo sau.

## 3. Đánh số và phân cấp

- Chương dùng Heading 1: `CHƯƠNG 1. ...`, `CHƯƠNG 2. ...`.
- Heading 2 đánh số `1.1`, `1.2`; Heading 3 đánh số `1.1.1`, `1.1.2`.
- Mở đầu, Phần triển khai, Kết luận và Tài liệu tham khảo dùng Heading 1 nhưng có thể không mang số chương theo quy định khoa.
- TOC lấy Heading 1–3; không gõ số trang thủ công.
- Không dùng Heading 4 trong thân bài; chi tiết sâu hơn chuyển thành đoạn bold hoặc danh sách.

## 4. Hình và bảng

- Hình: caption bên dưới, dạng `Hình 3.2. Phân bố lớp EuroSAT`.
- Bảng: caption bên trên, dạng `Bảng 4.1. Kích thước các split của Online Retail II`.
- Đánh số theo chương bằng trường Word; mọi hình/bảng phải được nhắc trong văn bản trước hoặc ngay sau vị trí xuất hiện.
- Hình raster tối thiểu 150 dpi ở kích thước hiển thị; ưu tiên 200–300 dpi cho plot. Không kéo méo tỷ lệ.
- Plot dùng palette nhất quán và color-blind friendly; không truyền đạt kết quả chỉ bằng màu.
- Bảng dữ liệu/metric phải là native Word table, có hàng header lặp khi qua trang; tránh chụp màn hình DataFrame.
- Bảng không rộng quá vùng text. Nếu cần landscape, dùng section riêng và trở lại portrait ngay sau bảng.
- Ô số canh phải; số thập phân cùng precision trong một cột. Dùng dấu chấm làm dấu thập phân trong metric/code, giải thích đơn vị bằng tiếng Việt.
- Ghi nguồn dưới caption khi hình/bảng chuyển thể từ nguồn ngoài; artifact nội bộ ghi trong manifest, không lộ absolute path trong DOCX.

## 5. Công thức, code và thuật ngữ

- Công thức dùng equation object, đánh số theo chương khi được tham chiếu; biến italic, hàm/toán tử upright.
- Chỉ trích code 10–25 dòng để giải thích thuật toán. Code đầy đủ nằm ở notebook/source và được dẫn bằng tên file tương đối.
- Tên class/API (`Conv2D`, `SimpleRNN`, `nn.RNN`) giữ nguyên tiếng Anh, dùng monospace khi phù hợp.
- Lần đầu dùng thuật ngữ ghi Việt–Anh, ví dụ “học có giám sát (supervised learning)”; các lần sau dùng nhất quán theo bảng thuật ngữ.

## 6. Trích dẫn và tài liệu tham khảo

- Kiểu trích dẫn trong thân bài: số thứ tự trong ngoặc vuông, ví dụ `[12]`; thứ tự tài liệu theo lần xuất hiện.
- Nguồn lịch sử ưu tiên bài báo gốc/website lưu trữ của tác giả hoặc tổ chức học thuật.
- Dataset trích cả trang nguồn và paper/DOI nếu có.
- Không đưa URL dài vào body; URL/DOI nằm trong entry tài liệu tham khảo.
- Ngày truy cập cho nguồn web/dataset: `2026-10-05`.
- Mỗi citation key trong manuscript phải có đúng một entry trong `bibliography.bib`; không có entry mồ côi trong bản release.

## 7. Header, footer và front matter

- Header trang nội dung: tên rút gọn của tiểu luận ở trang chẵn; tên chương hiện tại ở trang lẻ nếu build engine hỗ trợ ổn định.
- Footer: số trang ở giữa hoặc góc ngoài, nhất quán toàn tài liệu.
- Bìa và trang tên không hiển thị header/footer. Front matter có thể dùng số La Mã thường; nội dung chính bắt đầu lại từ 1.
- Bìa dùng palette xanh đậm của mẫu, nhưng không để thành phần trang trí làm giảm tính học thuật.

## 8. Accessibility và chất lượng

- Mọi hình thông tin có alt text ngắn; hình trang trí được đánh dấu decorative nếu công cụ hỗ trợ.
- Không dùng màu làm tín hiệu duy nhất; contrast chữ–nền đủ đọc khi in grayscale.
- Table có header row rõ; không merge ô phức tạp nếu không cần.
- Link hiển thị bằng nhãn có nghĩa thay vì đường dẫn máy local.
- Trước release: cập nhật TOC/list fields, reopen DOCX, render bằng artifact-tool, kiểm tra từng trang và chạy scan placeholder/path/token.

## 9. Quy tắc văn phong

- Giọng văn học thuật, trực tiếp, dựa trên bằng chứng; mỗi bảng/hình có đoạn nhận xét “kết quả cho thấy gì” và “không cho phép kết luận gì”.
- Phân biệt rõ dữ liệu raw, dữ liệu sau làm sạch, benchmark subset và TEST.
- Không dùng “tốt nhất” nếu chỉ so trong protocol nội bộ; dùng “cao nhất trong các cấu hình được đánh giá”.
- Không làm tròn để che giấu chênh lệch nhỏ; metric chính 3–4 chữ số thập phân, thời gian ghi độ phân giải phù hợp.
- Kết quả âm, collapse hoặc baseline thắng phải được giữ nguyên và giải thích.
