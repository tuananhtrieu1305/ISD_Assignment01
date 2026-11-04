<!-- page_target: 3-4; style: term_paper/config/style_spec.md -->

# MỞ ĐẦU

## 0.1. Bối cảnh và lý do chọn đề tài

Trí tuệ nhân tạo (Artificial Intelligence — AI) không hình thành từ một thuật toán đơn lẻ. Lĩnh vực này phát triển qua nhiều cách tiếp cận: suy luận dựa trên luật, biểu diễn tri thức, tìm kiếm, học máy thống kê và mạng neuron. Machine Learning (ML) ước lượng quy luật từ dữ liệu; Convolutional Neural Network (CNN) khai thác cấu trúc cục bộ; Recurrent Neural Network (RNN) mô hình hóa thứ tự bằng trạng thái ẩn. Knowledge Base/Knowledge Graph (KB/KG) biểu diễn tri thức có quan hệ, còn Retrieval-Augmented Generation (RAG) truy hồi bằng chứng ngoài trước khi trả lời. Chuỗi kỹ thuật này cho phép khảo sát AI từ mô hình dự đoán đến hệ thống hỏi đáp có provenance [@goodfellow2016deep; @hogan2021knowledgegraphs; @lewis2020rag].

Việc chỉ trình bày công thức hoặc gọi một thư viện huấn luyện chưa đủ để cho thấy mô hình hoạt động như thế nào. Một kết quả thực nghiệm còn phụ thuộc vào cách chia dữ liệu, phạm vi fit bộ tiền xử lý, seed, hàm mất mát, tiêu chí chọn checkpoint và cách tính metric. Nếu các yếu tố đó thay đổi giữa các implementation, chênh lệch kết quả không còn phản ánh riêng framework hoặc thuật toán. Ngược lại, cài đặt hoàn toàn từ đầu giúp nhìn rõ phép toán nhưng có thể che khuất các vấn đề thực tế như lưu mô hình, suy luận theo batch và kiểm soát dữ liệu. Vì vậy, tiểu luận lựa chọn cách tiếp cận song song: triển khai từ nền tảng (scratch), Keras và PyTorch dưới một protocol chung.

Đề tài cũng xuất phát từ nhu cầu nối các bài thực hành riêng lẻ thành một chu trình có thể kiểm chứng. Các notebook hiện có đã xử lý dữ liệu bảng, ảnh và chuỗi thời gian, nhưng mỗi bài được xây dựng cho một mục tiêu học tập khác nhau. Nếu ghép trực tiếp các metric cuối cùng, sự khác biệt về split, preprocessing hoặc kiến trúc có thể tạo ra một so sánh thiếu công bằng. Tiểu luận vì vậy không coi notebook là văn bản báo cáo hoàn chỉnh. Chúng được dùng như nguồn bằng chứng ban đầu; dữ liệu, cấu hình, prediction và metric phải được truy vết trước khi đưa vào bảng tổng hợp.

Một lý do khác là khoảng cách giữa mô hình trong notebook và một chức năng inference có thể sử dụng. Mô hình đạt metric trên tập TEST chưa tự động trở thành một hệ thống triển khai được. Đầu vào mới cần được kiểm tra, biến đổi bằng đúng preprocessor đã fit trên TRAIN, chuyển qua đúng phiên bản mô hình và trả về output có diễn giải. Với bài toán sức khỏe hoặc tài chính, output còn phải đi kèm giới hạn sử dụng; dự đoán thực nghiệm không phải chẩn đoán y khoa hay khuyến nghị đầu tư. Phần triển khai trong tiểu luận được xem là phép kiểm tra cuối của tính nhất quán giữa dữ liệu, mô hình và mã suy luận, không phải tuyên bố về một sản phẩm sẵn sàng vận hành.

Từ các vấn đề trên, đề tài “Lịch sử phát triển AI và thực nghiệm ML, CNN, RNN, Knowledge Graph và RAG” được lựa chọn nhằm trả lời hai nhu cầu. Về học thuật, báo cáo hệ thống hóa các mốc phát triển và giải thích cơ chế của mô hình dự đoán lẫn truy hồi tri thức. Về thực nghiệm, báo cáo xây dựng đường dẫn từ dữ liệu thô đến kết quả và triển khai, trong đó mỗi con số quan trọng gắn với artifact có thể tái tính. Cách tổ chức này phân biệt điều thí nghiệm chứng minh với điều nằm ngoài phạm vi.

## 0.2. Mục tiêu nghiên cứu

Mục tiêu tổng quát của tiểu luận là xây dựng một khảo sát có hệ thống về AI, ML, CNN, RNN, KB/KG và RAG, đồng thời kiểm chứng các khái niệm bằng thực nghiệm tái lập trên nhiều dạng dữ liệu. Báo cáo không hướng đến kết quả state-of-the-art. Trọng tâm Chương 2–4 là hiểu cơ chế và so sánh ba implementation trong cùng điều kiện; Chương 5 đánh giá năm cấu hình retrieval trên cùng corpus và evaluator.

Các mục tiêu cụ thể gồm:

1. Hệ thống hóa lịch sử AI từ các tiền đề về logic và neuron nhân tạo, qua AI biểu tượng, học máy thống kê, deep learning, Transformer đến mô hình nền tảng và AI tạo sinh.
2. Trình bày nguyên lý của các kỹ thuật ML cơ bản cho classification và regression; giải thích vai trò của dữ liệu, hàm mất mát, tối ưu hóa và đánh giá khả năng khái quát.
3. Làm rõ cách CNN sử dụng convolution, activation và pooling để học đặc trưng không gian; khảo sát cả ảnh RGB và trường hợp chuyển dữ liệu bảng thành chuỗi một chiều có kiểm soát.
4. Làm rõ cơ chế trạng thái ẩn, Backpropagation Through Time và gradient clipping của Vanilla RNN; đặt kết quả trong quan hệ với LSTM, attention và giới hạn phụ thuộc dài hạn [@elman1990structure; @hochreiter1997lstm].
5. Xây dựng các implementation tương ứng bằng NumPy scratch, Keras và PyTorch; dùng cùng sample keys, split, preprocessing output, topology logic và budget trong mỗi matched track.
6. Đánh giá mô hình bằng prediction artifact thay vì nhập metric thủ công; báo cáo accuracy, precision, recall, F1 hoặc MAE, RMSE, R² theo đúng loại bài toán, kèm baseline và failure case.
7. Xây dựng KB/KG cho miền y khoa và báo cáo doanh nghiệp; so sánh sparse, dense, hybrid, graph-only và graph-guided RAG bằng retrieval, answer, citation, latency, ablation và challenge metric.
8. Triển khai các luồng inference có kiểm tra đầu vào, nạp đúng model/index/preprocessor, cung cấp provenance/citation và từ chối khi không đủ bằng chứng.

Các mục tiêu trên được sắp xếp theo chuỗi “lịch sử — cơ chế — thực nghiệm — tri thức/truy hồi — triển khai”. Chuỗi này tránh hai cực: báo cáo chỉ tóm lược lý thuyết nhưng thiếu kiểm chứng, hoặc tập notebook có nhiều output nhưng thiếu lập luận xuyên suốt.

## 0.3. Đối tượng, phạm vi và câu hỏi nghiên cứu

Đối tượng nghiên cứu gồm ba họ mô hình dự đoán và một hệ truy hồi tri thức. Chương 2 khảo sát ML cơ bản và Multilayer Perceptron (MLP) trên dữ liệu bảng; Chương 3 tập trung vào CNN trên ảnh và Conv1D; Chương 4 dùng Vanilla RNN cho chuỗi hành vi và chuỗi thời gian. Chương 5 khảo sát KB, property graph và RAG bằng năm cấu hình B0–B4. LSTM, Transformer, mô hình nền tảng và full GraphRAG community-summary chỉ được dùng để đặt bối cảnh, không thay thế protocol đã khóa.

Phạm vi dữ liệu gồm tám dataset instance cho Chương 2–4 và ba nguồn mới cho Chương 5. Các nguồn cũ là CDC Diabetes, Vietnam Housing 2024, Synthetic E-Commerce, EuroSAT RGB, Oxford-IIIT Pet, Online Retail II và AAPL 2015–2025 [@helber2019eurosat; @helber2023eurosatdata; @parkhi2012catsdogs; @chen2012onlineretailii]. Chương 5 dùng MedQuAD cho hỏi đáp diabetes, FinQA cho retrieval/suy luận số trên báo cáo doanh nghiệp và 10 snapshot Wikidata khóa revision cho liên kết thực thể [@benabacha2019medquad; @chen2021finqa; @wikidata2026dataaccess].

Các dataset không được dùng để đưa ra kết luận phổ quát về mọi dữ liệu cùng loại. CDC là bài toán học thuật, không tạo ra chẩn đoán y khoa. Dữ liệu nhà ở và thương mại điện tử phản ánh schema, thời điểm và quy trình thu thập cụ thể. Chuỗi AAPL là một ảnh chụp lịch sử và luôn được so với baseline dự đoán giá đóng cửa phiên kế tiếp bằng giá cuối chuỗi; kết quả không được diễn giải thành chiến lược đầu tư. Với Oxford-IIIT Pet, kết quả Keras có sẵn chỉ đi vào bảng matched chính nếu scratch, Keras và PyTorch dùng cùng tập khóa mẫu.

Bốn câu hỏi nghiên cứu định hướng toàn bộ thực nghiệm:

- **RQ1:** Khi giữ cùng dữ liệu đã xử lý, split, topology logic, budget huấn luyện và metric, kết quả của implementation scratch, Keras và PyTorch khác nhau ở mức nào?
- **RQ2:** ML cơ bản, CNN và RNN phù hợp với những giả định cấu trúc dữ liệu nào, và điều gì xảy ra khi kiến trúc được áp dụng ngoài dạng dữ liệu tự nhiên của nó?
- **RQ3:** Làm thế nào chuyển một artifact thực nghiệm thành luồng inference có thể kiểm thử, đồng thời giữ nhất quán preprocessing, model version và giới hạn diễn giải?
- **RQ4:** Việc bổ sung lân cận Knowledge Graph vào RAG thay đổi retrieval, citation, latency và hành vi từ chối như thế nào trên MedQuAD diabetes và FinQA?

RQ1 không giả định ba framework phải tạo trọng số hoặc metric giống hệt nhau; sai khác số học và backend vẫn tồn tại. RQ2 không tìm một kiến trúc “tốt nhất” chung. RQ3 giới hạn ở inference minh họa và smoke test, không bao gồm cam kết SLA hay đánh giá tác động thực địa. RQ4 tách retrieval khỏi answer correctness: Recall@k cao hơn không đủ để khẳng định câu trả lời đúng, giảm hallucination hay giải được numerical reasoning.

Các thí nghiệm được thiết kế theo giới hạn phần cứng của môi trường học tập. Seed mặc định là 42; ưu tiên chạy CPU và chỉ dùng GPU khi môi trường sẵn có được ghi nhận. Một clean run là bắt buộc. Chỉ chạy thêm seed 52 và 62 khi full matched run không vượt ngưỡng thời gian đã khóa. Nếu scratch CNN trên toàn bộ dữ liệu vượt giới hạn vận hành, một benchmark subset phân tầng cố định được phép sử dụng, nhưng cả ba framework phải chuyển sang đúng cùng subset. Quyết định này làm giảm phạm vi suy diễn nhưng giữ tính công bằng của so sánh.

## 0.4. Phương pháp và cấu trúc tiểu luận

Tiểu luận kết hợp năm phương pháp. Thứ nhất, nghiên cứu tài liệu dùng nguồn gốc để xây dựng lịch sử và nền tảng. Thứ hai, audit notebook/artifact xác định dữ liệu, cell, prediction và khoảng trống. Thứ ba, controlled experiment giữ hợp đồng chung về split, preprocessing, kiến trúc và đánh giá cho Chương 2–4. Thứ tư, Chương 5 dùng evaluation contract riêng: cùng corpus, top-k và evaluator; tune trên VALIDATION; public TEST chỉ mở một lần sau khi khóa cấu hình. Thứ năm, artifact-first reporting yêu cầu bảng/hình sinh từ CSV/JSON/prediction có thể truy vết.

Trong mỗi matched track, bộ tiền xử lý chỉ được fit trên TRAIN. VALIDATION dùng để chọn hyperparameter, threshold, checkpoint và early stopping; TEST chỉ được mở cho đánh giá sau khi cấu hình đã khóa. Classification báo metric theo lớp và metric phù hợp với mất cân bằng; regression báo sai số trên đơn vị thật. Parameter count được đối chiếu bằng shape hoặc API. Thời gian chạy chỉ mô tả môi trường và lần chạy cụ thể, không được dùng để kết luận một framework nhanh hơn một cách phổ quát.

Nội dung còn lại được tổ chức như sau. Chương 1 trình bày lịch sử AI. Chương 2 trình bày ML có giám sát, baseline và matched MLP. Chương 3 giải thích CNN và so sánh scratch/Keras/PyTorch. Chương 4 trình bày Vanilla RNN, BPTT và hai bài toán chuỗi. Chương 5 xây KB/KG, so sánh B0–B4 trên MedQuAD/FinQA và triển khai Agent có citation/refusal. Deployment của MLP, CNN, RNN và KG-RAG được đặt ngắn ở cuối chương tương ứng thay vì thành chương riêng. Kết luận trả lời bốn câu hỏi nghiên cứu, tổng hợp giới hạn và hướng mở rộng.

Với cấu trúc này, phần lịch sử không đứng tách khỏi thực nghiệm. Những giới hạn từng xuất hiện trong lịch sử AI—kỳ vọng vượt quá dữ liệu, compute hoặc khả năng đánh giá—được chuyển thành nguyên tắc kiểm soát ở các chương sau. Mọi kết quả vì vậy được đọc trong phạm vi protocol của tiểu luận: nó cho thấy điều gì trên tập dữ liệu và cấu hình đã công bố, đồng thời nêu rõ điều chưa thể suy ra.
