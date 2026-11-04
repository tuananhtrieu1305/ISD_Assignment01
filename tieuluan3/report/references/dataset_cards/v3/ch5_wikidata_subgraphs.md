# ch5_wikidata_subgraphs — thẻ nguồn Phase 23

- Chương: 5; loại: `kg`; trạng thái: `ready`.
- Nguồn: https://www.wikidata.org/wiki/Wikidata:Data_access
- Phiên bản: Phase11 exact Wikidata revision IDs
- Thời điểm truy cập gốc (UTC): 2026-10-12T09:55:27+00:00
- Trích dẫn: Wikidata contributors. EntityData snapshots, exact revision IDs in Phase11 snapshot manifest.
- Giấy phép/quyền truy cập: `approved` — CC0 1.0; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution.
- Dung lượng vật lý: 3,528,666 byte / 21 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 10 narrow entity snapshots, not a QA benchmark; số đặc trưng nguồn: None.
- Target theo protocol: `claims`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch5_wikidata_subgraphs.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

## Kiểm tra và giới hạn

```json
{
  "records": 10,
  "features": null,
  "unit": "narrow entity snapshots, not a QA benchmark",
  "columns": [],
  "claims": 2056,
  "checks": [
    "revision_snapshot_hashes",
    "all_raw_files_match_phase20_baseline"
  ],
  "deferred": "Structural/provenance audit only; not an invented third QA TEST dataset."
}
```
