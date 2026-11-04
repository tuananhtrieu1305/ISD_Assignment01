# A03 / Web

HTML/CSS/JS; dữ liệu kết quả/trace/figure thật đã lưu. A01–A03 có thêm inference CPU qua backend gốc khi dùng runner.

Từ repository root trong Git Bash:

```bash
./scripts/run_web_gitbash.sh A03
```

Mở **http://127.0.0.1:8013**. Thêm `9000` ở cuối lệnh nếu cần cổng khác. Nhấn Ctrl+C để dừng runner. Backend dùng WSL Ubuntu/user tuananh và môi trường Python hiện có.

Không cần npm build. Dùng runner trên để phục vụ cả giao diện dùng chung và API. Mở riêng `index.html` hoặc chỉ phục vụ thư mục `web/` sẽ thiếu asset `/_demo-ui/`. Đổi cổng bằng `./scripts/run_web_gitbash.sh A03 9000`. Notebook tải về cần mở trong repository với kernel và dữ liệu theo README bài.

Giao diện hiện hành tập trung vào đầu vào và kết quả; không yêu cầu nhập JSON hoặc xem metadata huấn luyện. Nhập thông tin rồi bấm **Kiểm tra** để chạy Improved DNN của bài toán. Mỗi bài có API/port riêng.

Render: root `render.yaml` mặc định phục vụ tiểu luận3. Template riêng của bài chỉ là cấu hình tham khảo; không tự sửa Dashboard, tạo service hoặc deploy. Xem `docs/reorganization/render_handoff.md` ở repository root. Dependency/data/model lớn local không tự có trong clean checkout; serving bundle có release/hash riêng.

<!-- notebook-inline-v1 -->

Notebook đã gộp, đầy đủ source trong cell: [danh sách hiện hành](../README.md). Bản tải notebook trên web (nếu có) trùng SHA-256 với `../notebooks/`; mở trong repository để dùng dataset và kernel hiện có.
