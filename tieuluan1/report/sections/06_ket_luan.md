<!-- page_target: 2; style: term_paper/config/style_spec.md -->

# KẾT LUẬN

## K.1. Kết quả đạt được

Tiểu luận đã hoàn thành một chuỗi công việc thống nhất từ lịch sử, nền tảng thuật toán, dữ liệu, cài đặt, thực nghiệm đến triển khai. Chương 1 đặt ML, CNN và RNN trong tiến trình dài hơn của AI: tiến bộ không chỉ đến từ một kiến trúc, mà từ sự kết hợp giữa biểu diễn, dữ liệu, năng lực tính toán, thuật toán tối ưu và protocol đánh giá. Ba chương thực nghiệm chuyển bài học đó thành ràng buộc kỹ thuật: preprocessing chỉ fit trên TRAIN; VALIDATION dùng để chọn learning rate, threshold và checkpoint; TEST chỉ dùng sau khi cấu hình đã khóa; mọi metric chính có prediction artifact để tái tính.

Phạm vi thực nghiệm gồm tám dataset instance và 63 lượt huấn luyện matched: 27 lượt MLP ở Chương 2, 18 lượt CNN ở Chương 3 và 18 lượt RNN ở Chương 4. Ba implementation scratch đều thực hiện phần học cốt lõi mà không dựa vào autograd: MLP có forward/backpropagation/Adam; CNN có convolution, pooling, backward và update; RNN có forward nhiều bước, Backpropagation Through Time, clipping và Adam. Keras và PyTorch biểu diễn topology logic tương ứng. Parameter count, sample key, target, split hash và preprocessor hash được đối chiếu trong từng track. Tổng cộng 287.253 dòng dự đoán TEST được lưu từ matched experiments, bên cạnh model, lịch sử loss và metadata.

Kết quả chính được tóm tắt trong Bảng K.1. Bảng không chọn riêng run đẹp nhất: các giá trị matched là mean qua seed 42, 52 và 62, còn baseline được ghi đúng theo artifact nguồn. Mỗi kết quả phải được đọc cùng quy mô dữ liệu và giới hạn protocol.

**Bảng K.1. Tổng hợp kết quả xuyên ba chương thực nghiệm**

| Chương/bài toán | Metric chính | Kết quả nổi bật trong protocol | Điều không được suy ra |
|---|---|---|---|
| MLP — Diabetes binary | F1 TEST, mean 3 seed | NumPy/Keras/PyTorch đều khoảng 0,7745–0,7746; cao hơn Random Forest nguồn 0,7602 trong contextual comparison | Không chứng minh khả năng chẩn đoán hoặc framework vượt trội |
| MLP — Housing | RMSE TEST, tỷ VND | PyTorch thấp nhất trong nhóm: 1,3990 ± 0,0033; baseline RF nguồn 1,4399 | Không đại diện giá giao dịch hay toàn thị trường Việt Nam |
| MLP — Churn | F1 TEST | NumPy cao nhất trong matched MLP: 0,3454 ± 0,0078; vẫn dưới logistic regression 0,3562 | MLP không mặc nhiên tốt hơn mô hình tuyến tính |
| CNN — EuroSAT matched | Macro-F1 TEST | Keras cao nhất trong nhóm: 0,2641 ± 0,0794 trên 500 TRAIN ảnh | Không so trực tiếp với A05 full-data Basic 0,7256 |
| CNN — CDC Conv1D | Macro-F1 TEST | PyTorch cao nhất trong nhóm: 0,4153 ± 0,0053; recall Prediabetes vẫn rất thấp | Không chứng minh adjacency cột tabular là cấu trúc tự nhiên |
| RNN — Customer-week | F1 TEST | PyTorch cao nhất trong nhóm: 0,3265 ± 0,0058; PR-AUC 0,2466 ± 0,0013 | Không bảo đảm hành vi mua tương lai hoặc hiệu quả chiến dịch |
| RNN — AAPL | RMSE TEST, USD | PyTorch RNN thấp nhất: 27,7904 ± 2,6129; naive last-Close chỉ 3,8789 | Không tạo cơ sở dự báo giao dịch hoặc khuyến nghị đầu tư |

*Nguồn bảng: `ch2_framework_summary.csv`, `ch2_best_vs_classical.csv`, `ch3_framework_summary.csv`, `ch3_a05_architecture_ablation.csv` và `ch4_framework_summary.csv`; matched values dùng TEST seed 42/52/62.*

Phần triển khai đưa bốn artifact NumPy seed 42 ra khỏi notebook. Diabetes nhận 21 health indicators; EuroSAT nhận PNG/JPEG và trả top-3; Customer nhận chuỗi 8 × 5; AAPL nhận 30 × 5 và luôn hiện RNN cạnh naive last-Close. Service xác minh SHA-256 khi khởi động, trả version trong response, từ chối input sai shape/type/domain và không log payload. Mười hai test Phase 6 đạt; core deployment có weighted line coverage 85,3%. Docker image chạy non-root, health check trả `ok` và xác minh đủ bốn bundle. Đây là bằng chứng rằng artifact có thể tái sử dụng nhất quán, không phải chứng nhận hệ thống production.

## K.2. Trả lời câu hỏi nghiên cứu

**RQ1 — Ba implementation khác nhau ở mức nào khi protocol được giữ cố định?** Kết quả không hỗ trợ một thứ hạng framework chung. Ở diabetes MLP, F1 trung bình gần như trùng nhau; ở CDC Conv1D, macro-F1 chỉ cách nhau 0,0079 giữa giá trị cao nhất và thấp nhất. Ngược lại, EuroSAT và customer cho thấy chênh lệch rõ hơn cùng variation qua seed. PyTorch RNN đạt mean F1 customer cao hơn Keras và NumPy, nhưng điều này không chứng minh API PyTorch tạo mô hình tốt hơn ngoài topology, dữ liệu và budget hiện tại. Initialization, dtype, kernel, shuffle và quỹ đạo tối ưu vẫn khác. Kết luận của RQ1 là matched protocol làm so sánh có ý nghĩa và loại nhiều nguyên nhân sai, nhưng không buộc ba framework hội tụ về cùng trọng số hoặc metric.

**RQ2 — Mức độ phù hợp giữa kiến trúc và cấu trúc dữ liệu thể hiện ra sao?** MLP hoạt động hợp lý trên vector tabular nhưng không luôn vượt baseline cổ điển: churn là phản ví dụ trực tiếp. Conv2D khai thác locality và weight sharing tự nhiên trên ảnh, song data/capacity budget quyết định mạnh; matched EuroSAT 500 TRAIN ảnh thấp hơn nhiều A05 Basic full-data. Conv1D trên 21 cột CDC có giả định locality phụ thuộc thứ tự CSV, vì vậy kết quả không đủ để khẳng định convolution phù hợp dữ liệu bảng. RNN biểu diễn đúng thứ tự customer-week và OHLCV, nhưng recurrent state không bảo đảm dự báo tốt. AAPL cho thấy một mô hình có loss giảm và kiến trúc phù hợp hình thức vẫn có thể thất bại trước baseline khi target level bị distribution shift. Kiến trúc cung cấp inductive bias, không thay thế kiểm tra baseline, data regime và metric.

**RQ3 — Làm thế nào chuyển artifact thành inference có thể kiểm thử mà không làm mất provenance?** Câu trả lời được hiện thực hóa bằng một bundle gồm model, preprocessor, schema, threshold/baseline, version và SHA-256. Luồng bắt buộc là validate → preprocess bằng object đã fit trên TRAIN → inference → inverse-transform/postprocess → response có provenance và cảnh báo. Demo input tạo response deterministic; service test đối chiếu trực tiếp với prediction CSV; HTTP smoke test kiểm tra cả success và invalid input; Docker đóng gói đúng phiên bản dependency. Với AAPL, baseline và cảnh báo là một phần của output contract, không phải chú thích tùy chọn. Nhờ đó deployment không được phép làm kết quả trông tốt hơn báo cáo.

## K.3. Hạn chế và hướng phát triển

Giới hạn đầu tiên nằm ở dữ liệu. Diabetes dựa trên health indicators tự báo cáo; housing là giá rao bán; e-commerce churn là synthetic; customer windows từ cùng khách hàng có tương quan; AAPL chỉ là một ticker và một giai đoạn; EuroSAT split theo ảnh không bảo đảm geographic holdout; Oxford có protocol ngắn và không transfer learning. Benchmark subset giúp scratch CNN/RNN chạy trong giới hạn phần cứng nhưng thu hẹp phạm vi suy diễn. Ba seed mô tả variation nội bộ, chưa đủ cho kiểm định thống kê rộng. Contextual comparison với baseline nguồn còn có khác biệt fit scope và vì vậy không được xem như controlled model replacement.

Giới hạn thứ hai nằm ở search và metric. Mỗi track chỉ thử một không gian learning rate nhỏ, topology cố định và early stopping rule định trước. Classification probability chưa được calibration độc lập. F1 mặc định coi precision và recall quan trọng tương đương dù chi phí nghiệp vụ có thể khác. Timing đo trên một máy CPU và phụ thuộc warm-up, backend cùng tải nền. AAPL dự đoán price level làm persistence baseline đặc biệt mạnh; thí nghiệm chưa khảo sát return/difference target hoặc rolling-origin evaluation. Kết quả âm không chỉ ra duy nhất một nguyên nhân, vì nhiều yếu tố thay đổi cùng data regime.

Hướng phát triển nên được đăng ký trước khi mở TEST mới. Với dữ liệu bảng, có thể bổ sung calibration, phân tích residual theo subgroup và external/temporal holdout. Với EuroSAT, geographic split, augmentation và transfer learning cần được so sánh dưới budget rõ ràng; với Oxford, pretrained representation là baseline cần thiết. Với customer, threshold nên xuất phát từ cost matrix và đánh giá thêm cohort khách hàng mới. Với AAPL, nên chuyển sang return, dùng rolling-origin evaluation, nhiều ticker/regime và vẫn giữ naive/risk-aware baseline; LSTM, GRU hoặc attention chỉ đáng thử nếu cùng protocol không làm mất baseline.

Ứng dụng triển khai còn thiếu authentication, TLS, shared rate limiting, monitoring drift, calibration monitoring, canary/rollback và đánh giá tác động thực địa. Các tính năng đó là điều kiện để tiến gần production, nhưng vẫn không thay thế thẩm định chuyên môn trong y tế hoặc quản trị rủi ro trong tài chính. Kết luận cuối cùng của tiểu luận vì vậy không phải “deep learning luôn tốt hơn”, mà là: một kết quả đáng tin cậy phải gắn mô hình với dữ liệu phù hợp, phép so sánh được kiểm soát, baseline đủ mạnh, artifact có thể truy vết và giới hạn sử dụng được nói rõ.
