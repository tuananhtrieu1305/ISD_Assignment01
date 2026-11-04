# ch3_idrid — thẻ nguồn Phase 23

- Chương: 3; loại: `image`; trạng thái: `ready`.
- Nguồn: https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid
- Phiên bản: IDRiD original B. Disease Grading ZIP; sha256:8a9f4752b35d74cc35ff48b21ad44f295a6f800110ec218fc2d1c264803e4d8c
- Thời điểm truy cập gốc (UTC): 2026-10-17T02:39:14.920283+00:00
- Trích dẫn: Porwal, P., Pachade, S., and Kokare, M. (2018). Indian Diabetic Retinopathy Image Dataset (IDRiD). IEEE DataPort. DOI:10.21227/H25W98.
- Giấy phép/quyền truy cập: `approved` — CC BY 4.0, established from bundled IDRiD LICENSE.txt and CC-BY-4.0.txt; exact member hashes in import receipt. Retain authors/citation/license, identify adaptations; no clinical-use claims.
- Dung lượng vật lý: 212,405,123 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 516 fundus RGB images; official 413 train + 103 test; số đặc trưng nguồn: None.
- Target theo protocol: `dr_grade`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch3_idrid.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 520 thành viên, 212,276,527 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch3_idrid/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 516,
  "official_split_counts": {
    "train": 413,
    "test": 103
  },
  "identity_policy": "official_split/image_stem",
  "native_image_shapes": [
    [
      4288,
      2848,
      "RGB"
    ]
  ],
  "license_status": "approved",
  "license_identifier": "CC-BY-4.0",
  "license_evidence": [
    {
      "archive": "data/raw/ch3/idrid/manual/B_Disease_Grading.zip",
      "member": "B. Disease Grading/LICENSE.txt",
      "sha256": "ebc63a59874a44419ac860fa5cceb5c6428b74e09b5712620f08d68f0f335a88",
      "size_bytes": 306,
      "role": "dataset_declaration"
    },
    {
      "archive": "data/raw/ch3/idrid/manual/B_Disease_Grading.zip",
      "member": "B. Disease Grading/CC-BY-4.0.txt",
      "sha256": "dce09367809a1ebae8d90ceb60fa6618360e13d2cd9d304dfb595719e2f02f58",
      "size_bytes": 17344,
      "role": "full_license_text"
    }
  ],
  "checks": [
    "all_member_hashes",
    "safe_archive_paths",
    "image_decode",
    "label_image_identity",
    "official_413_103_split",
    "grade_0_to_4"
  ],
  "features": null,
  "unit": "fundus RGB images; official 413 train + 103 test",
  "columns": [
    {
      "name": "image_id",
      "dtype": "string",
      "role": "id"
    },
    {
      "name": "official_split",
      "dtype": "category",
      "role": "group"
    },
    {
      "name": "dr_grade",
      "dtype": "integer",
      "role": "target"
    }
  ]
}
```
