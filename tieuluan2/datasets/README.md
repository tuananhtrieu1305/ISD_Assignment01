# Dataset của tieuluan2

Danh sách, kích cỡ, schema/hash và đường dẫn vật lý: `catalog.json`.

Từ repository root, chạy `scripts/run_assignment.ps1 -Project tieuluan2 -ListDatasets` hoặc dùng `scripts/datasets.py`. Dữ liệu dùng chung trỏ đến file thật trong workspace; không yêu cầu symlink/junction. Giữ split/scaler riêng từng bài. Không gọi model trên TEST để kiểm migration.
