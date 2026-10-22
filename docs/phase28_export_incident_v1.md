# Phase28 — biên bản dừng kiểm chứng xuất CPU, v1

Ngày ghi nhận: 18/10/2026. Trạng thái phase vẫn **IN_PROGRESS**, chưa nghiệm thu.

## Hiện trạng đã xác minh

- 90/132 selection đã hoàn tất: 74 RNN và 16 baseline. Đã kiểm lại SHA-256 của
  854 reference duy nhất, gồm 52 source đã khai báo, config/contract và artifact được
  selection tham chiếu: PASS. Đây là kiểm hash, không phải audit lại toàn bộ metric.
- Controller gốc kết thúc exit code 1; `active_controller.json` có `pid=null`.
  Checkpoint cũ còn PID 4229 đã được cập nhật để tránh hiểu nhầm rằng train vẫn chạy.
- Lượt `ch4_household_power_rnn_pytorch_s17_main` đã train đủ điều kiện dừng sớm:
  11 epoch, 4.125 optimizer update; best epoch 5 (chỉ số lưu bằng 4), bad_epochs=6.
  Lượt này **chưa có selection thành công**, không tính vào 90 lượt trên.
- 42 selection còn thiếu gồm lượt đã train nhưng chưa xuất này và 41 lượt còn lại.
  Không có TEST artifacts Phase28; không chạy lại TEST Ch2/Ch3/Ch5.

## Bằng chứng nguyên nhân

Giữ nguyên checkpoint và bốn TRAIN window đầu theo khai báo; không cập nhật weights,
không chạy validation hoặc TEST trong hai phép chẩn đoán. Ngưỡng gốc luôn là
`rtol=1e-4, atol=1e-5`.

| So sánh với NumPy CPU float32 | Sai số tuyệt đối lớn nhất | Đạt ngưỡng gốc |
|---|---:|---|
| PyTorch GPU, cuDNN fused | 2,5168061e-5 | Không; 1/12 đầu ra |
| PyTorch GPU, cuDNN tắt riêng khi chẩn đoán | 5,9604645e-7 | Có |
| PyTorch native CPU | 4,7683716e-7 | Có |

NumPy float64 và PyTorch CPU float64 cũng không đạt khi đối chiếu với GPU fused;
hai cách tính CPU float64 lại khớp nhau ở mức gần machine precision. Checkpoint
khớp chính xác best weights trong optimizer snapshot. Bằng chứng cho thấy khác biệt
số học theo kernel GPU/cuDNN, không cho thấy hỏng checkpoint hay sai thứ tự weights.
Việc tắt cuDNN chỉ dùng để chẩn đoán, không thay backend/kernel train đã khai báo.

Các bằng chứng giữ nguyên:

- `artifacts/manifests/phase28/attempts/ch4_household_power_rnn_pytorch_s17_main_20261018T081020547830Z.json`
- `artifacts/manifests/phase28/attempts/export_numeric_probe_v1.json`, SHA-256
  `6820a97a24a938950081b84658016b4d3a6186aadb2dca614775b2f1df340e48`.
- `artifacts/manifests/phase28/attempts/export_numeric_probe_v2.json`, SHA-256
  `1048484fa2e5c58d33cc60af252089012125e217ae0a53ff6d185f02ed49f78d`.
- Best NPZ SHA-256 `e3437f37fab6f26196f9a7d72601d4de29a1518a96f9143ed9167316bc054e82`;
  best metadata SHA-256 `5511295b71f317c738334c27aea3e5a118ef4abd7d933de4de0a82ecaa1e2911`.
- `resume/epoch_011.json` SHA-256
  `d2e2078d2d38ef05d9a25379c8d406d06d1d0541fe3216dbbafedcd40d9c28a4`.

## Quyết định cần chốt trước khi tiếp tục

**Đề xuất r2, chưa triển khai hoặc coi là được duyệt:** dùng native CPU độc lập làm
reference cho kiểm xuất NumPy CPU, vẫn giữ nguyên ngưỡng gốc. Áp dụng kiểm bổ sung
thống nhất cho cả 108 RNN; lưu riêng kết quả đối chiếu GPU/CPU, bao gồm FAIL hiện tại.
Không gọi phép đối chiếu GPU/CPU gốc là PASS. Đây là thay đổi reference của bước
nghiệm thu export sau khai báo, nên cần người dùng đồng ý trước khi thực hiện.

Nếu được duyệt, cần làm tuần tự:

1. Khai báo revision r2 mới, pin source gốc/release, 90 selection và checkpoint lỗi;
   không sửa 52 source/config đã khóa, không nới tolerance, không tuning theo kết quả.
2. Viết test cho strict native-CPU export gate, khôi phục từ completed training state,
   chặn nhầm stage lỗi và bảo toàn artifact; kiểm RED/GREEN trước khi chạy thật.
3. Hoàn tất lượt orphan từ best weights hiện có, không train thêm. Được tính lại
   validation từ đúng checkpoint này để tạo prediction bị mất trong process lỗi,
   ghi rõ recovery; không chọn lại epoch/hyperparameter và không mở TEST.
4. Process gốc đã mất telemetry cuối trước khi lưu. Snapshot có elapsed_seconds
   35,7892374 nhưng không thay thế được full train wall hoặc peak RAM/VRAM gốc.
   Báo thiếu và loại lượt này khỏi aggregate train-time/RAM/VRAM (main Power PyTorch
   còn n=2), không điền số ước lượng hoặc 0. Nếu cần cấu trúc nullable phải tạo
   recovery schema có phiên bản, tuyệt đối không sửa schema Phase22 đã khóa.
5. Chạy tiếp 41 lượt còn lại qua runner có phiên bản, bỏ qua 90 selection hoàn tất.
   Lưu telemetry trước export để tránh mất thêm bằng chứng nếu có lỗi tương tự.
6. Audit saved predictions, native CPU receipts, tests hai env tuần tự, regression,
   preservation, coverage, notebook/demo và visual QA; sau đó mới khóa toàn phase.

Không chạy lại controller gốc hoặc `finish_phase28.ps1 -ResumeTraining` lúc này:
lượt orphan đã có `best.npz`, trong khi runner gốc không có đường finalization-only.
Không đổi kernel train/giảm lookback/đổi seed để né lỗi. Chưa đổi UI/API/DOCX.
