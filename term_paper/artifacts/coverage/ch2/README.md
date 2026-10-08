# Chapter 2 coverage note

Ngày đo: 2026-10-06  
Công cụ: Python standard-library `trace` trên 17 unit tests; 3 data-integration tests và full artifact verifier được chạy riêng để tránh chi phí trace trên toàn bộ dataset.

| Module | Line coverage |
|---|---:|
| `src/scratch/mlp.py` | 95% |
| `src/keras_impl/mlp.py` | 96% |
| `src/pytorch_impl/mlp.py` | 91% |
| `src/common/ch2_experiment.py` | 98% |
| `src/common/ch2_metrics.py` | 94% |
| `src/common/ch2_protocol.py` | 90% |

`ch2_reporting.py` đạt 20% trong unit-test trace vì phần lớn module là pipeline I/O và CLI. Phần này được kiểm tra end-to-end bằng `term_paper/tools/verify_phase3.py`: đọc lại 27 run, 196.713 prediction rows, load 27 model, tái tính metric và xác minh 4 figure/chapter artifacts.
