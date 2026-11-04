# Mở 11 bài sau REORG

Mỗi bài có `datasets/`, `notebooks/`, `web/`. Dữ liệu lớn dùng chung theo SHA khi thực sự cùng snapshot; split/scaler riêng từng bài được giữ nguyên. `datasets/catalog.json` ghi nơi lưu thật. Tiểu luận2 là bản dẫn xuất Ch1–5, không gán báo cáo sáu chương cho bản này.

## Chạy web local

Từ PowerShell ở root:

```powershell
./scripts/run_web.ps1 -Project A01
./scripts/run_web.ps1 -Project tieuluan3
```

Chỉ chạy lệnh cho bài bạn muốn; một terminal tương ứng một web. Ctrl+C để dừng. Có thể thêm `-Port 9000`. Runner dùng WSL Ubuntu/user tuananh và Python3.11.17 đã có, bind localhost. Nó không tạo môi trường GPU hoặc train model.

| Bài | URL mặc định | Chế độ |
|---|---|---|
| A01 | http://127.0.0.1:8011 | Hai dataset, xem metric + so sánh ML CPU |
| A02 | http://127.0.0.1:8012 | Ba dataset, xem metric + so sánh ML CPU |
| A03 | http://127.0.0.1:8013 | Ba pipeline, kết quả gốc + inference CPU |
| A04 | http://127.0.0.1:8014 | Năm bài toán, replay comparison đã lưu |
| A05 | http://127.0.0.1:8015 | Ba dataset, bốn kiến trúc Keras/dataset, replay |
| A06 | http://127.0.0.1:8016 | Hai dataset, RNN và baseline/dự đoán đã lưu |
| tieuluan1 | http://127.0.0.1:8017 | React/Python bản bốn chương, bốn model demo |
| tieuluan2 | http://127.0.0.1:8018 | React/Python Ch1–5, RNN–LSTM/KG–RAG |
| tieuluan3 | http://127.0.0.1:8019 | React/Python đủ sáu chương |
| agent01 | http://127.0.0.1:8020 | Q-learning maze, greedy/BFS replay, manual play |
| agent02 | http://127.0.0.1:8021 | Hai shop, ba regime, 20 hình và ví dụ tính Q |

Ba frontend tiểu luận đã có build local, nhưng dist là generated/ignored. Sau clean checkout hoặc sau sửa frontend, build lại:

```powershell
./scripts/build_web.ps1 -Project tieuluan3
```

Nếu chưa có dependency Node, thêm `-Install` để cài đúng package-lock của giao diện. Dùng Node22.23.4; script tận dụng bản local đang có. Việc này chỉ tác động node_modules của frontend, không sửa hai venv GPU. Tiểu luận1 giữ lock/router của phiên bản cũ, không nâng theo V3.

A04–A06 và hai agent có thể dùng static server chỉ trỏ vào `web/`, không cần Python model backend. A01–A03 static-only vẫn xem metric/notebook, muốn inference dùng runner. Không public repository root bằng http.server vì chứa dữ liệu/checkpoint/provenance.

## Notebook và dữ liệu

Lệnh notebook vẫn dùng `scripts/run_assignment.ps1`; xem README từng bài. Torch/NumPy và Keras/TensorFlow dùng hai kernel WSL riêng. Không dùng Python Windows/Anaconda cho notebook, không cài gộp hai framework. Notebook tải từ web cần mở trong repository cùng dữ liệu/kernel, không phải bundle độc lập.

Runtime views đã có ở `provenance/runtime/assign/`; sau khi đổi máy, dùng **`scripts/materialize_assignment.py --project A01`** bằng Python WSL hiện có, thêm `--copy-only` nếu cần. Đây là materializer hiện hành: recipe Phase2 cộng source-location overlay Phase3. `materialize_project.py` là helper Phase2 lịch sử, không dùng riêng sau cleanup các folder web/reference. Bốn service module tiểu luận1 hiện ở `tieuluan1/src/term_paper/deployment/app/`.

Muốn materialize phải cung cấp đủ source/data/checkpoint đúng hash; Git không tự mang raw/model bị ignore. Serving Render dùng archive đã khai báo nên không cần raw/training cache. Không gọi controller hoặc TEST gate lịch sử để kiểm đường dẫn. Các thí nghiệm gốc/seal/metric/report giữ nguyên byte; mọi thay đổi thuật toán về sau cần revision mới.

Các warning sklearn của tiểu luận1 được giữ nguyên; không re-fit artifact cũ. Lượt kiểm clean-checkout đã dùng thư mục tạm trên filesystem Linux WSL để tránh overhead NTFS, cùng interpreter và archive đã khóa.
