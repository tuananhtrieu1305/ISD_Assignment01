# MỞ ĐẦU

## 0.1. Lý do chọn đề tài

Một bộ dữ liệu sức khỏe có thể được dùng để phân loại nhãn khảo sát, một bức ảnh để nhận
diện vật thể, còn lịch sử giá vàng để dự đoán các mốc tiếp theo. Cả ba đều tạo ra đầu ra
từ dữ liệu, nhưng cách tổ chức thông tin khác nhau. Dữ liệu bảng cần quan tâm ý nghĩa
cột; ảnh cần giữ quan hệ không gian; chuỗi cần giữ thứ tự thời gian. Chọn mô hình mà
không xét những khác biệt đó dễ dẫn đến một chương trình chạy được nhưng kết luận sai.

Tiểu luận khảo sát lịch sử AI và thực nghiệm các kỹ thuật ML, CNN, RNN–LSTM, KB/KG–RAG
và hệ đa tác tử. Nội dung nối các bài thực hành bằng một quy trình chung: xác định bài
toán, kiểm tra dữ liệu, mô tả phép biến đổi, học mô hình, đánh giá và đưa checkpoint
vào giao diện minh họa. Lịch sử giúp hiểu vì sao các ý tưởng xuất hiện; thực nghiệm
cho biết chúng hoạt động đến đâu trong điều kiện cụ thể của đề tài.

Các miền tiểu đường, giá nhà và giá vàng được ưu tiên ở nơi phù hợp. Với dữ liệu bảng,
CDC và Ames tạo hai bài toán phân loại/hồi quy. Ảnh võng mạc IDRiD tạo ví dụ liên quan
biến chứng tiểu đường, nhưng không thay thế việc đọc ảnh của bác sĩ. Chuỗi vàng World
Bank và chỉ số nhà BIS cho thấy bài toán dự báo cần xử lý lịch, đơn vị và thời điểm
thông tin khả dụng. Dữ liệu đối chứng ở những miền khác giúp tránh đồng nhất một kỹ
thuật với một ứng dụng duy nhất.

Việc học từ đầu bằng NumPy làm rõ các phép tính mà một lời gọi thư viện có thể che đi.
Keras và PyTorch giúp đối chiếu cách tổ chức mô hình, tự động vi phân và chạy GPU.
So sánh này chỉ có nghĩa khi chúng nhận cùng dữ liệu, cùng kiến trúc và cùng ngân sách.
Do đó, trọng tâm không phải chọn một tên framework “tốt nhất”, mà là giải thích được
đầu vào đi qua những hàm nào và số liệu cuối được tạo ra như thế nào.

## 0.2. Mục tiêu và câu hỏi nghiên cứu

Mục tiêu của đề tài là xây dựng một khảo sát cơ bản, dễ theo dõi và có bằng chứng thực
nghiệm. Phần lý thuyết đi từ bài toán, ví dụ và luồng xử lý đến các phép tính cần để đọc
code scratch. Không dùng khai triển toán dài thay cho giải thích hoạt động của mô hình.

Các câu hỏi chính được gắn với chương thực nghiệm:

- Với dữ liệu bảng, ba implementation MLP khác nhau thế nào về chất lượng, thời gian,
  bộ nhớ và khả năng đóng gói khi so với mô hình ML cổ điển?
- Với ba miền ảnh, CNN cùng kiến trúc có tạo ra kết quả tương tự giữa scratch, Keras
  và PyTorch không? Những lỗi nào vẫn xuất hiện dù đã đủ độ sâu?
- Trên các chuỗi vàng, nhà và điện năng, LSTM có giảm sai số so với RNN và các quy tắc
  dự đoán đơn giản không? Kết luận thay đổi thế nào theo horizon và giai đoạn?
- Bổ sung knowledge graph vào truy hồi có cải thiện việc tìm đúng bằng chứng không?
  Citation hợp lệ có đồng nghĩa với câu trả lời đúng không?
- Thêm router, verifier và reporter có giúp kiểm soát lỗi công cụ so với gọi trực tiếp
  không, và chi phí phối hợp thể hiện ở đâu?

Không câu hỏi nào mặc định mô hình sâu hơn hoặc hệ nhiều vai trò hơn phải tốt hơn.
Kết quả âm được giữ lại để phân biệt giới hạn của cấu hình với lỗi đo lường hoặc lỗi mã.

## 0.3. Đối tượng và phạm vi

Chương1 dùng Iris, MNIST và metadata ImageNet làm ba trường hợp lịch sử, không huấn luyện
mô hình. Chương2 khảo sát CDC Diabetes, Ames Housing và Bank Marketing. Chương3 dùng
IDRiD, EuroSAT và CIFAR-10. Chương4 dùng vàng World Bank, chỉ số nhà BIS và điện năng
Household Power, với cả RNN và LSTM. Chương5 giữ MedQuAD, FinQA và Wikidata; hai nguồn
đầu có benchmark QA, còn Wikidata phục vụ cấu trúc/liên kết thực thể. Chương6 dùng ba
bộ nhiệm vụ mới theo miền tiểu đường, nhà và vàng, xây trên snapshot đã có.

Mạng MLP, RNN và LSTM có sáu lớp học được; CNN có bảy lớp. Input, activation, pooling,
bước thời gian và từng cổng LSTM không được dùng để tăng số đếm. Độ sâu này phục vụ
yêu cầu môn học và tính đối chiếu, không phải bằng chứng kiến trúc tối ưu. Mã đầy đủ
được giữ trong module và notebook mỏng; thân chương chỉ trích phần cần để hiểu cơ chế.

KB/KG–RAG trong đề tài dùng truy hồi và trả lời trích xuất có nguồn, không tái tạo toàn
bộ mô hình sinh trong công trình RAG gốc [1]. Hệ đa tác tử là điều phối
nhiều vai trò theo luật xác định, không phải LLM tự chủ hoặc hệ suy luận mở. Hai phạm
vi này cần được phân biệt với các thuật ngữ rộng hơn trong nghiên cứu.

## 0.4. Phương pháp thực hiện

Dữ liệu được thu nhận từ nguồn có provenance và lưu phiên bản/hash. Trước khi train,
EDA xác định kích cỡ, phân bố, nhãn thiếu, trùng lặp và giới hạn giấy phép. Dữ liệu bảng
được xử lý theo nhóm trùng khi cần; ảnh giữ official TEST; chuỗi chia theo lịch của
target. Scaler, imputer, vocabulary và trọng số lớp chỉ dùng phần train đã khóa.

Ba implementation cùng họ dùng cùng canonical weights ban đầu, thứ tự batch, split và
budget. Một số tập train lớn dùng matched subset đã khai báo để scratch có thể chạy;
full validation và TEST được giữ. Các bảng không ghép matched-subset với full-train
như cùng điều kiện. Ba seed mô tả độ ổn định, không tạo thành ba quần thể độc lập.

Validation dùng chọn checkpoint. TEST mở sau khi khóa cấu hình, mã đánh giá và danh
sách lượt chạy; các bảng/hình tiếp theo đọc prediction đã lưu. Một sự cố schema khi
hoàn tất TEST chuỗi được phục hồi bằng output cũ và journal có phiên bản, không dự
đoán lại những claim đã sử dụng. Cách xử lý này được trình bày cùng giới hạn số đo ở
Chương4 để không biến lỗi vận hành thành kết quả thuận lợi hơn.

Phân loại đọc đồng thời macro-F1, recall và confusion matrix thay vì chỉ accuracy.
Hồi quy/dự báo dùng sai số theo đơn vị gốc, tách horizon và chuỗi. Truy hồi tách tìm
bằng chứng, trả lời và citation. Tác tử tách hoàn thành câu trả lời với từ chối đúng
rubric. Thời gian và bộ nhớ luôn đi kèm điều kiện đo; số chưa đo không được điền0.

Mô hình được train offline trên NumPy CPU hoặc TensorFlow/PyTorch GPU trong hai môi
trường đã khóa. API CPU dùng NumPy portable để phục vụ weights; chế độ local GPU dùng
framework native. Giao diện React cho chọn chương/dataset, nhập một input chung và xem
các implementation. Inference minh họa không phải một lần kiểm tra TEST hoặc phép đo
chất lượng mới. Triển khai cloud chưa được coi là thành công chỉ vì build local đạt.

## 0.5. Ý nghĩa và giới hạn sử dụng

Đóng góp học tập của đề tài nằm ở việc liên kết cơ chế với mã và kết quả có thể kiểm
tra. Hợp hàm mô tả toàn luồng, còn bảng từng hàm giải thích input/output, shape, tham
số và trường hợp biên. Cùng contract được dùng trong code, báo cáo và web để hạn chế
việc ba nơi mô tả ba kiến trúc khác nhau.

Các snapshot có giới hạn đại diện. CDC là khảo sát tự báo cáo; ảnh y khoa có dữ liệu
ít; Ames phản ánh giao dịch lịch sử ở một địa phương. BIS là chỉ số, không phải giá
một căn nhà. Vàng và BIS không có bộ vintage đầy đủ để chứng minh thông tin đã được
công bố đúng ngày dự báo. Điện năng chỉ từ một hộ. Benchmark tác tử có template tổng
hợp và quyền công cụ hẹp, không phản ánh mọi câu hỏi thực tế.

Vì vậy, output không dùng cho chẩn đoán, quyết định điều trị, định giá hiện tại hoặc
mua bán tài sản. Nguồn dẫn có thật cũng không chứng minh nội dung đúng chuyên môn.
Những giới hạn này được giữ ngay cạnh kết quả và khi trình diễn giao diện.

## 0.6. Bố cục tiểu luận

Chương1 trình bày các mốc AI và ba benchmark lịch sử. Chương2 đi từ ML cơ bản đến MLP
trên dữ liệu bảng. Chương3 giải thích CNN và thực nghiệm ảnh. Chương4 phát triển RNN
sang LSTM, so sánh trên cùng chuỗi. Chương5 tổ chức tri thức và truy hồi bằng chứng.
Chương6 kiểm tra sự phối hợp và kiểm chứng giữa nhiều vai trò. Cuối mỗi chương thực
nghiệm có một mục triển khai ngắn; hướng dẫn thao tác dài đặt ở phụ lục. Kết luận
tổng hợp các câu trả lời, giới hạn và hướng nghiên cứu tiếp theo.
