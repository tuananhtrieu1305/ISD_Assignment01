# Web demo AG02

Nhấp đúp `index.html` và mở bằng Chrome hoặc Edge. Không cần server, package hoặc Python.

- Phát lại / tạm dừng / đi từng bước / làm lại episode train đầu của baseline CONTROLLED IID seed11 (20 bước đã lưu).
- Chọn IID/Persistent/Gold để xem final mean±sample std, n=5; rule n=5 scenario panel.
- Xem 20 hình và caption gốc của notebook.
- Thử phép tính Q câu3, gồm terminal không bootstrap.

Dữ liệu là bản sao chỉ đọc từ trace_sample.json, policy_summary.csv, figure_catalog.json và PNG gốc. Không huấn luyện, chạy policy, mở final claim hoặc sửa artifact nguồn. Phần cập nhật Q là ví dụ số học giả định, không cập nhật model.

Notebook tải xuống là bản sao nguyên byte. Notebook AG02 vốn cần input trong source bundle khi Run All; bản sao tải riêng không phải bundle tự chứa.

`source_manifest.json` ghi SHA256 các input đã sao chép. Demo chỉ chạy local, không deploy.
