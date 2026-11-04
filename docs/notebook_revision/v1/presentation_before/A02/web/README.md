# A02 / Web

HTML/CSS/JS; dữ liệu kết quả/trace/figure thật đã lưu. A01–A03 có thêm inference CPU qua backend gốc khi dùng runner.

Từ repository root trong PowerShell:

```powershell
./scripts/run_web.ps1 -Project A02
```

Mở **http://127.0.0.1:8012**. Thêm `-Port 9000` nếu cần port khác. Đóng terminal hoặc Ctrl+C để dừng process của runner. Dùng WSL Ubuntu/user tuananh và Python3.11.17 hiện có. Không bootstrap/doctor hoặc tạo venv GPU mới.

Không cần npm build. Có thể mở static server chỉ trỏ vào `web/` để xem replay. Để dùng inference A01–A03, dùng web runner bên dưới. Notebook download cần mở trong repository với kernel và dữ liệu theo README bài.

Mỗi bài có API/port riêng. Không để trang của bài này trỏ backend bài khác. Dữ liệu biểu đồ giữ metric/split/đơn vị từ nguồn; xem caption và bảng. Không diễn giải replay là inference live. Mẫu demo tiểu luận1 dùng TRAIN hoặc fixture; không forward TEST để kiểm UI.

Render: root `render.yaml` mặc định phục vụ tiểu luận3. Template riêng của bài chỉ là cấu hình tham khảo; không tự sửa Dashboard, tạo service hoặc deploy. Xem `docs/reorganization/render_handoff.md` ở repository root. Dependency/data/model lớn local không tự có trong clean checkout; serving bundle có release/hash riêng.
