# KẾ HOẠCH THỰC THI TIỂU LUẬN AI/ML/CNN/RNN

> **Vai trò của file này:** Đây là nguồn sự thật duy nhất (single source of truth) để thực hiện tiểu luận. Khi người dùng gõ **`làm phase N`**, trợ lý phải đọc toàn bộ file này, đọc các `AGENTS.md` liên quan, kiểm tra trạng thái và tự thực hiện đầy đủ phase tương ứng cho đến khi đạt tiêu chí nghiệm thu hoặc gặp một blocker thực sự cần người dùng quyết định.

## 0. Thông tin quản trị

| Trường | Giá trị |
|---|---|
| Tên dự án | Tiểu luận môn học: Lịch sử AI, ML cơ bản, CNN và RNN |
| Workspace | `C:\DATA\assign` |
| File kế hoạch | `C:\DATA\assign\TIEU_LUAN_AI_EXECUTION_PLAN.md` |
| Ngày lập kế hoạch | 2026-10-05 |
| Ngôn ngữ báo cáo | Tiếng Việt; giữ thuật ngữ kỹ thuật tiếng Anh khi tự nhiên |
| Sản phẩm cuối | Một file DOCX tiểu luận hoàn chỉnh, đã render và kiểm tra từng trang |
| Thư mục làm việc mới | `term_paper/` |
| Nguyên tắc bảo toàn | Không sửa dữ liệu raw; không ghi đè notebook/model/report hiện có trong `pipeline/`, `A05/`, `A06/` |

## 1. Cách xử lý lệnh `làm phase N`

Khi nhận lệnh dạng `làm phase N`, trợ lý phải:

1. Đọc toàn bộ file này và các `AGENTS.md` áp dụng cho đường dẫn sắp thao tác.
2. Kiểm tra bảng trạng thái phase và nhật ký thực thi ở cuối file.
3. Kiểm tra dependency của phase. Nếu dependency chưa hoàn thành nhưng có thể hoàn tất an toàn như một bước chuẩn bị trực tiếp, thực hiện bước chuẩn bị đó; không tự ý mở rộng sang một phase độc lập khác.
4. Kiểm tra trạng thái Git và bảo toàn mọi thay đổi có sẵn của người dùng.
5. Thực hiện phase bằng dữ liệu/artifact thật. Không bịa metric, hình, trích dẫn, thời gian chạy hoặc kết quả kiểm thử.
6. Chạy kiểm tra tương ứng với rủi ro của phase.
7. Cập nhật ngay trong file này:
   - `Status` của phase;
   - ngày thực hiện;
   - file đã tạo hoặc sửa;
   - lệnh kiểm tra và kết quả;
   - quyết định, sai lệch và blocker còn lại.
8. Chỉ đánh dấu `COMPLETE` khi toàn bộ acceptance criteria của phase đạt. Nếu chưa đạt, để `IN_PROGRESS`; chỉ dùng `BLOCKED` khi không thể tiếp tục nếu thiếu quyết định/quyền truy cập từ người dùng.
9. Trả lời người dùng bằng tóm tắt kết quả, đường dẫn file và các kiểm tra đã chạy.

### Quy tắc tự chủ

- Không hỏi lại các lựa chọn đã được quyết định trong file này.
- Có thể tự chọn chi tiết triển khai nhỏ nếu không làm thay đổi mục tiêu, dataset, giao thức so sánh hoặc cấu trúc báo cáo.
- Phải hỏi người dùng nếu cần thông tin cá nhân chưa có trên bìa, credential để publish public, chi phí dịch vụ, hoặc một thay đổi lớn về phạm vi.
- Nếu cloud deployment chưa được cấp credential, hoàn thành local deployment và Docker/package trước; ghi cloud publish là `OPTIONAL_PENDING_CREDENTIALS`, không chặn các phần còn lại.
- Nếu package bắt buộc bị thiếu, không tự cài đặt trái với quy tắc environment hiện hữu. Ghi rõ package và xin quyền khi thực sự cần.

## 2. Yêu cầu gốc và cách diễn giải đã khóa

### 2.1. Yêu cầu cấu trúc

- Mở đầu: 3–4 trang.
- Chương 1: Lịch sử phát triển AI, 8 trang.
- Chương 2: Các kỹ thuật Machine Learning cơ bản, 10–15 trang.
- Chương 3: Convolutional Neural Network, 10–15 trang.
- Chương 4: Recurrent Neural Network, 10–15 trang.
- Có phần deployment.

### 2.2. Yêu cầu thực nghiệm

- Chương 2–4, mỗi chương sử dụng 2–3 dataset.
- Với mỗi dataset phải có tối thiểu:
  - tên và link nguồn;
  - license/citation nếu tìm được;
  - kích cỡ file và kích cỡ logic (rows/images/samples, features, classes);
  - một số mẫu input/output;
  - phân bố target/class hoặc phân bố dữ liệu chính;
  - nhận xét và hạn chế.
- Chương 2–4 đều phải có code tương ứng:
  - scratch;
  - Keras;
  - PyTorch.
- Ba implementation phải được đánh giá trên cùng dữ liệu và cùng split trong track so sánh framework.
- Có bảng so sánh metric, parameter count, training time, inference time và nhận xét.

### 2.3. Diễn giải điểm mơ hồ

Mặc định áp dụng yêu cầu “mỗi chương có 2–3 dataset” cho **Chương 2–4**, vì Chương 1 là lịch sử AI và không phải chương thực nghiệm. Chương 1 có thể dùng các benchmark lịch sử như Iris, MNIST hoặc ImageNet trong timeline/case box, nhưng không bắt buộc huấn luyện 2–3 dataset.

Nếu sau này người dùng cung cấp xác nhận khác từ giảng viên, cập nhật mục này và requirement matrix trước khi viết DOCX cuối.

## 3. Nguồn hiện có và trạng thái ban đầu

### 3.1. Chương 2 — ML cơ bản

Nguồn:

- `pipeline/diabetes_pipeline.ipynb`
- `pipeline/house_price_pipeline.ipynb`
- `pipeline/customer_behavior_pipeline.ipynb`
- `pipeline/diabetes/`
- `pipeline/house_price/`
- `pipeline/customer_behavior/`

Hiện có:

- Ba dataset và ba bài toán.
- EDA, preprocessing, leakage analysis, sklearn baselines.
- NumPy DNN scratch, model artifacts, schema, demo input và demo prediction.

Còn thiếu:

- Matched Keras MLP và PyTorch MLP.
- Registry link/license/citation đầy đủ.
- Bảng so sánh ba implementation trên cùng split.
- Deployment thực sự.

### 3.2. Chương 3 — CNN

Nguồn:

- `A05/notebooks/01_CNN_Fundamentals.ipynb`
- `A05/notebooks/02_EuroSAT_CNN.ipynb`
- `A05/notebooks/03_Oxford_Pets_CNN.ipynb`
- `A05/notebooks/04_CDC_Diabetes_CNN.ipynb`
- `A05/notebooks/05_Model_Comparison.ipynb`
- `A05/results/`
- `A05/report/A05_Assignment_Report.docx`

Hiện có:

- EuroSAT, Oxford-IIIT Pet, CDC Diabetes.
- Basic/AlexNet-inspired/VGG-inspired/ResNet-inspired bằng Keras/TensorFlow.
- Metrics, checkpoints, figures và report riêng.

Còn thiếu:

- Trainable CNN scratch có backward/update, không chỉ forward minh họa.
- Matched PyTorch CNN.
- Framework comparison trên cùng subset/split.
- Dataset URLs/citations trong nội dung cuối.
- Rút nội dung từ report riêng xuống 10–15 trang.

Lưu ý diễn giải:

- “From scratch” của A05 hiện có nghĩa là random initialization, không dùng pretrained weights. Nó không thay thế implementation NumPy scratch mà yêu cầu tiểu luận cần bổ sung.
- Kết quả collapse hoặc gần random phải được giữ nguyên và giải thích, không sửa số liệu để tạo kết luận đẹp.

### 3.3. Chương 4 — RNN

Nguồn:

- `A06/notebooks/01_RNN_Fundamentals.ipynb` đến `08_Framework_Comparison.ipynb`
- `A06/src/`
- `A06/results/`
- `A06/report/A06_Assignment_Report.docx`
- File style tham khảo do người dùng gửi: `C:\Users\anhca\Documents\Intel_sys_dev\A06_Assignment_Report.docx`

Hiện có:

- UCI Online Retail II và AAPL 2015–2025.
- PyTorch Vanilla RNN và Keras SimpleRNN.
- Shared processed arrays, chronological splits, leakage controls, metrics, predictions và tests.

Còn thiếu:

- NumPy Vanilla RNN scratch có BPTT và training.
- So sánh đủ scratch/Keras/PyTorch.
- Dataset URLs/citations đầy đủ.
- Rút nội dung xuống 10–15 trang.

### 3.4. DOCX mẫu

Đặc điểm style đã quan sát:

- A4 portrait; lề trái rộng hơn lề phải.
- Times New Roman, body khoảng 10.5–11.5 pt, giãn dòng khoảng 1.5.
- Heading màu xanh đậm `#17365D`; heading cấp hai `#2F75B5`.
- Header/footer nhỏ, có tiêu đề assignment và số trang.
- Có bìa trang trí, trang tiêu đề, mục lục, danh mục hình và danh mục bảng.
- Văn phong dựa trên bằng chứng, nêu rõ protocol, kết quả và hạn chế.
- Code dùng font monospace; hình/bảng có caption đánh số theo chương.

Điểm cải tiến cho DOCX cuối:

- Dùng native Word tables thay cho ảnh chụp bảng khi có thể.
- Có tài liệu tham khảo học thuật đầy đủ.
- Không chèn toàn bộ notebook vào thân bài.
- Mọi bảng/hình phải có nguồn artifact và nhận xét.

## 4. Cấu trúc thư mục đích

Mọi nội dung mới được tạo trong `term_paper/`:

```text
term_paper/
├── README.md
├── config/
│   ├── requirements_matrix.md
│   ├── experiment_contract.md
│   ├── report_outline.md
│   └── style_spec.md
├── sources/
│   ├── source_registry.csv
│   ├── bibliography.bib
│   └── dataset_cards/
├── notebooks/
│   ├── ch2_ml_framework_comparison.ipynb
│   ├── ch3_cnn_framework_comparison.ipynb
│   └── ch4_rnn_framework_comparison.ipynb
├── src/
│   ├── common/
│   ├── scratch/
│   ├── keras_impl/
│   └── pytorch_impl/
├── tests/
├── artifacts/
│   ├── manifests/
│   ├── models/
│   ├── metrics/
│   ├── predictions/
│   └── figures/
├── deployment/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
└── report/
    ├── manuscript.md
    ├── build_report.py
    ├── assets/
    ├── renders/
    └── Tieu_luan_AI_ML_CNN_RNN.docx
```

Không bắt buộc tạo tất cả thư mục ngay ở Phase 0; chỉ tạo khi phase cần đến.

## 5. Hợp đồng thực nghiệm chung

### 5.1. Tính tái lập

- Seed chính: `42`.
- Mọi split phải được lưu thành artifact hoặc được định danh bằng index/key/date.
- Preprocessor/scaler chỉ fit trên TRAIN.
- Validation dùng để chọn hyperparameter, threshold và checkpoint.
- TEST chỉ dùng sau khi cấu hình đã khóa.
- Không thay dữ liệu raw bằng nguồn online khác nếu file hiện có đọc được.
- Mọi metric trong báo cáo phải được tính lại được từ prediction artifact.

### 5.2. So sánh framework

Trong mỗi track scratch/Keras/PyTorch:

- Giữ cùng input features, target, split và preprocessing.
- Giữ cùng topology logic, activation, loss, batch size, learning rate, epoch budget và early-stopping rule trong khả năng API cho phép.
- Ghi rõ khác biệt không tránh được giữa framework.
- Không dùng số dòng code hoặc runtime CPU đơn lẻ để kết luận framework tốt hơn một cách phổ quát.
- Bắt buộc báo cáo parameter count, epochs thực chạy, training duration, inference duration và metric nhiệm vụ.

### 5.3. Chính sách số lần chạy

- Một clean run với seed 42 là bắt buộc.
- Nếu một full matched run mất không quá 20 phút CPU, chạy thêm seed 52 và 62, báo cáo mean ± standard deviation.
- Nếu vượt ngưỡng, giữ seed 42 và ghi rõ đây là single-seed controlled experiment.

### 5.4. Metric

Classification:

- Accuracy.
- Precision, Recall, F1; ưu tiên macro-F1 cho multiclass/imbalance.
- ROC-AUC khi có ý nghĩa.
- Confusion matrix.
- Per-class recall đối với class quan trọng.

Regression:

- MAE.
- RMSE.
- R².
- Baseline phù hợp.
- Actual-vs-predicted plot và residual/error summary.

## 6. Thiết kế nội dung và page budget

| Phần | Ngân sách |
|---|---:|
| Front matter | 5–6 trang |
| Mở đầu | 3–4 trang |
| Chương 1 — Lịch sử AI | 8 trang |
| Chương 2 — ML cơ bản | 12–14 trang |
| Chương 3 — CNN | 12–14 trang |
| Chương 4 — RNN | 12–14 trang |
| Phần triển khai | 3–4 trang |
| Kết luận | 1–2 trang |
| Tài liệu tham khảo | 2–3 trang |
| Phụ lục | 5–10 trang, không tính vào thân bài nếu quy định cho phép |

Mục tiêu: khoảng 54–63 trang nội dung chính; khoảng 59–69 trang khi tính front matter, chưa tính phụ lục dài.

## 7. Bảng trạng thái phase

| Phase | Tên | Dependency | Status |
|---:|---|---|---|
| 0 | Khởi tạo và đóng băng bằng chứng | Không | COMPLETE |
| 1 | Requirement matrix, nguồn, outline và style | Phase 0 | COMPLETE |
| 2 | Mở đầu và Chương 1 — Lịch sử AI | Phase 1 | COMPLETE |
| 3 | Hoàn thiện Chương 2 — ML cơ bản | Phase 1 | COMPLETE |
| 4 | Hoàn thiện Chương 3 — CNN | Phase 1; nên sau Phase 3 để tái dùng framework | COMPLETE |
| 5 | Hoàn thiện Chương 4 — RNN | Phase 1; có thể dùng utility từ Phase 3 | COMPLETE |
| 6 | Deployment tích hợp | Phase 3–5 | COMPLETE |
| 7 | Tổng hợp và viết manuscript | Phase 2–6 | COMPLETE |
| 8 | Dựng DOCX hoàn chỉnh | Phase 7 | COMPLETE |
| 9 | QA, render và release | Phase 8 | COMPLETE |

---

# PHASE 0 — KHỞI TẠO VÀ ĐÓNG BĂNG BẰNG CHỨNG

## Mục tiêu

Tạo vùng làm việc độc lập và inventory có thể kiểm chứng trước khi chạy thêm thí nghiệm.

## Công việc bắt buộc

1. Đọc trạng thái Git; không sửa hoặc hoàn tác thay đổi có sẵn.
2. Đọc `A05/AGENTS.md`, `A06/PROJECT_SPEC.md`, `A06/CURRENT_STATE.md` và các README liên quan.
3. Tạo cấu trúc tối thiểu `term_paper/`.
4. Lập inventory cho:
   - notebooks;
   - raw/processed datasets;
   - checkpoints;
   - metrics/predictions;
   - figures;
   - reports.
5. Tính SHA-256 cho các artifact nguồn quan trọng; với kho ảnh lớn, hash manifest hoặc file danh sách thay vì tạo bản sao.
6. Kiểm tra notebook metadata: cell count, execution count, error outputs, imports và framework.
7. Tạo mapping từ từng kết luận hiện có tới file metric/figure nguồn.
8. Ghi nhận các inconsistency, bao gồm notebook có output nhưng execution count trống/không liên tục.

## Deliverables

- `term_paper/README.md`
- `term_paper/artifacts/manifests/source_inventory.json`
- `term_paper/artifacts/manifests/source_hashes.csv`
- `term_paper/artifacts/manifests/notebook_audit.csv`
- `term_paper/artifacts/manifests/gap_analysis.md`

## Acceptance criteria

- Không file nguồn nào trong `pipeline/`, `A05/`, `A06/` bị sửa.
- Inventory ghi đủ ba chương thực nghiệm.
- Hash và kích cỡ artifact quan trọng được lưu.
- Mọi gap trong yêu cầu thầy được map vào ít nhất một phase sau.

---

# PHASE 1 — REQUIREMENT MATRIX, NGUỒN, OUTLINE VÀ STYLE

## Mục tiêu

Khóa cấu trúc báo cáo, nguồn trích dẫn, dataset cards và quy chuẩn trình bày trước khi huấn luyện thêm.

## Công việc bắt buộc

1. Tạo requirement traceability matrix: yêu cầu → chương/mục → artifact → trạng thái.
2. Tạo outline đến cấp heading 3 cho toàn bộ DOCX.
3. Tạo source registry cho mọi dataset:
   - tên chuẩn;
   - URL nguồn ưu tiên official/primary;
   - ngày truy cập;
   - license;
   - local path;
   - file size và logical size;
   - citation.
4. Kiểm tra và ghi lại chênh lệch giữa README và dữ liệu thực tế.
5. Tạo bibliography ban đầu cho lịch sử AI và lý thuyết ML/CNN/RNN; ưu tiên paper gốc, repository chính thức và tài liệu framework chính thức.
6. Chốt style specification dựa trên DOCX mẫu:
   - page size, margins;
   - font ladder;
   - heading colors;
   - caption/numbering;
   - table style;
   - code style;
   - header/footer;
   - citation style.
7. Chốt image/table budget cho từng chương để không vượt số trang.

## Deliverables

- `term_paper/config/requirements_matrix.md`
- `term_paper/config/report_outline.md`
- `term_paper/config/style_spec.md`
- `term_paper/config/experiment_contract.md`
- `term_paper/sources/source_registry.csv`
- `term_paper/sources/bibliography.bib`
- `term_paper/sources/dataset_cards/*.md`

## Acceptance criteria

- Mọi yêu cầu của giảng viên có vị trí rõ trong outline.
- Mỗi dataset có URL và local provenance hoặc ghi rõ lý do chưa có.
- Citation lịch sử AI dùng nguồn học thuật/primary, không dựa vào blog tổng hợp làm nguồn chính.
- Page budget cộng lại phù hợp mục 6.

---

# PHASE 2 — MỞ ĐẦU VÀ CHƯƠNG 1: LỊCH SỬ PHÁT TRIỂN AI

## Mục tiêu

Viết phần nền tảng học thuật độc lập với các notebook thực nghiệm.

## Nội dung Mở đầu

1. Lý do chọn đề tài.
2. Mục tiêu tổng quát và mục tiêu cụ thể.
3. Câu hỏi nghiên cứu:
   - Mức độ khác nhau giữa scratch, Keras và PyTorch khi giữ cùng protocol?
   - Kiến trúc nào phù hợp với loại dữ liệu nào?
   - Kết quả thực nghiệm có thể đưa vào một ứng dụng inference như thế nào?
4. Phạm vi, dataset, giới hạn phần cứng.
5. Phương pháp nghiên cứu và cấu trúc tiểu luận.

## Nội dung Chương 1

1. Neuron nhân tạo và nền tảng trước 1956.
2. Turing, Dartmouth và sự hình thành AI.
3. Symbolic AI, search và expert systems.
4. Perceptron, giới hạn ban đầu và AI winters.
5. Backpropagation và statistical machine learning.
6. Deep learning revival, GPU, dữ liệu lớn và AlexNet.
7. RNN/LSTM, attention, Transformer.
8. Foundation models và Generative AI.
9. Timeline tổng hợp và liên hệ sang Chương 2–4.

## Deliverables

- `term_paper/report/sections/00_mo_dau.md`
- `term_paper/report/sections/01_lich_su_ai.md`
- Timeline/diagram nguồn trong `term_paper/report/assets/ch1/`

## Acceptance criteria

- Mở đầu tương đương 3–4 trang theo style spec.
- Chương 1 tương đương khoảng 8 trang.
- Mọi mốc/lời khẳng định lịch sử quan trọng có citation.
- Không chép dài nguyên văn nguồn.
- Có đoạn chuyển tiếp hợp lý sang ML, CNN và RNN.

---

# PHASE 3 — HOÀN THIỆN CHƯƠNG 2: ML CƠ BẢN

## Mục tiêu

Tận dụng ba pipeline hiện có, bổ sung matched MLP bằng NumPy/Keras/PyTorch và tạo chương 10–15 trang.

## Dataset

1. CDC Diabetes binary classification.
2. Vietnam House Price regression.
3. Synthetic E-Commerce Customer Behavior churn classification.

## Track A — Classical ML baselines

Tái sử dụng kết quả thật hiện có cho Logistic/Linear Regression, KNN, Decision Tree, Random Forest, Gradient Boosting, SVM và các baseline phù hợp. Không retrain nếu artifact đủ kiểm chứng; nếu cần chạy lại, giữ split và preprocessing hiện có.

## Track B — Matched MLP framework comparison

Triển khai cùng topology logic:

- NumPy scratch: forward, loss, backpropagation, optimizer/update, predict, save/load.
- Keras: Dense MLP tương ứng.
- PyTorch: `nn.Sequential`/module tương ứng.

Protocol:

- Dùng cùng processed arrays và split.
- Topology mặc định: input → Dense 64 + ReLU → Dense 32 + ReLU → task output; thay đổi chỉ khi shape/task bắt buộc và phải ghi trong contract.
- Binary classification: sigmoid/BCE.
- Regression: linear output/MSE; báo metric ở đơn vị thật.
- Cùng batch size, learning-rate candidates, epoch budget và early stopping.
- Chọn checkpoint bằng validation.

## Nội dung chương

1. Khái niệm supervised learning và workflow.
2. Các kỹ thuật ML cơ bản và công thức chính.
3. Ba dataset cards.
4. Preprocessing và leakage controls.
5. Code scratch/Keras/PyTorch.
6. Bảng kết quả và biểu đồ.
7. Phân tích ưu/nhược điểm, failure cases và giới hạn.

## Deliverables

- `term_paper/src/scratch/mlp.py`
- `term_paper/src/keras_impl/mlp.py`
- `term_paper/src/pytorch_impl/mlp.py`
- `term_paper/notebooks/ch2_ml_framework_comparison.ipynb`
- `term_paper/tests/test_ch2_*.py`
- `term_paper/artifacts/metrics/ch2_*.csv`
- `term_paper/artifacts/predictions/ch2_*`
- `term_paper/artifacts/figures/ch2/`
- `term_paper/report/sections/02_ml_co_ban.md`

## Acceptance criteria

- Ba implementation train và infer được trên cả 3 dataset.
- Metric được tính từ prediction artifact, không nhập tay.
- Cùng split và preprocessing được xác nhận bằng hash/key.
- Có kiểm thử shape, loss giảm trên toy data, save/load và metric reproduction.
- Chương viết tương đương 12–14 trang.

---

# PHASE 4 — HOÀN THIỆN CHƯƠNG 3: CNN

## Mục tiêu

Bổ sung scratch và PyTorch CNN, giữ kết quả Keras hiện có như bằng chứng, rồi cô đọng thành chương 10–15 trang.

## Dataset

1. EuroSAT.
2. Oxford-IIIT Pet.
3. CDC Diabetes Health Indicators.

## Track A — Matched framework comparison bắt buộc

Đánh giá scratch/Keras/PyTorch trên ít nhất hai dataset:

- EuroSAT: Conv2D image classification.
- CDC Diabetes: Conv1D adaptation.

Oxford-IIIT Pet là dataset thứ ba và case study mở rộng; nếu runtime scratch cho phép trong operational bound, chạy cùng matched track trên fixed stratified subset. Nếu không, dùng kết quả Keras hiện có và ghi rõ phạm vi.

### Kiến trúc mặc định

EuroSAT:

- Conv2D 8 filters, kernel 3×3, ReLU.
- MaxPool 2×2.
- Conv2D 16 filters, kernel 3×3, ReLU.
- Global average pooling hoặc flatten có kiểm soát.
- Dense classification output.

CDC Diabetes:

- Conv1D adaptation có progression tương đương.
- Giữ nguyên thứ tự 21 feature và nêu rõ adjacency là nhân tạo.

NumPy scratch phải có forward và backward cho các layer cần thiết, optimizer/update và unit test numerical-gradient trên tensor nhỏ.

### Kiểm soát CPU

- Dùng fixed stratified benchmark subset giống nhau cho cả ba framework nếu full data làm scratch không khả thi.
- Subset indices phải được lưu.
- Không so model scratch trên subset với model framework trên full data trong cùng bảng chính.
- Kết quả full-data Keras A05 đặt ở bảng/case study riêng.

## Track B — Keras architecture ablation

Tái sử dụng Basic/AlexNet-inspired/VGG-inspired/ResNet-inspired từ A05. Ghi rõ đây là controlled common-protocol comparison, không phải best-achievable benchmark cho từng family.

## Deliverables

- `term_paper/src/scratch/cnn.py`
- `term_paper/src/keras_impl/cnn.py`
- `term_paper/src/pytorch_impl/cnn.py`
- `term_paper/notebooks/ch3_cnn_framework_comparison.ipynb`
- `term_paper/tests/test_ch3_*.py`
- Saved subset indices/splits.
- `term_paper/artifacts/metrics/ch3_*.csv`
- `term_paper/artifacts/predictions/ch3_*`
- `term_paper/artifacts/figures/ch3/`
- `term_paper/report/sections/03_cnn.md`

## Acceptance criteria

- Scratch CNN vượt qua numerical-gradient/toy overfit test.
- Ba framework dùng cùng benchmark samples.
- Có kết quả ít nhất trên EuroSAT và CDC Diabetes.
- Không che giấu collapse/near-random results trong A05.
- Chương viết tương đương 12–14 trang.

---

# PHASE 5 — HOÀN THIỆN CHƯƠNG 4: RNN

## Mục tiêu

Thêm NumPy Vanilla RNN scratch với BPTT và so sánh công bằng với Keras/PyTorch trên hai dataset hiện có.

## Dataset

1. UCI Online Retail II: customer-week binary classification.
2. AAPL 2015–2025: next-trading-day Close regression.

## Matched Vanilla RNN

- NumPy scratch: recurrent cell, many-to-one forward, BPTT, gradient clipping, optimizer, save/load.
- Keras: `SimpleRNN` + Dense.
- PyTorch: `nn.RNN` + Linear.
- Hidden size mặc định cho controlled benchmark: 32, trừ khi Phase 5 audit chứng minh một giá trị khác cần thiết.
- Sequence length giữ nguyên: customer 8 tuần, stock 30 phiên.
- Input features, processed arrays và chronological splits giữ nguyên A06.
- Customer dùng BCE và threshold được khóa/chọn bằng validation.
- Stock dùng MSE trong training scale và metric ở USD sau inverse transform.
- Stock luôn so với naive last-Close baseline.

## Kiểm thử scratch RNN

- Forward shape test.
- Numerical-gradient test trên sequence nhỏ.
- Toy sequence overfit test.
- Gradient clipping test.
- Save/load parity.
- Prediction/metric reproduction.

## Deliverables

- `term_paper/src/scratch/rnn.py`
- `term_paper/src/keras_impl/rnn.py`
- `term_paper/src/pytorch_impl/rnn.py`
- `term_paper/notebooks/ch4_rnn_framework_comparison.ipynb`
- `term_paper/tests/test_ch4_*.py`
- `term_paper/artifacts/metrics/ch4_*.csv`
- `term_paper/artifacts/predictions/ch4_*`
- `term_paper/artifacts/figures/ch4/`
- `term_paper/report/sections/04_rnn.md`

## Acceptance criteria

- Scratch RNN thực sự train bằng BPTT, không chỉ forward demo.
- Ba implementation dùng cùng TEST keys/dates/labels.
- Customer có confusion matrix và ROC/PR analysis phù hợp imbalance.
- Stock có naive baseline và không đưa khuyến nghị đầu tư.
- Chương viết tương đương 12–14 trang.

---

# PHASE 6 — DEPLOYMENT TÍCH HỢP

## Mục tiêu

Tạo một ứng dụng inference chạy được, trình bày rõ model provenance và giới hạn sử dụng.

## Phạm vi tối thiểu

Ứng dụng có ba tab/use case:

1. **Tabular ML:** nhập các health indicators và trả dự đoán diabetes risk; hiển thị cảnh báo “không phải chẩn đoán y khoa”.
2. **CNN:** upload ảnh EuroSAT, trả top classes và confidence.
3. **RNN:** upload sequence/CSV customer hoặc AAPL; với stock phải hiển thị cả RNN và naive baseline, kèm cảnh báo “không phải khuyến nghị đầu tư”.

## Lựa chọn công nghệ

1. Kiểm tra package hiện có.
2. Ưu tiên Streamlit cho UI học thuật nhanh và ảnh chụp báo cáo.
3. Nếu Streamlit không có nhưng FastAPI có, dùng FastAPI + HTML/JSON demo.
4. Nếu thiếu dependency bắt buộc, chuẩn bị source/requirements trước và xin phép cài đặt; không tự động phá environment hiện có.
5. Docker/local reproducible deployment là bắt buộc nếu toolchain hỗ trợ; public cloud là tùy chọn và cần credential của người dùng.

## Yêu cầu kỹ thuật

- Input schema validation.
- Model/preprocessor version và hash.
- `/health` hoặc health indicator tương đương.
- Demo input và deterministic response.
- Không log dữ liệu nhạy cảm.
- Friendly error cho sai shape/type.
- Smoke tests cho từng use case.

## Deliverables

- `term_paper/deployment/app/`
- `term_paper/deployment/tests/`
- `term_paper/deployment/requirements.txt`
- `term_paper/deployment/Dockerfile` nếu khả thi.
- `term_paper/deployment/README.md`
- Screenshots trong `term_paper/report/assets/deployment/`
- `term_paper/report/sections/05_trien_khai.md`

## Acceptance criteria

- App chạy local và dự đoán được ít nhất một mẫu cho từng chương thực nghiệm.
- Prediction khớp notebook/artifact trong tolerance hợp lý.
- Invalid input được từ chối có thông báo rõ.
- Có screenshot và quy trình chạy lại.
- Nếu chưa publish public do credential, local deployment vẫn được đánh dấu complete; cloud status ghi riêng.

---

# PHASE 7 — TỔNG HỢP VÀ VIẾT MANUSCRIPT

## Mục tiêu

Kết hợp toàn bộ section thành một bản thảo thống nhất, đúng page budget và truy vết được.

## Công việc bắt buộc

1. Ghép Mở đầu, Chương 1–4, deployment, kết luận và tài liệu tham khảo.
2. Chuẩn hóa thuật ngữ Việt–Anh.
3. Mỗi dataset dùng cùng template trình bày:
   - nguồn/link/license;
   - kích cỡ/schema;
   - output mẫu;
   - phân bố;
   - preprocessing;
   - nhận xét/hạn chế.
4. Mỗi bảng kết quả phải ghi metric, split, seed và source artifact.
5. Chỉ trích code ngắn 10–25 dòng; code đầy đủ trỏ tới notebook/repository.
6. Viết conclusion trung thực, không biến kết quả âm thành tuyên bố tích cực giả tạo.
7. Kiểm tra citation coverage, figure/table numbering và cross-reference plan.

## Deliverables

- `term_paper/report/manuscript.md`
- `term_paper/report/report_manifest.json`
- `term_paper/report/assets/` hoàn chỉnh.

## Acceptance criteria

- Không còn placeholder nội dung trừ thông tin bìa cần người dùng xác nhận.
- Page estimate nằm trong budget.
- Mọi con số có artifact nguồn.
- Mọi hình/bảng được nhắc đến trong text.
- Citation và bibliography không có orphan/missing entries.

---

# PHASE 8 — DỰNG DOCX HOÀN CHỈNH

## Mục tiêu

Tạo file DOCX cuối theo style mẫu nhưng cải thiện accessibility và khả năng chỉnh sửa.

## Công việc bắt buộc

1. Đọc đầy đủ skill/instruction về DOCX đang có trong môi trường.
2. Tạo build script có thể chạy lại.
3. Tạo:
   - cover và title page;
   - TOC;
   - list of figures/tables;
   - Heading 1–3;
   - captions và cross-references;
   - native tables;
   - code blocks;
   - header/footer và page numbers;
   - bibliography.
4. Giữ palette/font/layout của file mẫu.
5. Không chèn đường dẫn máy cục bộ vào nội dung người đọc nhìn thấy, trừ phụ lục tái lập khi cần.
6. Reopen và structural validation sau build.

## Deliverables

- `term_paper/report/build_report.py`
- `term_paper/report/Tieu_luan_AI_ML_CNN_RNN.docx`
- Build log/validation JSON.

## Acceptance criteria

- DOCX mở được và có đủ nội dung.
- Heading/TOC/caption numbering nhất quán.
- Native tables không bị cắt text.
- Không có tool token, placeholder hoặc citation nội bộ bị lộ.
- File build có thể tái tạo từ manuscript và assets.

---

# PHASE 9 — QA, RENDER VÀ RELEASE

## Mục tiêu

Kiểm tra nội dung, hình thức, accessibility và phát hành duy nhất file DOCX cuối.

## Công việc bắt buộc

1. Render DOCX bằng `render_docx.py --renderer artifact-tool`.
2. Kiểm tra **mọi trang** ở độ phân giải đủ đọc.
3. Sửa và render lại cho đến khi không còn:
   - clipping/overlap;
   - bảng vỡ;
   - ảnh/caption tách bất hợp lý;
   - trang trắng không chủ ý;
   - font/glyph lỗi;
   - heading orphan;
   - mật độ trang quá dày hoặc khoảng trắng lớn bất thường.
4. Chạy accessibility audit.
5. Kiểm tra page budget theo từng phần.
6. Đối chiếu ngẫu nhiên và tự động metric trong DOCX với CSV/JSON nguồn.
7. Kiểm tra link/citation và mục lục.
8. Scrub metadata riêng tư không cần thiết nếu phù hợp.
9. Chỉ giao file DOCX cuối; PNG/PDF render là QA nội bộ trừ khi người dùng yêu cầu.

## Deliverables

- `term_paper/report/Tieu_luan_AI_ML_CNN_RNN.docx` bản release.
- Internal QA logs trong `term_paper/report/qa/`.

## Acceptance criteria

- 100% trang đã được kiểm tra trực quan.
- Không lỗi layout nhìn thấy.
- Không finding accessibility mức high/medium chưa xử lý hoặc giải thích.
- Mọi yêu cầu trong `requirements_matrix.md` ở trạng thái satisfied hoặc documented exception được người dùng chấp nhận.
- Final DOCX là artifact duy nhất được gửi cho người dùng.

---

## 8. Definition of Done toàn dự án

Dự án chỉ hoàn thành khi:

- Có một DOCX duy nhất bao gồm Mở đầu, Chương 1–4, deployment, kết luận và tài liệu tham khảo.
- Mở đầu và mỗi chương nằm trong page budget hợp lý.
- Chương 2–4 có 2–3 dataset với link, kích cỡ, mẫu, phân bố và nhận xét.
- Scratch/Keras/PyTorch được cài đặt và đánh giá theo matched protocol.
- Mọi metric, bảng và figure truy ngược về artifact thật.
- Deployment chạy được và có kiểm thử.
- DOCX đã qua render → inspect → fix → rerender.
- Không sửa hoặc làm mất các assignment gốc.

## 9. Nhật ký thực thi

Mỗi phase sau khi chạy phải thêm một entry theo mẫu:

```markdown
### YYYY-MM-DD — Phase N — STATUS

- Phạm vi đã làm:
- File tạo/sửa:
- Lệnh/test đã chạy:
- Kết quả:
- Quyết định:
- Sai lệch so với plan:
- Việc còn lại/blocker:
```

### 2026-10-05 — Lập kế hoạch — COMPLETE

- Phạm vi đã làm: Audit cấp cao các notebook, artifacts và DOCX mẫu; xác định gap so với yêu cầu giảng viên; lập execution plan.
- File tạo/sửa: `TIEU_LUAN_AI_EXECUTION_PLAN.md`.
- Kết quả: Đã khóa 10 phase từ khởi tạo đến release.
- Quyết định: Giữ `pipeline/`, `A05/`, `A06/` làm nguồn đọc; mọi nội dung mới đặt trong `term_paper/`.
- Việc còn lại: Phase 0 ở trạng thái READY.

### 2026-10-05 — Phase 0 — COMPLETE

- Phạm vi đã làm: Đọc lại execution plan, `A05/AGENTS.md`, A05/A06 README, `A06/PROJECT_SPEC.md`, `A06/CURRENT_STATE.md`; tạo workspace độc lập; lập inventory notebooks, raw/processed datasets, model/preprocessor artifacts, metrics, predictions, figures và reports; audit execution metadata; lập gap analysis và evidence map.
- File tạo/sửa: `term_paper/README.md`; `term_paper/tools/build_phase0_inventory.ps1`; `term_paper/tools/verify_phase0_inventory.ps1`; `term_paper/artifacts/manifests/source_inventory.json`; `source_hashes.csv`; `notebook_audit.csv`; `gap_analysis.md`; 6 CSV trong `folder_manifests/`; cập nhật file kế hoạch này.
- Lệnh/test đã chạy: `build_phase0_inventory.ps1`; `verify_phase0_inventory.ps1`; parse lại JSON/CSV; kiểm tra trạng thái Git nguồn trước/sau.
- Kết quả: PASS — 16 notebook; 148 hash records; 25 model/preprocessor artifacts; 77 metric/prediction/metadata files; 6 folder manifests; 0 notebook error outputs; mọi file-content hash và folder-manifest entry được xác minh; trạng thái Git dưới `pipeline/`, `A05/`, `A06/` không thay đổi.
- Quyết định: Với kho ảnh lớn, dùng manifest đã sắp xếp theo path/kích cỡ/mtime và SHA-256 của manifest; với notebook, raw file quan trọng, model, metric, prediction và report, dùng SHA-256 nội dung file.
- Sai lệch so với plan: Không có. Có thêm hai script build/verify để Phase 0 có thể tái tạo và kiểm chứng.
- Việc còn lại/blocker: Không có blocker. Phase 1 ở trạng thái READY.

### 2026-10-05 — Phase 1 — COMPLETE

- Phạm vi đã làm: Khóa ma trận truy vết toàn bộ yêu cầu giảng viên; outline đến Heading 3; ngân sách trang/hình/bảng; style DOCX dựa trên file mẫu; hợp đồng split/preprocessing/matched comparison; source registry; bibliography ban đầu; 8 dataset cards cho Chương 2–4.
- File tạo/sửa: `term_paper/config/requirements_matrix.md`; `report_outline.md`; `style_spec.md`; `experiment_contract.md`; `term_paper/sources/source_registry.csv`; `bibliography.bib`; 8 card + README trong `term_paper/sources/dataset_cards/`; `term_paper/tools/verify_phase1.ps1`; cập nhật file kế hoạch này.
- Lệnh/test đã chạy: `term_paper/tools/verify_phase1.ps1`; kiểm đếm trực tiếp raw CSV/annotation manifests; đối chiếu metadata A06; kiểm tra Git status cho `pipeline/`, `A05/`, `A06/`.
- Kết quả: PASS — 8 registry rows; 8 dataset cards; 26 bibliography entries; mọi citation key dataset có entry; mọi local provenance path tồn tại; mọi registry hash xuất hiện trong Phase 0 hash manifest; outline/requirements/style/contract đầy đủ; source folders không có thay đổi mới do Phase 1.
- Quyết định: Dùng 3 dataset ở Chương 2, 3 dataset ở Chương 3 và 2 dataset ở Chương 4. Matched comparison Chương 3 bắt buộc trên EuroSAT + CDC; Oxford là matched track chỉ khi cùng subset/split khả thi. Giữ 51 trang cho Mở đầu + Chương 1–4 và 64 trang trước phụ lục.
- Sai lệch so với plan: Không có. Bổ sung script verification để Phase 1 tái kiểm tra được.
- Việc còn lại/blocker: Không có blocker. License của hai dataset Kaggle (diabetes, housing) chưa xác minh và được ghi `UNVERIFIED`; AAPL không có open redistribution license được xác minh. Đây là documented limitation, không chặn phase sau. Phase 2 và Phase 3 ở trạng thái READY.

### 2026-10-06 — Phase 2 — COMPLETE

- Phạm vi đã làm: Viết Mở đầu và Chương 1 theo outline khóa; hệ thống hóa lịch sử từ McCulloch–Pitts, Turing, Dartmouth, AI biểu tượng, các chu kỳ suy giảm, perceptron/backpropagation, statistical ML, CNN/ImageNet/AlexNet, RNN/LSTM, attention/Transformer đến foundation models và AI tạo sinh; tạo timeline có ánh xạ nguồn theo từng mốc.
- File tạo/sửa: `term_paper/report/sections/00_mo_dau.md`; `01_lich_su_ai.md`; `term_paper/report/assets/ch1/ai_history_timeline.mmd`; `ai_history_timeline.svg`; `timeline_sources.csv`; `README.md`; `term_paper/tools/verify_phase2.ps1`; `term_paper/README.md`; bổ sung 13 nguồn vào `term_paper/sources/bibliography.bib`; cập nhật file kế hoạch này.
- Lệnh/test đã chạy: tìm và đối chiếu nguồn gốc/nguồn chính thức; `term_paper/tools/verify_phase2.ps1`; parse XML của SVG; kiểm tra Git status cho `pipeline/`, `A05/`, `A06/`.
- Kết quả: PASS — Mở đầu 2.110 từ; Chương 1 4.431 từ; 32 citation key duy nhất đều có bibliography entry; bibliography đạt 39 entry; timeline có 18 mốc nguồn, Mermaid source và SVG hợp lệ. Nội dung có đủ RQ1–RQ3, phạm vi/giới hạn, foundation models/generative AI và đoạn chuyển tiếp sang ML/CNN/RNN.
- Quyết định: Manuscript dùng citation key dạng Pandoc `[@key]` để Phase 7–8 chuyển thành trích dẫn số theo thứ tự xuất hiện. Các phát biểu lịch sử ưu tiên bài báo gốc, báo cáo lưu trữ hoặc trang chính thức; không dùng trích dẫn dài nguyên văn.
- Sai lệch so với plan: Không có sai lệch nội dung. Có thêm script verification và `timeline_sources.csv` để kiểm tra độ dài, Heading 1–3, khóa trích dẫn và provenance của hình. PNG preview không được tạo do Chrome/Edge headless lỗi GPU trong môi trường hiện tại; đây không chặn deliverable nguồn SVG và sẽ được kiểm tra trực quan khi dựng/render DOCX ở Phase 8–9.
- Việc còn lại/blocker: Không có blocker. Page budget hiện được kiểm soát bằng số từ; số trang thực tế sẽ được đo và tinh chỉnh sau khi dựng DOCX. Phase 3 ở trạng thái READY.

### 2026-10-06 — Phase 3 — COMPLETE

- Phạm vi đã làm: Hoàn thiện Chương 2 trên ba bộ dữ liệu CDC Diabetes, Vietnam Housing và Synthetic E-Commerce Churn; tái sử dụng baseline ML cổ điển có provenance; xây dựng MLP matched topology `input → 64 ReLU → 32 ReLU → output` bằng NumPy scratch, Keras và PyTorch; chạy huấn luyện, chọn learning rate/checkpoint bằng validation, suy luận TEST, tổng hợp kết quả, hình và notebook tái lập.
- File tạo/sửa: `term_paper/src/scratch/mlp.py`; `src/keras_impl/mlp.py`; `src/pytorch_impl/mlp.py`; các module protocol/data/metric/runner/reporting trong `term_paper/src/common/`; `term_paper/config/ch2_experiment.json`; `term_paper/notebooks/ch2_ml_framework_comparison.ipynb`; 5 file `term_paper/tests/test_ch2_*.py`; `term_paper/tools/verify_phase3.py`; `verify_phase3.ps1`; metric/prediction/model/manifest/coverage/figure artifacts của Chương 2; `term_paper/report/sections/02_ml_co_ban.md`; bổ sung 3 nguồn nền tảng vào `term_paper/sources/bibliography.bib`; cập nhật requirement matrix, README và execution plan.
- Lệnh/test đã chạy: `term_paper/tools/verify_phase3.ps1`; `python -m unittest discover -s term_paper/tests -p 'test_ch2_*.py' -v`; kiểm tra coverage bằng `python -m trace`; execute notebook bằng `jupyter nbconvert --to notebook --execute --inplace`; load lại toàn bộ model và tái tính metric trực tiếp từ prediction CSV.
- Kết quả: PASS — 20/20 test; 27 lượt chạy độc lập = 3 dataset × 3 framework × 3 seed; 196.713 dòng dự đoán TEST; 27/27 model load-check thành công; parameter count khớp giữa framework trên từng dataset; 4 figure; chương dài 5.997 từ, có 5 bảng và 10 citation key; bibliography đạt 42 entry. Coverage mã implementation lõi: NumPy 95%, Keras 96%, PyTorch 91%; metric/protocol/experiment utilities đạt 90–98%.
- Quyết định: Dùng ba seed `42/52/62` vì một vòng đầy đủ nằm dưới operational bound đã khóa; fit toàn bộ preprocessing chỉ trên TRAIN và giữ cùng processed arrays/split cho ba framework; báo cáo mean ± sample SD. Housing tạo 143 feature sau khi fit đúng TRAIN thay vì 154 feature của pipeline cũ fit trên DEV. Giữ nguyên kết quả âm có ý nghĩa: MLP không vượt Logistic Regression về F1 trên churn, trong khi MLP cải thiện diabetes F1 và housing RMSE so với baseline cổ điển tốt nhất.
- Sai lệch so với plan: Không có sai lệch phạm vi. Bổ sung các module common, manifest/hash provenance, script verifier và coverage artifact để kết quả có thể tái lập và audit. Số trang 12–14 hiện được kiểm soát bằng 5.997 từ; số trang thực tế sẽ được đo sau khi dựng DOCX ở Phase 8.
- Việc còn lại/blocker: Không có blocker. Phase 4 ở trạng thái READY; Phase 5 giữ PENDING theo thứ tự thực thi tuần tự.

### 2026-10-06 — Phase 4 — COMPLETE

- Phạm vi đã làm: Hoàn thiện Chương 3 với hai track. Track matched cài đặt topology `Conv(8,3) → ReLU → MaxPool(2) → Conv(16,3) → ReLU → GAP → Dense` bằng NumPy scratch, Keras và PyTorch trên EuroSAT Conv2D và CDC Diabetes Conv1D. Track ablation nhập nguyên vẹn 12 kết quả Keras A05 cho EuroSAT, Oxford-IIIT Pet và CDC; Oxford được giữ là case study riêng theo điều kiện trong plan.
- File tạo/sửa: `term_paper/src/scratch/cnn.py`; `src/keras_impl/cnn.py`; `src/pytorch_impl/cnn.py`; các module `ch3_data.py`, `ch3_protocol.py`, `ch3_metrics.py`, `ch3_experiment.py`, `run_ch3_experiments.py`, `ch3_reporting.py`; `term_paper/config/ch3_experiment.json`; 5 file `term_paper/tests/test_ch3_*.py`; `term_paper/notebooks/ch3_cnn_framework_comparison.ipynb`; `term_paper/tools/build_ch3_notebook.py`; `verify_phase4.py`; `verify_phase4.ps1`; model/metric/prediction/manifest/coverage/figure artifacts Chương 3; `term_paper/report/sections/03_cnn.md`; bổ sung hai nguồn VGG/ResNet vào bibliography; cập nhật requirement matrix, README và execution plan.
- Lệnh/test đã chạy: `python -m unittest discover -s term_paper/tests -p 'test_ch3_*.py' -v`; `python -m term_paper.src.common.run_ch3_experiments --seeds 42`, sau đó `--seeds 52 62`; `python -m term_paper.src.common.ch3_reporting`; execute notebook bằng `jupyter nbconvert --execute`; `term_paper/tools/verify_phase4.ps1`; line coverage bằng Python `trace`.
- Kết quả: PASS — 19/19 test; 18 matched run = 2 dataset × 3 framework × 3 seed; 14.850 prediction rows; 18/18 model load-check; sample-key/preprocessor/split hash parity đạt; parameter count bằng nhau (EuroSAT 1.562, CDC 483); 5 figure; notebook execute không lỗi; Chương 3 dài 5.544 từ, 5 bảng, 5 hình và 11 citation key; bibliography đạt 44 entry. Coverage implementation lõi: NumPy 97%, Keras 98%, PyTorch 94%; data/metric/protocol utilities đạt 90–100% ngoại trừ artifact helper 80%.
- Quyết định: Dùng fixed stratified benchmark subset 500/150/150 cho EuroSAT và 6.000/1.500/1.500 cho CDC vì scratch Conv2D full data không phù hợp operational bound; cả ba framework dùng đúng cùng subset. Clean run seed 42 dưới hai phút nên chạy thêm seed 52/62 theo hợp đồng. Oxford không vào matched table vì plan cho phép dùng A05 case study khi không chạy cùng keys trên ba framework.
- Kết quả thực nghiệm chính: EuroSAT matched mean macro-F1: NumPy 0,2403±0,0666, Keras 0,2641±0,0794, PyTorch 0,2026±0,0098. CDC: 0,4075±0,0191, 0,4119±0,0161 và 0,4153±0,0053. A05 full-data được tách riêng: Basic EuroSAT 0,7256, trong khi AlexNet/VGG/ResNet-inspired đều collapse ở 0,0200; Oxford có macro-F1 0,0014–0,0198; CDC Basic cao nhất 0,4392.
- Sai lệch so với plan: Không có sai lệch phạm vi. Benchmark subset và Oxford case-study path đều là nhánh đã quy định trong plan. Bổ sung verifier, notebook builder, manifest/hash provenance và coverage artifact để kết quả có thể audit. Số trang 12–14 hiện kiểm soát bằng 5.544 từ; số trang thực tế sẽ được đo khi dựng DOCX ở Phase 8.
- Việc còn lại/blocker: Không có blocker. Phase 5 ở trạng thái READY.

### 2026-10-06 — Phase 5 — COMPLETE

- Phạm vi đã làm: Hoàn thiện Chương 4 bằng matched Vanilla RNN hidden-32, many-to-one trên Online Retail II customer-week classification và AAPL next-Close regression. Cài đặt NumPy scratch có forward nhiều bước, BPTT, global gradient clipping, Adam, early stopping và save/load; tạo wrapper Keras `SimpleRNN` và PyTorch `nn.RNN` tương đương; chạy learning-rate selection bằng VALIDATION, threshold selection customer bằng VALIDATION, đánh giá ba seed và giữ naive last-Close làm baseline bắt buộc.
- File tạo/sửa: `term_paper/src/scratch/rnn.py`; `src/keras_impl/rnn.py`; `src/pytorch_impl/rnn.py`; các module `ch4_data.py`, `ch4_protocol.py`, `ch4_metrics.py`, `ch4_experiment.py`, `run_ch4_experiments.py`, `ch4_reporting.py`; `term_paper/config/ch4_experiment.json`; 5 file `term_paper/tests/test_ch4_*.py`; `term_paper/notebooks/ch4_rnn_framework_comparison.ipynb`; `term_paper/tools/build_ch4_notebook.py`; `verify_phase5.py`; `verify_phase5.ps1`; model/metric/prediction/manifest/coverage/figure artifacts Chương 4; `term_paper/report/sections/04_rnn.md`; cập nhật requirement matrix và README.
- Lệnh/test đã chạy: red/green TDD cho `test_ch4_rnn.py` và bốn test module data/artifact/runner/reporting; `python -m unittest discover -s term_paper/tests -p 'test_ch4_*.py' -v`; `python -m term_paper.src.common.run_ch4_experiments --seeds 42`, sau đó `--seeds 52 62`; `python -m term_paper.src.common.ch4_reporting`; execute notebook bằng `jupyter nbconvert --execute`; `python -m term_paper.tools.verify_phase5`; line coverage bằng Python `trace --count --missing`.
- Kết quả: PASS — 20/20 test; 18 matched run = 2 dataset × 3 framework × 3 seed; 75.690 prediction rows; 18/18 model load-check; TEST key/date/target, split hash và preprocessor hash parity đạt; cả ba framework có 1.249 trainable parameters; 6 figure; notebook execute không lỗi; Chương 4 dài 5.606 từ, 5 bảng, 6 hình và 10 citation key. Coverage implementation lõi: NumPy 97,8%, Keras 96,9%, PyTorch 92,7%; data/metric utilities 97,2–100%, protocol 81,5%.
- Quyết định: Customer dùng fixed stratified subset 30.000/8.000/8.000 lấy từ đúng chronological TRAIN/VAL/TEST A06 để scratch chạy trong operational bound; cả ba framework dùng cùng keys. AAPL dùng toàn bộ 1.915/411/410 arrays. PyTorch giữ `bias_hh_l0` zero/frozen để matched parameter count và phương trình một recurrent bias. Clean seed 42 dưới 20 phút nên chạy thêm seed 52/62. Prediction CSV là nguồn sự thật để xử lý ROC-AUC nhạy với floating-point ties sau serialization.
- Kết quả thực nghiệm chính: Customer mean F1 — NumPy 0,2864±0,0273, Keras 0,2985±0,0070, PyTorch 0,3265±0,0058; PR-AUC tương ứng 0,2163±0,0251, 0,2217±0,0139 và 0,2466±0,0013. AAPL mean RMSE — NumPy 36,9741±4,9221 USD, Keras 32,7533±6,0509, PyTorch 27,7904±2,6129; naive last-Close 3,8789 USD. Cả 9 RNN stock runs thua naive và kết quả âm được giữ nguyên; không đưa khuyến nghị đầu tư.
- Sai lệch so với plan: Không có sai lệch phạm vi. Fixed customer subset là nhánh operational-bound đã cho phép trong hợp đồng; A06 full-data hidden-64 được nhập làm reference riêng, không trộn với matched table. Keras/PyTorch model reload khớp trên training scale `atol≤1e-6`; khi inverse-transform stock sang USD, verifier dùng `atol=1e-4` do scaler khuếch đại sai khác float32. Số trang 12–14 hiện kiểm soát bằng 5.606 từ; số trang thực tế sẽ được đo khi dựng DOCX ở Phase 8.
- Việc còn lại/blocker: Không có blocker. Phase 6 ở trạng thái READY.

### 2026-10-06 — Phase 6 — COMPLETE

- Phạm vi đã làm: Xây ứng dụng inference cục bộ có ba tab cho Diabetes tabular, EuroSAT CNN và RNN Customer/AAPL; nạp bốn NumPy model seed 42 cùng preprocessor; validate input theo allow-list; hiển thị probability/top-3/RNN-vs-naive, provenance SHA-256 và cảnh báo y khoa/tài chính; bổ sung health endpoint, rate limit, security headers, Docker và tài liệu chạy lại.
- File tạo/sửa: `term_paper/deployment/app/` gồm server, service, schema và HTML/CSS/JS; 3 module test trong `deployment/tests/`; `requirements.txt`; `Dockerfile`; `README.md`; `model_registry.json`; `coverage_summary.md`; `docker_smoke_test.json`; các `.cover`; `term_paper/report/sections/05_trien_khai.md`; 2 PNG trong `report/assets/deployment/`; `term_paper/tools/verify_phase6.py`; `verify_phase6.ps1`; cập nhật requirement matrix, README và execution plan.
- Lệnh/test đã chạy: red/green TDD bằng `python -m unittest discover -s term_paper/deployment/tests -v`; coverage bằng Python `trace --count --missing --summary`; `python -m term_paper.tools.verify_phase6`; chạy app thật và chụp Chrome headless; build image Docker bằng sáu named contexts; chạy container, gọi `/health` và demo→predict AAPL; xóa container smoke-test sau kiểm tra.
- Kết quả: PASS — 12/12 test; 4/4 deterministic demo chạy qua HTTP; output bốn service khớp prediction artifact (`1e-6` classification, `1e-4` AAPL USD); core deployment weighted line coverage 85,3%; 4 model/preprocessor bundle xác minh SHA-256; Phần 5 dài 1.888 từ với đủ mục 5.1–5.6 và 2 ảnh chụp 1.440 px; Docker image `tieu-luan-ai:phase6` build thành công, chạy non-root, `/health=ok`, 4 model verified và AAPL trả RNN 181,25 USD so với naive 186,28 USD.
- Quyết định: Do Streamlit/FastAPI/Flask không có sẵn, dùng `ThreadingHTTPServer` thư viện chuẩn và UI tĩnh có chủ đích; tránh cài framework web vào environment assignment. Chỉ deploy model NumPy seed 42 để bundle nhẹ và gắn trực tiếp với scratch implementation; Keras/PyTorch vẫn được giữ trong benchmark Chương 2–4. Public cloud ghi `OPTIONAL_PENDING_CREDENTIALS`; local và Docker là phạm vi hoàn thành.
- Sai lệch so với plan: Không có sai lệch chức năng. Thay Streamlit bằng HTTP server + HTML theo fallback đã quy định vì thiếu dependency. Docker dùng named build contexts để không gửi toàn workspace 2,7 GB. Môi trường test phụ `backend/.venv` có scikit-learn 1.9.0 nên phát cảnh báo khi đọc artifact 1.9.1, nhưng parity vẫn đạt; Docker dùng đúng scikit-learn 1.9.1 và smoke test đạt.
- Việc còn lại/blocker: Không có blocker. Phase 7 ở trạng thái READY.

### 2026-10-07 — Phase 7 — COMPLETE

- Phạm vi đã làm: Hợp nhất tóm tắt, Mở đầu, Chương 1–4, Phần 5 và Kết luận; chuẩn hóa thuật ngữ; chuyển citation key sang trích dẫn số theo thứ tự xuất hiện; tạo tài liệu tham khảo có thứ tự; đóng gói toàn bộ figure theo đường dẫn tương đối; bổ sung cross-reference và nguồn artifact cho mọi bảng; lập manifest truy vết và bộ kiểm tra acceptance có thể chạy lại.
- File tạo/sửa: `term_paper/report/front_matter.md`; `report/sections/02_ml_co_ban.md`; `03_cnn.md`; `04_rnn.md`; `05_trien_khai.md`; `06_ket_luan.md`; `report/terminology.md`; `report/manuscript.md`; `report/references_ordered.md`; `report/report_manifest.json`; 15 PNG được đóng gói vào `report/assets/ch2/`, `ch3/`, `ch4/`; `term_paper/tools/build_phase7_manuscript.py`; `verify_phase7.py`; `verify_phase7.ps1`; cập nhật requirement matrix, README và execution plan.
- Lệnh/test đã chạy: `term_paper/tools/verify_phase7.ps1` (build + acceptance); `term_paper/tools/verify_phase0_inventory.ps1 -WorkspaceRoot C:\DATA\assign`; `git diff --check`; kiểm tra citation/bibliography, heading order, word budget, figure/table cross-reference, source artifact, hash, code excerpt, placeholder, token và đường dẫn tuyệt đối.
- Kết quả: PASS — manuscript 29.779 từ; 8 dataset instance có link/license status/provenance; 9 phần cấp 1; 18 hình và 16 bảng đều có nhắc trong nội dung; 44/44 nguồn được trích dẫn, không missing/orphan; 3 code excerpt đều 10–25 dòng; 63 matched run và 287.253 dòng dự đoán TEST được ghi trong manifest; page estimate 65 nằm trong budget 59–69. Phase 0 invariant PASS với 148 hash record, 6 folder manifest và trạng thái nguồn `pipeline/`, `A05/`, `A06/` không đổi so với baseline đã khóa.
- Quyết định: `manuscript.md` là nguồn nội dung chính cho Phase 8; section source vẫn giữ Pandoc key để biên tập, còn build script sinh citation số deterministic. Thông tin bìa chưa biết chỉ được ghi `PENDING_INPUT` trong manifest, không chèn placeholder vào manuscript. Kết quả âm được giữ nguyên: MLP churn dưới logistic regression, ba CNN sâu A05 collapse và cả 9 RNN AAPL run thua naive.
- Sai lệch so với plan: Không có sai lệch phạm vi. Bổ sung build/verifier và `references_ordered.md` để việc chuyển sang DOCX có thể tái lập. Số trang 65 hiện là ước lượng biên tập; số trang chính xác sẽ được đo sau render ở Phase 8.
- Việc còn lại/blocker: Không có blocker nội dung. Phase 8 ở trạng thái READY; thông tin bìa vẫn cần người dùng cung cấp trước bản nộp cuối, nhưng có thể dựng DOCX với trạng thái metadata được quản lý.

### 2026-10-07 — Phase 8 — COMPLETE

- Phạm vi đã làm: Đọc và áp dụng quy trình DOCX; trích xuất phong cách và metadata từ file mẫu; dựng cover, title page, mục lục liên kết, danh mục hình/bảng, Heading 1–3, caption, bookmark/cross-reference, bảng Word native, code block, header/footer, số trang và bibliography; sửa OOXML để Microsoft Word mở trực tiếp; thực hiện phân trang nhiều lượt để khóa số trang; reopen, structural validation và kiểm tra trực quan toàn bộ bản render Word.
- File tạo/sửa: `term_paper/report/build_report.py`; `word_paginate_export.ps1`; `render_pdf_winrt.ps1`; `extract_docx_layout.mjs`; `derive_page_map.py`; `make_contact_sheets.py`; `validate_report.py`; `build_log.json`; `report_validation.json`; `report/Tieu_luan_AI_ML_CNN_RNN.docx`; PNG timeline và logo được đóng gói trong `report/assets/`; cập nhật requirement matrix, README và execution plan.
- Lệnh/test đã chạy: build DOCX ba lượt với page map từ Word; mở/lưu và export PDF bằng Microsoft Word 16 chạy ẩn; `render_docx.py --renderer artifact-tool`; render PDF thành 73 PNG bằng Windows PDF API; kiểm tra 9 contact sheet chứa đủ 73 trang; Open XML SDK validation; `validate_report.py`; reopen bằng `python-docx`.
- Kết quả: PASS — DOCX 73 trang, 3.226.772 byte; 125 heading; 18 hình; 16 bảng nội dung native + 3 bảng code; 34 caption; 44 tài liệu tham khảo; 159/159 bookmark mục lục/danh mục được Word phân trang, 0 thiếu; validation 20/20 PASS; không clipping/overflow, không placeholder/tool token/đường dẫn tuyệt đối. Mở đầu 4 trang; Chương 1 8 trang; Chương 2–4 mỗi chương 14 trang, đúng yêu cầu giảng viên.
- Quyết định: Dùng mục lục/danh mục tĩnh có hyperlink và số trang sinh từ bookmark sau khi Microsoft Word phân trang để kết quả ổn định. Metadata bìa lấy từ file mẫu đã cung cấp: Triệu Tuấn Anh, B23DCCN053, D23CTPM01, PGS.TS Trần Đình Quế, Học kỳ 1 năm học 2026–2027.
- Sai lệch so với plan: `artifact-tool` đã được chạy trên bản cuối nhưng bản cài hiện tại làm co mọi native Word table thành cột hẹp; lỗi tái hiện trên hai DOCX tối giản độc lập. Vì yêu cầu bắt buộc giữ bảng native, bản authoritative được cross-render bằng Microsoft Word 16 và kiểm tra đủ 73/73 trang; ngoại lệ renderer được ghi trong `report_validation.json`. Tổng 73 trang cao hơn ước lượng 59–69 do front matter 8 trang và phần triển khai/kết luận chi tiết, trong khi toàn bộ phần có định lượng bắt buộc của giảng viên đều đúng budget.
- Việc còn lại/blocker: Không có blocker. Phase 9 ở trạng thái READY để audit accessibility/metric-link lần cuối, scrub metadata nếu cần và phát hành artifact duy nhất.

### 2026-10-07 — Phase 9 — COMPLETE

- Phạm vi đã làm: Audit accessibility, style, comment/tracked changes, navigation, link/citation, page budget, metric–artifact và metadata; thêm alt text cho logo PTIT; làm sạch Office identity và build comment khỏi metadata nhưng giữ tác giả học thuật; render lại bằng artifact-tool và Microsoft Word; kiểm tra hồi quy toàn bộ phase liên quan; khóa một DOCX release duy nhất.
- File tạo/sửa: `term_paper/report/build_report.py`; `finalize_release_metadata.py`; `verify_phase9.py`; `report/Tieu_luan_AI_ML_CNN_RNN.docx`; các log nội bộ trong `report/qa/phase9/`; cập nhật README và execution plan.
- Lệnh/test đã chạy: `a11y_audit.py`; `style_lint.py`; `accept_tracked_changes.py --mode report`; `comments_extract.py`; Microsoft Word pagination/PDF export; `render_docx.py --renderer artifact-tool`; Windows PDF render; contact-sheet comparison; `validate_report.py`; `verify_phase9.py`; verifier Phase 4–7; Phase 0 source invariant; unit test Phase 3.
- Kết quả: PASS — 16/16 release checks; 73 trang; 159/159 navigation target; Mở đầu 4 trang, Chương 1 8 trang, Chương 2–4 mỗi chương 14 trang; 24/24 metric tổng hợp khớp chính xác CSV nguồn; 287.253 dòng prediction TEST; 318 internal hyperlink; 52 HTTPS target; 44 reference; 0 comment, 0 tracked change; 0 accessibility high; metadata creator/lastModifiedBy đều là Triệu Tuấn Anh và không còn custom property/build comment.
- Quyết định: Giữ 43 raw DOI/source URL trong bibliography vì đây là thông tin học thuật trực tiếp và chỉ bị audit xếp low. Ba finding medium về table header được giải thích: đó là ba code block một ô, không phải bảng dữ liệu nên không có semantic header. Không chạy style normalization toàn cục vì sẽ xóa emphasis, font code/equation và typography bìa có chủ đích.
- Sai lệch so với plan: Bản artifact-tool vẫn co cột của bảng Word native do lỗi renderer đã tái hiện bằng fixture tối giản; artifact-tool render vẫn được thực thi, còn QA trực quan authoritative dùng Word 16. Verifier Phase 3 legacy có quy tắc cấm mọi URL trong Chương 2, xung đột yêu cầu hiện hành phải có link dataset; 20/20 unit test của Phase 3 PASS và Phase 7/9 thay thế quy tắc text cũ bằng kiểm tra link HTTPS.
- Việc còn lại/blocker: Không có. Toàn bộ Phase 0–9 COMPLETE; DOCX release đã sẵn sàng nộp.
