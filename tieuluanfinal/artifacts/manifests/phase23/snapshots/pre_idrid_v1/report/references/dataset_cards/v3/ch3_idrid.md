# ch3_idrid — thẻ nguồn Phase 23

- Chương: 3; loại: `image`; trạng thái: `pending_user_download`.
- Nguồn: https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid
- Phiên bản: IDRiD B. Disease Grading (awaiting user-supplied original release)
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:11:19.634796+00:00
- Trích dẫn: Porwal, P. et al. (2018). Indian Diabetic Retinopathy Image Dataset (IDRiD). IEEE DataPort. DOI:10.21227/H25W98.
- Giấy phép/quyền truy cập: `pending` — Manual access/terms confirmation required; user chose to download later. Do not assert a license or invent a local 516-image snapshot.
- Dung lượng vật lý: 0 byte / 0 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: chưa có grading images; published 516 NOT measured until imported; số đặc trưng nguồn: None.
- Target theo protocol: `dr_grade`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch3_idrid.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

## Kiểm tra và giới hạn

```json
{
  "status": "pending_user_download",
  "files": [],
  "records": null,
  "reason": "User chose to download IDRiD later; no replacement dataset or fabricated counts.",
  "features": null,
  "unit": "grading images; published 516 NOT measured until imported",
  "columns": []
}
```
