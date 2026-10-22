# Môi trường V3 — WSL2/GPU

## Tái tạo và kiểm tra

Từ PowerShell tại `C:\DATA\assign`:

```powershell
.\scripts\bootstrap.ps1
.\scripts\doctor.ps1
```

Bootstrap sử dụng distro `Ubuntu-24.04`, uv 0.13.1 và CPython 3.11.17. Không dùng
Anaconda, Python MSYS/Windows hay venv V2. Lần đầu cần ít nhất 20 GiB trống trên ổ
chứa repository/VHD; khi tiếp tục cài cần ít nhất 2 GiB dự phòng.
Không dựa vào dung lượng ảo của `/` trong WSL để đánh giá dung lượng ổ C.
Mặc định VHD và repository đều nằm trên C; nếu chuyển VHD sang ổ khác phải kiểm tra cả hai ổ.

Runtime và cache nằm tại `~/.local/share/ai-term-paper-v3/` **trong WSL**:

| Thành phần | Vị trí |
|---|---|
| PyTorch GPU, NumPy scratch, API, công cụ report | `.venv-torch/bin/python` |
| Keras GPU | `.venv-keras/bin/python` |
| Python được quản lý | `python/` |
| Cache hardlink cùng filesystem ext4 | `cache/` |
| Jupyter kernels | `share/jupyter/kernels/` |

`uv.lock` là nguồn khóa chính. Các bản xuất `requirements/torch.lock`, `keras.lock`
và `keras-torch.lock` chứa hash để kiểm toán. `uv sync --locked` không tự resolve
lại khi bootstrap. Không cài thêm bằng pip tùy tiện. Muốn đổi dependency phải sửa
`pyproject.toml`, khóa lại bằng uv rồi xuất lại cả ba requirements và chạy doctor.

## Chính sách backend

Hai env có cùng phiên bản thư viện xử lý dữ liệu, nhưng tách backend CUDA để không
xung đột TensorFlow/PyTorch. Bootstrap thử TensorFlow chính thức trước bằng ma trận,
CNN, RNN, LSTM và backward thực. Nếu thất bại, giữ nguyên log/JSON rồi chuyển env
Keras sang extra `keras-torch` đã khóa. Đây vẫn là Keras 3 API nhưng dùng chung
engine PyTorch, **không phải một backend độc lập**; khi so sánh trong báo cáo phải
công khai hạn chế này. Không tự compile TensorFlow hoặc dùng wheel không chính thức.

Backend được chốt trong `artifacts/manifests/environment.json`, không được suy ra
chỉ từ tên GPU hoặc `is_available()`. Doctor chạy mỗi backend trên GPU và CPU ở
process riêng; kiểm tra tensor device, gradient hữu hạn, cập nhật trọng số, layer
count và peak VRAM dưới 8 GiB. Dữ liệu là synthetic nhỏ, không phải kết quả thí nghiệm.
Không chạy evaluator TEST Ch5 trong quy trình này.

Wrapper chọn đúng môi trường/backend trước import (runner thí nghiệm mới được xây ở Phase 25):

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module pytest tests/api -q
```

Trong WSL có thể dùng `bash scripts/run_experiment.sh torch pytest tests/api -q`.
`scratch` chọn env NumPy/PyTorch nhưng code scratch không được gọi autograd/layer framework.

## VS Code và notebook

1. Mở terminal WSL: `wsl -d Ubuntu-24.04`.
2. `cd /mnt/c/DATA/assign` rồi `code .`; chọn cửa sổ **WSL: Ubuntu-24.04**.
3. Select Interpreter trỏ tới đường dẫn Linux đầy đủ của `.venv-torch/bin/python`
   hoặc `.venv-keras/bin/python` phía trên. Không chọn interpreter Windows.
4. Trong notebook chọn kernel `AI V3 (torch, WSL GPU)` hoặc `AI V3 (keras, WSL GPU)`.
   Nếu chưa thấy kernel, chọn trực tiếp Python environment tương ứng.
5. Với notebook Keras phải đặt `os.environ['KERAS_BACKEND']` **trước khi import keras**:
   `tensorflow` nếu manifest chọn TensorFlow, `torch` nếu manifest chọn `keras-torch`.
   Restart kernel khi đổi backend. CPU fallback: đặt `CUDA_VISIBLE_DEVICES=-1`
   trước import framework; luôn ghi rõ CPU trong kết quả.

Chạy JupyterLab trong WSL (không mở server công khai):

```bash
cd /mnt/c/DATA/assign
source scripts/runtime_common.sh
export KERAS_BACKEND=torch  # chỉ khi manifest chọn keras-torch
"$task_runtime/.venv-torch/bin/python" -m jupyterlab --ip=127.0.0.1 --no-browser
```

Chạy API và regression tests bằng cùng env trong WSL:

```bash
source scripts/runtime_common.sh
"$task_runtime/.venv-torch/bin/python" -m apps.api.app
# Terminal WSL khác, cùng repository:
source scripts/runtime_common.sh
"$task_runtime/.venv-torch/bin/python" -m pytest tests/api -q
```

Các notebook `legacy/` chưa được chuyển sang contract V3: không chạy hàng loạt.
Frontend vẫn chạy bằng Node riêng ở `apps/web/`; Phase 21 không cài lại node_modules.
Môi trường Render CPU được xử lý theo deploy contract ở Phase 32, không đưa CUDA lên Render.

## Nguồn chính thức

- [uv: tích hợp PyTorch và explicit CUDA index](https://docs.astral.sh/uv/guides/integration/pytorch/).
- [TensorFlow: cài GPU trong WSL bằng and-cuda](https://www.tensorflow.org/install/pip).
- [Keras 3: chọn backend trước import và tách môi trường](https://keras.io/getting_started/).

## Dung lượng và lỗi cài

Không xóa Anaconda tự động: đó không phải dependency của V3 nhưng có thể phục vụ
dự án khác. Không cài Linux NVIDIA display driver trong WSL. Giữ driver Windows
đang hoạt động; bootstrap chỉ dùng wheel CUDA chính thức đã khóa.
Khi tải gián đoạn, chạy lại bootstrap để tái sử dụng cache. Không xóa raw/cache Ch5.
Nếu thiếu dung lượng, dừng và giải phóng ổ chứa VHD trước khi chạy tiếp.
