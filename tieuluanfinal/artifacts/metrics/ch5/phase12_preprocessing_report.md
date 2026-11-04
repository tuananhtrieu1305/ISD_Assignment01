# Phase 12 — Báo cáo tiền xử lý, split và bộ đánh giá

Ngày khóa: 2026-10-12. TEST chưa được dùng để tuning.

## Kết quả MedQuAD diabetes

- Rule `diabetes-focus-question-v1` chỉ dùng focus/question và yêu cầu answer; không dùng answer-only match.
- Trên 47.441 QA raw: 274 record được chọn; loại 27 exact duplicate; còn 247 document/query và 762 answer chunk/evidence.
- Group theo normalized focus, SHA-256 seed 42: train 152, validation 33, test 62; 62 group, không giao nhau giữa split.
- Manual audit deterministic: 40 TP, 0 FP, 17 TN, 3 FN; inclusion precision 1,000. Ba FN là Leprechaunism, Aceruloplasminemia và Wolfram syndrome; audit exclusion là mẫu near-match làm giàu, không phải ước lượng recall corpus.
- Chunking: tối đa 120 whitespace words, overlap 20, giữ word/character offsets và raw hash.

## Kết quả FinQA

- Giữ official split: train 6.251, validation 883, public test 1.147, private test 919 query.
- Dedupe context tạo đúng 2.789 page document và 86.421 `text_i`/`table_i` chunk.
- Có đủ 14.108 gold evidence locator; alias upstream `text_-1` được ánh xạ về post-text cuối.
- 328 annotation khác raw-linearization chỉ ở spacing/punctuation; token-level mismatch bằng 0.
- Public page group overlap bằng 0. Company-year report key vẫn overlap 197/243/93 giữa các cặp split; đây là thuộc tính official benchmark và được công bố trong contract.
- Private test dùng lại 303 public-test page và không có full gold; chỉ dùng inference demo. Một câu hỏi trùng exact giữa public/private được giữ với source-aware ID và ghi duplicate audit.

## Bộ đánh giá đã khóa

- 16 challenge query: 8 medical + 8 finance; mỗi domain có 4 OOD và 4 adversarial; expected behavior đều là abstain.
- Top-k: 1, 3, 5, 10.
- Retrieval: document Recall@k, chunk Recall@k, MRR@10.
- Answer: normalized exact match, token F1; FinQA thêm execution/program accuracy.
- Chỉ train/validation dùng tuning; public TEST bị khóa. Private test không tính metric.

## Artifact

- Processed JSONL/CSV: `term_paper/knowledge_rag/data/processed/phase12/`.
- Config: `term_paper/knowledge_rag/config/phase12.json`.
- Evaluation contract: `term_paper/knowledge_rag/evaluation_contract.md`.
- Machine-readable audit: `phase12_preprocessing_audit.json`.
- Manifest: `preprocessing_manifest.json`.
- Manual review: `phase12_diabetes_manual_audit.csv`.

Verifier kiểm tra hash, ID uniqueness, raw provenance, dangling relation, gold mapping, group leakage, challenge behavior, manual precision và trạng thái TEST.
