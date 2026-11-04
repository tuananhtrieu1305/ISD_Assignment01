# ch4_gold_pink_sheet — thẻ nguồn Phase 23

- Chương: 4; loại: `timeseries`; trạng thái: `ready`.
- Nguồn: https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx
- Phiên bản: Pink Sheet October 2026 historical monthly workbook; latest revised vintage; sha256:ea1c350827878ea3bbe30e3cda16a13fd3bd5b409b8458940dc94a36b5a33154
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:19:43.210164+00:00
- Trích dẫn: World Bank (2026). Commodity Price Data (The Pink Sheet), historical monthly data, October 2026 snapshot.
- Giấy phép/quyền truy cập: `approved` — World Bank Commodity Prices - History and Projections catalog: CC BY 4.0. https://datacatalog.worldbank.org/search/dataset/0038238/commodity-prices-history-and-projections . Attribute World Bank and preserve unit/source notes. Not a real-time vintage.
- Dung lượng vật lý: 586,099 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 801 monthly observations, latest revised vintage; số đặc trưng nguồn: 4.
- Target theo protocol: `gold_usd_per_troy_ounce`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch4_gold_pink_sheet.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 31 thành viên, 3,550,099 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch4_gold_pink_sheet/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 801,
  "features": 4,
  "unit": "monthly observations, latest revised vintage",
  "columns": [
    {
      "name": "month",
      "dtype": "datetime",
      "role": "time"
    },
    {
      "name": "gold_usd_per_troy_ounce",
      "dtype": "number",
      "role": "target"
    },
    {
      "name": "silver",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "platinum",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "crude_oil",
      "dtype": "number",
      "role": "feature"
    }
  ],
  "observed_columns": [
    "None",
    "Crude oil, average",
    "Crude oil, Brent",
    "Crude oil, Dubai",
    "Crude oil, WTI",
    "Coal, Australian",
    "Coal, South African **",
    "Natural gas, US",
    "Natural gas, Europe",
    "Liquefied natural gas, Japan",
    "Natural gas index",
    "Cocoa",
    "Coffee, Arabica",
    "Coffee, Robusta",
    "Tea, avg 3 auctions",
    "Tea, Colombo",
    "Tea, Kolkata",
    "Tea, Mombasa",
    "Coconut oil",
    "Groundnuts",
    "Fish meal",
    "Groundnut oil **",
    "Palm oil",
    "Palm kernel oil",
    "Soybeans",
    "Soybean oil",
    "Soybean meal",
    "Rapeseed oil",
    "Sunflower oil",
    "Barley",
    "Maize",
    "Sorghum",
    "Rice, Thai 5% ",
    "Rice, Thai 25% ",
    "Rice, Thai A.1",
    "Rice, Viet Namese 5%",
    "Wheat, US SRW",
    "Wheat, US HRW",
    "Banana, Europe",
    "Banana, US",
    "Orange",
    "Beef **",
    "Chicken **",
    "Lamb **",
    "Shrimps, Mexican",
    "Sugar, EU",
    "Sugar, US",
    "Sugar, world",
    "Tobacco, US import u.v.",
    "Logs, Cameroon",
    "Logs, Malaysian",
    "Sawnwood, Cameroon",
    "Sawnwood, Malaysian",
    "Plywood",
    "Cotton, A Index",
    "Rubber, TSR20 **",
    "Rubber, RSS3",
    "Phosphate rock",
    "DAP",
    "TSP",
    "Urea ",
    "Potassium chloride **",
    "Aluminum",
    "Iron ore, cfr spot",
    "Copper",
    "Lead",
    "Tin",
    "Nickel",
    "Zinc",
    "Gold",
    "Platinum",
    "Silver",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None",
    "None"
  ],
  "raw_to_contract_aliases": {
    "Gold": "gold_usd_per_troy_ounce",
    "Crude oil, average": "crude_oil"
  },
  "time_range": [
    "1960M01",
    "2026M09"
  ],
  "selected_column_indices": {
    "Gold": 69,
    "Silver": 71,
    "Platinum": 70,
    "Crude oil, average": 1
  },
  "checks": [
    "sheet_schema",
    "required_commodity_columns",
    "numeric_gold",
    "history_length"
  ],
  "deferred": "Phase24 uses gold plus explanatory commodities with one-period lag; no windows fitted here."
}
```
