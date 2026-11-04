# Ma trận web sau khi sắp xếp

Đây là đặc tả dùng cho Phase2–3, không phải tuyên bố11 web đã chạy được. Phase1 chỉ đọc source,
phục hồi và kiểm byte. Web lịch sử trong staging là nguồn tham chiếu, không tự chạy server.

| Bài | Dataset/bài toán phải thấy | Phương pháp/kết quả | Dạng web đích và ca nghiệm thu |
|---|---|---|---|
| A01 | Pima diabetes; giá nhà Việt Nam | 5 mô hình ML/bài; metadata và artifact của A01 | Vanilla theo agent01; chọn mẫu, giải thích output, đổi mô hình; inference thật chỉ sau probe model/schema |
| A02 | Pima; giá nhà VN; customer behavior | ML truyền thống, customer tabular và text+tabular theo notebook | Vanilla;3 mục dữ liệu; không dùng nhầm bộ CDC của A03 hoặc Olist của A04 |
| A03 | CDC balanced; giá nhà VN; customer behavior | Các baseline ML + NumPy deep learning gốc/cải tiến theo comparison | Vanilla; hiển thị comparison thực; phân biệt baseline và model cuối; pipeline/preprocessor load từ artifact gốc |
| A04 | CDC2021; King County; Olist churn; MNIST; CIFAR10 | MLP/CNN, NumPy/Keras/PyTorch và các cải tiến có trong từng notebook | Vanilla;5 mục dữ liệu; phần nào replay/live phải ghi rõ; CIFAR Python-format cần xử lý riêng |
| A05 | EuroSAT; Oxford-IIIT Pet; CDC3 lớp | Basic/AlexNet-inspired/VGG-inspired/ResNet-inspired;12 checkpoint Keras tổng cộng | Vanilla;3 tab;4 kiến trúc/tab; Conv2D ảnh, Conv1D tabular; giải thích giới hạn feature adjacency |
| A06 | Online RetailII customer tuần; AAPL next Close | Vanilla RNN Keras/PyTorch, naive baseline theo metric gốc | Vanilla;2 tab;class/probability hoặc giá; đường actual/predicted đúng đơn vị/thời điểm |
| tieuluan1 | Ch1 lịch sử; Ch2ML; Ch3CNN; Ch4RNN của bản4 chương | Giữ web tổng hợp của commit tiểu luận1; serving CPU NumPy theo registry gốc | React/Python theo phiên bản; giữ navigation/style, sample payload, compare result; không ép dùng dataset V3 |
| tieuluan2 | Ch1–5 của tiểu luận3, gồm RNN–LSTM và KG–RAG | Giống V3 ở5 chương đầu; bỏ Ch6 serving/router/taskset/catalog/UI | React/Python; kiểm tất cả chapter/subtab; `/agents` và catalog multi_agent không hoạt động/expose |
| tieuluan3 | Đủ6 chương của bản hiện tại | Giữ scratch/Keras/PyTorch comparisons, RNN/LSTM, KG–RAG và multi-agent | React/Python; không làm mất compare-all hoặc readiness; so golden sample/TRAIN demo; không scientific TEST |
| agent01 | Mê cung10×10 | Phát lại greedy24 bước/BFS24 đã lưu; manual play | Tái dùng `web-demo/dist` payload; play/pause/step/reset/speed, va tường, tải đúng notebook |
| agent02 | Mô phỏng2 cửa hàng: IID/Persistent/Gold | Trace đã lưu, mean±sample std n5,20hình/caption, phép tính Q giả định | Tái dùng web-demo; replay20 bước, đổi regime, tải notebook, mở hình; không training/final claim |

## Ranh giới hành vi

- Không gọi kiến trúc Keras tự viết của A05 là NumPy scratch; cũng không giả thêm PyTorch
  vào A05 nếu notebook gốc không có. Mục tiêu là phục hồi đúng bài đã làm.
- Static web có thể chạy replay/results mà không gọi Python. Replay phải có nhãn và nguồn;
  không tạo số ngẫu nhiên rồi gọi là dự đoán. Inference chỉ mở sau kiểm checkpoint, preprocess,
  schema và golden input. Không có model thì giữ chức năng xem dữ liệu/kết quả thật.
- UI tiểu luận1–3 phải tiếp tục có giao diện tổng hợp theo chương và backend cần thiết;
  bản1 khác dataset/model/bố cục bản3, không được thay bằng bản3 chỉ đổi tiêu đề.
- Mọi biểu đồ phải giải thích trục/đơn vị, tập dữ liệu/split, đường/cột/vùng sai số,
  điều kết quả cho thấy và giới hạn. Không so trực tiếp sai metric hay khác dataset.
- Port/API URL đặt bằng config; không để11 web cùng trỏ API hiện tại rồi hiện sai bài.
- Ca chung: link notebook, input mẫu, đường dẫn asset, lỗi input, reload route, mobile layout;
  live web có thêm CORS/health/readiness. Không mở TEST nghiên cứu cho ca UI.

## Render

Root mặc định tiếp nối hai service hiện có và phục vụ `tieuluan3` sau migration. Phase3 chuẩn bị
đường dẫn build/start, source/bundle parity và hướng dẫn đổi Settings một lần. Phase1 không sửa
`render.yaml`, không push/deploy và không thao tác tài khoản. Các bản tiểu luận1/2 có config riêng;
8 static web không bắt buộc dựng thêm8 Python service.
