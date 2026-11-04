# Dataset V3 — thu nhận, kiểm chứng và bàn giao

Nguồn đặc tả là `experiments/configs/v3/protocol_v3.json` đã khóa Phase 22.
Các URL/gói tải thực tế nằm ở `experiments/configs/v3/acquisition_sources.json`.
Không sửa protocol để điền số đếm mới: số đo thuộc manifest/thẻ nguồn.

## Các lớp bằng chứng

1. **Receipt tải về** — `artifacts/manifests/phase23/receipts/<id>.json`:
   URL ban đầu/cuối, thời điểm UTC, SHA-256, byte size, ETag/Last-Modified nếu có.
   Nguồn có checksum chính thức (EuroSAT/CIFAR) phải khớp trước khi được nhận.
2. **Dataset manifest** — `artifacts/manifests/datasets/<id>.json`:
   trường `contract` theo JSON Schema V3; `inspection` là số đo/schema nguồn;
   `archive_inventory` tham chiếu danh sách hash thành viên, không phải bản giải nén.
3. **Registry** — `data/registry.yaml`: danh sách 18 ID, trạng thái, parent ID,
   đường dẫn và hash manifest. Không coi một ID `declared` là dataset đã có để train.
4. **Source card** — `report/references/dataset_cards/v3/<id>.md`:
   link, phiên bản, citation, license/access scope, kích cỡ và giới hạn nguồn.
   Đây chưa phải EDA/sample/distribution hoàn chỉnh của Phase 24.
5. **Khóa provenance** — khóa hiện hành lấy từ `provenance_lock` trong `data/registry.yaml`.
   Bản IDRiD là `artifacts/manifests/phase23/updates/idrid_20261017_8a9f4752b35d/dataset_lock.json`
   (62 file). Khóa gốc `artifacts/manifests/phase23/dataset_lock.json` và 58 metadata cũ trong
   `snapshots/pre_idrid_v1/` giữ nguyên. Chạy lại không được ghi đè khóa để hợp thức hóa byte đã đổi.

Các file JSON trong `docs/contracts/v3/examples/` là **synthetic schema examples**,
không được dùng thay các manifest đo thật ở trên. Các fixture test cũng không phải dataset.

## Chạy trong runtime đã khóa

Từ PowerShell ở `C:\DATA\assign`, sau khi kiểm ổ C còn đủ dung lượng:

```powershell
# Tải các nguồn tự động; file đã có receipt/hash hợp lệ sẽ không tải lại.
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.acquire_datasets --all

# Kiểm chứng tái sử dụng OFFLINE, không chấp nhận thiếu file/receipt hoặc sai hash.
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.acquire_datasets --all --offline

# Builder tạo registry ban đầu; sau cập nhật có phiên bản chỉ kiểm tra/giữ registry hiện hành.
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.build_phase23_registry

# Kiểm chứng sâu theo khóa hiện hành, không ghi đè khóa cũ.
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase23 --deep
```

Không dùng Python Windows hay tạo venv tạm. Runtime Phase 21 nằm ngoài source.
Downloader giữ dự phòng **5 GiB**, kiểm free ở phân vùng chứa `data/raw`, không dựa vào
dung lượng ảo WSL root. Không tự hạ reserve nếu thiếu chỗ; không xóa cache/raw Ch5 để lấy chỗ.
Không đặt credential trong URL hoặc log command line toàn hệ thống.

File raw đã có mà không có receipt tin cậy, hoặc hash sai, sẽ bị từ chối **không ghi đè**.
Đây là bảo vệ dữ liệu người dùng, không phải lỗi nên giải quyết bằng cách bỏ kiểm hash.
Sau một lượt bị ngắt, chỉ dọn đúng partial do lượt đó tạo sau khi xác minh path/hash và
không còn writer. Không dùng lệnh xóa đệ quy cả `data/raw`.

## Trạng thái có ý nghĩa gì?

- `ready`: nguồn đã được thu nhận/đo/hash và ghi phạm vi license/access. **Không có nghĩa**
  đã chia tập, chống leakage, fit preprocessing hoặc sẵn sàng tuyên bố chất lượng mô hình.
- `pending_user_download`: nguồn chưa được cung cấp/kiểm chứng; không bịa số mẫu local.
  IDRiD đã hết pending ngày 17/10/2026; xem [biên bản IDRiD](idrid_manual.md).
- `declared`: ba task view Ch6 có parent ID nhưng chưa tạo task benchmark ở Phase 31;
  không sao chép raw từ Ch2/4/5.

ImageNet Ch1 là **metadata-only**: một trang challenge, không phải ảnh ImageNet local.
Ch5 là **historical baseline** giữ nguyên hash/commit/revision và TEST seal.
Không dùng một lượt acquisition hay regression làm lý do mở lại TEST để tuning.

`license_status=approved` phải đọc cùng `license_note`: có nguồn dùng CC/MIT, có nguồn chỉ
ghi phạm vi nghiên cứu local và yêu cầu attribution. Không tự gán SPDX hoặc suy ra quyền
phân phối lại raw từ việc URL tải được. Raw được ignore và không đưa lên Render/Git.

## Archive và biến nguồn cần lưu ý

| Dataset | Vật mang giữ nguyên | Dùng đúng phần nguồn |
|---|---|---|
| CDC diabetes | CSV UCI | Diabetes_binary 0/1; bỏ ID khỏi feature |
| Ames | TXT gốc của De Cock | 2.930 dòng; SalePrice → sale_price; PID/Order là ID |
| Bank | ZIP UCI chứa ZIP con | bank.zip!bank-full.csv; y → subscription; bỏ duration cho dự đoán trước gọi |
| EuroSAT | EuroSAT_RGB.zip | RGB 64×64; không tải gói multispectral 2,1 GB |
| IDRiD | B_Disease_Grading.zip | ZIP B đã có cả ảnh/CSV/license; ID phải gồm train/test vì trùng basename |
| CIFAR-10 | cifar-10-binary.tar.gz | 5 train batch + test batch, binary records; không nạp pickle |
| Gold | XLSX Pink Sheet monthly | Sheet Monthly Prices; Gold, Silver, Platinum, Crude oil, average; giữ đơn vị/vintage |
| BIS | WS_SPP CSV trong ZIP | Bulk gồm nominal/real và index/YoY; không gộp đơn vị hoặc dùng toàn bulk như panel đã chọn |
| Power | TXT trong ZIP | Dòng gốc theo phút, dấu ? giữ nguyên; chưa phải cửa sổ forecast theo giờ |

Ch5 MedQuAD manifest đếm **toàn upstream corpus**, trong khi lát cắt diabetes đã khóa có
247 query lịch sử. FinQA có private_test trong snapshot; presence không đồng nghĩa được dùng
để tuning/đánh giá lại. Wikidata là supporting graph, không phải benchmark QA thứ ba được bịa thêm.

## Phạm vi tiếp theo

Phase24 đã tạo sample input/output, phân bố, missing/outlier/duplicate audit, split và preprocessing
train-only. Catalog `data/catalog_v3.json` liên kết thẻ `v3_eda/`, EDA, split và fitted state;
không ghi đè registry/thẻ nguồn Phase23. Xem [biên bản Phase24](../phase24_report.md).
Time series split theo thời gian và có ba rolling folds mỗi nguồn; official TEST giữ nguyên.
IDRiD có một ảnh train trùng TEST được quarantine; nhãn nguồn không bị tự sửa.
Chưa train/đánh giá mô hình. Không đổi dataset/resolution/subset/split để làm đẹp kết quả.
Tiếp theo là Phase25: adapter tensor có feature order rõ ràng/serialization roundtrip,
model contract và hợp hàm; GPU peak probe trước huấn luyện. CNN vẫn nghiệm thu ở Phase27,
không suy ra chất lượng mô hình từ thu nhận/EDA thành công.
