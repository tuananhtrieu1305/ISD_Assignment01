# ch1_iris_history — thẻ nguồn Phase 23

- Chương: 1; loại: `tabular`; trạng thái: `ready`.
- Nguồn: https://archive.ics.uci.edu/static/public/53/iris.zip
- Phiên bản: UCI 53 original Iris snapshot; sha256:d11fe30213d36434a0879aab7cb00ce3c812eb7ba2495874438abff7b7b762e9
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:15:24.140603+00:00
- Trích dẫn: Fisher, R. A. (1936). Iris. UCI Machine Learning Repository. DOI:10.24432/C56C76.
- Giấy phép/quyền truy cập: `approved` — CC BY 4.0; attribution required. https://archive.ics.uci.edu/dataset/53/iris
- Dung lượng vật lý: 3,738 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 150 raw rows; số đặc trưng nguồn: 4.
- Target theo protocol: `none`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch1_iris_history.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 4 thành viên, 12,205 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch1_iris_history/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 150,
  "features": 4,
  "unit": "raw rows",
  "columns": [
    {
      "name": "sepal_length",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "sepal_width",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "petal_length",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "petal_width",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "species",
      "dtype": "string",
      "role": "target"
    }
  ],
  "observed_columns": [
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
    "species"
  ],
  "raw_to_contract_aliases": {
    "sepal_length": "sepal_length",
    "sepal_width": "sepal_width",
    "petal_length": "petal_length",
    "petal_width": "petal_width",
    "species": "species"
  },
  "excluded_feature_columns": [],
  "checks": [
    "row_count",
    "column_schema"
  ]
}
```
