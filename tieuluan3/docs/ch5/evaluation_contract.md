# Phase 12 — Evaluation contract cho Chương 5 Knowledge & RAG

Phiên bản: 1.0, khóa ngày 2026-10-12. Contract này phải được giữ nguyên cho B0–B4; mọi thay đổi sau khi xem kết quả TEST phải tạo phiên bản mới và được ghi là protocol deviation.

## 1. Đơn vị dữ liệu và provenance

Mọi record dùng ID ổn định sinh từ SHA-256 của các trường định danh, không dùng thứ tự dòng:

- `document_id`: một MedQuAD answer hoặc một FinQA report page/context duy nhất;
- `chunk_id`: một answer window MedQuAD hoặc một evidence unit `text_i`/`table_i` FinQA;
- `query_id`: câu hỏi gắn với dataset và raw record;
- `evidence_id`: quan hệ query → gold chunk;
- `group_id`: normalized MedQuAD focus hoặc FinQA page ID.

Document giữ `raw_source_path`, SHA-256 raw, source URL/locator và metadata. Chunk giữ `document_id`, locator và offset/unit gốc. Query giữ gold document/chunk/evidence IDs và answer/program khi upstream cung cấp.

## 2. Lọc MedQuAD diabetes

Filter `diabetes-focus-question-v1` chỉ nhận record có answer và tín hiệu diabetes trong `Focus` hoặc `Question`. Không dùng keyword chỉ xuất hiện trong `Answer`, vì cách đó đưa các bệnh khác vào corpus do answer tình cờ nhắc diabetes. `diabetes insipidus` bị loại để tránh nhầm với diabetes mellitus.

Rule chạy trên 47.441 QA raw, chọn 274 record và loại 27 exact duplicate `(focus, question, answer)`, còn 247 query. Manual audit deterministic gồm 40 inclusion và 20 excluded near-match:

- inclusion precision: 40/40 = 1,000;
- 17 true negative, chủ yếu keyword chỉ nằm trong answer hoặc diabetes insipidus;
- 3 false negative có ý nghĩa lâm sàng: Leprechaunism, Aceruloplasminemia và Wolfram syndrome;
- mẫu exclusion được cố ý làm giàu near-match nên không dùng để ước lượng recall toàn corpus.

False negative được giữ trong audit, không sửa rule sau khi biết TEST. Nếu mở rộng rule ở nghiên cứu sau, phải tăng version filter và dựng lại split.

## 3. Split và chống leakage

### MedQuAD

- Group theo normalized `Focus`; mọi câu hỏi cùng focus luôn ở cùng split.
- SHA-256 group assignment, seed 42: train 70%, validation 15%, test 15%.
- Kết quả khóa: train 152, validation 33, test 62 query trên 62 group; không có group giao nhau.

### FinQA

- Giữ nguyên official train/dev/public-test; `dev` được đổi tên hiển thị thành `validation`.
- Group retrieval là report page ID sau khi bỏ suffix QA cuối. Public train/validation/test lần lượt có 2.110/299/380 page và không có page overlap.
- Company-year report key vẫn giao nhau 197/243/93 giữa các cặp public split. Đây là thuộc tính của official FinQA split; không được remap vì yêu cầu tái lập benchmark. Báo cáo phải nêu đây là giới hạn và không tuyên bố split độc lập ở mức annual report.
- `private_test` có 919 query trên 303 page trùng public test, không có full gold; chỉ dùng inference demo, không tính metric và không dùng tuning.
- Khi đánh giá retrieval, candidate corpus bị giới hạn theo split của query. Private-test dùng page corpus tương ứng của public test.

## 4. Chunking đã khóa

- MedQuAD: whitespace word window tối đa 120 từ, overlap 20 từ; giữ word/character offsets. Mọi chunk thuộc cùng document và split.
- FinQA: một chunk cho mỗi official `text_i` và `table_i`; `pre_text + post_text` giữ đúng thứ tự upstream. Bảng dùng đúng `table_row_to_text` của repo FinQA đã sửa lỗi năm 2022.
- Alias annotation `text_-1` duy nhất được ánh xạ tới post-text cuối của record tương ứng và được ghi trong audit.
- Không thay chunk size, overlap hoặc table linearization giữa B0–B4.

## 5. Query, gold evidence và challenge set

- Mỗi query phải có `query_id`, domain, dataset, split, group và gold document/chunk/evidence khi upstream cung cấp.
- MedQuAD dùng answer chunk làm gold evidence.
- FinQA dùng `gold_inds`; text locator và table locator được ánh xạ về chunk. Khoảng trắng quanh dấu câu có thể khác giữa raw table cell và annotation, nên audit báo cả exact-spacing mismatch và token-level mismatch.
- Challenge set có 16 query: 8 medical, 8 finance; mỗi domain gồm 4 OOD và 4 adversarial. Tất cả có expected behavior `abstain`, không có fabricated gold answer.

## 6. Metric và top-k

Top-k cố định: `1, 3, 5, 10`.

Retrieval:

- document Recall@k: tỷ lệ gold document xuất hiện trong k document đầu;
- chunk Recall@k: tỷ lệ gold chunk xuất hiện trong k chunk đầu;
- MRR@10: nghịch đảo rank của gold item đầu tiên, 0 nếu không có trong top 10.

Answer:

- normalized exact match: lowercase, bỏ punctuation/article và chuẩn hóa whitespace;
- token F1 trên multiset token chuẩn hóa;
- FinQA execution accuracy và program accuracy theo evaluator upstream;
- answer không có citation hợp lệ bị tính sai, dù text trùng gold.

Safety/challenge:

- abstention accuracy;
- unsupported-answer rate;
- invalid-citation rate.

Mọi metric là macro average theo query. Phải công bố số query có gold; private-test không được đưa vào mẫu số.

## 7. Quy tắc tuning và TEST

1. Chỉ train và validation được dùng chọn tokenizer, retriever, top-k policy, graph hop, threshold và prompt/template.
2. Top-k reporting grid đã khóa, không chọn riêng theo TEST.
3. TEST chỉ chạy sau khi B0–B4, threshold và code evaluator đã khóa hash.
4. Không sửa filter, split, chunk hoặc gold mapping sau khi xem TEST mà không ghi protocol deviation.
5. B0–B4 dùng cùng query/candidate corpus và evaluator; khác biệt duy nhất là thành phần retrieval/graph/generation được định nghĩa ở Phase 14–15.
6. Kết quả âm, abstention và failure case phải được giữ, không lọc hậu nghiệm.

## 8. Tái lập

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase12_preprocessing.py -q
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.build_phase12_preprocessing
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase12
```

Nguồn cấu hình: `config/phase12.json`. Hash, kích cỡ, counts và trạng thái TEST được khóa trong `artifacts/manifests/preprocessing_manifest.json`.
