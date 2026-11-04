# Notebook hiện hành

Notebook hiện hành được gộp thành **3 file**; toàn bộ cây `notebooks/` luôn tối đa 4 notebook. Xem [cách đọc và chạy notebook](../docs/notebook_revision/v1/README.md).

| Notebook | Kernel hỗ trợ | Nội dung |
|---|---|---|
| [customer_behavior_pipeline.ipynb](notebooks/customer_behavior_pipeline.ipynb) | torch | Code notebook trực tiếp; output lịch sử giữ nguyên |
| [diabetes_pipeline.ipynb](notebooks/diabetes_pipeline.ipynb) | torch | Code notebook trực tiếp; output lịch sử giữ nguyên |
| [house_price_pipeline.ipynb](notebooks/house_price_pipeline.ipynb) | torch | Code notebook trực tiếp; output lịch sử giữ nguyên |

Bản trước khi gộp nằm ở `provenance/notebooks_before_inline_v1/notebooks/`, giữ nguyên byte và output. Kết quả chạy mới từ runner nằm tại `artifacts/notebook_runs/`, không sinh thêm notebook trong `notebooks/`.

Chọn kernel theo [README bài](../README.md). Mở [hướng dẫn chung](../../docs/notebook_revision/v1/README.md).
