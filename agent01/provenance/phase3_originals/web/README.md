# Web demo Discovering AI Agent

Mở `dist/index.html` bằng Chrome/Edge (nhấp đúp), không cần cài package hoặc chạy server.

- **Xem agent**: chạy, tạm dừng, đi từng bước, đổi tốc độ, làm lại.
- **Tự thử**: dùng phím mũi tên hoặc nút; va tường kết thúc lượt, giới hạn 400 bước.
- Tải notebook gốc từ liên kết trên trang.

Web phát lại đường greedy thực đã lưu ở `../evidence/results.json`; không chạy Python hoặc huấn luyện mới. `data.js` lấy mê cung trực tiếp từ notebook và sao chép kết quả thực. Bản notebook trong `dist/` là bản sao tải xuống, không sửa notebook gốc. BFS chỉ là đối chứng sau huấn luyện.

Toàn bộ demo nằm trong thư mục này, tách khỏi web và artifact V3.
