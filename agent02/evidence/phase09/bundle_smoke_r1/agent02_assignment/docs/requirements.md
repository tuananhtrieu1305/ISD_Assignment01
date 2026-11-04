# Yêu cầu đã chốt cho Agent02

Ngày: 24/10/2026. Đây là đặc tả phạm vi, không phải protocol thí nghiệm đã khóa.

## Đầu ra và giới hạn

- Báo cáo riêng, nộp một PDF theo mẫu tên `agent02_class_team_name.pdf`.
- Hạn đề ghi: 23:30 ngày 29/10/2026; xác minh giờ lớp trước khi nộp.
- Đủ môi trường e-commerce, hai loại agent, thí nghiệm A–E và trả lời 10 câu.
- Python chạy được, có bảng/hình, cấu hình và seed; kết quả phải đo thật.
- DOCX sửa được và notebook là sản phẩm bổ trợ đề xuất, không thay PDF bắt buộc.
- Slide MAS chỉ tham khảo theo xác nhận người dùng. Không làm 5 bài MAS, không LLM,
  web, API, Render, DQN hay yêu cầu 3 framework/5 layer của bài V3.
- Không áp giới hạn 6 trang của bài trước. Ngắn gọn không đồng nghĩa bỏ câu bắt buộc.

## Chất lượng lý thuyết — U01

Theo lưu ý mới của người dùng: ngắn gọn, đủ ý, dễ hiểu; ưu tiên ví dụ gần gũi và bảng
so sánh. Không đưa công thức phức tạp hoặc dẫn xuất dài nếu không cần để trả lời đề.

Giữ tối thiểu công thức Q-update và phép tính câu 3; giải thích các biến bằng lời.
Phép tính margin câu 5 và reward trung bình câu 6 phải rõ. Không bỏ toán bắt buộc,
nhưng không thêm Bellman proofs, policy gradients hoặc DQN loss ngoài phạm vi.

## Chất lượng biểu đồ — U02

Mọi hình output từ code, notebook hay báo cáo đều phải giải thích được:

1. Hình trả lời câu hỏi nào? Đọc dữ liệu từ CSV/run nào?
2. Trục x/y là gì, đơn vị và mẫu số ra sao?
3. Mỗi đường/cột/vùng sai số biểu thị gì?
4. Raw hay đã làm mượt? Cửa sổ bao nhiêu episode? Tổng hợp qua mấy seed?
5. Xu hướng/dao động quan sát được và chênh lệch định lượng chính là gì?
6. Đó là train hay frozen evaluation? Có đối chứng công bằng không?
7. Điều gì chưa thể kết luận? Không suy ra hội tụ hoặc nhân quả chỉ từ hình đẹp.

Ghi chú diễn giải phải đi cùng hình từ phase 3–7, được dùng lại ở notebook/báo cáo.
Không chỉ chèn ảnh hoặc đọc lại tiêu đề. Khi chưa có số đo, để template chưa điền;
không bịa số để hoàn thiện văn bản. Phase 1 không sinh biểu đồ thí nghiệm.

## Truy vết yêu cầu

R01–R16 và U01–U02 được liệt kê trong mục 3 của plan v1.1. Q1–Q10 lần lượt:
modeling; rule/RL; Q-update; exploration; reward/margin; evaluation; alpha/stability;
interaction/non-stationarity; limitations và sửa môi trường; improved agent.

Baseline giữ một Q-learning đối đầu một rule cố định theo companion/code. Hai learner
cùng học là diagnostic riêng, không được mô tả nhầm là baseline. Alpha cần 3 mức;
exploration cần ít nhất 3 cấu hình. Protocol seeds/eval/config cuối thuộc phase 2.

## Dữ liệu và tái sử dụng

Trajectories chính sinh từ simulator của thầy, có nhãn synthetic. Gold chỉ là mở rộng
hiệu chỉnh kịch bản, không là nhu cầu thật hay giao dịch đầu tư. CDC/Ames phù hợp với
ví dụ thống kê/hỗ trợ, không cung cấp treatment/market intervention trajectories.

Chỉ ghi file mới trong folder Agent02. Runtime WSL Ubuntu/tuananh đã khóa được tái
sử dụng; không cài dependencies hoặc mở TEST/train cũ. Các dataset/model/artifact
V3 và bài trước là đầu vào chỉ đọc. Không tự nộp bài/commit/push/deploy.

## Metadata còn thiếu

Thông tin đã biết: Triệu Tuấn Anh, B23DCCN053, D23CTPM01. Chưa xác nhận làm cá nhân
hay nhóm và `team_name` cho tên PDF cuối; không suy đoán, không chặn phase code.
