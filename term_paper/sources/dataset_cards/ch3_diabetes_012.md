# Dataset card — CDC Diabetes Health Indicators (3 lớp)

## Nhận dạng và nguồn

- Dataset ID: `ch3_diabetes_012`.
- Chương/bài toán: Chương 3, multiclass classification với Conv1D adaptation.
- Nguồn: <https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset>.
- Truy cập: 2026-10-05. Citation key: `teboul2019diabetes`.
- License: `UNVERIFIED`; không suy đoán từ mirror.
- Local: `A05/datasets/diabetes/diabetes_012_health_indicators_BRFSS2015.csv`; 22,738,151 bytes; SHA-256 `a971809d0786d2d7d7f6070f83dfe8af9d860ea33a79e0e2701c8a49f78f9861`.

## Kích thước và schema

- 253,680 hàng × 22 cột; 21 predictor và target `Diabetes_012`.
- Target mapping: 0 = no diabetes; 1 = prediabetes; 2 = diabetes.
- Predictor schema giống bản binary: blood pressure/cholesterol indicators, BMI, lifestyle, self-rated health và mã nhân khẩu học.

## Phân bố và mẫu

| Lớp | Số hàng | Tỷ lệ xấp xỉ |
|---|---:|---:|
| 0 — No diabetes | 213,703 | 84.24% |
| 1 — Prediabetes | 4,631 | 1.83% |
| 2 — Diabetes | 35,346 | 13.93% |

- Mẫu input rút gọn: `HighBP=1, HighChol=1, BMI=40, Smoker=1, GenHlth=5, Age=9, Income=3`.
- Output của hàng mẫu đầu: `Diabetes_012=0`.
- Split A05: TRAIN 177,576; VAL 38,052; TEST 38,052, stratified seed 42.

## Tiền xử lý và biểu diễn CNN

- StandardScaler fit TRAIN, giữ nguyên thứ tự 21 predictor trong CSV.
- Biểu diễn Conv1D: `(length=21, channels=1)`.
- Class weights tính trên TRAIN. Macro-F1 và per-class recall, đặc biệt lớp 1, là metric trọng tâm.

## Nhận xét và giới hạn

- Lớp prediabetes chỉ 1.83%, nên accuracy có thể cao dù model bỏ qua lớp này; confusion matrix và recall lớp 1 là bắt buộc.
- Áp Conv1D lên chuỗi 21 feature tạo adjacency nhân tạo: feature lân cận trong file không phải lân cận không gian/thời gian tự nhiên. Đây là case study kiến trúc, không phải khẳng định CNN phù hợp nhất cho dữ liệu bảng.
- Self-reported survey không thay thế chẩn đoán lâm sàng.

## Bằng chứng local

- Notebook: `A05/notebooks/04_CDC_Diabetes_CNN.ipynb`.
- Splits: `A05/results/splits/diabetes_{train,val,test}.csv`.
- Metrics/figures hiện có: `A05/results/metrics/diabetes_*`, `A05/results/figures/diabetes/`.
