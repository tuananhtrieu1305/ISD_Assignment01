# Ma trận truy vết yêu cầu tiểu luận

Ngày khóa: 2026-10-05  
Nguồn yêu cầu: nội dung giảng viên do người dùng cung cấp.  
Quy ước trạng thái: `LOCKED` = đã khóa thiết kế; `AVAILABLE` = đã có bằng chứng nguồn; `PLANNED` = sẽ tạo ở phase sau; `PENDING_INPUT` = cần thông tin/quyền từ người dùng; `N/A` = không áp dụng.

## 1. Yêu cầu cấu trúc và dung lượng

| ID | Yêu cầu | Vị trí trong outline | Artifact/bằng chứng | Phase | Trạng thái |
|---|---|---|---|---:|---|
| STR-01 | Mở đầu dài 3–4 trang | Mở đầu, mục 0.1–0.4 | DOCX trang 9–12; `report_validation.json` | 2, 8 | AVAILABLE |
| STR-02 | Chương 1: Lịch sử phát triển AI, 8 trang | Chương 1, mục 1.1–1.6 | DOCX trang 13–20; `report_validation.json` | 2, 8 | AVAILABLE |
| STR-03 | Chương 2: ML cơ bản, 10–15 trang | Chương 2, mục 2.1–2.8 | DOCX trang 21–34; artifact Chương 2 | 3, 8 | AVAILABLE |
| STR-04 | Chương 3: CNN, 10–15 trang | Chương 3, mục 3.1–3.8 | DOCX trang 35–48; artifact Chương 3 | 4, 8 | AVAILABLE |
| STR-05 | Chương 4: RNN, 10–15 trang | Chương 4, mục 4.1–4.8 | DOCX trang 49–62; artifact Chương 4 | 5, 8 | AVAILABLE |
| STR-06 | Có phần triển khai mô hình | Phần 5, mục 5.1–5.6 | `deployment/`; `report/sections/05_trien_khai.md`; 2 ảnh chụp UI | 6 | AVAILABLE |
| STR-07 | Có kết luận và tài liệu tham khảo | Kết luận; Tài liệu tham khảo | `report/manuscript.md`; `report/references_ordered.md`; `bibliography.bib` | 7 | AVAILABLE |
| STR-08 | Sản phẩm cuối là một DOCX hoàn chỉnh | Toàn tài liệu | `report/Tieu_luan_AI_ML_CNN_RNN.docx`; `report/build_log.json` | 8–9 | AVAILABLE |

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

## 4. Yêu cầu triển khai, trình bày và QA

| ID | Yêu cầu | Vị trí trong outline | Artifact/bằng chứng | Phase | Trạng thái |
|---|---|---|---|---:|---|
| DEP-01 | Ứng dụng inference chạy local | 5.1–5.5 | `deployment/app/`; 12 test; Docker smoke test | 6 | AVAILABLE |
| DEP-02 | Có use case đại diện ML/CNN/RNN | 5.2–5.4 | Tabular diabetes; EuroSAT image; customer/AAPL sequence; demo API | 6 | AVAILABLE |
| DEP-03 | Có schema validation, model hash và health check | 5.5 | `schemas.py`; `model_registry.json`; `/health`; verifier | 6 | AVAILABLE |
| DEP-04 | Có cảnh báo y khoa/tài chính | 5.2; 5.4 | UI, API response, screenshot và section triển khai | 6 | AVAILABLE |
| DOC-01 | Theo phong cách DOCX mẫu | Toàn tài liệu | `style_spec.md`; DOCX render 73 trang | 1, 8 | AVAILABLE |
| DOC-02 | TOC, danh mục hình và danh mục bảng | Front matter | 159 bookmark/hyperlink, 0 mục thiếu; `report_validation.json` | 8 | AVAILABLE |
| DOC-03 | Hình/bảng có caption theo chương | Toàn tài liệu | 18 figure, 16 table và cross-reference trong `report_manifest.json` | 1, 7–8 | AVAILABLE |
| DOC-04 | Bảng dữ liệu ưu tiên native Word table | Toàn tài liệu | 16 bảng nội dung native + 3 code block native; `report_validation.json` | 1, 8 | AVAILABLE |
| DOC-05 | Trích dẫn học thuật và bibliography nhất quán | Chương 1–4; Tài liệu tham khảo | `bibliography.bib`; citation-key audit | 1, 7 | AVAILABLE |
| DOC-06 | Render và kiểm tra 100% trang | QA release | artifact-tool render; Word PDF 73/73 trang; `report_validation.json` | 8–9 | AVAILABLE |
| DOC-07 | Thông tin bìa đầy đủ | Bìa và trang tên | Metadata trích từ DOCX mẫu; cover/title pages | 8 | AVAILABLE |
| DOC-08 | Không lộ đường dẫn máy hoặc token nội bộ | Toàn tài liệu | content scan 20/20 PASS trong `report_validation.json` | 8–9 | AVAILABLE |

## 5. Các ngoại lệ được quản lý

- License của hai dataset Kaggle `diabetes-health-indicators-dataset` và `vietnam-housing-dataset-2024` chưa xác minh được từ metadata chính thức có thể truy cập ở Phase 1. Registry ghi `UNVERIFIED`, không suy đoán.
- License GPL-3.0 của Synthetic E-Commerce Behavior lấy từ README đi kèm bản dữ liệu local; trang Kaggle là URL nguồn nhưng metadata license chưa được crawler xác nhận độc lập.
- AAPL là snapshot tải qua Yahoo Finance/yfinance: giấy phép Apache-2.0 của `yfinance` chỉ áp dụng cho phần mềm, không phải quyền tái phân phối dữ liệu thị trường. Báo cáo chỉ dùng số liệu tổng hợp/mẫu tối thiểu và không đóng gói lại toàn bộ CSV.
- Public cloud deployment cần credential nên không phải điều kiện chặn; local deployment và hướng dẫn tái lập là bắt buộc.
