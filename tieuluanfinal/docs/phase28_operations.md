# Vận hành Phase28 — RNN validation-only

Nghiệm thu và các sai lệch xem [biên bản](phase28_report.md).
Trạng thái phát hành lấy từ `artifacts/manifests/phase28/checkpoint.json`, khóa tại
`experiment_lock.json`. Chỉ coi COMPLETE khi khóa tồn tại và kiểm hash PASS.

## Sau phát hành: chỉ audit hoặc demo

```powershell
.\scripts\check_phase28.ps1
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.demo_phase28 -ModuleArguments @('--dataset','ch4_gold_pink_sheet')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.demo_phase28 -ModuleArguments @('--dataset','ch4_bis_house_prices')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.demo_phase28 -ModuleArguments @('--dataset','ch4_household_power')
```

Check chỉ đọc artifact/prediction, không train hoặc TEST forward. Auditor có thể cập nhật
`verification.json` (file mutable bị loại khỏi release lock). Demo dùng fixed TRAIN request;
serving thực tế là NumPy CPU, không phải native TensorFlow/PyTorch dù checkpoint được train
bằng các framework đó. Kernel/framework GPU không cần import để chạy3 notebook demo.

Không chạy lại prepare/controller/train/worker/finish/receipt để tạo bằng chứng mới sau khóa.
`finish_phase28.ps1` có nhánh sau-lock chỉ verify; không dùng ResumeTraining cho run đã chọn.
Mọi sửa file đã khóa cần revision mới giữ bằng chứng cũ. Không sửa raw/spec/core/Ch2/Ch3/Ch5.

## Phạm vi đã khóa

132 selection:27 RNN main +81 RNN rolling +24 baseline last-value/seasonal-naive.
Ba dataset Gold/BIS/Power, seed17/42/73; mỗi baseline một lượt/view. Mạng3 RNN32 + Dense16/8/3
có6 learnable layers; h reset mỗi window. Scratch NumPy/manual BPTT CPU, Keras TensorFlow
GPU/XLA và PyTorch GPU/eager độc lập. Common initialization/batch schedule, batch32,
max40epoch/patience6/min_delta1e-5, Adam canonical lr0,001/eps1e-7, global clip1.

WindowData dùng DatasetView/TensorAdapter, frozen train stats và canonical feature order.
Cache row features cap64MiB; batch gather NTF, không dựng toàn bộ window tensor.
Mọi horizon của một window cùng target-time partition; không random split theo window.
CSV nguồn có cả snapshot được đọc vật lý, nhưng không materialize/predict TEST windows.
Metric dùng target float64 gốc; context chỉ dùng quá khứ đã quan sát, không impute nhãn.

Main matched train531/2.504/12.000 và validation115/588/5.033. Lookback24/12/168; horizon
1/3/6 tháng,1/2/4 quý,1/6/24 giờ. Mỗi rolling fold có scaler/prefix riêng; fold chồng lịch
không phải thí nghiệm độc lập. Chỉ main checkpoints được bàn giao cho TEST Phase29.
Power chỉ một hộ; Gold/BIS revised snapshot không có vintage/lịch công bố để suy ra giao dịch thật.

## R2 và các guard bắt buộc giữ nguyên

Release gốc pin52 source; revision r2 pin thêm exporter/controller, hai test và authorization.
Không sửa/format các source đã pin. R2 strict native-CPU receipts áp dụng108 RNN,
rtol1e-4/atol1e-5; giữ riêng so sánh GPU/CPU gốc. Scratch là round-trip manual engine.

Power/PyTorch seed17: best checkpoint đã train11 epoch/best5, được khôi phục không thêm update.
Giữ FAIL GPU/cuDNN→CPU và checkpoint hash. Original train_seconds/peak_ram_bytes/peak_vram_bytes
là null theo recovery schema riêng, loại khỏi cost aggregate (n=2); không sửa schema Phase22,
không lấy peak recovery hoặc elapsed snapshot làm số đo train. Quality vẫn đủ3 seed.

Window index gap phase28.1 và Keras XLA đã kiểm trước declaration. Giữ probe graph ban đầu,
probe XLA, training logs và RED XML. XLA Assert có thể bị bỏ nên host finite/shape/gradient checks
không được bỏ. CPU TensorFlow receipt cố ý ẩn CUDA, không diễn giải warning NO_DEVICE là fallback.

## Lịch sử chạy và nghiệm thu — không còn queue chờ

Controller r2 đã hoàn tất132/132, exit0/PID=null. Bộ chờ Windows PID23296/session55253 là
lịch sử: nó đã thoát khi finish gặp lỗi root resolution. Hai entrypoint đã sửa, có RED/GREEN;
không dùng PID cũ để kết luận process còn sống. Không khởi động lại queue đã hoàn tất.

Nghiệm thu tiếp tục tuần tự, không train lại:39 Torch-env unit +1 Keras GPU unit,
263 regression +1 preservation +3 report/notebook +2 PowerShell root tests =309 test duy nhất.
108 CPU receipts và saved-prediction audit PASS; không mở TEST. XML focused/RED/lịch sử
không cộng vào total. Coverage RNN90,2216%;7 hình đã xem, report đã seal.

Auditor round-trip hiện hành đối chiếu full metric row theo name/horizon, không list order.
Bản auditor cũ giữ nguyên byte; đọc `phase28_audit_roundtrip_note.md`.
Không sửa metric gốc để qua audit. Chú giải rolling/forecast được đưa ngoài axes trước seal.

Hai file `.acceptance_waiter.lock`/`.acceptance_pipeline.lock` dùng exclusive handles chống
trùng writer; file còn tồn tại không có nghĩa process còn giữ lock. Khi chưa release, cần kiểm
process thực và lock trước bất kỳ pipeline/coverage writer nào. Hiện không còn controller train.
Sau release không ghi đè XML/coverage/pretest evidence hoặc chạy lại TEST.

## Bàn giao Phase29

`holdout_handoff.json` liệt kê27 RNN main và6 baseline, `trained_validation_registry.json`
tách khỏi registry initialized Phase25. Phase29 triển khai LSTM thật trên cùng windows/scaler/
budget, kiểm6 learnable layers, BPTT/gates/serialization và khai báo policy CPU export trước train.
Chỉ sau khi cả hai họ cùng evaluator/approved IDs khóa mới mở TEST chung một lần.
Không mở lại TEST Ch2/Ch3/Ch5 hoặc tuning sau TEST.

API HTTP/React/Render vẫn Phase32–33; ghép DOCX/render QA Phase34–35. Không nhầm demo
NumPy CLI với deployment live. Không tự thực hiện Phase29 khi người dùng mới yêu cầu Phase28.
