# Phase 0 — Gap Analysis và Evidence Map

## 1. Phạm vi audit

Audit bao phủ:

- 3 notebook Chương 2 trong `pipeline/`;
- 5 notebook Chương 3 trong `A05/notebooks/`;
- 8 notebook Chương 4 trong `A06/notebooks/`;
- raw/processed datasets dùng trực tiếp;
- model và preprocessor artifacts;
- metrics, predictions, figures và reports hiện có;
- DOCX mẫu ngoài workspace do người dùng cung cấp.

Các file nguồn chỉ được đọc. Mọi output Phase 0 nằm trong `term_paper/`.

## 2. Tóm tắt inventory

| Nhóm | Số lượng/Quy mô đã lập chỉ mục |
|---|---:|
| Notebook | 16 |
| Notebook Chương 2 / 3 / 4 | 3 / 5 / 8 |
| Model hoặc preprocessor artifacts | 25 |
| Metric/prediction/metadata files | 77 |
| Hash records | 148 |
| A05 result figures | 56 files, 16,919,342 bytes |
| A06 result figures | 27 files, 2,400,722 bytes |
| EuroSAT | 27,000 files, 91,844,360 bytes |
| Oxford-IIIT Pet folder | 25,864 files, 821,045,236 bytes |
| A06 processed arrays | 6 files, 2,835,949 bytes |

Chi tiết và SHA-256 nằm trong `source_inventory.json`, `source_hashes.csv` và `folder_manifests/`.

## 3. Notebook execution metadata

Không notebook nào chứa output kiểu `error`. Tuy nhiên, 7 notebook có output đã lưu nhưng `execution_count` bị trống ở một phần hoặc toàn bộ code cells:

- `A05/notebooks/02_EuroSAT_CNN.ipynb`: 3/25 code cells có execution count.
- `A05/notebooks/03_Oxford_Pets_CNN.ipynb`: 0/24.
- `A06/notebooks/01_RNN_Fundamentals.ipynb`: 7/10.
- `A06/notebooks/02_Customer_Behavior_Data.ipynb`: 4/14.
- `A06/notebooks/03_Stock_Data.ipynb`: 4/9.
- `A06/notebooks/04_PyTorch_Customer_RNN.ipynb`: 6/11.
- `A06/notebooks/05_PyTorch_Stock_RNN.ipynb`: 4/13.

Điều này không phủ định audit report hiện có — `A06/CURRENT_STATE.md` ghi nhận clean execution 91/91 cells — nhưng notebook serialization hiện tại không tự chứng minh được thứ tự thực thi. Trước khi dùng notebook mới cho tiểu luận, Phase 3–5 phải clean-run và lưu execution metadata nhất quán.

## 4. Requirement gap matrix

| Yêu cầu | Bằng chứng hiện có | Gap | Phase xử lý |
|---|---|---|---:|
| Mở đầu 3–4 trang | Chưa có report tích hợp | Thiếu hoàn toàn | 2, 7 |
| Lịch sử AI 8 trang | Không có trong notebook hiện tại | Thiếu hoàn toàn | 2 |
| Chương 2 có 2–3 dataset | Diabetes, house price, customer behavior | Đạt về số lượng | 3 |
| Chương 2 scratch/Keras/PyTorch | NumPy DNN + sklearn | Thiếu matched Keras/PyTorch | 3 |
| Chương 3 có 2–3 dataset | EuroSAT, Oxford Pets, CDC Diabetes | Đạt về số lượng | 4 |
| Chương 3 scratch/Keras/PyTorch | Keras CNN; manual forward demo | Thiếu trainable NumPy CNN và PyTorch CNN | 4 |
| Chương 4 có 2–3 dataset | Online Retail II và AAPL | Đạt về số lượng | 5 |
| Chương 4 scratch/Keras/PyTorch | Keras + PyTorch; manual NumPy forward | Thiếu trainable NumPy RNN/BPTT | 5 |
| Link/license/citation dataset | Tên/local path chủ yếu đã có | URL và citation chưa đồng nhất | 1 |
| Kích cỡ, mẫu, phân bố, nhận xét | Có trong notebook/report | Cần chuẩn hóa theo một dataset-card template | 1, 3–5, 7 |
| So sánh ba implementation | Chưa đủ ở bất kỳ chương nào | Cần matched protocol | 3–5 |
| Deployment | Chỉ có model artifact/demo JSON | Chưa có app/API, schema validation và smoke test | 6 |
| Một DOCX cuối | A05/A06 có report riêng | Chưa tích hợp; báo cáo riêng vượt page budget | 7–9 |
| Tài liệu tham khảo học thuật | Rất hạn chế | Thiếu bibliography/citation coverage | 1, 2, 7 |

## 5. Evidence map — Chương 2

| Kết luận hiện có | Artifact số liệu chính | Artifact hỗ trợ |
|---|---|---|
| Diabetes Improved DNN: F1 0.7712, ROC-AUC 0.8192 | `pipeline/diabetes/metadata.json` | `pipeline/diabetes/final_comparison.csv`, `pipeline/diabetes_pipeline.ipynb` |
| House Price Improved DNN: RMSE 1.4169 tỷ VND, R² 0.5799 | `pipeline/house_price/metadata.json` | `pipeline/house_price/final_comparison.csv`, `pipeline/house_price_pipeline.ipynb` |
| Customer churn Improved DNN: F1 0.3644, ROC-AUC 0.6655 | `pipeline/customer_behavior/metadata.json` | `pipeline/customer_behavior/final_comparison.csv`, `pipeline/customer_behavior_pipeline.ipynb` |
| Ba pipeline đã lưu model/preprocessor/schema/demo | `pipeline/*/metadata.json` | `pipeline/*/model.*`, `preprocessor.joblib`, `feature_schema.json`, `demo_input.json`, `demo_prediction.json` |

Gap phương pháp: kết quả hiện tại so sánh classical sklearn models với NumPy DNN; chưa phải cùng một MLP được cài bằng scratch/Keras/PyTorch.

## 6. Evidence map — Chương 3

| Kết luận hiện có | Artifact số liệu chính | Figure/report hỗ trợ |
|---|---|---|
| EuroSAT BasicCNN2D đạt accuracy 0.7398 và macro-F1 0.7256 | `A05/results/metrics/eurosat_models.csv` | `A05/results/figures/eurosat/`, `A05/report/A05_report.md` |
| EuroSAT AlexNet/VGG/ResNet-inspired cùng collapse ở accuracy 0.1111, macro-F1 0.0200 | `A05/results/metrics/eurosat_models.csv` | Confusion matrices và error grids trong `A05/results/figures/eurosat/` |
| Oxford Pets BasicCNN2D cao nhất nhưng chỉ accuracy 0.0472, macro-F1 0.0198 | `A05/results/metrics/oxford_pets_models.csv` | `A05/results/figures/oxford_pets/` |
| Diabetes BasicCNN1D có macro-F1 cao nhất 0.4392; các kiến trúc có trade-off recall khác nhau | `A05/results/metrics/diabetes_models.csv` | `A05/results/metrics/diabetes_per_class_metrics.csv`, `A05/results/figures/diabetes/` |
| Có 44 hyperparameter experiment rows và split artifacts | `A05/results/hyperparameters/` | `A05/results/splits/`, `A05/README.md` |

Gap phương pháp:

- “From scratch” của A05 là random initialization trong Keras, không phải NumPy implementation.
- Không có PyTorch CNN.
- Common protocol giữa bốn kiến trúc là một controlled ablation, không chứng minh best-achievable performance của từng family.
- Oxford và ba deep EuroSAT models cho kết quả rất yếu; phải giữ và giải thích trung thực.

## 7. Evidence map — Chương 4

| Kết luận hiện có | Artifact số liệu chính | Figure/report hỗ trợ |
|---|---|---|
| Customer PyTorch/Keras có F1 0.2485/0.2491, ROC-AUC 0.7009/0.7005 | `A06/results/metrics/framework_comparison.json` | `A06/results/figures/comparison/customer_*` |
| Hai framework đồng ý 99.2536% thresholded labels; probability correlation 0.9919 | `A06/results/metrics/framework_comparison.json` | `A06/results/predictions/*customer_predictions.csv` |
| Stock PyTorch RNN: RMSE 23.5788 USD, R² -0.0269 | `A06/results/metrics/pytorch_stock_metrics.json` | `A06/results/figures/pytorch_stock/` |
| Stock Keras RNN: RMSE 27.8703 USD, R² -0.4347 | `A06/results/metrics/keras_stock_metrics.json` | `A06/results/figures/keras_stock/` |
| Naive last-Close thắng rõ: RMSE 3.8789 USD, R² 0.9722 | `A06/results/metrics/framework_comparison.json` | `A06/results/figures/comparison/stock_*` |
| Split thời gian, scaler TRAIN-only và alignment đã được audit | `A06/results/metrics/preprocessing_metadata.json` | `A06/report/A06_AUDIT_REPORT.md`, `A06/CURRENT_STATE.md` |

Gap phương pháp: chưa có Vanilla RNN scratch train bằng BPTT trên hai processed datasets.

## 8. Dataset provenance gaps

1. Notebook hiện tại hầu như không chứa URL nguồn trực tiếp; Phase 1 phải lập source registry chính thức.
2. `datasets/customer_behavior/README.md` có bất nhất nội bộ: phần mô tả nói 10K customers/120K transactions/80K sessions/25K reviews, trong khi một số dòng bảng README ghi 5,000. Notebook đọc file thật và báo quy mô lớn hơn; Phase 1 phải coi dữ liệu thực tế là bằng chứng chính và ghi chênh lệch.
3. AAPL là snapshot local khóa đến 2025-12-31. Không được tải lại dữ liệu hiện tại trong các phase sau.
4. Oxford Pets phải dùng official annotation sample set, không glob toàn bộ raw images.
5. A05 Diabetes và pipeline Diabetes là hai biến thể dataset/target khác nhau; không được nhập nhằng chúng trong báo cáo.

## 9. Rủi ro và kiểm soát

| Rủi ro | Kiểm soát |
|---|---|
| Vượt page budget do tái dùng nguyên report A05/A06 | Chỉ lấy bảng/hình/kết luận cần thiết; viết lại theo outline 12–14 trang/chương |
| Scratch CNN quá chậm trên CPU | Fixed stratified benchmark subset dùng giống nhau cho cả ba framework; lưu indices |
| So sánh không công bằng | Hash split/preprocessor, matched topology và test-key alignment |
| Metric bị nhập tay sai | Sinh bảng từ CSV/JSON; kiểm tra lại từ prediction artifacts |
| Dataset source không rõ | Source registry + access date + license + local hash ở Phase 1 |
| Notebook output cũ nhưng execution metadata thiếu | Clean-run notebook mới và lưu execution counts liên tục |
| Kết quả âm bị diễn giải sai | Giữ baseline và limitations; không tuyên bố winner phổ quát |
| Ghi đè assignment gốc | Mọi code/artifact mới đặt trong `term_paper/` |

## 10. Kết luận Phase 0

Nguồn hiện có đủ mạnh để tái sử dụng EDA, preprocessing, metrics, predictions và figures. Phần việc mới bắt buộc tập trung vào source/citation normalization, matched scratch–Keras–PyTorch experiments, deployment và biên soạn DOCX tích hợp. Không cần thay dataset hoặc xóa kết quả hiện có.

