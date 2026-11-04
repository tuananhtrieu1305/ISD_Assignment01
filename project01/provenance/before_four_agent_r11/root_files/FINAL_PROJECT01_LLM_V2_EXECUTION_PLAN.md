# Kế hoạch hiện hành — project01 RAG + LLM và tiểu luận final

**Override r10 theo yêu cầu người dùng 03/11/2026:** Verifier gọi Gemini một lần để kiểm ngữ nghĩa/số và có thể sửa bản nháp ngay trong call đó, sau đó code kiểm cứng citation/score. Một cặp hợp lệ dùng4generation: direct+Coordinator+Reporter+Verifier; reranker/Risk local, không có repair call riêng. Chế độ demo mặc định gửi hồ sơ TRAIN đủ21field; combined thiếu hồ sơ bị chặn trước API. Budget/UI/backend dùng4slot. Các đoạn r7 về đúng3call và Verifier chỉ-code bên dưới là lịch sử, bị override này thay thế. Đọc `project01/docs/llm_v2/SEMANTIC_VERIFIER_R10.md`; chưa gọi API thật cho r10. Evaluation40cặp dự trù160generation, chưa mở held-out.

Phiên bản 2.5 — 03/11/2026, Asia/Bangkok. Ưu tiên làm gấp, đúng **3 phase**. **Copy đủ phần cần dùng từ project nhóm vào project01, port tối đa code RAG/KG đã có và bàn giao không phụ thuộc `RAG_KG_Tham_khao/`; xóa thư mục tham khảo sau nghiệm thu cuối.** Google AI Studio / Gemini API **free tier**, ngân sách trả phí **0 USD**.

**Override r7 theo yêu cầu mới nhất:** khôi phục cách rerank local của project tham khảo, không dùng GeminiReranker. Bản phục vụ nhẹ dùng `LocalEvidenceReranker` cùng interface `BaseReranker`, kết hợp hybrid RRF/lexical/KG và không tải BGE lớn. Verifier là cổng integrity bằng Python, không gọi LLM và không được nhận là thẩm định ngữ nghĩa/lâm sàng. Một cặp so sánh dùng đúng **3 generation call**:1 direct +1 Coordinator/pre-retrieval +1 Reporter; không có repair loop. Embedding query dùng quota embedding riêng và phải hiển thị tách biệt. UI không cho bắt đầu lượt mới khi còn dưới3 generation slot.

- Checkpoint hiện hành: `docs/final_project01/llm_v2/checkpoint.json`.
- Kế hoạch trước `FINAL_PROJECT01_EXECUTION_PLAN.md` là lịch sử: Phase 1–2 hoàn tất, Phase 3 chưa thực hiện; phần final chưa làm được chuyển đầy đủ vào Phase 3 của kế hoạch này.
- Đây là kế hoạch được người dùng yêu cầu lập sau khi đồng ý nâng cấp bằng API LLM. Lượt lập kế hoạch **không bắt đầu Phase 1**, không gọi API có phí, không tải corpus mới hoặc thay pipeline đang chạy.
- Đọc thêm `docs/final_project01/llm_v2/reference_rag_kg_review.md` và `reference_rag_kg_snapshot.json` trước Phase 1. Bản 2.2 yêu cầu **port module/hàm thực tế của nhóm**; bản 2.3 yêu cầu copy đầy đủ source/tài nguyên cần dùng vào project01, rồi xóa thư mục tham khảo sau gate mục 4.6. Giữ nguồn nguyên trạng trước khi chuyển đủ và nghiệm thu, không xóa trong lượt chỉ sửa plan.

## 1. Lệnh điều phối

| Lệnh người dùng | Thực hiện |
|---|---|
| `làm phase 1`, `làm FINAL phase 1`, `làm LLM phase 1` | Phase 1 của **kế hoạch v2 này** |
| `làm phase 2`, `làm FINAL phase 2`, `làm LLM phase 2` | Phase 2 v2 sau khi Phase 1 COMPLETE |
| `làm phase 3`, `làm FINAL phase 3`, `làm LLM phase 3` | Phase 3 v2 sau khi Phase 2 COMPLETE |
| `làm tiếp task đang dở` | Đọc checkpoint v2, tiếp tục active phase; không tự mở phase tiếp |
| `kiểm tra phase đã xong chưa` | Audit sản phẩm/bằng chứng; không tự chạy lại benchmark, train hoặc TEST |
| Tiền tố `REORG`, `AG02`, `V3` | Kế hoạch lịch sử tương ứng; không tự gọi bằng lệnh không tiền tố |

Đọc toàn bộ kế hoạch và checkpoint v2 trước mỗi phase. Ghi rõ current_step, việc xong/còn thiếu, process thật và output. Chỉ COMPLETE khi đủ nghiệm thu; không thêm phase chỉ để chia nhỏ công việc nội bộ.

## 2. Mục tiêu cuối và phạm vi giữ lại

1. **Project01:** trả lời tiếng Việt rõ ràng, đúng trọng tâm; dùng LLM suy luận/tổng hợp từ bằng chứng đã truy hồi, có nguồn và biết nêu giới hạn.
2. **Demo chính:** đặt cạnh nhau **LLM trực tiếp** và **hệ đa agent + RAG + cùng LLM**. Không còn dùng bỏ bớt agent P0/P1/P2 làm phép so sánh chính.
3. **Tiểu luận final:** một DOCX sáu chương từ tiểu luận3, giải thích Ch5 → Ch6 và case study project01 mới; web tổng hợp có tích hợp pipeline thật.

Giữ pipeline năm vai trò Coordinator / Risk / Knowledge / Reporter / Verifier; tái sử dụng React, Flask, CDC checkpoint và runtime hiện có. Không train MLP/CNN/RNN/LSTM mới, không fine-tune LLM, không mở lại TEST cũ. Không thêm framework agent, vector database server hay microservice để giải quyết việc có thể làm bằng code hiện tại.

**Nguồn RAG chính là project nhóm**, không phải viết một implementation mới tương đương từ đầu. Giữ class/interface, luồng gọi và các hàm có thể giữ; thay các phần phụ thuộc luật lao động, OpenAI/Groq và hạ tầng không cần thiết. React/Flask và năm agent project01 là vỏ tích hợp; core RAG của nhóm chạy bên trong Knowledge/Reporter. FastAPI/frontend nhóm không cần trở thành service thứ ba, nhưng tận dụng schema, cách đóng gói response/source và test hữu ích. Code port vào notebook, không chỉ import thư mục tham khảo.

**project01 phải tự chứa source và artifact cần để build/chạy demo.** Không import, đọc file, symlink/junction hoặc thêm PYTHONPATH trỏ sang thư mục tham khảo. Sau khi chuyển, thư mục tham khảo chỉ là nguồn lịch sử cho tới lúc cleanup; tên đường dẫn có thể còn trong attribution/hash provenance nhưng không là dependency. Không nhân bản venv/node_modules hoặc dữ liệu luật không dùng; dependency Python/Node được khai báo và cài theo lock, runtime WSL hiện có vẫn được tận dụng.

Lý thuyết vẫn ngắn gọn, đủ ý, dễ hiểu, ít công thức. Giải thích hợp các hàm theo input → xử lý → output. Project01 giữ **3 notebook**, mỗi cây notebooks tối đa 4, source thuật toán đầy đủ trong cell; backend export một chiều từ notebook. File `.py` hỗ trợ vận hành không được trở thành implementation thuật toán duy nhất.

## 3. Điểm xuất phát và những điều cần sửa thật

- Bản offline hoàn tất: CDC 253.680 dòng/21 field, checkpoint scratch seed42/6 Dense; MedQuAD subset 247 document/762 chunk, graph 62 lexical anchor; BM25 + LSA + graph.
- Bản hiện tại chưa gọi LLM. Hàm chọn trích đoạn dựa vào từ khóa có thể lấy một câu cùng chủ đề nhưng không trả lời đúng câu hỏi. Glossary làm mất quan hệ/cấu trúc tiếng Việt; chunk có thể đứt ngữ cảnh, compact snapshot thiếu URL gốc từng bài.
- Ví dụ lỗi development đã quan sát: hỏi “Bệnh thận có làm tăng nguy cơ tiểu đường không?” nhưng trả câu nhắc kiểm tra bệnh thận hằng năm. Phải giữ đúng chiều quan hệ A → B, không lấy B → A làm bằng chứng thay thế.
- UI `answer_first_v2` đã đặt câu trả lời trước, nguồn/công cụ và trace dưới; có ba tab. Giữ nguyên nguyên tắc ưu tiên câu trả lời này.
- P0/P1/P2 và 120 đầu ra cũ là lịch sử. 82,5% task success không là chất lượng RAG+LLM mới, càng không là accuracy chẩn đoán. Không dùng bộ evaluation đã xem làm held-out mới.
- Verifier cũ chủ yếu kiểm integrity/số/từ khóa, chưa đủ để kiểm một câu trả lời LLM có diễn đạt lại. Cần kiểm mức hỗ trợ từng phát biểu bằng evidence.
- Source nhóm đã khảo sát: có pre-retrieval, hybrid search/RRF, reranking, Gemini generation, source formatting và KG extraction/cache/aggregate/visualization. Pre-retrieval còn tạo `ChatOpenAI` trực tiếp; KG notebook có cả OpenAI/Groq và chưa nối vào web. Vì vậy phải sửa các điểm đó, không chỉ thay key trong `.env` rồi gọi là đã chuyển hoàn toàn sang Gemini.

## 4. Các quyết định triển khai

### 4.1. API, chi phí và môi trường

- **Provider đã chốt: Gemini Developer API, key từ Google AI Studio; chỉ dùng Free Tier.** Không triển khai adapter OpenAI trong đợt này. Tổng chi phí trả phí được phép là **0 USD** cho cả embedding, development, demo và evaluation; không bật billing, mua credit, tự nâng tier hoặc chuyển sang model/tính năng trả phí.
- Phase 1 chỉ còn chốt model ID và hạn mức request/token thực tế của project, không hỏi lại provider/ngân sách đã được người dùng xác nhận. Model ưu tiên khảo sát `gemini-3.8-flash`, embedding text ưu tiên `gemini-embedding-001`: tài liệu giá công khai ngày 01/11/2026 có free tier, nhưng **chưa probe quyền truy cập/quota/key của tài khoản**. Chỉ chọn chính thức sau kiểm tra; cả hai nhánh dùng cùng model sinh câu trả lời. Nếu model không truy cập được thì chỉ chọn model khác còn free trong project và chốt trước evaluation, không chuyển trả phí.
- Key người dùng đã cung cấp qua chat **không được chép vào plan/checkpoint hoặc file tracked**. Backend đọc `GEMINI_API_KEY` từ môi trường hoặc `.env` local đã xác nhận Git ignore; Render dùng Environment Variables. Không đưa vào `VITE_*`, frontend, notebook output, log hoặc Git; không yêu cầu gửi lại key trong chat. Key đã xuất hiện trong chat nên khuyến nghị thay bằng key mới và đặt trực tiếp vào env; chưa kiểm thử, không tự thu hồi hoặc sử dụng để gọi API trong lượt chỉ cập nhật plan.
- Giữ hai runtime khoa học WSL Ubuntu/user tuananh hiện có. **Ưu tiên tái sử dụng lớp LangChain/Gemini và cấu trúc module của nhóm**, không viết lại HTTP client chỉ để né dependency nếu làm tăng công việc. Phase 1 audit package có sẵn; thiếu dependency phục vụ RAG thì dùng một env phục vụ riêng nhỏ/có khóa, tái dùng Python WSL hiện có, không nâng/cài trộn vào hai env GPU. Chỉ cài các package thật sự được core port dùng, không cài nguyên requirements không pin của nhóm, Torch/CUDA hoặc OpenAI/Groq/Cohere chỉ để thỏa import không dùng.
- Không cần huấn luyện GPU. Embedding là tạo index suy luận một lần, phải tính chi phí, lưu model/version/hash và cache. Chọn embedding tương thích truy vấn/corpus; không gọi LSA cũ thành neural embedding.
- Chỉ số `/health` phản ánh tiến trình; trạng thái dữ liệu/provider/key hiển thị riêng. Không gọi LLM ở mỗi health check. Không có key/quota thì báo unavailable rõ, không âm thầm thay bằng trích đoạn cũ rồi gắn nhãn LLM.

### 4.1.1. Chính sách free tier bắt buộc

- Free tier có giới hạn RPM/TPM/RPD theo **project và model**, không phải mỗi key. Không đổi key để né quota; không mặc định mức quota từ bài hướng dẫn hoặc cho rằng key nào cũng được truy cập model ghi “free” trên bảng giá. Xác nhận tier/quota trong AI Studio khi Phase 1, kiểm lại trước gọi thật; cấu hình project trả phí không được coi là free chỉ vì cùng model có dòng giá miễn phí.
- Chỉ dùng standard text generation/embedding đã xác nhận miễn phí. Tắt web search/grounding ngoài để giữ phép so sánh công bằng; không dùng Batch API/explicit context caching/dịch vụ khác nếu chưa xác nhận có free tier. “Gửi nhiều candidate trong một request rerank” là đóng gói prompt thường, không có nghĩa gọi Batch API.
- Một hàng đợi API tuần tự dùng chung cho mọi agent và cả hai nhánh, giới hạn token/call, backoff theo Retry-After với số lần thử hữu hạn. Khi hết quota ngày hoặc không đủ free-tier entitlement: lưu checkpoint, dừng gọi API và báo rõ; không tự chuyển trả phí hoặc lặp retry vô hạn. Nếu chỉ gặp giới hạn theo phút thì lên lịch lại có giới hạn, không khóa lượt làm việc bằng sleep dài.
- **80 output đánh giá không có nghĩa chỉ 80 API request.** Agentic RAG còn gọi lập truy vấn/rerank/sinh/kiểm chứng; embeddings và development cũng dùng quota. Phase 1 phải dự tính tổng request/token và chia phiên/ngày nếu cần. Khi chờ quota, giữ nguyên model/prompt/corpus đã khóa, chỉ tiếp tục claim chưa dùng; không chạy lại output đã hoàn thành hoặc âm thầm giảm số câu để nhanh đủ điểm.
- Cache embedding theo hash corpus/model và lưu output đúng lineage; cache local không bị gọi là trả lời live mới. Đo latency và token riêng, bao gồm retry/thời gian chờ; không dùng giá paid tier để nói có phí thực thu. Giá free-tier được ghi 0 theo cấu hình/tài liệu đã kiểm, còn hóa đơn thực tế không được tự khẳng định đã xác minh nếu chưa xem.
- Chỉ gửi văn bản corpus công khai và dữ liệu demo không định danh. Google công bố nội dung free tier có thể được dùng để cải thiện sản phẩm; không đưa hồ sơ sức khỏe thật hoặc thông tin cá nhân vào demo API.
- Các cập nhật plan 2.1/2.2 không đổi số phase, không bắt đầu Phase 1 và chưa thực hiện API probe. Nguồn đối chiếu: [Pricing](https://ai.google.dev/gemini-api/docs/pricing), [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), [API key security](https://ai.google.dev/gemini-api/docs/api-key).

### 4.2. Kiến trúc đích

```text
Câu hỏi + hồ sơ tùy chọn
  → Coordinator: phạm vi, intent, câu hỏi gốc, chiều quan hệ, kế hoạch
  → Pre-retrieval: chuẩn hóa/dịch truy vấn, tối đa 3 truy vấn khi thực sự cần
  → Knowledge: core RAG nhóm đã port, BM25 + semantic embedding + mini-KG có nguồn → RRF gộp ứng viên
  → Reranker: liên quan tới câu hỏi và có thông tin giúp trả lời? → top evidence
  → Risk: chỉ khi cần, kiểm đủ 21 field → checkpoint CDC giữ nguyên
  → Reporter (LLM): bản nháp tiếng Việt, phát biểu + citation
  → Verifier: nguồn/claim support/contradiction/score/đúng trọng tâm
  → Nếu cần: tối đa 1 vòng tìm thêm/sửa rồi kiểm lại
  → Phát hành đúng bản đã kiểm; không viết lại tự do sau kiểm chứng
```

- Coordinator có thể dùng LLM output có cấu trúc để phân tích intent/query; quyết định được giới hạn bởi code/allowlist. Không để tài liệu truy hồi ra lệnh đổi công cụ hoặc bỏ quy tắc.
- Bắt đầu retrieval với khoảng 20 candidate, chọn khoảng 5–8 evidence sau rerank. Đây là giá trị development, phải chốt trước evaluation, không lời hứa cấu hình tối ưu.
- Giữ interface và cách tạo RankedResult/original_rank của reranker nhóm. Bản phục vụ mặc định dùng Gemini rerank candidate theo lô prompt trong free tier; không thêm key Cohere. Class BGE và embedding BGE của nhóm có thể giữ làm tùy chọn local nếu đã có model/runtime và probe đủ tài nguyên, không tải/cài model lớn chỉ để tái sử dụng cho đủ. Cấu hình nào dùng phải được ghi rõ; không âm thầm đổi reranker sau evaluation freeze.
- Graph là **mini-KG có assertion được kiểm theo nguồn**, cộng lớp document/chunk/mention; lexical anchor cũ chỉ hỗ trợ alias/candidate. Có đường về source chunk và câu trích, không tự tuyên bố là ontology y khoa đầy đủ hoặc suy luận nhân quả. Kế hoạch tối giản cụ thể ở mục 4.5.
- Reporter trả lời trực tiếp trước, giải thích ngắn phía sau, gắn citation theo phát biểu; trả tiếng Việt dù nguồn tiếng Anh. Chỉ các phát biểu từ evidence được gắn nhãn có căn cứ. Không thêm kiến thức nội tại rồi gắn citation không hỗ trợ.
- Verifier kết hợp kiểm code và kiểm ngữ nghĩa có giới hạn bằng LLM. Cùng LLM tự kiểm không phải đánh giá độc lập/chuyên gia; structured JSON đúng schema không đảm bảo nội dung đúng.
- Giữ score CDC bằng dữ liệu server, không cho LLM thay số hoặc suy thành xác suất mắc bệnh cá nhân. Thiếu field không tự điền. Không gửi hồ sơ thật/định danh lên API trong demo; dùng mẫu TRAIN hoặc synthetic đã ghi rõ.
- Chốt deadline mới từ probe API, không giữ cứng 30s offline nếu không phù hợp. Có timeout từng call, trần tổng thời gian/token/call, retry hữu hạn và tối đa một vòng feedback. Timeout local không được mô tả thành bảo đảm hủy xử lý/chi phí ở provider.

### 4.3. So sánh công bằng

Hai nhánh có tên rõ: `llm_direct` và `agentic_rag`. Dùng cùng model/version sinh câu trả lời, cùng câu hỏi, ngôn ngữ, giới hạn độ dài đầu ra và yêu cầu trả lời hữu ích/an toàn. Cấu hình lấy mẫu tương đương trong giới hạn API. Baseline được prompt tốt và dùng kiến thức có sẵn, không bị bắt buộc “chỉ trả lời từ evidence” khi không được cấp evidence.

- `llm_direct`: không corpus project, không retrieval, không web search/grounding bên ngoài. Không ép bịa citation.
- `agentic_rag`: thêm các bước đã nêu và tài liệu có nguồn. Số call/token thường cao hơn; báo đầy đủ overhead, không so chi phí một call baseline với riêng call cuối pipeline.
- Đánh giá chung trên cùng câu hỏi bằng tài liệu tham chiếu độc lập: đúng trọng tâm, tính đúng, đủ ý, biết giới hạn. Groundedness/citation coverage là metric riêng; baseline không có citation nội bộ không tự động bị chấm sai toàn bộ câu trả lời.
- Phép so sánh chính là **hỏi đáp kiến thức**. Hồ sơ+CDC là demo chức năng bổ sung, không bắt LLM trực tiếp đoán lại checkpoint rồi chấm theo điểm của MLP. Nếu cần so nhánh combined thì cho hai bên cùng output model cố định và đổi tên baseline cho đúng; không nhập nhằng với LLM thuần.
- Không tuyên bố RAG thắng trước khi đo; LLM trực tiếp có thể tốt hơn ở một số câu và nhanh/rẻ hơn.

### 4.4. Bản đồ port bắt buộc — tận dụng tối đa project nhóm

Nguồn dưới đây tương đối với `RAG_KG_Tham_khao/PTHTTM-RAG/`. **Phase 1 copy đủ file/module/helper cần thiết sang `project01/provenance/group_rag_kg_source/` và ghi hash/bản đồ original → bản local → cell notebook → export**; Phase 2 port từ bản local này, không dựa vào thư mục tham khảo nữa. Phần nào không lấy phải nêu lý do ngắn (domain/hạ tầng/quota/lỗi), không thay toàn bộ bằng code tự viết mà vẫn gọi là tái sử dụng.

| Nguồn nhóm | Giữ lại trực tiếp | Phần sửa tối thiểu |
|---|---|---|
| `chatbot/app/retrieval/pre_retrieval.py` | QueryStrategy, rewrite/decomposition/expansion, unique/parse và flow process | Bỏ tạo ChatOpenAI cứng; dùng Gemini client chung, sửa tham số llm bị bỏ qua, prompt y khoa/Anh–Việt, cap 3 query bằng code |
| `chatbot/app/retrieval/hybrid_searcher.py` | HybridSearcher, `_fuse`, RRF/rank metadata | Thêm list KG candidate theo cùng chunk ID; VectorDBClient adapter local; tất cả call Gemini đi qua queue chung |
| `chatbot/app/retrieval/retriever.py` | `_prepare_queries`, gom nhiều query, dedup/top-k | Bảo toàn câu hỏi gốc; kiểm giới hạn số query; kiểm lại max-score merge trên dev, chỉ sửa nếu có lý do |
| `chatbot/app/database/bm25_store.py` | Build/search/tokenize và corpus serialization | Dùng chunk y khoa/version mới; không nạp index luật; kiểm metadata và hash khi reload |
| `chatbot/app/indexing/chunking.py`, `indexer.py` | Section-first/overlap, index flow, metadata-in-context | Thay chương/mục/điều bằng title/section/URL; ID/index dựa version nội dung để không skip tài liệu đã đổi |
| `chatbot/app/indexing/embedding.py`, `database/vector_db.py` | Interface embed_text/embed_batch và VectorDBClient | Thêm Gemini embedding cùng shape; thay Qdrant mặc định bằng NumPy/local index cho corpus nhỏ; không tạo một hệ retrieval khác |
| `chatbot/app/retrieval/reranker.py` | BaseReranker, ranked result, original_rank/top_n | Thêm GeminiReranker theo interface; BGE local tùy chọn như trên, Cohere không là dependency bắt buộc |
| `chatbot/app/generation/generator.py`, `prompt.py` | GeminiGenerator, build_context/messages, đánh số nguồn, extract text | Dùng chung Gemini adapter/quota, prompt tiểu đường, structured claims/citations/usage, source URL/quote |
| `chatbot/app/pipeline.py`, `api/schemas.py` | Trình tự retrieve → rerank → generate, response/source mapping, kiểu dữ liệu | Tách retrieve/rerank cho Knowledge và generate cho Reporter để không gọi LLM hai lần; thêm Verifier/Risk/trace, metadata y khoa |
| `chatbot/Extract_Graph.ipynb` | Normalize/cache/resume, build_graph_payload, export/visualization | Chỉ một extractor Gemini; bỏ phụ thuộc Neo4j ở đường demo mặc định, schema nhỏ và evidence span; xem mục 4.5 |
| Tests/logging/frontend nhóm | Case/tổ chức quan sát candidate trước/sau, nguồn và trạng thái | Chuyển case sang diabetes, tránh log profile/key; giữ React project01, không port lại toàn frontend |

**Mọi chỗ gọi OpenAI/Groq trong code port đều chuyển sang Gemini**: pre-retrieval, generation, KG extraction, graph QA nếu còn dùng. Không dùng OpenAI-compatible endpoint Groq như một cách thay tên nhưng vẫn cần key khác. Bỏ import/provider setting bắt buộc không còn dùng. Không chỉ đổi biến `OPENAI_API_KEY` thành tên khác rồi gửi key Gemini tới endpoint OpenAI. Không sửa các file tham khảo/bản archive để “dọn” lịch sử.

Qdrant/Neo4j adapter hiện có được giữ làm tham khảo/tùy chọn, không bắt buộc service mới. Không kết nối/sửa collection luật của nhóm, không copy credentials hoặc `.env`. Thư viện thực sự cần có version khóa; global settings/singleton không được khởi tạo provider ngoài ý muốn hoặc yêu cầu SECRET_KEY/auth của app nhóm khi chỉ dùng core.

### 4.5. KG nhanh nhất đủ tốt cho demo — mini-KG được kiểm nguồn

**Chọn một đồ thị nhỏ, có tác dụng thật; không trích toàn bộ corpus bằng LLM và không dựng lại hạ tầng Neo4j.** Dữ liệu chính là văn bản MedQuAD/corpus đã phục hồi ngữ cảnh; CDC chỉ phục vụ checkpoint. Không dựng graph từng người khảo sát hoặc suy quan hệ nhân quả từ feature CDC.

1. **Tái sử dụng schema/cache/aggregate của notebook nhóm.** Giữ `documents/entities/relationships`, đổi `articles` thành chunks đủ ngữ cảnh; thêm canonical ID/type/alias và source metadata. Giữ directed graph; chỉ 5–8 loại quan hệ theo tài liệu, không để LLM tự phát minh taxonomy lớn.
2. **Lớp provenance tự động:** Document → CONTAINS → Chunk → MENTIONS → Concept trên corpus, dùng lại anchor/alias khi đúng. Quan hệ MENTIONS không được mô tả thành quan hệ y khoa.
3. **Lớp assertion rất nhỏ:** bắt đầu khoảng **20–40 đoạn nguồn rõ**, mục tiêu tham khảo **20–50 concept và 25–60 assertion có căn cứ**, không phải số lượng bắt buộc phải lấp đầy. Chủ đề phục vụ demo: khái niệm/subtype, vận động, yếu tố nguy cơ, biến chứng/thận và kiểm tra sức khỏe. Chọn theo corpus/development, không theo lỗi held-out.
4. **Cách tạo nhanh:** đọc/chọn quan hệ và câu nguồn rõ để tạo seed JSON có review ngay ở Phase 1. Đây là curation, không giả nhận LLM đã extract. Phase 2 port extractor Gemini từ notebook nhóm để xác nhận/bổ sung có giới hạn trên chính tập nhỏ; cache theo hash chunk/model/prompt/schema. Nếu seed đã đủ coverage và source-checked thì không gọi LLM trên mọi chunk chỉ để tăng số cạnh. Không thêm phase hoặc biến toàn bộ KG thành một dự án nghiên cứu riêng.
5. Mỗi assertion phải lưu subject/relation/object, chunk/document ID, câu trích/offset, direction, polarity/điều kiện/subtype nếu có và review status. Kiểm quote thật sự nằm trong source; review ý nghĩa/chiều quan hệ, không chỉ kiểm có tên hai thực thể. Bắt buộc kiểm tất cả cạnh đưa vào demo và assertion dùng trả lời; cạnh chưa được kiểm không tham gia câu trả lời. `count` không là confidence. Không có cạnh không chứng minh quan hệ không tồn tại.
6. **Lưu/chạy nhẹ:** JSON + adjacency map; dùng lại logic export/visualize của nhóm, bỏ lớp Neo4j I/O ở mặc định. Tận dụng PyVis để xuất HTML minh họa nếu runtime đã có hoặc có thể cài trong env phục vụ nhỏ; không cần phát triển thư viện vẽ graph mới. UI hiển thị neighborhood/đường nguồn của câu hỏi và mở source chunk được, không chỉ ảnh graph toàn cục.
7. **Nối thật vào RAG:** lấy entity từ query plan/alias → duyệt có hướng 1 hop mặc định, tối đa 2 hop → lấy chunk nguồn của các cạnh phù hợp → thêm vào `_fuse` của HybridSearcher → rerank với câu hỏi gốc → đưa cả text evidence/đường graph vào context. Một đường A → B → C không được tự suy thành A gây C.
8. **Đủ demo khi:** có ví dụ thực thể/quan hệ truy được về quote/URL hoặc locator nguồn đúng scope; trace cho thấy graph retriever chạy và candidate từ graph vào rerank; có câu hỏi đảo chiều được xử lý đúng/thiếu bằng chứng được nêu rõ; câu trả lời tiếng Việt có citation hợp lệ. Không bắt buộc graph làm đổi top-k trong mọi câu hoặc phải thắng baseline. Không dùng Cypher do LLM sinh tự do hoặc `allow_dangerous_requests=True` trong app.

Mini-KG là artifact offline chuẩn bị một lần; chat chỉ tra cứu, không gọi extraction lại. Corpus/index đầy đủ vẫn hỗ trợ những câu ngoài graph, với coverage graph được ghi rõ. Tối ưu free tier: không thêm call LLM riêng chỉ để vẽ graph; kết hợp entity parsing vào pre-retrieval có sẵn. Không huấn luyện model mới.

### 4.6. Chuyển đủ sang project01 rồi xóa thư mục tham khảo

Đây là yêu cầu bàn giao đã được người dùng chốt, không phải tùy chọn. Vẫn chỉ 3 phase, không phát sinh phase migration riêng.

**Phase 1 — copy chọn lọc nhưng đủ dependency:**

- Copy các module ở bảng 4.4 và toàn bộ helper/import nội bộ cần cho chúng (schemas, config/logging, `__init__`, template/prompt, test/fixture hữu ích); ưu tiên giữ nguyên cây thư mục tương đối của phần `chatbot/app/` nhỏ để không bỏ sót import. Copy phần code KG cần từ notebook, README/attribution/license nếu có và các asset visualization thực sự dùng. Kiểm cả tài nguyên được đọc bằng path, không chỉ Python import.
- Bản gốc chọn lọc đặt tại `project01/provenance/group_rag_kg_source/`; bảng chuyển tại `project01/provenance/group_rag_kg_source/transfer_manifest.json`, có original path/hash, copied path/hash và quyết định port/không dùng. Snapshot/hash chỉ là provenance, không được buộc source gốc tồn tại mãi khi audit.
- Không copy `.git`, venv, node_modules, `.env`/key, cache model lớn, index/graph luật hoặc raw luật không được sử dụng. Nếu cần giữ một test/asset thì copy phần phụ thuộc của nó hoặc chuyển thành fixture y khoa. Nếu bản source/notebook có secret hoặc output chứa secret, lưu bản đã loại secret cùng ghi chú/hash gốc, không đưa secret sang provenance.
- Từ sau bước này, đọc/port từ bản đã copy trong project01. Notebook hoạt động vẫn chỉ 3 file hiện có; notebook/code tham khảo giữ ngoài cây `notebooks/`, không trở thành đường chạy bí mật của thuật toán.

**Phase 2 — đóng gói độc lập:**

- Code hoạt động nằm trong cell notebook và export backend ở project01, tên module riêng; không import từ `provenance/` để né yêu cầu notebook đầy đủ code. Config/prompt/test/static asset dùng thật đều ở project01.
- Corpus/chunk/vector/BM25/mini-KG/model CDC và dữ liệu demo cần cho serving phải có trong package của project01 hoặc có quy trình tái tạo đã khai báo từ nguồn hợp lệ. Đường chạy demo không đọc file từ thư mục tham khảo, index luật hoặc collection nhóm.
- Chuẩn bị README/requirements/lock/env mẫu/package manifest; build được từ dependency đã khai báo. Runtime WSL/Python/Node có thể dùng chung đã cài, nhưng không cần môi trường hay cache nằm trong folder tham khảo. Gói Render và tab Ch6 phải dùng đúng implementation/package local của project01.
- Kiểm clean-start tại một workspace/copy chỉ gồm source/package project01 và dependency khai báo, không cung cấp `RAG_KG_Tham_khao/`. Kiểm notebook ở mode demo/development, backend/API, React build/UI, graph lookup và citation, source/export parity. Không train hoặc chạy lại held-out đã tiêu thụ; có thể đọc saved results và chạy ví dụ smoke đã khai báo. Ghi proof rằng reference folder không có trong môi trường kiểm.

**Phase 3 — gate cleanup rồi xóa đúng folder:**

1. Đối chiếu transfer manifest, các bản gốc cần giữ, attribution và package. Mỗi file cần được port/retained; file không dùng ghi rõ lý do. Bản snapshot cũ tham chiếu original path được resolve về bản project01 nếu giữ, hoặc đánh dấu historical metadata/omitted non-runtime nếu không giữ. Không báo một file omitted là đã bảo toàn byte, không sửa receipt lịch sử.
2. Quét active imports/PYTHONPATH/path/config/build/deploy/notebook để không còn dependency tới folder tham khảo. Tên folder trong lịch sử/citation được phép, không nhầm với dependency hoạt động. Xác nhận demo project01 và tab tích hợp Ch6 chạy khi folder tham khảo không khả dụng.
3. Sau khi các điều kiện trên PASS, **xóa `C:\DATA\assign\RAG_KG_Tham_khao` theo yêu cầu cleanup của người dùng**, không xóa trước. Trước thao tác recursive delete phải resolve/check absolute target chính xác nằm trong workspace và chỉ là folder này, kiểm symlink/junction; dùng một shell PowerShell end-to-end với `-LiteralPath`, không tác động `.git`, dataset, env hoặc folder bài khác. Nếu phát hiện file mới/thay đổi chưa kiểm kê, chuyển phần cần giữ và đối chiếu lại trước khi xóa, không bỏ dữ liệu chưa biết.
4. Smoke lại demo/API/build cần thiết sau xóa, không chạy benchmark lại; ghi `reference_deleted=true`, số file chuyển, proof/hash package và kết quả. Nếu còn dependency hoặc thiếu nguồn thì chưa xóa/chưa gọi cleanup COMPLETE, tiếp tục sửa trong phase đang được gọi. Không hỏi lại cho đúng cleanup đã nằm trong phạm vi được người dùng chốt; chỉ làm rõ khi có dữ liệu ngoài phạm vi thực sự không thể xác định.

Mục tiêu cuối: người dùng có thể bỏ folder tham khảo mà không làm hỏng code, notebook, demo hoặc quá trình build/deploy project01. Giữ attribution và code gốc cần đối chiếu ngay trong project01, không giữ nguyên cả repository tham khảo chỉ để thay tên.

## Phase 1 — Chốt cách port RAG nhóm, API, dữ liệu và mini-KG seed

**Mục tiêu:** đầu vào đủ tốt và cấu hình đủ rõ để làm pipeline ngay, không mất thời gian xây lại nền khoa học.

### Công việc

1. Đọc plan/checkpoint và báo cáo khảo sát nhóm; kiểm snapshot source nhóm cùng receipt/bản archive hiện có. **Copy đủ module/helper/tài nguyên cần dùng vào project01 theo mục 4.6**, ghi transfer manifest/hash read-back, rồi chốt bảng port theo mục 4.4 và làm việc từ bản local. Chỉ viết adapter/extension còn thiếu. Giữ source nhóm nguyên trạng cho tới cleanup gate và notebook/UI/model/index/metric/report cũ đúng hash. Audit package/runtime để chọn dependency tối thiểu có khóa, không cài lại môi trường GPU hoặc triển khai thêm service database.
2. Dùng provider/budget đã chốt: Google AI Studio / Gemini Developer API, Free Tier, trả phí 0 USD. Kiểm `GEMINI_API_KEY` có sẵn ở backend mà không in giá trị; nếu chưa có thì hướng dẫn đặt key trực tiếp vào env, không hỏi lại provider hoặc yêu cầu gửi key trong chat. Xác nhận tier/quota/model miễn phí thực tế rồi probe một request tối thiểu trong Phase 1 được gọi; ghi model/usage/latency/trạng thái không secret. Chốt model, hàng đợi tuần tự, timeout/backoff/quota và ước tính tổng request; chưa build toàn UI. Không có quyền free tier thì dừng API và làm tiếp phần dữ liệu độc lập, không nâng cấp billing.
3. Rà MedQuAD gốc và các nguồn chính thống liên quan cần bổ sung. Tập trung chủ đề đủ demo: khái niệm, yếu tố nguy cơ, vận động, ăn uống, biến chứng và quan hệ tiểu đường–thận. Phục hồi tài liệu đủ ngữ cảnh cùng title/URL gốc/source ID nếu có thể; chỉ thêm nguồn có quyền sử dụng phù hợp và attribution. Không đoán URL từ compact ID, không tải dữ liệu lớn không phục vụ câu hỏi.
4. Tạo corpus revision riêng: source snapshot/hash/ngày lấy, title/URL/section/document/chunk IDs, language, kích cỡ và ví dụ; chia theo đoạn/câu đủ nghĩa, có overlap vừa phải. Giữ corpus/index cũ nguyên trạng. Ghi bản nào có URL gốc, bản nào chỉ repository locator; không trộn âm thầm. Chốt corpus trước evaluation; không thêm tài liệu sau khi xem lỗi held-out rồi báo lại cùng score.
5. Chốt adapter Gemini cho mọi call OpenAI/Groq của module được port; embedding/store/rerank qua interface nhóm, token/quota budget. Dựng **seed mini-KG curated** theo mục 4.5 từ 20–40 đoạn rõ, lưu quote/nguồn/hướng/review; dùng curation nhẹ để có graph hữu ích nhanh, không extract toàn corpus. Chốt contract query/entity/evidence/claims/usage và cách graph candidate nhập RRF. Reranker không được coi chiều quan hệ ngược là câu trả lời đúng. Source thuật toán port/extraction tự động chính thức và web vẫn thuộc Phase 2.
6. Chốt bộ mới **20 development + 40 held-out câu hỏi kiến thức**, có paraphrase tiếng Việt, câu hỏi quan hệ/phủ định, nhiều ý, thiếu bằng chứng và ngoài phạm vi. Tách trùng/nghĩa tương đương và mẫu sự kiện giữa dev/held-out; dùng chung KB là hợp lệ, không bắt buộc tách KB thành hai kho khác nhau. Reference/gold lấy từ nội dung nguồn, không từ ranking của hệ; chấp nhận nhiều đoạn/tài liệu hợp lệ và ghi coverage qrels chưa đầy đủ.
7. Viết rubric, cách chấm ẩn danh hai câu trả lời, metric/chi phí và chính sách lỗi/retry. Mặc định **1 lần/câu/nhánh = 80 output**; chỉ thêm lặp độc lập nếu ngân sách cho phép và khai báo số lặp **trước** chạy. Không rerun chọn câu trả lời đẹp. Giữ ví dụ lỗi đã thấy làm development/regression, không gọi là held-out mới.

### Sản phẩm và nghiệm thu

- `project01/datasets/llm_v2/`: source catalog, corpus revision, dataset card, dev/held-out và reference/rubric có version.
- `project01/docs/llm_v2/architecture.md`, `evaluation_protocol.md`; config `.example` không secret và provider contract/preflight receipt.
- Bảng original source → bản copy project01 → thành phần giữ/sửa → notebook/export dự kiến, cùng transfer manifest/hash read-back và lý do những phần không cần port; đủ helper/asset để làm tiếp khi source tham khảo không sẵn. Seed graph JSON có provenance/quote/review và thống kê/coverage thực, không bắt đủ số cạnh bằng suy đoán. Chưa cần Neo4j/Qdrant hoặc một web mới; chưa xóa folder tham khảo.
- Có model ID/free tier/quota đã xác nhận, budget trả phí 0 USD; probe API thật tối thiểu PASS; corpus đủ ngữ cảnh/metadata được kiểm; protocol chốt trước chạy held-out. Thiếu env key hoặc chưa đủ quyền free tier thì ghi WAITING_CONFIGURATION/WAITING_QUOTA và phần độc lập đã xong, không báo API PASS giả, không hỏi lại budget.
- `docs/final_project01/llm_v2/phase1_report.md`, checkpoint Phase 1 COMPLETE, Phase 2 READY. Chưa đánh giá held-out, chưa làm DOCX; không tự bắt đầu Phase 2.

## Phase 2 — Port RAG nhóm sang Gemini, nối mini-KG/agent, web và đánh giá

**Mục tiêu:** câu trả lời thật sự tốt hơn về tính hữu ích/căn cứ nếu evidence cho phép, có phép so sánh minh bạch.

### Công việc theo ưu tiên

1. Giữ bản gốc 3 notebook trước khi thay; cập nhật chính 3 file hiện có, không thêm notebook con vượt giới hạn. **Port trực tiếp bản code nhóm đã copy vào project01 theo bảng 4.4/4.6**, giữ rõ nguồn/hàm gốc và diff/adapter cần thiết, không viết lại một RAG khác hoặc import từ folder tham khảo/provenance. Notebook 01 chứa chunking/index/query/BM25/vector/RRF/rerank và các hàm KG normalization/cache/aggregate/export/lookup đã port; notebook 02 chứa GeminiGenerator/PromptBuilder/pipeline đã port và năm agent/Verifier/API; notebook 03 chứa rubric/evaluator/summary/plots. Export backend có hash/version, namespace riêng tránh xung đột package `app`; đổi file frozen cần revision/resolver đúng archive. Không seed lại producer cũ.
2. Ưu tiên một luồng dọc chạy thật từ **core nhóm** trên vài tài liệu y khoa: retriever → reranker → GeminiGenerator, rồi đặt cạnh Gemini trực tiếp. Sửa dứt điểm ChatOpenAI tạo cứng và mọi extractor OpenAI/Groq; không cần key ngoài Gemini. Chỉ sau đó nối mini-KG, agents và hoàn thiện UI. Không làm đẹp UI trong khi core chưa trả lời đúng ý; không bỏ core nhóm để xây từ đầu.
3. Dùng strategy pre-retrieval đã port, bảo toàn câu gốc/chiều quan hệ/phủ định, cap 3 query; Gemini calls qua một queue, không để asyncio.gather của nhóm tạo fan-out vượt quota. Tạo semantic index/caches versioned qua interface nhóm, không refit index lịch sử. Port extractor/normalizer/cache/aggregate/visualize từ Extract_Graph; bắt đầu bằng seed đã kiểm, chỉ bổ sung phạm vi nhỏ khi thật sự thiếu coverage development. Nối graph retriever 1–2 hop vào RRF và dùng source chunk thật, không chỉ xuất graph HTML. Thử retrieval/rerank trên dev, xem candidate trước/sau, contribution graph và nguồn; không dùng held-out để chọn cạnh.
4. Reporter tạo câu trả lời trực tiếp, dễ hiểu, có claims/citations; Verifier kiểm đúng câu hỏi, hỗ trợ từng phát biểu, mâu thuẫn, URL/ID và điểm model. Khi không đủ nguồn, trả câu giới hạn hữu ích thay vì gắn citation cho suy đoán. Tối đa một feedback loop; cuối cùng phát hành đúng văn bản đã được kiểm. Không lưu hoặc hiển thị chain-of-thought.
5. Web giữ 3 tab, kết quả chính là **LLM trực tiếp / Hệ đa agent + RAG** đặt cạnh nhau. Nguồn, truy vấn viết lại, reranking, kiểm chứng/trace là phần mở rộng. Hiển thị model, trạng thái chạy, latency tổng, token và chi phí ước tính theo giá đã kiểm; phân biệt usage provider trả về với ước lượng. Streaming nếu có không gọi bản nháp chưa kiểm là câu trả lời đã duyệt. Phần hồ sơ/CDC giữ như demo bổ sung. P0/P1/P2 chỉ truy cập ở tài liệu/benchmark lịch sử, không là lựa chọn chính.
6. Kiểm tra tập trung: câu hỏi ảnh đã lỗi/chiều ngược, tiếng Việt, query không đổi ý, citation bịa/không hỗ trợ, không đủ bằng chứng, thiếu BMI, score không bị LLM đổi, prompt injection từ tài liệu, API timeout/quota/401, secret không vào frontend/log, deadline/budget và notebook-export parity. Kiểm API/UI thật desktop/mobile; mock chỉ cho lỗi cần tái hiện, ghi rõ; không dùng mock để nghiệm thu khả năng trả lời thật.
7. Chốt corpus/index/prompts/query/rerank/model/config/evaluator và rubric sau development. Chạy 40 held-out ×2 nhánh đúng số lặp đã khai báo, trong budget. Ghi raw request/response đã loại secret, source IDs, usage, thời gian toàn pipeline, cache/live, lỗi/retry và claim. Không thay raw output, không bỏ case lỗi, không dùng lại held-out để tuning. Nếu có incident thì giữ evidence và tạo revision công khai, không âm thầm chạy lại.
8. Chấm chung về đúng trọng tâm/tính đúng/đủ ý/biết giới hạn; RAG thêm citation support và retrieval relevance. Chấm ẩn nhánh, cân bằng thứ tự; người dùng có thể đọc/chấm một subset khi sẵn sàng, không giả nhận đã có chuyên gia. LLM judge chỉ hỗ trợ và ghi model/reviewer; không để Verifier tự chấm chính nó thành benchmark độc lập. Báo n, lỗi, mức bất định khi phù hợp; không chọn metric độ dài/HTTP200 làm chất lượng.
9. Xuất bảng và tối đa 3–4 hình có giải thích trục/đơn vị/mẫu số/thông điệp: chất lượng hai nhánh, mức hỗ trợ nguồn, latency/token/chi phí, nhóm lỗi khi hữu ích. Cập nhật README/hướng dẫn demo/report Markdown bằng revision giữ gốc. Chuẩn bị Render config/dependencies CPU/package version mới, key server-side, không deploy.

### Sản phẩm và nghiệm thu

- Hai nhánh thực sự gọi cùng model API; pipeline dùng evidence mới, có pre-retrieval/rerank/Verifier và câu trả lời tiếng Việt. Không có key/quota thì thông báo rõ, không thay bằng replay mà gọi live.
- Có source reuse map khớp code thực (hàm/class nhóm → cell/export), không còn đường gọi OpenAI/Groq/Cohere bắt buộc trong active pipeline; Gemini key chạy được cả pre-retrieval, generation và extractor được sử dụng. Mini-KG có source-backed assertions, graph candidate tham gia retrieval/rerank và ví dụ graph → chunk → citation; không chỉ ảnh minh họa.
- Ba notebook có full code và output development; mặc định chỉ đọc saved output, `RUN_API/RUN_EVALUATION=False`, `ALLOW_PAID_API=False`; khi chạy phase được yêu cầu chỉ bật call free-tier có kiểm soát. Backend/source/package parity PASS.
- Có kết quả held-out mới (mặc định 80 output), rubric/review/usage/chi phí đầy đủ; P0/P1/P2 cũ nguyên trạng, không tái dùng 82,5% làm kết quả mới.
- UI/API smoke/E2E PASS, source và bản trước được bảo toàn; `phase2_report.md`, checkpoint COMPLETE và Phase 3 READY. Chưa tự làm DOCX/Phase 3.
- Package/source/config/prompt/asset cần build/chạy nằm trong project01; clean-start không có thư mục tham khảo PASS theo mục 4.6. Chưa xóa source tham khảo trước nghiệm thu tích hợp cuối Phase 3.

## Phase 3 — Tích hợp tiểu luận final, demo tổng hợp và bàn giao

**Mục tiêu:** hoàn thành cả phần final còn dở trong kế hoạch trước bằng sản phẩm mới đã đánh giá.

### Công việc

1. Tạo final tại `tieuluan3/report/final/`, giữ DOCX/manuscript phát hành trước nguyên trạng. Sáu chương: lịch sử AI; ML; CNN; RNN–LSTM; KB/KG/RAG; đa agent và case study project01 RAG+LLM. Giữ lý thuyết cơ bản, ít công thức và giải thích hợp hàm/từng hàm bằng ví dụ.
2. Rà yêu cầu thầy từ evidence có sẵn: 2–3 dataset mỗi chương theo phạm vi đã có (link/kích cỡ/mẫu/phân bố/nhận xét), Scratch/Keras/PyTorch cho các chương thực nghiệm; CNN/RNN/LSTM trên 5 layer theo quy ước đếm công bố; bảng so sánh mô hình. Không tự train hoặc mở lại TEST để lấp thiếu số. Ghi thiếu thực sự nếu có, không tạo metric giả.
3. Ch5 giải thích pre-retrieval/hybrid search/mini-KG/rerank/grounded generation, ghi rõ source RAG/KG kế thừa project nhóm và phần chỉnh cho y khoa/Gemini. Ch6 giải thích năm vai trò, feedback và so sánh cùng LLM trực tiếp. Có một ảnh neighborhood/đường nguồn của mini-KG đã chạy thật, thống kê/coverage/curation chính xác, không nhận graph nhỏ là ontology đầy đủ. Kết quả cũ A0/A1/A2 và P0/P1/P2 chỉ giữ đúng phạm vi lịch sử/đối chiếu, không trộn với benchmark mới. Giải thích mọi biểu đồ và không tuyên bố RAG thắng khi số đo không ủng hộ.
4. Tích hợp pipeline mới thật vào tab Ch6 của demo tiểu luận3 bằng adapter/revision, không chỉ hyperlink hoặc replay. Giữ các chương cũ chạy theo mode đã công bố. Nếu backend source đổi phải tạo serving bundle revision mới; không âm thầm phục vụ archive cũ. Project01 vẫn có web độc lập, hai nơi dùng chung implementation/version mới.
5. Cập nhật notebook Ch6 của tiểu luận3 bằng revision giữ bản trước, vẫn tối đa 4 notebook/cây và có source thực trong cell. Tránh sao chép hai implementation lệch nhau; khai báo export/reuse tương thích yêu cầu source notebook.
6. Xuất **`tieuluan3/report/final/Tieu_Luan_AI_Final.docx`**, đúng thông tin bìa đã xác nhận: Triệu Tuấn Anh/B23DCCN053/D23CTPM01, PGS.TS Trần Đình Quế, Học viện Công nghệ Bưu chính Viễn thông. Giữ style tiểu luận3, render và kiểm toàn bộ trang, mục lục/bảng/hình/caption/link/nguồn. Chỉ một DOCX final; project riêng dùng README/report Markdown. PDF chỉ là bản đọc/QA nếu toolchain có sẵn.
7. Deploy là mục ngắn cuối chương, không thành chương riêng. Chốt hướng dẫn local/Git Bash/PowerShell, cấu hình Render hai service, provider secrets, model/package, quota/budget và trạng thái thật. Kiểm source/clean-start/UI/notebook/URL và gate độc lập ở mục 4.6; **sau PASS thì xóa đúng folder tham khảo rồi smoke lại**, ghi cleanup report. Không commit/push/deploy nếu chưa có yêu cầu riêng. Tài liệu trình bày rõ giới hạn nguồn, LLM, kiểm chứng và privacy của demo synthetic.

### Sản phẩm và nghiệm thu

- DOCX final mở được, nội dung khớp source/kết quả, render và xem toàn bộ trang PASS.
- Project01 và tab Ch6 tổng hợp chạy pipeline mới thật, câu trả lời là phần nổi bật; các tab khoa học cũ giữ được đường chạy.
- README, hướng dẫn demo dễ hiểu, báo cáo project Markdown, bảng/hình và danh sách file bàn giao; `phase3_report.md`, checkpoint toàn kế hoạch COMPLETE.
- Giữ nguyên artifact/TEST/evaluation cũ, không báo đã deploy online nếu mới kiểm cấu hình local.
- `RAG_KG_Tham_khao/` đã được xóa sau gate, project01 và tab Ch6 vẫn chạy/build từ source/package trong project01; mọi phần cần giữ đã chuyển đủ và attribution/hash truy được. Không xóa dữ liệu khoa học cũ hoặc env trong cleanup này.

## 5. Đường dẫn bàn giao và quy tắc tiếp tục

```text
FINAL_PROJECT01_LLM_V2_EXECUTION_PLAN.md
docs/final_project01/llm_v2/
  checkpoint.json
  phase1_report.md / phase2_report.md / phase3_report.md
project01/
  datasets/llm_v2/                 # sources/corpus/cards/dev/held-out/reference
  docs/llm_v2/                     # architecture/protocol/config choices
  artifacts/llm_v2/                # index/cache/probes/freeze/raw results/summary
    kg/                            # seed/assertions/adjacency/review/visualization nhỏ, không DB server
  provenance/                     # bản gốc thực sự thay đổi, nằm ngoài notebooks/
    group_rag_kg_source/           # source nhóm cần giữ + transfer_manifest, không dependency runtime
  notebooks/                      # vẫn 3 notebook code chính
  web/                            # React/Python hiện có, revision mới
  report/llm_v2/                  # kết quả và hình mới
tieuluan3/report/final/Tieu_Luan_AI_Final.docx
```

- Giữ các plan/checkpoint/AGENTS trước cập nhật ở `docs/final_project01/baseline/before_llm_v2/`, metadata trong `plan_v2_preservation.json`. Plan v1 nguyên byte, không thay handoff cũ. Việc thay dispatcher không là thực hiện phase.
- Verifier lịch sử hiện có: `scripts/verify_final_project01.py` cho REORG/inline-v1/FINAL-v1 baseline và `project01/scripts/verify_answer_first_v2.py` cho project01/2 UI revision. Khi đổi file đã pin ở phase mới, tạo revision resolver đúng archive/hash thay vì sửa verifier cũ hoặc cập nhật lại receipt cũ.
- Không cài lại môi trường GPU, chạy producer lịch sử, training/TEST cũ, commit/push/deploy hoặc tự mở phase tiếp theo.
- Provider/ngân sách đã chốt ở 2.1, không hỏi lại. Phase 1 xác minh model/quota/env key; thiếu phần nào thì hỏi đúng phần đó và tiếp tục công việc độc lập. Chỉ free tier, không dùng chi phí giả hoặc vượt trần trả phí 0 USD. Ghi rõ API call nào đã/chưa chạy.
- Mỗi phase chỉ cần một biên bản, checkpoint và evidence thiết yếu; không mở thêm tầng quy trình/phases cho việc nhỏ. Ưu tiên demo hai câu trả lời chạy thật trước khi làm đẹp/bổ sung tính năng.
- Bản 2.2: port tối đa core project nhóm, Gemini-only, mini-KG nhỏ có nguồn, không thêm phase/hạ tầng. Bản trước plan/checkpoint/dispatcher giữ tại `llm_v2/history/before_reference_reuse_v2_2/`, ghi ở `reference_reuse_preservation.json`. Chỉ cập nhật plan, chưa port code hoặc dựng graph.
- Bản 2.3: project01 tự chứa source/package; Phase 1 copy đủ, Phase 2 bỏ mọi dependency tham khảo và clean-start độc lập, Phase 3 gate rồi xóa folder tham khảo. Bản 2.2 trước sửa giữ ở `llm_v2/history/before_standalone_v2_3/`, metadata `standalone_preservation.json`. Lượt sửa plan chưa copy/delete hoặc chạy phase.

Tài liệu thiết kế tham khảo đã đọc: [OpenAI — Optimizing LLM Accuracy](https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy), [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices), [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output), [Searching for Best Practices in RAG](https://arxiv.org/html/2407.01219v1). Phải kiểm lại tài liệu/provider/model/pricing thực sự dùng ở Phase 1; không coi model ID hoặc giá trên mạng là đã xác nhận quyền truy cập của tài khoản.
