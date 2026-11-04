# Chạy và kiểm tra Chương 2 V3

Runtime bắt buộc: WSL2 và hai môi trường đã khóa ở Phase21. Mọi lệnh dưới đây chạy từ PowerShell tại `C:\DATA\assign`. Không cài lại package bằng Python Windows.

## Manifest và trạng thái

Revision hiện hành là **r2**, dưới `artifacts/manifests/phase26/revisions/r2/`. Root Phase26 còn giữ preflight v1 bị từ chối trước train do object cache; không dùng release v1 để tiếp tục. `revision_r2.json` giải thích thay đổi, `preflight_v1_source/` giữ source trước sửa.

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase26_controller -ModuleArguments @('--stage','status')
```

`active_controller.json` chứa PID WSL. Kiểm đúng PID/module nếu cần; không liệt kê command line toàn máy. Nếu một controller vẫn chạy, không khởi động cái thứ hai. Xem epoch và lỗi trong `logs/`; `runs/<run_id>/selection.json` chỉ có khi run hoàn tất.

## Tiếp tục huấn luyện

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase26_controller -ModuleArguments @('--stage','train')
```

Controller bỏ qua run đã hoàn tất; mỗi run mới đi qua hash checks và dùng đúng venv theo framework. Các run chưa hoàn tất chỉ được resume từ optimizer state hợp lệ. Không thay code, config, architecture, subset hoặc budget để một run cũ tự tiếp tục. Nếu finalization bị ngắt và đã có một phần artifact immutable, dừng kiểm tra thay vì xoá/ghi đè.

Các ID dạng `ch2_cdc_diabetes_mlp_keras_s42` hoặc `ch2_ames_housing_random_forest_s42`. Có 54 run: 27 MLP và 27 baseline. Device scratch/classical là CPU; Keras/PyTorch train bằng GPU. Train tuần tự để không chạy hai framework GPU cùng lúc.

## Đánh giá TEST — không phải lệnh demo

Chỉ dùng khi đủ 54 validation selection và audit trước TEST đã PASS:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module coverage -ModuleArguments @('json','--rcfile=experiments/configs/v3/phase26_coverage.ini','-o','artifacts/manifests/phase26/revisions/r2/coverage_combined.json')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase26_roundtrip_v1 -ModuleArguments @('--pretest')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase26_controller -ModuleArguments @('--stage','lock-test')
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase26_controller -ModuleArguments @('--stage','test')
```

Mỗi dataset có một seal và 18 approved run. Không xóa `.claimed`, `evaluation.started`, result hoặc seal. Run đã claim nhưng thiếu result không được thử lại; batch phải fail-seal. Sau evaluated, controller không gọi forward TEST lại. Audit, report và đồ thị chỉ đọc prediction đã lưu. Ch5 hoàn toàn không tham gia evaluator này.

## Demo CPU sau khi checkpoint đã có

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.demo_phase26 -ModuleArguments @('--dataset','ch2_ames_housing','--seed','42')
```

Đổi dataset thành `ch2_cdc_diabetes` hoặc `ch2_bank_marketing`. Demo dùng bốn mẫu TRAIN cố định và checkpoint của sáu phương pháp. Với checkpoint native, inference chuyển sang NumPy CPU portable đã kiểm parity; không gọi đó là Keras/Torch native inference. Notebook mỏng trong `experiments/notebooks/v3/ch02_ml/` sẽ được sinh cùng report; dùng kernel WSL `ai-v3-torch`.

## Báo cáo và nghiệm thu

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.summarize_phase26
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase26_roundtrip_v1 -ModuleArguments @('--lock')
```

Chỉ lock sau khi đã QA hình, bảng, nội dung, test/regression và tài liệu cuối. Sau lock, `scripts/check_phase26.ps1` chỉ kiểm lại artifact; không train, thay bằng chứng test hay mở TEST. Báo cáo tích hợp DOCX thuộc Phase34–35; API/React mới thuộc Phase32–33. Model NPZ/cache ignored nên clone repo một mình không đủ cho demo; đóng gói phục vụ Render sẽ được thực hiện ở Phase32 với artifact budget rõ ràng.
