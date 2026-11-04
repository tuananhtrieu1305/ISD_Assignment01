# ch5_medquad_diabetes — thẻ nguồn Phase 23

- Chương: 5; loại: `qa`; trạng thái: `ready`.
- Nguồn: https://github.com/abachaa/MedQuAD
- Phiên bản: 577bd37b96c02d1833b2c9eed2de9f96964e96cb
- Thời điểm truy cập gốc (UTC): 2026-10-12T09:55:27+00:00
- Trích dẫn: Abacha, A. and Demner-Fushman, D. (2019). A question-entailment approach to question answering. BMC Bioinformatics 20:511. MedQuAD.
- Giấy phép/quyền truy cập: `approved` — CC BY 4.0; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution. Some copyrighted upstream answers were removed by MedQuAD; empty answers must not be reconstructed from another source.
- Dung lượng vật lý: 37,183,352 byte / 11,278 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 47441 QA pairs in entire preserved upstream corpus, NOT diabetes-only split; số đặc trưng nguồn: None.
- Target theo protocol: `gold_evidence_answer`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch5_medquad_diabetes.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

## Kiểm tra và giới hạn

```json
{
  "records": 47441,
  "features": null,
  "unit": "QA pairs in entire preserved upstream corpus, NOT diabetes-only split",
  "columns": [],
  "nonempty_answers": 16407,
  "historical_diabetes_queries_phase12": 247,
  "deferred": "Phase30 reuses the locked diabetes filter/split; never reconstruct or tune TEST here.",
  "checks": [
    "all_raw_files_match_phase20_baseline"
  ]
}
```
