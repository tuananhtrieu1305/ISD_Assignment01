# Biên bản nghiệm thu Phase 21 — 2026-10-17

Trạng thái: **COMPLETE**. Hai backend độc lập chạy được trên GPU; không cần dùng
fallback Keras/PyTorch. Chưa tải dataset mới, chưa chạy training thực nghiệm và không mở TEST Ch5.

## Runtime đã chốt

- Windows NVIDIA driver 591.74; WSL2 Ubuntu 24.04.4, kernel 6.6.87.2.
- NVIDIA GeForce RTX 5050 Laptop GPU, compute capability 12.0, 8151 MiB VRAM.
- uv 0.13.1, CPython 3.11.17; runtime Linux `~/.local/share/ai-term-paper-v3/`.
- `.venv-torch`: PyTorch 2.14.1+cu130, CUDA 13.0, cuDNN 9.24; wheel có `sm_120`.
- `.venv-keras`: Keras 3.15.1 + TensorFlow 2.21.0; CUDA wheel libraries 12.9,
  cuDNN 9.27. TensorFlow build dùng CUDA 12.5.1, không chứa cubin native sm_120;
  GPU smoke đã chạy thành công qua PTX JIT. Không đồng nhất hai thông tin CUDA này.
- Chung: NumPy 2.4.6, pandas 3.0.6, SciPy 1.17.1, sklearn 1.9.0,
  joblib 1.6.0, Pillow 12.3.0, Keras 3.15.1, h5py 3.14.0.
- `uv.lock` SHA-256: `b0c71fd20e221ed3456278e1916079c46ac206831a98dcf40d3b8f7a83477862`.
  Ba bản export requirements chứa version và hash; bootstrap dùng `--locked`.

Hai venv được tạo mới từ lock trong WSL. Cache và env dùng hardlink cùng filesystem
ext4, tổng runtime đo khoảng 13 GiB; không nhân đôi thư viện chung. Không dùng
Anaconda/venv cũ, không sửa shell profile, không cài Linux display driver hoặc CUDA bằng apt.

## Vấn đề đã xử lý

TensorFlow ban đầu không tìm thấy CUDA shared libraries dù `and-cuda` đã được cài.
Đã áp dụng cấu hình wheel-local theo [hướng dẫn TensorFlow](https://www.tensorflow.org/install/pip),
thêm `LD_LIBRARY_PATH` riêng cho process TensorFlow trong bootstrap, doctor, runner và kernel.
Probe sau sửa đạt; lần đầu mất khoảng 42 giây, lần kiểm tra sau khoảng 17 giây.
Giữ log lỗi ban đầu tại `artifacts/manifests/phase21/tensorflow-initial.*` để đối chiếu.
Không kết luận thiếu hỗ trợ GPU chỉ từ lỗi library discovery.

Đã bổ sung fallback đã khóa, chỉ chọn khi probe thực sự thất bại. Khi chuyển backend,
helper chỉ gỡ symlink do dự án tạo trong venv, tránh để thư mục TensorFlow rỗng bị
nhận nhầm là một module đã cài. Kiểm tra gradient Keras chỉ xét `requires_grad`,
không coi trạng thái RNG không học được là gradient bị thiếu.

## Kiểm chứng

| Kiểm tra | Kết quả | Peak tensor allocator |
|---|---|---:|
| PyTorch GPU: matmul + CNN/RNN/LSTM backward/update | PASS | 88,3 MiB |
| PyTorch CPU fallback: cùng bốn workload | PASS | 0 MiB GPU |
| Keras/TensorFlow GPU: matmul + CNN/RNN/LSTM backward/train_on_batch | PASS | 64,5 MiB |
| Keras/TensorFlow CPU fallback: cùng bốn workload | PASS | 0 MiB GPU |
| Regression API + environment contracts + NumPy scratch compatibility | 46/46 PASS | — |
| Coverage riêng module `src/common/environment.py` | 100% statements | — |
| KG–RAG public demo queries medical/finance | 2/2 PASS | — |

CNN fixture có 5 Conv + 2 Dense; RNN/LSTM fixture có 3 recurrent + 3 Dense.
Tất cả kiểm tra tensor device thật, loss/gradient hữu hạn và trọng số thay đổi.
Peak là số đo allocator framework, **không bao gồm toàn bộ driver context/desktop**;
không được dùng số này làm dự báo bộ nhớ training dataset lớn. Fixture là synthetic,
không phải mô hình/kết quả V3 cuối cùng và không dùng để so metric giữa framework.
Scratch smoke chỉ xác nhận code NumPy V2 còn chạy/save/load được; độ sâu và LSTM
scratch V3 vẫn thuộc Phase 25–29.

`bootstrap.ps1` và `doctor.ps1` đã chạy độc lập thành công; `run_experiment.ps1`
đã chạy bộ 46 test. Lint, format, cú pháp Python/Bash/PowerShell được kiểm tra theo
phạm vi thay đổi. Không cấu hình thêm một static type checker trong phase này.

Verifier bảo toàn đạt: DOCX V2 đúng hash, 998 thành viên source snapshot đúng hash,
11.345 raw Ch5 và 10 prediction TEST đúng hash, `run_count=1`; bundle KG–RAG đúng hash.
Không reset/commit Git và không gỡ Anaconda.

## Cảnh báo còn lại

1. Bốn cảnh báo sklearn xuất hiện khi load preprocessor V2 lưu bằng 1.9.1 trong env
   1.9.0 (bản index Ch5 được lưu bằng 1.9.0). API và demo đạt nhưng chưa đảm bảo
   tương thích mọi serialized object. Không sửa artifact đã khóa; xử lý migration
   riêng ở Phase 30/32, không chạy lại TEST để tuning.
2. TensorFlow dùng PTX JIT trên Blackwell: kernel/shape mới có thể khởi động chậm.
   Mỗi phase training phải kiểm chứng workload thật, không suy rộng smoke thành
   bảo đảm mọi phép toán đều hỗ trợ. Fallback chỉ được dùng khi có log và công khai.
3. Dung lượng host dao động mạnh khi cài/chạy CUDA/WSL; kiểm tra cuối sau khi các
   process GPU kết thúc còn khoảng 11 GiB. Cần kiểm tra/giải phóng thêm trước
   Phase 23 tải dataset lớn. Không dựa vào dung lượng ảo gần 1 TB của WSL.

## Đầu ra và cách dùng

- Hướng dẫn: `docs/environment_v3.md`.
- Lệnh Windows: `scripts/bootstrap.ps1`, `scripts/doctor.ps1`, `scripts/run_experiment.ps1`.
- Lệnh WSL: các file `.sh` tương ứng; hai kernel `AI V3 (torch, WSL GPU)` và
  `AI V3 (keras, WSL GPU)` được đăng ký project-local, đã đặt backend trước import.
- Evidence: `artifacts/manifests/environment.json`, thư mục `artifacts/manifests/phase21/`.
- Các log fallback thất bại cũ chỉ là lịch sử debug; manifest `environment.json`
  mới nhất mới quyết định profile đang hoạt động (`tensorflow`, PASS).

Phase tiếp theo: **22 — Khóa SRS, kiến trúc, schema và giao thức V3**.
