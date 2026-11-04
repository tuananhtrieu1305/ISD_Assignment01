# Phase 23 — nghiệm thu thu nhận dataset và provenance

Ngày 17/10/2026. **COMPLETE, đã bổ sung IDRiD do người dùng tải thủ công.**
Đây là nghiệm thu nguồn dữ liệu, không phải nghiệm thu mô hình hay báo cáo cuối.
Không có huấn luyện, EDA/split hay DOCX V3 mới trong phase này.

## Đã lưu được

- **11 snapshot tự động từ nguồn chính thức**, tổng **313.065.095 byte**, có receipt SHA-256:
  Iris, MNIST, metadata ILSVRC2012, CDC diabetes, Ames, Bank, EuroSAT RGB,
  CIFAR-10 binary, World Bank Pink Sheet, BIS WS_SPP và household power.
- **IDRiD Disease Grading ZIP**, 212.405.123 byte; 516 ảnh RGB 4288×2848 và hai CSV nhãn
  (413 train, 103 test). Đã kiểm CC BY 4.0 từ hai file license đi kèm; không cần CSV tải riêng.
- **18 dataset manifest/thẻ nguồn** tại `artifacts/manifests/datasets/` và
  `report/references/dataset_cards/v3/`. Đây là thẻ phiên bản nguồn, chưa phải EDA đầy đủ.
- `data/registry.yaml` V3 đủ 18 ID: **15 ready, 3 Ch6 task view declared**, không còn IDRiD pending.
  Không nhầm `ready` của nguồn với việc đã chia tập/fit preprocessing/huấn luyện.
- Toàn bộ **11.345 raw file Ch5** khớp hash baseline trước migration. Không tải lại,
  không nhân bản raw Ch5/Ch6, không mở lại TEST để tuning.
- Downloader HTTPS có giới hạn byte/disk, kiểm hash, không ghi đè dữ liệu đã có;
  đọc/hash archive không giải nén, chặn traversal/link/special files và sai Content-Range.
  CIFAR dùng binary TAR, không nạp pickle từ nguồn tải về.
- Các script: `acquire_datasets`, `build_phase23_registry`, `verify_phase23`,
  `verify_idrid_manual`, `update_phase23_idrid`; source inspectors, provenance revisions và test.

| Nguồn | Số đo local đã có | Lưu ý cho Phase 24 |
|---|---:|---|
| Iris | 150 dòng, 4 biến | Minh họa lịch sử, không phải thí nghiệm Ch2 |
| MNIST | 70.000 ảnh | Giữ official split; không dùng thay dataset CNN V3 |
| ILSVRC2012 | 1 trang metadata, 0 ảnh | Không tải full ImageNet |
| CDC diabetes | 253.680 dòng, 21 biến | Binary; ID không phải feature |
| Ames original | 2.930 dòng, 82 cột nguồn | SalePrice → sale_price; loại PID/Order |
| Bank original | 45.211 dòng | bank.zip!bank-full.csv; bỏ duration |
| EuroSAT RGB | 27.000 ảnh RGB 64×64 | Không dùng bản multispectral 2,1 GB |
| IDRiD grading | 516 ảnh RGB 4288×2848 | 413 train/103 test; ID gồm split vì basename bị trùng |
| CIFAR-10 binary | 60.000 ảnh RGB 32×32 | 50.000 train + 10.000 test gốc; không nạp pickle |
| Pink Sheet October 2026 | 801 tháng | Vintage sửa đổi mới nhất, không tuyên bố real-time |
| BIS WS_SPP bulk | 35.780 quan sát quý không thiếu | Chưa chọn panel nominal, không gộp unit/real/YoY |
| Household power | 2.075.259 dòng phút | Chưa tổng hợp giờ hoặc điền thiếu |
| MedQuAD raw | 47.441 QAPair; 16.407 answer không rỗng | Toàn corpus, không nhầm với 247 diabetes query lịch sử |
| FinQA raw | 9.200 record, gồm private_test | Giữ chính sách/split Ch5 đã khóa |
| Wikidata | 10 snapshot entity | Hỗ trợ KG, không phải QA benchmark thứ ba |

Phần mẫu/phân bố/nhận xét đầy đủ và leakage audit thuộc Phase 24; không trình bày
các con số đếm nguồn trên là metric mô hình hoặc số training window.

## Ngoại lệ và giới hạn còn giữ

**CIFAR-10 đã hoàn tất:** tải Range từ cùng nguồn chính thức sau khi ổ C được giải phóng
lên khoảng 11,3 GiB. File 170.052.171 byte khớp MD5 tác giả
`c32a1d4ab5d03f1284b67883e8d87530`; SHA-256
`c4a38c50a1bc5f3a1c5537f2155ab9d68f9f25eb1ed8d9ddda3db29a59bca1dd`.
Đã xóa đúng partial cũ 24 MiB sau kiểm path/hash/không còn writer; không xóa dữ liệu khác.
File tạm có thể tạo lại bằng tải nguồn chính thức; không tính partial là dataset.

**IDRiD đã nhập thành công:**
`data/raw/ch3/idrid/manual/B_Disease_Grading.zip`; SHA-256
`8a9f4752b35d74cc35ff48b21ad44f295a6f800110ec218fc2d1c264803e4d8c`.
Tên ngoài `B. Disease Grading.zip` được chuẩn hóa vì schema đường dẫn Phase22 không cho khoảng trắng;
byte ZIP, tên và nội dung bên trong không đổi. Không giải nén trùng hoặc sửa CSV/ảnh.
Train/test cùng có `IDRiD_001` nên dùng ID `train/IDRiD_001`, `test/IDRiD_001`.
Xem [biên bản nhập IDRiD](datasets/idrid_manual.md). Đây là nghiệm thu nguồn, chưa phải
nghiệm thu ma trận mô hình CNN ba dataset; không dùng official test để tuning.

Ba task view Ch6 chỉ `declared`, chưa tạo benchmark; sẽ làm ở Phase 31.

Registry/deep verifier **PASS**; không còn gate thu nhận IDRiD. Builder được bảo vệ để
không ghi đè registry có phiên bản bằng trạng thái pending cũ. Ch6 vẫn chờ Phase 31.

## Kiểm tra đã chạy

- Data tests sau nhập IDRiD: **97 PASS, không skip**; coverage bốn module dữ liệu/import
  khoảng **96%** (acquisition 94%, source inspection 99%, provenance 99%, IDRiD verifier 95%).
  Evidence: `artifacts/manifests/phase23/idrid-data-tests.xml`, `idrid_data_coverage.json`.
- Contract/API/environment/scratch compatibility: **121 PASS**, bốn cảnh báo sklearn V2
  đã biết, không sửa checkpoint cũ. Evidence: `idrid-regression-tests.xml` cùng thư mục.
- Tổng cộng **218 test đạt**. Lint/format 9 file Python cập nhật IDRiD đạt; các guard thêm bằng TDD:
  source tự động phải ready, khóa không ghi đè, cap CSV ngoài ZIP và giữ LF cho YAML/JSONL
  để không hỏng hash sau Windows checkout. Không đổi đặc tả đã khóa hoặc raw Ch5.
- `--all --offline`: **11/11 reused**, không tải lại file đúng hash.
- Deep verifier **PASS**: **11.357 raw file, 688.438.598 byte**, **9 archive inventories,
  27.581 thành viên** đọc/hash trực tiếp; raw đều ignored. Không tạo bản giải nén trùng.
- Khóa hiện hành **62 file provenance**:
  `artifacts/manifests/phase23/updates/idrid_20261017_8a9f4752b35d/dataset_lock.json`.
  Khóa gốc `artifacts/manifests/phase23/dataset_lock.json` giữ SHA-256
  `afc01c76d35ac4c2b34134632a33fd367e1d8dea931bdf650d4471b435adc4c1`;
  **58 metadata** cũ được lưu/kiểm trong `snapshots/pre_idrid_v1/`.
  Chỉ đổi registry entry/manifest/card IDRiD và thêm evidence thuộc IDRiD; 17 entry khác giữ nguyên.
  31 file đặc tả Phase 22, `uv.lock`, V2 và 10 prediction TEST Ch5 không đổi;
  `run_count=1`. 7 config/23 metric Ch5 cũng khớp baseline qua Phase22 verifier.
- Scan pattern secret giới hạn trong mã/test Python Phase23 không thấy pattern private key/token
  phổ biến; không tuyên bố đây là audit toàn repository/history.
- Nguồn/giấy phép/phiên bản: `experiments/configs/v3/acquisition_sources.json`,
  `artifacts/manifests/phase23/source_discovery.json` và từng source card.
  `approved` là phạm vi dùng nghiên cứu local đã ghi trong note, không phải giấy phép
  phân phối lại toàn bộ raw; không tự gán SPDX cho Ames/CIFAR/BIS nếu nguồn không ghi.

## Bàn giao

Gõ **“làm phase 24”** để thực hiện EDA, mẫu input/output, phân bố, split và leakage audit
trên các nguồn đã ready. Không tự khởi động Phase 24 trong lần nghiệm thu này.
IDRiD đã được kiểm file/điều khoản và cập nhật provenance có phiên bản,
**giữ nguyên khóa Phase23 gốc**. Chạy lại import/builder đã kiểm tra PASS, không tạo lại khóa.

Hướng dẫn archive/alias, trạng thái và lệnh vận hành: [docs/datasets/README.md](datasets/README.md).
Trước xử lý thêm dữ liệu, vẫn kiểm dung lượng host, không hạ reserve 5 GiB hay tự dọn ổ.
`Get-PSDrive` từng trả Free=null; dùng `.NET DriveInfo` và `/mnt/c`, không dùng free ảo WSL root.

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.acquire_datasets --all --offline
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase22
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase23 --deep
```

Lần thu nhận tự động đầu có 77 data + 121 regression test, khóa 58 file; bằng chứng cũ được giữ.
Lần bổ sung IDRiD có 97 data + 121 regression test, khóa mới 62 file nối với snapshot metadata cũ.
Các lệnh trên dùng kiểm tra lại, không ghi đè khóa. Evidence hiện hành:
`artifacts/manifests/phase23/verification.json`, `offline_reuse.json`, `registry_build.json`,
`updates/idrid_20261017_8a9f4752b35d/`, `idrid-data-tests.xml`, `idrid-regression-tests.xml`,
`idrid_data_coverage.json`, `idrid_manual.json`, `checkpoint.json`.
