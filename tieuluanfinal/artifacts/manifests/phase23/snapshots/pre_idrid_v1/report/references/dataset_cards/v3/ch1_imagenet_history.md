# ch1_imagenet_history — thẻ nguồn Phase 23

- Chương: 1; loại: `metadata`; trạng thái: `ready`.
- Nguồn: https://www.image-net.org/challenges/LSVRC/2012/index.php
- Phiên bản: ILSVRC 2012 official challenge metadata only; sha256:9d63dd697cceeeb640da708183bbbd6f4c35f98175d4cbec0439c3f3ea4373cc
- Thời điểm truy cập gốc (UTC): 2026-10-17T01:15:25.227649+00:00
- Trích dẫn: Russakovsky, O. et al. (2015). ImageNet Large Scale Visual Recognition Challenge. IJCV. DOI:10.1007/s11263-015-0816-y.
- Giấy phép/quyền truy cập: `approved` — Only a local provenance copy of the public challenge webpage, not an image dataset license. Cite/paraphrase metadata; no redistribution of page or ImageNet images. Full image access remains subject to ImageNet terms.
- Dung lượng vật lý: 18,582 byte / 1 file; không tính bản giải nén vì không tạo bản giải nén.
- Kích cỡ logic: 1 official metadata webpage, ZERO local images; số đặc trưng nguồn: None.
- Target theo protocol: `none`.
- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/ch1_imagenet_history.json`.

Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.

## Kiểm tra và giới hạn

```json
{
  "records": 1,
  "features": null,
  "unit": "official metadata webpage, ZERO local images",
  "columns": [],
  "checks": [
    "official_page_identity"
  ],
  "published_not_measured": {
    "categories": 1000,
    "training_images_approx": 1200000
  }
}
```
