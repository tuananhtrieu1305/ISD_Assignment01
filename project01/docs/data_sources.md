# Nguồn, dữ liệu và artifact sử dụng

## CDC diabetes

Nguồn [UCI dataset 891](https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators), DOI 10.24432/C53919; upstream [Diabetes Health Indicators trên Kaggle](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset). UCI ghi 253.680 mẫu và 21 feature; schema target của bản binary gộp prediabetes/diabetes. Một số mô tả tổng quát ở trang nguồn không nhất quán với schema binary; project lấy schema file và manifest đã khóa làm chuẩn.

Raw local 13.494.568 byte, SHA-256 `9f71fda9d4ae5f4878c99b9233b6a16accfa9a17c194116a6b78100540934964`. Vị trí canonical cụ thể trong `datasets/catalog.json`. Không sao chép raw, không mở lại TEST. Thống kê đọc từ EDA đã lưu: TRAIN 177.505 dòng, class0=152.760/class1=24.745; tập fit preprocessing matched TRAIN 20.000. Corpus raw có 25.772 dòng feature trùng theo EDA, không suy ra đã định danh bệnh nhân độc lập.

UCI chỉ dẫn điều khoản upstream; manifest cũ đã ghi bằng chứng Kaggle API CC0 Public Domain. Lần Phase 1 này xác nhận lại được trang UCI và chỉ dẫn upstream, chưa lấy lại được API license qua công cụ web; kế thừa provenance license đã lưu, không tự gán CC BY mặc định của UCI. Dùng citation nguồn dù upstream ghi CC0.

Checkpoint scratch/NumPy seed42: 40.022 byte; 21 input → Dense64/64/32/32/16/1, các activation giữa lớp, tổng 6 Dense. Mean/std và thứ tự feature giữ nguyên từ TRAIN. Target là nhãn khảo sát tự báo cáo lịch sử, class-weighted score không phải dự đoán xác suất mắc mới/đánh giá cá nhân đã hiệu chuẩn.

Ví dụ input trong `datasets/demo_profiles.json` là 3 mẫu matched TRAIN có nguồn rõ; không là bệnh nhân mới. Probe chỉ chạy 1 forward trên mẫu đầu, không dùng nhãn để chấm predictive accuracy.

## MedQuAD và KB/KG

Nguồn [MedQuAD](https://github.com/abachaa/MedQuAD/tree/577bd37b96c02d1833b2c9eed2de9f96964e96cb), [license CC BY 4.0](https://github.com/abachaa/MedQuAD/blob/master/LICENSE.txt). Nguồn tổng là 47.457 QA pair từ 12 website NIH; đó không phải kích cỡ subset đang dùng. Snapshot phục vụ project có **762 đoạn / 247 document**, tiếng Anh; không có QA split metadata/URL riêng từng document trong compact container.

Sparse index 142.342 byte; dense LSA 3.956.275 byte; hai index giữ cùng 762 ID. Container chunks 7.082.594 byte và graph 1.217.627 byte hiện chung medical/finance; probe chỉ giữ nội dung medical. Không deserialize finance indexes. Subset medical-only sẽ xuất ở Phase 2 có lineage/parity và license, không sửa container cũ.

Graph medical có **62 concept anchor**, cạnh anchor → chunk được kiểm không dangling. Đây là lexical support cho retrieval, không có đầy đủ quan hệ y khoa kiểu thuốc–liều–điều trị. Citation phải nêu source repository/commit và local document/chunk locator/hash; không dựng URL bệnh viện hoặc tuyên bố bản snapshot đã cập nhật hướng dẫn lâm sàng hôm nay.

Ví dụ corpus, độ dài nhỏ nhất/lớn nhất/trung bình và hash từng asset ở `datasets/catalog.json`, truy hồi probe hiển thị trong notebook01. Đoạn có thể bắt đầu/đứt giữa câu do chunking; Phase 2 phải tránh diễn giải thiếu ngữ cảnh và chấm support thực chất. Tài liệu/index là bản dẫn xuất: giữ nguồn và ghi rõ filtering/chunking/indexing; không thay tên thành dataset tự thu thập.

## Đánh giá mới

60 tình huống synthetic được viết riêng, 20 development / 40 evaluation. Hồ sơ không phải bệnh án; gold evidence chọn từ corpus theo nội dung, không tìm câu hỏi/nhãn TEST cũ. Đánh giá chất lượng phối hợp tool và nguồn, không kiểm hiệu quả điều trị hoặc predictive generalization mới của checkpoint. Xem protocol và audit kèm dataset.

Các trang nguồn đã được kiểm ở 01/11/2026; số đo local được lấy từ file/manifest đã pin, không từ số hiện hành của repository trên mạng.
