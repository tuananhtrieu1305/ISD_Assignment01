# Phase29 — checkpoint RESUME2, 19/10/2026

## Trạng thái

Người dùng đã yêu cầu tiếp tục; **không còn USER PAUSE**. Phase29 vẫn IN_PROGRESS,
không phải COMPLETE. Snapshot bàn giao: **73/108 selection**, đang chạy
`ch4_household_power_lstm_keras_s17_main`. Vàng và BIS đã đủ72 lượt main/rolling;
Power scratch seed17 main hoàn tất14 epoch, chọn best epoch7 (zero-based).
Đọc lại manifest thay vì dùng các con số/PID snapshot này làm trạng thái hiện tại.

- Queue WSL PID3767, tool session29693; chỉ một queue/coverage writer.
- Bộ chờ hậu kiểm Windows PID22436, tool session42613 đang chạy
  `scripts/finish_phase29_development.ps1 -Watch -Distribution Ubuntu`.
- Bộ chờ giữ exclusive file handle `.development_pipeline.lock`, đợi đủ108 selection
  và controller finished/PID=null, rồi chạy tests/CPU receipts/audit/coverage/proof tuần tự.
  **Không tự tạo seal, mở TEST, viết report hoặc release.** Không mở thêm acceptance,
  coverage writer hoặc bộ chờ khi process này còn sống. File lock tồn tại không đồng nghĩa
  handle còn sống: kiểm process/session thực trước khi tiếp tục.
- Host C còn32,56GiB ở lần đo gần nhất; giữ reserve5GiB. Không hạ guard, xóa dữ liệu,
  đổi pagefile/WSL hoặc train lại các selection đã có.

## Runtime recovery r1 đã PASS

`Ubuntu-24.04` không còn đăng ký, runtime user anhca cũ không tồn tại. Đã khai báo recovery,
cài đúng lock vào Ubuntu24.04.4/user tuananh:

`/home/tuananh/.local/share/ai-term-paper-v3/`

Python3.11.17, uv0.13.1; hai venv riêng cho PyTorch2.14.1+cu130 và
Keras3.15.1/TensorFlow2.21.0. Bốn probe độc lập torch/TF ×GPU/CPU đều PASS
matmul/CNN/RNN/LSTM update. Không fallback, nâng dependency hoặc dùng Python Windows.
Shared-package parity với môi trường khóa PASS. GPU RTX5050/driver591.74 vẫn nhận đúng.

Receipt, declaration, probes/logs và hash nằm tại
`artifacts/manifests/phase29/runtime_recovery/r1/`. Ba file recovery đã pin không sửa/format.
Môi trường cũ, uv.lock và69 source train giữ hash; đã chạy controller `--stage status`
qua `check_sources()` sau recovery. Năm selection có sẵn không train lại.

Mọi wrapper mới **phải thêm `-Distribution Ubuntu`**. Không chạy bootstrap/doctor cũ
vì chúng có thể ghi đè metadata/evidence đã khóa. GPU CLI nằm tại
`/usr/lib/wsl/lib/nvidia-smi`. Phiên runtime đã thay đổi: không mô tả chi phí thực nghiệm
là một phiên máy liên tục hoặc benchmark cô lập; các unit test synthetic nhẹ chạy trong
lúc queue còn hoạt động cũng cần được ghi rõ khi phân tích hiệu năng.

## Evaluator và audit chuẩn bị trước TEST

Các file mới ngoài69 source train:

- `holdout_data.py`: gate tiêu thụ trước đọc/gather TEST, main scaler frozen, kiểm ID/
  calendar/same-series/target partition, không điền nhãn.
- `holdout_cache.py`: bảng feature dùng chung + index cửa sổ, NPZ numeric64MiB,
  hash trên đúng bytes được load, parity mọi window, targetsfloat64, không pickle.
- `joint_evaluation.py` và `scripts/phase29_joint_test.py`: approved60 main
  (27RNN+27LSTM+6baseline), claim từng model trước inference, một TEST forward/window,
  weights/optimizer không đổi, không timing warmup/repeats trên TEST, fail-sealed nếu ngắt.
- `scripts/phase29_receipts.py`:108 native CPU receipts độc lập trên4 TRAIN ID cố định,
  CUDA ẩn trước import backend; giữ ngưỡng1e-4/1e-5 và GPU diagnostic gốc.
- `scripts/verify_phase29_validation.py`: audit saved validation predictions/history/
  minimum/batch schedule/optimizer/checkpoint/receipts; chỉ forward4 TRAIN để round-trip.
- `scripts/prepare_phase29_pretest.py`: unique tests/0skip/global coverage>=80%, lint,
 108selection/receipts + runtime/audit evidence; khóa fingerprint evaluator trước TEST.
- `scripts/verify_phase29_test.py`: chỉ đọc cache/prediction đã lưu để recompute metric,
  kiểm3 seal evaluated/count1,60run/111900prediction row; không nạp model/TEST forward.

**38 test evaluator synthetic PASS**, evidence `new-evaluator-tests-r3.xml`; lint16 file mới
PASS, PowerShell parser PASS. Đây chưa phải nghiệm thu toàn Phase29. Các RED/attempt XML
giữ lại, không cộng chúng vào số test cuối. Chưa có actual108 CPU receipts/full validation
audit/pretest proof, seal hoặc TEST thật tại thời điểm snapshot.

Không sửa/format các file trong EVAL_SOURCE_FILES khi pipeline hậu kiểm đang hoạt động;
auditor/proof sắp ghi fingerprint và receipts sẽ pin writer source. Thay đổi sau proof
cần revision mới. Không sửa69 file train đã khai báo hoặc evidence pretrain cũ.

## Tiếp tục thế nào

1. Kiểm checkpoint, active_controller, queue3767/session29693 và bộ chờ22436/session42613.
   Queue lỗi thì bảo toàn log/progress/best, tìm nguyên nhân; không chạy acceptance/TEST.
2. Chờ108 selection/controller thoát. Theo dõi bộ chờ; không tự chạy cùng coverage/receipt
   writer. Nó dừng nếu bất kỳ bước nào lỗi; sửa cần revision theo evidence đã được tạo,
   không overwrite proof/XML đã seal hoặc nới tolerance.
3. Sau pretest PASS, đọc audit/tests/coverage/source fingerprint/approved IDs. Chỉ khi đầy
   đủ mới chạy rõ ràng `scripts.phase29_joint_test --stage lock-test`, rồi `--stage test`
   qua runtime hiện hành. Một seal/dataset cho cả RNN/LSTM. Không chạy TEST Phase28 hoặc
   mở lại TEST Ch2/Ch3/Ch5. Claim đã consumed không được tự retry.
4. Sau TEST: `scripts.verify_phase29_test` chỉ audit saved outputs; tổng hợp mean/sampleSD,
   horizon/series/rolling/efficiency/gate diagnostics; giữ telemetry null của orphan RNN
   Power/Torch/s17, qualityn3/costn2. Không dựng số thay thế.
5. Viết bản thảo Ch4 RNN–LSTM mới, hình300dpi/SVG và xem QA, notebook/demo CPU, test bổ sung,
   biên bản/experiment_lock/check wrapper. Giữ bản RNN Phase28 nguyên byte. DOCX34–35,
   API/UI32–33, không mô tả CLI NumPy là Render live. Chưa tự bắt đầu Phase30.

Lý thuyết LSTM cơ bản/từng cổng/hợp hàm/6 learnable layers/code ba loại đã có draft
`report/sections/v3/ch04_lstm_theory.md`; chưa có bản Ch4 hợp nhất với TEST được nghiệm thu.
