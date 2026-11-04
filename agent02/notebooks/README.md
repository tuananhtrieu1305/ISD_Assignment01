# Notebook hiện hành

Notebook hiện hành được gộp thành **1 file**; toàn bộ cây `notebooks/` luôn tối đa 4 notebook. Xem [cách đọc và chạy notebook](../docs/notebook_revision/v1/README.md).

| Notebook | Kernel hỗ trợ | Nội dung |
|---|---|---|
| [AG02_Code_and_Results.ipynb](notebooks/AG02_Code_and_Results.ipynb) | torch | Code đầy đủ ngay trong cell; mặc định không train/TEST lại |

Bản trước khi gộp nằm ở `provenance/notebooks_before_inline_v1/notebooks/`, giữ nguyên byte và output. Kết quả chạy mới từ runner nằm tại `artifacts/notebook_runs/`, không sinh thêm notebook trong `notebooks/`.

`%%inline_module` chạy **source có ngay trong cell** trong namespace riêng, không đọc implementation từ file `.py`. Chạy từ trên xuống; sau khi sửa một hàm/lớp, chạy lại cell đó và các cell sử dụng nó. Code dữ liệu, loss/optimizer, model và train/evaluate đều có thể đọc trong notebook. Giữ `RUN_EXPERIMENTS=False` khi xem lại bài đã khóa.

Chọn kernel theo [README bài](../README.md). Mở [hướng dẫn chung](../../docs/notebook_revision/v1/README.md).
