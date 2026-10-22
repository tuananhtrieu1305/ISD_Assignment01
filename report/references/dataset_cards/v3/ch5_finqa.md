# ch5_finqa — thẻ nguồn Phase 23

- Chương: 5; loại: `qa`; trạng thái: `ready`.
- Nguồn: https://github.com/czyssrs/FinQA
- Phiên bản: 0f16e2867befa6840783e58be38c9efb9229d742
- Thời điểm truy cập gốc (UTC): 2026-10-12T09:55:27+00:00
- Trích dẫn: Chen, Z. et al. (2021). FinQA: A Dataset of Numerical Reasoning over Financial Data. EMNLP. https://aclanthology.org/2021.emnlp-main.300/
- Giấy phép/quyền truy cập: `approved` — MIT; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution.
- Dung lượng vật lý: 122,256,362 byte / 46 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 9200 raw QA records including private_test; số đặc trưng nguồn: None.
- Target theo protocol: `gold_evidence_program`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch5_finqa.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

## Kiểm tra và giới hạn

```json
{
  "records": 9200,
  "features": null,
  "unit": "raw QA records including private_test",
  "columns": [],
  "official_split_counts": {
    "dev": 883,
    "private_test": 919,
    "test": 1147,
    "train": 6251
  },
  "deferred": "No evaluation; private/public label policies remain the locked Ch5 protocol.",
  "checks": [
    "all_raw_files_match_phase20_baseline"
  ]
}
```
