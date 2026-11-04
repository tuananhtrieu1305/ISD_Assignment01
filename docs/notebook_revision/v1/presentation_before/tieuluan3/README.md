# tieuluan3 — Tiểu luận 3 – sáu chương

Ba thư mục chính: `datasets/`, `notebooks/`, `web/`. Source phụ trợ và kết quả gốc được giữ theo đúng bài.

- Dataset cụ thể, vị trí vật lý, SHA256 và schema: [catalog](datasets/catalog.json).
- Notebook gốc cùng output cũ: `provenance/originals/`; notebook chính là migration revision.
- Kernel Torch/NumPy: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
- Kernel Keras/TensorFlow: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`.
- Mở VS Code trong WSL **Ubuntu**, chọn interpreter tương ứng. Không dùng Python Windows/Anaconda.
- Mỗi bài chạy trong kernel mới để tránh lẫn namespace `src` giữa các bài.

Từ root repository trong PowerShell:

```powershell
./scripts/run_assignment.ps1 -Project tieuluan3 -Inspect
./scripts/run_assignment.ps1 -Project tieuluan3 -ListDatasets
```

Thêm `-Notebook "notebooks/ten_file.ipynb" -Cpu` để chạy notebook xem kết quả/demo được liệt kê. Runner tự chọn framework theo catalog. Notebook train lịch sử chỉ kiểm tĩnh + smoke riêng trong migration; runner không tự Run All chúng. A04 có notebook tách framework trong `notebooks/training/`, mặc định `RUN_TRAINING=False` chỉ xem số liệu cũ. Không train lại để xem báo cáo.

| Notebook | Kernel/framework | Vai trò |
|---|---|---|
| `notebooks/ch06_multi_agent/diabetes.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch06_multi_agent/gold.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch06_multi_agent/house.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch05_knowledge_rag/ch5_finqa.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch05_knowledge_rag/ch5_medquad_diabetes.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch05_knowledge_rag/ch5_wikidata_subgraphs.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch04_rnn_lstm/ch4_bis_house_prices.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch04_rnn_lstm/ch4_gold_pink_sheet.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch04_rnn_lstm/ch4_household_power.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch04_rnn/ch4_bis_house_prices.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch04_rnn/ch4_gold_pink_sheet.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch04_rnn/ch4_household_power.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch03_cnn/ch3_cifar10.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch03_cnn/ch3_eurosat.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch03_cnn/ch3_idrid.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch02_ml/ch2_ames_housing.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch02_ml/ch2_bank_marketing.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |
| `notebooks/ch02_ml/ch2_cdc_diabetes.ipynb` | torch | read-only checkpoint/results demo; fixed TRAIN inputs |

`provenance/runtime/assign/` là layout tương thích được tạo từ manifest, dùng hardlink hoặc copy đã kiểm hash, không cần symlink/junction. Không sửa trực tiếp file trong view. Khi chuyển máy, xem [hướng dẫn chung](../docs/reorganization/phase2_runtime.md) và materialize bằng `scripts/materialize_assignment.py` nếu cần; dataset/checkpoint local lớn không tự có trong Git.

Web đã nghiệm thu Phase3. Chạy `./scripts/run_web.ps1 -Project tieuluan3` từ root, mở http://127.0.0.1:8019. Xem [README web](web/README.md) và [hướng dẫn hiện hành](../docs/reorganization/phase3_runtime.md).
