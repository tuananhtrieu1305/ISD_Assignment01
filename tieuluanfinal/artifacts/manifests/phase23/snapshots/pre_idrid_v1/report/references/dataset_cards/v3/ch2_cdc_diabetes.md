# ch2_cdc_diabetes — thẻ nguồn Phase 23

- Chương: 2; loại: `tabular`; trạng thái: `ready`.
- Nguồn: https://archive.ics.uci.edu/static/public/891/data.csv
- Phiên bản: UCI 891 / CDC BRFSS 2015 binary diabetes; sha256:9f71fda9d4ae5f4878c99b9233b6a16accfa9a17c194116a6b78100540934964
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:15:52.984993+00:00
- Trích dẫn: Teboul, A. (2021). Diabetes Health Indicators Dataset, derived from CDC BRFSS 2015. UCI dataset 891. DOI:10.24432/C53919.
- Giấy phép/quyền truy cập: `approved` — UCI directs licensing to upstream Kaggle; public Kaggle API confirms CC0: Public Domain. https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset . Not assumed to inherit UCI's default CC BY license.
- Dung lượng vật lý: 13,494,568 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 253680 raw rows; số đặc trưng nguồn: 21.
- Target theo protocol: `diabetes_binary`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch2_cdc_diabetes.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

## Kiểm tra và giới hạn

```json
{
  "records": 253680,
  "features": 21,
  "unit": "raw rows",
  "columns": [
    {
      "name": "id",
      "dtype": "integer",
      "role": "id"
    },
    {
      "name": "diabetes_binary",
      "dtype": "integer",
      "role": "target"
    },
    {
      "name": "high_bp",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "high_chol",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "chol_check",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "bmi",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "smoker",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "stroke",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "heart_diseaseor_attack",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "phys_activity",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "fruits",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "veggies",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "hvy_alcohol_consump",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "any_healthcare",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "no_docbc_cost",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "gen_hlth",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "ment_hlth",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "phys_hlth",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "diff_walk",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "sex",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "age",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "education",
      "dtype": "integer",
      "role": "feature"
    },
    {
      "name": "income",
      "dtype": "integer",
      "role": "feature"
    }
  ],
  "observed_columns": [
    "ID",
    "Diabetes_binary",
    "HighBP",
    "HighChol",
    "CholCheck",
    "BMI",
    "Smoker",
    "Stroke",
    "HeartDiseaseorAttack",
    "PhysActivity",
    "Fruits",
    "Veggies",
    "HvyAlcoholConsump",
    "AnyHealthcare",
    "NoDocbcCost",
    "GenHlth",
    "MentHlth",
    "PhysHlth",
    "DiffWalk",
    "Sex",
    "Age",
    "Education",
    "Income"
  ],
  "raw_to_contract_aliases": {
    "ID": "id",
    "Diabetes_binary": "diabetes_binary",
    "HighBP": "high_bp",
    "HighChol": "high_chol",
    "CholCheck": "chol_check",
    "BMI": "bmi",
    "Smoker": "smoker",
    "Stroke": "stroke",
    "HeartDiseaseorAttack": "heart_diseaseor_attack",
    "PhysActivity": "phys_activity",
    "Fruits": "fruits",
    "Veggies": "veggies",
    "HvyAlcoholConsump": "hvy_alcohol_consump",
    "AnyHealthcare": "any_healthcare",
    "NoDocbcCost": "no_docbc_cost",
    "GenHlth": "gen_hlth",
    "MentHlth": "ment_hlth",
    "PhysHlth": "phys_hlth",
    "DiffWalk": "diff_walk",
    "Sex": "sex",
    "Age": "age",
    "Education": "education",
    "Income": "income"
  },
  "excluded_feature_columns": [
    "id"
  ],
  "checks": [
    "row_count",
    "column_schema"
  ]
}
```
