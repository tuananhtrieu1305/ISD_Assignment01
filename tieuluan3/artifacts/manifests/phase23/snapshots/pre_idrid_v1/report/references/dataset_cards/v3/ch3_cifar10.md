# ch3_cifar10 — thẻ nguồn Phase 23

- Chương: 3; loại: `image`; trạng thái: `ready`.
- Nguồn: https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz
- Phiên bản: CIFAR-10 original binary release 2009; not Python pickle; sha256:c4a38c50a1bc5f3a1c5537f2155ab9d68f9f25eb1ed8d9ddda3db29a59bca1dd
- Thời điểm truy cập gốc (UTC): 2026-10-17T02:08:44.072442+00:00
- Trích dẫn: Krizhevsky, A. (2009). Learning Multiple Layers of Features from Tiny Images. University of Toronto technical report.
- Giấy phép/quyền truy cập: `approved` — Author-hosted public research benchmark; author requests citation. No explicit SPDX license asserted. Local academic analysis only; no raw redistribution. https://www.cs.toronto.edu/~kriz/cifar.html
- Dung lượng vật lý: 170,052,171 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 60000 images (50000 train + 10000 test); số đặc trưng nguồn: 3072.
- Target theo protocol: `object_class`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch3_cifar10.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 8 thành viên, 184,380,149 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch3_cifar10/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 60000,
  "features": 3072,
  "unit": "images (50000 train + 10000 test)",
  "columns": [],
  "native_shape": [
    32,
    32,
    3
  ],
  "batch_counts": {
    "cifar-10-batches-bin/data_batch_1.bin": 10000,
    "cifar-10-batches-bin/data_batch_3.bin": 10000,
    "cifar-10-batches-bin/data_batch_4.bin": 10000,
    "cifar-10-batches-bin/test_batch.bin": 10000,
    "cifar-10-batches-bin/data_batch_5.bin": 10000,
    "cifar-10-batches-bin/data_batch_2.bin": 10000
  },
  "checks": [
    "binary_not_pickle",
    "record_length",
    "batch_count",
    "label_range"
  ]
}
```
