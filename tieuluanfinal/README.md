# Tiểu luận final

Bản sao của tieuluan3. Chương1–5 và các scientific artifact cũ được giữ; Chương6 thay bằng hệ4agent Coordinator → Knowledge → Reporter → Verifier của project01 (four-agent-r11). Không Risk/hồ sơ.

## Chạy demo trong Git Bash

```bash
cd /c/DATA/assign
bash tieuluanfinal/scripts/run_web.sh
```

Mở http://127.0.0.1:8040, tab Multi-Agent tại /agents. Cần các port8040–8042 trống; Ctrl+C dừng đúng các worker launcher tạo. Nếu đổi port, ví dụ `bash tieuluanfinal/scripts/run_web.sh 8050`, hai port kế tiếp cũng phải trống.

Ch1–5 dùng serving bundle gốc đã pin trong bản sao, không train/TEST. Ch6 sử dụng source/config/corpus/index/KG đóng gói tại web/agent; không chạy implementation từ project01 hay folder tham khảo. Ch6 dùng lại môi trường WSL project01/environment/llm_v2/.venv và sổ quota project01/artifacts/llm_v2/runtime để không vô tình reset ngân sách. Key có thể đặt trong biến môi trường hoặc tieuluanfinal/.env; nếu chưa có, launcher đọc key hiện có ở project01/.env vào process mà không sao chép hay in giá trị.

Một cặp cần4generation request, query embedding dùng quota riêng. Mở trang/KG/health không gọi model. Không tự chạy thêm câu để tìm kết quả thắng.

## Notebook

- 01_ML_CNN.ipynb: code và kết quả Ch2–3 như tiểu luận3; hai kernel Torch/Keras đã có.
- 02_RNN_LSTM.ipynb: Ch4, hai kernel hiện có.
- 03_Knowledge_RAG.ipynb: Ch5 như tiểu luận3.
- 04_Multi_Agent.ipynb: full source Ch6 mới và các output KQ1–KQ6. Kernel WSL `/mnt/c/DATA/assign/project01/environment/llm_v2/.venv/bin/python`; Run All không gọi API/train/TEST.

Output Ch6 đọc từ lượt thật ngày03/11: artifacts/final_ch06/live_job_r11.json. Một lượt development, không phải benchmark held-out và không chứng minh pipeline luôn thắng.

## Báo cáo

File cuối: report/final/Tieu_Luan_AI_Final.docx, dựa trực tiếp trên DOCX người dùng gửi; chỉ đổiCh6 và các mục navigation củaCh6. Bản nguồn/bìa/Ch1–5/kết luận giữ nguyên. Bản notebookCh6 trước sửa ở provenance/before_final_ch06.

Build bằng toolchain Node22 đã có: từ root chạy `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tieuluanfinal/scripts/build_final_web.ps1`.

Bản local này chưa deploy cloud; root render.yaml vẫn trỏ bản tiểu luận3 hiện có. Không coi archiveCh6 cũ là pipelineGemini mới. Không copy venv/node_modules/secret; danh sách copy/hash trong docs/final_revision.
