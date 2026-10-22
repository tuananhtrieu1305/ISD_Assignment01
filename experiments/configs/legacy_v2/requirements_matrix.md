# Ma trận truy vết yêu cầu tiểu luận

Phiên bản: 2.1 — chốt phát hành Phase 19, ngày 2026-10-14.
Nguồn yêu cầu: nội dung giảng viên do người dùng cung cấp.  
Quy ước trạng thái: `LOCKED` = đã khóa thiết kế; `AVAILABLE` = đã có bằng chứng nguồn; `PLANNED` = sẽ tạo ở phase sau; `PENDING_INPUT` = cần thông tin/quyền từ người dùng; `N/A` = không áp dụng.

## 1. Yêu cầu cấu trúc và dung lượng

| ID | Yêu cầu | Vị trí trong outline | Artifact/bằng chứng | Phase | Trạng thái |
|---|---|---|---|---:|---|
| STR-01 | Mở đầu dài 3–4 trang | Mở đầu, mục 0.1–0.4 | DOCX trang 10–13; `report_validation_kg_rag.json` | 2, 8, 19 | AVAILABLE |
| STR-02 | Chương 1: Lịch sử phát triển AI, 8 trang | Chương 1, mục 1.1–1.6 | DOCX trang 14–21; `report_validation_kg_rag.json` | 2, 8, 19 | AVAILABLE |
| STR-03 | Chương 2: ML cơ bản, 10–15 trang | Chương 2, mục 2.1–2.9 | DOCX trang 22–36; artifact Chương 2 | 3, 8, 19 | AVAILABLE |
| STR-04 | Chương 3: CNN, 10–15 trang | Chương 3, mục 3.1–3.9 | DOCX trang 37–50; artifact Chương 3 | 4, 8, 19 | AVAILABLE |
| STR-05 | Chương 4: RNN, 10–15 trang | Chương 4, mục 4.1–4.9 | DOCX trang 51–65; artifact Chương 4 | 5, 8, 19 | AVAILABLE |
| STR-06 | Có phần triển khai mô hình | Mục 2.9, 3.9, 4.9 và 5.6 | `deployment/`; `backend/`; `web/`; các mục deploy ngắn cuối chương | 6, 16, 18 | AVAILABLE |
| STR-07 | Có kết luận và tài liệu tham khảo | Kết luận; Tài liệu tham khảo | `report/manuscript.md`; `report/references_ordered.md`; `bibliography.bib` | 7 | AVAILABLE |
| STR-08 | Sản phẩm cuối là một DOCX hoàn chỉnh | Toàn tài liệu | `Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`; 86 trang; final verifier PASS | 8–9, 19 | AVAILABLE |
| STR-09 | Chương 5 Knowledge & RAG dài 12–15 trang | Chương 5, mục 5.1–5.7 | DOCX trang 66–78: 13 trang; content verifier 9/9 PASS | 17, 19 | AVAILABLE |

## 2. Yêu cầu dataset

Giải thích đã khóa: yêu cầu 2–3 dataset áp dụng cho ba chương thực nghiệm 2–4; Chương 1 là chương lịch sử nên không huấn luyện dataset.

| ID | Yêu cầu | Vị trí trong outline | Artifact/bằng chứng | Phase | Trạng thái |
|---|---|---|---|---:|---|
| DATA-01 | Chương 2 có 2–3 dataset | 2.4.1–2.4.3 | 3 dataset cards: Diabetes Binary, Vietnam Housing, E-Commerce Behavior | 1 | AVAILABLE |
| DATA-02 | Chương 3 có 2–3 dataset | 3.4.1–3.4.3 | 3 dataset cards: EuroSAT, Oxford-IIIT Pet, CDC Diabetes 012 | 1 | AVAILABLE |
| DATA-03 | Chương 4 có 2–3 dataset | 4.4.1–4.4.2 | 2 dataset cards: Online Retail II, AAPL | 1 | AVAILABLE |
| DATA-04 | Mỗi dataset có link nguồn | Mục dataset card của từng chương | `sources/source_registry.csv`; 8 dataset cards | 1 | AVAILABLE |
| DATA-05 | Mỗi dataset có kích cỡ vật lý và logic | Mục dataset card của từng chương | `source_hashes.csv`; 8 dataset cards | 1 | AVAILABLE |
| DATA-06 | Mỗi dataset có input/output mẫu | Mục dataset card của từng chương | Mục “Mẫu trình bày” trong 8 dataset cards; bảng/hình dataset trong `report/manuscript.md` | 1, 3–7 | AVAILABLE |
| DATA-07 | Mỗi dataset có phân bố | Mục dataset card của từng chương | Phân bố thực đo trong 8 dataset cards; figure tái tạo ở Phase 3–5 | 1, 3–5 | AVAILABLE |
| DATA-08 | Mỗi dataset có nhận xét/hạn chế | Mục dataset card của từng chương | Mục “Nhận xét và giới hạn” trong 8 dataset cards | 1 | AVAILABLE |
| DATA-09 | Có license/citation khi xác minh được | Mục dataset card; Tài liệu tham khảo | `source_registry.csv`; `bibliography.bib` | 1 | AVAILABLE |
| DATA-10 | Sai lệch README so với dữ liệu thật phải được nêu | 2.4.3 | `ch2_ecommerce_behavior.md` | 1 | AVAILABLE |
| DATA-11 | Chương 5 có 2–3 dataset/nguồn dữ liệu | 5.2.1 | MedQuAD, FinQA, Wikidata dataset cards và registry | 11, 17 | AVAILABLE |
| DATA-12 | Dataset Chương 5 có link, size, mẫu, phân bố, nhận xét và license | 5.2.1; Bảng 5.1; Hình 5.1 | `sources/dataset_cards/ch5_*.md`; Phase 11 audit | 11, 17 | AVAILABLE |
| DATA-13 | Snapshot và provenance Chương 5 được khóa | 5.2 | commit MedQuAD/FinQA; Wikidata revision; raw manifest SHA-256 | 11–13 | AVAILABLE |

## 3. Yêu cầu code và thực nghiệm

| ID | Yêu cầu | Vị trí trong outline | Artifact/bằng chứng | Phase | Trạng thái |
|---|---|---|---|---:|---|
| EXP-01 | Chương 2 có code scratch | 2.5.1 | `src/scratch/mlp.py`; notebook Chương 2 | 3 | AVAILABLE |
| EXP-02 | Chương 2 có code Keras | 2.5.2 | `src/keras_impl/mlp.py`; notebook Chương 2 | 3 | AVAILABLE |
| EXP-03 | Chương 2 có code PyTorch | 2.5.3 | `src/pytorch_impl/mlp.py`; notebook Chương 2 | 3 | AVAILABLE |
| EXP-04 | Chương 3 có code scratch trainable | 3.5.1 | `src/scratch/cnn.py`; numerical-gradient/toy-overfit tests | 4 | AVAILABLE |
| EXP-05 | Chương 3 có code Keras | 3.5.2 | A05 hiện có; wrapper matched trong `src/keras_impl/cnn.py` | 4 | AVAILABLE |
| EXP-06 | Chương 3 có code PyTorch | 3.5.3 | `src/pytorch_impl/cnn.py`; notebook Chương 3 | 4 | AVAILABLE |
| EXP-07 | Chương 4 có code scratch với BPTT | 4.5.1 | `src/scratch/rnn.py`; numerical-gradient, clipping, toy-overfit và save/load tests | 5 | AVAILABLE |
| EXP-08 | Chương 4 có code Keras | 4.5.2 | A06 hiện có; wrapper matched trong `src/keras_impl/rnn.py` | 5 | AVAILABLE |
| EXP-09 | Chương 4 có code PyTorch | 4.5.3 | A06 hiện có; wrapper matched trong `src/pytorch_impl/rnn.py` | 5 | AVAILABLE |
| EXP-10 | Đánh giá 3 implementation trên cùng dữ liệu/split | 2.6; 3.6; 4.6 | `experiment_contract.md`; split/index artifacts; parity checks Ch2–4 | 3–5 | AVAILABLE |
| EXP-11 | Đánh giá trên 2–3 dataset mỗi chương | 2.6; 3.6; 4.6 | Ch2: 3; Ch3: EuroSAT + CDC matched, Oxford case study; Ch4: 2 matched | 3–5 | AVAILABLE |
| EXP-12 | So sánh metric nhiệm vụ | 2.6; 3.6; 4.6 | `ch2_framework_comparison.csv`; `ch3_framework_comparison.csv`; `ch4_framework_comparison.csv` | 3–5 | AVAILABLE |
| EXP-13 | So sánh parameter count | 2.6; 3.6; 4.6 | Metric artifacts Ch2–4; Ch4 khớp 1.249 tham số | 3–5 | AVAILABLE |
| EXP-14 | So sánh training/inference time | 2.6; 3.6; 4.6 | Timing fields trong comparison CSV và summary Ch2–4 | 3–5 | AVAILABLE |
| EXP-15 | Không rò rỉ dữ liệu; preprocessing chỉ fit TRAIN | 2.3; 3.3; 4.3 | `experiment_contract.md`; saved preprocessors/hashes; temporal split checks Ch4 | 3–5 | AVAILABLE |
| EXP-16 | Metric trong bài truy ngược được về prediction artifact | Mọi bảng kết quả | Prediction CSV + notebook/verifier tái tính metric Ch2–4 | 3–5, 7 | AVAILABLE |
| EXP-17 | Không che giấu kết quả collapse/âm | 3.7; 4.7; Kết luận | Ch3 giữ collapse A05; Ch4 giữ 9/9 RNN stock thua naive | 4–7 | AVAILABLE |
| EXP-18 | Chương 5 so sánh B0–B4 trên cùng corpus/evaluator | 5.3–5.5 | Phase 15 TEST metrics, prediction, ablation và bootstrap CI | 14–17 | AVAILABLE |
| EXP-19 | Public TEST Chương 5 chỉ chạy sau khi khóa cấu hình | 5.3.3 | `phase15_test_run.json`: `COMPLETE`, `run_count=1` | 15 | AVAILABLE |
| EXP-20 | KG/RAG có leakage, citation, refusal và error audit | 5.2–5.5 | graph verifier, challenge 16/16, citation validity và error analysis | 13–17 | AVAILABLE |
| EXP-21 | Yêu cầu scratch/Keras/PyTorch vẫn thuộc Chương 2–4 | 2.5; 3.5; 4.5 | MLP/CNN/RNN matched implementations; Ch5 dùng retrieval protocol phù hợp | 3–5, 18 | AVAILABLE |

## 4. Yêu cầu triển khai, trình bày và QA

| ID | Yêu cầu | Vị trí trong outline | Artifact/bằng chứng | Phase | Trạng thái |
|---|---|---|---|---:|---|
| DEP-01 | Ứng dụng inference chạy local | 2.9; 3.9; 4.9; 5.6 | React `web/`, Flask `backend/`, Phase 6 service và E2E Phase 16 | 6, 16, 18 | AVAILABLE |
| DEP-02 | Có use case đại diện ML/CNN/RNN/KG-RAG | 2.9; 3.9; 4.9; 5.6 | Diabetes, EuroSAT, customer/AAPL và Agent retrieval | 6, 16, 18 | AVAILABLE |
| DEP-03 | Có schema validation, artifact hash và health/readiness | Các mục deploy cuối chương | `model_registry.json`; `kg_manifest.json`; `/health`; `/ready`; verifier | 6, 16 | AVAILABLE |
| DEP-04 | Có cảnh báo y khoa/tài chính, citation và refusal | 2.9; 4.9; 5.4–5.6 | UI/API response, challenge set và screenshot | 6, 15–18 | AVAILABLE |
| DOC-01 | Theo phong cách DOCX mẫu | Toàn tài liệu | `style_spec.md`; DOCX mở rộng render 86 trang | 1, 8, 19 | AVAILABLE |
| DOC-02 | TOC, danh mục hình và danh mục bảng | Front matter | 178/178 navigation target được Word phân trang; TOC/danh mục khớp page map | 8, 18–19 | AVAILABLE |
| DOC-03 | Hình/bảng có caption theo chương | Toàn tài liệu | 22 hình, 21 bảng trong manuscript Phase 18; hash/cross-reference verifier | 1, 7–8, 17–18 | AVAILABLE |
| DOC-04 | Bảng dữ liệu ưu tiên native Word table | Toàn tài liệu | 21 bảng nội dung là native Word table, có header lặp | 1, 8, 18–19 | AVAILABLE |
| DOC-05 | Trích dẫn học thuật và bibliography nhất quán | Chương 1–5; Tài liệu tham khảo | 57 entry; citation-key audit không thiếu/orphan | 1, 7, 11, 17–18 | AVAILABLE |
| DOC-06 | Render và kiểm tra 100% trang | QA release | Bản mở rộng 86/86 trang đã render và kiểm tra trực quan; `visual_qa.json` PASS | 8–9, 19 | AVAILABLE |
| DOC-07 | Thông tin bìa đầy đủ | Bìa và trang tên | Metadata trích từ DOCX mẫu; cover/title pages | 8 | AVAILABLE |
| DOC-08 | Không lộ đường dẫn máy hoặc token nội bộ | Toàn tài liệu | content scan 20/20 PASS trong `report_validation.json` | 8–9 | AVAILABLE |

## 5. Các ngoại lệ được quản lý

- License của hai dataset Kaggle `diabetes-health-indicators-dataset` và `vietnam-housing-dataset-2024` chưa xác minh được từ metadata chính thức có thể truy cập ở Phase 1. Registry ghi `UNVERIFIED`, không suy đoán.
- License GPL-3.0 của Synthetic E-Commerce Behavior lấy từ README đi kèm bản dữ liệu local; trang Kaggle là URL nguồn nhưng metadata license chưa được crawler xác nhận độc lập.
- AAPL là snapshot tải qua Yahoo Finance/yfinance: giấy phép Apache-2.0 của `yfinance` chỉ áp dụng cho phần mềm, không phải quyền tái phân phối dữ liệu thị trường. Báo cáo chỉ dùng số liệu tổng hợp/mẫu tối thiểu và không đóng gói lại toàn bộ CSV.
- Public cloud deployment cần credential nên không phải điều kiện chặn; local deployment và hướng dẫn tái lập là bắt buộc.
