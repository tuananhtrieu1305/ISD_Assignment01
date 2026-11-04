# Lõi mô hình V3 — hướng dẫn từ Phase25

Lõi dùng chung nằm trong `src/common/`. Không gọi helper transform EDA để tạo tensor train.
Không dùng notebook V2 làm runner V3. Mạng được khởi tạo ở Phase25 chưa phải model đã train.

## Đường dữ liệu thống nhất

`catalog → split IDs → frozen statistics → tensor adapter → computational plan → backend`

`DatasetView(dataset_id).ids("train")` trả matched train IDs cố định; validation luôn đầy đủ.
`ids("train", matched=False)` chỉ dành cho full-data track được khai báo riêng.
Loader phát triển từ chối TEST và quarantine; không có cờ boolean để bỏ niêm phong.
Evaluator one-shot có seal/config/code/approved run IDs được triển khai ở Phase26–29.
RNN và LSTM chỉ mở TEST chung ở Phase29. Ch5 không được chạy lại evaluator TEST.

Thứ tự tensor bảng: các biến số theo `input_columns`, sau đó các biến danh mục theo
`input_columns`, mỗi biến dùng đúng thứ tự vocab train đã khóa. Danh sách
`output_feature_names` được lưu rõ trong adapter sidecar; thứ tự key JSON không có ý nghĩa.
Không đổi mean/std/median/vocab hoặc fit lại trên validation/TEST.

Ảnh: Pillow RGB/BILINEAR theo resolution đã khóa, uint8 → float32/255.
Scratch/Keras nhận NHWC, PyTorch training batch nhận NCHW. Các phương thức parity của
`TorchBackend` nhận **NHWC canonical** rồi đổi layout nội bộ; không chuyển NCHW lần thứ hai.
EuroSAT dùng mapping tên lớp → ID mới, cố định theo thứ tự tên từ train; CIFAR giữ ID nguồn;
IDRiD giữ grade 0–4. Class weights được map cùng ID, không tự tính lại.

Loader ảnh hiện là đường tham chiếu kiểm chứng, chưa tối ưu I/O train. Đặc biệt CIFAR TAR.GZ
được mở/giải mã lại khi lấy mẫu nên test hai batch nhỏ có thể mất khoảng 30 giây.
Phase27 phải thêm batch reader/cache uint8 có budget và test pixel/ID parity trước train;
không nhân bản raw hoặc cache toàn bộ float32 tensor của ảnh.

Chuỗi: NTF (batch, thời gian, feature), chỉ materialize batch window được yêu cầu.
Target không bao giờ được impute. `DatasetView(id, fold=1..3)` dùng IDs và scaler riêng của fold.
Cache series chỉ là bảng nhỏ, không phải tensor của mọi window. Cache thiếu được dựng từ raw,
stable sort và dùng cùng độ chính xác CSV đã khóa trước khi transform; không refit statistics.
`TensorAdapter.inverse_target` đưa dự đoán về đơn vị gốc trước tính metric.

## Một kiến trúc cho ba implementation

`build_plan` đọc kiến trúc và kích thước từ giao thức Phase22. MLP có 6 Dense; CNN có
5 Conv và 2 Dense; RNN/LSTM có 3 recurrent và 3 Dense. Activation/pool không được đếm.
Pooling CNN dùng chỉ số **0-based** trong protocol `[1,3]`, tức sau Conv thứ 2 và thứ 4.
Sau Conv thứ 5 có global average pooling. Output của mạng là logits/giá trị chuẩn hóa;
loss hoặc bước suy luận mới đổi logits thành xác suất. Không coi logits là xác suất.

Trọng số canonical: Dense IO, Conv HWIO, recurrent W(input, gates×hidden),
U(hidden, gates×hidden). LSTM có thứ tự i/f/g/o, forget bias = 1. PyTorch chuyển layout và
đặt bias recurrent thứ hai bằng 0/frozen. Đếm riêng tham số trainable, không tính bias frozen.
Trạng thái h/c reset mỗi window; hai tầng recurrent đầu trả toàn chuỗi, tầng cuối trả bước cuối.

`canonical_weights(plan, seed)` dùng NumPy để ba backend nhận cùng điểm khởi tạo. Các seed
17/42/73 không làm đổi split/subset. Không dùng `tiny=True` cho model thực nghiệm thật;
đây chỉ là fixture kiểm tra đạo hàm nhỏ. Scratch forward/backward/BPTT chỉ dùng NumPy.

`make_contract → validate_model → render_functions` tạo contract hợp schema Phase22,
kiểm chuỗi shape, công thức parameter count, số lớp và thứ tự hợp hàm. Renderer xuất bản
kỹ thuật `F = f_L ∘ ... ∘ f_1`, bản dễ đọc `đầu vào → các bước → đầu ra`, bảng hàm/shape,
signature, vai trò, corner case, công thức tối thiểu và mapping sang ba implementation.
Report/UI sẽ đọc cùng JSON, không tự mô tả kiến trúc khác.

Schema sidecar mới nằm ở `src/common/schemas/phase25/`; **không thay schema/spec Phase22**.
Registry hiện hành `artifacts/manifests/phase25/initialized_contract_registry.json` có
`lifecycle=initialized_only`, `inference_ready=false`. Parameter count là số đo kiến trúc,
không phải bằng chứng mô hình có chất lượng dự đoán hay sẵn sàng deploy.

## Các hàm trainer cốt lõi, giải thích ngắn

| Hàm | Input → Output | Vai trò / lưu ý |
|---|---|---|
| `seed_everything(seed, backend)` | seed → RNG được đặt lại | Bật deterministic, không bảo đảm bitwise giữa CPU/GPU |
| `batch_order(size,batch_size,seed,epoch)` | số mẫu → list batch index | Cùng thứ tự cho ba framework; lưu lịch/hash trong runner |
| `NumpyNetwork.forward(x, trace=True)` | tensor → output và trace | Ghi shape ở từng bước, không dùng autograd |
| `loss_and_gradient(logits,y,task,sample_weight)` | dự đoán/nhãn → loss và gradient | BCE/softmax CE ổn định; MSE; weighted mean chia tổng weight |
| `NumpyNetwork.backward(dy)` | gradient output → gradient weight/input | Truyền ngược, gồm BPTT và các cổng LSTM |
| `clip_gradients(grads,max_norm=1)` | gradient → gradient đã chặn, norm cũ | Chặn global norm, không clip từng tensor riêng |
| `Adam.step(weights, gradients)` | trọng số/gradient → trọng số mới | Adam chuẩn `sqrt(v_hat)+epsilon` |
| `NativeAdam.step(x,y,task,sample_weight)` | batch → loss/norm, update native | Update GPU không chép trọng số/gradient về NumPy |
| `EarlyStopping.observe(validation_loss,epoch)` | loss → save_best/stop | Lưu minimum thật; min_delta chỉ điều khiển patience |
| `regression_metrics(y,pred,horizons,series)` | giá trị đơn vị gốc → metric | RMSE/MAE/sMAPE, breakdown horizon/series, macro-series RMSE |
| `classification_metrics(y,probabilities)` | ID/xác suất → metric | F1/recall/confusion/AUROC/AP; thiếu support → null + reason |
| `inference_timing(function,synchronize)` | lời gọi → p50/p95 | 5 warmup + 30 lần đo, batch 1; nêu rõ có transfer/layout |
| `DeviceMonitor.start/finish` | workload → RAM/VRAM/time | VRAM allocator peak đo thật; RSS là high-water cả process |
| `ArtifactStore.save/load_checkpoint` | mảng + provenance → NPZ/metadata | Không pickle, pin metadata hash khi phục vụ/đọc từ manifest |

Adam Keras mặc định dùng epsilon-hat, không trùng quy ước đã khóa. `NativeAdam` TensorFlow
dùng slots/update rõ ràng để giữ `sqrt(v_hat)+1e-7`; không dùng stock Keras Adam cho matched track.
PyTorch dùng Adam với cùng epsilon/betas/lr và global norm 1. Gradient của CPU TensorFlow
cũng nằm trong device context CPU, không chỉ forward.

Loss phân loại nhận logits, không nhận xác suất đã sigmoid/softmax. Nhãn binary có shape N×1,
multiclass là vector ID N; target hồi quy N×outputs. NaN/OOM/timeout phải ghi failed,
không tự giảm model/batch/sample cho riêng một framework.
Metric binary hiện dùng argmax trên `[1-p,p]`: p>0,5 là lớp 1, trường hợp bằng nhau chọn lớp 0.
F1 dùng fixed class set/`zero_division=0`; AUROC/AP thiếu class và recall của lớp không có mẫu
được trả null kèm lý do. Runner phải giữ công khai quy ước này, không dùng threshold TEST tuning.

## Kiểm tra số và đo hiệu năng

Đạo hàm số dùng float64, sai phân trung tâm trên tiny synthetic data, tránh điểm gấp ReLU.
Gradient backend dùng symmetric relative L2 **cho từng tensor**:
`norm(g_ref-g)/(norm(g_ref)+norm(g))`, mẫu số sàn 1e-12, ngưỡng khóa 1e-3.
Ngưỡng này không phải phần trăm sai số của từng phần tử gần 0. Luôn lưu thêm max absolute error.
Forward dùng rtol 1e-4, atol 1e-5. IEEE FP32 được chọn rõ cho PyTorch/cuDNN và TensorFlow.

Probe bộ nhớ dùng tensor giả có **đúng shape/batch size** Phase24/22, forward/backward/Adam thật.
Đây không phải benchmark accuracy hay peak của toàn bộ training. VRAM là allocator của framework,
không bao gồm driver/ứng dụng khác; không so trực tiếp allocator PyTorch/TensorFlow như tổng VRAM.
RSS là peak cả đời process, không phải bộ nhớ tăng thêm của riêng model đang đo.
Timing probe gồm transfer/layout/output-to-host, chưa phải timing model-only cuối cùng.

Checkpoint NPZ được kiểm hash, size, dtype/shape, finite values, expanded ZIP size và
`allow_pickle=False`. Provenance bắt buộc có 9 hash: dataset, split, subset, preprocessing,
adapter, config, code, environment và model contract. Với nguồn ngoài, phải pin hash của metadata
bằng manifest tin cậy; hash nằm trong một file metadata tự sửa không chứng minh tính xác thực.
NPZ hiện là checkpoint **trọng số** portable/CPU-loadable, không phải snapshot resume đầy đủ
optimizer/RNG/early-stopping. Phases26–29 phải lưu trạng thái resume và run ledger riêng nếu cần.

## Lệnh

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.prepare_phase25
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase25
```

Trước khóa, probe có thể chạy bằng module `scripts.phase25_backend_probe`, tham số
`--implementation pytorch|keras --device cpu|gpu`. Sau khóa, producer/probe chỉ kiểm chứng,
không ghi đè evidence. Đổi core cần revision có phiên bản và biên bản; không xóa khóa.

Nguồn API đã đối chiếu: [Keras LSTM](https://keras.io/api/layers/recurrent_layers/lstm/),
[Keras Adam](https://keras.io/api/optimizers/adam/),
[PyTorch LSTM](https://docs.pytorch.org/docs/2.14/generated/torch.nn.LSTM.html),
[PyTorch CUDA/IEEE FP32](https://docs.pytorch.org/docs/2.14/notes/cuda.html).
