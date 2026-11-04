# tieuluan2 — Tiểu luận 2 – năm chương, dẫn xuất

Ba thư mục chính: `datasets/`, `notebooks/`, `web/`. Source phụ trợ và kết quả gốc được giữ theo đúng bài.

- Dataset cụ thể, vị trí vật lý, SHA256 và schema: [catalog](datasets/catalog.json).
- Notebook gốc cùng output cũ: `provenance/originals/`; notebook chính là migration revision.
- Kernel Torch/NumPy: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
- Kernel Keras/TensorFlow: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`.
- Mở VS Code trong WSL **Ubuntu**, chọn interpreter tương ứng. Không dùng Python Windows/Anaconda.
- Mỗi bài chạy trong kernel mới để tránh lẫn namespace `src` giữa các bài.

Từ root repository trong PowerShell:

```powershell
./scripts/run_assignment.ps1 -Project tieuluan2 -Inspect
./scripts/run_assignment.ps1 -Project tieuluan2 -ListDatasets
```

Notebook hiện hành được gộp thành **4 file**; toàn bộ cây `notebooks/` luôn tối đa 4 notebook. Xem [cách đọc và chạy notebook](../docs/notebook_revision/v1/README.md).

| Notebook | Kernel hỗ trợ | Nội dung |
|---|---|---|
| [01_ML.ipynb](notebooks/01_ML.ipynb) | torch, keras | Code đầy đủ ngay trong cell; mặc định không train/TEST lại |
| [02_CNN.ipynb](notebooks/02_CNN.ipynb) | torch, keras | Code đầy đủ ngay trong cell; mặc định không train/TEST lại |
| [03_RNN_LSTM.ipynb](notebooks/03_RNN_LSTM.ipynb) | torch, keras | Code đầy đủ ngay trong cell; mặc định không train/TEST lại |
| [04_Knowledge_RAG.ipynb](notebooks/04_Knowledge_RAG.ipynb) | torch, keras | Code đầy đủ ngay trong cell; mặc định không train/TEST lại |

Bản trước khi gộp nằm ở `provenance/notebooks_before_inline_v1/notebooks/`, giữ nguyên byte và output. Kết quả chạy mới từ runner nằm tại `artifacts/notebook_runs/`, không sinh thêm notebook trong `notebooks/`.

`%%inline_module` chạy **source có ngay trong cell** trong namespace riêng, không đọc implementation từ file `.py`. Chạy từ trên xuống; sau khi sửa một hàm/lớp, chạy lại cell đó và các cell sử dụng nó. Code dữ liệu, loss/optimizer, model và train/evaluate đều có thể đọc trong notebook. Giữ `RUN_EXPERIMENTS=False` khi xem lại bài đã khóa.

`provenance/runtime/assign/` là layout tương thích được tạo từ manifest, dùng hardlink hoặc copy đã kiểm hash, không cần symlink/junction. Không sửa trực tiếp file trong view. Khi chuyển máy, xem [hướng dẫn chung](../docs/reorganization/phase2_runtime.md) và materialize bằng `scripts/materialize_assignment.py` nếu cần; dataset/checkpoint local lớn không tự có trong Git.

Web đã nghiệm thu Phase3. Chạy `./scripts/run_web.ps1 -Project tieuluan2` từ root, mở http://127.0.0.1:8018. Xem [README web](web/README.md) và [hướng dẫn hiện hành](../docs/reorganization/phase3_runtime.md).
