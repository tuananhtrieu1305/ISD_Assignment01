# ch1_mnist_history — thẻ nguồn Phase 23

- Chương: 1; loại: `image`; trạng thái: `ready`.
- Nguồn: https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz
- Phiên bản: Keras sanctioned MNIST NPZ; original 60000/10000 split; sha256:731c5ac602752760c8e48fbffcf8c3b850d9dc2a2aedcf2cc48468fc17b673d1
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:15:26.213819+00:00
- Trích dẫn: LeCun, Y., Cortes, C., and Burges, C. MNIST handwritten digit database; NPZ distributed by Keras.
- Giấy phép/quyền truy cập: `approved` — CC BY-SA 3.0 as explicitly documented at https://keras.io/api/datasets/mnist/; retain attribution/share-alike for adaptations.
- Dung lượng vật lý: 11,490,434 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 70000 images (official 60000 train + 10000 test); số đặc trưng nguồn: 784.
- Target theo protocol: `none`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch1_mnist_history.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 4 thành viên, 54,950,320 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch1_mnist_history/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 70000,
  "features": 784,
  "unit": "images (official 60000 train + 10000 test)",
  "columns": [],
  "checks": [
    "npz_no_pickle",
    "shape",
    "dtype",
    "label_range"
  ],
  "native_shape": [
    28,
    28,
    1
  ]
}
```
