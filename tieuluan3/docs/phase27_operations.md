# Vận hành Phase27 — CNN V3

Trạng thái hiện hành nằm ở `artifacts/manifests/phase27/checkpoint.json` và
`active_controller.json`. Kế hoạch gốc là `TIEU_LUAN_AI_V3_EXECUTION_PLAN.md`.
Không tự chạy Phase28 hoặc sửa DOCX/UI/API live trong Phase27.

**Sau nghiệm thu 18/10/2026:** đủ 27 CNN + 9 majority và cả 3 seal TEST evaluated/count1.
Không chạy lại các lệnh train/TEST lịch sử dưới đây. Chỉ dùng `scripts/check_phase27.ps1`
để kiểm hash/audit. Bản thảo hiện hành là `report/sections/v3/ch03_cnn_r2.md`, pointer
`artifacts/manifests/phase27/active_report.json`; bản đầu được giữ nguyên làm lịch sử.

## Các lớp dữ liệu

- Source raw, Phase24 index/splits/preprocessing và core Phase25 giữ nguyên.
- Development cache ở `data/processed/v3/phase27/<dataset>_development/`:
  uint8 NHWC + int64 label + Unicode ID, `allow_pickle=False`, hash từng file.
  Chỉ matched train + full validation: 412 / 7.050 / 10.000 ảnh.
- Mọi decoded model pixel được kiểm hash Phase24. CIFAR dùng một lượt TAR.GZ streaming,
  binary record, không pickle hoặc extract archive.
- Cache TEST riêng chỉ được dựng sau consumed claim, không bằng cờ override của DatasetView.
- Reserve host C tối thiểu 5 GiB; cap 256 MiB/cache. Không dùng free ảo WSL root.
  Không tự xóa env, raw, artifact niêm phong hoặc dữ liệu người dùng để lấy chỗ.

## Nguồn đã khai báo trước training

`release.json` khóa source/config/contract/protocol/environment; 27 CNN + 9 majority.
`src/ch03_cnn/`, prepare/controller/worker và coverage INI không được sửa sau khai báo.
Sửa cần revision có phiên bản và giữ bằng chứng cũ, không xóa khóa để chạy lại.
Không có augmentation trong matched preprocessing Phase24. Class weights chỉ áp dụng IDRiD.

## Lệnh (PowerShell, từ workspace)

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase27_controller --stage status
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase27_controller --stage train
```

Không chạy controller thứ hai khi PID cũ còn sống. Worker chạy tuần tự, Keras/Torch native GPU,
scratch NumPy CPU. Không chạy benchmark/probe/coverage writer khác song song. Controller ghi log
riêng từng run trong `artifacts/manifests/phase27/logs/` và dừng khi worker thất bại.

Resume đọc `artifacts/models/v3/ch03_cnn/<run>/progress.json`, pin hash immutable epoch state.
State gồm weights/m/v/iterations, best weights, history và early stopping. Không thêm epoch
khi state đã dừng sớm. Conv Adam slots chuyển HWIO↔OIHW đúng, không dùng `.T` bốn chiều.
Train seconds cộng các đoạn chạy và loại khoảng tạm dừng; metric timestamp thuộc invocation
hoàn tất. Peak RSS là của process đo, không tự gộp/ước lượng peak của process đã bị ngắt.
Không tự train lại run có selection. Nếu crash giữa ghi best và selection, cần audit/recovery
có phiên bản, không xóa checkpoint để tạo lại kết quả.

## TEST

Chỉ sau nghiệm thu tất cả validation selection, parity, unit/regression, coverage, provenance,
khóa evaluator/pretest evidence mới được gọi stage `lock-test`, sau đó stage `test`.
Controller không tự chuyển từ train sang TEST. Ba dataset có seal Phase27 riêng; không tái sử dụng
seal Ch2/Ch5. Full TEST counts: IDRiD103 / EuroSAT4.050 / CIFAR10.000.

Claim đã ghi nhưng chưa có kết quả hoàn chỉnh là quyền đã tiêu thụ, không tự retry.
Đánh giá lỗi chuyển `failed_sealed`; không mở lại để sửa metric. Phân tích sau TEST dùng file
prediction JSONL.GZ đã lưu. Saliency chỉ lấy fixed TRAIN sample, không chọn ảnh theo TEST.

## Bàn giao

Config/model/functions ở `artifacts/manifests/phase27/runs/`; checkpoints ignored tại
`artifacts/models/v3/ch03_cnn/`. Số đo mới ở `artifacts/metrics/phase27/`, prediction ở
`artifacts/predictions/phase27/`. Registry trained phải tách registry initialized Phase25.
CPU inference portable phải ghi rõ training implementation khác actual serving backend.
Tích hợp HTTP/React/Render thật thuộc Phase32–33; DOCX cuối thuộc Phase34–35.

## Chuỗi nghiệm thu sau khi train xong

`scripts/check_phase27.ps1` chỉ đọc trạng thái trước release; sau release kiểm hash/audit,
không train hoặc mở lại TEST. `scripts/finish_phase27.ps1` không được chạy đồng thời với
controller đang sống: nó tự gọi controller resume trước unit/regression/coverage.
Mặc định finish dừng ở pretest. Trong scope hoàn tất Phase27, sau khi mọi gate đạt mới dùng:

```powershell
.\scripts\finish_phase27.ps1 -EvaluateTest
```

Lệnh chạy TEST one-shot có claim, audit chỉ đọc prediction, CPU export/smoke, report và notebook QA.
Nó **chưa** phát hành lock cuối: phải xem đủ 7 hình PNG, ghi visual QA với đúng hash, đọc lại
biên bản/coverage và chạy `scripts.release_phase27 --lock` sau đó. Không sửa auditor sau pretest
verification; nếu phát hiện lỗi phải có revision, không ghi đè proof đã khóa.

Visual QA đã tạo revision trình bày r2 bằng `scripts.revise_phase27_report`: sửa ba confusion
grids/common count scale và chú thích, giữ nguyên mọi metric/prediction/checkpoint. Chứng từ
`revisions/r2/report_generation.json`, `revisions/r2/report-tests.xml`, `visual_qa.json`.
Không gọi lại producer sau khóa; tích hợp Phase34 phải đọc pointer hiện hành thay vì bản thảo r1.
