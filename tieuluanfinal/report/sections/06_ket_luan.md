<!-- page_target: 2; style: term_paper/config/style_spec.md -->

# KẾT LUẬN

## K.1. Kết quả đạt được

Tiểu luận đã hoàn thành một chuỗi công việc thống nhất từ lịch sử, nền tảng thuật toán, dữ liệu, cài đặt, thực nghiệm, biểu diễn tri thức đến triển khai. Chương 1 đặt ML, CNN, RNN và RAG trong tiến trình dài hơn của AI: tiến bộ không chỉ đến từ một kiến trúc, mà từ sự kết hợp giữa biểu diễn, dữ liệu, năng lực tính toán và protocol đánh giá. Chương 2–4 kiểm soát preprocessing TRAIN, lựa chọn trên VALIDATION và matched comparison. Chương 5 giữ cùng corpus/evaluator cho B0–B4, khóa cấu hình trước public TEST và lưu prediction, graph, index cùng manifest để tái tính metric.

Phạm vi thực nghiệm gồm tám dataset instance và 63 lượt huấn luyện matched: 27 lượt MLP ở Chương 2, 18 lượt CNN ở Chương 3 và 18 lượt RNN ở Chương 4. Ba implementation scratch đều thực hiện phần học cốt lõi mà không dựa vào autograd: MLP có forward/backpropagation/Adam; CNN có convolution, pooling, backward và update; RNN có forward nhiều bước, Backpropagation Through Time, clipping và Adam. Keras và PyTorch biểu diễn topology logic tương ứng. Parameter count, sample key, target, split hash và preprocessor hash được đối chiếu trong từng track. Tổng cộng 287.253 dòng dự đoán TEST được lưu từ matched experiments, bên cạnh model, lịch sử loss và metadata.

Chương 5 bổ sung ba nguồn MedQuAD, FinQA và Wikidata. Property graph medical có 1.336 đỉnh/1.506 cạnh; graph finance có 99.355 đỉnh/97.809 cạnh, đều đạt provenance 100% và không chứa gold-derived retrieval edge. Public TEST gồm 62 câu medical và 1.147 câu finance, chạy đúng một lần theo cấu hình khóa. B4 đạt Recall@5 0,581 ở medical và 0,480 ở finance; mức tăng so với B2 lần lượt là 0,177 và 0,037, nhưng B4 finance vẫn thấp hơn BM25 B0 = 0,532. Citation validity 1,000 không được đồng nhất với answer correctness; exact match/execution FinQA gần 0 cho thấy lớp trả lời chưa giải được suy luận số.

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
| KG-RAG — MedQuAD diabetes | Chunk Recall@5 TEST | B4 = 0,581; B2 = 0,403; chênh +0,177, CI 95% [0,096; 0,274] | Không chứng minh khả năng chẩn đoán hoặc độ đúng lâm sàng |
| KG-RAG — FinQA | Chunk Recall@5 TEST | B4 = 0,480 > B2 = 0,443 nhưng < BM25 B0 = 0,532 | Không chứng minh đã giải numerical reasoning hoặc vượt mọi baseline |

*Nguồn bảng: metric summary Chương 2–4 và `phase15_test_metrics.json`, `phase15_bootstrap_ci.csv`; matched values Chương 2–4 dùng TEST seed 42/52/62, KG-RAG dùng public TEST one-shot.*

Deployment được phân bổ vào cuối Chương 2–5. Diabetes nhận 21 health indicator; EuroSAT nhận PNG/JPEG và trả top-3; Customer nhận chuỗi 8 × 5; AAPL nhận 30 × 5 và luôn hiện RNN cạnh naive last-Close. Agent KG-RAG chỉ cho phép hai retriever, trả citation/evidence/graph trace và từ chối prompt injection hoặc câu ngoài miền. Service xác minh SHA-256, từ chối input sai schema và không cần API key. Đây là bằng chứng artifact có thể tái sử dụng nhất quán, không phải chứng nhận hệ thống production.

## K.2. Trả lời câu hỏi nghiên cứu

**RQ1 — Ba implementation khác nhau ở mức nào khi protocol được giữ cố định?** Kết quả không hỗ trợ một thứ hạng framework chung. Ở diabetes MLP, F1 trung bình gần như trùng nhau; ở CDC Conv1D, macro-F1 chỉ cách nhau 0,0079 giữa giá trị cao nhất và thấp nhất. Ngược lại, EuroSAT và customer cho thấy chênh lệch rõ hơn cùng variation qua seed. PyTorch RNN đạt mean F1 customer cao hơn Keras và NumPy, nhưng điều này không chứng minh API PyTorch tạo mô hình tốt hơn ngoài topology, dữ liệu và budget hiện tại. Initialization, dtype, kernel, shuffle và quỹ đạo tối ưu vẫn khác. Kết luận của RQ1 là matched protocol làm so sánh có ý nghĩa và loại nhiều nguyên nhân sai, nhưng không buộc ba framework hội tụ về cùng trọng số hoặc metric.

**RQ2 — Mức độ phù hợp giữa kiến trúc và cấu trúc dữ liệu thể hiện ra sao?** MLP hoạt động hợp lý trên vector tabular nhưng không luôn vượt baseline cổ điển: churn là phản ví dụ trực tiếp. Conv2D khai thác locality và weight sharing tự nhiên trên ảnh, song data/capacity budget quyết định mạnh; matched EuroSAT 500 TRAIN ảnh thấp hơn nhiều A05 Basic full-data. Conv1D trên 21 cột CDC có giả định locality phụ thuộc thứ tự CSV, vì vậy kết quả không đủ để khẳng định convolution phù hợp dữ liệu bảng. RNN biểu diễn đúng thứ tự customer-week và OHLCV, nhưng recurrent state không bảo đảm dự báo tốt. AAPL cho thấy một mô hình có loss giảm và kiến trúc phù hợp hình thức vẫn có thể thất bại trước baseline khi target level bị distribution shift. Kiến trúc cung cấp inductive bias, không thay thế kiểm tra baseline, data regime và metric.

**RQ3 — Làm thế nào chuyển artifact thành inference có thể kiểm thử mà không làm mất provenance?** Bundle dự đoán gồm model, preprocessor, schema, threshold/baseline, version và SHA-256. Bundle KG-RAG gồm corpus, BM25/LSA index, graph anchor, locked-config hash và citation validator. Luồng chung là validate → preprocess/route → inference hoặc retrieval → postprocess → response có provenance và cảnh báo. Service test đối chiếu prediction hoặc artifact hash; readiness thất bại nếu file bị thay đổi. Với AAPL, naive baseline là bắt buộc; với KG-RAG, citation chỉ được phát từ retrieved ID và câu không đủ bằng chứng phải từ chối.

**RQ4 — Knowledge Graph thay đổi RAG như thế nào?** Trên medical, B4 tăng Recall@5 từ 0,403 của B2 lên 0,581; ablation VALIDATION giảm từ 0,667 xuống 0,364 khi bỏ graph. Trên finance, B4 tăng nhẹ so với B2 nhưng vẫn dưới BM25; graph-only chỉ đạt 0,034 do anchor/entity coverage thấp. Dense branch còn làm giảm finance validation trong cấu hình hiện tại. Do B4 thay cả fusion weight, hiệu ứng TEST B4–B2 thuộc toàn bộ cấu hình hybrid, không thể quy hết cho graph. Challenge 16/16 và citation validity 1,000 xác nhận contract trên bộ kiểm tra hữu hạn, không chứng minh loại bỏ hallucination.

## K.3. Hạn chế và hướng phát triển

Giới hạn đầu tiên nằm ở dữ liệu. Diabetes dựa trên health indicators tự báo cáo; housing là giá rao bán; e-commerce churn là synthetic; customer windows từ cùng khách hàng có tương quan; AAPL chỉ là một ticker và một giai đoạn; EuroSAT không có geographic holdout; Oxford có protocol ngắn. MedQuAD diabetes chỉ có 247 tài liệu sau lọc và filter còn false negative; FinQA official split còn overlap company-year key; Wikidata chỉ có 10 entity. Benchmark subset và snapshot hẹp giúp chạy trong giới hạn phần cứng nhưng thu hẹp phạm vi suy diễn.

Giới hạn thứ hai nằm ở search và metric. Mỗi track chỉ thử một không gian learning rate nhỏ, topology cố định và early stopping rule định trước. Classification probability chưa được calibration độc lập. F1 mặc định coi precision và recall quan trọng tương đương dù chi phí nghiệp vụ có thể khác. Timing đo trên một máy CPU và phụ thuộc warm-up, backend cùng tải nền. AAPL dự đoán price level làm persistence baseline đặc biệt mạnh; thí nghiệm chưa khảo sát return/difference target hoặc rolling-origin evaluation. Kết quả âm không chỉ ra duy nhất một nguyên nhân, vì nhiều yếu tố thay đổi cùng data regime.

Hướng phát triển nên được đăng ký trước khi mở TEST mới. Với dữ liệu bảng, cần calibration, subgroup và external/temporal holdout. Với EuroSAT/Oxford, cần geographic split, augmentation và pretrained baseline. Với customer/AAPL, cần cost matrix, cohort mới, return target và rolling-origin evaluation. Với KG-RAG, cần mở rộng entity snapshot có audit, đánh giá reranker, dùng report-level split bổ sung và xây program generator/calculator deterministic cho FinQA; mọi cấu hình mới phải dùng VALIDATION hoặc TEST mới, không tối ưu tiếp trên public TEST đã mở.

Ứng dụng còn thiếu authentication, TLS, shared rate limiting, monitoring drift, canary/rollback và đánh giá tác động thực địa. KG-RAG còn thiếu mô hình sinh được đánh giá độc lập, calculator an toàn và red-team rộng. Các tính năng đó là điều kiện để tiến gần production nhưng không thay thế thẩm định y khoa hoặc quản trị rủi ro tài chính. Kết luận cuối cùng không phải “deep learning/KG-RAG luôn tốt hơn”, mà là: kết quả đáng tin cậy phải gắn mô hình với dữ liệu phù hợp, baseline đủ mạnh, phép so sánh được kiểm soát, artifact truy vết được và giới hạn sử dụng được nói rõ.
