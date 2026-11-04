# Kiến trúc chốt ở Phase 1 — 02/11/2026

Trạng thái: thiết kế và đầu vào đã chuẩn bị. **Web/pipeline LLM mới chưa triển khai**; code hoạt động hiện tại vẫn là bản offline. Phase 2 port source nhóm từ bản local, không đọc folder tham khảo hay chạy code trong provenance.

## Luồng chính

```text
Câu hỏi tiếng Việt
  ├─ LLM trực tiếp: cùng Gemini 3.8 Flash, không retrieval/search ngoài
  └─ Coordinator + pre-retrieval (1 call): intent, ngôn ngữ, chiều quan hệ,
       giữ câu gốc, nhiều nhất 3 query và entity IDs
       → Knowledge: BM25 + Gemini embedding + mini-KG có nguồn
       → HybridSearcher._fuse: RRF theo cùng chunk_id → khoảng 20 candidate
       → GeminiReranker (1 call): xếp lại theo câu gốc, chọn tối đa 6 evidence
       → Risk: tùy nhu cầu, đủ 21 field mới dùng CDC checkpoint bất biến
       → Reporter (1 call): câu trả lời Việt + claims/citation
       → Verifier (1 call + code): evidence có thực, quote/chiều/điều kiện,
         hỗ trợ từng claim, không thay score CDC
       → phát hành chính xác bản được duyệt
```

Năm agent là năm trách nhiệm trong Python, không phải năm service hoặc năm model. Risk không cần API LLM. Coordinator chia sẻ một call với strategy pre-retrieval. Knowledge gọi Gemini rerank nhưng BM25/RRF/graph lookup chạy local. Tối đa một vòng phản hồi: lấy thêm evidence nếu cần → Reporter sửa → Verifier kiểm lại, không lặp vô hạn. Không đủ nguồn thì phát hành câu trả lời giới hạn hữu ích. Không cung cấp chain-of-thought, chỉ kế hoạch/công cụ/nguồn/quyết định ngắn.

## Những hàm được ghép

| Khối | Input → xử lý → output |
|---|---|
| QueryStrategy/PreRetriever | Câu gốc → rewrite/decompose có ràng buộc → queries/entity/intent/direction |
| Embedder | Title/section/text hoặc query → Gemini embedding-001 768 chiều → vector L2 chuẩn hóa |
| BM25Store | Chunk tiếng Anh + query → tokenizer/index → rank sparse |
| VectorDBClient local | Vector truy vấn → cosine trên NumPy → rank dense |
| Graph lookup | Entity + chiều/loại quan hệ → 1 hop, tối đa 2 → assertion IDs và chunk nguồn |
| HybridSearcher._fuse | Ba danh sách rank → RRF k=60 → candidate chung ID |
| Retriever._merge_results | Candidate của tối đa 3 query → dedup → candidate giới hạn |
| BaseReranker._to_ranked_result | Candidate + điểm mới → giữ original_rank → RankedResult |
| PromptBuilder/GeminiGenerator | Câu gốc + evidence đánh số → sinh câu trả lời/claims → bản nháp |
| Verifier | Bản nháp + chunk gốc/CDC server → code + semantic check → duyệt/sửa/giới hạn |

Giá trị development khởi đầu: dense/sparse/KG weight 0,4/0,4/0,2; top candidate 20; top evidence 6; query tối đa 3. Khóa cấu hình thực sau development trước held-out. Không nhận đây là bộ tham số tối ưu.

## KG có tác dụng gì?

Seed r2 có 35 concept, 35 assertion từ 20 chunk/17 tài liệu. Từng assertion có quote, vị trí trong full QA, URL, hướng, polarity và điều kiện. Ví dụ `diabetes → MAY_DAMAGE → kidney_damage` trỏ về câu mô tả glucose cao làm hại thận. Không suy ngược `kidney_damage → diabetes`. Quan hệ `SUPPORTS` luôn phải đọc điều kiện: *duy trì đường huyết an toàn* bảo vệ thần kinh, khác hoàn toàn *đường huyết cao*.

Phase 2 port normalize/cache/aggregate/export/PyVis từ notebook nhóm; thêm provenance Document→CONTAINS→Chunk→MENTIONS→Concept. MENTIONS không là assertion y khoa. Graph trả chính chunk nguồn vào RRF và rerank; không chỉ vẽ ảnh graph. Chuỗi A→B→C không cho phép suy A gây C. Không có cạnh không chứng minh không tồn tại quan hệ.

## Provider và môi trường

Generation dùng **gemini-3.8-flash**, endpoint Interactions `store=false`, thinking `low`, không search/grounding. Probe thật PASS; `generateContent` trước đó timeout, model 2.5 thử tương thích trả 404, giữ nguyên receipt lỗi. Dùng SDK `google-genai` trong env serving nhỏ đã có `uv.lock`; bridge theo interface LangChain để giữ QueryStrategy/GeminiGenerator. Không mặc định wrapper `ChatGoogleGenerativeAI` dùng endpoint đã probe PASS; kiểm SDK bridge ở Phase 2. HTTP stdlib chỉ dùng cho preflight, không thay toàn bộ core nhóm.

Embedding `gemini-embedding-001`, `RETRIEVAL_DOCUMENT` cho corpus và `RETRIEVAL_QUERY` cho truy vấn, cùng dimension 768, L2 normalize cả hai. Probe document vector PASS, index thật chưa build. Cache key gồm model/dimension/task/text hash. Index lưu nội bộ JSON/NumPy, không Qdrant/Neo4j server. Không dùng LSA làm neural embedding.

Python WSL hiện có 3.11.17; hai env GPU giữ nguyên. `environment/llm_v2/uv.lock` resolve 72 package, chưa cài. Phase 2 tạo đúng **một env serving riêng** từ lock này. Không bắt Torch/TF/OpenAI/Groq/Cohere/Neo4j/Qdrant để thỏa import không dùng. Thư viện visualization chỉ dùng offline.

## Quota và trải nghiệm demo

Người dùng xác nhận ngày 02/11/2026: generation 5 RPM / 250.000 TPM / **20 RPD**; embedding 100 RPM / 30.000 TPM / 1.000 RPD. Người dùng chọn giữ model và chạy nhiều ngày. Không đổi key để tăng quota hoặc tự giảm benchmark.

Một queue chung, concurrency=1; conservative cap generation 4 RPM, 18 RPD (chừa 2 cho thao tác ngoài app), embedding 60 RPM/900 RPD; không vượt quota provider. Cần đối chiếu snapshot sử dụng mới trước phiên, không coi ledger local thấy được mọi call ngoài app. Reset theo ngày provider ở America/Los_Angeles, không UTC hay ngày Bangkok. Timeout một call 90s, comparison deadline 900s gồm chờ; UI dùng job/polling, hiển thị tiến độ và `waiting_quota` thay vì spinner vô hạn. Tham số này cần xác minh bằng luồng dọc Phase 2.

Hai nhánh thường cần 5 generation call/cặp (1 direct + 4 RAG), tương đương ít nhất 200 call cho 40 câu. Dự trù tối đa một vòng feedback thêm 3 call/cặp → 320 call, chưa retry. Tối thiểu 10–16 ngày quota provider nếu dành toàn bộ 20 RPD cho evaluation; cap local 18 RPD là 12–18 ngày. Development 20 cặp có thể thêm 100–160 call (6–9 ngày cap local), không là dự báo hoàn thành chắc chắn. Phase 2 ưu tiên demo vài câu trước, rồi chạy evaluation theo checkpoint nhiều ngày. Không tự sleep hàng giờ/ngày.

## Contract dữ liệu / an toàn

Chi tiết machine-readable ở `provider_config.example.json` và `contracts.json`. Giới hạn question 4096 ký tự; profile synthetic/TRAIN tùy chọn. Key chỉ backend `project01/.env` đã ignore hoặc Render env; không gửi frontend. Chỉ văn bản công khai lên API. Tài liệu retrieval là dữ liệu không đáng tin để ra lệnh; không cho đổi tool/system prompt. JSON hợp schema không đảm bảo claim đúng.

API dự kiến: tạo compare job → poll trạng thái từng nhánh → kết quả cuối gồm answer_vi, claims, citations, usage, model/version, cache/live, latency toàn pipeline và error rõ. `/health` chỉ liveness, `/ready` báo data/provider config riêng và không gọi LLM. Sai key/quota/timeout không fallback offline rồi gắn nhãn live. Timeout local không bảo đảm provider đã hủy request; ghi unknown consumption, không tự replay claim held-out.

## Chuyển source và notebook

`reuse_map.json` chỉ rõ original → copy → class/hàm giữ/sửa → cell/export dự kiến. Phase 1 đã copy, chưa port. Giữ 3 notebook `01_Data_KB_RAG`, `02_Diabetes_Multi_Agent`, `03_Evaluation`; code thuật toán đủ trong cell, export một chiều sang namespace mới `project01_llm_v2` dưới backend. Trước sửa phải archive/hash notebook/module/UI cũ và tạo resolver revision đúng lịch sử. Không sửa verifier/receipt cũ.

Nguồn chính thức đã đối chiếu 02/11/2026: [Interactions](https://ai.google.dev/gemini-api/docs/interactions-overview), [embedding](https://ai.google.dev/gemini-api/docs/embeddings), [giá](https://ai.google.dev/gemini-api/docs/pricing), [quota](https://ai.google.dev/gemini-api/docs/rate-limits). Model miễn phí công khai + user xác nhận tier không phải chứng nhận đã kiểm hóa đơn.
