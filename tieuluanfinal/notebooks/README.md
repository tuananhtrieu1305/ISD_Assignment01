# Bốn notebook của tiểu luận final

| Notebook | Kernel WSL | Nội dung |
|---|---|---|
| [01_ML_CNN.ipynb](01_ML_CNN.ipynb) | Torch hoặc Keras hiện có | Giữ thuật toán và kết quả Ch2–3 |
| [02_RNN_LSTM.ipynb](02_RNN_LSTM.ipynb) | Torch hoặc Keras hiện có | Giữ thuật toán và kết quả Ch4 |
| [03_Knowledge_RAG.ipynb](03_Knowledge_RAG.ipynb) | Torch hiện có | Ch5 như bản tiểu luận3 |
| [04_Multi_Agent.ipynb](04_Multi_Agent.ipynb) | Gemini serving hiện có | Full source 4 agent/RAG/KG, output KQ1–KQ6 |

Chọn interpreter cho notebook04: `/mnt/c/DATA/assign/project01/environment/llm_v2/.venv/bin/python` trong WSL Ubuntu. Ba notebook đầu giữ hai môi trường `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python` và `.venv-keras/bin/python`; không cài trộn dependency.

Notebook chứa code thực trong cell. `%%inline_module` và `%%llm_v2_module` chỉ chạy source trong cell, không đọc implementation từ `.py`. Notebook04 có16module đầy đủ; source backend là export một chiều. Không gọi Gemini khi Run All; phần kết quả nạp lại journal thật đã lưu ngày03/11/2026.

KQ1: thống kê dữ liệu và KG. KQ2: input/output từng stage. KQ3: xếp hạng và nguồn. KQ4: hai câu trả lời cùng Verifier. KQ5: request/token/thời gian. KQ6: biểu đồ có giải thích.

Giữ các cờ API/evaluation/training/TEST ở False. Không chạy lại thí nghiệm khoa học đã khóa. Output của runner ở `../artifacts/notebook_runs/final_ch06_r1/`; journal minh họa ở `../artifacts/final_ch06/live_job_r11.json`. Bản notebook04 trước thay ở `../provenance/before_final_ch06/notebooks/`.
