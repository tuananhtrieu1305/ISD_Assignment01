# ch6_diabetes_tasks — dữ liệu và kiểm tra Phase 24

Phạm vi: **declared_parent_view_NOT_AGENT_BENCHMARK**. Không huấn luyện hay đánh giá TEST trong Phase 24.

## Nguồn, kích cỡ và cấu trúc

Nguồn: [Teboul, A. (2021). Diabetes Health Indicators Dataset, derived from CDC BRFSS 2015. UCI dataset 891. DOI:10.24432/C53919.](https://archive.ics.uci.edu/static/public/891/data.csv)
Phiên bản: Declared task view over pinned parent sources; tasks generated Phase31

Giấy phép/phạm vi: Inherits ALL parent source terms; no duplicate raw files and no generated benchmark yet.

Raw: 0 byte; None agent task view, not generated yet.

Số đo và schema phần dùng trong V3:

```json
{
  "agent_tasks": null,
  "parent_dataset_ids": [
    "ch2_cdc_diabetes",
    "ch5_medquad_diabetes"
  ],
  "additional_raw_bytes": 0
}
```

## Mẫu input/output

Chỉ dẫn lại mẫu thật từ parent, KHÔNG phải task/gold answer của hệ agent. Task input/output schema và benchmark sẽ khóa Phase31.

```json
[
  {
    "from_parent": "ch2_cdc_diabetes",
    "parent_sample": [
      {
        "id": "row_0048946",
        "input": {
          "bmi": 24,
          "chol_check": 1,
          "heart_diseaseor_attack": 0,
          "high_bp": 1,
          "high_chol": 1,
          "phys_activity": 1,
          "smoker": 0,
          "stroke": 0
        },
        "known_output": 0
      }
    ]
  }
]
```

## Phân bố và chất lượng dữ liệu

```json
{
  "agent_distribution": null,
  "parent_distribution_references": [
    "ch2_cdc_diabetes/eda.json",
    "ch5_medquad_diabetes/eda.json"
  ]
}
```

## Cách chia tập và tiền xử lý

Chưa tạo task/split Ch6. Phase31 gom paraphrase/template/source ID và kế thừa TEST seal; không copy raw hay mở TEST parent để tuning.

## Nhận xét và giới hạn

- Không coi declared là dataset đã train/đánh giá.
- Ba miền ưu tiên giữ diabetes, house, gold; không bịa số task hoặc metric.

Nguồn và điều khoản của từng parent:

- [ch2_cdc_diabetes](ch2_cdc_diabetes.md): [Teboul, A. (2021). Diabetes Health Indicators Dataset, derived from CDC BRFSS 2015. UCI dataset 891. DOI:10.24432/C53919.](https://archive.ics.uci.edu/static/public/891/data.csv).
- [ch5_medquad_diabetes](ch5_medquad_diabetes.md): [Abacha, A. and Demner-Fushman, D. (2019). A question-entailment approach to question answering. BMC Bioinformatics 20:511. MedQuAD.](https://github.com/abachaa/MedQuAD).

## Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch6_diabetes_tasks/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.
