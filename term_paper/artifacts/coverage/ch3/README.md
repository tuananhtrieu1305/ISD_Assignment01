# Chapter 3 coverage note

Ngày đo: 2026-10-06  
Công cụ: Python standard-library `trace` trên 19 unit/integration tests. Full artifact verification được chạy riêng để tránh tính thời gian load 18 model vào unit coverage.

| Module | Line coverage |
|---|---:|
| `src/scratch/cnn.py` | 97% |
| `src/keras_impl/cnn.py` | 98% |
| `src/pytorch_impl/cnn.py` | 94% |
| `src/common/ch3_data.py` | 96% |
| `src/common/ch3_metrics.py` | 100% |
| `src/common/ch3_protocol.py` | 90% |
| `src/common/ch3_experiment.py` | 80% |

Hai module orchestration `run_ch3_experiments.py` và `ch3_reporting.py` có coverage unit lần lượt 12% và 18% vì phần lớn mã là pipeline I/O/CLI. Các nhánh production này đã chạy end-to-end: 18 run, 14.850 prediction rows, 18 model load-check, metric reproduction, sample-key parity, A05 provenance, notebook execution và figure/chapter validation đều PASS trong `term_paper/tools/verify_phase4.py`.
