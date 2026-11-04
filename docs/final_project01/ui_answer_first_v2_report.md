# UI revision answer_first_v2 — 01/11/2026

Yêu cầu: ưu tiên câu trả lời cuối cho người dùng; tab Luồng agent riêng trở nên dư sau khi đã có quy trình ngay trong trang kết quả.

## Kết quả

- Menu còn 3 tab: Câu hỏi & hồ sơ, Kết quả & nguồn, So sánh phương pháp.
- Kết quả mở bằng khối **Câu trả lời cho bạn**, lấy nội dung từ `output.answer.sections` hiện có của backend. Phần trả lời kiến thức được trình bày trước, kết quả hồ sơ kế tiếp, rồi thông tin cần bổ sung/lỗi. Không viết câu trả lời y khoa mới trong React.
- Giữ câu hỏi thực sự đã gửi theo lượt chạy; sửa form mà chưa chạy không làm câu hỏi trên kết quả cũ bị thay nhầm.
- Nguồn, query, model detail và các đoạn ứng viên nằm trong phần mở rộng. Link đối chiếu ngay dưới câu trả lời tự mở phần nguồn.
- So sánh cách xử lý P0/P1/P2 vẫn nằm bên dưới; nhật ký trace chi tiết được gộp thành phần mở rộng ngay tại đó. Đã bỏ nhánh tab trace và nút chuyển tới tab cũ.
- Thiếu BMI hiển thị thông tin cần bổ sung trong câu trả lời, không tạo score; knowledge-only không có kết quả mô hình; numeric-only không có câu trả lời kiến thức giả; từ chối ngoài phạm vi được diễn đạt dễ hiểu.

Giới hạn thuật toán vẫn như Phase 2: câu trả lời kiến thức là trích đoạn tiếng Anh được chọn từ corpus, chưa được LLM tổng hợp/viết lại. Ví dụ vận động hiện trả một lời nhắc trao đổi với bác sĩ trước khi bắt đầu hoạt động mới, chưa phải phần giải thích toàn diện về lợi ích vận động. Revision này sửa thứ tự và mức độ rõ ràng trên UI, không biến trích đoạn ngắn thành một lời giải thích đầy đủ hoặc thay kết luận đánh giá.

## Bảo toàn và kiểm tra

- Đã lưu đủ 16 file theo release `results_flow_v1` trước khi sửa, cùng SHA-256 trong `project01/artifacts/ui_revisions/answer_first_v2/preservation.json`; bản gốc ở `project01/provenance/ui_before_answer_first_v2/`.
- Không sửa notebook, backend, model, dataset, graph/index, evaluator, freeze hay 120 output đã khóa. Acceptance Phase 2 và release UI v1 giữ nguyên.
- Vite production build PASS; 32 kiểm tra browser với API thật PASS. Kiểm câu trả lời khớp chính xác backend, thứ tự hiển thị, 3 tab, link mở citation, trace inline, đổi variant, knowledge/numeric/combined, thiếu BMI, ngoài phạm vi, câu hỏi đã gửi không đổi khi sửa form, mobile và không có lỗi JavaScript.
- Đã xem ảnh desktop/mobile mới; câu trả lời nằm trước nguồn và khối quy trình, không tràn trang. Máy chủ kiểm tra cổng 8042 đã dừng, không đụng máy chủ người dùng ở 8031.
- Không chạy bộ benchmark lại. Đây chỉ là các lượt ví dụ kiểm UI, không ghi đè raw results và không train/TEST.

Audit hiện hành: `project01/scripts/verify_answer_first_v2.py`. Script resolve release UI v1 về archive tương ứng rồi gọi verifier v1 nguyên trạng; v1 tiếp tục resolve UI Phase 2 về archive Phase 2. File mới được pin ở `answer_first_v2/release.json`, kết quả audit mới ở `verification.json`. Không gọi verifier lịch sử trực tiếp rồi cập nhật lại hash để bỏ qua thay đổi.

Dist đã build. Khi server đang chạy, Ctrl+F5 rồi chạy lại ví dụ sẽ thấy bản mới. Phase 3 vẫn READY, chưa tự bắt đầu; không commit/push/deploy.
