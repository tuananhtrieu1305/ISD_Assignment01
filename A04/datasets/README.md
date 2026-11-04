# Dataset của A04

Danh sách, kích cỡ, schema/hash và đường dẫn vật lý: `catalog.json`.

Từ repository root, chạy `scripts/run_assignment.ps1 -Project A04 -ListDatasets` hoặc dùng `scripts/datasets.py`. Dữ liệu dùng chung trỏ đến file thật trong workspace; không yêu cầu symlink/junction. Giữ split/scaler riêng từng bài. Không gọi model trên TEST để kiểm migration.
