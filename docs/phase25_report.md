# Phase25 — lõi dùng chung, model contract và hợp hàm

Ngày 17/10/2026. Trạng thái: **COMPLETE**.
Không train dữ liệu thật, không tuning/đánh giá model trên TEST, không sửa UI/API hay DOCX.

## Sản phẩm

- 11 module mới trong `src/common/`: tensor adapter, data access, model/shape/parameter core,
  NumPy engine, hai backend native, Adam native, seed/trainer hooks, metric, parity, artifact và device.
- 9 tensor adapter sidecar, 12 computational plans/configs và **36 model contracts**
  (3 MLP + 3 CNN + 3 RNN + 3 LSTM, mỗi họ/dataset có scratch/Keras/PyTorch).
- Registry: `artifacts/manifests/phase25/initialized_contract_registry.json`.
  Tất cả là `initialized_only`, `inference_ready=false`, **không phải model đã train**.
- 36 bộ JSON/CSV bảng hàm và 36 Markdown hướng dẫn tại `report/references/functions/v3/`.
  Mỗi bộ có hợp hàm kỹ thuật, luồng dễ đọc, shape, parameter count, signature, vai trò,
  công thức cần thiết, giải thích ký hiệu, ví dụ, corner case và mapping ba implementation.
- Hai schema sidecar mới ở `src/common/schemas/phase25/`; dùng lại schema model Phase22,
  không sửa `src/common/schemas/v3/` hoặc protocol đã khóa.
- Runner nghiệm thu `scripts/check_phase25.ps1`, producer `scripts.prepare_phase25`,
  probe `scripts.phase25_backend_probe`, verifier `scripts.verify_phase25`.

Hướng dẫn chi tiết và giới hạn: [model_core_v3.md](model_core_v3.md).

## Sửa vấn đề thứ tự feature và label

Thống kê Phase24 được giữ nguyên. Adapter mới dùng thứ tự `input_columns` và vocab đã khóa,
ghi `output_feature_names` rõ ràng; test trước/sau JSON `sort_keys=True` cho cả fixture và dữ liệu thật.
Không sửa/format module dữ liệu cũ, không fit lại trên validation/TEST.
Ch2 có chiều input lần lượt **21 / 313 / 50** (CDC/Ames/Bank).
Ch4 có **4 / 51 / 14** feature (Gold/BIS/Power), lookback **24 / 12 / 168**.

EuroSAT nhãn chuỗi được map sang ID cố định từ các lớp train; CIFAR và IDRiD giữ ID nguồn.
Class weights dùng cùng mapping; ảnh NHWC/NCHW được kiểm pixel parity.
Chuỗi chỉ tạo tensor cho window đang dùng, không lưu bản nhân rộng mọi window.
Cả 9 rolling folds dùng scaler/IDs riêng đã khóa; cache thiếu tái dựng từ raw không refit.
Loader phát triển từ chối TEST/quarantine, không có cờ bỏ niêm phong.

## Đếm lớp và tham số

| Dataset | Họ | Lớp học được | Tham số trainable |
|---|---|---:|---:|
| CDC | MLP | 6 | 9.249 |
| Ames | MLP | 6 | 27.937 |
| Bank | MLP | 6 | 11.105 |
| IDRiD | CNN | 7 | 10.157 |
| EuroSAT | CNN | 7 | 10.322 |
| CIFAR-10 | CNN | 7 | 10.322 |
| Gold | RNN / LSTM | 6 / 6 | 6.035 / 22.067 |
| BIS | RNN / LSTM | 6 / 6 | 7.539 / 28.083 |
| Power | RNN / LSTM | 6 / 6 | 6.355 / 23.347 |

Không đếm pooling/activation/time step/gate/container. PyTorch bias recurrent thứ hai là
0/frozen; số tham số học được khớp canonical NumPy và Keras. Contract bác bỏ model thiếu lớp,
shape bị đứt, parameter count giả, hàm/thứ tự hợp hàm không khớp.

## Kiểm tra và những vấn đề đã xử lý

Đã có test RED trước implementation. Đạo hàm số dùng float64/tiny synthetic data, sai phân
trung tâm; fixture tránh điểm gấp ReLU, không đổi initialization thực nghiệm.
Parity có forward, loss, gradient và ba bước Adam; canonical initialization dùng chung.
LSTM gate order i/f/g/o, forget bias 1; các recurrent state reset giữa window.

Keras Adam mặc định dùng epsilon-hat khác quy ước giao thức. Update TensorFlow được hiện thực
native với denominator `sqrt(v_hat)+1e-7`, không chuyển gradient/weights sang NumPy khi update.
Đã sửa device context cho cả backward và update TensorFlow, không chỉ forward.
Early-stopping lưu loss validation thấp nhất thật; min_delta chỉ dùng cho patience.

Probe ban đầu dùng thêm kiểm tra elementwise gradient quá nhạy với giá trị gần 0 và thất bại
ở PyTorch GPU RNN. Lần thử được giữ trong `attempts/`. Phép đo nghiệm thu được định nghĩa rõ:
symmetric relative L2 từng tensor, ngưỡng protocol **1e-3**; lưu cả max absolute error.
IEEE FP32 được chọn riêng cho matmul/conv/RNN; không đổi protocol, seed hoặc dataset theo TEST.

Checkpoint NPZ không pickle, có hash/size/dtype/shape/finite/budget, pin metadata hash tùy manifest
tin cậy và **9 provenance hashes bắt buộc**. E2E synthetic kiểm update → save → load CPU →
forward/parity → giải thích contract. Đây là checkpoint trọng số, không phải snapshot resume optimizer.

## Giới hạn / bàn giao

Nghiệm thu: **330 test PASS, 0 skip** (61 core Torch + 6 Keras + 263 regression),
coverage statement+branch **95,67%**, từng module >=89,9%. Lint/format **28 file Python PASS**.
16 trường hợp parity (4 họ × 2 backend × CPU/GPU) và 24 probe kích thước trên GPU PASS.
Peak allocator lớn nhất: PyTorch **125.947.904 byte (~120,1 MiB)**,
TensorFlow **134.422.272 byte (~128,2 MiB)**; không phải peak toàn training.
Scan pattern secret giới hạn đúng source/test Phase25 không thấy pattern phổ biến;
không phải audit toàn history hoặc chứng nhận không có lỗ hổng dependency.

Khóa **219 file**: `artifacts/manifests/phase25/core_lock.json`, SHA-256
`596e500edf30f4ab6440eb050f3ff2c274c30a9e02e062831a338ad83fa647d1`.
Verifier giữ nguyên 31 spec file Phase22 và 294 file Phase24, Ch5 TEST run_count=1.
Producer chạy lại sau khóa PASS, chỉ kiểm chứng. Đối chiếu độc lập trên Windows:
219/219 hash khớp. Verifier Phase22/24 cuối PASS, giữ 62 provenance file Phase23
và snapshot metadata cũ 58 file; môi trường và các baseline bảo toàn.

- Chưa có metric chất lượng trên dataset thật hoặc checkpoint deploy V3; chỉ chuẩn bị lõi.
- Probe bộ nhớ dùng tensor giả đúng shape/batch đã khóa; số này không phải peak toàn training.
  Allocator VRAM không bao gồm driver/process khác. RSS là high-water cả đời process.
- TensorFlow còn warning sm_120/PTX JIT nhưng probe chạy trên GPU thật; không fallback backend.
- Các process coverage có thể báo module-not-imported khi chỉ chạy một backend; coverage cuối
  gộp **tuần tự** từ unit/integration/E2E và CPU/GPU probes, không cho hai writer chạy song song.
- Bốn warning sklearn V2 1.9.1/1.9.0 vẫn được công khai; không sửa artifact niêm phong để bỏ warning.
- Loader ảnh tham chiếu, đặc biệt CIFAR TAR.GZ, chưa tối ưu train I/O. Phase27 cần batch/cache
  uint8 có memory budget và test pixel/ID parity trước train, không nhân bản raw.
- Phase26 phải tạo run ledger/evaluator có seal, metric đơn vị gốc và checkpoint **mới**,
  không ghi đè registry initialized này. Nhóm so sánh từng run phải khóa thêm seed/run ID cụ thể.
- Phase28 chỉ validation; Phase29 mở TEST RNN/LSTM chung sau khóa cả hai họ. Ch5 không mở lại TEST.
- Không thay môi trường/dependency, không commit/reset/history rewrite hoặc xóa dữ liệu người dùng.

## Lệnh kiểm chứng

```powershell
.\scripts\check_phase25.ps1
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase25
```

Sau khóa, producer/probe/check runner chỉ kiểm chứng artifact đã khóa, không chạy lại để ghi đè.
Kết quả nghiệm thu cuối, coverage từng module, test counts và hashes nằm trong
`artifacts/manifests/phase25/verification.json` và `core_lock.json`.

Tiếp theo: **“làm phase 26” — ML/MLP trên CDC, Ames và Bank**.
