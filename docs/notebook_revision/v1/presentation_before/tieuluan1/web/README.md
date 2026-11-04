# tieuluan1 / Web

React/Python cùng style và chức năng phiên bản gốc; bốn chương của bản1.

Từ repository root trong PowerShell:

```powershell
./scripts/run_web.ps1 -Project tieuluan1
```

Mở **http://127.0.0.1:8017**. Thêm `-Port 9000` nếu cần port khác. Đóng terminal hoặc Ctrl+C để dừng process của runner. Dùng WSL Ubuntu/user tuananh và Python3.11.17 hiện có. Không bootstrap/doctor hoặc tạo venv GPU mới.

Build frontend trong folder frontend bằng `npm ci --no-fund --no-audit` rồi `npm run build`. Node22.23.4. Backend local dùng runtime Torch/NumPy WSL hiện có, không cài TensorFlow vào backend Render. Build local đã dùng đúng lock; bản1 có cache dependency riêng.

`.env.example` trong frontend minh họa API origin. Mặc định UI gọi cùng origin với web runner; nếu tách static/backend trên Render, đặt VITE_API_BASE_URL trước khi build. Không dùng chung API URL giữa ba bài.

Mỗi bài có API/port riêng. Không để trang của bài này trỏ backend bài khác. Dữ liệu biểu đồ giữ metric/split/đơn vị từ nguồn; xem caption và bảng. Không diễn giải replay là inference live. Mẫu demo tiểu luận1 dùng TRAIN hoặc fixture; không forward TEST để kiểm UI.

Render: root `render.yaml` mặc định phục vụ tiểu luận3. Template riêng của bài chỉ là cấu hình tham khảo; không tự sửa Dashboard, tạo service hoặc deploy. Xem `docs/reorganization/render_handoff.md` ở repository root. Dependency/data/model lớn local không tự có trong clean checkout; serving bundle có release/hash riêng.
