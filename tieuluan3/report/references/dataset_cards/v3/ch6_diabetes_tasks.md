# ch6_diabetes_tasks — thẻ nguồn Phase 23

- Chương: 6; loại: `task_view`; trạng thái: `declared`.
- Nguồn: https://archive.ics.uci.edu/static/public/891/data.csv
- Phiên bản: Declared task view over pinned parent sources; tasks generated Phase31
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:15:52.984993+00:00
- Trích dẫn: Teboul, A. (2021). Diabetes Health Indicators Dataset, derived from CDC BRFSS 2015. UCI dataset 891. DOI:10.24432/C53919.
- Giấy phép/quyền truy cập: `approved` — Inherits ALL parent source terms; no duplicate raw files and no generated benchmark yet.
- Dung lượng vật lý: 0 byte / 0 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: chưa có agent task view, not generated yet; số đặc trưng nguồn: None.
- Target theo protocol: `verified_response`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch6_diabetes_tasks.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Nguồn cha (tham chiếu, không sao chép raw): ch2_cdc_diabetes, ch5_medquad_diabetes

## Kiểm tra và giới hạn

```json
{
  "records": null,
  "features": null,
  "unit": "agent task view, not generated yet",
  "columns": [],
  "checks": [
    "parent_ids_match_locked_protocol"
  ],
  "deferred": "Phase31 creates fixed task families and benchmark; parent TEST seals remain intact."
}
```
