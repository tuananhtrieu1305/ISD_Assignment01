# TIỂU LUẬN MÔN HỌC TRÍ TUỆ NHÂN TẠO

Lịch sử AI và thực nghiệm ML, CNN, RNN–LSTM, Knowledge Graph–RAG và hệ đa tác tử

## Tóm tắt

Tiểu luận trình bày các kỹ thuật AI từ ví dụ và luồng xử lý, sau đó kiểm chứng trên
dữ liệu bảng, ảnh, chuỗi, corpus tri thức và bộ nhiệm vụ tác tử. ML, CNN, RNN và LSTM
có các implementation scratch, Keras và PyTorch theo cùng điều kiện so sánh. Hợp hàm,
shape và bảng từng hàm được đối chiếu với contract dùng chung. Kết quả cho thấy mô
hình phức tạp không luôn vượt baseline; kiểm tra nguồn và giới hạn suy diễn quan
trọng như metric. API Python và React minh họa inference từ checkpoint đã khóa,
không chạy lại TEST. Hệ KG–RAG dùng trả lời trích xuất, còn tác tử điều phối theo luật
với quyền công cụ hẹp; không tuyên bố trợ lý chuyên môn hoặc hệ tự chủ tổng quát.

## Từ viết tắt và quy ước

| Ký hiệu | Nghĩa trong tiểu luận |
|---|---|
| AI | Trí tuệ nhân tạo |
| ML | Học máy |
| MLP | Mạng perceptron nhiều lớp |
| CNN | Mạng nơ-ron tích chập |
| RNN | Mạng nơ-ron hồi quy theo chuỗi |
| LSTM | Mạng có bộ nhớ ngắn và dài hạn |
| BPTT | Lan truyền ngược theo thời gian |
| KB / KG | Kho tri thức / đồ thị tri thức |
| RAG | Truy hồi làm đầu vào cho lớp trả lời |
| LSA / RRF | Phân tích ngữ nghĩa tiềm ẩn / hợp nhất thứ hạng nghịch đảo |
| TRAIN / VALIDATION / TEST | Học tham số / chọn checkpoint / đánh giá cuối đã khóa |
| B, T, D | Số mẫu một batch, số bước thời gian, số đặc trưng |
| NHWC / NCHW | Thứ tự batch–cao–rộng–kênh / batch–kênh–cao–rộng |
| MAE / RMSE | Sai số tuyệt đối trung bình / căn sai số bình phương trung bình |
| RSS / VRAM | Bộ nhớ resident process / bộ nhớ thiết bị đồ họa trong phạm vi đo |
| SHA-256 | Hash kiểm tra nội dung file, không chứng minh nguồn đúng chuyên môn |
| Seed | Khởi tạo bộ sinh ngẫu nhiên; không phải một split dữ liệu mới |

