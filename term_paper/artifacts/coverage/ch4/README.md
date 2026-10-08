# Chapter 4 coverage note

Ngày đo: 2026-10-06  
Công cụ: Python standard-library `trace --count --missing` trên 20 unit/integration tests. Full artifact verification được chạy riêng để kiểm tra 18 model, 75.690 prediction rows, notebook và manuscript.

| Module | Line coverage |
|---|---:|
| `src/scratch/rnn.py` | 97,8% |
| `src/keras_impl/rnn.py` | 96,9% |
| `src/pytorch_impl/rnn.py` | 92,7% |
| `src/common/ch4_data.py` | 97,2% |
| `src/common/ch4_metrics.py` | 100,0% |
| `src/common/ch4_protocol.py` | 81,5% |
| `src/common/ch4_experiment.py` | 70,6% |

Hai module orchestration `run_ch4_experiments.py` và `ch4_reporting.py` có coverage unit lần lượt 15,5% và 22,5% vì phần lớn mã là pipeline I/O/CLI và vẽ hình. Các nhánh production này đã chạy end-to-end: 18 run, 18/18 model load-check, metric reproduction, key/date parity, A06 provenance, sáu figure và notebook execution đều PASS trong `term_paper/tools/verify_phase5.py`.
