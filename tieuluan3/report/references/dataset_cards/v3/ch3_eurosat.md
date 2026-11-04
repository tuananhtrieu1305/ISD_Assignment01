# ch3_eurosat — thẻ nguồn Phase 23

- Chương: 3; loại: `image`; trạng thái: `ready`.
- Nguồn: https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1
- Phiên bản: Zenodo 7711810 v2; RGB only; sha256:b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:19:42.751580+00:00
- Trích dẫn: Helber, P., Bischke, B., Dengel, A., and Borth, D. (2019). EuroSAT: A Novel Dataset and Deep Learning Benchmark for Land Use and Land Cover Classification. IEEE JSTARS. DOI:10.1109/JSTARS.2019.2918242.
- Giấy phép/quyền truy cập: `approved` — MIT confirmed by Zenodo record metadata; also respect Copernicus Sentinel data terms as noted by authors. https://github.com/phelber/EuroSAT ; https://zenodo.org/records/7711810 . Multispectral 2.1 GB package deliberately not downloaded.
- Dung lượng vật lý: 94,658,721 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 27000 RGB image patches; số đặc trưng nguồn: 12288.
- Target theo protocol: `land_cover`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch3_eurosat.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

Kiểm tra archive: 27,000 thành viên, 91,844,360 byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `artifacts/manifests/datasets/ch3_eurosat/archive_members.jsonl`.

## Kiểm tra và giới hạn

```json
{
  "records": 27000,
  "features": 12288,
  "unit": "RGB image patches",
  "columns": [],
  "native_shape": [
    64,
    64,
    3
  ],
  "class_names": [
    "AnnualCrop",
    "Forest",
    "HerbaceousVegetation",
    "Highway",
    "Industrial",
    "Pasture",
    "PermanentCrop",
    "Residential",
    "River",
    "SeaLake"
  ],
  "checks": [
    "all_images_decode",
    "image_count",
    "class_count",
    "native_shape"
  ]
}
```
