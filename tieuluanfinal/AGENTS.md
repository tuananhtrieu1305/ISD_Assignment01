# Tiểu luận final

Revision riêng theo yêu cầu ngày03/11/2026: copy tieuluan3, chỉ thay Chương6 bằng project01 four-agent-r11.
Không sửa ngược tieuluan3/project01 hoặc chạy train/TEST/evaluation/API để dựng báo cáo.
Ch1–5 giữ code khoa học; notebook chỉ đổi PROJECT_NAME để chọn bản sao.
Notebook04 chứa source đầy đủ, backend export bằng scripts/prepare_tieuluanfinal.py --export ở root.
Tối đa4notebook, bản cũ giữ trong provenance/before_final_ch06.
Web tích hợp chạy Git Bash: bash tieuluanfinal/scripts/run_web.sh; port8040.
Ch6 Gemini dùng env serving đã khóa, Ch1–5 dùng envTorch hiện có, không cài trộn dependency.
Sổ quota chia sẻ bằng GEMINI_STATE_ROOT, key chỉ kế thừa trong process; không copy.env.
DOCX bản gốc ngoài workspace chỉ đọc, giữ mọi phần ngoàiCh6 và navigation liên quan.
Không commit/push/deploy. Bằng chứng ở docs/final_revision và artifacts/final_ch06.
