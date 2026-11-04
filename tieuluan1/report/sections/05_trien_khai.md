<!-- page_target: 3-4; style: term_paper/config/style_spec.md -->

# PHẦN 5. TRIỂN KHAI MÔ HÌNH

Phần này chuyển các artifact đã đánh giá ở Chương 2–4 thành một ứng dụng inference chạy cục bộ. Mục tiêu không phải tạo một sản phẩm y tế, viễn thám hay tài chính hoàn chỉnh, mà chứng minh toàn bộ đường đi từ input đến output có thể tái lập ngoài notebook. Ứng dụng gồm ba khu vực tương ứng với dữ liệu bảng, ảnh và chuỗi; sử dụng bốn model NumPy seed 42 đã khóa. Việc chọn model NumPy giúp triển khai nhẹ, đồng thời giữ liên hệ trực tiếp với phần cài đặt từ đầu của tiểu luận. Keras và PyTorch vẫn là đối tượng so sánh thực nghiệm, không cần được nạp đồng thời vào tiến trình phục vụ.

## 5.1. Kiến trúc ứng dụng và provenance

### 5.1.1. Luồng input → validate → preprocess → model → response

Ứng dụng dùng kiến trúc ba lớp nhỏ. Giao diện HTML/CSS/JavaScript thu nhận input và gửi JSON đến HTTP server cục bộ. Lớp schema kiểm tra kiểu dữ liệu, tập trường cho phép, miền giá trị, kích thước ảnh và shape chuỗi. Chỉ khi validation đạt, `ModelService` mới gọi đúng preprocessor và model. Response chứa dự đoán, thông tin diễn giải tối thiểu, cảnh báo sử dụng và provenance. Server không ghi payload vào log và không lưu input xuống đĩa.

Đường đi chung có thể biểu diễn là `input → allow-list validation → preprocessing đã fit trên TRAIN → model inference → postprocessing → JSON/UI`. Diabetes nhận đúng 21 trường; EuroSAT giải mã PNG/JPEG và đưa về RGB 64 × 64; Customer nhận ma trận 8 × 5; AAPL nhận 30 × 5 theo thứ tự Open, High, Low, Close, Volume. Với AAPL, bước postprocessing inverse-transform output về USD rồi tính thêm naive last-Close từ dòng cuối input. Validation diễn ra ở server, do đó không thể bỏ qua bằng cách gửi request trực tiếp thay vì dùng form.

Không cài thêm web framework vào môi trường assignment. Streamlit, FastAPI và Flask đều không có sẵn khi kiểm tra Phase 6; server vì vậy được xây bằng `ThreadingHTTPServer` trong thư viện chuẩn. Lựa chọn này giảm dependency vận hành nhưng vẫn cung cấp endpoint, status code và security header rõ ràng. Phần tính toán chỉ cần NumPy, pandas, scikit-learn, joblib và Pillow—các dependency đã có trong pipeline artifact và được ghim phiên bản cho Docker.

### 5.1.2. Model/preprocessor version và SHA-256

`model_registry.json` định danh bốn bundle: `ch2-numpy-seed42`, `ch3-numpy-seed42`, `ch4-customer-numpy-seed42` và `ch4-aapl-numpy-seed42`. Mỗi bundle ghi đường dẫn model, SHA-256 model, SHA-256 của một hoặc nhiều preprocessor và decision threshold nếu là classification. Khi khởi động, service đọc từng file, tự tính SHA-256 và dừng ngay nếu file thiếu hoặc hash không khớp. Vì vậy, giao diện không thể âm thầm dùng một checkpoint đã bị thay đổi.

Endpoint `/health` trả trạng thái chung, version service và cờ `hash_verified` cho từng model. Endpoint `/api/models` cung cấp registry để UI hiển thị version cùng 12 ký tự đầu của hash. Provenance cũng được lặp lại trong mỗi response dự đoán, giúp ảnh chụp hoặc JSON kết quả vẫn xác định được model ngay cả khi tách khỏi phiên chạy. Cơ chế này không chứng minh model đúng về mặt nghiệp vụ; nó chứng minh artifact đang phục vụ đúng artifact đã được đánh giá. Hình 5.1 cho thấy health indicator, ba tab và model registry trong cùng giao diện.

![Giao diện tổng quan của ứng dụng inference tích hợp](../assets/deployment/phase6_overview.png)

**Hình 5.1.** Giao diện tổng quan với health indicator, ba use case và model registry đã xác minh hash. Nguồn: ảnh chụp ứng dụng Phase 6.

## 5.2. Use case ML: diabetes risk

### 5.2.1. Form nhập liệu, output và cảnh báo y khoa

Tab ML cơ bản dùng MLP NumPy của bài toán Diabetes Binary. Form biểu diễn đủ 21 health indicators và buộc người dùng nhập mọi trường. Các biến nhị phân chỉ nhận 0 hoặc 1; BMI nằm trong 10–100; `GenHlth`, `Age`, `Education` và `Income` theo đúng miền mã hóa của dataset; số ngày sức khỏe thể chất/tinh thần nằm trong 0–30. Server từ chối trường thừa, nhờ đó các giá trị như tên bệnh nhân hoặc ghi chú riêng tư không bị truyền nhầm vào pipeline.

Sau validation, input được đặt theo đúng thứ tự feature, chuyển qua `ColumnTransformer`/`StandardScaler` đã fit trên TRAIN, rồi đưa vào MLP. UI hiển thị xác suất và threshold 0,37 thay vì chỉ trả nhãn 0/1. Cách này làm rõ rằng class là quyết định từ một điểm cắt, không phải một kết luận chắc chắn. Response luôn kèm câu “Kết quả học thuật, không phải chẩn đoán y khoa” và khuyến nghị tham khảo chuyên gia y tế. Model chỉ học quan hệ thống kê từ bộ dữ liệu quan sát; nó không dùng hồ sơ lâm sàng đầy đủ, không được hiệu chuẩn cho dân số Việt Nam và chưa qua quy trình kiểm định thiết bị y tế.

## 5.3. Use case CNN: EuroSAT

### 5.3.1. Upload ảnh, top classes và confidence

Tab CNN nhận ảnh PNG/JPEG tối đa 5 MB. Pillow xác minh định dạng và nội dung ảnh trước khi decode đầy đủ; giới hạn pixel ngăn ảnh nén có kích thước giải nén bất thường. Ảnh hợp lệ được chuyển RGB, resize song tuyến tính về 64 × 64 và chuẩn hóa về [0,1], giống pipeline EuroSAT. Các loại file khác hoặc chuỗi base64 lỗi nhận HTTP 400 với thông báo thân thiện.

Thay vì chỉ hiện class thắng, UI xếp hạng ba lớp cùng confidence. Đây là cách trình bày phù hợp hơn khi hai loại sử dụng đất có tín hiệu gần nhau. Confidence là output softmax, không phải xác suất đã calibration theo điều kiện địa lý mới. Model học từ EuroSAT và chưa được kiểm chứng trên ảnh có độ phân giải, sensor, mùa vụ hay miền địa lý khác. Cảnh báo trên response vì thế xác định đây là phân loại minh họa, không thay thế phân tích viễn thám chuyên nghiệp.

## 5.4. Use case RNN: customer/AAPL

### 5.4.1. Sequence input, RNN output, baseline và cảnh báo tài chính

Tab RNN có hai chế độ dùng chung một trình nhập CSV. Customer yêu cầu đúng tám hàng, mỗi hàng gồm năm feature tuần; bốn feature giao dịch không âm và `active_flag` chỉ nhận 0/1. Output gồm xác suất hoạt động ở tuần kế tiếp, class tại threshold 0,655 và cảnh báo rằng pattern lịch sử không bảo đảm hành vi tương lai. Input không chứa customer ID; sample key chỉ xuất hiện ở demo để truy vết.

AAPL yêu cầu đúng 30 hàng OHLCV. Mỗi hàng phải thỏa `Low ≤ Open/Close ≤ High`, giá dương và volume không âm. Sau khi RNN dự đoán trên scale huấn luyện, output được inverse-transform về USD. Giao diện bắt buộc đặt kết quả RNN cạnh naive last-Close, kèm chênh lệch. Điều này bảo toàn kết luận âm ở Chương 4: trên TEST đã khóa, cả chín RNN run đều kém baseline đơn giản. Hình 5.2 minh họa cách hai output được đặt cạnh nhau; không được chỉ trình diễn một giá dự đoán RNN rồi tạo ấn tượng rằng mô hình là công cụ giao dịch hữu hiệu.

![Kết quả AAPL hiển thị RNN và naive baseline](../assets/deployment/phase6_aapl_result.png)

**Hình 5.2.** Kết quả demo AAPL hiển thị đồng thời RNN, naive last-Close, chênh lệch và cảnh báo tài chính. Nguồn: ảnh chụp ứng dụng Phase 6.

Cảnh báo “không phải khuyến nghị đầu tư” luôn nằm trong response server và khu vực kết quả. Dữ liệu chỉ gồm một ticker và năm biến lịch sử; không có tin tức, sự kiện doanh nghiệp, lãi suất hay risk profile của người dùng. Việc triển khai chứng minh inference kỹ thuật, không mở rộng phạm vi kết luận của thực nghiệm.

## 5.5. Kiểm thử và tái lập

### 5.5.1. Health check, invalid input và smoke tests

Bộ test Phase 6 kiểm tra ba tầng. Nhóm schema thử cả input hợp lệ và các trường hợp thiếu/thừa trường, `NaN`, miền sai, sequence sai shape, OHLC bất nhất và nội dung giả ảnh. Nhóm service nạp bốn artifact, chạy mẫu TEST đã khóa và đối chiếu output với prediction CSV: classification/probability dùng tolerance `1e-6`; AAPL sau inverse scaling dùng `1e-4`. Nhóm HTTP khởi động server trên cổng tạm, gọi health, tải static UI, chạy luồng demo → prediction, kiểm tra lỗi 400/404 và các security header.

Mỗi response thành công có `request_id` ngẫu nhiên để nối lỗi vận hành mà không log payload. Lỗi validation trả mã `invalid_input`; exception nội bộ chỉ trả thông báo tổng quát, không lộ stack trace hay đường dẫn máy. Request JSON bị giới hạn 7 MB và rate limiter in-memory giới hạn theo IP. CSP chỉ cho phép tài nguyên cùng origin và ảnh `data:`; server thêm `nosniff`, cấm iframe, tắt referrer và quyền camera/microphone/geolocation.

### 5.5.2. Chạy local, Docker và trạng thái cloud

Ứng dụng chạy từ workspace bằng module `term_paper.deployment.app.server`, mặc định bind `127.0.0.1:8000`. `requirements.txt` ghim năm package trực tiếp. Dockerfile dùng Python 3.12 slim, cài dependency không cache, chỉ copy source/artifact cần thiết, chuyển sang non-root user và khai báo health check. Build phải chạy từ workspace root để các đường `term_paper/`, `A05/` và `A06/` có trong context. README triển khai cung cấp lệnh local, Docker, health check và test.

Public cloud được ghi `OPTIONAL_PENDING_CREDENTIALS`, không phải blocker. Ứng dụng chưa có authentication, TLS, persistent audit store hay autoscaling; expose trực tiếp ra Internet sẽ vượt thiết kế. Localhost và container tái lập là phạm vi hoàn thành của tiểu luận.

## 5.6. Hạn chế khi triển khai

Deployment không biến benchmark thành sản phẩm production. Thứ nhất, model chỉ đại diện seed 42, trong khi chương thực nghiệm dùng nhiều seed để đo variation. Thứ hai, server load toàn bộ model vào một process; rate limit chỉ lưu trong RAM và không phối hợp giữa replica. Thứ ba, resize ảnh và input form chưa có giải thích feature thân thiện cho người dùng không chuyên. Thứ tư, joblib dựa trên pickle nên chỉ được load artifact tin cậy; hệ thống chủ động không cung cấp upload model.

Giám sát hiện dừng ở health và request ID, chưa đo drift, calibration, latency percentile hay tỷ lệ lỗi dài hạn. Nếu phát triển tiếp, cần bổ sung authentication, reverse proxy TLS, structured metrics không chứa dữ liệu nhạy cảm, versioned rollout, rollback, model card, đánh giá fairness và kiểm thử trên dữ liệu ngoài miền. Với y tế và tài chính, còn cần quy trình chuyên gia, quản trị rủi ro và yêu cầu pháp lý tương ứng.

Trong phạm vi bài học, kết quả quan trọng là chuỗi bằng chứng đã khép kín: model và preprocessor có hash; schema đúng với training pipeline; bốn output demo khớp artifact; lỗi input bị từ chối; cảnh báo miền nhạy cảm không bị ẩn; và quy trình local/Docker có thể chạy lại. Deployment vì vậy là lớp trình bày và kiểm chứng inference, không phải lời khẳng định model đã sẵn sàng cho quyết định thực tế.
