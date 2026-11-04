# project01 — hệ đa agent cho tiểu đường

- Kế hoạch hiện hành: `../FINAL_PROJECT01_EXECUTION_PLAN.md`; checkpoint `../docs/final_project01/checkpoint.json`.
- Chỉ thực hiện phase được gọi; Phase 1 dựng nền, Phase 2 mới pipeline/web/đánh giá, Phase 3 DOCX final.
- Tối đa 4 notebook trong toàn bộ `notebooks/`, dự kiến 3. Code thuật toán thật nằm trong cell; backend export một chiều từ notebook ở Phase 2.
- Dùng runtime WSL Ubuntu/user tuananh đã có, CPU NumPy + index; không đổi env hoặc cài trộn Torch/TF.
- Bản gốc dataset/checkpoint/index/metric/TEST của tiểu luận3 chỉ đọc. Không train/TEST lại; benchmark evaluation project01 chỉ chạy ở Phase 2 được yêu cầu, sau khóa protocol/code.
- Corpus MedQuAD là snapshot tiếng Anh. Citation không suy đoán URL bài gốc nếu container không có; output model là lớp no diabetes / prediabetes or diabetes, không phải xác suất mắc mới hoặc chẩn đoán.
- Không commit/push/deploy. Không dùng kết quả evaluation để sửa hệ rồi báo lại cùng số đo; thay đổi phải có revision rõ.
