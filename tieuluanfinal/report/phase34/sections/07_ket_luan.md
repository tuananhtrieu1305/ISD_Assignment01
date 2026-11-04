# KẾT LUẬN

## K.1. Kết quả đạt được

Các thực nghiệm cho thấy chất lượng của một hệ AI phải được đọc cùng cấu trúc dữ liệu
và điều kiện đánh giá. Học từ đầu làm rõ forward, loss, gradient và cập nhật trọng số;
thư viện giúp tổ chức và thực thi, nhưng không thay thế việc kiểm tra split, nhãn và
đơn vị. Hợp hàm và bảng từng hàm nối hai cách nhìn này: từ một ví dụ đầu vào tới kết
quả, rồi từ kết quả quay về đúng phép tính trong code.

Với dữ liệu bảng, MLP sáu lớp hoạt động được ở cả ba implementation, nhưng không
thường xuyên vượt mô hình cổ điển. Trên CDC và Bank, rừng cây có trung bình macro-F1
cao hơn MLP trong cấu hình đã khóa. Trên Ames, sai số của mạng và rừng cây cần đọc
cùng độ lệch chuẩn, không chỉ thứ hạng trung bình. Accuracy của majority cao ở tập
mất cân bằng không đi kèm khả năng nhận ra lớp thiểu số. Vì vậy, câu trả lời cho câu
hỏi Chương2 là phải so với baseline phù hợp và dùng nhiều góc nhìn chất lượng.

Với ảnh, CNN bảy lớp cho phép đối chiếu trọn vẹn ba implementation trên ba miền.
EuroSAT và CIFAR-10 có kết quả học hữu ích trong matched track, trong khi IDRiD còn
macro-F1 thấp và nhiều lớp có recall bằng0. Tăng số lớp để đủ độ sâu không tự giải
quyết kích thước dữ liệu, mất cân bằng và chi tiết nhỏ bị mất khi resize. Saliency
TRAIN chỉ minh họa độ nhạy của mạng, không xác nhận dấu hiệu bệnh hoặc quan hệ nhân quả.

Với chuỗi, LSTM không mặc định tốt hơn Vanilla RNN. Kết quả vàng và BIS không vượt
baseline đơn giản ở metric chính, còn điện năng cho thấy mạng có thể khai thác cấu
trúc hữu ích hơn. Các horizon không có cùng đơn vị thời gian giữa ba miền, nên không
gộp thành một sai số chung. Bộ nhớ/cổng và gradient diagnostics giúp giải thích cơ
chế, nhưng không đủ để suy rằng mô hình sẽ dự đoán thị trường tương lai tốt hơn.

Với tri thức, KG có ích rõ khi lân cận graph đưa thêm evidence đúng vào tập ứng viên
y khoa. Trên tài chính, B4 không luôn vượt BM25 và việc tìm đoạn có liên quan vẫn chưa
giải được chương trình suy luận số của FinQA. Citation hợp lệ chỉ xác nhận nguồn có
thể truy ra; nó khác việc chọn đúng gold evidence hoặc đưa ra answer đúng. Chương5
vì vậy giữ riêng retrieval, answer và provenance thay vì quy tất cả thành “độ chính xác RAG”.

Với hệ đa tác tử, thêm verifier giúp chặn các output bị can thiệp trong challenge đã
khai báo. Nó không cải thiện phép tính của tool vốn đúng và không khiến hệ hiểu câu
hỏi tự do. A2 có task success cao hơn vì từ chối đúng output hỏng; answer completion
không tăng theo cùng cách. Thêm vai trò còn tăng message và công việc kiểm tra. Đây
là lợi ích về kiểm soát luồng dữ liệu trong một threat model hẹp, không chứng nhận
an toàn tổng quát hoặc trí thông minh nổi lên.

## K.2. Bài học về triển khai và tính tái lập

Một checkpoint chỉ có ý nghĩa khi được ghép với đúng preprocessing, thứ tự feature,
nhãn và metadata. API/UI đã liên kết chúng để chạy cùng input và chỉ ra backend/device
thực tế. CPU portable giúp demo không cần GPU, nhưng số đo này không đại diện cho
TensorFlow hoặc PyTorch native. Kết quả lịch sử, demo mới và trạng thái cloud được
tách riêng để tránh một ảnh giao diện bị hiểu thành bằng chứng chất lượng khoa học.

Trường hợp thiếu telemetry và lỗi schema cho thấy tính tái lập còn bao gồm cách giữ
lại thất bại. Dữ liệu đã forward không bị chạy lại chỉ để sửa một file hoàn tất;
chi phí chưa đo không được thay bằng0; mẫu số chất lượng và mẫu số chi phí có thể
khác nhau. Một bản báo cáo đáng kiểm tra cần nêu rõ các trường hợp đó bên cạnh kết
quả thuận lợi, thay vì chỉ giữ bảng cuối trông đồng đều.

## K.3. Hạn chế và hướng phát triển

Đề tài dùng một số kiến trúc nhỏ và ngân sách cố định nhằm so sánh cơ chế. Chưa có
bằng chứng rằng đây là lựa chọn tốt nhất cho từng miền, chưa có kiểm định trên dữ
liệu ngoài snapshot và không có nghiên cứu tác động với người dùng thực. Độ ổn định
ba seed không thay thế một chiến dịch tái lập trên nhiều split và phần cứng.

Hướng tiếp theo có thể là mô hình ảnh pretrained có protocol độc lập, chuỗi có vintage
đúng thời điểm công bố, dữ liệu bổ sung từ nhiều hộ gia đình và đánh giá chuyển miền.
Với KG–RAG, có thể nghiên cứu embedding mạnh hơn hoặc bộ thực thi chương trình số;
với tác tử, cần benchmark câu hỏi đa dạng và threat model rộng hơn. Mỗi thay đổi phải
khai báo tập development và TEST mới, không dùng các TEST đã xem để điều chỉnh rồi
tuyên bố cải thiện trên cùng bộ đo.

Về phần mềm, triển khai cloud cần kiểm tra lại dependency CPU trong môi trường mới,
URL API HTTPS, CORS, bộ nhớ và giới hạn job thực tế. Thành công local chưa phải SLA
hay chứng nhận phù hợp gói dịch vụ. Hướng phát triển này giữ nguyên mục tiêu học
tập của tiểu luận: hiểu đúng mô hình, đo đúng phạm vi và có thể giải thích kết quả.
