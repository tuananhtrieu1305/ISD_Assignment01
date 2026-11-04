# Chương 5 — Knowledge Base, Knowledge Graph và RAG

Workspace này phục vụ Phase 10–19 của kế hoạch `CHUONG_5_KNOWLEDGE_RAG_EXECUTION_PLAN.md`.

## Cấu trúc đã khóa

- Chương 4 — RNN được giữ nguyên numbering, code và artifact.
- Chương 5 — Knowledge Base, Knowledge Graph và Retrieval-Augmented Generation được thêm sau RNN.
- Phần deployment độc lập sẽ được phân bổ thành các mục ngắn ở cuối Chương 2–5; chi tiết vận hành dài chuyển sang Phụ lục PL.D/README.
- DOCX baseline `term_paper/report/Tieu_luan_AI_ML_CNN_RNN.docx` là chỉ đọc trong Phase 10–18.
- SHA-256 baseline: `0c82a1e90d394420a7143534ca2b06ebc912648b1c9ea17dd58784d095ce1e9d`.
- Bản mở rộng dự kiến: `term_paper/report/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`.

## Kết quả Phase 10

Baseline đã khóa:

- 82 file code/nội dung/deployment được hash;
- manuscript hiện có 125 heading, 18 hình và 16 bảng;
- migration map có 167 dòng: 125 heading + 18 hình + 16 bảng + 8 nhóm nội dung deployment;
- release baseline: 73 trang, 3.218.862 byte;
- không sửa DOCX baseline.

Các artifact:

- `artifacts/manifests/phase10_baseline.json`: SHA-256 và kích cỡ của release, manuscript, section, report builder/verifier và deployment source.
- `artifacts/manifests/environment_audit.json`: máy local, Python environment, package, Render target, lựa chọn stack và smoke benchmark.
- `artifacts/manifests/report_migration_map.csv`: đích đến của từng heading/hình/bảng và tám nhóm deployment.
- `artifacts/manifests/phase10_verification.json`: kết quả acceptance checks.

## Stack kỹ thuật tối thiểu

Stack bắt buộc, chạy không cần GPU/API key:

- sparse retrieval: `pure_python_bm25`;
- dense baseline: TF-IDF → `TruncatedSVD`/LSA 128 chiều → cosine trên matrix `float32` đã tính trước;
- graph runtime: adjacency index thuần Python; NetworkX chỉ dùng tùy chọn cho phân tích offline;
- answer layer: extractive grounded, citation chỉ trỏ tới retrieved IDs và có abstention threshold;
- FinQA calculator: interpreter phép toán allow-list, không dùng `eval`;
- backend/frontend: mở rộng Flask `backend/` và React `web/` hiện có.

Lý do lựa chọn:

- Render Free hiện có 0,1 CPU và 512 MB RAM; filesystem là ephemeral và service ngủ sau 15 phút không có request: <https://render.com/docs/compute-plans>, <https://render.com/docs/free>.
- Backend local đã có NumPy/scikit-learn nhưng không có Sentence Transformers, ONNX Runtime, FAISS hoặc rank-bm25.
- Ngân sách đã khóa: peak process dưới 400 MiB; artifact KG/RAG đóng gói dưới 192 MiB; cold start ứng dụng dưới 20 giây, không tính thời gian Render đánh thức service.
- Local workspace chỉ còn khoảng 2,4 GB trống tại thời điểm audit, nên Phase 11–16 không được tải model lớn nếu chưa kiểm tra dung lượng.

Ứng viên `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` được giữ cho ablation offline vì hỗ trợ 50 ngôn ngữ, vector 384 chiều và Apache-2.0. Model khoảng 0,1B tham số không được chọn làm runtime mặc định trên Render 512 MB: <https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2>.

Required generator là bộ soạn câu trả lời extractive có citation. Adapter LLM local/API chỉ là tùy chọn, mặc định tắt và không được trở thành dependency của test, Render startup hoặc demo cuối.

## Audit khả năng tái sử dụng

| Khu vực | Quyết định | Nội dung |
|---|---|---|
| `backend/` | REUSE | Flask app factory, CORS allow-list, rate limit, security headers, health và error schema |
| `web/` | REUSE | React Router, layout, component trạng thái/kết quả và visual style hiện có |
| `term_paper/deployment/` | PARTIAL_REUSE | hash verification, schema và deterministic demo; static server/UI cũ không phải public target |
| `neo4j_scripts/` | REFERENCE_ONLY | chỉ có hai graph minh họa 19 dòng cho prediction; chưa có corpus ingestion, provenance hoặc retrieval |
| `render.yaml` | REUSE_AND_EXTEND | giữ kiến trúc Python Web Service + React Static Site |

Tại thời điểm audit Phase 10, Node/npm chưa có trên `PATH` và backend `.venv` dùng scikit-learn 1.9.0. Phase 16 đã khôi phục Node 24 để test/build UI và nâng `.venv` lên scikit-learn 1.9.1 cho khớp requirements/Render. Index Phase 14 vẫn mang metadata serialize 1.9.0; cross-minor smoke trên 1.9.1 đã PASS và giới hạn này được ghi công khai trong `phase16_deployment_report.md`.

## Smoke benchmark

Micro-smoke CPU gồm 6 document và 3 query:

- BM25: 3/3 top-1 đúng;
- TF-IDF + TruncatedSVD/LSA: 3/3 top-1 đúng;
- kết quả chỉ xác nhận code path và khả năng chạy CPU, không phải kết luận chất lượng trên MedQuAD/FinQA.

## Chạy lại Phase 10

Từ workspace root:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m unittest term_paper.tests.test_phase10_verifier -v
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.build_phase10_baseline
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase10
```

Builder ghi lại hash theo trạng thái hiện tại. Không chạy builder sau khi cố ý thay đổi baseline nếu mục tiêu chỉ là kiểm tra tính bất biến; khi đó chỉ chạy verifier.

## Kết quả Phase 11

Ba nguồn thật đã được khóa và đo trực tiếp:

- MedQuAD commit `577bd37b96c02d1833b2c9eed2de9f96964e96cb`: 11.274 XML, 47.441 QA, 16.407 answer hiện hữu; CC BY 4.0.
- FinQA commit `0f16e2867befa6840783e58be38c9efb9229d742`: 8.281 public QA có program và 919 private-test QA; MIT.
- Wikidata: 10 entity snapshot hẹp, chia đều medical/finance, 2.056 claim; từng entity có revision ID; CC0 1.0; không dùng full dump.

Raw file đã được khóa trong `artifacts/manifests/raw_manifest.csv` với aggregate SHA-256 `b7af4e6c5e5e8bc4bc4d09e8fad05df119ada7a1159438cc467bb1e678dafcb1`. Git metadata của hai clone đã được thay bằng `source_snapshot.json` để raw tree không trở thành nested repository; commit SHA và commit time vẫn được bảo toàn.

Artifact chính:

- `data/raw/`: MedQuAD, FinQA và cache Wikidata.
- `artifacts/manifests/raw_manifest.csv`: 11.345 file-level hash record.
- `artifacts/manifests/phase11_snapshot_manifest.json`: URL, commit/revision, license, kích cỡ và dataset-level hash.
- `artifacts/metrics/phase11_data_audit.json` và `.md`: schema, missing/duplicate, split và phân bố đo từ local.
- `artifacts/figures/phase11/`: ba hình phân bố sơ bộ.
- `../sources/dataset_cards/ch5_*.md`: ba dataset card.

Chạy kiểm tra Phase 11:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase11_acquisition.py -q
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase11
```

Không chạy lại builder sau khi raw đã khóa nếu chỉ cần kiểm tra; verifier sẽ phát hiện mọi file bị sửa, thiếu hoặc đổi hash.

## Kết quả Phase 12

Corpus và evaluation contract đã khóa:

- MedQuAD diabetes: 274 candidate, loại 27 exact duplicate, còn 247 query/document và 762 chunk/evidence; grouped split 152/33/62 theo train/validation/test.
- FinQA: 9.200 query, 2.789 page document, 86.421 chunk và 14.108 gold evidence; giữ official split 6.251/883/1.147 và private-test 919 inference-only.
- Challenge: 16 query OOD/adversarial, chia đều medical/finance, expected behavior `abstain`.
- Manual diabetes audit: 40 TP, 0 FP, 17 TN, 3 FN; inclusion precision 1,000.
- Public page group overlap bằng 0. Official company-year report key vẫn overlap và được ghi là limitation; không remap benchmark hậu nghiệm.
- TEST ở trạng thái `SEALED_NOT_USED_FOR_TUNING`.

Artifact chính:

- `data/processed/phase12/{documents,chunks,queries,evidence}.jsonl`;
- `data/processed/phase12/challenge_queries.jsonl`;
- `config/phase12.json` và `config/phase12_manual_reviews.json`;
- `evaluation_contract.md`;
- `artifacts/manifests/preprocessing_manifest.json`;
- `artifacts/metrics/phase12_preprocessing_audit.json` và `.md`;
- `artifacts/metrics/phase12_diabetes_manual_audit.csv`.

Chạy lại và kiểm tra:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase12_preprocessing.py -q
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.build_phase12_preprocessing
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase12
```

## Kết quả Phase 13

Hai Knowledge Graph có schema và provenance đã được dựng hoàn toàn offline:

- medical: 1.336 node, 1.506 edge, 62 entity MedQuAD và 3 exact Wikidata link;
- finance: 99.355 node, 97.809 edge, 137 company, 799 annual report, 86.421 chunk và 5 exact Wikidata link;
- provenance coverage node/edge đạt 100%; duplicate rate bằng 0; không có dangling edge;
- không có cạnh gold-derived nối câu hỏi tới đáp án/document; gold chỉ nằm trong evaluation artifact Phase 12;
- audit có 203 local entity/concept/company: 8 linked, 195 unresolved, không ép bất kỳ match mơ hồ nào;
- mỗi domain có `nodes.jsonl`, `edges.jsonl`, `graph.graphml` và `adjacency.json` để truy vấn không cần Neo4j.

Artifact chính:

- `config/phase13.json` và `graph_schema.md`;
- `data/processed/phase13/{medical,finance}/`;
- `artifacts/metrics/phase13_graph_statistics.{json,csv}` và `phase13_entity_link_audit.csv`;
- `artifacts/figures/phase13/`;
- `artifacts/manifests/phase13_graph_manifest.json`, `phase13_verification.json` và `phase13_coverage.json`.

Chạy lại và kiểm tra:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase13_graph.py -q
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.build_phase13_graphs
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase13
```

## Kết quả Phase 14

Ba baseline dùng chung corpus, validation query, top-k và evaluator đã được khóa:

- B0: BM25 (`k1=1,5`, `b=0,75`);
- B1: TF-IDF + TruncatedSVD/LSA 128 chiều;
- B2: weighted reciprocal-rank fusion, chọn sparse weight `0,75` trên validation theo macro-domain chunk Recall@5;
- TEST chưa được chạy: `SEALED_NOT_RUN`.

Chunk Recall@5 trên validation:

| Domain | B0 | B1 | B2 |
|---|---:|---:|---:|
| Medical | 0,333 | 0,394 | 0,364 |
| Finance | 0,535 | 0,245 | 0,450 |

B2 cải thiện rõ so với dense B1 trên finance nhưng chưa vượt BM25 B0. Answer layer extractive đạt token F1 khoảng 0,207–0,217 trên medical và gần 0 trên FinQA, cho thấy retrieval thuần chưa xử lý được numerical reasoning. Cả ba model trên cả hai domain đều abstain 100% trên 16 challenge query; citation validity đạt 100%.

Artifact chính:

- `config/phase14.json` và `config/phase14_locked.json`;
- `data/processed/phase14/indexes/{medical,finance}/`;
- `artifacts/predictions/phase14/`;
- `artifacts/metrics/phase14_metrics.{json,csv}` và `phase14_tuning.json`;
- `artifacts/figures/phase14/`;
- `notebooks/ch5_rag_baselines_b0_b2.ipynb`;
- `artifacts/manifests/phase14_baseline_manifest.json`, `phase14_verification.json` và `phase14_coverage.json`.

Chạy lại và kiểm tra:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase14_rag.py -q
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.build_phase14_baselines
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase14
```

## Kết quả Phase 15

B3 và B4 đã được khóa trên validation trước khi public TEST được chạy đúng một lần:

- B3: graph-neighborhood retrieval với giới hạn 2 hop;
- B4: weighted RRF với trọng số sparse/dense/graph `0,6/0,1/0,3`;
- locked config SHA-256: `560c671a3920bd6bde9f7fc005f3c952f857c55969c989bb6109932623210c9e`;
- TEST manifest: `COMPLETE`, `run_count=1`; FinQA private-test không được dùng.

Chunk Recall@5 trên public TEST:

| Domain | B0 | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|---:|
| Medical | 0,403 | 0,339 | 0,403 | 0,581 | 0,581 |
| Finance | 0,532 | 0,232 | 0,443 | 0,034 | 0,480 |

B4 cải thiện so với B2 `+0,177` ở medical và `+0,037` ở finance; 95% bootstrap CI lần lượt là `0,096–0,274` và `0,022–0,052`. Đây là hiệu ứng của cấu hình hybrid đầy đủ, không phải bằng chứng rằng graph một mình tạo ra toàn bộ mức tăng. Trên finance, B4 vẫn thấp hơn BM25 B0. Citation validity đạt 100%; B3/B4 đều từ chối đúng 16/16 challenge OOD/adversarial và không phát citation. Không có tuyên bố “giảm hallucination”.

Artifact chính:

- `artifacts/predictions/phase15/`: prediction B0–B4 TEST, B3–B4 validation/challenge;
- `artifacts/metrics/phase15_test_metrics.{json,csv}`, `phase15_bootstrap_ci.csv`, `phase15_ablation_validation.csv`, `phase15_error_analysis.csv` và `phase15_case_studies.jsonl`;
- `artifacts/figures/phase15/`: sáu figure Word-ready;
- `notebooks/ch5_kgrag_b0_b4.ipynb`: notebook đã execute;
- `artifacts/manifests/phase15_{validation_manifest,test_run,experiment_manifest,verification,coverage}.json`;
- `phase15_experiment_report.md`.

Chỉ chạy verifier khi kiểm tra lại. Không chạy lại TEST hoặc xóa `phase15_test_run.json`:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase15_kgrag.py -q
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase15
```

## Kết quả Phase 16

Agent KG–RAG B4 đã được tích hợp vào Flask API và React UI:

- endpoint `POST /api/agent/query`, health `/health`, readiness/hash check `/ready`;
- router chỉ cho phép `medical_retriever` và `finance_retriever`;
- lazy-load 87.183 chunk, bốn index và 203 graph anchor trong gói 68.393.687 byte;
- câu trả lời extractive có citation/evidence/graph path, có abstention và safety warning;
- trang React `/rag`, E2E browser thật và ảnh `report/assets/ch5_knowledge_rag/phase16_agent_medical.png`;
- Render Blueprint gồm Python web service và React static site, không cần API key;
- backend regression, frontend test/type-check/build, audit dependency, verifier và E2E đều PASS.

Chi tiết kiến trúc, API, cách chạy, cách deploy, giới hạn version persistence và bằng chứng xem tại `phase16_deployment_report.md`. Artifact chính gồm `backend/models/kg_manifest.json`, `artifacts/manifests/phase16_verification.json`, `phase16_coverage.json` và `artifacts/e2e/phase16_e2e.json`.

## Kết quả Phase 17

Chương 5 hoàn chỉnh nằm tại `../report/sections/05_knowledge_rag.md`, gồm 5.570 từ và ước tính 14,06 trang trước khi dựng Word. Nội dung có đủ mục 5.1–5.7, ba dataset, B0–B4, protocol/leakage, hai case study, ablation/error/safety và mục Agent ngắn. Sáu hình và năm bảng đều có provenance; sáu file hình dùng trong chương được khóa hash ở `../report/assets/ch5_knowledge_rag/asset_manifest.json`.

Kiểm tra lại nội dung mà không chạy lại public TEST:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase17_content.py -q -p no:cacheprovider
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase17
```

Verifier đạt 9/9, unit/integration test đạt 9/9 và coverage của `verify_phase17.py` trên 80%. Phase 18 mới ghép section này vào manuscript và migration phần deployment; Phase 19 mới dựng, paginate và QA DOCX cuối.

## Kết quả Phase 18

`05_knowledge_rag.md` đã được ghép sau Chương 4 RNN. Deployment không còn là Heading 1 độc lập: MLP, CNN và RNN dùng các mục 2.9, 3.9, 4.9; Agent KG-RAG giữ ở 5.6. File `05_trien_khai.md` được bảo toàn ngoài manuscript làm nguồn lịch sử. Tóm tắt, Mở đầu/RQ4, Kết luận, outline, requirements matrix, thuật ngữ, bibliography, title/running header và report manifest đã đồng bộ.

Manuscript Phase 18 có 35.057 từ, 22 hình, 21 bảng, 57 tài liệu tham khảo và ước tính 86,2 trang. Verifier migration đạt 15/15, sáu test đạt 6/6, coverage hai module Phase 18 đạt 89%; baseline DOCX 73 trang không thay đổi hash. Chạy kiểm tra mà không chạy lại public TEST:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.build_phase18_manuscript
& '.\backend\.venv\Scripts\python.exe' -m pytest term_paper\tests\test_phase18_migration.py -q -p no:cacheprovider
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase18
```

Phase 19 sẽ dựng và QA `report/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`; manuscript hiện tại chưa phải release DOCX mới.
