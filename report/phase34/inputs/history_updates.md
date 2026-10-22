## 1.7. Ba benchmark minh họa lịch sử

Iris, MNIST và ImageNet đại diện cho ba cách đặt bài toán phân loại ở quy mô khác
nhau. Iris bắt đầu từ vài phép đo mô tả bông hoa; MNIST dùng ảnh chữ số đã chuẩn hóa;
ImageNet đưa đánh giá nhận dạng ảnh sang nhiều lớp và hình ảnh tự nhiên phức tạp hơn.
Chúng được dùng ở đây để hiểu vai trò của dữ liệu và benchmark, không tạo thêm một
cuộc thi mô hình trong chương lịch sử.

### 1.7.1. Iris và phân loại từ các phép đo

Một bông hoa được mô tả bằng chiều dài/rộng đài và cánh. Mỗi hàng đi kèm tên loài đã
ghi nhận. Luồng nhiệm vụ là **bốn phép đo → quy tắc hoặc mô hình phân loại → tên loài**.
Vì đầu vào ít chiều và nhãn rõ, người học có thể quan sát quan hệ giữa đặc trưng và
lớp trước khi dùng mô hình nhiều tham số. Bảng hồ sơ bên dưới trình bày ba input/output
nguồn, không phải dự đoán do tiểu luận tạo ra.

Iris phù hợp để học cách chia dữ liệu và đọc confusion matrix. Quy mô nhỏ và các lớp
cân bằng lại khiến nó không thể đại diện cho khó khăn của khảo sát sức khỏe mất cân
bằng hoặc dữ liệu có drift. Một thuật toán thành công trên Iris chưa được chứng minh
phù hợp với tiểu đường. Chương2 vì vậy dùng snapshot CDC cùng baseline và group audit.

### 1.7.2. MNIST và học biểu diễn từ điểm ảnh

Ảnh chữ số giữ cấu trúc hai chiều thay vì một vector mô tả hình học đã được người thu
thập chọn sẵn. Luồng nhiệm vụ là **ảnh xám → đặc trưng học được → xác suất chữ số**.
Các mẫu trong hồ sơ lấy official train; nhãn là chữ số nguồn. Không huấn luyện hoặc
đo accuracy MNIST trong tiểu luận này.

LeNet cho thấy mạng tích chập có thể kết hợp việc học đặc trưng với nhận dạng tài liệu
[@lecun1998document]. MNIST giúp nhiều phương pháp được so trên cùng dữ liệu, nhưng
ảnh nhỏ và đã chuẩn hóa khác ảnh đáy mắt độ phân giải cao hoặc ảnh vệ tinh nhiều kiểu
kết cấu. Việc chuyển sang ba dataset Chương3 là để quan sát những khác biệt đó, không
vì một kết quả MNIST đủ chứng minh năng lực nhận dạng ngoài thực tế.

### 1.7.3. ImageNet và giới hạn của metadata

ILSVRC2012 tổ chức bài toán phân loại ảnh với1.000 category công bố. AlexNet kết hợp
mạng tích chập, dữ liệu và tính toán GPU trong bối cảnh đánh giá này
[@krizhevsky2012imagenet; @russakovsky2015imagenet]. Mốc này nên được hiểu là một kết
quả nhận dạng trong protocol cụ thể, không phải thời điểm máy có mọi năng lực trí tuệ.

Snapshot local của tiểu luận chỉ gồm trang metadata chính thức. Không có ảnh ImageNet
local, nên không dựng ba ảnh mẫu, phân bố lớp hay metric huấn luyện giả. Ví dụ duy
nhất có thể đối chiếu là trang metadata và thông tin category công bố. Sự khác biệt
giữa kích cỡ công bố và số đã thu nhận phải được giữ rõ ngay trong hồ sơ dữ liệu.

### 1.7.4. Liên hệ với các chương thực nghiệm

Ba benchmark không tạo thành thang đo chung để xếp hạng mọi hệ AI. Số lớp, cách lấy
mẫu, dữ liệu đã chuẩn hóa và quyền truy cập đều khác nhau. Một pipeline đáng kiểm tra
cần giữ nguồn, định nghĩa nhãn và protocol trước khi đọc con số. Chương2–4 áp dụng
nguyên tắc ấy trên dữ liệu bảng, ảnh và chuỗi. Chương5 bổ sung nguồn bằng chứng còn
Chương6 kiểm quyền gọi công cụ và sự phối hợp. Dù hình thức thay đổi, câu hỏi vẫn là
hệ nhận thông tin nào, được phép làm gì và kết luận được đo trong điều kiện nào.
