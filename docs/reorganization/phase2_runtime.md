# Chạy code sau REORG Phase2

## Môi trường

Dùng WSL distro `Ubuntu`, user `tuananh`; Python3.11.17. Torch: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`; Keras: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`. Kernel Keras cần wheel-local CUDA library paths đã được cấu hình trong `scripts/run_assignment.sh`; ưu tiên runner. Không cài gộp Torch và TensorFlow, không bootstrap/doctor lịch sử ghi đè evidence cũ.

Mở project trong cửa sổ VS Code WSL. Chọn interpreter đúng framework trong README từng bài. Restart kernel trước khi đổi bài; helper chủ động chặn namespace còn từ bài khác. Tên hiển thị kernel trong notebook là gợi ý; runner dùng trực tiếp interpreter đã khóa, không dựa vào Python Windows.

## Lệnh

Từ PowerShell, dùng `scripts/run_assignment.ps1 -Project A01 -Inspect` hoặc `-ListDatasets`. Thêm `-Notebook notebooks/ten.ipynb -Cpu` để chạy notebook demo/kết quả. Framework mặc định `auto`; có thể chỉ rõ `-Framework keras` cho notebook Keras.

Trong WSL ở root: `bash scripts/run_assignment.sh auto --project A04 --cpu --notebook notebooks/diabetes_pipeline04.ipynb`.

Resolver trong WSL: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python scripts/datasets.py A06 a06_02 --verify`. Catalog dùng đường dẫn tính từ repository root; dữ liệu lớn có thể nằm ở bài khác theo SHA, nhưng split/scaler vẫn riêng.

Các layout `provenance/runtime/assign/` là cache tương thích, không phải source hoạt động thứ hai. Tạo lại bằng Python WSL hiện có: `python scripts/materialize_project.py --project A06`; thêm `--copy-only` nếu filesystem không hỗ trợ hardlink. Manifest ở `docs/reorganization/phase2/runtime_view_map.json`, luôn kiểm hash nguồn và từ chối ghi đè target khác hash. Không cần symlink/junction. Sau clean checkout phải cung cấp đủ raw/checkpoint local đúng hash trước; đây không phải một gói tự tải toàn bộ artifact.

## Bảo toàn và giới hạn

Runtime chuyển các thao tác ghi file legacy phổ biến sang một thư mục mới trong `notebooks/executed/artifacts/`; đây là helper chống ghi đè, không phải sandbox cho mọi syscall. Notebook train không được auto-execute bởi migration. A04 mặc định chỉ xem kết quả; bật huấn luyện mới là một thí nghiệm riêng, không sửa các seal/kết quả gốc. Không chạy các controller/TEST lịch sử để kiểm relocation.

CIFAR A04: archive đang có là binary V3, adapter đọc đúng nhãn và NHWC; không giả thành Python pickle. Parity kiểm trên tám ảnh TRAIN. A06: canonical CSV là Git LF; một bản CRLF có cùng toàn bộ hàng CSV được tạo trong provenance để thỏa hash raw của code cũ. Canonical LF không đổi.

Notebook demo CNN/RNN/LSTM tiểu luận dùng migration adapter `assignment_runtime.paper_demo`, gọi serving registry pin seed42. Bản demo thí nghiệm cũ đòi Git HEAD tại lúc train nên được giữ lịch sử. Không thay guard hoặc lock gốc. Serving dùng NumPy CPU cho ba bộ weights đã train; không diễn giải latency này là benchmark native Keras/PyTorch/GPU.

Các phép thử migration sử dụng fixture/synthetic hoặc mẫu TRAIN đã khai báo. Notebook có thể đọc bảng metric/prediction TEST đã lưu để trình bày; không forward TEST mới. Full huấn luyện chưa được chạy lại. Tương thích đầy đủ web/Render và clean-checkout packaging là gate Phase3.
