# Dataset card — CDC Diabetes Health Indicators (binary)

## Nhận dạng và nguồn

- Dataset ID: `ch2_diabetes_binary`.
- Chương/bài toán: Chương 2, binary classification nguy cơ diabetes.
- Nguồn: <https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset>.
- Truy cập: 2026-10-05. Citation key: `teboul2019diabetes`.
- License: `UNVERIFIED`; chưa xác nhận được từ metadata chính thức có thể truy cập, vì vậy không gán license theo suy đoán.
- Local: `datasets/diabetes/diabetes.csv`; 6,347,570 bytes; SHA-256 `873128ba0264d66a8b09bb6158f21fd4bedc10459d1ed5ecad3b94167a9539b4`.

## Kích thước và schema

- Raw: 70,692 hàng × 22 cột; 21 predictor và target `Diabetes_binary`.
- Sau loại exact duplicates trong notebook nguồn: 69,057 hàng; model matrix `(69,057, 21)`.
- Biến gồm chỉ báo sức khỏe/lối sống và các mã thứ bậc: `HighBP`, `HighChol`, `BMI`, `Smoker`, `PhysActivity`, `GenHlth`, `Age`, `Education`, `Income`, v.v.

## Phân bố và mẫu

- Raw target cân bằng chính xác: class 0 = 35,346 (50%); class 1 = 35,346 (50%).
- Mẫu input rút gọn thực tế: `HighBP=1, HighChol=0, BMI=26, Smoker=0, PhysActivity=1, Age=4, Income=8`.
- Output tương ứng của hàng mẫu đầu: `Diabetes_binary=0`.
- Khi trình bày DOCX, dùng 2–3 hàng rút gọn và biểu đồ target; không in toàn bộ 22 cột trên một bảng ngang.

## Tiền xử lý và split khóa

- Loại exact duplicates trước split.
- Outer split stratified 80/20 với seed 42; development split tiếp thành TRAIN/VAL, tỷ lệ hiệu dụng khoảng 64/16/20.
- Median imputation và StandardScaler chỉ fit TRAIN.

## Nhận xét và giới hạn

- Bản balanced thuận tiện cho so sánh thuật toán nhưng không phản ánh prevalence tự nhiên; accuracy vì vậy không được diễn giải như hiệu quả lâm sàng ngoài đời.
- Biến là self-reported survey indicators, không phải chẩn đoán y khoa. Deployment phải hiển thị cảnh báo “không phải chẩn đoán y khoa”.
- Exact-duplicate removal làm phân bố sau làm sạch lệch nhẹ khỏi 50/50; mọi metric phải dùng split artifact sau làm sạch.

## Bằng chứng local

- Notebook: `pipeline/diabetes_pipeline.ipynb`.
- Metadata/model hiện có: `pipeline/diabetes/metadata.json`, `model.npz`, `preprocessor.joblib`.
- Figure phân bố mới sẽ được tái tạo ở Phase 3 từ split artifact, không chụp output notebook.
