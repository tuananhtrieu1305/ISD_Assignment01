# project01 — RAG + LLM v2

- R8 ngày03/11: runtime `full-demo-r8`, nút Demo đủ5agent dùng câu DPP58 và hồ sơ TRAIN đủ21field. Risk output đưa vào Reporter; code ghép summary trước Verifier và kiểm đúng score. Vẫn3generation, rawprofile chỉ local. Đọc `docs/llm_v2/DEMO_FULL_PIPELINE_R8.md` và checkpoint. Chưa chạy cặp Gemini thật cho câu này, không khẳng định baseline sai; không tự gọi API để tìm output thắng.

- Revision hiện hành r7: đúng3 generation call/cặp (direct + pre-retrieval + Reporter).
  Knowledge Agent dùng hybrid retrieval/KG và reranker local; Code Verifier dùng Python;
  không LLM rerank/verify/repair. Embedding query dùng quota riêng. Không bắt đầu job mới
  nếu còn dưới3 generation slot. Tab `03 Luồng xử lý` riêng đã được người dùng yêu cầu,
  ưu tiên hiển thị input/output thật và công cụ của năm vai trò.

- Plan hiện hành: `../FINAL_PROJECT01_LLM_V2_EXECUTION_PLAN.md`; checkpoint `../docs/final_project01/llm_v2/checkpoint.json`. Đọc toàn bộ trước phase.
- Plan 2.3 lấy `../RAG_KG_Tham_khao/PTHTTM-RAG/` làm nguồn ban đầu: Phase 1 copy đủ module/helper/asset cần dùng vào `provenance/group_rag_kg_source/` kèm transfer manifest/hash, Phase 2 port từ bản local vào notebook. Không chỉ học ý tưởng rồi viết lại; đọc reference_rag_kg_review.md/snapshot và giữ attribution.
- Bàn giao project01 tự chứa source/package cần chạy; không import/read/symlink/PYTHONPATH tới folder tham khảo hoặc dùng provenance làm implementation bí mật. Phase 2 clean-start không có folder tham khảo; Phase 3 sau gate mục 4.6 xóa đúng `C:\DATA\assign\RAG_KG_Tham_khao` theo yêu cầu người dùng và smoke lại. Giữ nguồn nguyên trạng tới gate, không xóa trong lượt sửa plan, không xóa env/dữ liệu bài khác.
- Mọi call OpenAI/Groq trong code port chuyển sang Gemini, gồm pre-retrieval/generation/KG extraction. Chỉ free tier, trả phí 0 USD. Không copy key/index/graph luật hoặc bắt thêm key nhà cung cấp khác.
- KG làm nhỏ theo mục 4.5: seed curated từ 20–40 đoạn có quote/nguồn, extraction/cache/aggregate/visualize kế thừa nhóm, JSON/adjacency và 1–2 hop lấy source chunk vào RRF/rerank. Không thêm Neo4j/Qdrant server hoặc extract toàn corpus để demo; số cạnh không là chỉ tiêu phải lấp bằng suy đoán.
- Bare phase 1/2/3 và FINAL/LLM phase N thuộc v2: API/KB/protocol → pipeline/web/evaluation mới → tích hợp DOCX final. Không làm lại v1 hoặc tự mở phase kế tiếp.
- Demo chính: `llm_direct` và `agentic_rag`, cùng model/version sinh câu trả lời. Giữ năm vai trò, thêm pre-retrieval/semantic retrieval/reranking/grounded generation/claim verification.
- Chốt provider/model/budget trước API thật; key backend từ env bị Git ignore, không chat/log/frontend/VITE/Git. Lập plan chưa là lệnh bắt đầu Phase 1 hoặc chi tiền.
- Giữ 3 notebook, tối đa 4 file/cây; source thuật toán trong cell, export backend một chiều. Không seed producer cũ hoặc sửa `.py` backend độc lập với notebook.
- Giữ hai runtime khoa học WSL Ubuntu/user tuananh hiện có; thiếu dependency core RAG được dùng env phục vụ nhỏ có khóa thay vì viết lại toàn bộ core hoặc cài trộn vào env GPU. Không train/fine-tune hoặc mở lại TEST khoa học cũ.
- Mọi source/model/index/prediction/metric đã pin giữ bản gốc, đổi có revision. P0/P1/P2 và 120 output cũ không bị ghi đè, 82,5% không là kết quả LLM mới.
- Evaluation mới chỉ Phase 2 v2 sau freeze, mặc định 40 câu ×2 nhánh, không chọn rerun đẹp. Câu hỏi kiến thức là so sánh chính; hồ sơ CDC là tính năng bổ sung.
- Nguồn/citation không đoán URL, không gọi lexical graph là causal KG; score CDC không là xác suất mắc mới/chẩn đoán. Không đủ evidence thì nêu giới hạn.
- UI ưu tiên câu trả lời tiếng Việt; nguồn/trace mở rộng và tab Luồng xử lý riêng. Không commit/push/deploy; một DOCX final, project report Markdown.
