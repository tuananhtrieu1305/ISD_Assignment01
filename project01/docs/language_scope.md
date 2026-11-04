# Quyết định ngôn ngữ

Corpus MedQuAD phục vụ project là **tiếng Anh**. UI và các nhãn/giải thích pipeline sẽ là tiếng Việt. Trả lời trích xuất giữ tiếng Anh kèm nguồn; không tự dịch nội dung y khoa dài khi chưa có mô hình hoặc bộ dịch được kiểm chứng.

Probe Phase 1 dùng ba nhóm query mới: physical activity, kidney disease và retinopathy trong diabetes. Mỗi nhóm so sánh tiếng Anh, tiếng Việt trực tiếp và query tạo bởi từ điển cụm từ hữu hạn `datasets/query_glossary.json`.

Kết quả chi tiết ở `artifacts/phase1/probe.json`. Cả ba query tiếng Việt trực tiếp đều có **0/3 ID top3 giao với query tiếng Anh tương ứng**; có score dương không chứng minh hiểu câu hỏi. Sau ánh xạ hữu hạn, cả ba nhóm có **3/3 ID top3 trùng** query tiếng Anh. Đây là chẩn đoán lexical ở ba ví dụ, không phải accuracy hỏi đáp, đánh giá dịch hoặc bảo đảm generalization.

Phase 2 sẽ:

- Cho nhập tiếng Anh trực tiếp và tiếng Việt trong phạm vi các khái niệm hỗ trợ; hiển thị rõ query đã ánh xạ.
- Dùng mapping hữu hạn đã khai báo và kiểm riêng. Giữ các từ tiếng Anh chuyên môn đã có; không nhận là dịch toàn văn hoặc hiểu tiếng Việt tự do.
- Nếu không nhận được chủ đề hoặc chỉ còn từ chung chung, hỏi làm rõ thay vì tự tạo câu hỏi có vẻ liên quan.
- Áp policy lên cả input gốc và query chuẩn hóa; không dùng mapping để xóa yêu cầu kê đơn/câu hỏi ngoài phạm vi rồi trả một câu trích xuất không đúng intent.
- Giữ benchmark chính tiếng Anh để đo phối hợp/truy hồi, tách smoke tiếng Việt của glossary và công khai giới hạn này trong demo/báo cáo.

Không bổ sung LLM/API hay môi trường dịch mới chỉ để che giới hạn ngôn ngữ; không thay TEST cũ hoặc điều chỉnh benchmark bằng các probe này.
