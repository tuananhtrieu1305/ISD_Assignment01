# ch6_house_tasks — dữ liệu và kiểm tra Phase 24

Phạm vi: **declared_parent_view_NOT_AGENT_BENCHMARK**. Không huấn luyện hay đánh giá TEST trong Phase 24.

## Nguồn, kích cỡ và cấu trúc

Nguồn: [De Cock, D. (2011). Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project. Journal of Statistics Education 19(3). DOI:10.1080/10691898.2011.11889627.](https://jse.amstat.org/v19n3/decock/AmesHousing.txt)
Phiên bản: Declared task view over pinned parent sources; tasks generated Phase31

Giấy phép/phạm vi: Inherits ALL parent source terms; no duplicate raw files and no generated benchmark yet.

Raw: 0 byte; None agent task view, not generated yet.

Số đo và schema phần dùng trong V3:

```json
{
  "agent_tasks": null,
  "parent_dataset_ids": [
    "ch2_ames_housing",
    "ch4_bis_house_prices"
  ],
  "additional_raw_bytes": 0
}
```

## Mẫu input/output

Chỉ dẫn lại mẫu thật từ parent, KHÔNG phải task/gold answer của hệ agent. Task input/output schema và benchmark sẽ khóa Phase31.

```json
[
  {
    "from_parent": "ch2_ames_housing",
    "parent_sample": [
      {
        "id": "row_0001475",
        "input": {
          "alley": null,
          "land_contour": "Lvl",
          "lot_area": 8450,
          "lot_frontage": 65.0,
          "lot_shape": "Reg",
          "ms_sub_class": 20,
          "ms_zoning": "RL",
          "street": "Pave"
        },
        "known_output": 210000
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
    "ch2_ames_housing/eda.json",
    "ch4_bis_house_prices/eda.json"
  ]
}
```

## Cách chia tập và tiền xử lý

Chưa tạo task/split Ch6. Phase31 gom paraphrase/template/source ID và kế thừa TEST seal; không copy raw hay mở TEST parent để tuning.

## Nhận xét và giới hạn

- Không coi declared là dataset đã train/đánh giá.
- Ba miền ưu tiên giữ diabetes, house, gold; không bịa số task hoặc metric.

Nguồn và điều khoản của từng parent:

- [ch2_ames_housing](ch2_ames_housing.md): [De Cock, D. (2011). Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project. Journal of Statistics Education 19(3). DOI:10.1080/10691898.2011.11889627.](https://jse.amstat.org/v19n3/decock/AmesHousing.txt).
- [ch4_bis_house_prices](ch4_bis_house_prices.md): [Bank for International Settlements (2026). Selected residential property prices (WS_SPP), BIS Data Portal; underlying national sources.](https://data.bis.org/static/bulk/WS_SPP_csv_col.zip).

## Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch6_house_tasks/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.
