# Bản thảo tích hợp sáu chương V3

Đọc `manuscript.md` để xem nội dung liền mạch từ Mở đầu đến phụ lục. Bìa/tóm tắt/từ
viết tắt nằm riêng ở `front_matter.md`. `contents.md` và `figures_and_tables.md` là
danh mục nội dung chưa phân trang, không phải TOC Word đã cập nhật số trang.

Nguồn hiện hành được chọn ở `report/active_manuscript_v3.json`; manifest Phase34
ghi hash và publication_order cho bước dựng Word. Không dùng root builder V2 hoặc
bản inactive Ch3/5/6 chỉ vì tên ngắn hơn. Ch3 dùng r2, Ch4 RNN–LSTM hợp nhất, Ch5 r2,
Ch6 active_report_r2. Không sửa nguồn đã khóa22–33.

- Thân bài: sáu chương,18dataset, lý thuyết cơ bản, hợp hàm/từng hàm, kết quả và giới hạn.
- Phụ lục A: hồ sơ nguồn/schema/mẫu/phân bố đầy đủ; field dài trích có ghi chú.
- Phụ lục B: function/shape/parameter/mapping cho12kiến trúc và36implementation contract.
- Phụ lục C: môi trường, chạy local, deploy contract và cách đọc bằng chứng.
- Phụ lục D: trích method nguyên văn từ source scratch/Keras/PyTorch đã thực thi.
- References:43nguồn theo thứ tự trích; `references.bib` giữ entry gốc tương ứng.
- `outline_extension.json`: mapping mục dự kiến Phase22 sang heading tích hợp, không sửa spec.

Kết quả kiểm nội dung ở artifacts/manifests/phase34/verification.json. Ma trận54yêu
cầu giữ rõ gate cuối chưa thực hiện. Tất cả số khoa học lấy artifact đã có, không
train/infer lại TEST. Các số thiếu, TEST schema recovery và failed seal vẫn được nêu.

Đây là source cho Phase35, không phải DOCX đã render. Phase35 phải dựng file mới tại
releases/v3/, không ghi đè V2/A06. Giữ style source-derived, kiểm font, hình, bảng dài,
đánh số/cross-reference và từng trang; không kéo dài bằng code dump để đạt budget.
Chi tiết kỹ thuật dài có thể giữ ở phụ lục điện tử, nhưng không làm mất bằng chứng
đối chiếu khi tạo bản in. Việc đổi nội dung đã khóa cần revision, không sửa trực tiếp.
