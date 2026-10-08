<!-- page_target: 3-4; style: term_paper/config/style_spec.md -->

# MỞ ĐẦU

## 0.1. Bối cảnh và lý do chọn đề tài

Trí tuệ nhân tạo (Artificial Intelligence — AI) không hình thành từ một thuật toán đơn lẻ. Lĩnh vực này phát triển qua nhiều cách tiếp cận: suy luận dựa trên luật, tìm kiếm trong không gian trạng thái, học máy thống kê và mạng neuron. Trong đó, machine learning (ML) chuyển trọng tâm từ việc viết sẵn mọi quy tắc sang việc ước lượng quy luật từ dữ liệu; Convolutional Neural Network (CNN) khai thác cấu trúc cục bộ của ảnh; còn Recurrent Neural Network (RNN) mô hình hóa dữ liệu có thứ tự bằng trạng thái ẩn. Ba nhóm kỹ thuật này tạo thành một trục phát triển phù hợp để khảo sát cả lý thuyết, cài đặt và ứng dụng của AI hiện đại [@goodfellow2016deep].

Việc chỉ trình bày công thức hoặc gọi một thư viện huấn luyện chưa đủ để cho thấy mô hình hoạt động như thế nào. Một kết quả thực nghiệm còn phụ thuộc vào cách chia dữ liệu, phạm vi fit bộ tiền xử lý, seed, hàm mất mát, tiêu chí chọn checkpoint và cách tính metric. Nếu các yếu tố đó thay đổi giữa các implementation, chênh lệch kết quả không còn phản ánh riêng framework hoặc thuật toán. Ngược lại, cài đặt hoàn toàn từ đầu giúp nhìn rõ phép toán nhưng có thể che khuất các vấn đề thực tế như lưu mô hình, suy luận theo batch và kiểm soát dữ liệu. Vì vậy, tiểu luận lựa chọn cách tiếp cận song song: triển khai từ nền tảng (scratch), Keras và PyTorch dưới một protocol chung.

Đề tài cũng xuất phát từ nhu cầu nối các bài thực hành riêng lẻ thành một chu trình có thể kiểm chứng. Các notebook hiện có đã xử lý dữ liệu bảng, ảnh và chuỗi thời gian, nhưng mỗi bài được xây dựng cho một mục tiêu học tập khác nhau. Nếu ghép trực tiếp các metric cuối cùng, sự khác biệt về split, preprocessing hoặc kiến trúc có thể tạo ra một so sánh thiếu công bằng. Tiểu luận vì vậy không coi notebook là văn bản báo cáo hoàn chỉnh. Chúng được dùng như nguồn bằng chứng ban đầu; dữ liệu, cấu hình, prediction và metric phải được truy vết trước khi đưa vào bảng tổng hợp.

Một lý do khác là khoảng cách giữa mô hình trong notebook và một chức năng inference có thể sử dụng. Mô hình đạt metric trên tập TEST chưa tự động trở thành một hệ thống triển khai được. Đầu vào mới cần được kiểm tra, biến đổi bằng đúng preprocessor đã fit trên TRAIN, chuyển qua đúng phiên bản mô hình và trả về output có diễn giải. Với bài toán sức khỏe hoặc tài chính, output còn phải đi kèm giới hạn sử dụng; dự đoán thực nghiệm không phải chẩn đoán y khoa hay khuyến nghị đầu tư. Phần triển khai trong tiểu luận được xem là phép kiểm tra cuối của tính nhất quán giữa dữ liệu, mô hình và mã suy luận, không phải tuyên bố về một sản phẩm sẵn sàng vận hành.

Từ các vấn đề trên, đề tài “Lịch sử phát triển AI và thực nghiệm các kỹ thuật ML, CNN, RNN” được lựa chọn nhằm trả lời hai nhu cầu. Về học thuật, báo cáo hệ thống hóa các mốc phát triển và giải thích cơ chế của những thuật toán tiêu biểu. Về thực nghiệm, báo cáo xây dựng một đường dẫn từ dữ liệu thô đến kết quả và triển khai, trong đó mỗi con số quan trọng phải gắn với artifact có thể tái tính. Cách tổ chức này giúp phân biệt điều mà thí nghiệm thực sự chứng minh với điều nằm ngoài phạm vi của nó.

## 0.2. Mục tiêu nghiên cứu

Mục tiêu tổng quát của tiểu luận là xây dựng một khảo sát có hệ thống về AI, ML, CNN và RNN, đồng thời kiểm chứng các khái niệm bằng thực nghiệm tái lập trên nhiều dạng dữ liệu. Báo cáo không hướng đến thiết lập kết quả state-of-the-art. Trọng tâm là hiểu cơ chế, kiểm soát protocol và so sánh ba cách cài đặt trong cùng điều kiện.

Các mục tiêu cụ thể gồm:

1. Hệ thống hóa lịch sử AI từ các tiền đề về logic và neuron nhân tạo, qua AI biểu tượng, học máy thống kê, deep learning, Transformer đến mô hình nền tảng và AI tạo sinh.
2. Trình bày nguyên lý của các kỹ thuật ML cơ bản cho classification và regression; giải thích vai trò của dữ liệu, hàm mất mát, tối ưu hóa và đánh giá khả năng khái quát.
3. Làm rõ cách CNN sử dụng convolution, activation và pooling để học đặc trưng không gian; khảo sát cả ảnh RGB và trường hợp chuyển dữ liệu bảng thành chuỗi một chiều có kiểm soát.
4. Làm rõ cơ chế trạng thái ẩn, Backpropagation Through Time và gradient clipping của Vanilla RNN; đặt kết quả trong quan hệ với LSTM, attention và giới hạn phụ thuộc dài hạn [@elman1990structure; @hochreiter1997lstm].
5. Xây dựng các implementation tương ứng bằng NumPy scratch, Keras và PyTorch; dùng cùng sample keys, split, preprocessing output, topology logic và budget trong mỗi matched track.
6. Đánh giá mô hình bằng prediction artifact thay vì nhập metric thủ công; báo cáo accuracy, precision, recall, F1 hoặc MAE, RMSE, R² theo đúng loại bài toán, kèm baseline và failure case.
7. Triển khai một luồng inference có kiểm tra đầu vào, nạp đúng model/preprocessor và cung cấp thông tin provenance, từ đó chứng minh rằng artifact huấn luyện có thể được tái sử dụng ngoài notebook.

Các mục tiêu trên được sắp xếp theo chuỗi “lịch sử — cơ chế — thực nghiệm — triển khai”. Chuỗi này tránh hai cực: một báo cáo chỉ tóm lược lịch sử nhưng thiếu kiểm chứng, hoặc một tập notebook có nhiều output nhưng thiếu lập luận xuyên suốt.

## 0.3. Đối tượng, phạm vi và câu hỏi nghiên cứu

Đối tượng nghiên cứu gồm ba họ mô hình. Chương 2 khảo sát các thuật toán ML cơ bản và Multilayer Perceptron (MLP) trên dữ liệu bảng. Chương 3 tập trung vào CNN trên dữ liệu ảnh và một thí nghiệm Conv1D. Chương 4 tập trung vào Vanilla RNN cho classification chuỗi hành vi và regression chuỗi thời gian. LSTM, attention, Transformer và mô hình nền tảng được trình bày trong phần lịch sử và nền tảng để xác định vị trí của các mô hình thực nghiệm; chúng không thay thế phạm vi matched comparison đã khóa.

Phạm vi dữ liệu gồm tám dataset instance. Chương 2 dùng CDC Diabetes binary classification, Vietnam Housing 2024 regression và Synthetic E-Commerce Customer Behavior churn classification. Chương 3 dùng EuroSAT RGB, Oxford-IIIT Pet và CDC Diabetes 012 được biểu diễn cho Conv1D. Chương 4 dùng UCI Online Retail II ở dạng chuỗi khách hàng–tuần và AAPL giai đoạn 2015–2025 ở dạng chuỗi 30 phiên. EuroSAT được gắn với công trình và bản phát hành dataset tương ứng [@helber2019eurosat; @helber2023eurosatdata]; Oxford-IIIT Pet được dùng theo annotation chính thức [@parkhi2012catsdogs]; Online Retail II được truy vết về UCI Machine Learning Repository [@chen2012onlineretailii].

Các dataset không được dùng để đưa ra kết luận phổ quát về mọi dữ liệu cùng loại. CDC là bài toán học thuật, không tạo ra chẩn đoán y khoa. Dữ liệu nhà ở và thương mại điện tử phản ánh schema, thời điểm và quy trình thu thập cụ thể. Chuỗi AAPL là một ảnh chụp lịch sử và luôn được so với baseline dự đoán giá đóng cửa phiên kế tiếp bằng giá cuối chuỗi; kết quả không được diễn giải thành chiến lược đầu tư. Với Oxford-IIIT Pet, kết quả Keras có sẵn chỉ đi vào bảng matched chính nếu scratch, Keras và PyTorch dùng cùng tập khóa mẫu.

Ba câu hỏi nghiên cứu định hướng toàn bộ thực nghiệm:

- **RQ1:** Khi giữ cùng dữ liệu đã xử lý, split, topology logic, budget huấn luyện và metric, kết quả của implementation scratch, Keras và PyTorch khác nhau ở mức nào?
- **RQ2:** ML cơ bản, CNN và RNN phù hợp với những giả định cấu trúc dữ liệu nào, và điều gì xảy ra khi kiến trúc được áp dụng ngoài dạng dữ liệu tự nhiên của nó?
- **RQ3:** Làm thế nào chuyển một artifact thực nghiệm thành luồng inference có thể kiểm thử, đồng thời giữ nhất quán preprocessing, model version và giới hạn diễn giải?

RQ1 không giả định ba framework phải tạo ra trọng số hoặc metric giống hệt nhau. Sai khác số học, quy ước logits/probability, thứ tự mini-batch và kernel backend có thể làm quỹ đạo tối ưu khác nhau. So sánh chỉ có ý nghĩa khi các biến kiểm soát được công bố. RQ2 cũng không tìm một kiến trúc “tốt nhất” chung cho mọi bài toán; nó xem xét mức độ phù hợp giữa inductive bias và cấu trúc dữ liệu. RQ3 giới hạn ở triển khai inference phục vụ minh họa và smoke test, không bao gồm cam kết SLA, bảo mật sản xuất, giám sát drift dài hạn hoặc đánh giá tác động thực địa.

Các thí nghiệm được thiết kế theo giới hạn phần cứng của môi trường học tập. Seed mặc định là 42; ưu tiên chạy CPU và chỉ dùng GPU khi môi trường sẵn có được ghi nhận. Một clean run là bắt buộc. Chỉ chạy thêm seed 52 và 62 khi full matched run không vượt ngưỡng thời gian đã khóa. Nếu scratch CNN trên toàn bộ dữ liệu vượt giới hạn vận hành, một benchmark subset phân tầng cố định được phép sử dụng, nhưng cả ba framework phải chuyển sang đúng cùng subset. Quyết định này làm giảm phạm vi suy diễn nhưng giữ tính công bằng của so sánh.

## 0.4. Phương pháp và cấu trúc tiểu luận

Tiểu luận kết hợp bốn phương pháp. Thứ nhất, nghiên cứu tài liệu được dùng để xây dựng lịch sử và nền tảng thuật toán; nguồn gốc như bài báo, sách và kho lưu trữ học thuật được ưu tiên hơn nội dung tổng hợp. Thứ hai, audit notebook và artifact xác định dữ liệu nào đã tồn tại, cell nào đã chạy, metric nào có prediction nguồn và khoảng trống nào cần bổ sung. Thứ ba, controlled experiment giữ một hợp đồng chung về split, preprocessing, kiến trúc và đánh giá. Thứ tư, artifact-first reporting yêu cầu bảng và hình được sinh từ CSV/JSON/prediction có thể truy vết, thay vì sao chép số từ output màn hình.

Trong mỗi matched track, bộ tiền xử lý chỉ được fit trên TRAIN. VALIDATION dùng để chọn hyperparameter, threshold, checkpoint và early stopping; TEST chỉ được mở cho đánh giá sau khi cấu hình đã khóa. Classification báo metric theo lớp và metric phù hợp với mất cân bằng; regression báo sai số trên đơn vị thật. Parameter count được đối chiếu bằng shape hoặc API. Thời gian chạy chỉ mô tả môi trường và lần chạy cụ thể, không được dùng để kết luận một framework nhanh hơn một cách phổ quát.

Nội dung còn lại được tổ chức như sau. Chương 1 trình bày lịch sử phát triển AI và rút ra các điều kiện làm nên tiến bộ: biểu diễn, dữ liệu, năng lực tính toán, thuật toán tối ưu và protocol đánh giá. Chương 2 trình bày ML có giám sát, các baseline cổ điển và matched MLP trên ba dataset bảng. Chương 3 giải thích CNN, mô tả ba dataset và so sánh scratch/Keras/PyTorch trên các track đủ điều kiện. Chương 4 trình bày Vanilla RNN, BPTT và hai bài toán chuỗi. Phần triển khai mô tả luồng input–validate–preprocess–model–response, provenance và kiểm thử. Kết luận trả lời ba câu hỏi nghiên cứu, tổng hợp giới hạn và xác định hướng mở rộng.

Với cấu trúc này, phần lịch sử không đứng tách khỏi thực nghiệm. Những giới hạn từng xuất hiện trong lịch sử AI—kỳ vọng vượt quá dữ liệu, compute hoặc khả năng đánh giá—được chuyển thành nguyên tắc kiểm soát ở các chương sau. Mọi kết quả vì vậy được đọc trong phạm vi protocol của tiểu luận: nó cho thấy điều gì trên tập dữ liệu và cấu hình đã công bố, đồng thời nêu rõ điều chưa thể suy ra.
