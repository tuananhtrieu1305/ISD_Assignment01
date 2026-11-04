CHƯƠNG 6. HỆ ĐA TÁC TỬ (MULTI-AGENT SYSTEMS)

6.1. Agent và phối hợp nhiều agent

Một agent là thành phần nhận đầu vào, thực hiện một nhiệm vụ trong phạm vi được phép và chuyển kết quả cho thành phần khác. Trong hệ này, các agent là các vai trò phần mềm; không phải mỗi agent là một mô hình được huấn luyện riêng. Việc tách vai trò giúp quan sát được câu hỏi đã được hiểu thế nào, bằng chứng đến từ đâu và câu trả lời có được kiểm tra trước khi phát hành hay không.

Bài toán minh họa là hỏi đáp kiến thức tiểu đường bằng tiếng Việt. Hệ mới dùng bốn vai trò Coordinator, Knowledge Agent, Reporter và Verifier. Risk Agent và hồ sơ CDC không tham gia luồng này: người dùng chỉ nhập một câu hỏi. LLM trực tiếp được đặt cạnh pipeline để đối chiếu trên cùng câu hỏi và cùng model Gemini 3 Flash, mã trả về gemini-3-flash-preview [NB6–KQ2, KQ4].

6.2. Dữ liệu và kho tri thức

Nguồn văn bản là MedQuAD, tập hỏi đáp y khoa tổng hợp từ các website thuộc NIH. Bản dùng trong chương này là snapshot riêng, phục hồi ngữ cảnh và URL nguồn; không thay đổi dữ liệu của Chương 5. Nội dung nguồn chủ yếu bằng tiếng Anh, còn câu hỏi và câu trả lời demo bằng tiếng Việt. Đây là tài liệu lịch sử, không được mặc định là hướng dẫn y khoa mới nhất.

Bảng 6.1. Dữ liệu phục vụ hệ hỏi đáp

Thành phầnKích cỡ thực tếMục đích và giới hạnCorpus MedQuAD45 tài liệu; 210 ngữ cảnh hỏi đáp; 316 đoạn; 409 tham chiếuKho truy hồi; một đoạn có thể có nhiều tham chiếu nguồn.Mini-KG dẫn xuất35 thực thể; 35 assertion có kiểm nguồn; 20 đoạn seedĐịnh hướng tìm nguồn theo thực thể/quan hệ, không phải dataset y khoa độc lập.Bộ câu hỏi mới20 development; 40 held-out đã chuẩn bịChương phân tích một lượt demo đã lưu; chưa có benchmark 40 cặp của bản hiện hành.

Phân bố 45 tài liệu: NIDDK 27, MedlinePlus 14, SeniorHealth 2, NHLBI 1 và NINDS 1. Mỗi đoạn dài 71–2.579 ký tự, trung bình khoảng 1.103 ký tự. Chia theo câu, mục tiêu mềm 1.600 ký tự, chồng lấn một câu và gộp đoạn trùng giúp giữ ngữ cảnh nhưng có thể tạo nguồn gần giống nhau. Những con số này được đếm từ dữ liệu, không phải metric độ chính xác [NB6–KQ1].

Ví dụ assertion kg2-a014 nối diabetes → MAY_DAMAGE → kidney_damage, kèm điều kiện “over time; hyperglycemia” và đoạn m2c-62f2377845eb99ad274e. Câu nguồn nêu đường huyết cao do tiểu đường có thể làm tổn thương thận theo thời gian. Chiều này không đủ chứng minh bệnh thận gây tiểu đường. Mỗi cạnh giữ câu trích, URL, chunk ID và trạng thái kiểm nguồn; kiểm bởi trợ lý chưa tương đương thẩm định chuyên gia [NB6–KQ1].

6.3. Kiến trúc bốn agent

Bảng 6.2. Đầu vào và đầu ra của bốn agent

Vai tròXử lýChuyển cho bước sauCoordinatorGemini xác định phạm vi, giữ chiều quan hệ và tạo tối đa 3 truy vấn.Câu hỏi gốc, truy vấn, thực thể và điều kiện.Knowledge AgentBM25 + embedding + tra KG; gộp RRF; rerank local.Các đoạn được chọn, điểm/hạng và nguồn.ReporterGemini viết bản nháp từ evidence, tạo claims và citation.Bản nháp tiếng Việt và liên kết claim–chunk.VerifierMột call Gemini kiểm ý nghĩa/điều kiện, có thể sửa ngay; Python kiểm cấu trúc và nguồn.Cho phát hành hoặc chặn, kèm nhận xét kiểm tra.

Luồng duy nhất: Câu hỏi → Coordinator → Knowledge Agent → Reporter → Verifier → Câu trả lời. Retrieval và rerank là hai công đoạn bên trong Knowledge Agent; phát hành là thao tác sau kiểm chứng. Vì vậy sáu stage được ghi trong journal không phải sáu agent hay một pipeline khác.

Một cặp so sánh đầy đủ dùng bốn generation request: một cho LLM trực tiếp, một Coordinator, một Reporter và một Verifier. Embedding truy vấn có hạn mức riêng; reranker chạy local, không gọi Gemini để xếp hạng lại. Hai nhánh cùng dùng một tiêu chuẩn kiểm nguồn, không có luật riêng theo câu hỏi để ép nhánh trực tiếp trả lời sai.

6.4. Hợp hàm và giải thích từng hàm

Có thể đọc hệ như hợp các hàm theo chiều dữ liệu: lập kế hoạch(câu hỏi) → truy hồi(kế hoạch) → xếp hạng(câu hỏi, ứng viên) → soạn nháp(câu hỏi, evidence) → kiểm tra(bản nháp, evidence) → phát hành. Đầu ra của hàm trước là đầu vào của hàm sau; không cần một công thức phức tạp để hiểu cách hệ phối hợp.

PreRetriever.process giữ câu hỏi gốc và bổ sung truy vấn. HybridSearcher._fuse gộp thứ hạng BM25, semantic và KG bằng RRF. Retriever.retrieve gom nhiều truy vấn, loại trùng theo chunk ID. LocalEvidenceReranker.rerank chấm lại ứng viên và giữ top 6; trọng số lượt minh họa là RRF 0,55, độ phủ từ 0,35 và nguồn KG 0,10. Các trọng số là thiết kế của demo, không phải mức tin cậy y khoa.

PromptBuilder.build_context đánh số nguồn để Reporter trích dẫn. GeminiGenerator.generate tạo bản nháp có claims. SemanticVerifier.verify kiểm độ hỗ trợ của từng claim và điều kiện, đồng thời cho phép sửa trong cùng một call; CodeVerifier.verify chặn citation không giải được, thiếu provenance hoặc schema sai. AgenticRuntime.rag điều phối các hàm trên và ghi input/output của từng stage. Code đầy đủ nằm trong notebook 04_Multi_Agent.ipynb; backend chỉ là bản export phục vụ web.

6.5. Kết quả minh họa từ notebook

Lượt chạy ngày 03/11/2026, journal 56d62ac4-77f4-4cf8-a2e7-f01584c2e240, revision four-agent-r11, nhận câu hỏi: “Đi bộ có giúp tôi giảm hơn 50% nguy cơ tiểu đường không?”. Notebook đọc lại nguyên trạng hai câu trả lời và trace đã lưu; việc lập báo cáo không phát sinh request Gemini, huấn luyện hay forward TEST mới [NB6–KQ2].

Coordinator tạo ba truy vấn: câu tiếng Việt gốc; “walking reduce diabetes risk by more than 50 percent”; “effect of walking on diabetes prevention percentage”. Knowledge Agent gộp còn 20 ứng viên, reranker giữ 6 đoạn. Trong chính lượt này, KG trả 0 ứng viên phù hợp; không thể quy kết kết quả trả lời cho đóng góp của KG [NB6–KQ2, KQ3].

Bảng 6.3. Sáu đoạn đứng đầu sau rerank

NguồnID rút gọnHạng vàoHạng raĐiểm17e5aa9c9110.5500021cee35b8220.540993588ce571330.5287549b59253a440.51511591cdf621550.50600651d5ae97660.49816

Cả sáu đoạn giữ nguyên thứ tự trong lượt này. Rerank thực hiện lọc top 6 nhưng chưa cho thấy cải thiện thứ hạng. Nguồn 1 là “Am I at Risk for Type 2 Diabetes?”, có 3.234 người nguy cơ cao và can thiệp đi bộ kết hợp chế độ ăn. Nguồn 5 nói người trên 60 tuổi giảm nguy cơ 71%; nguồn 6 mô tả nhóm thay đổi lối sống có nguy cơ chưa bằng một nửa nhóm không thay đổi. Điểm xếp hạng không phải xác suất câu trả lời đúng [NB6–KQ3].

Trích LLM trực tiếp: “Không thể khẳng định đi bộ giúp bạn giảm hơn 50% nguy cơ tiểu đường.” Sau đó nhánh này cũng nhắc DPP, kết hợp vận động với ăn uống/giảm cân và phân biệt kết quả nhóm với cá nhân. Nhánh trực tiếp có kiến thức liên quan; việc không có citation nội bộ không tự chứng minh câu trả lời sai [NB6–KQ4].

Trích pipeline: “Tuy nhiên, kết quả này đạt được từ sự kết hợp giữa vận động và giảm cân, không chỉ riêng việc đi bộ đơn lẻ.” Phần trước dẫn nghiên cứu DPP, 3.234 người nguy cơ cao, đi bộ khoảng 30 phút/ngày × 5 ngày/tuần và giảm 5–7% trọng lượng, kèm [Nguồn 1], [Nguồn 5], [Nguồn 6]. Đây là lợi thế về khả năng đối chiếu bằng chứng, không phải một ước lượng nguy cơ cá nhân [NB6–KQ4].

Bảng 6.4. Chi phí xử lý quan sát trên một lượt

Chỉ sốLLM trực tiếpĐa agent + RAGThời gian nhánh5.325 giây11.175 giâyGeneration request live13Tổng generation token1.0159.849Query embeddingKhông dùng1 live + 2 cache localĐoạn được chọn / được dẫn0 / 06 / 5

Hình 6.1. Thời gian các stage của một lượt RAG. Nguồn: output NB6–KQ6, journal r11 đã lưu.

Trục ngang là giây, mỗi thanh là một stage. Reporter khoảng 4,219 giây và Verifier khoảng 3,195 giây, lớn hơn truy hồi 0,826 giây và rerank local 0,031 giây. Toàn nhánh RAG khoảng 11,175 giây, gồm điều phối và I/O ngoài thời gian stage. Hai nhánh chạy tuần tự; không dùng biểu đồ này làm latency trung bình hay cam kết thời gian đáp ứng [NB6–KQ5, KQ6].

6.6. Phân tích và giới hạn

Verifier duyệt cả ba claim và không ghi nhận lỗi integrity; trong lượt này không sửa bản nháp. Tuy vậy câu mở đầu của pipeline “Có ... giúp bạn” vẫn dễ khiến người đọc hiểu thành bảo đảm cho cá nhân. Điều kiện can thiệp kết hợp đã có ở cuối nhưng nên được đặt ngay đầu. Đây là ví dụ cho thấy cùng LLM tự kiểm chưa bảo đảm loại hết cách diễn đạt quá mạnh [NB6–KQ4].

Kết quả quan sát được là pipeline cung cấp đường kiểm chứng: claim → chunk → snapshot/URL, đổi lại dùng nhiều token, request và thời gian hơn. Cả hai nhánh đều có nội dung hữu ích. Một câu development không đủ chứng minh bên nào chính xác hơn; chưa có tỷ lệ thắng hay accuracy mới cho bộ 40 câu. Các kết quả A0/A1/A2 và TEST cũ thuộc baseline đã lưu, không chuyển thành metric của hệ Gemini này.

Mini-KG nhỏ có thể bỏ sót quan hệ; không tìm thấy cạnh không có nghĩa quan hệ không tồn tại. Nguồn có thể trùng ý hoặc lỗi thời. Citation hợp lệ chỉ xác nhận truy được nguồn, không tự xác nhận mọi diễn giải là đúng. Demo không thu bệnh án, không chẩn đoán, kê đơn hay thay tư vấn chuyên môn.

6.7. Notebook và truy vết đầu ra

Notebook 04_Multi_Agent.ipynb chứa toàn bộ code và sáu mục output: KQ1 đếm dữ liệu/tra KG; KQ2 đọc journal và các stage; KQ3 bảng xếp hạng và nguồn; KQ4 hai câu trả lời cùng Verifier; KQ5 tổng hợp thời gian/token/request; KQ6 biểu đồ thời gian. Ký hiệu [NB6–KQn] trong chương chỉ trực tiếp đến các mục này. Mặc định RUN_API, RUN_EVALUATION, RUN_TRAINING và RUN_TEST đều False; Run All không gửi câu hỏi mới lên Gemini.

Nguồn corpus: https://github.com/abachaa/MedQuAD. Snapshot minh họa DPP/NIDDK: https://github.com/abachaa/MedQuAD/blob/577bd37b96c02d1833b2c9eed2de9f96964e96cb/5_NIDDK_QA/0000022.xml. Snapshot SeniorHealth: cùng commit, 7_SeniorHealth_QA/0000015.xml. ID đầy đủ, URL gốc và câu trích nằm trong output KQ3; journal gốc tại artifacts/final_ch06/live_job_r11.json. MedQuAD giữ attribution/điều khoản nguồn trong dataset card.

6.8. Triển khai ngắn

Tab Multi-Agent của demo tổng hợp sử dụng implementation bốn agent đã đóng gói trong tieuluanfinal, tách với các chương khoa học cũ. Người dùng nhập câu hỏi, bấm Trả lời, xem hai đáp án; tab Luồng xử lý hiển thị input/output thật; tab Đồ thị tri thức cho xem cạnh, chiều và nguồn. KG chạy bằng SVG local, không cần Neo4j.

Từ Git Bash tại thư mục assign, chạy: bash tieuluanfinal/scripts/run_web.sh, rồi mở http://127.0.0.1:8040/agents. Key chỉ được nạp ở backend; dùng chung môi trường và sổ quota local đang có, không chép key vào notebook hoặc frontend. Hệ kiểm hạn mức trước khi tạo lượt, giữ journal khi lỗi/quota và không gọi model qua health check. Bản bàn giao đã kiểm local; chưa commit, push hoặc deploy cloud.
