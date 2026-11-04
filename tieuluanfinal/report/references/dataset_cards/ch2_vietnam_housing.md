# Dataset card — Vietnam Housing Dataset 2024

## Nhận dạng và nguồn

- Dataset ID: `ch2_vietnam_housing`.
- Chương/bài toán: Chương 2, regression giá nhà.
- Nguồn: <https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024>.
- Truy cập: 2026-10-05. Citation key: `nguyen2024housing`.
- License: `UNVERIFIED`; chưa tìm được license từ metadata chính thức có thể truy cập.
- Local: `datasets/housing_price/vietnam_housing_dataset.csv`; 3,532,685 bytes; SHA-256 `7ee188d69aca06349a81bac0c2d2d1503058d5aec7124edfd075154fa87d97c8`.

## Kích thước và schema

- Raw: 30,229 hàng × 12 cột.
- Sau làm sạch: 30,223 hàng; X logic có 12 feature, sau one-hot là 154 cột; target chuẩn hóa tên `Price_BillionVND`.
- Các cột raw: `Address`, `Area`, `Frontage`, `Access Road`, `House direction`, `Balcony direction`, `Floors`, `Bedrooms`, `Bathrooms`, `Legal status`, `Furniture state`, `Price`.

## Phân bố và mẫu

- Price raw/clean nằm trong khoảng 1.0–11.5 tỷ VND; sau làm sạch: mean 5.873, Q1 4.2, median 5.9, Q3 7.5 tỷ VND.
- Diện tích sau làm sạch: mean 68.51 m², median 56 m², khoảng 10–595 m².
- Mẫu input thực tế rút gọn: `Area=84`, `Floors=4`, `Legal status=Have certificate`; nhiều thuộc tính hướng/tiếp cận bị thiếu.
- Output hàng mẫu: `Price=8.6` tỷ VND.

## Tiền xử lý và split khóa

- Price-derived `price_per_m2_million` chỉ dùng EDA, không đưa vào X để tránh target leakage.
- Numeric: median imputation + scaling. Categorical: điền `Unknown` + one-hot; tất cả fit TRAIN.
- Outer split 80/20 seed 42; TRAIN/VAL hiệu dụng khoảng 64/16; TEST 20%.
- MLP regression được phép train trên standardized `log1p(price)`; metric bắt buộc inverse-transform về tỷ VND.

## Nhận xét và giới hạn

- Address có cardinality cao và mang yếu tố vị trí mạnh; cần tránh để one-hot vô tình ghi nhớ các địa chỉ hiếm.
- Missingness không đồng đều giữa frontage, road access, bedrooms/bathrooms và hướng; “không có thông tin” không đồng nghĩa giá trị bằng 0.
- Tập dữ liệu chỉ là snapshot rao bán, không nhất thiết là giá giao dịch; không suy rộng thành chỉ số thị trường Việt Nam.

## Bằng chứng local

- Notebook: `pipeline/house_price_pipeline.ipynb`.
- Metadata/model: `pipeline/house_price/metadata.json`, `model.npz`, `preprocessor.joblib`.
- Notebook ghi rõ 30,223 hàng sau cleaning và target summary nêu trên.
