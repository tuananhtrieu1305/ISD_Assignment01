# Tiểu luận AI — V3

Kế hoạch đang hoạt động: [TIEU_LUAN_AI_V3_EXECUTION_PLAN.md](TIEU_LUAN_AI_V3_EXECUTION_PLAN.md).
Lệnh `làm phase 20` đến `làm phase 35` được thực hiện theo file này. Hai kế hoạch Phase 0–19
được giữ làm lịch sử.

Tiểu luận gồm lịch sử AI, ML cơ bản, CNN, RNN–LSTM, KG–RAG và hệ đa agent. Phase 20 đã gom
source về cấu trúc mới và đóng băng bản phát hành V2. Runtime V3 dùng WSL2/GPU;
xem [hướng dẫn môi trường](docs/environment_v3.md) và manifest nghiệm thu thực tế.

Phase 22 đã khóa [SRS V3](docs/srs_v3.md), [giao thức thực nghiệm](experiments/configs/v3/protocol_v3.json)
và [outline sáu chương](report/outline_v3.json). Xem [biên bản Phase 22](docs/phase22_report.md).
**Phase 23 đã nhập bổ sung IDRiD**: 11 snapshot tự động và ZIP Disease Grading do người dùng tải;
IDRiD đủ 516 ảnh/nhãn (413 train, 103 test), giấy phép CC BY 4.0 trong ZIP.
Registry V3 đủ 18 ID: 15 `ready`, 3 task view Ch6 `declared`.
Khóa provenance mới gồm 62 file; khóa gốc và snapshot 58 metadata cũ được giữ nguyên.
**Phase 24 đã hoàn tất**: 18 card EDA, 9 split, 9 rolling folds, 55 bảng CSV, 19 hình;
263 test đạt, coverage khoảng 98%, khóa 294 artifact/code/test file.
Catalog dữ liệu dùng tiếp: `data/catalog_v3.json`; xem [biên bản Phase 24](docs/phase24_report.md).
**Phase 25 đã hoàn tất**: 9 tensor adapter, 12 kiến trúc, 36 model/function contracts;
330 test PASS, coverage 95,67%, CPU/GPU parity đạt, khóa 219 file.
Xem [biên bản Phase25](docs/phase25_report.md) và [hướng dẫn lõi](docs/model_core_v3.md).
Registry Phase25 vẫn là `initialized_only`, không ghi đè bằng checkpoint đã train.
**Phase26 đã hoàn tất**: 54 run ML/MLP trên CDC/Ames/Bank, trong đó 27 MLP train độc lập;
3 batch TEST niêm phong một lần, 299 test PASS, coverage cuối 92,12%, khóa 1.032 file.
Manifest hiện hành: `artifacts/manifests/phase26/revisions/r2/`; registry trained riêng với Phase25.
Đọc [bản thảo Chương 2](report/sections/v3/ch02_ml.md), [biên bản nghiệm thu](docs/phase26_report.md)
và [hướng dẫn demo/kiểm tra an toàn](docs/phase26_operations.md).
**Phase27 đã hoàn tất**: 27 CNN (5 Conv + 2 Dense) và 9 majority trên IDRiD/EuroSAT/CIFAR-10.
3 TEST seal đều evaluated/count1; 293 test PASS/0 skip, coverage 93,11%; khóa 2.378 file.
Xem [bản thảo Chương 3 hiện hành — r2](report/sections/v3/ch03_cnn_r2.md),
[biên bản nghiệm thu CNN](docs/phase27_report.md) và [vận hành CNN](docs/phase27_operations.md).
`artifacts/manifests/phase27/active_report.json` chọn revision trình bày; bản đầu giữ nguyên.
Kiểm chỉ-đọc bằng `scripts/check_phase27.ps1`; không train/TEST lại các run đã khóa.
**Phase28 đã hoàn tất**: 108 RNN (27 main +81 rolling) và24 baseline causal trên Gold/BIS/Power.
309 test PASS/0 skip, coverage90,22%;223.861 prediction validation được audit,
108 native-CPU receipts PASS, khóa7.386 file. TEST RNN/LSTM vẫn chưa mở.
Xem [bản thảo Chương4A — RNN](report/sections/v3/ch04_rnn.md),
[biên bản nghiệm thu](docs/phase28_report.md) và [vận hành RNN](docs/phase28_operations.md).
R2 giữ nguyên checkpoint/FAIL GPU–CPU và ghi null số đo train bị mất của một lượt; không train lại.
Kiểm chỉ-đọc bằng `scripts/check_phase28.ps1`; không ghi đè source/checkpoint/XML/coverage đã khóa.
**Tiếp theo: “làm phase29” — LSTM**, giữ cùng dữ liệu/budget; chỉ TEST chung sau khi cả hai họ khóa.
Chưa deploy hay build DOCX V3; các bước đó thuộc Phase32–35. Không chạy lại TEST đã khóa.
Xem [biên bản Phase 23](docs/phase23_report.md) và [hướng dẫn dataset](docs/datasets/README.md);
UI/API và DOCX V3 vẫn thuộc các phase tích hợp sau; không nhầm checkpoint Ch2 mới với bundle UI V2.

| Đường dẫn | Nội dung |
|---|---|
| `apps/api/` | Python API và bundle demo hiện tại |
| `apps/web/` | React UI, nguồn style cho bản V3 |
| `src/` | Code cần tái sử dụng và vị trí module theo chương |
| `experiments/` | Cấu hình và notebook nguồn cũ để tham khảo |
| `data/` | Registry, raw snapshots local và split manifests |
| `artifacts/` | Metrics, hình, provenance và checkpoint được chọn |
| `report/` | Manuscript, sections, ảnh và bibliography |
| `releases/v2/` | DOCX/PDF V2, báo cáo mẫu, source snapshot có hash |
| `tests/api/` | Regression API hiện tại |
| `docs/repository_manifest.md` | Danh sách giữ lại, đường dẫn mới và cách khôi phục |

Bản báo cáo hiện tại: [DOCX V2](releases/v2/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx).
Các notebook trong `experiments/notebooks/legacy/` giữ nguyên nội dung để tham khảo; runner V3
sẽ được xây ở Phase 25–29 trước khi chạy lại thực nghiệm.

Chuẩn bị/kiểm tra runtime từ PowerShell ở repository root:

```powershell
.\scripts\bootstrap.ps1
.\scripts\doctor.ps1
```

Chạy Python/API/notebook trong VS Code **Remote WSL**, bằng interpreter đã khóa;
không dùng `python` mặc định của Windows. Lệnh chi tiết có trong hướng dẫn môi trường.

Chạy React:

```powershell
cd apps/web
npm ci
npm run dev
```

`render.yaml` đã trỏ tới `apps/api` và `apps/web`. `data/raw`, môi trường Python, cache,
`node_modules` và checkpoint huấn luyện mới được ignore. Các bundle demo nhỏ V2 được giữ
để UI/API còn có thể chạy trong thời gian chuyển đổi.
