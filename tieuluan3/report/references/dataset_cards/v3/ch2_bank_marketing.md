# ch2_bank_marketing — thẻ nguồn Phase 23

- Chương: 2; loại: `tabular`; trạng thái: `ready`.
- Nguồn: https://archive.ics.uci.edu/static/public/222/bank+marketing.zip
- Phiên bản: UCI 222; bank.zip/bank-full.csv, original 45211-row variant; sha256:e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:15:33.045387+00:00
- Trích dẫn: Moro, S., Rita, P., and Cortez, P. (2014). Bank Marketing. UCI. DOI:10.24432/C5K306.
- Giấy phép/quyền truy cập: `approved` — CC BY 4.0. https://archive.ics.uci.edu/dataset/222/bank+marketing . Retain attribution; exclude duration before-call prediction.
- Dung lượng vật lý: 1,023,843 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 45211 raw rows; số đặc trưng nguồn: 15.
- Target theo protocol: `subscription`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch2_bank_marketing.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 12 thành viên, 12,533,959 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch2_bank_marketing/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 45211,
  "features": 15,
  "unit": "raw rows",
  "columns": [
    {
      "name": "age",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "job",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "marital",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "education",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "default",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "balance",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "housing",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "loan",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "contact",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "day",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "month",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "duration",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "campaign",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "pdays",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "previous",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "poutcome",
      "dtype": "string",
      "role": "feature"
    },
    {
      "name": "subscription",
      "dtype": "string",
      "role": "target"
    }
  ],
  "observed_columns": [
    "age",
    "job",
    "marital",
    "education",
    "default",
    "balance",
    "housing",
    "loan",
    "contact",
    "day",
    "month",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "poutcome",
    "y"
  ],
  "raw_to_contract_aliases": {
    "age": "age",
    "job": "job",
    "marital": "marital",
    "education": "education",
    "default": "default",
    "balance": "balance",
    "housing": "housing",
    "loan": "loan",
    "contact": "contact",
    "day": "day",
    "month": "month",
    "duration": "duration",
    "campaign": "campaign",
    "pdays": "pdays",
    "previous": "previous",
    "poutcome": "poutcome",
    "y": "subscription"
  },
  "excluded_feature_columns": [
    "duration"
  ],
  "checks": [
    "row_count",
    "column_schema"
  ],
  "selected_member": "bank.zip!bank-full.csv"
}
```
