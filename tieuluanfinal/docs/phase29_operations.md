# Vận hành Phase29 — LSTM và TEST chung RNN–LSTM

Trạng thái hiện tại đọc `artifacts/manifests/phase29/checkpoint.json`. Chưa COMPLETE khi
chưa có release lock và audit sau phát hành PASS. Không dùng kết quả khởi tạo Phase25 làm
checkpoint đã train. Không ghi đè bất kỳ file trong khóa Phase22–28 hoặc TEST Ch5.

## Track phát triển

108 LSTM = 3 dataset × 3 implementation × 3 seed × (main + 3 rolling folds).
Giữ nguyên 24 baseline đã train/đánh giá ở Phase28, không train lại RNN hoặc baseline.
Chỉ27 LSTM main và27 RNN main +6 baseline main mới đủ điều kiện bàn giao TEST chung;
81 rolling checkpoint mỗi họ chỉ phục vụ development. Không chọn seed theo TEST.

Ba LSTM32 + Dense16/ReLU + Dense8/ReLU + Dense3 tuyến tính:6 learnable layers.
Không đếm các cổng hoặc timestep thành layer. Cùng frozen windows/scalers/canonical feature order,
initial weights, seed17/42/73, matched train IDs, full validation, Adam sqrt(v_hat)+epsilon,
clip global norm1, batch32/max40epoch/patience6/min_delta1e-5/120phút mỗi run như Phase28.
Trạng thái h/c reset mỗi window; không shuffle thời gian trong window. Không thêm dropout/tuning.

Scratch NumPy CPU gọi manual BPTT Phase25. PyTorch GPU eager dùng canonical slots W/U
transpose và bias_hh=0/frozen. Keras vẫn TensorFlow GPU độc lập, graph tf.function **không XLA**
để native LSTM có thể dispatch cuDNN. Đây là execution policy khai báo/probe trước train,
không phải đổi backend hoặc siêu tham số. Host finite checks vẫn giữ nguyên.
API tham chiếu: [Keras LSTM](https://keras.io/api/layers/recurrent_layers/lstm/),
[PyTorch LSTM](https://docs.pytorch.org/docs/2.14/generated/torch.nn.LSTM.html).
Context7 không có trong tool inventory; đã đối chiếu tài liệu chính thức thay thế.

CPU export khai báo từ đầu: portable NumPy so native CPU cùng weights/first4 TRAIN,
rtol1e-4/atol1e-5. Giữ cả raw output/error/PASS hoặc FAIL của GPU–CPU làm diagnostic;
không nới tolerance và không thay validation native GPU bằng CPU để che sai khác.
Gates/carry equation/input-gradient diagnostics chỉ trên4 TRAIN windows cố định, không suy
ra quan hệ nhân quả hay khẳng định LSTM luôn tốt hơn RNN.

## Lệnh theo thứ tự

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase29_preflight -ModuleArguments @('--inventory')
.\scripts\run_experiment.ps1 -Framework scratch -Module scripts.phase29_preflight -ModuleArguments @('--method','scratch')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase29_preflight -ModuleArguments @('--method','pytorch')
.\scripts\run_experiment.ps1 -Framework keras -Module scripts.phase29_preflight -ModuleArguments @('--method','keras')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.prepare_phase29
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase29_controller -ModuleArguments @('--stage','train')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase29_controller -ModuleArguments @('--stage','status')
```

Chỉ một controller/worker/coverage writer. Đọc PID thực trước khi tiếp tục, không chạy hai queue.
Source trong release.json được pin trước optimizer update; thay đổi phải tạo revision giữ lịch sử.
Lưu epoch optimizer/m/v/iterations/history/best/early stopping; nếu crash thì kiểm nguyên nhân,
không tự retrain run đã chọn. RAM là high-water process, VRAM là peak allocator, không tổng GPU.
Nếu resume, phải ghi rõ phạm vi đo RAM/VRAM; không bịa telemetry process đã mất.
Giữ reserve host C5GiB; không dựa vào free ảo WSL root hoặc tự xóa env/dữ liệu.

## Gate trước TEST và nghiệm thu còn lại

Sau108 selection: kiểm hash/parity/serialization/receipts, test hai env tuần tự, regression,
preservation và coverage>=80%. Khóa cả hai họ/main checkpoint/config/approved IDs/evaluator
trước claim TEST; claim được tiêu thụ trước materialize, crash không cho mở lại.
Evaluator mới phải có test synthetic cho leakage, hash mismatch, duplicate/failed claim.
Không chạy TEST bằng controller phát triển; module này không có lệnh TEST.

Sau TEST chỉ audit saved predictions, không TEST forward/tuning. Sinh bảng RNN–LSTM theo
dataset/horizon/series và mean±SD seed, giữ null train/RAM/VRAM orphan RNN Power/PyTorch17,
cost n=2/quality n=3. Viết Ch4 dễ hiểu, hợp hàm và từng hàm/cổng; xuất notebook/demo CPU,
xem toàn bộ hình rồi seal và release thật. HTTP/React32–33, DOCX34–35, không gọi CLI là deploy live.
