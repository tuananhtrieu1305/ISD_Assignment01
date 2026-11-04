# Khảo sát RAG/KG của nhóm để tái sử dụng cho project01

Ngày 02/11/2026. Source tham khảo: `RAG_KG_Tham_khao/PTHTTM-RAG/`.

Phạm vi: đọc source, code cell và JSON graph đã lưu. Không import/chạy ứng dụng hoặc notebook tham khảo, không kết nối Qdrant/Neo4j, không tải model, không chạy test/train/evaluation hay gọi API. Chưa xác nhận end-to-end, tốc độ, RAM hoặc chất lượng trả lời của project nhóm trong runtime hiện tại.

## Kết luận

**Có thể dùng lại khung RAG và cách dựng KG, rồi chuyên biệt hóa cho dữ liệu tiểu đường.** Không cần viết lại toàn bộ. Tuy nhiên, RAG và KG của source nhóm hiện là hai luồng tách rời; không thể chỉ thay dataset là chatbot tự có KG hỗ trợ truy hồi.

Ưu tiên chuyển logic phù hợp vào ba notebook project01 và export backend; không import trực tiếp package `app` của nhóm hoặc sao chép toàn bộ hạ tầng/dependency vào env GPU hiện có. Giữ source tham khảo nguyên trạng và ghi attribution cho công việc nhóm.

## 1. Những phần đã có và dùng được

| Thành phần | Source | Cách tái sử dụng |
|---|---|---|
| Viết lại/tách/mở rộng truy vấn | `chatbot/app/retrieval/pre_retrieval.py` | Giữ khung strategy, chuyển provider sang Gemini và prompt từ pháp luật sang y khoa; bảo toàn chiều quan hệ, phủ định, ngôn ngữ; giới hạn tối đa 3 query bằng code |
| Hybrid search + RRF | `chatbot/app/retrieval/hybrid_searcher.py` | Dùng thuật toán hợp nhất dense/sparse theo rank; thêm nhánh KG và metadata nguồn chung |
| Hợp nhất nhiều truy vấn | `chatbot/app/retrieval/retriever.py` | Giữ cơ chế gom theo chunk ID; xem lại cách chỉ lấy max score và giới hạn query; không fan-out API vô hạn |
| BM25 | `chatbot/app/database/bm25_store.py` | Tái sử dụng nguyên lý index/query và metadata; rebuild corpus y khoa revision mới, không nạp index luật |
| Reranker | `chatbot/app/retrieval/reranker.py` | Giữ interface candidate → ranked result và original_rank; chọn Gemini rerank theo lô prompt để tránh thêm model nặng ở bản phục vụ đầu tiên |
| Gemini generation | `chatbot/app/generation/generator.py` | Có `GeminiGenerator`; tái sử dụng cách đưa context và lấy text, bổ sung usage/quota/timeouts/schema và Verifier |
| Context có đánh số nguồn | `chatbot/app/generation/prompt.py` | Giữ cách đóng gói nguồn, thay system prompt/metadata; ánh xạ citation thực sự được dùng và kiểm claim support |
| Chunking có cấu trúc | `chatbot/app/indexing/chunking.py` | Dùng ý tưởng section-first + overlap; thay chương/mục/điều bằng title/section/URL và chia câu đủ nghĩa |
| KG extraction/cache/aggregate/visualization | `chatbot/Extract_Graph.ipynb` | Tái sử dụng cấu trúc hàm và cache/resume; thay schema/phạm vi/provider và thêm bằng chứng cho từng quan hệ |

Luồng web của nhóm trong `ChatbotPipeline.ask`: retriever → reranker → generator → answer/sources. Không có graph retriever hoặc Verifier trong luồng này.

## 2. Những điểm không được mang nguyên trạng

1. **Pre-retrieval còn gọi OpenAI.** `PreRetriever.__init__` tạo `ChatOpenAI` trực tiếp; chọn `LLM_PROVIDER=gemini` chỉ đổi generator. Tham số `llm` truyền vào constructor cũng chưa được dùng. Đổi provider factory/injection trước khi chạy bằng key Gemini free tier.
2. **KG chưa tích hợp vào RAG web.** `app/` không đọc graph JSON hay truy vấn Neo4j. Các câu hỏi graph trong notebook không chứng minh chatbot web đang dùng graph.
3. **Dữ liệu, prompt và schema là luật lao động.** Có `chuong/muc/dieu`, collection/index luật và regex `### Điều ...`. Cần chuyển sang document/chunk y khoa; không dùng trọng số/index/vector luật cho diabetes.
4. **Đang phụ thuộc nhiều thành phần hơn project01:** FastAPI/LangChain, BGE-M3 embedding, BGE cross-encoder, Qdrant; KG notebook dùng Neo4j. Requirements không pin version. Không cài nguyên requirements vào hai env GPU đang khóa. BGE có thể khảo sát sau khi đo tài nguyên, không mặc định là lựa chọn phù hợp cho Render free.
5. **KG notebook có nhiều bản hàm extraction.** Bản đầu dùng OpenAI; bản sau đổi sang Groq và truyền literal `GROQ_API_KEY`, không phải đọc giá trị env ở dòng đó. Chọn một implementation Gemini rõ ràng, không dựa vào thứ tự cell để vô tình chọn provider khác.
6. **Cache KG chưa khóa đầy đủ model/prompt/schema.** Article ID có hash nội dung nhưng cache skip chỉ theo ID; đổi extractor có thể vẫn đọc kết quả cũ. Cache mới phải có fingerprint corpus/chunk/model/prompt/schema và trạng thái thành công/lỗi rõ.
7. **Quan hệ mới lưu nguồn ở cấp article, chưa có evidence span chính xác.** Cần thêm quote/offset, hướng, phủ định, điều kiện và kiểm nội dung. `count` là số lần xuất hiện, không phải confidence hoặc mức đúng y khoa.
8. **Entity normalization còn đơn giản.** Casefold tên chưa giải quyết alias Anh–Việt, subtype hoặc cùng tên khác loại; Neo4j MERGE dùng tên raw có thể không khớp tên canonical. Dùng ID canonical có type, alias rõ và kiểm endpoint/dedup.
9. **Chunk/index cần version theo nội dung.** ID hiện theo document + chunk_index; indexer bỏ qua nếu document_id đã tồn tại ở hai store, dù nội dung có thể đổi. Bản project01 phải có corpus hash/version và không trộn vector của hai embedding model/dimension.
10. **Source list chưa là citation verification.** Pipeline trả mọi result sau rerank, chưa phân biệt câu trả lời thực sự trích nguồn nào; cần citation map + claim evidence và Verifier của project01.
11. **Notebook có `allow_dangerous_requests=True` cho GraphCypherQAChain.** Bản làm nhanh không dùng LLM sinh Cypher tự do; dùng truy vấn được định nghĩa trước, chỉ đọc, có giới hạn hop/kết quả.
12. Test pipeline hiện dùng mock công cụ; không coi đó là bằng chứng đã đo chất lượng RAG/KG thật. Chưa tìm thấy file LICENSE/COPYING ở root tham khảo; ghi nguồn nhóm và phần chỉnh sửa, không tự gán giấy phép open-source cho cả repository.

## 3. Hiện trạng KG tham khảo

Đọc trực tiếp `chatbot/kg_graph_all_data.json` được:

| Thành phần | Số lượng |
|---|---:|
| Tài liệu luật | 4 |
| Article | 1.407 |
| Entity | 6.001 |
| Relationship | 8.850 |

Graph JSON khoảng 8,4 MB theo byte file. Đây là số bản ghi xuất sẵn của miền luật, chưa audit tính đúng toàn bộ; không phải graph tiểu đường. Payload gồm `documents/articles/entities/relationships`; mỗi relationship có `source/type/target/count/source_files/article_ids`.

Phần dùng lại có giá trị nhất là quy trình: chia tài liệu → trích thực thể/quan hệ → lưu cache từng phần → chuẩn hóa/gộp → xuất JSON → trực quan hóa. Không cần tái sử dụng graph luật hoặc bắt buộc chạy Neo4j để áp dụng quy trình đó.

## 4. Dựng KG tiểu đường nhanh từ dữ liệu nào?

**Dùng văn bản MedQuAD/corpus y khoa đã phục hồi ngữ cảnh để tạo tri thức.** CDC là dữ liệu khảo sát bảng dùng cho checkpoint, không phải nguồn để biến tương quan feature thành quan hệ nhân quả.

Không dựng graph cho 253.680 người khảo sát. Có thể thêm node metadata mô hình/21 feature nếu cần giải thích công cụ, với quan hệ `MODEL_USES_FEATURE`; không gán các feature thành nguyên nhân bệnh chỉ vì model sử dụng chúng.

Đề xuất hai lớp trong cùng KG:

1. **Lớp provenance tự động:** Document → CONTAINS → Chunk → MENTIONS → Concept. Có thể dùng lại 62 lexical anchor để khởi tạo alias/candidate, nhưng quan hệ nhắc đến không phải sự thật y khoa.
2. **Lớp assertion có bằng chứng:** Concept A → loại quan hệ → Concept B, chỉ khi tài liệu nói rõ. Mỗi assertion lưu source_chunk_id/document_id, quote/offset, direction, polarity, điều kiện/subtype và trạng thái kiểm tra.

Schema loại thực thể nhỏ: Disease/Subtype, Symptom, RiskFactor, Complication, Lifestyle, Test và MedicalConcept. Quan hệ nhỏ, allowlist và phân biệt association với causation; không cho LLM tự phát minh hàng trăm loại quan hệ. Không thêm phác đồ/liều điều trị vào phạm vi demo.

Một quan hệ được đưa vào graph chỉ khi trích dẫn chứng minh được cả hai đầu và ý nghĩa quan hệ; tên hai thực thể cùng xuất hiện chưa đủ. Không có cạnh trong graph chỉ có nghĩa chưa có assertion được ghi nhận, không chứng minh quan hệ đó không tồn tại.

### Phạm vi làm nhanh

- Tạo lớp provenance trên corpus mới đã chốt.
- Pilot extraction trên khoảng 50–100 đoạn đủ ngữ cảnh thuộc các chủ đề cần demo, chọn theo phạm vi corpus/development, không theo lỗi held-out. Đây là phạm vi khởi đầu, không phải graph đã làm hoặc quota đủ cho một ngày.
- Gemini trích quan hệ một lần khi chuẩn bị dữ liệu, lưu cache và kiểm source span. Số đoạn gộp mỗi call theo token/quota; không chạy lại extraction trong từng lượt chat.
- Kiểm các cạnh dùng trong ví dụ demo và một mẫu kiểm độc lập, giữ cạnh chưa xác minh ngoài tập assertion được dùng trả lời. Không gọi review trợ lý là thẩm định lâm sàng.
- Xuất JSON và adjacency index; backend có thể duyệt graph bằng Python, frontend minh họa neighborhood bằng JSON. Không bắt buộc thêm service Neo4j/Qdrant. Có adapter sau nếu nhu cầu thật sự xuất hiện.

## 5. KG phải tham gia retrieval thật

```text
Câu hỏi
 → Coordinator / viết lại truy vấn bằng Gemini
 → BM25 + semantic vector search + concept/entity lookup
 → tìm neighborhood 1–2 hop có hướng/loại quan hệ phù hợp
 → lấy chính các source chunk của assertion
 → gộp candidate theo cùng chunk ID bằng RRF
 → rerank theo câu hỏi gốc
 → Gemini viết câu trả lời tiếng Việt có citation
 → Verifier kiểm phát biểu với chunk nguồn, không chỉ nhìn cạnh graph
```

Graph trả thêm nguồn liên quan và đường giải thích. Một đường A → B → C không tự động chứng minh phát biểu A gây C. Không bỏ evidence text chỉ vì đã có graph; câu hỏi thiếu bằng chứng cần câu trả lời giới hạn đúng phạm vi.

## 6. Áp dụng vào ba phase đã có

- **Phase 1:** dùng khảo sát này làm đầu vào; chốt thành phần lấy lại, schema KG nhỏ/metadata/alias, corpus và quota extraction cùng Gemini adapter. Không làm thêm một phase riêng cho KG.
- **Phase 2:** chuyển logic đã chọn vào notebook 01/02, dựng semantic index + KG pilot, nối graph vào Knowledge Agent và hoàn thiện rerank/generation/Verifier. So sánh chính vẫn LLM trực tiếp với hệ đa agent + RAG/KG, cùng Gemini. Benchmark mới đo cả usefulness và nguồn, không giả định graph luôn tốt hơn.
- **Phase 3:** đưa sơ đồ/ảnh graph và ví dụ đường nguồn có thật vào tiểu luận; giải thích rõ phạm vi/pilot/khả năng kiểm chứng, không nhận là ontology y khoa đầy đủ.

Không sửa source nhóm, không sao chép API key, `.env`, index luật hoặc graph luật sang project01. Giữ UI và hợp đồng năm agent của project01; chỉ tái sử dụng module/thuật toán cần thiết có khai báo nguồn. Ba notebook vẫn là nguồn xem code chính.

Đây là báo cáo khảo sát, chưa bắt đầu Phase 1 hoặc xây KG. Snapshot hash source đã đọc ở `reference_rag_kg_snapshot.json` cùng thư mục.
