# ch6_gold_tasks — dữ liệu và kiểm tra Phase 24

Phạm vi: **declared_parent_view_NOT_AGENT_BENCHMARK**. Không huấn luyện hay đánh giá TEST trong Phase 24.

## Nguồn, kích cỡ và cấu trúc

Nguồn: [World Bank (2026). Commodity Price Data (The Pink Sheet), historical monthly data, October 2026 snapshot.](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx)
Phiên bản: Declared task view over pinned parent sources; tasks generated Phase31

Giấy phép/phạm vi: Inherits ALL parent source terms; no duplicate raw files and no generated benchmark yet.

Raw: 0 byte; None agent task view, not generated yet.

Số đo và schema phần dùng trong V3:

```json
{
  "agent_tasks": null,
  "parent_dataset_ids": [
    "ch4_gold_pink_sheet"
  ],
  "additional_raw_bytes": 0
}
```

## Mẫu input/output

Chỉ dẫn lại mẫu thật từ parent, KHÔNG phải task/gold answer của hệ agent. Task input/output schema và benchmark sẽ khóa Phase31.

```json
[
  {
    "from_parent": "ch4_gold_pink_sheet",
    "parent_sample": [
      {
        "id": "GOLD/1961-12-01T00:00:00",
        "input": {
          "context_end": "1961-12-01T00:00:00",
          "context_start": "1960-01-01T00:00:00",
          "last_values": {
            "crude_oil_lag1": 1.6,
            "gold": 35.0,
            "platinum_lag1": 84.0,
            "silver_lag1": 0.9
          }
        },
        "known_output": {
          "horizons": [
            1,
            3,
            6
          ],
          "target_times": [
            "1962-01-01T00:00:00",
            "1962-03-01T00:00:00",
            "1962-06-01T00:00:00"
          ],
          "values": [
            35,
            35,
            35
          ]
        }
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
    "ch4_gold_pink_sheet/eda.json"
  ]
}
```

## Cách chia tập và tiền xử lý

Chưa tạo task/split Ch6. Phase31 gom paraphrase/template/source ID và kế thừa TEST seal; không copy raw hay mở TEST parent để tuning.

## Nhận xét và giới hạn

- Không coi declared là dataset đã train/đánh giá.
- Ba miền ưu tiên giữ diabetes, house, gold; không bịa số task hoặc metric.

Nguồn và điều khoản của từng parent:

- [ch4_gold_pink_sheet](ch4_gold_pink_sheet.md): [World Bank (2026). Commodity Price Data (The Pink Sheet), historical monthly data, October 2026 snapshot.](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx).

## Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch6_gold_tasks/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.
