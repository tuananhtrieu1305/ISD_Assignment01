# Phase 26 — Nghiệm thu Chương 2 V3

Nghiệm thu nội dung và thực nghiệm: **PASS**, ngày 2026-10-17. Trạng thái khóa cuối, số file và hash nằm trong `artifacts/manifests/phase26/revisions/r2/verification.json` và `experiment_lock.json`.

## Kết quả bàn giao

- Hoàn tất **54 run**: 3 dataset × 3 seed (17,42,73) × (3 MLP + 3 baseline), trong đó **27 MLP được train độc lập** bằng NumPy CPU, Keras/TensorFlow GPU và PyTorch GPU.
- Cả ba MLP cùng canonical weights ban đầu, matched train, thứ tự batch, loss/Adam/clipping và budget. Kiến trúc 5 Dense ẩn 64–64–32–32–16 + Dense đầu ra: **6 learnable layers**. Tham số CDC/Ames/Bank lần lượt **9.249 / 27.937 / 11.105**.
- Matched train 20.000/2.051/10.000; full validation 38.053/439/6.781; full TEST **38.122/440/6.782**. Không đổi split, không fit lại preprocessing và không giảm TEST.
- **3 seal evaluated, evaluation_count=1**, mỗi seal duyệt 18 run. Mỗi forward TEST có claim duy nhất; 54 prediction TEST và 54 metric TEST được giữ nguyên. Các audit/hình sau đó chỉ đọc prediction, không gọi lại TEST.
- **108 dòng run-summary, 564 dòng aggregate**, 5 CSV và 5 hình tổng quan PNG300dpi/SVG. Có mean/sample SD, per-class metric, calibration, confusion, learning curves, sai số giá nhà và nhóm chẩn đoán.
- **54/54 checkpoint có CPU load/parity** trên bốn mẫu TRAIN cố định. Demo seed42 đã chạy 18 model; ba notebook đều được validate và chạy chương trình demo CPU, không import framework GPU.
- **299 test PASS, 0 skip**: 33 test Phase26, 263 regression, 1 preservation, 2 report/notebook acceptance. Coverage các module Ch2 trước TEST **87,64%**, sau toàn bộ pipeline **92,12%**. Không cộng các lượt RED hoặc lượt chạy lặp vào tổng này.

## File chính

| Đường dẫn | Vai trò |
|---|---|
| `report/sections/v3/ch02_ml.md` | Bản thảo Ch2 gồm lý thuyết cơ bản, dữ liệu, code/mapping, hợp hàm, kết quả và mục deploy ngắn |
| `report/sections/v3/ch02_ml_theory.md` | Phần lý thuyết do biên tập; ưu tiên trực giác, sơ đồ và ít công thức |
| `src/ch02_ml/` | Trainer/resume, baseline portable, diagnostics, controller contracts và evaluator |
| `artifacts/manifests/phase26/revisions/r2/release.json` | Khai báo 54 run trước train; source/config hashes |
| `artifacts/manifests/phase26/revisions/r2/trained_registry.json` | Registry 54 checkpoint đã train/đánh giá; demo seed42 và serving backend NumPy CPU ghi nhãn rõ |
| `artifacts/models/v3/ch02_ml/` | NPZ trọng số/optimizer progress ignored; metadata có 9 provenance hashes |
| `artifacts/metrics/phase26/`, `artifacts/predictions/phase26/` | Metric và prediction validation/TEST |
| `artifacts/metrics/phase26/tables/` | runs, aggregate, layers, test_groups, preprocessing CSV |
| `artifacts/figures/phase26/` | Chất lượng, loss, calibration, confusion, giá nhà; 5 PNG và 5 SVG |
| `report/references/functions/v3_ch2/` | Ba tài liệu hàm sinh từ model contract |
| `experiments/notebooks/v3/ch02_ml/` | Ba notebook mỏng dùng kernel WSL ai-v3-torch |
| `docs/phase26_operations.md` | Lệnh trạng thái, demo và các hạn chế tiếp tục/TEST |

## Đọc kết quả đúng phạm vi

Trên TEST, Random Forest có macro-F1 trung bình 0,6508 (CDC) và 0,6538 (Bank). Ames: MLP Keras có RMSE trung bình khoảng 33.990 USD, Random Forest khoảng 34.024 USD; chênh lệch khoảng 34 USD nhỏ hơn nhiều độ dao động giữa seed, không phải bằng chứng thắng ổn định. Majority có accuracy cao nhưng recall lớp 1 bằng 0. Giữ các kết quả âm và mọi điểm sai số lớn, không lọc TEST để làm đẹp số.

Scratch CPU nhanh hơn native GPU với MLP nhỏ trong đường chạy này. Keras dùng TensorFlow graph, PyTorch dùng CUDA eager; TensorFlow/sm_120 có cảnh báo PTX JIT. Không suy đây là thứ hạng framework nói chung. Native inference đo chuyển host/device; baseline inference đo **NumPy portable**, không phải sklearn.predict tối ưu. Rừng cây portable duyệt bằng Python nên số đo không đại diện mọi implementation Random Forest.

RAM là high-water RSS của process riêng; VRAM là peak allocator, không phải tổng VRAM Task Manager. Thời gian train MLP gồm validation/progress I/O nhưng không gồm khởi tạo framework/parity. Trường `preprocessing_seconds` trong validation_details là nạp/cache development; phép biến đổi một raw record TRAIN được đo riêng, warm-up5/30 lần đo và ghi `preprocessing.csv`. Cấu hình máy: i7-13620H 10 lõi/16 luồng, RTX5050 Laptop 8151MiB, driver591.74; WSL2/Python3.11.17, Torch2.14.1+cu130, Keras3.15.1/TF2.21.0. Không khóa xung/nhiệt.

Brier/ECE và nhóm sex/age/year_built chỉ để chẩn đoán mô hình. Không fit calibrator hay threshold từ TEST; không tuyên bố chứng nhận công bằng, chẩn đoán bệnh, định giá thị trường hiện tại hay quan hệ nhân quả. Ba seed dùng cùng split; baseline xác định có thể cho cùng metric, không coi là ba mẫu dữ liệu độc lập.

## Hai điều chỉnh được lưu lịch sử

1. **Preflight v1** dừng ngay bước nạp cache trước optimizer update vì CDC group array dtype object. Safe loader từ chối pickle đúng. Giữ nguyên khai báo/config/receipts/log v1 và snapshot **33 source nguyên byte** ở `preflight_v1_source/`. **r2** đổi group sang Unicode, thêm guard object và dùng cache riêng; không đổi raw/split/budget/hyperparameter.
2. Auditor gốc dùng float64 mặc định khi đọc JSON, làm ECE tính lại lệch khoảng 1e-9–1e-8 so với bin mean float32 gốc. Thêm **`scripts.verify_phase26_roundtrip_v1.py`** và regression RED/GREEN, khôi phục dtype theo method/checkpoint metadata. **Không nới rtol/atol 1e-10, không sửa checkpoint/metric/prediction, không sửa source train/evaluator đã khai báo**. Auditor mới được hash trong pretest proof trước khi mở TEST; auditor gốc vẫn giữ nguyên. Đọc `audit_revision.json`.

## Bảo toàn và kiểm chứng

- 11.357 raw file, DOCX V2 và active provenance Phase23 giữ hash; 7 config, 23 metric, 10 prediction TEST Ch5 không đổi, Ch5 run_count=1.
- 31 spec file Phase22, 294 file Phase24, 219 file Phase25 và environment lock vẫn được kiểm từ auditor; registry initialized Phase25 không bị ghi đè.
- Bốn warning sklearn V2 (artifact1.9.1/runtime1.9.0) được giữ/công khai; không phải checkpoint Ch2 mới. Không load pickle cho model Ch2.
- Ruff toàn bộ source/test mới PASS; kiểm notebook chỉ thực thi chương trình literal đã review và đối chiếu notebook khớp hoàn toàn. Scan pattern secret giới hạn source Phase26 không thấy pattern phổ biến; không phải audit toàn lịch sử.
- Đã xem cả 5 PNG, kiểm nhãn/đơn vị/SD/axis/count và đối chiếu hash qua tái sinh. Biểu đồ tổng quan có thể tách panel ở Phase34 để bảo đảm cỡ chữ trên trang Word; QA từng trang DOCX ở Phase35.
- Không sửa UI/API, không build DOCX, không cài package/env, không xóa dữ liệu, không commit/reset hoặc thay Git history.

Kiểm lại sau khóa: `scripts/check_phase26.ps1` (chỉ audit, không train/TEST). Tiếp theo **Phase27 — CNN** khi người dùng yêu cầu; không tự chạy trong Phase26.
