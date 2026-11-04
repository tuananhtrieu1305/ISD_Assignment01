# project01 — RAG + LLM v2

- Plan hiện hành: `../FINAL_PROJECT01_LLM_V2_EXECUTION_PLAN.md`; checkpoint `../docs/final_project01/llm_v2/checkpoint.json`. Đọc toàn bộ trước phase.
- Bare phase 1/2/3 và FINAL/LLM phase N thuộc v2: API/KB/protocol → pipeline/web/evaluation mới → tích hợp DOCX final. Không làm lại v1 hoặc tự mở phase kế tiếp.
- Demo chính: `llm_direct` và `agentic_rag`, cùng model/version sinh câu trả lời. Giữ năm vai trò, thêm pre-retrieval/semantic retrieval/reranking/grounded generation/claim verification.
- Chốt provider/model/budget trước API thật; key backend từ env bị Git ignore, không chat/log/frontend/VITE/Git. Lập plan chưa là lệnh bắt đầu Phase 1 hoặc chi tiền.
- Giữ 3 notebook, tối đa 4 file/cây; source thuật toán trong cell, export backend một chiều. Không seed producer cũ hoặc sửa `.py` backend độc lập với notebook.
- Dùng runtime WSL Ubuntu/user tuananh hiện có; không cài trộn framework, train/fine-tune hoặc mở lại TEST khoa học cũ.
- Mọi source/model/index/prediction/metric đã pin giữ bản gốc, đổi có revision. P0/P1/P2 và 120 output cũ không bị ghi đè, 82,5% không là kết quả LLM mới.
- Evaluation mới chỉ Phase 2 v2 sau freeze, mặc định 40 câu ×2 nhánh, không chọn rerun đẹp. Câu hỏi kiến thức là so sánh chính; hồ sơ CDC là tính năng bổ sung.
- Nguồn/citation không đoán URL, không gọi lexical graph là causal KG; score CDC không là xác suất mắc mới/chẩn đoán. Không đủ evidence thì nêu giới hạn.
- UI ưu tiên câu trả lời tiếng Việt; nguồn/trace mở rộng, không tab Luồng agent riêng. Không commit/push/deploy; một DOCX final, project report Markdown.
