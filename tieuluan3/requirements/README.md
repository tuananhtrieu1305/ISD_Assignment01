# Khóa môi trường Phase 21

`uv.lock` ở root là nguồn khóa chính. Các file `torch.lock`, `keras.lock` và
`keras-torch.lock` được export từ cùng lock, có version/hash đầy đủ, dùng cho kiểm tra và đối chiếu.

Hai profile GPU được cài vào venv riêng. `keras-torch` chỉ là fallback sau khi probe TensorFlow
thực tế thất bại trên GPU; phải ghi backend này trong manifest và báo cáo.
