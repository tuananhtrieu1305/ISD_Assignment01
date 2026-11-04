# Bàn giao tiểu luận final ngày 04/11/2026

Báo cáo cuối ở `../../report/final/Tieu_Luan_AI_Final.docx`. Bản gốc người dùng gửi được giữ nguyên trong `../../provenance/before_final_ch06/`. Chỉ thay Chương6 và các mục điều hướng/bảng/hình của chương này; nội dung Chương1–5, bìa và kết luận giữ nguyên.

Chương6 trình bày bốn vai trò Coordinator → Knowledge → Reporter → Verifier, dữ liệu MedQuAD và mini-KG, hợp các hàm, một lượt chạy thật và giới hạn của kết quả. Mọi trích dẫn NB6–KQ1…KQ6 trỏ đến các phần output trong notebook04. Câu trả lời lấy nguyên trạng từ journal `56d62ac4-77f4-4cf8-a2e7-f01584c2e240` của bản four-agent-r11 ngày03/11, không dùng fixture giả lập làm kết quả mô hình.

Có đúng4notebook. Ba notebook đầu giữ các cell thuật toán như tiểu luận3; bootstrap chọn bản sao final. Notebook04 chứa16module đầy đủ và230cell code đã chạy thành công khi mạng bị chặn. Export backend khớp source notebook. Không train, forward TEST hoặc gọi Gemini/embedding mới trong quá trình làm final.

Demo giữ các chương cũ và tích hợp tab Multi-Agent mới. Từ Git Bash tại `C:/DATA/assign`, chạy `bash tieuluanfinal/scripts/run_web.sh`, mở `http://127.0.0.1:8040/agents`. Các port8040–8042 cần trống. Dùng lại hai runtime đã có; key chỉ ở backend, quota chia sẻ với project01. Không cần cài Neo4j hoặc cài lại môi trường GPU.

React build, TypeScript,11kiểm tra UI/API, đọc index/KG/key khi mạng bị chặn và mở Word chỉ đọc đều PASS. Đã render toàn báo cáo; trang thay đổi được kiểm ảnh,106trang còn lại trùng pixel với bản gốc ngoài trường footer. Word và LibreOffice có thể phân trang khác nhau do bộ dựng/font; không sửa các phần ngoài phạm vi để ép số trang.

Một lượt development chỉ cho phép phân tích ví dụ và chi phí, chưa chứng minh pipeline luôn tốt hơn LLM trực tiếp. Benchmark held-out40cặp của kế hoạch v2 chưa chạy; trạng thái kế hoạch đánh giá cũ được giữ nguyên. Chưa commit, push hoặc deploy cloud.

Bằng chứng: `verification.json`, `document_scope.json`, `readiness.json`; output notebook và journal ở `../../artifacts/`. Hash audit của bản sao kiểm70.873file, giữ các dataset/checkpoint/metric/prediction khoa học nguyên byte.
