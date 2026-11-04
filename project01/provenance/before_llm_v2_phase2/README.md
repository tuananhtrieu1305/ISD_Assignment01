# Project01 — Diabetes Agent Lab

Phase 2 đã có pipeline **5 agent + model CDC + KB/KG/RAG MedQuAD**, web React/Python và đánh giá mới. Chạy CPU, không cần LLM/API trả phí. Tích hợp tiểu luận final thuộc Phase 3.

Từ root `C:\DATA\assign` trong PowerShell:

```powershell
./project01/scripts/build_web.ps1
./project01/scripts/run_web.ps1
```

Mở **http://127.0.0.1:8031**; Ctrl+C để dừng. Bấm chạy sẽ dùng cùng đầu vào qua P0/P1/P2. Bảng benchmark chỉ đọc saved summary, không chạy evaluation lại. Gói medical-only 4.772.359 byte, không cần raw CSV/finance index/runtime view cũ để phục vụ demo.

| Notebook | Code và output |
|---|---|
| [01_Data_KB_RAG.ipynb](notebooks/01_Data_KB_RAG.ipynb) | Preprocessing, 6 Dense, BM25/LSA, graph, fusion, trích xuất; demo TRAIN/development |
| [02_Diabetes_Multi_Agent.ipynb](notebooks/02_Diabetes_Multi_Agent.ipynb) | Coordinator, Risk/Knowledge Agent, Verifier/Reporter, budget/process deadline, Flask API |
| [03_Evaluation.ipynb](notebooks/03_Evaluation.ipynb) | Evaluator, review, tổng hợp và plot; mặc định chỉ đọc kết quả đã lưu |

Code thật trong cell `%%project_module`; backend là export của notebook, không chỉnh `.py` riêng. Import giữa module dùng export của notebook tương ứng. Ba notebook đã chạy kernel thật và có output; Run All không train/TEST cũ hoặc tự chạy evaluation. Output mới lưu ở `artifacts/notebook_runs/`.

Kernel WSL Ubuntu/user tuananh: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.

```powershell
./project01/scripts/run.ps1 -Inspect
./project01/scripts/run.ps1 -Notebook 01_Data_KB_RAG.ipynb
./project01/scripts/run.ps1 -Notebook 02_Diabetes_Multi_Agent.ipynb
./project01/scripts/run.ps1 -Notebook 03_Evaluation.ipynb
```

Trong WSL, từ root: `python -B project01/scripts/notebook_source.py check` kiểm export; đổi thuật toán cần revision rồi `export`, không `seed` lại. Producer seed đã chặn sau freeze. `/ready` từ chối khi package sai hash hoặc notebook khác export.

Dữ liệu: CDC253.680 dòng/21 field, target dương gộp prediabetes/diabetes; model6 Dense seed42, score class-weighted không là xác suất mắc mới. `age` là nhóm1–13, không số tuổi; thiếu field không tự điền. MedQuAD762 chunk/247 document/62 lexical anchor; graph không ontology y khoa đầy đủ, dense là LSA. Corpus/trích đoạn tiếng Anh; UI tiếng Việt và query tiếng Việt qua glossary giới hạn. Citation là repository/commit + local locator, không raw URL từng bài. API không lưu hồ sơ gửi lên.

Kết quả:120 output từ40 tình huống ×3 biến thể, mỗi cặp chạy một lần. Sau review, cả ba **33/40=82,5% task success**; không phải accuracy chẩn đoán. P2 phát hiện tamper tốt hơn ở automatic checks nhưng chưa tăng chất lượng end-to-end vì lớp trích xuất còn yếu. Review bởi Codex assistant, không independent human/clinical review. Xem [báo cáo và giải thích plot](report/Project01_Report.md).

`evaluation/raw_results/` giữ raw nguyên byte; `evaluation/results/` là dẫn xuất thêm review/task labels, có `derived_from` hash; payload/timing không đổi. Không chạy lại evaluation sau khi đã xem kết quả. Chỉ audit/plot từ saved outputs.

[Protocol](docs/evaluation_protocol.md) · [nguồn dữ liệu](docs/data_sources.md) · [hướng dẫn Render](web/deploy/README.md). Chưa deploy cloud. Project `.gitignore` mở riêng JSON metadata/synthetic task cần dùng khi commit; raw/venv/secret vẫn bỏ qua. Các bản Phase1 và draft authoring giữ ở provenance.
