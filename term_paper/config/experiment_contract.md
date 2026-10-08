# Hợp đồng thực nghiệm chung

Phiên bản 1.0 — khóa ở Phase 1, ngày 2026-10-05. Mọi thay đổi sau này phải được ghi trong nhật ký plan, nêu lý do và không được dùng TEST để quyết định.

## 1. Nguyên tắc bất biến

1. Seed mặc định là `42`; đồng bộ Python/NumPy/framework khi API hỗ trợ.
2. Raw data trong `datasets/`, `A05/datasets/`, `A06/datasets/` là read-only.
3. Preprocessor, scaler, vocabulary và class weight chỉ fit/tính từ TRAIN.
4. Validation dùng cho hyperparameter, threshold, checkpoint và early stopping. TEST chỉ đánh giá sau khi cấu hình khóa.
5. Scratch, Keras và PyTorch trong cùng một track phải dùng cùng sample keys, split, preprocessing output, topology logic và budget.
6. Mọi prediction lưu theo từng sample cùng ground truth/key; metric trong báo cáo phải tái tính được từ artifact này.
7. Không thay đổi metric, split hoặc baseline sau khi nhìn TEST. Nếu phát hiện lỗi, invalid toàn run liên quan và chạy lại cả ba framework.

## 2. Chính sách split

### 2.1. Chương 2 — ML cơ bản

- Giữ outer split hiện có của notebook nguồn: 80% development, 20% TEST, `random_state=42`.
- Diabetes và customer churn dùng stratification; housing regression không stratify.
- Từ 80% development, tách 20% làm validation với seed 42; tỷ lệ hiệu dụng khoảng 64/16/20.
- Phải lưu raw row keys/indices cho TRAIN/VAL/TEST. Ba framework dùng đúng các index này.
- Diabetes raw 70,692 hàng giảm còn 69,057 sau loại exact duplicates; chỉ split sau bước làm sạch này.
- Customer static churn dùng `prediction_cutoff=2024-10-01 23:59:05`; feature hành vi chỉ lấy trước cutoff.

### 2.2. Chương 3 — CNN

- EuroSAT: dùng split A05 đã lưu, stratified 70/15/15 (`18,900/4,050/4,050`).
- Oxford-IIIT Pet: giữ official TEST 3,669; official trainval 3,680 được chia stratified thành TRAIN 2,944 và VAL 736. Loại 41 ảnh raw không có trong annotation chính thức.
- CDC Diabetes 012: dùng split A05 đã lưu, stratified 70/15/15 (`177,576/38,052/38,052`).
- Matched scratch/Keras/PyTorch bắt buộc trên EuroSAT và CDC. Nếu scratch trên full data vượt operational bound, tạo benchmark subset stratified cố định từ TRAIN/VAL/TEST; lưu danh sách key và dùng cùng subset cho cả ba framework.
- Oxford là case study mở rộng. Chỉ đưa vào bảng matched chính nếu cả ba framework chạy trên cùng keys; nếu không, tách riêng bảng Keras A05/case study.

### 2.3. Chương 4 — RNN

- Dùng nguyên processed arrays, sample keys và chronological split của A06.
- Online Retail II: sequence `8 × 5`, dự đoán `active_flag` tuần kế tiếp. Split theo `target_week`: TRAIN 247,458; VAL 50,354; TEST 53,052.
- AAPL: sequence `30 × 5`, dự đoán Close phiên kế tiếp. Split theo `target_date`: TRAIN 1,915; VAL 411; TEST 410.
- Validation/TEST được phép dùng history sớm hơn boundary vì đó là thông tin đã biết tại thời điểm dự đoán; target không được đi ngược qua boundary.

## 3. Preprocessing khóa

| Track | Input/preprocessing |
|---|---|
| Ch2 Diabetes | 21 predictor; median imputation + StandardScaler fit TRAIN |
| Ch2 Housing | Numeric median + scaling; categorical `Unknown` + one-hot; fit TRAIN; target model có thể dùng standardized `log1p`, metric inverse-transform về tỷ VND |
| Ch2 Customer | 43 numeric + 7 categorical + review text TF-IDF; fit TRAIN; không dùng dữ liệu sau cutoff |
| Ch3 EuroSAT | RGB 64×64×3, scale `[0,1]`; augmentation `none` cho matched track |
| Ch3 Oxford | RGB resized theo protocol A05; cùng resize/normalization cho mọi framework |
| Ch3 CDC | 21 feature theo thứ tự CSV, StandardScaler fit TRAIN; Conv1D input `(21,1)`; nêu rõ adjacency là nhân tạo |
| Ch4 Customer | 5 feature tuần, StandardScaler fit flattened TRAIN X; inactive weeks điền 0 trước scaling |
| Ch4 AAPL | Open/High/Low/Close/Volume; StandardScaler fit TRAIN X; target scaler fit TRAIN y; metric inverse-transform về USD |

## 4. Kiến trúc matched

### 4.1. Chương 2 — MLP

- Topology logic mặc định: `input → Dense(64) + ReLU → Dense(32) + ReLU → output`.
- Binary: 1 logit/sigmoid tương đương, BCE; regression: linear output, MSE.
- Scratch phải có forward, stable loss, backpropagation, mini-batch update, predict, save/load.
- Keras/PyTorch phải báo rõ quy ước logits so với probability để tránh double-sigmoid.

### 4.2. Chương 3 — CNN

- EuroSAT: Conv2D 8 filters 3×3 + ReLU → MaxPool 2×2 → Conv2D 16 filters 3×3 + ReLU → controlled flatten/GAP → classifier.
- CDC: progression Conv1D tương đương trên `(21,1)`; kernel/padding và output shape được ghi rõ.
- Scratch có backward cho convolution, activation, pooling/GAP và dense; có numerical-gradient test trên tensor nhỏ.
- Parameter count giữa framework phải khớp theo công thức, cho phép khác chỉ do bias/API và phải giải thích.

### 4.3. Chương 4 — Vanilla RNN

- Many-to-one Vanilla RNN, `tanh`, hidden size 32 cho controlled benchmark, 1 recurrent layer, linear/sigmoid head theo nhiệm vụ.
- Scratch có BPTT, gradient clipping, mini-batch update, predict và save/load.
- Customer dùng BCE; stock dùng MSE trên training scale.
- AAPL luôn có naive baseline: dự đoán next Close bằng Close cuối sequence.

## 5. Budget huấn luyện và chọn mô hình

- Cùng optimizer family, learning-rate candidates, batch size, max epochs, patience và `min_delta` trong một matched track.
- Giá trị cuối được chọn chỉ từ validation. Search space phải được ghi trước khi chạy và lưu thành artifact.
- Một clean run seed 42 là bắt buộc. Nếu một full matched run không quá 20 phút CPU, chạy thêm seed 52 và 62, báo mean ± standard deviation; nếu vượt ngưỡng, ghi rõ single-seed controlled experiment.
- Early stopping restore best validation checkpoint. Báo cả `best_epoch` và `epochs_run`.
- Thời gian training không gồm load raw data/EDA; gồm forward/backward/update của toàn quá trình fit. Ghi warm-up và thiết bị.

## 6. Metric và baseline

### 6.1. Classification

- Accuracy, precision, recall, F1; macro-F1 là metric chính cho multiclass/imbalance.
- ROC-AUC cho binary khi cả hai lớp xuất hiện; PR-AUC bổ sung cho Online Retail II.
- Confusion matrix và per-class recall; Ch3 CDC bắt buộc recall lớp prediabetes và diabetes.
- Baseline: majority class và/hoặc classical model phù hợp, tách khỏi bảng framework nếu topology không matched.

### 6.2. Regression

- MAE, RMSE và R² trên đơn vị thật; MAPE chỉ dùng khi target dương và nêu giới hạn.
- Housing baseline: median/linear/tree baseline từ notebook hiện có.
- AAPL baseline bắt buộc: last Close; không được kết luận RNN hữu ích nếu không vượt baseline.
- Có actual-vs-predicted, residual/error-by-time và failure examples.

## 7. Đo parameter và thời gian

- Parameter count là số trainable scalar parameters; scratch tính từ shape, Keras/PyTorch lấy API và cross-check bằng công thức.
- Inference benchmark dùng cùng TEST samples, batch policy và thiết bị; warm-up tối thiểu một lượt không tính giờ.
- Báo tổng inference seconds và milliseconds/sample. Không dùng một phép đo CPU đơn lẻ để tuyên bố framework tốt hơn phổ quát.
- Lưu CPU/GPU, OS, Python, NumPy, TensorFlow/Keras, PyTorch và thread settings trong environment artifact.

## 8. Artifact schema tối thiểu

### 8.1. Prediction artifact

Các cột bắt buộc:

- `chapter`, `dataset_id`, `framework`, `seed`, `split`;
- `sample_key` hoặc key nghiệp vụ/date;
- ground truth: `y_true`/`actual`;
- output: probability/logit/predicted class hoặc predicted value;
- threshold nếu classification binary;
- `model_sha256`, `preprocessor_sha256`, `split_sha256`.

### 8.2. Metric artifact

Mỗi dòng phải có:

- dataset/framework/seed/split;
- topology ID, parameter count, epochs run/best epoch;
- training seconds, inference seconds, sample count;
- metric values và đơn vị;
- đường dẫn tương đối + SHA-256 của prediction source.

### 8.3. Figure/table provenance

- Mỗi figure được sinh từ script/notebook và metric/prediction artifact, không chỉnh số bằng tay.
- Report manifest ánh xạ số Hình/Bảng → source artifact → SHA-256 → caption.

## 9. Kiểm thử bắt buộc

- Shape/dtype/finite-value tests cho preprocessing và forward.
- Loss giảm trên toy data cho mọi scratch model.
- Numerical gradient cho MLP/CNN/RNN scratch trên tensor nhỏ.
- Gradient clipping test cho RNN.
- Save/load parity trong tolerance: probability/value `atol ≤ 1e-6` khi cùng dtype/backend; nếu khác backend, ghi tolerance đã đo và lý do.
- Metric reproduction từ prediction artifact; sample-key equality giữa ba framework.
- Không có overlap giữa split; hash/index manifest khớp trước và sau training.

## 10. Xử lý sai lệch

- Khác biệt API không tránh được phải ghi trong bảng “implementation deviations”.
- Nếu framework không thể biểu diễn chính xác một operation, dùng phép biến đổi tương đương về toán học hoặc loại run khỏi matched table; không so trá hình.
- OOM/runtime quá mức cho phép dùng fixed benchmark subset, nhưng cả ba framework phải chuyển cùng subset.
- Mọi crash, collapse hoặc metric dưới baseline được giữ trong log; chỉ loại khi có lỗi kỹ thuật xác định và phải chạy lại theo cùng protocol.
