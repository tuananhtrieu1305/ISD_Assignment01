# ch6_gold_tasks — thẻ nguồn Phase 23

- Chương: 6; loại: `task_view`; trạng thái: `declared`.
- Nguồn: https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx
- Phiên bản: Declared task view over pinned parent sources; tasks generated Phase31
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:19:43.210164+00:00
- Trích dẫn: World Bank (2026). Commodity Price Data (The Pink Sheet), historical monthly data, October 2026 snapshot.
- Giấy phép/quyền truy cập: `approved` — Inherits ALL parent source terms; no duplicate raw files and no generated benchmark yet.
- Dung lượng vật lý: 0 byte / 0 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: chưa có agent task view, not generated yet; số đặc trưng nguồn: None.
- Target theo protocol: `verified_response`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch6_gold_tasks.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Nguồn cha (tham chiếu, không sao chép raw): ch4_gold_pink_sheet

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
