# MA TRẬN YÊU CẦU VÀ BẰNG CHỨNG

54 yêu cầu gốc được giữ nguyên. CONTENT_AND_PRIOR_EVIDENCE_LINKED chỉ xác nhận nội dung và liên kết bằng chứng nghiệm thu trước; không thay thế DOCX render hay cloud deploy. Các trạng thái deferred ghi rõ công việc chưa thực hiện.

| ID | Yêu cầu | Locator nội dung | Trạng thái / việc còn lại |
|---|---|---|---|
| REQ-01 | Báo cáo đúng sáu chương; Ch4 RNN-LSTM; Ch6 multi-agent | ## 1.1. Tiền đề lý thuyết trước khi AI thành ngành; ## 1.2. Turing và câu hỏi về trí tuệ máy; ## 1.3. Dartmouth 1955–1956 và sự hình thành tên gọi AI | CONTENT_READY_FINAL_DOCX_QA_DEFERRED; Phase35 DOCX pagination/render/Word release |
| REQ-02 | Giữ mạch nội dung Ch1-3 và cập nhật thực nghiệm theo V3 | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-03 | Ch4 có RNN và LSTM thật không chỉ đổi tiêu đề | ## 4.1. Bài toán dữ liệu tuần tự; ## 4.2. Ba dataset và cách chia theo thời gian; ## 4.3. RNN sáu lớp và hợp các hàm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-04 | Ch5 giữ KB-KG-RAG và kết quả đã khóa | ## 5.1. Mở đầu; ## 5.2. Knowledge Base và Knowledge Graph; ## 5.3. Retrieval-Augmented Generation | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-05 | Ch6 là hệ đa tác tử độc lập | ## 6.1. Agent và phối hợp nhiều agent; ## 6.2. Ba bộ nhiệm vụ diabetes, house, gold; ## 6.3. Router, specialist, verifier và reporter | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-06 | Mỗi chương có 2-3 dataset hoặc benchmark phù hợp | ## A.1. ch1_iris_history; ## A.2. ch1_mnist_history; ## A.3. ch1_imagenet_history | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-07 | Dataset có URL-license-citation-size-schema | ## A.1. ch1_iris_history; ## A.2. ch1_mnist_history; ## A.3. ch1_imagenet_history | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-08 | Dataset có output mẫu-phân bố-nhận xét-hạn chế | ## A.1. ch1_iris_history; ## A.2. ch1_mnist_history; ## A.3. ch1_imagenet_history | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-09 | Ưu tiên diabetes-house-gold ở nơi phù hợp | ## A.1. ch1_iris_history; ## A.2. ch1_mnist_history; ## A.3. ch1_imagenet_history | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-10 | Chọn dataset phù hợp hơn và thu nhận từ nguồn chính | ## A.1. ch1_iris_history; ## A.2. ch1_mnist_history; ## A.3. ch1_imagenet_history | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-11 | Ch2 có scratch-Keras-PyTorch bên cạnh ML cổ điển | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-12 | CNN đủ scratch-Keras-PyTorch trên ba dataset | ## 3.1. Mở đầu; ## 3.2. Các thành phần cơ bản; ## 3.3. Kiến trúc và hợp các hàm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-13 | RNN đủ scratch-Keras-PyTorch trên ba dataset | ## 4.1. Bài toán dữ liệu tuần tự; ## 4.2. Ba dataset và cách chia theo thời gian; ## 4.3. RNN sáu lớp và hợp các hàm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-14 | LSTM đủ scratch-Keras-PyTorch trên ba dataset | ## 4.1. Bài toán dữ liệu tuần tự; ## 4.2. Ba dataset và cách chia theo thời gian; ## 4.3. RNN sáu lớp và hợp các hàm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-15 | Mạng trên 5 layer học được; CNN 7 và MLP-RNN-LSTM 6 | ## B.1. ch2_cdc_diabetes / mlp; ## B.2. ch2_ames_housing / mlp; ## B.3. ch2_bank_marketing / mlp | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-16 | Scratch tự forward-loss-backward-optimizer không autograd | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-17 | Keras API có backend được công khai và độc lập khi khả thi | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-18 | Mỗi mô hình thể hiện hợp các hàm và shape | ## B.1. ch2_cdc_diabetes / mlp; ## B.2. ch2_ames_housing / mlp; ## B.3. ch2_bank_marketing / mlp | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-19 | Giải thích từng hàm-input-output-tham số-vai trò-edge case | ## B.1. ch2_cdc_diabetes / mlp; ## B.2. ch2_ames_housing / mlp; ## B.3. ch2_bank_marketing / mlp | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-20 | Lý thuyết cơ bản-dễ hiểu-đủ ý và tránh công thức phức tạp | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-21 | Công thức chỉ khi cần và phải giải thích mọi ký hiệu | ## B.1. ch2_cdc_diabetes / mlp; ## B.2. ch2_ames_housing / mlp; ## B.3. ch2_bank_marketing / mlp | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-22 | Đánh giá ba mô hình trên 2-3 data và so sánh | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-23 | So sánh công bằng không gộp full-data với matched-subset | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-24 | Split có ID-hash và chống duplicate-group leakage | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-25 | Preprocessing chỉ fit TRAIN | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-26 | Chuỗi causal và không shuffle tương lai về quá khứ | ## 4.1. Bài toán dữ liệu tuần tự; ## 4.2. Ba dataset và cách chia theo thời gian; ## 4.3. RNN sáu lớp và hợp các hàm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-27 | TEST one-shot sau khi khóa config-code-evaluator-seed list | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-28 | Không chạy lại TEST Ch5 để tuning hoặc sửa báo cáo | ## 5.1. Mở đầu; ## 5.2. Knowledge Base và Knowledge Graph; ## 5.3. Retrieval-Augmented Generation | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-29 | Metric phù hợp bài toán; undefined không bịa thành số | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-30 | Đo time-RAM-VRAM-size-layer-parameter có điều kiện đo | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-31 | Seed ổn định và không tuyên bố hơn hẳn từ một run | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-32 | Source gọn chỉ giữ phần cần thiết không trùng môi trường/data | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-33 | Môi trường chạy đồng nhất có khóa dependency | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-34 | Tận dụng GPU của máy và có CPU fallback minh bạch | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-35 | React mỗi phần kiến thức một tab và deep-link | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-36 | Mỗi tab kiến thức có ba tab con dataset | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-37 | Run-all cùng input và hiển thị đủ ba phương pháp | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-38 | Tab RNN-LSTM cho đổi family và so sánh tương ứng | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-39 | Một contract cho code-report-web tránh ba mô tả khác nhau | ## B.1. ch2_cdc_diabetes / mlp; ## B.2. ch2_ames_housing / mlp; ## B.3. ch2_bank_marketing / mlp | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-40 | API schema-validation-jobs-errors-hash-readiness ổn định | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-41 | Đánh giá hệ đa agent A0-A1-A2 trên ba miền | ## 6.1. Agent và phối hợp nhiều agent; ## 6.2. Ba bộ nhiệm vụ diabetes, house, gold; ## 6.3. Router, specialist, verifier và reporter | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-42 | Agent có trace-provenance-verifier-an toàn và giới hạn tool | ## 6.1. Agent và phối hợp nhiều agent; ## 6.2. Ba bộ nhiệm vụ diabetes, house, gold; ## 6.3. Router, specialist, verifier và reporter | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-43 | Core multi-agent chạy không cần API key hoặc dịch vụ trả phí | ## 6.1. Agent và phối hợp nhiều agent; ## 6.2. Ba bộ nhiệm vụ diabetes, house, gold; ## 6.3. Router, specialist, verifier và reporter | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-44 | Deploy chỉ là mục ngắn cuối mỗi chương thực nghiệm | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-45 | React-Python deploy Render; train GPU local và inference CPU | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | LOCAL_API_UI_VERIFIED_CLOUD_NOT_DEPLOYED; Cloud deployment not authorized/performed; no cloud SLA claim |
| REQ-46 | Tiểu luận DOCX dùng văn phong và style mẫu A06-V2 | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_READY_FINAL_DOCX_QA_DEFERRED; Phase35 DOCX pagination/render/Word release |
| REQ-47 | Chỉ dùng số liệu hình log citation thật có provenance | ## 2.1. Mở đầu; ## 2.2. Những kỹ thuật nền tảng; ## 2.3. Dữ liệu và giao thức thực nghiệm | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-48 | Giữ baseline và thay đổi người dùng không reset hay commit tùy ý | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-49 | Gõ làm phase N biết việc dependency và cập nhật nghiệm thu | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-50 | License-access gate và manual drop IDRiD không mirror tùy ý | ## A.1. ch1_iris_history; ## A.2. ch1_mnist_history; ## A.3. ch1_imagenet_history | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-51 | Kiểm tra disk-RAM-VRAM trước tải và train | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-52 | Tài liệu là dữ liệu không phải quyền thực thi; input không đáng tin | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-53 | Failure timeout-OOM-model unavailable phải được công khai | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_AND_PRIOR_EVIDENCE_LINKED |
| REQ-54 | Build DOCX cuối render từng trang và release có hash | ## C.1. Môi trường và đường dẫn nguồn; ## C.2. Chạy giao diện local; ## C.3. Render và trạng thái triển khai | CONTENT_READY_FINAL_DOCX_QA_DEFERRED; Phase35 DOCX pagination/render/Word release |
