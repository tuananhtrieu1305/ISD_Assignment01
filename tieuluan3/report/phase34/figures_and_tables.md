# DANH MỤC HÌNH VÀ BẢNG

Số trang được tạo sau phân trang DOCX, không ước đoán tại bước tích hợp.

## Hình

Hình 1.1. Timeline các mốc phát triển chính của AI
Hình 2.1. Chất lượng trên full TEST; error bar là độ lệch chuẩn giữa seed, không phải khoảng tin cậy theo dân số.
Hình 2.2. Loss train/validation seed 42. Train loss là trung bình trong lúc trọng số thay đổi; validation tính sau epoch, nên không cần bằng nhau ngay cả khi dùng cùng loss.
Hình 2.3. Reliability diagram từ prediction TEST đã lưu; bin rỗng không nối thành số 0. Class weighting làm mục tiêu học khác tần suất tự nhiên, nên phân biệt chất lượng phân lớp với hiệu chỉnh xác suất.
Hình 2.4. Confusion matrix seed 42, số đếm thật. Đọc false negative cùng recall lớp 1; accuracy cao không đồng nghĩa phát hiện tốt lớp thiểu số.
Hình 2.5. Giá thật và dự đoán của 440 nhà TEST. Điểm lệch xa đường chéo là ví dụ sai số lớn; không loại chúng khỏi metric.
Hình 3.1. Mẫu ảnh matched train IDRiD và nhãn nguồn; không phải kết quả chẩn đoán.
Hình 3.2. Mẫu ảnh matched train EuroSAT, nhãn lớp phủ đất.
Hình 3.3. Mẫu ảnh matched train CIFAR-10, nhãn vật thể.
Hình 3.4. Macro-F1 trên full TEST, matched train, ba seed. Thanh sai số là sample SD, không phải khoảng tin cậy.
Hình 3.5. Confusion matrix IDRiD, full TEST, seed42, matched train.
Hình 3.6. Confusion matrix EuroSAT, full TEST, seed42, matched train.
Hình 3.7. Confusion matrix CIFAR-10, full TEST, seed42, matched train.
Hình 3.8. Train wall mean trên ba seed; trục log, CPU/GPU và graph/eager được ghi riêng.
Hình 3.9. Train/validation loss theo epoch, seed42; đường dọc chỉ checkpoint được chọn bởi validation.
Hình 3.10. Độ nhạy logit trên ảnh TRAIN đầu tiên cố định, seed42; chuẩn hóa riêng mỗi ảnh.
Hình 4.1. TEST chung, sai số chính theo từng dataset; trục log, đơn vị riêng. Error bar là sample SD ba seed, đường baseline n=1.
Hình 4.2. TEST theo cả ba horizon, mean ± sample SD; tháng/quý/giờ theo dataset, không đồng nhất về thời lượng.
Hình 4.3. Ba expanding rolling VALIDATION; scaler riêng từng prefix. Đây là development, không phải ba lượt TEST hoặc ba mẫu độc lập.
Hình 4.4. Nhãn thật và dự đoán TEST đã lưu, một chuỗi/dataset; không phát sinh inference TEST để vẽ.
Hình 4.5. BIS TEST: RMSE từng nền kinh tế, trung bình ba seed, màu log10 cùng thang cho sáu cách triển khai.
Hình 4.6. Validation MSE chuẩn hóa theo epoch, seed42 main; không so giá trị loss giữa dataset như cùng đơn vị vật lý.
Hình 4.7. Input/forget/output gates theo bước thời gian, ba tầng LSTM, chỉ dùng TRAIN.
Hình 4.8. Input-gradient RMS của4 TRAIN windows cố định; floor1e−30 chỉ để hiển thị log nếu bằng0, không dùng cho metric/parity.
Hình 4.9. Train wall chính, mean ± sample SD trên số seed có telemetry; n=2 được ghi riêng, không phải latency TEST.
Hình 5.1. Phân bố chính của ba nguồn dữ liệu trong snapshot đã khóa.
Hình 5.2. Tập con các cạnh phục vụ truy hồi trong schema property graph; không phải toàn bộ topology.
Hình 5.3. Chunk Recall@5 trên public TEST, báo riêng medical và finance.
Hình 5.4. Ablation của B4 trên VALIDATION theo miền.
Hình 5.5. Các nhãn lỗi/proxy của B4 trên hai miền public TEST.
Hình 5.6. p95 latency đọc nguyên artifact Phase15; không đo lại trên runtime mới.
Hình 5.7. Citation validity và gold precision lịch sử cho hai miền.
Hình 6.1. Luồng có giới hạn của A2; A0/A1 lược bớt vai trò theo định nghĩa.** Nguồn:
Hình 6.2. Task success TEST, mỗi loại4task/miền/variant.** Nguồn: saved outputs900row, không chạy lại predictor TEST.
Hình 6.3. p50/p95 từ20task mỗi miền/variant, gồm ca có tool và ca từ chối sớm.** Không
Hình 6.4. Hai loại tỷ lệ lỗi khác nhau trên challenge TEST.** Cột0 về unsafe chỉ nói
Hình 6.5. Một trace TEST đã lưu; mũi tên là thứ tự chuyển message, không chain-of-thought.

## Bảng

Bảng 1.1. Nguồn, kích cỡ và cấu trúc
Bảng 1.2. Mẫu input/output
Bảng 1.3. Phân bố và chất lượng dữ liệu
Bảng 1.4. Nguồn, kích cỡ và cấu trúc
Bảng 1.5. Mẫu input/output
Bảng 1.6. Phân bố và chất lượng dữ liệu
Bảng 1.7. Nguồn, kích cỡ và cấu trúc
Bảng 1.8. Mẫu input/output
Bảng 1.9. Phân bố và chất lượng dữ liệu
Bảng 2.1. Hợp các hàm và vai trò từng hàm
Bảng 2.2. Ba bộ dữ liệu
Bảng 2.3. CDC Diabetes
Bảng 2.4. Ames Housing
Bảng 2.5. Bank Marketing
Bảng 2.6. Thời gian, bộ nhớ và kích thước
Bảng 2.7. Thời gian, bộ nhớ và kích thước
Bảng 2.8. Xác suất, sai số và phân tích nhóm
Bảng 2.9. Kiểm chứng mã và hợp đồng mô hình
Bảng 2.10. ch2_cdc_diabetes
Bảng 2.11. ch2_ames_housing
Bảng 2.12. ch2_bank_marketing
Bảng 3.1. Bảy lớp học được
Bảng 3.2. Hợp hàm: đầu ra bước trước là đầu vào bước sau
Bảng 3.3. Ba nguồn ảnh và kích cỡ
Bảng 3.4. Kết quả thực nghiệm
Bảng 3.5. IDRiD
Bảng 3.6. EuroSAT
Bảng 3.7. CIFAR-10
Bảng 3.8. Thời gian, bộ nhớ và checkpoint
Bảng 3.9. Thời gian, bộ nhớ và checkpoint
Bảng 3.10. ch3_idrid
Bảng 3.11. ch3_eurosat
Bảng 3.12. ch3_cifar10
Bảng 4.1. Nguồn, kích cỡ và ý nghĩa đầu ra
Bảng 4.2. Mẫu input/output thật và phân bố
Bảng 4.3. Mẫu input/output thật và phân bố
Bảng 4.4. Causal windows, scaler và rolling validation
Bảng 4.5. Luồng tổng thể và bảng shape
Bảng 4.6. Các hàm cốt lõi và mapping sang code
Bảng 4.7. Dữ liệu đầu vào và đầu ra
Bảng 4.8. Một bước LSTM: giữ, ghi và xuất
Bảng 4.9. Sáu lớp học được và hợp các hàm
Bảng 4.10. Ba implementation và các hàm huấn luyện
Bảng 4.11. Giao thức so sánh và ý nghĩa số đo
Bảng 4.12. Chất lượng trên TEST chung
Bảng 4.13. Chất lượng trên TEST chung
Bảng 4.14. Horizon dài và biến động giai đoạn
Bảng 4.15. Quá trình học, cổng và gradient
Bảng 4.16. Chi phí, sai lệch đo và giới hạn
Bảng 4.17. ch4_gold_pink_sheet
Bảng 4.18. ch4_bis_house_prices
Bảng 4.19. ch4_household_power
Bảng 5.1. Dữ liệu, giấy phép và phạm vi sử dụng
Bảng 5.2. Schema, provenance và hai đồ thị miền
Bảng 5.3. Ingestion, chunking và lập chỉ mục
Bảng 5.4. Protocol và metric
Bảng 5.5. Phân tích lỗi, provenance và giới hạn sử dụng
Bảng 5.6. Hợp các hàm và contract dùng chung
Bảng 5.7. ch5_medquad_diabetes
Bảng 5.8. ch5_finqa
Bảng 5.9. ch5_wikidata_subgraphs
Bảng 6.1. Nguồn và kích cỡ
Bảng 6.2. Giải thích từng hàm
Bảng 6.3. Kết quả TEST tác tử
Bảng 6.4. ch6_diabetes_tasks
Bảng 6.5. ch6_house_tasks
Bảng 6.6. ch6_gold_tasks
Bảng A.1. Nguồn, kích cỡ và cấu trúc
Bảng A.2. Mẫu input/output
Bảng A.3. Phân bố và chất lượng dữ liệu
Bảng A.4. Nguồn, kích cỡ và cấu trúc
Bảng A.5. Mẫu input/output
Bảng A.6. Phân bố và chất lượng dữ liệu
Bảng A.7. Nguồn, kích cỡ và cấu trúc
Bảng A.8. Mẫu input/output
Bảng A.9. Phân bố và chất lượng dữ liệu
Bảng A.10. Nguồn, kích cỡ và cấu trúc
Bảng A.11. Mẫu input/output
Bảng A.12. Phân bố và chất lượng dữ liệu
Bảng A.13. Nguồn, kích cỡ và cấu trúc
Bảng A.14. Mẫu input/output
Bảng A.15. Phân bố và chất lượng dữ liệu
Bảng A.16. Nguồn, kích cỡ và cấu trúc
Bảng A.17. Mẫu input/output
Bảng A.18. Phân bố và chất lượng dữ liệu
Bảng A.19. Nguồn, kích cỡ và cấu trúc
Bảng A.20. Mẫu input/output
Bảng A.21. Phân bố và chất lượng dữ liệu
Bảng A.22. Nguồn, kích cỡ và cấu trúc
Bảng A.23. Mẫu input/output
Bảng A.24. Phân bố và chất lượng dữ liệu
Bảng A.25. Nguồn, kích cỡ và cấu trúc
Bảng A.26. Mẫu input/output
Bảng A.27. Phân bố và chất lượng dữ liệu
Bảng A.28. Nguồn, kích cỡ và cấu trúc
Bảng A.29. Mẫu input/output
Bảng A.30. Phân bố và chất lượng dữ liệu
Bảng A.31. Nguồn, kích cỡ và cấu trúc
Bảng A.32. Mẫu input/output
Bảng A.33. Phân bố và chất lượng dữ liệu
Bảng A.34. Nguồn, kích cỡ và cấu trúc
Bảng A.35. Mẫu input/output
Bảng A.36. Phân bố và chất lượng dữ liệu
Bảng A.37. Nguồn, kích cỡ và cấu trúc
Bảng A.38. Mẫu input/output
Bảng A.39. Phân bố và chất lượng dữ liệu
Bảng A.40. Nguồn, kích cỡ và cấu trúc
Bảng A.41. Mẫu input/output
Bảng A.42. Phân bố và chất lượng dữ liệu
Bảng A.43. Nguồn, kích cỡ và cấu trúc
Bảng A.44. Mẫu input/output
Bảng A.45. Phân bố và chất lượng dữ liệu
Bảng A.46. A.16. ch6_diabetes_tasks
Bảng A.47. A.16. ch6_diabetes_tasks
Bảng A.48. A.17. ch6_house_tasks
Bảng A.49. A.17. ch6_house_tasks
Bảng A.50. A.18. ch6_gold_tasks
Bảng A.51. A.18. ch6_gold_tasks
Bảng B.1. B.1. ch2_cdc_diabetes / mlp
Bảng B.2. B.1. ch2_cdc_diabetes / mlp
Bảng B.3. B.2. ch2_ames_housing / mlp
Bảng B.4. B.2. ch2_ames_housing / mlp
Bảng B.5. B.3. ch2_bank_marketing / mlp
Bảng B.6. B.3. ch2_bank_marketing / mlp
Bảng B.7. B.4. ch3_idrid / cnn
Bảng B.8. B.4. ch3_idrid / cnn
Bảng B.9. B.5. ch3_eurosat / cnn
Bảng B.10. B.5. ch3_eurosat / cnn
Bảng B.11. B.6. ch3_cifar10 / cnn
Bảng B.12. B.6. ch3_cifar10 / cnn
Bảng B.13. B.7. ch4_gold_pink_sheet / rnn
Bảng B.14. B.7. ch4_gold_pink_sheet / rnn
Bảng B.15. B.8. ch4_gold_pink_sheet / lstm
Bảng B.16. B.8. ch4_gold_pink_sheet / lstm
Bảng B.17. B.9. ch4_bis_house_prices / rnn
Bảng B.18. B.9. ch4_bis_house_prices / rnn
Bảng B.19. B.10. ch4_bis_house_prices / lstm
Bảng B.20. B.10. ch4_bis_house_prices / lstm
Bảng B.21. B.11. ch4_household_power / rnn
Bảng B.22. B.11. ch4_household_power / rnn
Bảng B.23. B.12. ch4_household_power / lstm
Bảng B.24. B.12. ch4_household_power / lstm
Bảng B.25. B.13. Đối chiếu tất cả implementation
