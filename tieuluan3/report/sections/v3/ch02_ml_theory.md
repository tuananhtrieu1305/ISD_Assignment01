# CHƯƠNG 2. CÁC KỸ THUẬT MACHINE LEARNING CƠ BẢN

## 2.1. Mở đầu

Machine Learning (ML), hay học máy, xây dựng cách dự đoán từ những ví dụ đã biết thay vì viết toàn bộ quy tắc bằng tay. Với một căn nhà, đầu vào có thể là diện tích, năm xây dựng và chất lượng công trình; đầu ra là giá bán. Với bộ dữ liệu sức khỏe, đầu vào là các chỉ báo khảo sát; đầu ra là nhãn đã ghi nhận trong nguồn dữ liệu. Đây là hai dạng học có giám sát: hồi quy dự đoán một giá trị số, còn phân loại dự đoán một nhãn.

Chương này đặt câu hỏi: khi giữ nguyên dữ liệu và kiến trúc, MLP tự viết, Keras và PyTorch khác nhau thế nào về chất lượng, thời gian và bộ nhớ? Các mô hình cổ điển được dùng làm mốc đối chiếu. Mạng nhiều lớp không được mặc định là tốt hơn; một mô hình tuyến tính hoặc rừng cây vẫn có thể phù hợp hơn với dữ liệu bảng.

Ba bài toán được chọn là nhận diện nhãn tiểu đường trong khảo sát CDC, ước lượng giá nhà Ames và dự đoán đăng ký tiền gửi Bank Marketing. Hai bài toán đầu gắn với các miền ưu tiên của tiểu luận; bài toán còn lại giúp kiểm tra sự khác biệt trên dữ liệu mất cân bằng ở một miền khác. Các kết quả sức khỏe chỉ phục vụ học thuật, không phải chẩn đoán.

## 2.2. Những kỹ thuật nền tảng

### 2.2.1. Tiền xử lý và chia dữ liệu

Một mô hình không đọc trực tiếp các trường văn bản như loại nhà hay nghề nghiệp. Trước tiên, các trường số được điền thiếu bằng trung vị rồi chuẩn hóa bằng thống kê của tập huấn luyện. Trường phân loại được chuyển thành các cột one-hot: mỗi cột biểu thị có hay không một giá trị danh mục. Danh mục chưa gặp khi huấn luyện được mã hóa thành toàn số 0 ở nhóm cột tương ứng, không tự mở rộng đầu vào.

Luồng xử lý là: **bản ghi gốc → kiểm schema → điền thiếu/chuẩn hóa/one-hot → vector số → mô hình → xác suất hoặc giá nhà**. Mã định danh và nhãn không được đưa vào vector đầu vào. Riêng Bank, `duration` bị loại vì chỉ biết sau cuộc gọi, trong khi bài toán cần dự đoán trước cuộc gọi.

Tập train dùng để học tham số; validation dùng để chọn checkpoint; TEST chỉ dùng để đánh giá cuối. Những bản ghi trùng đặc trưng được gom trước khi chia để hạn chế một ví dụ xuất hiện ở cả hai phía. Thống kê điền thiếu, scaler, từ vựng và trọng số lớp đều chỉ được fit trên matched train đã khóa. Với Ames, giá nhà được chuẩn hóa khi train và đổi ngược sang USD khi tính sai số. Nhãn thật tính metric vẫn lấy giá gốc, tránh sai số làm tròn do đổi ngược nhãn float32.

### 2.2.2. Mô hình đơn giản và mô hình tuyến tính

Baseline đơn giản trả về lớp phổ biến nhất ở bài toán phân loại hoặc trung vị giá nhà ở bài toán hồi quy. Nó không học quan hệ giữa đặc trưng và đầu ra. Vai trò của baseline là cho biết mô hình phức tạp có thực sự tạo thêm ích lợi hay chỉ hưởng lợi từ phân bố dữ liệu.

Logistic Regression kết hợp các đặc trưng theo trọng số rồi chuyển điểm số thành xác suất nhị phân. Ridge Regression cũng học một tổ hợp tuyến tính nhưng thêm ràng buộc để trọng số không quá lớn. Cả hai đều nhanh, dễ đóng gói và tạo mốc đối chiếu hữu ích với MLP. Chúng có thể bỏ sót những quan hệ phi tuyến nếu chỉ dùng các đặc trưng gốc.

Random Forest kết hợp nhiều cây quyết định. Một cây đặt các câu hỏi liên tiếp về đặc trưng; kết quả của rừng là trung bình xác suất hoặc giá trị từ các cây. Rừng cây có thể biểu diễn tương tác phi tuyến mà không cần thiết kế tầng mạng. Đổi lại, checkpoint và thời gian dự đoán có thể lớn hơn mô hình tuyến tính. Khái niệm “trên 5 layer” không áp dụng cho các baseline cổ điển này.

Trong code, `fit_baseline(name,x,y,task,seed)` trả mô hình đã fit và một bản portable chỉ gồm các mảng số. `PortableBaseline.predict(x)` nhận `[B,D]` và trả `[B,2]` xác suất phân loại hoặc `[B,1]` giá đã chuẩn hóa. Luồng Logistic là **vector số → tổ hợp tuyến tính → sigmoid → hai xác suất**; Ridge là **vector số → tổ hợp tuyến tính → đổi ngược giá sang USD**; Random Forest là **vector số → đi qua từng cây theo ngưỡng → lấy giá trị ở lá → trung bình các cây → hậu xử lý**. Các hàm dự đoán không fit lại, từ chối sai số chiều hoặc giá trị không hữu hạn. Baseline hằng bỏ qua đặc trưng và chỉ lặp giá trị đã học từ train.

### 2.2.3. MLP và sáu lớp học được

MLP biến vector đầu vào qua nhiều lớp Dense. Mỗi lớp Dense học một phép kết hợp mới; hàm ReLU ở giữa cho phép biểu diễn quan hệ phi tuyến. Chương này dùng năm lớp ẩn có độ rộng **64, 64, 32, 32, 16**, sau đó là một lớp đầu ra một chiều. Tổng cộng có **sáu lớp có tham số học được**; Input và ReLU không được tính vào con số này.

Luồng shape, với `B` là số mẫu trong batch và `D` là số đặc trưng sau tiền xử lý:

`[B,D] → Dense64 → ReLU → Dense64 → ReLU → Dense32 → ReLU → Dense32 → ReLU → Dense16 → ReLU → Dense1 → [B,1]`.

Tại một lớp Dense, phép tính cốt lõi là `z = xW + b`: `x` là ma trận đầu vào `[B,d_in]`, `W` là trọng số `[d_in,d_out]`, `b` là vector lệch `[d_out]` và `z` có shape `[B,d_out]`. Ví dụ, lớp đầu của CDC nhận `[B,21]`, dùng trọng số `[21,64]` và trả về `[B,64]`. ReLU giữ số dương và đưa số âm về 0, nên không đổi shape và không thêm tham số.

Ở bài toán phân loại, Dense cuối trả về logit, chưa phải xác suất. Sigmoid chuyển logit thành xác suất lớp 1; lớp 0 có xác suất bằng một trừ giá trị đó. Chọn lớp 1 khi xác suất lớn hơn 0,5; trường hợp đúng bằng 0,5 chọn lớp 0 theo quy ước argmax đã khóa. Với Ames, đầu ra là giá đã chuẩn hóa và phải đổi ngược đơn vị trước khi hiển thị.

### 2.2.4. Hợp các hàm và vai trò từng hàm

Mô hình đầy đủ có thể viết ngắn gọn `F = f_L ∘ ... ∘ f_2 ∘ f_1`, nghĩa là **đầu ra của bước trước trở thành đầu vào của bước sau**, đọc từ phải sang trái. Trong triển khai này, các bước là tiền xử lý, chuỗi Dense/ReLU và hậu xử lý. Công thức chỉ mô tả luồng xử lý, không phải thêm một thuật toán khác.

| Hàm/signature | Input → output | Vai trò và tham số | Trường hợp cần chú ý |
|---|---|---|---|
| `TensorAdapter.transform(frame)` | Bản ghi đúng schema → `[B,D]` float32 | Dùng thống kê/từ vựng train đã khóa, không fit lại | Từ chối thừa/thiếu cột; danh mục mới thành all-zero |
| `dense(x,W,b)` | `[B,d_in]` → `[B,d_out]` | Học `W,b`, tạo tổ hợp đặc trưng | Phải đúng thứ tự feature và shape trọng số |
| `relu(x)` | `[B,d]` → `[B,d]` | Phi tuyến, không có tham số | Giá trị âm thành 0; tại 0 dùng quy ước đạo hàm trong core |
| `loss_and_gradient(logits,y,task,weights)` | Dự đoán/nhãn cùng batch → loss và gradient đầu ra | BCE ổn định cho nhị phân; MSE cho hồi quy | Nhãn/weight không hợp lệ hoặc loss không hữu hạn bị từ chối |
| `loss_gradients(x,y,task,weights)` | Batch → loss, gradient theo từng tensor | Scratch lan truyền ngược qua từng lớp; native dùng autodiff | Không dùng autograd trong scratch; không bỏ batch cuối |
| `clip_gradients(grads)` | Các gradient → gradient đã giới hạn và norm ban đầu | Chặn global norm ở 1 để hạn chế cập nhật quá lớn | Không tự sửa NaN/Inf; phải báo lỗi |
| `Adam.step(weights,grads)` | Trọng số/gradient → trọng số mới | Dùng lịch sử gradient và bình phương gradient | Resume phải giữ cả trọng số, moment và số bước |
| `predict_batches(trainer,x)` | `[N,D]` → `[N,1]` | Dự đoán theo lô, giữ thứ tự mẫu | Từ chối tập rỗng hoặc kết quả không hữu hạn |
| `task_outputs(logits,"binary")` | `[N,1]` → `[N,2]` | Đổi logit thành xác suất hai lớp | Không nhầm logit với xác suất |
| `TensorAdapter.inverse_target(value)` | Giá chuẩn hóa → USD | Khôi phục đơn vị giá nhà bằng scaler train | Không dùng scaler mới fit trên validation/TEST |

Đối chiếu ba implementation: Dense/ReLU scratch nằm trong `src/common/numpy_engine.py`; Keras dùng `keras.layers.Dense` và `Activation`; PyTorch dùng `torch.nn.Linear` và `ReLU` thông qua adapter trong `src/common/backend_models.py`. Torch lưu ma trận trọng số theo layout khác, nên adapter chuyển vị khi trao đổi canonical weights. Bảng shape, parameter count và giải thích chi tiết từng function ID được sinh trực tiếp từ `model_contract.json`, không chép lại bằng tay.

### 2.2.5. Học trọng số và chọn checkpoint

Mỗi batch đi qua bốn bước: dự đoán, tính loss, tính gradient và cập nhật trọng số. Loss cho biết dự đoán lệch nhãn bao nhiêu. Gradient chỉ hướng thay đổi loss khi điều chỉnh từng trọng số. Scratch tự tính các đạo hàm và lan truyền ngược bằng NumPy; hai framework còn lại tính đạo hàm tự động trên cùng kiến trúc.

Adam dùng hai bộ nhớ phụ: trung bình gradient và trung bình bình phương gradient. Dạng cập nhật cần để đọc code là `w ← w − η m̂/(√v̂ + ε)`. Ở đây `w` là một trọng số, `η` là learning rate, `m̂` và `v̂` là hai bộ nhớ đã hiệu chỉnh bước đầu, còn `ε` tránh mẫu số bằng 0. Chi tiết hiệu chỉnh nằm trong mã và tài liệu kỹ thuật của core. Cả ba implementation dùng epsilon **sau căn của v đã hiệu chỉnh**, không thay bằng Adam mặc định có quy ước epsilon khác.

Sau mỗi epoch, mô hình được đánh giá trên toàn validation. Checkpoint có validation loss nhỏ nhất được giữ lại. Patience 6 và min_delta chỉ điều khiển lúc dừng; chúng không được dùng để bỏ qua một checkpoint có loss nhỏ hơn. Nếu bị ngắt, trạng thái resume giữ optimizer, lịch sử, checkpoint tốt nhất và trạng thái dừng sớm; không bắt đầu một thực nghiệm mới ngầm.

### 2.2.6. Liên hệ trực tiếp ba đường code

Kiến trúc không được viết thành ba bản thông số khác nhau. Cả ba dùng một computational plan, rồi adapter tạo các layer tương ứng:

```python
plan = build_plan("mlp", [D], outputs=1)
weights = canonical_weights(plan, seed=42)
```

`D` lần lượt là 21, 313 hoặc 50; plan chứa sáu Dense và năm ReLU. Đoạn chung chỉ tạo kiến trúc/trọng số ban đầu, chưa phải checkpoint đã train. Ba cách tạo trainer dưới đây là ba lựa chọn riêng, chạy trong đúng môi trường, không import hai framework GPU vào cùng process:

```python
# Scratch: môi trường scratch/torch, phép toán học bằng NumPy
trainer = ScratchTrainer(plan, weights)
```

```python
# Keras: môi trường keras, backend TensorFlow độc lập
trainer = KerasTrainer(plan, weights, device="gpu")
```

```python
# PyTorch: môi trường torch, native CUDA
trainer = TorchTrainer(plan, weights, device="gpu")
```

Vòng huấn luyện dùng cùng interface `step(x_batch, y_batch, task, sample_weight)` và `predict(x_batch)`. Trong scratch, `NumpyNetwork.forward` lặp từng bước của plan, tính `x @ W + b`, lưu activation và tự tính gradient theo chiều ngược lại trong `loss_gradients`. Keras xây functional model từ Dense/Activation rồi dùng GradientTape trong graph step; Torch xây ModuleDict gồm Linear/ReLU và dùng autograd. Chuẩn hóa layout trọng số và optimizer không làm scratch trở thành lời gọi framework. Toàn bộ mã nằm trong `src/common/numpy_engine.py`, `src/common/backend_models.py` và `src/ch02_ml/training.py`; notebook chỉ gọi lại module, không chứa bản thuật toán sao chép.

## 2.3. Dữ liệu và giao thức thực nghiệm

### 2.3.1. Ba bộ dữ liệu

| Bộ dữ liệu | Nguồn và phạm vi | Snapshot local | Đầu vào mô hình | Matched train / validation / TEST |
|---|---|---:|---:|---:|
| CDC Diabetes | [UCI 891](https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators), BRFSS 2015 | 253.680 dòng; CSV 13.494.568 byte | 21 biến; nhãn 1 gộp tiền tiểu đường/tiểu đường | 20.000 / 38.053 / 38.122 |
| Ames Housing | [De Cock, JSE 2011](https://jse.amstat.org/v19n3/decock/AmesHousing.txt) | 2.930 nhà; TXT 960.807 byte | 79 trường gốc, thành 313 chiều; giá bán USD | 2.051 / 439 / 440 |
| Bank Marketing | [UCI 222](https://archive.ics.uci.edu/dataset/222/bank+marketing) | 45.211 dòng; ZIP 1.023.843 byte | 15 biến sau khi bỏ duration, thành 50 chiều | 10.000 / 6.781 / 6.782 |

CDC có giấy phép CC0 xác minh từ nguồn upstream; Bank dùng CC BY 4.0 và phải giữ attribution. Nguồn TXT Ames phục vụ dạy học/nghiên cứu nhưng không công bố SPDX rõ ràng; tiểu luận giữ trích dẫn, không mặc định giấy phép GPL của package khác áp dụng cho TXT và không phân phối lại raw. ZIP Bank là kích thước gói nguồn, không phải chỉ dung lượng bảng dùng train. Các SHA-256, schema đầy đủ và ngày thu nhận nằm trong data cards Phase 23–24.

Ví dụ từ matched train: CDC `row_0048946` có high_bp=1, high_chol=1, BMI=24, smoker=0 và nhãn nguồn 0; Ames `row_0001475` có lot_area=8.450, ms_zoning=RL và giá nguồn 210.000 USD; Bank `row_0030605` có age=31, job=self-employed, balance=0 và nhãn nguồn 0. Đây là **nhãn quan sát**, không phải kết quả mô hình; bản ghi đầy đủ và ba mẫu mỗi dataset nằm trong `report/references/dataset_cards/v3_eda/`.

CDC mất cân bằng: train đầy đủ có 152.760 nhãn 0 và 24.745 nhãn 1. Bank có 27.946 nhãn 0 và 3.702 nhãn 1 trong train đầy đủ. Vì vậy không chỉ báo cáo accuracy: dự đoán mọi mẫu là lớp phổ biến vẫn có thể đạt accuracy cao nhưng recall lớp 1 bằng 0. Ames có trung vị giá train 160.000 USD, phân bố lệch và giá trị lớn; RMSE nhạy với vài căn dự đoán sai nhiều, nên cần đọc kèm MAE và biểu đồ sai số.

CDC có 25.772 dòng trùng feature; một số nhóm có nhãn mâu thuẫn. Các dòng này được gom khi chia, không sửa nhãn cho mô hình dễ học hơn. Ames có trường thiếu đáng kể như alley và pool_qc; thiếu có thể liên quan việc không có tiện ích, không tự hiểu là 0. Bank có giá trị danh mục `unknown` và 16 dòng trùng feature; `unknown` vẫn được giữ như một mức danh mục. Không tự xóa outlier để cải thiện kết quả.

Chia nhóm/ngẫu nhiên chỉ đánh giá khả năng tổng quát trên snapshot này. Không có patient/customer ID xác minh cho CDC và Bank, nên không khẳng định độc lập theo bệnh nhân/khách hàng. Kết quả Ames không chứng minh dự báo thị trường tương lai hoặc chuyển sang địa phương khác.

### 2.3.2. Điều kiện so sánh đã khóa

Mỗi dataset dùng ba seed 17, 42, 73. Mỗi seed có ba MLP và ba baseline, tổng cộng 54 run; trong đó có 27 run mạng sâu. Cùng một seed dùng cùng canonical initial weights và cùng thứ tự batch cho ba MLP. Tập matched train cố định theo seed lấy mẫu 42; thay seed huấn luyện không thay dữ liệu. Full validation và full TEST luôn được giữ nguyên, không gọi kết quả này là full-train track.

Cùng seed không có nghĩa quá trình train của ba framework phải giống từng bit. Thứ tự phép tính dấu phẩy động và kernel CPU/GPU có thể tạo sai khác nhỏ; qua nhiều lần cập nhật, các đường hội tụ có thể tách nhau. Vì vậy kiểm parity dùng tolerance đã khóa trên cùng bộ trọng số; độ ổn định kết quả huấn luyện được mô tả riêng bằng ba seed, không che sai khác bằng cách sao chép checkpoint từ một implementation sang hai implementation còn lại.

MLP dùng float32, batch 32, tối đa 40 epoch, learning rate 0,001, Adam beta 0,9/0,999, epsilon 10⁻⁷ và global clipping 1. Chỉ có một cấu hình siêu tham số đã khai báo; không tìm lại cấu hình sau khi nhìn TEST. Phân loại dùng trọng số lớp fit trên matched train; baseline majority không dùng trọng số. Forest có 200 cây, max_depth=12, min_samples_leaf=5, hai CPU worker. Logistic dùng C=1, lbfgs, max_iter=1.000; Ridge dùng alpha=1.

Scratch chạy NumPy trên CPU. Keras giữ TensorFlow độc lập và chạy GPU bằng `tf.function`, không XLA; PyTorch chạy CUDA eager. Đây là khác biệt đường thực thi được công khai, nên số đo không chỉ phản ánh tên framework. Hai môi trường WSL2 dùng Python 3.11.17, NumPy/dữ liệu chung và dependency đã khóa. GPU là RTX 5050 Laptop khoảng 8 GiB. TensorFlow trên sm_120 có cảnh báo PTX JIT; không gọi đường chạy này là hỗ trợ kernel native đầy đủ.

### 2.3.3. Cách đánh giá và giới hạn số đo

Phân loại dùng macro-F1, accuracy, weighted-F1, recall từng lớp, AUROC, average precision và confusion matrix. Brier và ECE với 10 bin mô tả độ lệch giữa xác suất và tần suất thực tế. Chúng chỉ là chẩn đoán: không fit thêm bộ hiệu chỉnh xác suất và không thay threshold từ TEST. Trọng số lớp có thể tăng recall nhưng làm xác suất lệch so với tần suất tự nhiên; phải đọc cả hai mặt.

Giá nhà được đánh giá bằng MAE/RMSE theo USD, R², MAPE và sMAPE. Metric không xác định được lưu null cùng lý do, không thay bằng 0. Bảng tổng hợp dùng trung bình và độ lệch chuẩn mẫu trên ba seed. Với majority/median/Logistic/Ridge, các lần chạy có thể trả cùng kết quả; không xem đó là ba tập dữ liệu độc lập hay bằng chứng kiểm định ý nghĩa thống kê.

Phân tích nhóm được khai báo trước: CDC theo mã sex của nguồn; Bank theo age dưới 60 và từ 60; Ames theo năm xây trước/từ 1980. Chỉ báo cáo support và sai số/recall/FPR phù hợp, không gọi là chứng nhận công bằng hay kết luận nhân quả. Nhóm không có lớp dương/âm được ghi rõ metric không xác định.

Thời gian huấn luyện MLP gồm các epoch, validation và ghi progress checkpoint; không gồm khởi tạo framework và kiểm parity đầu vào. Thời gian baseline gồm fit và xuất mô hình portable. Inference đo một mẫu TRAIN cố định, warm-up 5 lần rồi đo 30 lần, có đồng bộ và chuyển dữ liệu host/device; không gồm tiền xử lý hay đổi ngược đơn vị. RAM là high-water RSS của cả process riêng, không phải RAM tăng thêm của riêng mạng. VRAM là peak allocator của framework, không phải tổng VRAM trong Task Manager. Checkpoint size chỉ tính file trọng số NPZ, metadata ghi riêng.

Baseline cổ điển được fit bằng scikit-learn nhưng thời gian inference trong bảng đo bản NumPy portable, không phải `sklearn.predict` tối ưu. Đặc biệt, bản rừng cây duyệt từng cây bằng Python; số đo mô tả đường đóng gói demo đang dùng, không chứng minh Random Forest nói chung chậm hơn mạng nơ-ron.

TEST được mở theo ba batch niêm phong, mỗi batch dataset có 18 run đã khai báo. Mã evaluator, cấu hình và tất cả checkpoint được khóa trước lần mở. Mỗi run nhận một claim không thể lặp; nếu bị ngắt sau claim mà chưa có kết quả đầy đủ thì niêm phong lỗi, không tự dự đoán lại. Các phân tích và hình sau đó đọc prediction artifact đã lưu, không gọi mô hình trên TEST thêm lần nữa.
