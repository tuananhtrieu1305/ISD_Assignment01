# KẾ HOẠCH MỞ RỘNG CHƯƠNG 5 — KNOWLEDGE BASE, KNOWLEDGE GRAPH VÀ RAG

> **LỊCH SỬ:** Phase 10–19 đã hoàn thành. Yêu cầu V3 ngày 2026-10-16 và các lệnh
> `làm phase 20` đến `làm phase 35` phải theo `TIEU_LUAN_AI_V3_EXECUTION_PLAN.md`.

> **Trạng thái kế hoạch:** `COMPLETE` ngày 2026-10-14. Đây là nguồn sự thật cho đợt mở rộng Chương 5 của tiểu luận. Các Phase 0–9 trong `TIEU_LUAN_AI_EXECUTION_PLAN.md` là lịch sử đã hoàn thành; đợt mở rộng dùng **Phase 10–19** để không trùng số.
>
> Khi người dùng gõ **`làm phase N`** với `N` từ 10 đến 19, trợ lý phải đọc toàn bộ file này, kiểm tra dependency, trạng thái Git và nhật ký, rồi tự thực hiện phase tương ứng đến khi đạt tiêu chí nghiệm thu hoặc gặp blocker thực sự cần người dùng quyết định.

## 0. Mục tiêu cuối và phạm vi đã khóa

Mục tiêu cuối là tạo một bản DOCX tiểu luận mới có Chương 5 đúng nội dung giảng viên ghi trên bảng:

- Knowledge Base (KB), Knowledge Graph (KG) và Retrieval-Augmented Generation (RAG);
- sự kết hợp KG–RAG;
- hai case study thực nghiệm: bệnh tiểu đường và tài chính/chứng khoán;
- một mục ngắn triển khai với Agent ở cuối chương.

Quyết định cấu trúc bắt buộc:

1. **Chương 4 giữ nguyên** là “Recurrent Neural Network (RNN)”; không renumber code, artifact, heading hoặc caption hiện có.
2. **Chương 5 mới** là “Knowledge Base, Knowledge Graph và Retrieval-Augmented Generation”.
3. **Không còn chương/phần deployment độc lập.** Nội dung trong `report/sections/05_trien_khai.md` được phân bổ thành các mục ngắn ở cuối các chương chính:
   - cuối Chương 2: triển khai dự đoán nguy cơ tiểu đường bằng ML;
   - cuối Chương 3: triển khai phân loại EuroSAT bằng CNN;
   - cuối Chương 4: triển khai RNN cho customer/AAPL;
   - cuối Chương 5: triển khai KG–RAG với Agent.
4. Kết luận trở thành **Chương 6/Kết luận** tùy style cuối cùng, nhưng phải đứng sau Chương 5.
5. Bản release 73 trang hiện tại `term_paper/report/Tieu_luan_AI_ML_CNN_RNN.docx` là **baseline chỉ đọc**. Không ghi đè nó trong các Phase 10–18.
6. Bản ứng viên mới dùng tên `term_paper/report/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`; chỉ được coi là release khi Phase 19 hoàn thành.

## 1. Cách xử lý lệnh `làm phase N`

Khi nhận lệnh cho Phase 10–19, trợ lý phải:

1. Đọc toàn bộ file này và phần liên quan trong `TIEU_LUAN_AI_EXECUTION_PLAN.md`.
2. Đọc mọi `AGENTS.md` áp dụng cho đường dẫn sẽ thao tác.
3. Kiểm tra bảng trạng thái ở Mục 10 và nhật ký ở Mục 14.
4. Kiểm tra `git status`; không ghi đè thay đổi không liên quan của người dùng.
5. Dùng dữ liệu, code, metric, hình và trích dẫn thật; không bịa số liệu hoặc kết quả kiểm thử.
6. Nếu cần tải dữ liệu/model, ưu tiên nguồn chính thức và lưu URL, thời điểm truy cập, revision/commit và SHA-256.
7. Chạy kiểm tra tương xứng với rủi ro; lưu log/artifact có thể tái lập.
8. Cập nhật trạng thái, file tạo/sửa, lệnh kiểm tra, kết quả, quyết định và blocker vào chính file này.
9. Chỉ đánh dấu `COMPLETE` khi mọi acceptance criteria của phase đạt.
10. Trả lời người dùng bằng kết quả, file quan trọng và kiểm tra đã chạy.

Quy tắc tự chủ:

- Không hỏi lại các quyết định đã khóa trong kế hoạch này.
- Được tự chọn chi tiết nhỏ về thư viện hoặc cấu trúc code nếu không đổi dataset, câu hỏi nghiên cứu, giao thức đánh giá hay cấu trúc chương.
- Không tự ý dùng dịch vụ trả phí, gửi dữ liệu lên dịch vụ ngoài hoặc yêu cầu API key.
- Hệ thống bắt buộc chạy được ở chế độ không có API key. LLM/API bên ngoài, nếu có, chỉ là adapter tùy chọn.
- Nếu một model sinh không phù hợp tài nguyên Render, giữ đánh giá RAG local và deploy chế độ extractive/grounded có citation; không làm Phase 16 phụ thuộc vào GPU.
- Nội dung y khoa chỉ mang tính thông tin, không chẩn đoán/điều trị. Nội dung tài chính không dự báo giá hay khuyến nghị đầu tư.

## 2. Diễn giải nội dung trong ảnh giảng viên

Ảnh bảng được chuyển thành dàn ý chuẩn hóa sau:

### 5.1. Mở đầu

#### 5.1.1. KG và RAG kết hợp như thế nào

- RAG văn bản bổ sung tri thức ngoài tham số cho mô hình sinh.
- KG bổ sung entity, relation, đường đi nhiều bước và provenance có cấu trúc.
- Luồng kết hợp: truy vấn → nhận dạng entity/ý định → truy hồi văn bản và subgraph → hợp nhất/rerank → sinh hoặc trích xuất câu trả lời có dẫn nguồn.

#### 5.1.2. Vai trò và ý nghĩa của KB, KG và RAG

- cập nhật tri thức mà không huấn luyện lại toàn bộ mô hình;
- tăng khả năng kiểm chứng và truy vết;
- hỗ trợ câu hỏi cần liên kết nhiều tài liệu;
- giới hạn: lỗi truy hồi, lỗi entity linking, tri thức lỗi thời và hallucination vẫn có thể xảy ra.

### 5.2. Knowledge Base và Knowledge Graph

#### 5.2.1. Khái niệm KB, KG, ontology, entity, relation và triple

#### 5.2.2. Mô hình dữ liệu, schema và provenance

#### 5.2.3. Xây dựng hai domain graph có thể tái lập

- graph y khoa từ metadata MedQuAD, UMLS CUI/semantic type sẵn có và entity Wikidata được xác minh;
- graph tài chính từ company/report/table/metric/reasoning program của FinQA và entity Wikidata;
- xuất JSONL/CSV/GraphML và manifest; không phụ thuộc Neo4j để chạy tối thiểu.

### 5.3. Retrieval-Augmented Generation

#### 5.3.1. Ingestion, chunking, embedding và indexing

#### 5.3.2. Sparse, dense, hybrid retrieval và reranking

#### 5.3.3. Graph-guided retrieval và hợp nhất bằng chứng

#### 5.3.4. Sinh/trích xuất câu trả lời có citation, từ chối khi thiếu bằng chứng

#### 5.3.5. Giao thức đánh giá và các baseline

### 5.4. KB và RAG cho bệnh tiểu đường

#### 5.4.1. MedQuAD và lát cắt diabetes

#### 5.4.2. Schema/graph y khoa và pipeline truy hồi

#### 5.4.3. Kết quả, ablation, ví dụ đúng/sai và giới hạn an toàn

### 5.5. KB và RAG cho tài chính/chứng khoán

#### 5.5.1. FinQA và báo cáo tài chính doanh nghiệp

#### 5.5.2. Schema/graph company–report–metric và reasoning program

#### 5.5.3. Kết quả, ablation, ví dụ đúng/sai và giới hạn

Phần “chứng khoán” được hiểu là hỏi đáp trên báo cáo tài chính của công ty niêm yết, **không** biến thành bài toán đoán giá cổ phiếu. Đây là bài toán phù hợp hơn với KB/RAG, có gold evidence và gold reasoning program để đánh giá.

### 5.6. Deploy với Agent

#### 5.6.1. Agent router và các tool

- `search_medical_corpus`;
- `search_financial_corpus`;
- `lookup_knowledge_graph`;
- `answer_with_citations`;
- `refuse_or_clarify` khi câu hỏi ngoài phạm vi hoặc thiếu bằng chứng.

#### 5.6.2. Backend Python, React UI, kiểm thử và giới hạn vận hành

### 5.7. Tiểu kết chương

Mục 5.7 được bổ sung để đóng chương; không thay đổi các nội dung bắt buộc 5.1–5.6 từ ảnh sau khi hiệu chỉnh số chương theo yêu cầu mới nhất của người dùng.

## 3. Dataset đã chọn

Chương 5 dùng đúng **3 nguồn dữ liệu thật**, trong đó hai nguồn là corpus/benchmark QA và một nguồn là KG mở. Số lượng sau lọc, kích cỡ byte và phân bố chỉ được chốt sau khi Phase 11 tải và đo trực tiếp.

| ID mới | Dataset | Vai trò | Thông tin chính đã xác minh | Lý do phù hợp |
|---|---|---|---|---|
| `ch5_medquad_diabetes` | MedQuAD | Corpus + QA benchmark y khoa | 47.457 cặp QA từ 12 website NIH, 37 loại câu hỏi, có question focus/CUI/semantic type; CC BY 4.0 | Có nguồn y khoa đáng tin cậy, metadata thực thể tốt cho KG và đủ câu hỏi để tạo lát cắt diabetes |
| `ch5_finqa` | FinQA | Corpus + QA benchmark tài chính | khoảng 2,8 nghìn báo cáo và hơn 8 nghìn QA; gồm text, bảng, supporting facts và gold reasoning program; repository MIT | Phù hợp hỏi đáp báo cáo tài chính, kiểm tra truy hồi lẫn suy luận số có giải thích |
| `ch5_wikidata_subgraphs` | Wikidata domain snapshots | KG nền cho hai domain | structured data CC0; lấy entity/relation hẹp qua API/WDQS, lưu revision và snapshot | Cung cấp QID, alias và quan hệ chuẩn hóa; tránh tải dump toàn bộ rất lớn |

Nguồn chính thức đã khóa:

- MedQuAD: <https://github.com/abachaa/MedQuAD>
- FinQA: <https://github.com/czyssrs/FinQA> và paper tại <https://aclanthology.org/2021.emnlp-main.300/>
- Wikidata data access: <https://www.wikidata.org/wiki/Wikidata:Data_access>
- RAG gốc: <https://arxiv.org/abs/2005.11401>
- Microsoft GraphRAG (nguồn tham khảo, không bắt buộc dùng package): <https://microsoft.github.io/graphrag/>

Quy tắc dataset:

- Không dùng mirror nếu nguồn chính thức còn truy cập được.
- Ghim commit SHA/tag khi clone hoặc tải repository.
- Raw data là chỉ đọc; dữ liệu lọc/chunk/split nằm trong `term_paper/knowledge_rag/data/processed/`.
- Với MedQuAD, không tự crawl lại ba subset đã bị gỡ câu trả lời vì lý do bản quyền.
- MedQuAD diabetes subset được lọc bằng rule công khai, sau đó audit mẫu thủ công; lưu cả included/excluded reason.
- FinQA giữ official split. Không cho cùng report rò rỉ giữa train/dev/test ngoài thiết kế chính thức.
- Wikidata chỉ lấy subgraph hẹp từ seed entity đã xác minh; lưu query, timestamp, revision ID và response hash.
- Báo cáo phải có link, license, kích cỡ file, số mẫu, mẫu input/output, phân bố và nhận xét cho cả ba nguồn.

## 4. Câu hỏi nghiên cứu và giả thuyết

| ID | Câu hỏi nghiên cứu | Cách trả lời |
|---|---|---|
| RQ5.1 | KG bổ sung gì cho RAG văn bản trong hai domain? | So sánh baseline retrieval với graph-guided/hybrid retrieval trên cùng query và corpus |
| RQ5.2 | Phương pháp nào truy hồi đúng bằng chứng nhất? | Recall@k, MRR@10, nDCG@10, evidence precision/recall |
| RQ5.3 | Bằng chứng tốt hơn có cải thiện câu trả lời cuối không? | EM/token-F1 hoặc answer accuracy; FinQA execution/program accuracy khi áp dụng được; citation correctness |
| RQ5.4 | Hệ thống xử lý câu hỏi ngoài phạm vi và thiếu bằng chứng ra sao? | Bộ OOD/adversarial nhỏ, abstention rate, unsupported-claim rate và case analysis |
| RQ5.5 | Có thể deploy Agent nhẹ, có citation trên Render không? | API/UI/E2E test, p50/p95 latency, memory/index size và cold-start smoke test |

Giả thuyết không được viết thành kết luận trước khi chạy thử nghiệm:

- hybrid sparse+dense thường tăng recall so với từng retriever riêng;
- graph expansion có thể giúp câu hỏi multi-hop nhưng có thể làm giảm precision nếu entity linking sai;
- citation và cơ chế từ chối giúp kiểm soát rủi ro nhưng không bảo đảm câu trả lời đúng.

## 5. Hệ thống so sánh và giao thức đánh giá

### 5.1. Các cấu hình bắt buộc

| Mã | Cấu hình | Mục đích |
|---|---|---|
| B0 | BM25/sparse retrieval | Baseline lexical, nhẹ và giải thích được |
| B1 | Dense retrieval | Đo lợi ích semantic matching |
| B2 | Hybrid sparse+dense fusion | Đo lợi ích kết hợp hai tín hiệu |
| B3 | KG-only / entity-neighborhood retrieval | Đo khả năng của cấu trúc graph |
| B4 | Hybrid KG–RAG | Hệ thống đề xuất: hybrid text retrieval + entity linking + graph expansion/rerank |

Nếu tài nguyên không cho phép embedding model lớn, Phase 10 chọn model nhẹ hơn nhưng phải giữ nguyên năm cấu hình logic. Không thay metric hoặc test set sau khi xem kết quả TEST.

### 5.2. Lớp trả lời

- Bắt buộc có chế độ **extractive/grounded** chạy offline: chọn evidence, tạo câu trả lời ngắn có citation và từ chối nếu score dưới threshold.
- Adapter mô hình sinh local hoặc API là tùy chọn; nếu dùng phải ghi model/version, prompt, decoding, chi phí/quota và seed khi có.
- Kết quả retriever và generator được báo cáo tách biệt để không quy mọi lỗi cho LLM.
- FinQA cần bộ xử lý phép toán an toàn từ gold/predicted reasoning program; không dùng `eval` tùy ý.

### 5.3. Metric bắt buộc

- Retrieval: Recall@1/5/10, MRR@10, nDCG@10 và evidence precision/recall.
- Answer: Exact Match, token-F1/answer accuracy; FinQA thêm execution accuracy và program accuracy nếu pipeline tạo program.
- Grounding: citation precision, citation recall, evidence coverage, unsupported-claim rate.
- Safety: abstention rate trên câu hỏi OOD/thiếu bằng chứng; false-answer rate sau khi nên từ chối.
- Vận hành: index size, build time, p50/p95 latency và peak memory nếu đo ổn định được.
- Báo cáo mean và 95% bootstrap CI trên query test khi hợp lý; tuyệt đối không tạo “ba seed” giả cho retrieval deterministic.

### 5.4. Fairness và chống leakage

- Cùng corpus snapshot, query set, top-k và evaluation script cho B0–B4.
- Mọi tuning threshold/weight chỉ dùng TRAIN/DEV; TEST chạy một lần sau khi khóa config.
- MedQuAD split theo group của question focus/entity để giảm near-duplicate leakage; lưu ID manifest.
- FinQA giữ official split và gold supporting facts chỉ dùng làm label đánh giá, không chèn vào index theo cách làm lộ đáp án.
- Mỗi prediction row phải có `query_id`, `system_id`, retrieved IDs/scores, answer, citations, latency và config hash.

## 6. Kiến trúc code và artifact đích

```text
term_paper/
├── knowledge_rag/
│   ├── README.md
│   ├── config/
│   │   ├── data_sources.yaml
│   │   ├── preprocessing.yaml
│   │   ├── graph_schema.yaml
│   │   └── experiments.yaml
│   ├── data/
│   │   ├── raw/                 # dữ liệu tải về, không chỉnh sửa
│   │   ├── interim/
│   │   └── processed/
│   ├── src/
│   │   ├── acquisition/
│   │   ├── preprocessing/
│   │   ├── graph/
│   │   ├── retrieval/
│   │   ├── generation/
│   │   ├── evaluation/
│   │   └── agent/
│   ├── tests/
│   ├── notebooks/
│   │   └── ch5_knowledge_rag_experiments.ipynb
│   └── artifacts/
│       ├── manifests/
│       ├── indexes/
│       ├── graphs/
│       ├── predictions/
│       ├── metrics/
│       └── figures/
├── report/
│   ├── sections/04_rnn.md
│   ├── sections/05_knowledge_rag.md
│   └── Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx
├── sources/dataset_cards/
└── tools/
```

Không bắt buộc tạo toàn bộ cây thư mục ở Phase 10. Chỉ tạo khi phase cần đến. Neo4j có thể được hỗ trợ dưới dạng export/demo, nhưng NetworkX/adjacency index hoặc cấu trúc Python tương đương phải đủ để test và deploy mà không cần dịch vụ ngoài.

## 7. Ngân sách nội dung sau mở rộng

| Phần | Mục tiêu |
|---|---:|
| Front matter | 8–10 trang, cập nhật TOC/danh mục |
| Mở đầu | 3–4 trang |
| Chương 1 | 8 trang |
| Chương 2 | 10–15 trang, gồm mục deploy ngắn |
| Chương 3 | 10–15 trang, gồm mục deploy ngắn |
| Chương 4 — RNN | 10–15 trang, gồm mục deploy ngắn |
| **Chương 5 — Knowledge & RAG** | **12–15 trang** |
| Kết luận + tài liệu tham khảo | 5–7 trang |
| Tổng dự kiến | khoảng 82–90 trang trước phụ lục, chốt bằng Word pagination |

Ngân sách Chương 5:

- 5.1: 1–1,5 trang;
- 5.2: 2–2,5 trang;
- 5.3: 2,5–3 trang;
- 5.4: 2,5–3 trang;
- 5.5: 2,5–3 trang;
- 5.6: 1–1,5 trang;
- 5.7: 0,5 trang.

Tối đa mục tiêu cho Chương 5 là 6 hình và 5 bảng. Hình/bảng mở rộng chuyển sang phụ lục hoặc artifact, không nhồi dày trang.

## 8. Kế hoạch phân bổ lại deployment

Nguồn hiện có `report/sections/05_trien_khai.md` phải được map trước khi xóa khỏi manuscript:

| Nội dung cũ | Vị trí mới |
|---|---|
| kiến trúc input → validate → preprocess → model → response | rút gọn ở phần phương pháp chung và nhắc tại từng mục deploy |
| provenance/model hash | bảng/nguyên tắc chung ở Mở đầu hoặc phụ lục; mỗi chương nêu artifact riêng |
| diabetes form/cảnh báo y khoa | cuối Chương 2 |
| EuroSAT upload/top classes | cuối Chương 3 |
| customer/AAPL sequence và cảnh báo tài chính | cuối Chương 4 |
| Agent KG–RAG/citation/refusal | mục 5.6 Chương 5 |
| health check, invalid input, local/Docker/Render | rút gọn ở mỗi mục deploy; hướng dẫn dài để ở phụ lục/README |
| hạn chế deployment | đưa về tiểu kết/hạn chế từng chương |

Không được xóa section cũ trước khi verifier xác nhận mọi đoạn/bảng/hình cần giữ đã có đích mới.

## 9. Quan hệ với yêu cầu scratch/Keras/PyTorch

Yêu cầu scratch/Keras/PyTorch vẫn được đáp ứng bởi:

- Chương 2: MLP;
- Chương 3: CNN;
- Chương 4: RNN, giữ nguyên nội dung, code, artifact và numbering hiện có.

Chương 5 Knowledge & RAG không giả tạo ba implementation Keras/PyTorch vì đây không phải phép so sánh framework neural network tương đương. Thay vào đó, chương này so sánh B0–B4 trên cùng hai benchmark QA, có ablation và metric retrieval/generation. Phase 18 phải cập nhật requirement matrix để chỉ rõ yêu cầu scratch/Keras/PyTorch vẫn được đáp ứng nguyên vẹn ở Chương 2–4, còn Chương 5 dùng giao thức so sánh retrieval/GraphRAG phù hợp với nội dung mới.

## 10. Bảng trạng thái Phase 10–19

| Phase | Tên | Dependency | Status |
|---:|---|---|---|
| 10 | Khóa baseline, audit môi trường và migration map | Phase 0–9 COMPLETE | `COMPLETE` |
| 11 | Thu nhận và kiểm định 3 dataset | 10 | `COMPLETE` |
| 12 | Tiền xử lý, split và bộ đánh giá | 11 | `COMPLETE` |
| 13 | Xây dựng KB/KG cho hai domain | 12 | `COMPLETE` |
| 14 | Xây dựng RAG baseline B0–B2 | 12 | `COMPLETE` |
| 15 | KG–RAG B3–B4, chạy thực nghiệm và phân tích | 13, 14 | `COMPLETE` |
| 16 | Agent, backend Python, React UI và deploy nhẹ | 15 | `COMPLETE` |
| 17 | Viết hoàn chỉnh Chương 5 | 15, 16 | `COMPLETE` |
| 18 | Tái cấu trúc toàn tiểu luận và phân bổ deployment | 17 | `COMPLETE` |
| 19 | Dựng DOCX, render, QA và phát hành | 18 | `COMPLETE` |

## 11. Chi tiết từng phase

# PHASE 10 — KHÓA BASELINE, AUDIT MÔI TRƯỜNG VÀ MIGRATION MAP

## Mục tiêu

Bảo toàn release hiện tại, đo chính xác trạng thái repo và khóa thiết kế kỹ thuật trước khi tải dữ liệu.

## Công việc bắt buộc

1. Hash DOCX 73 trang, manuscript, các section, build/validation scripts và deployment hiện tại.
2. Lập inventory liên quan: dung lượng đĩa, Python env/package, Node, Render config, model/index khả thi trên CPU/RAM.
3. Audit `backend/`, `web/`, `term_paper/deployment/`, `neo4j_scripts/` để xác định phần tái sử dụng.
4. Lập migration map từng heading/figure/table từ cấu trúc cũ sang mới.
5. Khóa naming: Chương 4 RNN giữ nguyên; Chương 5 KG/RAG; không có phần deploy riêng.
6. Khóa model embedding/generator tối thiểu sau benchmark smoke nhỏ; ưu tiên multilingual query nhưng corpus tiếng Anh.
7. Tạo verifier Phase 10 và baseline manifest.

## Deliverables

- `term_paper/knowledge_rag/README.md`
- `term_paper/knowledge_rag/artifacts/manifests/phase10_baseline.json`
- `term_paper/knowledge_rag/artifacts/manifests/environment_audit.json`
- `term_paper/knowledge_rag/artifacts/manifests/report_migration_map.csv`
- `term_paper/tools/verify_phase10.py` hoặc `.ps1`

## Acceptance criteria

- Hash baseline đầy đủ và tái kiểm tra được.
- Chưa sửa/ghi đè DOCX release cũ.
- Migration map không làm mất heading, figure, table hoặc deployment use case hiện có.
- Model/tool lựa chọn có lý do về chất lượng, license, kích cỡ và khả năng chạy CPU/Render.
- Verifier PASS; Phase 11 chuyển `READY`.

---

# PHASE 11 — THU NHẬN VÀ KIỂM ĐỊNH 3 DATASET

## Mục tiêu

Tải snapshot thật từ nguồn chính thức, khóa license/provenance và tạo dataset card dựa trên số đo local.

## Công việc bắt buộc

1. Tải/clone MedQuAD và FinQA; lưu source URL, commit SHA, accessed time và SHA-256.
2. Tạo truy vấn Wikidata có phạm vi hẹp, User-Agent đúng chính sách, retry/backoff và cache.
3. Đo physical/logical size từ dữ liệu local, không sao chép số marketing khi có thể tự đếm.
4. Audit schema, missing/duplicate, ngôn ngữ, loại câu hỏi, report/table/program distribution.
5. Xác minh license và citation từ nguồn chính thức.
6. Tạo ba dataset card và thêm ba row mới vào registry với chapter mới.
7. Lưu mẫu input/output đã khử dữ liệu không cần thiết và hình phân bố sơ bộ.

## Deliverables

- raw snapshots/cache trong `term_paper/knowledge_rag/data/raw/`
- `raw_manifest.csv` và hash manifest
- ba dataset card mới trong `term_paper/sources/dataset_cards/`
- registry/bibliography entries mới
- báo cáo audit dữ liệu

## Acceptance criteria

- 3/3 nguồn có URL chính thức, license status, snapshot/commit/revision và hash.
- Các con số row/report/QA/entity được đo bằng script và khớp card.
- Không crawl lại nội dung MedQuAD bị gỡ.
- Không dùng full Wikidata dump.
- Raw data bất biến sau khi hash; verifier PASS.

---

# PHASE 12 — TIỀN XỬ LÝ, SPLIT VÀ BỘ ĐÁNH GIÁ

## Mục tiêu

Tạo corpus/chunk/query/gold-evidence thống nhất để mọi hệ B0–B4 so sánh công bằng.

## Công việc bắt buộc

1. Parse XML MedQuAD và JSON FinQA bằng schema rõ ràng.
2. Xây rule/filter diabetes, lưu reason cho từng record và audit mẫu thủ công.
3. Chuẩn hóa document/chunk ID ổn định; giữ mapping về source URL/report/table row.
4. Giữ official FinQA split; tạo MedQuAD grouped split deterministic, seed 42.
5. Tạo query set, gold document/evidence và OOD/adversarial set nhỏ.
6. Khóa chunking/tokenization/top-k/evaluation contract trước khi chạy TEST.
7. Viết unit tests cho parser, duplicate handling, split leakage và metric toy cases.

## Deliverables

- processed corpus/query/evidence/split files
- `preprocessing_manifest.json`
- `evaluation_contract.md`
- config Phase 12
- tests và verifier

## Acceptance criteria

- Mỗi query có ID, domain, split và gold evidence/answer khi nguồn có.
- Không giao nhau group/entity/report trái contract giữa split.
- Mọi chunk truy ngược được về raw source và hash.
- Rule diabetes có precision audit chấp nhận được và false inclusion được ghi nhận.
- Unit tests/verifier PASS; TEST vẫn chưa dùng để tuning.

---

# PHASE 13 — XÂY DỰNG KB/KG CHO HAI DOMAIN

## Mục tiêu

Tạo hai graph có schema, provenance và kiểm tra chất lượng, đủ cho graph retrieval nhưng không phụ thuộc dịch vụ ngoài.

## Công việc bắt buộc

1. Khóa schema node/edge cho medical và finance.
2. Tạo entity từ metadata/gold structure trước; extraction heuristic phải deterministic.
3. Link entity sang Wikidata bằng candidate + validation; không tự nhận match mơ hồ.
4. Lưu provenance trên mỗi node/edge: source record, extractor version, confidence.
5. Xuất node/edge CSV hoặc JSONL và GraphML; tạo adjacency index chạy local.
6. Đo node/edge/type/degree/component/entity-link coverage và duplicate rate.
7. Tạo hình schema và subgraph mẫu; viết tests cho graph invariants và đường đi mẫu.

## Deliverables

- medical/finance graph artifacts
- graph schema/config
- entity-link audit
- graph statistics CSV/JSON và figures
- tests/verifier

## Acceptance criteria

- 100% node/edge có ID ổn định và provenance.
- Không có dangling edge; schema validation PASS.
- Wikidata link mơ hồ được để unresolved, không ép match.
- Graph có thể load/query mà không cần Neo4j.
- Các thống kê và hình đều sinh lại được từ artifact.

---

# PHASE 14 — XÂY DỰNG RAG BASELINE B0–B2

## Mục tiêu

Triển khai sparse, dense và hybrid retrieval trên cùng corpus/split, kèm answer layer grounded tối thiểu.

## Công việc bắt buộc

1. B0 BM25 hoặc sparse tương đương; B1 dense; B2 fusion có weight tune trên DEV.
2. Cache embedding/index với model/config/hash.
3. Triển khai answer layer extractive/grounded có citation và threshold từ chối.
4. Chạy smoke trên TRAIN/DEV; khóa config trước TEST.
5. Đánh giá retrieval/answer/latency trên hai domain; lưu prediction row-level.
6. Tạo notebook có thể execute và tests cho deterministic ranking, citation mapping, cache invalidation.

## Deliverables

- source modules retrieval/generation/evaluation
- indexes và manifests
- predictions/metrics B0–B2
- notebook draft và figures baseline
- tests/verifier

## Acceptance criteria

- Cùng query/corpus/top-k cho B0–B2.
- Prediction đầy đủ provenance và config hash.
- Metric tái tính được hoàn toàn từ prediction.
- Answer không có citation giả; thiếu evidence phải từ chối.
- Tests/notebook/verifier PASS.

---

# PHASE 15 — KG–RAG B3–B4, THỰC NGHIỆM VÀ PHÂN TÍCH

## Mục tiêu

Hoàn thiện graph retrieval/hybrid KG–RAG, chạy so sánh B0–B4 và tạo toàn bộ bằng chứng cho Chương 5.

## Công việc bắt buộc

1. B3 entity-neighborhood/subgraph retrieval.
2. B4 hợp nhất sparse+dense với graph expansion/rerank.
3. Khóa hyperparameter bằng DEV; chạy TEST một lần theo manifest.
4. Tính metric bắt buộc, bootstrap CI khi phù hợp và operational metrics.
5. Chạy ablation: bỏ graph, bỏ dense, bỏ sparse, giới hạn hop/top-k.
6. Phân tích error theo entity linking, retrieval miss, numerical reasoning, unsupported answer và OOD.
7. So sánh riêng medical và finance; không gộp thành một score gây hiểu sai.
8. Hoàn thiện notebook execute, tables, figures, case-study traces và verifier.

## Deliverables

- predictions/metrics B3–B4 và bảng B0–B4
- ablation/error-analysis artifacts
- notebook hoàn chỉnh
- 4–6 figures và bảng Word-ready
- test coverage/verifier report

## Acceptance criteria

- Mọi metric truy ngược được tới prediction/query/evidence.
- Không thay config sau khi xem TEST nếu không version thành experiment mới và giải thích.
- Có cả trường hợp KG giúp, không giúp và làm xấu kết quả nếu thực tế xảy ra.
- Không tuyên bố “giảm hallucination” nếu không đo grounding/unsupported claims.
- Notebook chạy lại không lỗi; verifier PASS.

---

# PHASE 16 — AGENT, BACKEND PYTHON, REACT UI VÀ DEPLOY NHẸ

## Mục tiêu

Tích hợp một Agent KG–RAG thực tế vào `backend/` và `web/`, chạy local và phù hợp Render CPU.

## Công việc bắt buộc

1. Thiết kế Agent router có tool allow-list; không thực thi code tùy ý từ input.
2. Thêm API chat/query có response schema: answer, domain, citations, evidence, route, abstained, latency, artifact version.
3. Lazy-load index; hash-check artifact; health/readiness endpoint.
4. Thêm React page theo style hiện tại: chat, domain badge, citation/evidence drawer, graph path nhỏ và cảnh báo.
5. Xử lý input length, timeout, rate limit, CORS và lỗi an toàn.
6. Unit/integration/E2E test cho medical, finance, OOD, prompt-injection-like input và missing artifact.
7. Cập nhật `render.yaml`, requirements và tài liệu deploy nếu kích cỡ/cold start cho phép.
8. Chụp tối đa 1–2 ảnh UI dùng trong mục 5.6.

## Deliverables

- backend Agent/API và tests
- React UI và tests
- deployment manifests/config
- screenshot + smoke-test logs
- nội dung bằng chứng cho 5.6

## Acceptance criteria

- App chạy không cần API key và trả citation tới corpus thật.
- Agent chỉ gọi tool được khai báo; không lộ path/secret/prompt nội bộ.
- Không đưa chẩn đoán y khoa hoặc khuyến nghị đầu tư.
- Local E2E PASS; Render build/start được mô phỏng hoặc deploy thật nếu người dùng đã kết nối.
- Existing ML/CNN/RNN UI không bị regression.

---

# PHASE 17 — VIẾT HOÀN CHỈNH CHƯƠNG 5

## Mục tiêu

Viết `05_knowledge_rag.md` 12–15 trang theo đúng dàn ý 5.1–5.7, chỉ dùng kết quả thật.

## Công việc bắt buộc

1. Viết lý thuyết KB/KG/RAG, công thức/thuật toán vừa đủ và trích nguồn gốc/primary.
2. Trình bày ba dataset: link, license, kích cỡ, mẫu, phân bố, nhận xét.
3. Mô tả B0–B4, split, leakage control, metric và giới hạn.
4. Viết riêng case diabetes và finance, có bảng kết quả, error cases và safety.
5. Viết mục 5.6 Agent ngắn 1–1,5 trang; chi tiết vận hành để README/phụ lục.
6. Thêm source/provenance cho mọi figure/table và cross-reference trong nội dung.
7. Kiểm tra thuật ngữ KB/KG/RAG/GraphRAG/Agent thống nhất.

## Deliverables

- `term_paper/report/sections/05_knowledge_rag.md`
- assets Chương 5 đóng gói trong `report/assets/ch5_knowledge_rag/`
- bibliography/source registry cập nhật
- content verifier Phase 17

## Acceptance criteria

- Có đủ mục 5.1–5.7 và đúng 12–15 trang ước tính trước khi dựng Word.
- 3 dataset đủ link/size/sample/distribution/comment/license status.
- Không có metric/hình/bảng không truy vết được.
- Không có tuyên bố y khoa/tài chính vượt bằng chứng.
- Citation keys không thiếu/orphan; verifier PASS.

---

# PHASE 18 — TÁI CẤU TRÚC TOÀN TIỂU LUẬN VÀ PHÂN BỔ DEPLOYMENT

## Mục tiêu

Hợp nhất Chương 5 mới vào manuscript sau Chương 4 RNN và loại bỏ phần deploy độc lập mà không mất nội dung cần thiết.

## Công việc bắt buộc

1. Giữ `04_rnn.md` là Chương 4, giữ nguyên heading/caption/cross-reference/artifact label hiện có và chỉ bổ sung mục deploy ngắn ở cuối chương.
2. Chèn mục deploy ngắn vào cuối Chương 2, 3, 4, 5 theo mapping Mục 8.
3. Xóa phần deployment độc lập khỏi manuscript chỉ sau khi migration verifier PASS.
4. Cập nhật tóm tắt, từ khóa, Mở đầu, câu hỏi nghiên cứu, cấu trúc bài, kết luận và hạn chế.
5. Cập nhật title, running header, terminology, outline, requirements matrix, source registry, report manifest và bibliography.
6. Sửa build/verify scripts để không hard-code 73 trang, 125 heading hoặc numbering cũ.
7. Build `manuscript.md` mới và kiểm tra citation/caption/page-estimate/hash.

## Deliverables

- section Chương 2/3/4/5 đã tích hợp deploy
- manuscript/references/manifest mới
- outline và requirements matrix phiên bản 2
- migration/renumber verifier

## Acceptance criteria

- Thứ tự: Mở đầu → Ch1 → Ch2 → Ch3 → Ch4 RNN → Ch5 KG/RAG → Kết luận → Tài liệu tham khảo.
- Không còn Heading 1 “Phần triển khai/Deployment”.
- Mỗi Chương 2–5 có một mục deploy ngắn.
- Không cross-reference/caption/citation bị gãy hoặc trùng số.
- Requirement framework vẫn trỏ đúng Ch2, Ch3, Ch4; requirement KG/RAG trỏ Ch5.
- Baseline DOCX cũ không thay đổi hash; verifier PASS.

---

# PHASE 19 — DỰNG DOCX, RENDER, QA VÀ PHÁT HÀNH

## Mục tiêu

Dựng bản DOCX mở rộng, kiểm tra 100% trang và phát hành artifact cuối mới mà vẫn giữ baseline cũ.

## Công việc bắt buộc

1. Dựng `Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx` từ manuscript mới.
2. Paginate bằng Word, cập nhật TOC/list of figures/list of tables và page map.
3. Render bằng quy trình documents hiện hành; kiểm tra trực quan mọi trang qua ảnh/contact sheet và trang chi tiết khi cần.
4. Sửa clipping, bảng vỡ, caption orphan, trang trắng, hyperlink, font/glyph và mật độ trang.
5. Chạy structural, accessibility, link/citation, metric-artifact, metadata và security/path audit.
6. Chạy regression tests code Ch2–5 và backend/web quan trọng.
7. Đối chiếu requirement matrix; chỉ release khi mọi mục satisfied hoặc documented exception được chấp nhận.

## Deliverables

- `term_paper/report/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`
- build/validation/release logs
- page renders/contact sheets nội bộ
- final release manifest với SHA-256

## Acceptance criteria

- 100% trang được kiểm tra trực quan.
- Chương 5 nằm trong 12–15 trang; Mở đầu và Ch1–3/Ch4 vẫn trong budget yêu cầu.
- TOC, danh mục hình/bảng và mọi internal hyperlink đúng trang.
- Mọi metric Chương 5 khớp artifact; mọi citation có reference.
- Không còn standalone deployment chapter.
- Không có accessibility high; finding medium phải được sửa hoặc giải thích hợp lệ.
- Baseline DOCX vẫn tồn tại và giữ nguyên hash.
- Final verifier PASS và file mới là artifact được giao.

## 12. Rủi ro và phương án xử lý

| Rủi ro | Cách xử lý đã khóa |
|---|---|
| MedQuAD diabetes subset quá nhỏ/lệch | báo số thực; mở rộng rule theo CUI/focus có audit, không trộn dataset y khoa không rõ nguồn |
| Wikidata API/WDQS chậm hoặc 429 | query hẹp, cache, User-Agent, retry/backoff; dùng revision đã lưu thay vì gọi mỗi lần chạy |
| Dense model quá lớn cho Render | precompute index; chọn model nhẹ ở Phase 10; deploy extractive grounded mode |
| FinQA cần suy luận số phức tạp | tách retrieval accuracy khỏi execution/program accuracy; dùng calculator tool an toàn |
| KG expansion giảm precision | ablation hop/top-k; report kết quả âm; dùng confidence và unresolved state |
| RAG sinh citation sai | citation chỉ lấy từ retrieved IDs; validator kiểm tra ID tồn tại; từ chối khi không đủ evidence |
| Renumber làm gãy report | migration map + automated heading/caption/cross-reference verifier trước DOCX |
| DOCX tăng quá dài | giữ Ch4 12–15 trang, deployment mỗi chương ngắn, chi tiết code/ops sang phụ lục/README |

## 13. Definition of Done cho đợt mở rộng

Đợt mở rộng chỉ hoàn thành khi:

- Chương 5 Knowledge & RAG có đủ mục 5.1–5.7 và 12–15 trang thực tế.
- MedQuAD, FinQA và Wikidata snapshots có provenance, license status, hash, size, sample, distribution và limitations.
- B0–B4 được đánh giá công bằng trên MedQuAD diabetes và FinQA; metric truy ngược tới prediction.
- Có KB/KG cho hai domain, schema/provenance rõ và load/query offline được.
- Agent backend Python + React UI chạy local, có citation/refusal/safety và không cần API key.
- RNN được bảo toàn nguyên vẹn ở Chương 4.
- Deployment chỉ xuất hiện ngắn ở cuối từng chương chính, không còn chương deployment riêng.
- Tóm tắt, Mở đầu, Kết luận, TOC, caption, citation và requirement matrix đồng bộ.
- DOCX mới đã render, kiểm tra 100% trang và vượt final verifier.
- DOCX baseline cũ vẫn nguyên vẹn.

## 14. Nhật ký thực thi

Mỗi phase phải thêm entry theo mẫu:

```markdown
### YYYY-MM-DD — Phase N — STATUS

- Phạm vi đã làm:
- File tạo/sửa:
- Dataset/model/source version:
- Lệnh/test đã chạy:
- Kết quả:
- Quyết định:
- Sai lệch so với plan:
- Việc còn lại/blocker:
```

### 2026-10-12 — Lập kế hoạch mở rộng — COMPLETE

- Phạm vi đã làm: Đọc cấu trúc tiểu luận và release hiện tại; diễn giải ảnh bảng; ban đầu lập phương án KG/RAG ở Chương 4, sau đó hiệu chỉnh theo yêu cầu mới nhất: giữ RNN là Chương 4, đặt Knowledge & RAG ở Chương 5 và phân bổ deployment vào cuối từng chương; chọn ba nguồn dữ liệu phù hợp; lập Phase 10–19.
- File tạo/sửa: kế hoạch active hiện tại `CHUONG_5_KNOWLEDGE_RAG_EXECUTION_PLAN.md`; thêm con trỏ active plan vào kế hoạch cũ và README workspace.
- Dataset/model/source version: Khóa nguồn chính thức MedQuAD, FinQA, Wikidata; phiên bản local/commit/revision sẽ được chốt ở Phase 11.
- Kết quả: Kế hoạch sẵn sàng; Phase 10 ở trạng thái `READY`.
- Quyết định: Dùng số phase nối tiếp để tránh xung đột lịch sử 0–9; giữ nguyên numbering/artifact RNN Chương 4; thêm KG/RAG thành Chương 5; không dùng chương deployment độc lập; không biến case tài chính thành dự báo giá cổ phiếu.
- Sai lệch so với plan: Không áp dụng.
- Việc còn lại/blocker: Không có blocker. Bắt đầu bằng lệnh `làm phase 10`.

### 2026-10-12 — Hiệu chỉnh thứ tự Chương 4–5 — COMPLETE

- Phạm vi đã làm: Sửa toàn bộ kế hoạch theo xác nhận mới nhất của người dùng: RNN giữ nguyên là Chương 4; Knowledge Base, Knowledge Graph và RAG là Chương 5.
- File tạo/sửa: đổi tên kế hoạch thành `CHUONG_5_KNOWLEDGE_RAG_EXECUTION_PLAN.md`; cập nhật con trỏ trong `TIEU_LUAN_AI_EXECUTION_PLAN.md` và `term_paper/README.md`.
- Dataset/model/source version: Đổi namespace dataset và câu hỏi nghiên cứu sang namespace Chương 5 (`ch5_*`, `RQ5.*`); lựa chọn nguồn dữ liệu không đổi.
- Lệnh/test đã chạy: scan toàn bộ tham chiếu chương, section, artifact, file DOCX và active-plan path; kiểm tra đủ Phase 10–19; `git diff --check`.
- Kết quả: Kế hoạch nhất quán với thứ tự Chương 4 RNN → Chương 5 Knowledge & RAG; Phase 10 vẫn `READY`.
- Quyết định: Không renumber code/artifact RNN hiện có; section mới dùng `05_knowledge_rag.md`; bản DOCX mới dùng hậu tố `CNN_RNN_KG_RAG` theo thứ tự chương.
- Sai lệch so với plan: Đây là hiệu chỉnh cấu trúc theo yêu cầu người dùng, thay thế quyết định ban đầu về việc đưa KG/RAG vào Chương 4.
- Việc còn lại/blocker: Không có blocker. Bắt đầu bằng lệnh `làm phase 10`.

### 2026-10-12 — Phase 10 — COMPLETE

- Phạm vi đã làm: Khóa hash release 73 trang, manuscript, section, report builder/verifier và deployment source; audit máy local, bốn Python environment, package, Render Free, `backend/`, `web/`, `term_paper/deployment/`, `neo4j_scripts/`; lập migration map từng heading/hình/bảng/use case; khóa stack CPU-only và chạy micro-smoke retrieval.
- File tạo/sửa: `term_paper/knowledge_rag/README.md`; `artifacts/manifests/phase10_baseline.json`; `environment_audit.json`; `report_migration_map.csv`; `phase10_verification.json`; `phase10_coverage.json`; `term_paper/tools/build_phase10_baseline.py`; `verify_phase10.py`; `term_paper/tests/test_phase10_verifier.py`; cập nhật kế hoạch này và `term_paper/README.md`.
- Dataset/model/source version: Chưa tải dataset ở Phase 10. Stack bắt buộc khóa ở `pure_python_bm25` + TF-IDF/TruncatedSVD LSA 128 chiều + adjacency index thuần Python + extractive grounded answer. `paraphrase-multilingual-MiniLM-L12-v2` chỉ là optional offline ablation, không phải Render default.
- Lệnh/test đã chạy: red test xác nhận module chưa tồn tại; 6/6 unit test PASS; build Phase 10; verifier 12/12 PASS; coverage unit+integration 93% (`build_phase10_baseline.py` 98%, `verify_phase10.py` 85%); `git diff --check` và scan tham chiếu/path.
- Kết quả: PASS — 82 baseline hash records; DOCX baseline 73 trang, 3.218.862 byte, SHA-256 `0c82a1e90d394420a7143534ca2b06ebc912648b1c9ea17dd58784d095ce1e9d`; 125 heading, 18 hình, 16 bảng và 8 nhóm deployment được phủ bởi 167 migration rows; BM25 và LSA micro-smoke cùng đạt 3/3 top-1.
- Quyết định: Giữ RNN nguyên vẹn ở Chương 4. Chương 5 mới dùng MedQuAD/FinQA/Wikidata ở phase sau. Render Free được thiết kế theo 0,1 CPU/512 MB RAM, peak process budget dưới 400 MiB và artifact budget dưới 192 MiB; không yêu cầu GPU, Neo4j server hoặc API key.
- Sai lệch so với plan: Node/npm không có trên PATH phiên audit, nhưng package-lock và bằng chứng build Phase 6 tồn tại nên không chặn Phase 10. Backend `.venv` có scikit-learn 1.9.0 trong khi requirements ghim 1.9.1; Phase 14 dùng environment 1.9.1 và Phase 16 phải đồng bộ trước E2E. Không tải transformer model để bảo toàn dung lượng đĩa còn khoảng 2,4 GB.
- Việc còn lại/blocker: Không có blocker. Phase 11 ở trạng thái `READY`.

### 2026-10-12 — Phase 11 — COMPLETE

- Phạm vi đã làm: Clone hai repo chính thức; thu 10 Wikidata entity bằng search API và `Special:EntityData` với User-Agent, cache, retry/backoff; parse/audit toàn bộ raw; khóa file-level hash; tạo ba dataset card, ba hình phân bố, registry và bibliography entries; kiểm tra chính sách bản quyền MedQuAD và phạm vi Wikidata.
- File tạo/sửa: `term_paper/knowledge_rag/data/raw/{medquad,finqa,wikidata}/`; `artifacts/manifests/{raw_manifest.csv,phase11_snapshot_manifest.json,phase11_verification.json,phase11_coverage.json}`; `artifacts/metrics/phase11_data_audit.{json,md}`; `artifacts/figures/phase11/`; `term_paper/sources/dataset_cards/ch5_*.md`; `term_paper/tools/{phase11_data.py,build_phase11_sources.py,verify_phase11.py}`; `term_paper/tests/test_phase11_acquisition.py`; registry, references và README.
- Dataset/model/source version: MedQuAD commit `577bd37b96c02d1833b2c9eed2de9f96964e96cb`, CC BY 4.0; FinQA commit `0f16e2867befa6840783e58be38c9efb9229d742`, MIT; Wikidata CC0 với 10 revision ID ghi trong snapshot manifest. Aggregate raw manifest SHA-256 `b7af4e6c5e5e8bc4bc4d09e8fad05df119ada7a1159438cc467bb1e678dafcb1`.
- Lệnh/test đã chạy: test đỏ do module Phase 11 chưa tồn tại; sau triển khai 8/8 unit/integration test PASS; coverage hai module parser/verifier 86%; builder acquisition/audit; verifier Phase 11 8/8 checks PASS; verifier Phase 10 12/12 checks PASS.
- Kết quả: MedQuAD đo local 11.274 XML/47.441 QA/16.407 answer; FinQA 8.281 public QA có program + 919 private-test; Wikidata 10 entity/785 property bucket/2.056 claim. Registry/card dùng số local, hash và snapshot cụ thể.
- Quyết định: Không crawl 31.034 MedQuAD answer rỗng; công khai chênh lệch 16 QA giữa README upstream và số đếm commit local; giữ official FinQA split; không dùng private test làm gold; Wikidata chỉ dùng narrow snapshot 5 medical + 5 finance, không dùng full dump. Xóa metadata `.git` lồng của hai clone sau khi lưu `source_snapshot.json` để tránh tạo embedded repository; raw content không bị xóa và có thể re-clone từ commit đã ghi.
- Sai lệch so với plan: FinQA local có 799 khóa company-year theo ID, không diễn giải thành số báo cáo pháp lý độc nhất. MedQuAD có 39 qtype quan sát được và 47.441 QA ở commit khóa, khác số 37/47.457 công bố trong README; báo cáo ưu tiên số đo tái lập.
- Việc còn lại/blocker: Không có blocker. Phase 12 ở trạng thái `READY`; raw đã khóa, không sửa tại chỗ.

### 2026-10-12 — Phase 12 — COMPLETE

- Phạm vi đã làm: Xây unified document/chunk/query/evidence schema; lọc và manual-audit MedQuAD diabetes; xử lý duplicate; tạo grouped split seed 42; giữ official FinQA split và map gold locator; tạo OOD/adversarial challenge set; khóa chunking, top-k, metric và quy tắc không tuning TEST; tạo manifest, tests và verifier quan hệ/provenance.
- File tạo/sửa: `term_paper/knowledge_rag/data/processed/phase12/*`; `config/{phase12.json,phase12_manual_reviews.json}`; `evaluation_contract.md`; `artifacts/manifests/{preprocessing_manifest.json,phase12_verification.json,phase12_coverage.json}`; `artifacts/metrics/phase12_*`; `term_paper/tools/{phase12_preprocessing.py,build_phase12_preprocessing.py,verify_phase12.py}`; `term_paper/tests/test_phase12_preprocessing.py`; cập nhật dataset cards MedQuAD/FinQA và README.
- Dataset/model/source version: Dùng nguyên snapshot Phase 11. Filter `diabetes-focus-question-v1`; MedQuAD split strategy `normalized-focus-group-hash`, seed 42, tỷ lệ 70/15/15; FinQA official train/dev/test/private-test. Chunk MedQuAD 120 words overlap 20; FinQA một chunk trên mỗi `text_i`/`table_i` theo upstream.
- Lệnh/test đã chạy: test đỏ khi module chưa tồn tại; test đỏ lần hai khi contract table locator chưa khớp upstream; test đỏ lần ba chứng minh verifier cũ chưa bắt dangling gold chunk; sau triển khai 10/10 Phase 12 tests PASS; coverage core parser/verifier 82%; builder chạy toàn corpus; verifier Phase 12 16/16 PASS.
- Kết quả: MedQuAD 274 candidate → 247 query sau 27 duplicate, split 152/33/62 và 762 chunk; manual audit 40 TP/0 FP/17 TN/3 FN, inclusion precision 1,000. FinQA 2.789 document/86.421 chunk/9.200 query/14.108 evidence; không thiếu locator, token mismatch 0. Tổng cộng 87.183 chunk, 14.870 evidence và 16 challenge query.
- Quyết định: Filter không dùng answer-only signal và loại diabetes insipidus; giữ ba false negative đã audit thay vì mở rộng rule sau khi nhìn dữ liệu. `text_-1` upstream được map tới post-text cuối. Private-test inference-only; public TEST `SEALED_NOT_USED_FOR_TUNING`. Mọi B0–B4 phải dùng cùng corpus, top-k 1/3/5/10 và evaluator.
- Sai lệch so với plan: Official FinQA public split không trùng page group nhưng company-year report key vẫn overlap train–validation 197, train–test 243, validation–test 93. Không remap vì mâu thuẫn yêu cầu giữ official split; limitation này được khóa trong evaluation contract. Có 328 khác biệt gold text ở spacing/punctuation nhưng token-level mismatch bằng 0.
- Việc còn lại/blocker: Không có blocker. Phase 13 ở trạng thái `READY`; TEST chưa được dùng cho tuning hoặc so sánh mô hình.

### 2026-10-13 — Phase 13 — COMPLETE

- Phạm vi đã làm: Khóa schema property graph cho medical và finance; dựng entity từ metadata/gold structure; trích khái niệm tài chính bằng exact lexicon; liên kết Wikidata theo candidate + exact validated alias; xuất JSONL, GraphML và adjacency index hai chiều; đo thống kê, tạo audit, schema figure và hai sample subgraph; viết test và verifier độc lập.
- File tạo/sửa: `term_paper/knowledge_rag/config/phase13.json`; `graph_schema.md`; `data/processed/phase13/{medical,finance}/`; `artifacts/metrics/phase13_*`; `artifacts/figures/phase13/`; `artifacts/manifests/phase13_graph_manifest.json`; `phase13_build_report.md`; `term_paper/tools/{phase13_graph.py,build_phase13_graphs.py,verify_phase13.py}`; `term_paper/tests/test_phase13_graph.py`; README và kế hoạch này.
- Dataset/model/source version: Dùng nguyên corpus Phase 12 và 10 Wikidata snapshot/revision Phase 11; extractor `phase13-deterministic-v1`; không gọi API ngoài, không dùng Neo4j, TEST vẫn `SEALED_NOT_USED_FOR_TUNING`.
- Lệnh/test đã chạy: test đỏ khi module Phase 13 chưa tồn tại; thêm regression đỏ để cấm gold-derived retrieval edge; sau triển khai 12/12 Phase 13 tests PASS; regression Phase 11–13 đạt 30/30; coverage core graph/verifier trên 80%; builder chạy toàn corpus; verifier độc lập PASS; build lần hai cho manifest SHA-256 trùng `8f23992aa9047fbda3122f3d3ed344cbea64bda1836a4342b5426f07c6c613c0`.
- Kết quả: Medical KG có 1.336 node/1.506 edge, 62 MedicalEntity, 3 exact Wikidata link; Finance KG có 99.355 node/97.809 edge, 137 company, 799 report, 86.421 chunk, 5 exact Wikidata link. Cả hai có provenance coverage 100%, duplicate rate 0, không dangling edge và không chứa gold-derived retrieval edge; entity-link audit có 203 dòng, 8 linked, 195 unresolved và 0 forced ambiguous link.
- Quyết định: Giữ toàn bộ title/focus MedQuAD thành local entity thay vì ép chúng về năm QID hẹp; chỉ tạo `SAME_AS` khi đúng một alias đã kiểm định khớp chính xác. Với finance, công ty lấy từ ticker/report ID, khái niệm lấy từ từ điển cố định; chỉ AAPL có alias công ty đã kiểm định trong snapshot hiện có. Gold document/chunk chỉ ở evaluation artifact Phase 12, không xuất thành cạnh graph; câu hỏi chỉ nối entity/concept suy ra từ chính nội dung câu hỏi. Graph runtime dùng adjacency `out`/`in` thuần JSON.
- Sai lệch so với plan: Không có sai lệch phạm vi. Entity-link coverage thấp có chủ ý (medical 4,84%; finance 3,55%) vì snapshot Phase 11 chỉ gồm 10 entity và chính sách không ép match; đây là đặc tính minh bạch, không phải lỗi schema.
- Việc còn lại/blocker: Không có blocker. Phase 14 ở trạng thái `READY`; Phase 16 phải đóng gói runtime subset dưới 192 MiB thay vì đưa toàn bộ GraphML phân tích 135,7 MB lên Render.

### 2026-10-13 — Phase 14 — COMPLETE

- Phạm vi đã làm: Triển khai B0 BM25, B1 TF-IDF + TruncatedSVD/LSA 128 chiều và B2 weighted reciprocal-rank fusion; xây cache index có corpus/config/file hash; tune B2 chỉ trên validation; khóa config trước TEST; thêm grounded extractive answer có citation, overlap threshold và guardrail; chạy validation, train smoke và challenge; xuất prediction row-level, metric, notebook execute, figures, tests và verifier.
- File tạo/sửa: `term_paper/knowledge_rag/config/{phase14.json,phase14_locked.json}`; `data/processed/phase14/indexes/`; `artifacts/predictions/phase14/`; `artifacts/metrics/phase14_*`; `artifacts/figures/phase14/`; `artifacts/manifests/{phase14_baseline_manifest.json,phase14_verification.json,phase14_coverage.json}`; `notebooks/ch5_rag_baselines_b0_b2.ipynb`; `phase14_build_report.md`; `term_paper/tools/{phase14_rag.py,build_phase14_baselines.py,verify_phase14.py}`; `term_paper/tests/test_phase14_rag.py`; README và kế hoạch này.
- Dataset/model/source version: Dùng đúng 762 medical chunks và 86.421 finance chunks Phase 12 cho cả B0–B2; scikit-learn local, không GPU/API/model download; B2 chọn sparse weight `0,75` trong tập ứng viên `0,25/0,5/0,75` theo macro-domain chunk Recall@5 validation. Locked config SHA-256 `ea5b3546a8e408648f5024d62bd0cb3584784ead2f594e126d2dea356240653d`; TEST `SEALED_NOT_RUN`.
- Lệnh/test đã chạy: test đỏ khi module Phase 14 chưa tồn tại; test đỏ cho dense batch; test đỏ cho document recall; test đỏ chứng minh verifier cũ chưa bắt metric drift/challenge failure; sau triển khai 13/13 Phase 14 tests PASS; regression Phase 11–14 đạt 43/43; coverage core retrieval/verifier 82%; builder full-corpus PASS; builder lần sau cache-hit cả medical/finance; verifier độc lập PASS và `git diff --check` không có whitespace error.
- Kết quả: Medical chunk Recall@5 B0/B1/B2 lần lượt `0,333/0,394/0,364`; finance `0,535/0,245/0,450`. Citation validity 100%; 16/16 challenge đều abstain cho cả ba model. Finance cache-hit p95 local khoảng 38,1/48,9/87,1 ms cho B0/B1/B2. Manifest SHA-256 `5720b14519918ad0d01a88a08081c145c3abb8066487c3e6815542f74167bf2e`.
- Quyết định: Chọn một B2 weight chung theo macro hai domain để tránh finance áp đảo vì nhiều query hơn. Không chạy TEST ở Phase 14. Không tuyên bố B2 tốt nhất: B1 tốt nhất medical Recall@5, còn B0 tốt nhất finance. FinQA program accuracy ghi `not applicable` vì B0–B2 không sinh program; normalized execution/exact match bằng 0 được giữ nguyên, không che giấu.
- Sai lệch so với plan: Không có sai lệch phạm vi. Grounded extractive answer đạt token F1 khoảng `0,207–0,217` trên medical nhưng gần 0 trên finance; đây là bằng chứng baseline chưa làm numerical reasoning và là đầu vào bắt buộc cho calculator/KG analysis ở Phase 15. Latency B1 được đo theo batch amortized, đã ghi rõ trong artifact.
- Việc còn lại/blocker: Không có blocker. Phase 15 ở trạng thái `READY`; phase này sẽ thêm B3/B4, calculator/graph expansion, chạy TEST đúng một lần theo locked manifest và phân tích ablation/error.

### 2026-10-13 — Phase 15 — COMPLETE

- Phạm vi đã làm: Triển khai B3 graph-neighborhood retrieval và B4 weighted RRF sparse+dense+graph; tune hop/trọng số chỉ trên validation; khóa cấu hình; chạy public TEST đúng một lần; đánh giá B0–B4 riêng medical/finance; thực hiện ablation, bootstrap CI, error analysis, OOD/adversarial challenge, case-study graph trace, notebook execute, sáu figure và verifier độc lập.
- File tạo/sửa: `term_paper/knowledge_rag/config/{phase15.json,phase15_locked.json}`; `artifacts/predictions/phase15/`; `artifacts/metrics/phase15_*`; `artifacts/figures/phase15/`; `artifacts/manifests/{phase15_validation_manifest.json,phase15_test_run.json,phase15_experiment_manifest.json,phase15_verification.json,phase15_coverage.json}`; `notebooks/ch5_kgrag_b0_b4.ipynb`; `phase15_experiment_report.md`; `term_paper/tools/{phase15_kgrag.py,build_phase15_experiments.py,verify_phase15.py}`; `term_paper/tests/test_phase15_kgrag.py`; README và kế hoạch này.
- Dataset/model/source version: Dùng đúng 762 medical chunks, 86.421 finance chunks và public TEST 62/1.147 query của Phase 12; private-test không được mở. B4 khóa 2-hop và trọng số sparse/dense/graph `0,6/0,1/0,3` theo macro-domain Recall@5 validation. Locked config SHA-256 `560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e`.
- Lệnh/test đã chạy: test đỏ cho OOD category và verifier giả-PASS; sau triển khai 11/11 Phase 15 tests PASS; regression Phase 11–15 đạt 53/53; coverage core retrieval/verifier 82%; validation/challenge builder PASS; public TEST one-shot PASS; verifier độc lập PASS với metric recomputation, query-set/hash/provenance/notebook/private-test checks; `git diff --check` được chạy ở bước kết thúc.
- Kết quả: TEST chunk Recall@5 medical B0/B1/B2/B3/B4 lần lượt `0,403/0,339/0,403/0,581/0,581`; finance `0,532/0,232/0,443/0,034/0,480`. B4 trừ B2 đạt `+0,177` (95% bootstrap CI `0,096–0,274`) ở medical và `+0,037` (`0,022–0,052`) ở finance. B4 vẫn thấp hơn BM25 B0 ở finance. Citation validity 100%; B3/B4 cùng abstain đúng 16/16 challenge, không phát citation. Manifest TEST ghi `run_count=1` và `COMPLETE`.
- Quyết định: Báo cáo hai domain riêng, không gộp theo số query. Gọi chênh lệch B4–B2 là hiệu ứng của toàn bộ cấu hình hybrid/fusion, không quy toàn bộ cho graph; ablation validation được dùng để tách ảnh hưởng. Không tuyên bố giảm hallucination; chỉ báo citation validity, unsupported-answer proxy và challenge refusal. FinQA program accuracy là `not applicable`; execution/exact match gần 0 phản ánh chưa có calculator/program generator ở mô hình Phase 15.
- Sai lệch so với plan: Không có sai lệch phạm vi. Medical không xuất hiện ca B4 làm xấu Recall@5 so với B2 trên TEST; finance có đủ ca giúp/làm xấu/trung tính. B3 graph-only rất yếu trên finance vì entity/concept coverage thấp đã được ghi nhận từ Phase 13; B4 giảm rủi ro này bằng sparse+dense fusion nhưng không vượt B0.
- Việc còn lại/blocker: Không có blocker. Phase 16 ở trạng thái `READY`; cần đóng gói runtime subset, thêm Agent/API/UI và kiểm tra giới hạn Render mà không làm thay đổi prediction/metric TEST Phase 15.

### 2026-10-13 — Phase 16 — COMPLETE

- Phạm vi đã làm: Đóng gói B4 thành runtime CPU-only có hash manifest; triển khai Agent router allow-list, Flask API, lazy loader, readiness, safety/rate-limit/timeout/CORS; thêm React `/rag`; chạy browser E2E và chụp ảnh; cập nhật Render Blueprint, dependency và tài liệu deploy.
- File tạo/sửa: `backend/knowledge_rag_service.py`, `backend/app.py`, `backend/models/kg_*`, `backend/tests/test_knowledge_rag_api.py`, `term_paper/tools/{build_phase16_runtime,verify_phase16}.py`, `term_paper/tests/test_phase16_runtime.py`, `web/src/pages/KnowledgeRagPage.tsx`, `web/src/api/knowledgeApi*.ts`, layout/style/router, `web/scripts/e2e_phase16.mjs`, `render.yaml`, report/manifest/E2E/screenshot Phase 16 và các README/kế hoạch.
- Dataset/model/source version: Dùng nguyên 762 medical + 86.421 finance chunk, BM25/LSA index và graph Phase 12–14; B4 khóa 2-hop với trọng số `0,6/0,1/0,3`; locked config SHA-256 `560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e`; public TEST không chạy lại.
- Lệnh/test đã chạy: 36 backend/Phase 16 test; 14 core Agent test; coverage core 95%; verifier 8/8; frontend 10/10 unit test, type-check, Vite production build và npm audit 0 vulnerability; Edge headless E2E local PASS; Render build verifier mode PASS.
- Kết quả: Runtime `phase16-b4-560c671a3920` có 87.183 chunk, 203 graph anchor, sáu artifact tổng 68.393.687 byte (65,23 MiB), dưới budget 192 MiB; medical/finance đều trả citation thật; injection/OOD/safety case abstain; E2E ghi 1 citation, 5 evidence, 4 graph node.
- Quyết định: Chỉ expose hai retriever cố định; không có shell/eval/exec hay API key; health nhẹ ở `/health`, readiness hash ở `/ready`; giữ nguyên root API contract để không regression; frontend nâng Vite/React Router và dependency liên quan lên bản audit sạch.
- Sai lệch so với plan: Browser Use không có surface khả dụng trong phiên (`browsers: []`), nên E2E dùng Edge headless qua CDP local và lưu log/screenshot tương đương. Index KG serialize bằng scikit-learn 1.9.0 còn Render ghim 1.9.1 cho model legacy; cross-minor smoke đã PASS và rủi ro được ghi rõ, không che giấu warning.
- Việc còn lại/blocker: Không có blocker. Phase 17 ở trạng thái `READY`; dùng metric Phase 15 và bằng chứng Agent/deploy Phase 16 để viết hoàn chỉnh Chương 5.

### 2026-10-13 — Phase 17 — COMPLETE

- Phạm vi đã làm: Viết hoàn chỉnh Chương 5 theo mục 5.1–5.7; trình bày lý thuyết KB/KG/RAG bằng nguồn gốc; mô tả MedQuAD, FinQA, Wikidata; báo cáo B0–B4, leakage control, public TEST, ablation, error, safety và hai case study; giữ Agent/deploy ở một mục ngắn; đóng gói hình và tạo verifier độc lập.
- File tạo/sửa: `term_paper/report/sections/05_knowledge_rag.md`; sáu asset và `asset_manifest.json` trong `term_paper/report/assets/ch5_knowledge_rag/`; `term_paper/tools/{build_phase17_content,verify_phase17}.py`; `term_paper/tests/test_phase17_content.py`; `phase17_{verification,coverage}.json`; `bibliography.bib`; `references_ordered.md`; các README và kế hoạch này.
- Dataset/model/source version: Giữ nguyên snapshot Phase 11–13 và metric one-shot Phase 15; locked config SHA-256 `560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e`; public TEST không chạy lại. Bổ sung nguồn gốc RDF, Knowledge Graphs, RAG, BM25, LSA, RRF, Wikidata và GraphRAG vào bibliography.
- Lệnh/test đã chạy: test đỏ do thiếu module verifier; sau triển khai 9/9 test PASS; coverage `verify_phase17.py` trên 80%; asset builder PASS; verifier Phase 17 9/9 PASS; citation/asset/hash/metric/page-budget audit PASS.
- Kết quả: Chapter source có 5.570 từ, ước tính 14,06 trang theo style đã khóa, đúng 6 hình/5 bảng và 13 citation key. Medical B4 Recall@5 `0,581`; finance B4 `0,480`, vẫn thấp hơn B0 `0,532`. Citation validity và challenge refusal được mô tả đúng phạm vi, không suy diễn thành độ đúng y khoa/tài chính.
- Quyết định: Gọi hệ thống là KG-RAG/graph-guided RAG, không đồng nhất với full GraphRAG community-summary pipeline. Giữ kết quả âm về dense/graph finance và answer numerical reasoning gần 0. Chưa ghép manuscript hoặc dựng DOCX ở Phase 17 để tránh trùng công việc Phase 18–19.
- Sai lệch so với plan: Không có sai lệch phạm vi. Ước lượng trang dùng 520 từ/trang cộng ngân sách cho hình/bảng, được hiệu chuẩn theo style 11,5 pt và chỉ là dự báo trước khi Word paginate.
- Việc còn lại/blocker: Không có blocker. Phase 18 ở trạng thái `READY`; cần tái cấu trúc manuscript, phân bổ deployment vào cuối Chương 2–5 và loại phần deployment độc lập sau khi migration verifier PASS.

### 2026-10-13 — Phase 18 — COMPLETE

- Phạm vi đã làm: Phân bổ deployment cũ vào mục 2.9/3.9/4.9 và giữ Agent ở 5.6; loại `05_trien_khai.md` khỏi danh sách section nhưng bảo toàn file nguồn; cập nhật tóm tắt, từ khóa, Mở đầu, RQ4, phương pháp, cấu trúc bài, kết luận và hạn chế; đồng bộ outline, requirements matrix, thuật ngữ, title/running header và DOCX validator động; dựng lại manuscript/references/manifest.
- File tạo/sửa: `term_paper/tools/{build_phase18_manuscript,verify_phase18}.py`; `term_paper/tests/test_phase18_migration.py`; `report/{front_matter,manuscript,references_ordered,report_manifest,terminology}.md/json`; section Chương 2–5 và Kết luận; `config/{report_outline,requirements_matrix}.md`; `report/{build_report,validate_report}.py`; `phase18_{verification,coverage}.json`; README và kế hoạch này.
- Dataset/model/source version: Không thay đổi dataset/model/prediction. Registry có 11 dòng cho Chương 2–5; bibliography có 57 entry, toàn bộ được cite. Locked config Phase 15 giữ SHA-256 `560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e`; public TEST không chạy lại.
- Lệnh/test đã chạy: test đỏ do thiếu module Phase 18; sau triển khai 6/6 test PASS; coverage hai module Phase 18 đạt 89%; manuscript builder PASS; verifier migration/renumber 15/15 PASS; kiểm tra citation/caption/hash/page budget và baseline hash PASS.
- Kết quả: Manuscript mới có 35.057 từ, 22 hình, 21 bảng, 57 tài liệu tham khảo và ước tính động 86,2 trang trong ngân sách 82–90. Thứ tự H1 đúng Mở đầu → Ch1 → Ch2 → Ch3 → Ch4 RNN → Ch5 KG/RAG → Kết luận → Tài liệu tham khảo; không còn standalone deployment heading. Ch2/3/4 lần lượt có mục 2.9/3.9/4.9; Ch5 dùng 5.6. Baseline DOCX vẫn có SHA-256 `0c82a1e90d394420a7143534ca2b06ebc912648b1c9ea17dd58784d095ce1e9d`.
- Quyết định: Giữ `05_trien_khai.md` ngoài manuscript làm nguồn lịch sử có thể truy vết thay vì xóa file. Hướng dẫn vận hành dài tiếp tục nằm trong README; thân bài chỉ giữ input/output, provenance, baseline, safety và phạm vi. Validator DOCX mới lấy số heading/caption/reference/page budget từ manifest thay vì hard-code 73 trang/125 heading.
- Sai lệch so với plan: Không tạo phụ lục PL.D mới vì `term_paper/deployment/README.md`, `RENDER_DEPLOY.md` và Phase 16 deployment report đã giữ đầy đủ hướng dẫn vận hành; đưa lại nội dung này vào manuscript sẽ lặp và vượt ngân sách. Không dựng DOCX ở Phase 18 theo ranh giới đã khóa.
- Việc còn lại/blocker: Không có blocker. Phase 19 ở trạng thái `READY`; cần dựng `Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`, Word paginate, cập nhật field, render và kiểm tra trực quan 100% trang trước khi phát hành.

### 2026-10-14 — Phase 19 — COMPLETE

- Phạm vi đã làm: Dựng DOCX mở rộng theo style mẫu; cập nhật TOC, danh mục hình/bảng và page map bằng Microsoft Word; sửa orphan header của Bảng 4.3 và dựng lại Hình 5.5; render PDF thành ảnh và kiểm tra trực quan 86/86 trang; chạy structural, accessibility, metadata, citation/artifact, security/path và regression audit; chốt release manifest SHA-256.
- File tạo/sửa: `term_paper/report/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`; `build_report.py`, `build_phase19_assets.py`, `validate_report.py`, `verify_phase19.py`; `qa_phase19/{word_page_map_final,visual_qa,a11y,accessibility_exceptions,render_docx_attempt,regression_summary,phase19_verification,final_release_manifest}.json`; requirements matrix, README và kế hoạch này.
- Dataset/model/source version: Không thay đổi dataset/model/prediction. Giữ khóa Phase 15 SHA-256 `560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e`; public TEST vẫn `run_count=1`. Baseline DOCX giữ SHA-256 `0c82a1e90d394420a7143534ca2b06ebc912648b1c9ea17dd58784d095ce1e9d`.
- Lệnh/test đã chạy: Word paginate/export hai vòng hậu-sửa và page map ổn định; validator DOCX 21/21 PASS; verifier Phase 16/17/18 lần lượt 8/8, 9/9, 15/15 PASS; 49 Python backend/runtime test PASS; 10 React API test PASS; TypeScript type-check và Vite production build PASS; final verifier Phase 19 17/17 PASS.
- Kết quả: Release có 86 trang, 178/178 navigation target, 22 hình, 21 bảng và 57 tài liệu tham khảo. Mở đầu 4 trang; Chương 1/2/3/4/5 lần lượt 8/15/14/15/13 trang. Accessibility không có finding high; ba finding medium đều là one-cell code containers và đã có documented exception. SHA-256 release `d7286dd4867e6216f197414e42fc112a3759621c017839fa9b1491b7c5dbfa51`.
- Quyết định: Microsoft Word 16 là renderer phân trang/PDF có thẩm quyền; ảnh trang dùng Windows PDF API. `documents/render_docx.py` đã được gọi nhưng không thể chạy vì máy Windows không có LibreOffice `soffice.exe`; ngoại lệ được ghi trong `render_docx_attempt.json` và không thay thế kiểm tra trực quan 100% trang.
- Sai lệch so với plan: Ba unit module Ch2–4 phụ thuộc TensorFlow không được thu thập trong `backend/.venv` vì môi trường này không cài TensorFlow; artifact đã khóa và verifier integrity vẫn PASS. Các regression quan trọng cho Phase 16–18, backend/API và web đều PASS; không chạy lại public TEST Phase 15.
- Việc còn lại/blocker: Không có. Phase 10–19 hoàn tất; `Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx` là artifact phát hành cuối.
