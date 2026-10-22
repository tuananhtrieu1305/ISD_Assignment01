# ch4_household_power — thẻ nguồn Phase 23

- Chương: 4; loại: `timeseries`; trạng thái: `ready`.
- Nguồn: https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip
- Phiên bản: UCI 235 original minute-resolution household power release; sha256:9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:20:34.606379+00:00
- Trích dẫn: Hebrail, G. and Berard, A. (2006). Individual Household Electric Power Consumption. UCI. DOI:10.24432/C58K54.
- Giấy phép/quyền truy cập: `approved` — CC BY 4.0. https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption . Single household, not population-independent evidence.
- Dung lượng vật lý: 20,640,916 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 2075259 raw minute rows, NOT hourly training windows; số đặc trưng nguồn: 7.
- Target theo protocol: `global_active_power_kw_hourly`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch4_household_power.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 1 thành viên, 132,960,755 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch4_household_power/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 2075259,
  "features": 7,
  "unit": "raw minute rows, NOT hourly training windows",
  "columns": [
    {
      "name": "date",
      "dtype": "string",
      "role": "time"
    },
    {
      "name": "time",
      "dtype": "string",
      "role": "time"
    },
    {
      "name": "global_active_power",
      "dtype": "number",
      "role": "target"
    },
    {
      "name": "global_reactive_power",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "voltage",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "global_intensity",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "sub_metering_1",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "sub_metering_2",
      "dtype": "number",
      "role": "feature"
    },
    {
      "name": "sub_metering_3",
      "dtype": "number",
      "role": "feature"
    }
  ],
  "observed_columns": [
    "Date",
    "Time",
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3"
  ],
  "checks": [
    "raw_line_count",
    "row_width",
    "column_schema"
  ],
  "deferred": "Phase24 causal hourly aggregation and missingness handling; raw '?' retained."
}
```
