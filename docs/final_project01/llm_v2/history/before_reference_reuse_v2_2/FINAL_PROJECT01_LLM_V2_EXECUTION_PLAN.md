# Kế hoạch hiện hành — project01 RAG + LLM và tiểu luận final

Phiên bản 2.1 — 01/11/2026, Asia/Bangkok. Ưu tiên làm gấp, đúng **3 phase**. Đã chốt Google AI Studio / Gemini API **free tier**, ngân sách trả phí **0 USD**.

- Checkpoint hiện hành: `docs/final_project01/llm_v2/checkpoint.json`.
- Kế hoạch trước `FINAL_PROJECT01_EXECUTION_PLAN.md` là lịch sử: Phase 1–2 hoàn tất, Phase 3 chưa thực hiện; phần final chưa làm được chuyển đầy đủ vào Phase 3 của kế hoạch này.
- Đây là kế hoạch được người dùng yêu cầu lập sau khi đồng ý nâng cấp bằng API LLM. Lượt lập kế hoạch **không bắt đầu Phase 1**, không gọi API có phí, không tải corpus mới hoặc thay pipeline đang chạy.

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

Lý thuyết vẫn ngắn gọn, đủ ý, dễ hiểu, ít công thức. Giải thích hợp các hàm theo input → xử lý → output. Project01 giữ **3 notebook**, mỗi cây notebooks tối đa 4, source thuật toán đầy đủ trong cell; backend export một chiều từ notebook. File `.py` hỗ trợ vận hành không được trở thành implementation thuật toán duy nhất.

## 3. Điểm xuất phát và những điều cần sửa thật

- Bản offline hoàn tất: CDC 253.680 dòng/21 field, checkpoint scratch seed42/6 Dense; MedQuAD subset 247 document/762 chunk, graph 62 lexical anchor; BM25 + LSA + graph.
- Bản hiện tại chưa gọi LLM. Hàm chọn trích đoạn dựa vào từ khóa có thể lấy một câu cùng chủ đề nhưng không trả lời đúng câu hỏi. Glossary làm mất quan hệ/cấu trúc tiếng Việt; chunk có thể đứt ngữ cảnh, compact snapshot thiếu URL gốc từng bài.
- Ví dụ lỗi development đã quan sát: hỏi “Bệnh thận có làm tăng nguy cơ tiểu đường không?” nhưng trả câu nhắc kiểm tra bệnh thận hằng năm. Phải giữ đúng chiều quan hệ A → B, không lấy B → A làm bằng chứng thay thế.
- UI `answer_first_v2` đã đặt câu trả lời trước, nguồn/công cụ và trace dưới; có ba tab. Giữ nguyên nguyên tắc ưu tiên câu trả lời này.
- P0/P1/P2 và 120 đầu ra cũ là lịch sử. 82,5% task success không là chất lượng RAG+LLM mới, càng không là accuracy chẩn đoán. Không dùng bộ evaluation đã xem làm held-out mới.
- Verifier cũ chủ yếu kiểm integrity/số/từ khóa, chưa đủ để kiểm một câu trả lời LLM có diễn đạt lại. Cần kiểm mức hỗ trợ từng phát biểu bằng evidence.

## 4. Các quyết định triển khai

### 4.1. API, chi phí và môi trường

- **Provider đã chốt: Gemini Developer API, key từ Google AI Studio; chỉ dùng Free Tier.** Không triển khai adapter OpenAI trong đợt này. Tổng chi phí trả phí được phép là **0 USD** cho cả embedding, development, demo và evaluation; không bật billing, mua credit, tự nâng tier hoặc chuyển sang model/tính năng trả phí.
- Phase 1 chỉ còn chốt model ID và hạn mức request/token thực tế của project, không hỏi lại provider/ngân sách đã được người dùng xác nhận. Model ưu tiên khảo sát `gemini-3.8-flash`, embedding text ưu tiên `gemini-embedding-001`: tài liệu giá công khai ngày 01/11/2026 có free tier, nhưng **chưa probe quyền truy cập/quota/key của tài khoản**. Chỉ chọn chính thức sau kiểm tra; cả hai nhánh dùng cùng model sinh câu trả lời. Nếu model không truy cập được thì chỉ chọn model khác còn free trong project và chốt trước evaluation, không chuyển trả phí.
- Key người dùng đã cung cấp qua chat **không được chép vào plan/checkpoint hoặc file tracked**. Backend đọc `GEMINI_API_KEY` từ môi trường hoặc `.env` local đã xác nhận Git ignore; Render dùng Environment Variables. Không đưa vào `VITE_*`, frontend, notebook output, log hoặc Git; không yêu cầu gửi lại key trong chat. Key đã xuất hiện trong chat nên khuyến nghị thay bằng key mới và đặt trực tiếp vào env; chưa kiểm thử, không tự thu hồi hoặc sử dụng để gọi API trong lượt chỉ cập nhật plan.
- Dùng runtime WSL Ubuntu/user tuananh hiện có. Ưu tiên HTTP client sẵn có/stdlib để không đổi hai env GPU; nếu bắt buộc có SDK mới thì dùng dependency/runtime phục vụ riêng có khóa và ghi rõ, không pip install tùy tiện vào env khoa học đã pin.
- Không cần huấn luyện GPU. Embedding là tạo index suy luận một lần, phải tính chi phí, lưu model/version/hash và cache. Chọn embedding tương thích truy vấn/corpus; không gọi LSA cũ thành neural embedding.
- Chỉ số `/health` phản ánh tiến trình; trạng thái dữ liệu/provider/key hiển thị riêng. Không gọi LLM ở mỗi health check. Không có key/quota thì báo unavailable rõ, không âm thầm thay bằng trích đoạn cũ rồi gắn nhãn LLM.

### 4.1.1. Chính sách free tier bắt buộc

- Free tier có giới hạn RPM/TPM/RPD theo **project và model**, không phải mỗi key. Không đổi key để né quota; không mặc định mức quota từ bài hướng dẫn hoặc cho rằng key nào cũng được truy cập model ghi “free” trên bảng giá. Xác nhận tier/quota trong AI Studio khi Phase 1, kiểm lại trước gọi thật; cấu hình project trả phí không được coi là free chỉ vì cùng model có dòng giá miễn phí.
- Chỉ dùng standard text generation/embedding đã xác nhận miễn phí. Tắt web search/grounding ngoài để giữ phép so sánh công bằng; không dùng Batch API/explicit context caching/dịch vụ khác nếu chưa xác nhận có free tier. “Gửi nhiều candidate trong một request rerank” là đóng gói prompt thường, không có nghĩa gọi Batch API.
- Một hàng đợi API tuần tự dùng chung cho mọi agent và cả hai nhánh, giới hạn token/call, backoff theo Retry-After với số lần thử hữu hạn. Khi hết quota ngày hoặc không đủ free-tier entitlement: lưu checkpoint, dừng gọi API và báo rõ; không tự chuyển trả phí hoặc lặp retry vô hạn. Nếu chỉ gặp giới hạn theo phút thì lên lịch lại có giới hạn, không khóa lượt làm việc bằng sleep dài.
- **80 output đánh giá không có nghĩa chỉ 80 API request.** Agentic RAG còn gọi lập truy vấn/rerank/sinh/kiểm chứng; embeddings và development cũng dùng quota. Phase 1 phải dự tính tổng request/token và chia phiên/ngày nếu cần. Khi chờ quota, giữ nguyên model/prompt/corpus đã khóa, chỉ tiếp tục claim chưa dùng; không chạy lại output đã hoàn thành hoặc âm thầm giảm số câu để nhanh đủ điểm.
- Cache embedding theo hash corpus/model và lưu output đúng lineage; cache local không bị gọi là trả lời live mới. Đo latency và token riêng, bao gồm retry/thời gian chờ; không dùng giá paid tier để nói có phí thực thu. Giá free-tier được ghi 0 theo cấu hình/tài liệu đã kiểm, còn hóa đơn thực tế không được tự khẳng định đã xác minh nếu chưa xem.
- Chỉ gửi văn bản corpus công khai và dữ liệu demo không định danh. Google công bố nội dung free tier có thể được dùng để cải thiện sản phẩm; không đưa hồ sơ sức khỏe thật hoặc thông tin cá nhân vào demo API.
- Bản 2.1 không đổi số phase, không bắt đầu Phase 1 và chưa thực hiện API probe. Nguồn đối chiếu: [Pricing](https://ai.google.dev/gemini-api/docs/pricing), [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), [API key security](https://ai.google.dev/gemini-api/docs/api-key).

### 4.2. Kiến trúc đích

```text
Câu hỏi + hồ sơ tùy chọn
  → Coordinator: phạm vi, intent, câu hỏi gốc, chiều quan hệ, kế hoạch
  → Pre-retrieval: chuẩn hóa/dịch truy vấn, tối đa 3 truy vấn khi thực sự cần
  → Knowledge: BM25 + semantic embedding + lexical graph → gộp ứng viên
  → Reranker: liên quan tới câu hỏi và có thông tin giúp trả lời? → top evidence
  → Risk: chỉ khi cần, kiểm đủ 21 field → checkpoint CDC giữ nguyên
  → Reporter (LLM): bản nháp tiếng Việt, phát biểu + citation
  → Verifier: nguồn/claim support/contradiction/score/đúng trọng tâm
  → Nếu cần: tối đa 1 vòng tìm thêm/sửa rồi kiểm lại
  → Phát hành đúng bản đã kiểm; không viết lại tự do sau kiểm chứng
```

- Coordinator có thể dùng LLM output có cấu trúc để phân tích intent/query; quyết định được giới hạn bởi code/allowlist. Không để tài liệu truy hồi ra lệnh đổi công cụ hoặc bỏ quy tắc.
- Bắt đầu retrieval với khoảng 20 candidate, chọn khoảng 5–8 evidence sau rerank. Đây là giá trị development, phải chốt trước evaluation, không lời hứa cấu hình tối ưu.
- Rerank bằng một lượt LLM theo lô trước nếu phù hợp ngân sách; trả candidate ID/đánh giá relevance. Kiểm ID tồn tại/không trùng/định dạng và có trạng thái không đủ bằng chứng. Không nhất thiết thêm cross-encoder nặng vào Render.
- Graph hỗ trợ candidate/concept expansion và có đường về nguồn. Giữ tên lexical graph nếu chưa xây được quan hệ y khoa được kiểm chứng; không tự tuyên bố KG suy luận nhân quả.
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

## Phase 1 — Chốt API, chuẩn bị KB và thiết kế đánh giá

**Mục tiêu:** đầu vào đủ tốt và cấu hình đủ rõ để làm pipeline ngay, không mất thời gian xây lại nền khoa học.

### Công việc

1. Đọc plan/checkpoint, kiểm các receipt/bản archive đang có. Ghi baseline cần sửa; giữ source/nb/UI/model/index/metric/report cũ đúng hash. Dùng verifier hiện hành ở cuối plan; không ghi đè verifier/receipt đã khóa.
2. Dùng provider/budget đã chốt: Google AI Studio / Gemini Developer API, Free Tier, trả phí 0 USD. Kiểm `GEMINI_API_KEY` có sẵn ở backend mà không in giá trị; nếu chưa có thì hướng dẫn đặt key trực tiếp vào env, không hỏi lại provider hoặc yêu cầu gửi key trong chat. Xác nhận tier/quota/model miễn phí thực tế rồi probe một request tối thiểu trong Phase 1 được gọi; ghi model/usage/latency/trạng thái không secret. Chốt model, hàng đợi tuần tự, timeout/backoff/quota và ước tính tổng request; chưa build toàn UI. Không có quyền free tier thì dừng API và làm tiếp phần dữ liệu độc lập, không nâng cấp billing.
3. Rà MedQuAD gốc và các nguồn chính thống liên quan cần bổ sung. Tập trung chủ đề đủ demo: khái niệm, yếu tố nguy cơ, vận động, ăn uống, biến chứng và quan hệ tiểu đường–thận. Phục hồi tài liệu đủ ngữ cảnh cùng title/URL gốc/source ID nếu có thể; chỉ thêm nguồn có quyền sử dụng phù hợp và attribution. Không đoán URL từ compact ID, không tải dữ liệu lớn không phục vụ câu hỏi.
4. Tạo corpus revision riêng: source snapshot/hash/ngày lấy, title/URL/section/document/chunk IDs, language, kích cỡ và ví dụ; chia theo đoạn/câu đủ nghĩa, có overlap vừa phải. Giữ corpus/index cũ nguyên trạng. Ghi bản nào có URL gốc, bản nào chỉ repository locator; không trộn âm thầm. Chốt corpus trước evaluation; không thêm tài liệu sau khi xem lỗi held-out rồi báo lại cùng score.
5. Chọn embedding/rerank strategy và token budget để làm nhanh/nhẹ trên Render. Xác định trường dữ liệu query plan, evidence, draft/claims/citations, verification và usage. Reranker không được coi chiều quan hệ ngược là câu trả lời đúng.
6. Chốt bộ mới **20 development + 40 held-out câu hỏi kiến thức**, có paraphrase tiếng Việt, câu hỏi quan hệ/phủ định, nhiều ý, thiếu bằng chứng và ngoài phạm vi. Tách trùng/nghĩa tương đương và mẫu sự kiện giữa dev/held-out; dùng chung KB là hợp lệ, không bắt buộc tách KB thành hai kho khác nhau. Reference/gold lấy từ nội dung nguồn, không từ ranking của hệ; chấp nhận nhiều đoạn/tài liệu hợp lệ và ghi coverage qrels chưa đầy đủ.
7. Viết rubric, cách chấm ẩn danh hai câu trả lời, metric/chi phí và chính sách lỗi/retry. Mặc định **1 lần/câu/nhánh = 80 output**; chỉ thêm lặp độc lập nếu ngân sách cho phép và khai báo số lặp **trước** chạy. Không rerun chọn câu trả lời đẹp. Giữ ví dụ lỗi đã thấy làm development/regression, không gọi là held-out mới.

### Sản phẩm và nghiệm thu

- `project01/datasets/llm_v2/`: source catalog, corpus revision, dataset card, dev/held-out và reference/rubric có version.
- `project01/docs/llm_v2/architecture.md`, `evaluation_protocol.md`; config `.example` không secret và provider contract/preflight receipt.
- Có model ID/free tier/quota đã xác nhận, budget trả phí 0 USD; probe API thật tối thiểu PASS; corpus đủ ngữ cảnh/metadata được kiểm; protocol chốt trước chạy held-out. Thiếu env key hoặc chưa đủ quyền free tier thì ghi WAITING_CONFIGURATION/WAITING_QUOTA và phần độc lập đã xong, không báo API PASS giả, không hỏi lại budget.
- `docs/final_project01/llm_v2/phase1_report.md`, checkpoint Phase 1 COMPLETE, Phase 2 READY. Chưa đánh giá held-out, chưa làm DOCX; không tự bắt đầu Phase 2.

## Phase 2 — Làm RAG + LLM, web hai nhánh và đánh giá

**Mục tiêu:** câu trả lời thật sự tốt hơn về tính hữu ích/căn cứ nếu evidence cho phép, có phép so sánh minh bạch.

### Công việc theo ưu tiên

1. Giữ bản gốc 3 notebook trước khi thay; cập nhật chính 3 file hiện có, không thêm notebook con vượt giới hạn. Notebook 01 chứa xử lý corpus/query, BM25/embedding/graph/fusion/rerank/context; notebook 02 chứa adapter LLM, năm vai trò, sinh/kiểm câu trả lời và API; notebook 03 chứa rubric/evaluator/summary/plots. Export backend có hash/version; đổi source frozen phải tạo revision mới cùng resolver cho archive cũ. Không seed lại producer cũ.
2. Làm một luồng dọc chạy được sớm: cùng câu hỏi → LLM trực tiếp và RAG+LLM → hai câu trả lời tiếng Việt. Sau đó hoàn thiện pre-retrieval, semantic index, rerank và Verifier. Không tiếp tục chỉ cải thiện UI trong khi core vẫn trả một đoạn trích không trả lời đúng ý.
3. Chạy pre-retrieval có cấu trúc, bảo toàn câu gốc/chiều quan hệ/phủ định, tối đa 3 query; giữ log ngắn đã chuẩn hóa. Tạo semantic index/caches versioned cho corpus mới, không refit index lịch sử. Thử retrieval/rerank trên dev với reference độc lập, xem candidate trước/sau, context và nguồn. Không mặc định mọi câu cần nhiều query hoặc nhiều lần LLM.
4. Reporter tạo câu trả lời trực tiếp, dễ hiểu, có claims/citations; Verifier kiểm đúng câu hỏi, hỗ trợ từng phát biểu, mâu thuẫn, URL/ID và điểm model. Khi không đủ nguồn, trả câu giới hạn hữu ích thay vì gắn citation cho suy đoán. Tối đa một feedback loop; cuối cùng phát hành đúng văn bản đã được kiểm. Không lưu hoặc hiển thị chain-of-thought.
5. Web giữ 3 tab, kết quả chính là **LLM trực tiếp / Hệ đa agent + RAG** đặt cạnh nhau. Nguồn, truy vấn viết lại, reranking, kiểm chứng/trace là phần mở rộng. Hiển thị model, trạng thái chạy, latency tổng, token và chi phí ước tính theo giá đã kiểm; phân biệt usage provider trả về với ước lượng. Streaming nếu có không gọi bản nháp chưa kiểm là câu trả lời đã duyệt. Phần hồ sơ/CDC giữ như demo bổ sung. P0/P1/P2 chỉ truy cập ở tài liệu/benchmark lịch sử, không là lựa chọn chính.
6. Kiểm tra tập trung: câu hỏi ảnh đã lỗi/chiều ngược, tiếng Việt, query không đổi ý, citation bịa/không hỗ trợ, không đủ bằng chứng, thiếu BMI, score không bị LLM đổi, prompt injection từ tài liệu, API timeout/quota/401, secret không vào frontend/log, deadline/budget và notebook-export parity. Kiểm API/UI thật desktop/mobile; mock chỉ cho lỗi cần tái hiện, ghi rõ; không dùng mock để nghiệm thu khả năng trả lời thật.
7. Chốt corpus/index/prompts/query/rerank/model/config/evaluator và rubric sau development. Chạy 40 held-out ×2 nhánh đúng số lặp đã khai báo, trong budget. Ghi raw request/response đã loại secret, source IDs, usage, thời gian toàn pipeline, cache/live, lỗi/retry và claim. Không thay raw output, không bỏ case lỗi, không dùng lại held-out để tuning. Nếu có incident thì giữ evidence và tạo revision công khai, không âm thầm chạy lại.
8. Chấm chung về đúng trọng tâm/tính đúng/đủ ý/biết giới hạn; RAG thêm citation support và retrieval relevance. Chấm ẩn nhánh, cân bằng thứ tự; người dùng có thể đọc/chấm một subset khi sẵn sàng, không giả nhận đã có chuyên gia. LLM judge chỉ hỗ trợ và ghi model/reviewer; không để Verifier tự chấm chính nó thành benchmark độc lập. Báo n, lỗi, mức bất định khi phù hợp; không chọn metric độ dài/HTTP200 làm chất lượng.
9. Xuất bảng và tối đa 3–4 hình có giải thích trục/đơn vị/mẫu số/thông điệp: chất lượng hai nhánh, mức hỗ trợ nguồn, latency/token/chi phí, nhóm lỗi khi hữu ích. Cập nhật README/hướng dẫn demo/report Markdown bằng revision giữ gốc. Chuẩn bị Render config/dependencies CPU/package version mới, key server-side, không deploy.

### Sản phẩm và nghiệm thu

- Hai nhánh thực sự gọi cùng model API; pipeline dùng evidence mới, có pre-retrieval/rerank/Verifier và câu trả lời tiếng Việt. Không có key/quota thì thông báo rõ, không thay bằng replay mà gọi live.
- Ba notebook có full code và output development; mặc định chỉ đọc saved output, `RUN_API/RUN_EVALUATION=False`, `ALLOW_PAID_API=False`; khi chạy phase được yêu cầu chỉ bật call free-tier có kiểm soát. Backend/source/package parity PASS.
- Có kết quả held-out mới (mặc định 80 output), rubric/review/usage/chi phí đầy đủ; P0/P1/P2 cũ nguyên trạng, không tái dùng 82,5% làm kết quả mới.
- UI/API smoke/E2E PASS, source và bản trước được bảo toàn; `phase2_report.md`, checkpoint COMPLETE và Phase 3 READY. Chưa tự làm DOCX/Phase 3.

## Phase 3 — Tích hợp tiểu luận final, demo tổng hợp và bàn giao

**Mục tiêu:** hoàn thành cả phần final còn dở trong kế hoạch trước bằng sản phẩm mới đã đánh giá.

### Công việc

1. Tạo final tại `tieuluan3/report/final/`, giữ DOCX/manuscript phát hành trước nguyên trạng. Sáu chương: lịch sử AI; ML; CNN; RNN–LSTM; KB/KG/RAG; đa agent và case study project01 RAG+LLM. Giữ lý thuyết cơ bản, ít công thức và giải thích hợp hàm/từng hàm bằng ví dụ.
2. Rà yêu cầu thầy từ evidence có sẵn: 2–3 dataset mỗi chương theo phạm vi đã có (link/kích cỡ/mẫu/phân bố/nhận xét), Scratch/Keras/PyTorch cho các chương thực nghiệm; CNN/RNN/LSTM trên 5 layer theo quy ước đếm công bố; bảng so sánh mô hình. Không tự train hoặc mở lại TEST để lấp thiếu số. Ghi thiếu thực sự nếu có, không tạo metric giả.
3. Ch5 giải thích pre-retrieval/hybrid search/KG/rerank/grounded generation; Ch6 giải thích năm vai trò, feedback và so sánh cùng LLM trực tiếp. Kết quả cũ A0/A1/A2 và P0/P1/P2 chỉ giữ đúng phạm vi lịch sử/đối chiếu, không trộn với benchmark mới hoặc để lấn nội dung chính. Giải thích mọi biểu đồ mới và không tuyên bố RAG thắng khi số đo không ủng hộ.
4. Tích hợp pipeline mới thật vào tab Ch6 của demo tiểu luận3 bằng adapter/revision, không chỉ hyperlink hoặc replay. Giữ các chương cũ chạy theo mode đã công bố. Nếu backend source đổi phải tạo serving bundle revision mới; không âm thầm phục vụ archive cũ. Project01 vẫn có web độc lập, hai nơi dùng chung implementation/version mới.
5. Cập nhật notebook Ch6 của tiểu luận3 bằng revision giữ bản trước, vẫn tối đa 4 notebook/cây và có source thực trong cell. Tránh sao chép hai implementation lệch nhau; khai báo export/reuse tương thích yêu cầu source notebook.
6. Xuất **`tieuluan3/report/final/Tieu_Luan_AI_Final.docx`**, đúng thông tin bìa đã xác nhận: Triệu Tuấn Anh/B23DCCN053/D23CTPM01, PGS.TS Trần Đình Quế, Học viện Công nghệ Bưu chính Viễn thông. Giữ style tiểu luận3, render và kiểm toàn bộ trang, mục lục/bảng/hình/caption/link/nguồn. Chỉ một DOCX final; project riêng dùng README/report Markdown. PDF chỉ là bản đọc/QA nếu toolchain có sẵn.
7. Deploy là mục ngắn cuối chương, không thành chương riêng. Chốt hướng dẫn local/Git Bash/PowerShell, cấu hình Render hai service, provider secrets, model/package, quota/budget và trạng thái thật. Kiểm source/clean-start/UI/notebook/URL; không commit/push/deploy nếu chưa có yêu cầu riêng. Tài liệu trình bày rõ giới hạn nguồn, LLM, kiểm chứng và privacy của demo synthetic.

### Sản phẩm và nghiệm thu

- DOCX final mở được, nội dung khớp source/kết quả, render và xem toàn bộ trang PASS.
- Project01 và tab Ch6 tổng hợp chạy pipeline mới thật, câu trả lời là phần nổi bật; các tab khoa học cũ giữ được đường chạy.
- README, hướng dẫn demo dễ hiểu, báo cáo project Markdown, bảng/hình và danh sách file bàn giao; `phase3_report.md`, checkpoint toàn kế hoạch COMPLETE.
- Giữ nguyên artifact/TEST/evaluation cũ, không báo đã deploy online nếu mới kiểm cấu hình local.

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
  provenance/                     # bản gốc thực sự thay đổi, nằm ngoài notebooks/
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

Tài liệu thiết kế tham khảo đã đọc: [OpenAI — Optimizing LLM Accuracy](https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy), [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices), [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output), [Searching for Best Practices in RAG](https://arxiv.org/html/2407.01219v1). Phải kiểm lại tài liệu/provider/model/pricing thực sự dùng ở Phase 1; không coi model ID hoặc giá trên mạng là đã xác nhận quyền truy cập của tài khoản.
