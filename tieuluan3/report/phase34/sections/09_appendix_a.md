# PHỤ LỤC A. HỒ SƠ DỮ LIỆU

Các mẫu là nhãn/evidence nguồn hoặc output tool đã lưu, không phải lần inference mới. Với ImageNet chỉ có metadata; không dựng ảnh hoặc đủ ba mẫu giả. Trường dài được trích để đọc, bản gốc liên kết giữ đầy đủ schema/hash.

## A.1. ch1_iris_history

Phạm vi: **historical_case**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Fisher, R. A. (1936). Iris. UCI Machine Learning Repository. DOI:10.24432/C56C76.](https://archive.ics.uci.edu/static/public/53/iris.zip)
Phiên bản: UCI 53 original Iris snapshot; sha256:d11fe30213d36434a0879aab7cb00ce3c812eb7ba2495874438abff7b7b762e9

Giấy phép/phạm vi: CC BY 4.0; attribution required. https://archive.ics.uci.edu/dataset/53/iris

Raw: 3,738 byte; 150 raw rows.

Số đo và schema phần dùng trong V3:

Bảng A.1. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| records | 150 |
| features | 4 |
| unit | raw rows |


#### Mẫu input/output

Mẫu nguồn phục vụ lịch sử, không phải output của mô hình được train trong Phase24.

Bảng A.2. Mẫu input/output

| input | known_output |
|---|---|
| [5.1, 3.5, 1.4, 0.2] | Iris-setosa |
| [4.9, 3.0, 1.4, 0.2] | Iris-setosa |
| [4.7, 3.2, 1.3, 0.2] | Iris-setosa |


#### Phân bố và chất lượng dữ liệu

Bảng A.3. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| Iris-setosa | 50 |
| Iris-versicolor | 50 |
| Iris-virginica | 50 |


#### Cách chia tập và tiền xử lý

Ch1 không huấn luyện. Giữ official split nếu có; không tạo TEST hay preprocessing fit cho chương lịch sử.

#### Nhận xét và giới hạn

- Benchmark nhỏ, cân bằng; chỉ minh họa lịch sử phân loại, không có thí nghiệm V3 Ch1.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch1_iris_history/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch1_iris_history](../../references/dataset_cards/v3_eda/ch1_iris_history.md).

## A.2. ch1_mnist_history

Phạm vi: **historical_case**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [LeCun, Y., Cortes, C., and Burges, C. MNIST handwritten digit database; NPZ distributed by Keras.](https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz)
Phiên bản: Keras sanctioned MNIST NPZ; original 60000/10000 split; sha256:731c5ac602752760c8e48fbffcf8c3b850d9dc2a2aedcf2cc48468fc17b673d1

Giấy phép/phạm vi: CC BY-SA 3.0 as explicitly documented at https://keras.io/api/datasets/mnist/; retain attribution/share-alike for adaptations.

Raw: 11,490,434 byte; 70000 images (official 60000 train + 10000 test).

Số đo và schema phần dùng trong V3:

Bảng A.4. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| records | 70000 |
| features | 784 |
| unit | images (official 60000 train + 10000 test) |


#### Mẫu input/output

Mẫu nguồn phục vụ lịch sử, không phải output của mô hình được train trong Phase24.

Bảng A.5. Mẫu input/output

| input | known_output |
|---|---|
| official train index 0, uint8 28x28 | 5 |
| official train index 1, uint8 28x28 | 0 |
| official train index 2, uint8 28x28 | 4 |


#### Phân bố và chất lượng dữ liệu

Bảng A.6. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| 0 | 6903 |
| 1 | 7877 |
| 2 | 6990 |
| 3 | 7141 |
| 4 | 6824 |
| 5 | 6313 |
| 6 | 6876 |
| 7 | 7293 |
| 8 | 6825 |
| 9 | 6958 |


#### Cách chia tập và tiền xử lý

Ch1 không huấn luyện. Giữ official split nếu có; không tạo TEST hay preprocessing fit cho chương lịch sử.

#### Nhận xét và giới hạn

- MNIST là case study lịch sử; không thay IDRiD/EuroSAT/CIFAR trong ma trận CNN V3.
- Official train có 0 ảnh trùng pixel; không tạo random split mới hay train Ch1.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch1_mnist_history/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch1_mnist_history](../../references/dataset_cards/v3_eda/ch1_mnist_history.md).

## A.3. ch1_imagenet_history

Phạm vi: **historical_case_metadata_only**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Russakovsky, O. et al. (2015). ImageNet Large Scale Visual Recognition Challenge. IJCV. DOI:10.1007/s11263-015-0816-y.](https://www.image-net.org/challenges/LSVRC/2012/index.php)
Phiên bản: ILSVRC 2012 official challenge metadata only; sha256:9d63dd697cceeeb640da708183bbbd6f4c35f98175d4cbec0439c3f3ea4373cc

Giấy phép/phạm vi: Only a local provenance copy of the public challenge webpage, not an image dataset license. Cite/paraphrase metadata; no redistribution of page or ImageNet images. Full image access remains subject to ImageNet terms.

Raw: 18,582 byte; 1 official metadata webpage, ZERO local images.

Số đo và schema phần dùng trong V3:

Bảng A.7. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| records | 1 |
| features | null |
| unit | official metadata webpage, ZERO local images |


#### Mẫu input/output

Mẫu nguồn phục vụ lịch sử, không phải output của mô hình được train trong Phase24.

Bảng A.8. Mẫu input/output

| input | known_output |
|---|---|
| Trang metadata ILSVRC2012 đã lưu | 1000 categories công bố; không có ảnh local |


#### Phân bố và chất lượng dữ liệu

Bảng A.9. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| local_metadata_page | 1 |
| local_images | 0 |


#### Cách chia tập và tiền xử lý

Ch1 không huấn luyện. Giữ official split nếu có; không tạo TEST hay preprocessing fit cho chương lịch sử.

#### Nhận xét và giới hạn

- Chỉ metadata/citation lịch sử. Không bịa ảnh mẫu, phân bố ảnh hay thí nghiệm trên full ImageNet.
- Quy mô ảnh công bố trong source card không phải số mẫu đo trên máy.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch1_imagenet_history/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch1_imagenet_history](../../references/dataset_cards/v3_eda/ch1_imagenet_history.md).

## A.4. ch2_cdc_diabetes

Phạm vi: **measured_tabular**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Teboul, A. (2021). Diabetes Health Indicators Dataset, derived from CDC BRFSS 2015. UCI dataset 891. DOI:10.24432/C53919.](https://archive.ics.uci.edu/static/public/891/data.csv)
Phiên bản: UCI 891 / CDC BRFSS 2015 binary diabetes; sha256:9f71fda9d4ae5f4878c99b9233b6a16accfa9a17c194116a6b78100540934964

Giấy phép/phạm vi: UCI directs licensing to upstream Kaggle; public Kaggle API confirms CC0: Public Domain. https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset . Not assumed to inherit UCI's default CC BY license.

Raw: 13,494,568 byte; 253680 raw rows.

Số đo và schema phần dùng trong V3:

Bảng A.10. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| rows | 253680 |
| features | ["high_bp", "high_chol", "chol_check", "bmi", "smoker", "stroke", "heart_diseaseor_attack", "phys_activity", "fruits", "veggies", "hvy_alcohol_consump", "any_healthcare", "no_docbc_cost", "gen_hlth", "ment_hlth", "phys_hlth", "diff_walk", "sex", "age", "education", "income"] |
| model_input_width | 21 |
| target | diabetes_binary |
| split | {"path": "data/splits/v3/ch2_cdc_diabetes/split_contract.json", "sha256": "557c1b646bf0259b9d475c2f0d25bf5bde33b8c4d8ed93d17fc4af2c1f813df4", "size_bytes": 1476} |
| matched_subset | {"path": "data/splits/v3/ch2_cdc_diabetes/matched_train.ids.jsonl.gz", "sha256": "5319b90adc4a6ae52918700506ae66054de74640f4012cb09b71f2a79d8c3759", "size_bytes": 53576} |
| counts | {"train": 177505, "validation": 38053, "test": 38122} |
| matched_train_count | 20000 |
| quarantine_count | 0 |


#### Mẫu input/output

Ba mẫu thuộc matched train, output là nhãn/giá nguồn, không phải dự đoán. Input hiển thị tối đa 8 biến; samples.json chứa đủ biến.

Bảng A.11. Mẫu input/output

| id | input | known_output |
|---|---|---|
| row_0048946 | {"high_bp": 1, "high_chol": 1, "chol_check": 1, "bmi": 24, "smoker": 0, "stroke": 0, "heart_diseaseor_attack": 0, "phys_activity": 1} | 0 |
| row_0129953 | {"high_bp": 0, "high_chol": 0, "chol_check": 1, "bmi": 21, "smoker": 0, "stroke": 0, "heart_diseaseor_attack": 0, "phys_activity": 1} | 0 |
| row_0216399 | {"high_bp": 0, "high_chol": 0, "chol_check": 1, "bmi": 22, "smoker": 0, "stroke": 0, "heart_diseaseor_attack": 0, "phys_activity": 1} | 0 |


#### Phân bố và chất lượng dữ liệu

Bảng A.12. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| target_by_partition | {"train": {"0": 152760, "1": 24745}, "validation": {"0": 32745, "1": 5308}, "test": {"0": 32829, "1": 5293}} |
| missing_by_feature | {"high_bp": 0, "high_chol": 0, "chol_check": 0, "bmi": 0, "smoker": 0, "stroke": 0, "heart_diseaseor_attack": 0, "phys_activity": 0, "fruits": 0, "veggies": 0, "hvy_alcohol_consump": 0, "any_healthcare": 0, "no_docbc_cost": 0, "gen_hlth": 0, "ment_hlth": 0, "phys_hlth": 0, "diff_walk": 0, "sex": 0, "age": 0, "education": 0, "income": 0} |
| duplicate_rows | 25772 |
| outliers | feature_profile.json, ngưỡng IQR từ train |


#### Cách chia tập và tiền xử lý

Gom exact feature duplicates và PID nếu có, rồi stratify theo nhóm 70/15/15 (xấp xỉ theo số dòng). Imputer/scaler/vocabulary/target scaler/class weight chỉ fit matched train; unknown category -> all-zero. Không tự xóa outlier.

#### Nhận xét và giới hạn

- CDC bản nhị phân: 1 gộp tiền tiểu đường/tiểu đường, không diễn giải thành ba lớp.
- Khảo sát tự báo cáo, quan sát chứ không chứng minh quan hệ nhân quả; không dùng để chẩn đoán.
- Không có patient ID được xác minh. Gom trùng feature không chứng minh độc lập bệnh nhân.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch2_cdc_diabetes/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch2_cdc_diabetes](../../references/dataset_cards/v3_eda/ch2_cdc_diabetes.md).

## A.5. ch2_ames_housing

Phạm vi: **measured_tabular**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [De Cock, D. (2011). Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project. Journal of Statistics Education 19(3). DOI:10.1080/10691898.2011.11889627.](https://jse.amstat.org/v19n3/decock/AmesHousing.txt)
Phiên bản: De Cock JSE 2011 original 2930-row tab-delimited release; sha256:6cfe6cb525ba437de428653a1040e2aed7d696640bf75203786a6d7a0e67cfcc

Giấy phép/phạm vi: Author-published teaching/research dataset accompanying JSE article; retain attribution; no explicit SPDX license on original TXT. GPL-2 in topepo/AmesHousing applies to that package, not automatically to this original source. Local academic analysis only; no raw redistribution.

Raw: 960,807 byte; 2930 raw rows.

Số đo và schema phần dùng trong V3:

Bảng A.13. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| rows | 2930 |
| features | ["ms_sub_class", "ms_zoning", "lot_frontage", "lot_area", "street", "alley", "lot_shape", "land_contour", "utilities", "lot_config", "land_slope", "neighborhood", "condition_1", "condition_2", "bldg_type", "house_style", "overall_qual", "overall_cond", "year_built", "year_remod_add", "roof_style", "roof_matl", "exterior_1st", "exterior_2nd", "mas_vnr_type", "mas_vnr_area", "exter_qual", "exter_cond", "foundation", "b (trích; bản đầy đủ trong nguồn) |
| model_input_width | 313 |
| target | sale_price |
| split | {"path": "data/splits/v3/ch2_ames_housing/split_contract.json", "sha256": "3c0db0100706a3b725b7e7af50a8fc1c9ec4ab9cb37cd18e1e041686b80b6505", "size_bytes": 1470} |
| matched_subset | {"path": "data/splits/v3/ch2_ames_housing/matched_train.ids.jsonl.gz", "sha256": "0542fa4ebf11a3bd430fb84850adf1b1d662be991f88c5ebb76a4c4ac611b5bd", "size_bytes": 4739} |
| counts | {"train": 2051, "validation": 439, "test": 440} |
| matched_train_count | 2051 |
| quarantine_count | 0 |


#### Mẫu input/output

Ba mẫu thuộc matched train, output là nhãn/giá nguồn, không phải dự đoán. Input hiển thị tối đa 8 biến; samples.json chứa đủ biến.

Bảng A.14. Mẫu input/output

| id | input | known_output |
|---|---|---|
| row_0001475 | {"ms_sub_class": 20, "ms_zoning": "RL", "lot_frontage": 65.0, "lot_area": 8450, "street": "Pave", "alley": null, "lot_shape": "Reg", "land_contour": "Lvl"} | 210000 |
| row_0001603 | {"ms_sub_class": 20, "ms_zoning": "RL", "lot_frontage": 37.0, "lot_area": 6951, "street": "Pave", "alley": null, "lot_shape": "IR1", "land_contour": "Lvl"} | 119500 |
| row_0001732 | {"ms_sub_class": 60, "ms_zoning": "RL", "lot_frontage": 63.0, "lot_area": 9729, "street": "Pave", "alley": null, "lot_shape": "IR1", "land_contour": "Lvl"} | 198444 |


#### Phân bố và chất lượng dữ liệu

Bảng A.15. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| target_by_partition | {"train": {"count": 2051.0, "mean": 180007.88980984886, "std": 76288.62916288216, "min": 12789.0, "25%": 129650.0, "50%": 160000.0, "75%": 214000.0, "max": 615000.0}, "validation": {"count": 439.0, "mean": 181666.46469248293, "std": 84922.31341486958, "min": 40000.0, "25%": 129450.0, "50%": 160500.0, "75%": 213000.0, "max": 745000.0}, "test": {"count": 440.0, "mean": 183601.58181818182, "std": 90528.58532658328, "min (trích; bản đầy đủ trong nguồn) |
| missing_by_feature | {"ms_sub_class": 0, "ms_zoning": 0, "lot_frontage": 490, "lot_area": 0, "street": 0, "alley": 2732, "lot_shape": 0, "land_contour": 0, "utilities": 0, "lot_config": 0, "land_slope": 0, "neighborhood": 0, "condition_1": 0, "condition_2": 0, "bldg_type": 0, "house_style": 0, "overall_qual": 0, "overall_cond": 0, "year_built": 0, "year_remod_add": 0, "roof_style": 0, "roof_matl": 0, "exterior_1st": 0, "exterior_2nd": 0, (trích; bản đầy đủ trong nguồn) |
| duplicate_rows | 2 |
| outliers | feature_profile.json, ngưỡng IQR từ train |


#### Cách chia tập và tiền xử lý

Gom exact feature duplicates và PID nếu có, rồi stratify theo nhóm 70/15/15 (xấp xỉ theo số dòng). Imputer/scaler/vocabulary/target scaler/class weight chỉ fit matched train; unknown category -> all-zero. Không tự xóa outlier.

#### Nhận xét và giới hạn

- Giá bán tính bằng USD; thiếu ở một số trường có thể biểu thị không có tiện ích, không mặc định bằng 0.
- PID/Order không làm feature. Gom PID và trùng feature theo liên kết bắc cầu.
- Chia theo nhóm/ngẫu nhiên không đại diện cho triển khai dự báo giá nhà tương lai hay địa phương khác.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch2_ames_housing/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch2_ames_housing](../../references/dataset_cards/v3_eda/ch2_ames_housing.md).

## A.6. ch2_bank_marketing

Phạm vi: **measured_tabular**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Moro, S., Rita, P., and Cortez, P. (2014). Bank Marketing. UCI. DOI:10.24432/C5K306.](https://archive.ics.uci.edu/static/public/222/bank+marketing.zip)
Phiên bản: UCI 222; bank.zip/bank-full.csv, original 45211-row variant; sha256:e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4

Giấy phép/phạm vi: CC BY 4.0. https://archive.ics.uci.edu/dataset/222/bank+marketing . Retain attribution; exclude duration before-call prediction.

Raw: 1,023,843 byte; 45211 raw rows.

Số đo và schema phần dùng trong V3:

Bảng A.16. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| rows | 45211 |
| features | ["age", "job", "marital", "education", "default", "balance", "housing", "loan", "contact", "day", "month", "campaign", "pdays", "previous", "poutcome"] |
| model_input_width | 50 |
| target | subscription |
| split | {"path": "data/splits/v3/ch2_bank_marketing/split_contract.json", "sha256": "72136591aca9bb338d59aab29106974f1cdf1103624a46074782c3b0182c9035", "size_bytes": 1485} |
| matched_subset | {"path": "data/splits/v3/ch2_bank_marketing/matched_train.ids.jsonl.gz", "sha256": "b271747e61b6dcdfc4cf3f5b29b8a28643aaf82760b1efa5b14f3fdec3de811d", "size_bytes": 25066} |
| counts | {"train": 31648, "validation": 6781, "test": 6782} |
| matched_train_count | 10000 |
| quarantine_count | 0 |


#### Mẫu input/output

Ba mẫu thuộc matched train, output là nhãn/giá nguồn, không phải dự đoán. Input hiển thị tối đa 8 biến; samples.json chứa đủ biến.

Bảng A.17. Mẫu input/output

| id | input | known_output |
|---|---|---|
| row_0030605 | {"age": 31, "job": "self-employed", "marital": "single", "education": "secondary", "default": "no", "balance": 0, "housing": "no", "loan": "yes"} | 0 |
| row_0032873 | {"age": 32, "job": "services", "marital": "divorced", "education": "secondary", "default": "no", "balance": 453, "housing": "yes", "loan": "no"} | 0 |
| row_0038552 | {"age": 28, "job": "blue-collar", "marital": "married", "education": "primary", "default": "no", "balance": 278, "housing": "yes", "loan": "yes"} | 0 |


#### Phân bố và chất lượng dữ liệu

Bảng A.18. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| target_by_partition | {"train": {"0": 27946, "1": 3702}, "validation": {"0": 5988, "1": 793}, "test": {"0": 5988, "1": 794}} |
| missing_by_feature | {"age": 0, "job": 0, "marital": 0, "education": 0, "default": 0, "balance": 0, "housing": 0, "loan": 0, "contact": 0, "day": 0, "month": 0, "campaign": 0, "pdays": 0, "previous": 0, "poutcome": 0} |
| duplicate_rows | 16 |
| outliers | feature_profile.json, ngưỡng IQR từ train |


#### Cách chia tập và tiền xử lý

Gom exact feature duplicates và PID nếu có, rồi stratify theo nhóm 70/15/15 (xấp xỉ theo số dòng). Imputer/scaler/vocabulary/target scaler/class weight chỉ fit matched train; unknown category -> all-zero. Không tự xóa outlier.

#### Nhận xét và giới hạn

- Bỏ duration vì chỉ biết sau cuộc gọi; giữ nhãn y: yes=1, no=0.
- Chuỗi 'unknown' là mức danh mục nguồn, không tự coi là số 0.
- Không có mã khách hàng để bảo đảm độc lập theo khách; giữ hạn chế này.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch2_bank_marketing/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch2_bank_marketing](../../references/dataset_cards/v3_eda/ch2_bank_marketing.md).

## A.7. ch3_idrid

Phạm vi: **measured_image**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Porwal, P., Pachade, S., and Kokare, M. (2018). Indian Diabetic Retinopathy Image Dataset (IDRiD). IEEE DataPort. DOI:10.21227/H25W98.](https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid)
Phiên bản: IDRiD original B. Disease Grading ZIP; sha256:8a9f4752b35d74cc35ff48b21ad44f295a6f800110ec218fc2d1c264803e4d8c

Giấy phép/phạm vi: CC BY 4.0, established from bundled IDRiD LICENSE.txt and CC-BY-4.0.txt; exact member hashes in import receipt. Retain authors/citation/license, identify adaptations; no clinical-use claims.

Raw: 212,405,123 byte; 516 fundus RGB images; official 413 train + 103 test.

Số đo và schema phần dùng trong V3:

Bảng A.19. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| images | 516 |
| classes | 5 |
| native_shapes | [[2848, 4288]] |
| model_shape_hwc | [128, 128, 3] |
| label_mapping | {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4"} |
| split | {"path": "data/splits/v3/ch3_idrid/split_contract.json", "sha256": "e4ba938f293fca2787d6670e4f0c989299e90df2c5dbc91081be47ab5160946b", "size_bytes": 1418} |
| matched_subset | {"path": "data/splits/v3/ch3_idrid/matched_train.ids.jsonl.gz", "sha256": "28328c2a0de708b03fd8022efcdaf88beb2c6966007b7c58776d4fe6d19f6847", "size_bytes": 784} |
| counts | {"train": 348, "validation": 64, "test": 103} |
| matched_train_count | 348 |
| quarantine_count | 1 |


#### Mẫu input/output

Mẫu và hình chỉ lấy matched train. known_output là nhãn gốc, không phải dự đoán.

Bảng A.20. Mẫu input/output

| id | input | known_output |
|---|---|---|
| train/IDRiD_001 | {"member": "B. Disease Grading/1. Original Images/a. Training Set/IDRiD_001.jpg", "native_shape": [2848, 4288, 3], "model_shape": [128, 128, 3]} | 3 |
| train/IDRiD_003 | {"member": "B. Disease Grading/1. Original Images/a. Training Set/IDRiD_003.jpg", "native_shape": [2848, 4288, 3], "model_shape": [128, 128, 3]} | 2 |
| train/IDRiD_006 | {"member": "B. Disease Grading/1. Original Images/a. Training Set/IDRiD_006.jpg", "native_shape": [2848, 4288, 3], "model_shape": [128, 128, 3]} | 4 |


#### Phân bố và chất lượng dữ liệu

Bảng A.21. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| class_counts | {"0": 168, "1": 25, "2": 168, "3": 93, "4": 62} |
| class_by_partition | {"train": {"2": 116, "0": 113, "3": 63, "4": 40, "1": 16}, "validation": {"2": 20, "0": 20, "3": 11, "4": 9, "1": 4}, "test": {"0": 34, "2": 32, "3": 19, "4": 13, "1": 5}} |
| decode_or_label_missing | 0 |
| pixel_duplicate_rows | 6 |
| quarantine | 1 |
| outlier_note | IQR brightness/black fraction, no clinical quality claim or row deletion; feature_profile.json |


#### Cách chia tập và tiền xử lý

Gom trùng pixel gốc và sau resize. Nếu có official TEST: giữ nguyên TEST, loại bản trùng TEST khỏi development bằng quarantine; validation chỉ lấy official train. Các phép fit/class weight dùng train. Không có augmentation khác nhau giữa framework.

#### Nhận xét và giới hạn

- Dữ liệu nhỏ và mất cân bằng; nhãn DR grade không phải chẩn đoán cho người dùng.
- Giảm về 128×128 cho track so sánh đã khóa có thể mất chi tiết tổn thương.
- ID gồm split/basename. Không có patient key xác minh; chỉ bảo đảm không trùng pixel giữa tập.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch3_idrid/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch3_idrid](../../references/dataset_cards/v3_eda/ch3_idrid.md).

## A.8. ch3_eurosat

Phạm vi: **measured_image**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Helber, P., Bischke, B., Dengel, A., and Borth, D. (2019). EuroSAT: A Novel Dataset and Deep Learning Benchmark for Land Use and Land Cover Classification. IEEE JSTARS. DOI:10.1109/JSTARS.2019.2918242.](https://zenodo.org/records/7711810/files/EuroSAT_RGB.zip?download=1)
Phiên bản: Zenodo 7711810 v2; RGB only; sha256:b4f5b234ecb7d7ff9c6cddb046543b4717c53fd6e9815be6c0e80cc614f51b90

Giấy phép/phạm vi: MIT confirmed by Zenodo record metadata; also respect Copernicus Sentinel data terms as noted by authors. https://github.com/phelber/EuroSAT ; https://zenodo.org/records/7711810 . Multispectral 2.1 GB package deliberately not downloaded.

Raw: 94,658,721 byte; 27000 RGB image patches.

Số đo và schema phần dùng trong V3:

Bảng A.22. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| images | 27000 |
| classes | 10 |
| native_shapes | [[64, 64]] |
| model_shape_hwc | [32, 32, 3] |
| label_mapping | {"AnnualCrop": "AnnualCrop", "Forest": "Forest", "HerbaceousVegetation": "HerbaceousVegetation", "Highway": "Highway", "Industrial": "Industrial", "Pasture": "Pasture", "PermanentCrop": "PermanentCrop", "Residential": "Residential", "River": "River", "SeaLake": "SeaLake"} |
| split | {"path": "data/splits/v3/ch3_eurosat/split_contract.json", "sha256": "369ba3a92317273cad5340c6a723da12515c95ee545fb64e36fbf1d7d85a8e50", "size_bytes": 1443} |
| matched_subset | {"path": "data/splits/v3/ch3_eurosat/matched_train.ids.jsonl.gz", "sha256": "f3b1bb18695870b08fd2aec5548a79b308df5688570f11a844eacd00680138ec", "size_bytes": 9001} |
| counts | {"train": 18900, "validation": 4050, "test": 4050} |
| matched_train_count | 3000 |
| quarantine_count | 0 |


#### Mẫu input/output

Mẫu và hình chỉ lấy matched train. known_output là nhãn gốc, không phải dự đoán.

Bảng A.23. Mẫu input/output

| id | input | known_output |
|---|---|---|
| EuroSAT_RGB/AnnualCrop/AnnualCrop_1.jpg | {"member": "EuroSAT_RGB/AnnualCrop/AnnualCrop_1.jpg", "native_shape": [64, 64, 3], "model_shape": [32, 32, 3]} | AnnualCrop |
| EuroSAT_RGB/Forest/Forest_100.jpg | {"member": "EuroSAT_RGB/Forest/Forest_100.jpg", "native_shape": [64, 64, 3], "model_shape": [32, 32, 3]} | Forest |
| EuroSAT_RGB/HerbaceousVegetation/HerbaceousVegetation_1003.jpg | {"member": "EuroSAT_RGB/HerbaceousVegetation/HerbaceousVegetation_1003.jpg", "native_shape": [64, 64, 3], "model_shape": [32, 32, 3]} | HerbaceousVegetation |


#### Phân bố và chất lượng dữ liệu

Bảng A.24. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| class_counts | {"AnnualCrop": 3000, "Forest": 3000, "HerbaceousVegetation": 3000, "Highway": 2500, "Industrial": 2500, "Pasture": 2000, "PermanentCrop": 2500, "Residential": 3000, "River": 2500, "SeaLake": 3000} |
| class_by_partition | {"train": {"AnnualCrop": 2100, "Forest": 2100, "HerbaceousVegetation": 2100, "Residential": 2100, "SeaLake": 2100, "Highway": 1750, "Industrial": 1750, "PermanentCrop": 1750, "River": 1750, "Pasture": 1400}, "validation": {"AnnualCrop": 450, "Forest": 450, "HerbaceousVegetation": 450, "Residential": 450, "SeaLake": 450, "Highway": 375, "Industrial": 375, "PermanentCrop": 375, "River": 375, "Pasture": 300}, "test": {" (trích; bản đầy đủ trong nguồn) |
| decode_or_label_missing | 0 |
| pixel_duplicate_rows | 0 |
| quarantine | 0 |
| outlier_note | IQR brightness/black fraction, no clinical quality claim or row deletion; feature_profile.json |


#### Cách chia tập và tiền xử lý

Gom trùng pixel gốc và sau resize. Nếu có official TEST: giữ nguyên TEST, loại bản trùng TEST khỏi development bằng quarantine; validation chỉ lấy official train. Các phép fit/class weight dùng train. Không có augmentation khác nhau giữa framework.

#### Nhận xét và giới hạn

- Ảnh RGB 64×64 gốc, track so sánh dùng 32×32 như protocol.
- Không có tọa độ/group địa lý được xác minh trong gói này; split không chứng minh độc lập không gian.
- Kiểm trùng pixel gốc và sau resize, không tự lọc ảnh theo kết quả mô hình.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch3_eurosat/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch3_eurosat](../../references/dataset_cards/v3_eda/ch3_eurosat.md).

## A.9. ch3_cifar10

Phạm vi: **measured_image**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Krizhevsky, A. (2009). Learning Multiple Layers of Features from Tiny Images. University of Toronto technical report.](https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz)
Phiên bản: CIFAR-10 original binary release 2009; not Python pickle; sha256:c4a38c50a1bc5f3a1c5537f2155ab9d68f9f25eb1ed8d9ddda3db29a59bca1dd

Giấy phép/phạm vi: Author-hosted public research benchmark; author requests citation. No explicit SPDX license asserted. Local academic analysis only; no raw redistribution. https://www.cs.toronto.edu/~kriz/cifar.html

Raw: 170,052,171 byte; 60000 images (50000 train + 10000 test).

Số đo và schema phần dùng trong V3:

Bảng A.25. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| images | 60000 |
| classes | 10 |
| native_shapes | [[32, 32]] |
| model_shape_hwc | [32, 32, 3] |
| label_mapping | {"0": "airplane", "1": "automobile", "2": "bird", "3": "cat", "4": "deer", "5": "dog", "6": "frog", "7": "horse", "8": "ship", "9": "truck"} |
| split | {"path": "data/splits/v3/ch3_cifar10/split_contract.json", "sha256": "f7ac586f8cb07a23333d64c0fa238936c026b178c52add74299711111a7dd755", "size_bytes": 1436} |
| matched_subset | {"path": "data/splits/v3/ch3_cifar10/matched_train.ids.jsonl.gz", "sha256": "96bc6a3da4112ba292a6d2e95b999bede66bfdeefb5468af7ad277b8ec17579b", "size_bytes": 13588} |
| counts | {"train": 45000, "validation": 5000, "test": 10000} |
| matched_train_count | 5000 |
| quarantine_count | 0 |


#### Mẫu input/output

Mẫu và hình chỉ lấy matched train. known_output là nhãn gốc, không phải dự đoán.

Bảng A.26. Mẫu input/output

| id | input | known_output |
|---|---|---|
| data_batch_1.bin/00026 | {"member": "cifar-10-batches-bin/data_batch_1.bin", "native_shape": [32, 32, 3], "model_shape": [32, 32, 3]} | 3 |
| data_batch_1.bin/00028 | {"member": "cifar-10-batches-bin/data_batch_1.bin", "native_shape": [32, 32, 3], "model_shape": [32, 32, 3]} | 4 |
| data_batch_1.bin/00029 | {"member": "cifar-10-batches-bin/data_batch_1.bin", "native_shape": [32, 32, 3], "model_shape": [32, 32, 3]} | 0 |


#### Phân bố và chất lượng dữ liệu

Bảng A.27. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| class_counts | {"0": 6000, "1": 6000, "2": 6000, "3": 6000, "4": 6000, "5": 6000, "6": 6000, "7": 6000, "8": 6000, "9": 6000} |
| class_by_partition | {"train": {"6": 4500, "9": 4500, "4": 4500, "1": 4500, "2": 4500, "7": 4500, "8": 4500, "3": 4500, "5": 4500, "0": 4500}, "validation": {"9": 500, "3": 500, "7": 500, "2": 500, "4": 500, "6": 500, "1": 500, "5": 500, "0": 500, "8": 500}, "test": {"3": 1000, "8": 1000, "0": 1000, "6": 1000, "1": 1000, "9": 1000, "5": 1000, "7": 1000, "4": 1000, "2": 1000}} |
| decode_or_label_missing | 0 |
| pixel_duplicate_rows | 0 |
| quarantine | 0 |
| outlier_note | IQR brightness/black fraction, no clinical quality claim or row deletion; feature_profile.json |


#### Cách chia tập và tiền xử lý

Gom trùng pixel gốc và sau resize. Nếu có official TEST: giữ nguyên TEST, loại bản trùng TEST khỏi development bằng quarantine; validation chỉ lấy official train. Các phép fit/class weight dùng train. Không có augmentation khác nhau giữa framework.

#### Nhận xét và giới hạn

- Giữ nguyên 10.000 ảnh official TEST, kể cả bản trùng trong chính TEST.
- Ảnh official train trùng pixel với TEST phải quarantine, không được âm thầm chuyển/xóa TEST.
- Đọc binary, không dùng pickle; test chỉ được đánh giá sau khi khóa release thí nghiệm.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch3_cifar10/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch3_cifar10](../../references/dataset_cards/v3_eda/ch3_cifar10.md).

## A.10. ch4_gold_pink_sheet

Phạm vi: **measured_timeseries**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [World Bank (2026). Commodity Price Data (The Pink Sheet), historical monthly data, October 2026 snapshot.](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx)
Phiên bản: Pink Sheet October 2026 historical monthly workbook; latest revised vintage; sha256:ea1c350827878ea3bbe30e3cda16a13fd3bd5b409b8458940dc94a36b5a33154

Giấy phép/phạm vi: World Bank Commodity Prices - History and Projections catalog: CC BY 4.0. https://datacatalog.worldbank.org/search/dataset/0038238/commodity-prices-history-and-projections . Attribute World Bank and preserve unit/source notes. Not a real-time vintage.

Raw: 586,099 byte; 801 monthly observations, latest revised vintage.

Số đo và schema phần dùng trong V3:

Bảng A.28. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| canonical_time_rows | 801 |
| series | 1 |
| features | ["gold", "silver_lag1", "platinum_lag1", "crude_oil_lag1"] |
| lookback | 24 |
| horizons | [1, 3, 6] |
| range | ["1960-01-01 00:00:00", "2026-09-01 00:00:00"] |
| source_clock | calendar markers; power civil clock as recorded, timezone/DST not reconstructed |
| contract_time_encoding | +00:00 is a normalized calendar coordinate for schema/ordering, NOT a claim that source measurements were timestamped in UTC |
| valid_windows | 762 |
| split | {"path": "data/splits/v3/ch4_gold_pink_sheet/split_contract.json", "sha256": "91a1fb8d745b1017b056636d2d90c6ec3da35ce27b7c046a8045cf8d29f51ddb", "size_bytes": 1578} |
| matched_subset | {"path": "data/splits/v3/ch4_gold_pink_sheet/matched_train.ids.jsonl.gz", "sha256": "c9b193cc6d8d16d76c4d1343fbf7aa71723a01bbdbb0bf0e861a6f3a3ceab60a", "size_bytes": 1216} |
| counts | {"train": 531, "validation": 115, "test": 116} |
| matched_train_count | 531 |
| quarantine_count | 0 |


#### Mẫu input/output

Mẫu window thuộc matched train; known_output là giá trị tương lai đã có trong nguồn train, không phải dự đoán. Target thiếu không bao giờ được điền.

Bảng A.29. Mẫu input/output

| id | input | known_output |
|---|---|---|
| GOLD/1961-12-01T00:00:00 | {"context_start": "1960-01-01T00:00:00", "context_end": "1961-12-01T00:00:00", "last_values": {"gold": 35.0, "silver_lag1": 0.9, "platinum_lag1": 84.0, "crude_oil_lag1": 1.6}} | {"horizons": [1, 3, 6], "target_times": ["1962-01-01T00:00:00", "1962-03-01T00:00:00", "1962-06-01T00:00:00"], "values": [35, 35, 35]} |
| GOLD/1962-01-01T00:00:00 | {"context_start": "1960-02-01T00:00:00", "context_end": "1962-01-01T00:00:00", "last_values": {"gold": 35.0, "silver_lag1": 1.0, "platinum_lag1": 84.0, "crude_oil_lag1": 1.6}} | {"horizons": [1, 3, 6], "target_times": ["1962-02-01T00:00:00", "1962-04-01T00:00:00", "1962-07-01T00:00:00"], "values": [35, 35, 35]} |
| GOLD/1962-02-01T00:00:00 | {"context_start": "1960-03-01T00:00:00", "context_end": "1962-02-01T00:00:00", "last_values": {"gold": 35.0, "silver_lag1": 1.0, "platinum_lag1": 84.0, "crude_oil_lag1": 1.5}} | {"horizons": [1, 3, 6], "target_times": ["1962-03-01T00:00:00", "1962-05-01T00:00:00", "1962-08-01T00:00:00"], "values": [35, 35, 35]} |


#### Phân bố và chất lượng dữ liệu

Bảng A.30. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| target_observed_summary | {"count": 801.0, "mean": 668.4631710362047, "std": 794.7810210708558, "min": 35.0, "25%": 159.0, "50%": 379.0, "75%": 1095.0, "max": 5020.0} |
| missing_target_rows | 0 |
| calendar_boundaries | ["2006-08-01T00:00:00", "2016-08-01T00:00:00"] |
| excluded_windows | {"cross_boundary": 10, "missing_target": 0, "unresolved_input": 0} |
| selected_series_count | 1 |
| per_series_counts | {"GOLD": 801} |
| selection | {"publication_lag": "explanatory commodities lagged one month; revised vintage, not realtime"} |


#### Cách chia tập và tiền xử lý

Split 70/15/15 theo lịch target chung. Mọi horizon của window phải ở cùng partition; context chỉ dùng quan sát trước target. Scaler/imputer chính fit prefix train, riêng từng rolling fold fit prefix của chính fold; không fit validation/test. Matched cap chỉ áp dụng train; giữ full validation/test. TEST RNN/LSTM mở chung ở Phase29 sau khóa cả hai họ.

#### Nhận xét và giới hạn

- Giá vàng USD/troy ounce; silver/platinum/crude oil giữ đơn vị nguồn và trễ một tháng.
- Snapshot đã chỉnh sửa hồi tố, không phải mô phỏng dữ liệu sẵn có theo vintage tại thời điểm thật.
- Chuỗi tháng ít mẫu; không tuyên bố khả năng giao dịch hoặc khuyến nghị đầu tư.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch4_gold_pink_sheet/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch4_gold_pink_sheet](../../references/dataset_cards/v3_eda/ch4_gold_pink_sheet.md).

## A.11. ch4_bis_house_prices

Phạm vi: **measured_timeseries**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Bank for International Settlements (2026). Selected residential property prices (WS_SPP), BIS Data Portal; underlying national sources.](https://data.bis.org/static/bulk/WS_SPP_csv_col.zip)
Phiên bản: BIS WS_SPP selected residential property prices bulk snapshot; sha256:2ef20238c23983100a3ded6c1398a6026b3a18fe6b898520df2738c80d1aaebd

Giấy phép/phạm vi: BIS Terms of permitted use of statistics, not CC BY assumed. https://www.bis.org/about/legal/permitted-use-statistics ; attribute BIS and original national sources, label own calculations, do not imply endorsement. No raw redistribution in this repo.

Raw: 135,216 byte; 35780 nonmissing quarterly series-observations in entire raw bulk (not selected nominal panel).

Số đo và schema phần dùng trong V3:

Bảng A.31. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| canonical_time_rows | 4689 |
| series | 49 |
| features | ["house_index", "index_change", "country_AT", "country_AU", "country_BE", "country_BG", "country_BR", "country_CA", "country_CH", "country_CL", "country_CN", "country_CO", "country_CY", "country_DE", "country_DK", "country_EE", "country_ES", "country_FI", "country_FR", "country_GB", "country_GR", "country_HK", "country_HR", "country_HU", "country_ID", "country_IE", "country_IL", "country_IS", "country_IT", "country_J (trích; bản đầy đủ trong nguồn) |
| lookback | 12 |
| horizons | [1, 2, 4] |
| range | ["2002-01-01 00:00:00", "2026-04-01 00:00:00"] |
| source_clock | calendar markers; power civil clock as recorded, timezone/DST not reconstructed |
| contract_time_encoding | +00:00 is a normalized calendar coordinate for schema/ordering, NOT a claim that source measurements were timestamped in UTC |
| valid_windows | 3660 |
| split | {"path": "data/splits/v3/ch4_bis_house_prices/split_contract.json", "sha256": "0525c25465cff66163dacd4d764c15707e216a3739762d28be08c0c222651e34", "size_bytes": 1585} |
| matched_subset | {"path": "data/splits/v3/ch4_bis_house_prices/matched_train.ids.jsonl.gz", "sha256": "5860881735bf9b4e2d4864cce30c2f44313c635fdd4ce335a60c3512c4bca65e", "size_bytes": 6946} |
| counts | {"train": 2504, "validation": 588, "test": 568} |
| matched_train_count | 2504 |
| quarantine_count | 0 |


#### Mẫu input/output

Mẫu window thuộc matched train; known_output là giá trị tương lai đã có trong nguồn train, không phải dự đoán. Target thiếu không bao giờ được điền.

Bảng A.32. Mẫu input/output

| id | input | known_output |
|---|---|---|
| Q.AT.N.628/2004-10-01T00:00:00 | {"context_start": "2002-01-01T00:00:00", "context_end": "2004-10-01T00:00:00", "last_values": {"house_index": 80.8486, "index_change": 1.7286000000000001, "country_AT": 1.0, "country_AU": 0.0}} | {"horizons": [1, 2, 4], "target_times": ["2005-01-01T00:00:00", "2005-04-01T00:00:00", "2005-10-01T00:00:00"], "values": [81.1628, 81.9485, 83.9914]} |
| Q.AT.N.628/2005-01-01T00:00:00 | {"context_start": "2002-04-01T00:00:00", "context_end": "2005-01-01T00:00:00", "last_values": {"house_index": 81.1628, "index_change": 0.3141999999999996, "country_AT": 1.0, "country_AU": 0.0}} | {"horizons": [1, 2, 4], "target_times": ["2005-04-01T00:00:00", "2005-07-01T00:00:00", "2006-01-01T00:00:00"], "values": [81.9485, 82.0271, 84.9342]} |
| Q.AT.N.628/2005-04-01T00:00:00 | {"context_start": "2002-07-01T00:00:00", "context_end": "2005-04-01T00:00:00", "last_values": {"house_index": 81.9485, "index_change": 0.7856999999999914, "country_AT": 1.0, "country_AU": 0.0}} | {"horizons": [1, 2, 4], "target_times": ["2005-07-01T00:00:00", "2005-10-01T00:00:00", "2006-04-01T00:00:00"], "values": [82.0271, 83.9914, 85.6413]} |


#### Phân bố và chất lượng dữ liệu

Bảng A.33. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| target_observed_summary | {"count": 4689.0, "mean": 124.86578741735978, "std": 53.5634477795657, "min": 16.4856, "25%": 92.7579, "50%": 107.6851, "75%": 151.6941, "max": 416.5466} |
| missing_target_rows | 0 |
| calendar_boundaries | ["2018-10-01T00:00:00", "2022-07-01T00:00:00"] |
| excluded_windows | {"cross_boundary": 294, "missing_target": 0, "unresolved_input": 0} |
| selected_series_count | 49 |
| per_series_counts | {"Q.AT.N.628": 98, "Q.AU.N.628": 98, "Q.BE.N.628": 97, "Q.BG.N.628": 97, "Q.BR.N.628": 98, "Q.CA.N.628": 98, "Q.CH.N.628": 98, "Q.CL.N.628": 97, "Q.CN.N.628": 85, "Q.CO.N.628": 97, "Q.CY.N.628": 97, "Q.DE.N.628": 97, "Q.DK.N.628": 97, "Q.EE.N.628": 85, "Q.ES.N.628": 97, "Q.FI.N.628": 97, "Q.FR.N.628": 98, "Q.GB.N.628": 98, "Q.GR.N.628": 98, "Q.HK.N.628": 98, "Q.HR.N.628": 97, "Q.HU.N.628": 97, "Q.ID.N.628": 98, "Q.IE (trích; bản đầy đủ trong nguồn) |
| selection | {"retained_series": ["Q.AT.N.628", "Q.AU.N.628", "Q.BE.N.628", "Q.BG.N.628", "Q.BR.N.628", "Q.CA.N.628", "Q.CH.N.628", "Q.CL.N.628", "Q.CN.N.628", "Q.CO.N.628", "Q.CY.N.628", "Q.DE.N.628", "Q.DK.N.628", "Q.EE.N.628", "Q.ES.N.628", "Q.FI.N.628", "Q.FR.N.628", "Q.GB.N.628", "Q.GR.N.628", "Q.HK.N.628", "Q.HR.N.628", "Q.HU.N.628", "Q.ID.N.628", "Q.IE.N.628", "Q.IL.N.628", "Q.IS.N.628", "Q.IT.N.628", "Q.JP.N.628", "Q.KR.N (trích; bản đầy đủ trong nguồn) |


#### Cách chia tập và tiền xử lý

Split 70/15/15 theo lịch target chung. Mọi horizon của window phải ở cùng partition; context chỉ dùng quan sát trước target. Scaler/imputer chính fit prefix train, riêng từng rolling fold fit prefix của chính fold; không fit validation/test. Matched cap chỉ áp dụng train; giữ full validation/test. TEST RNN/LSTM mở chung ở Phase29 sau khóa cả hai họ.

#### Nhận xét và giới hạn

- Chỉ VALUE=N và UNIT_MEASURE=628, chỉ số danh nghĩa 2010=100, không trộn Real/YoY.
- Loại aggregate; điều kiện coverage >=80, chọn lịch sử chung theo độ phủ 80% quốc gia, không theo giá trị/metric TEST.
- Bản đã revision, không có vintage/release calendar thật; kết quả là hồi cứu. Chỉ số khác giá nhà USD của Ames.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch4_bis_house_prices/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch4_bis_house_prices](../../references/dataset_cards/v3_eda/ch4_bis_house_prices.md).

## A.12. ch4_household_power

Phạm vi: **measured_timeseries**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Hebrail, G. and Berard, A. (2006). Individual Household Electric Power Consumption. UCI. DOI:10.24432/C58K54.](https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip)
Phiên bản: UCI 235 original minute-resolution household power release; sha256:9f84b46ade8a2d8e1286ec4b2b6c2987a45a755c59f263be3b3b3d10dfbda3ff

Giấy phép/phạm vi: CC BY 4.0. https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption . Single household, not population-independent evidence.

Raw: 20,640,916 byte; 2075259 raw minute rows, NOT hourly training windows.

Số đo và schema phần dùng trong V3:

Bảng A.34. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| canonical_time_rows | 34589 |
| series | 1 |
| features | ["Global_active_power", "Global_active_power_missing", "Global_reactive_power", "Global_reactive_power_missing", "Voltage", "Voltage_missing", "Global_intensity", "Global_intensity_missing", "Sub_metering_1", "Sub_metering_1_missing", "Sub_metering_2", "Sub_metering_2_missing", "Sub_metering_3", "Sub_metering_3_missing"] |
| lookback | 168 |
| horizons | [1, 6, 24] |
| range | ["2006-12-16 17:00:00", "2010-11-26 21:00:00"] |
| source_clock | calendar markers; power civil clock as recorded, timezone/DST not reconstructed |
| contract_time_encoding | +00:00 is a normalized calendar coordinate for schema/ordering, NOT a claim that source measurements were timestamped in UTC |
| valid_windows | 33741 |
| split | {"path": "data/splits/v3/ch4_household_power/split_contract.json", "sha256": "90053761ae0a15d0faa3323fb1a1261425d5204ab0e74416c225613e68f498b8", "size_bytes": 1582} |
| matched_subset | {"path": "data/splits/v3/ch4_household_power/matched_train.ids.jsonl.gz", "sha256": "f6de2e1df1ddc0a78130d7bd5ccfe432dc94f143f295d176076ddd3049750a72", "size_bytes": 30872} |
| counts | {"train": 23797, "validation": 5033, "test": 4911} |
| matched_train_count | 12000 |
| quarantine_count | 0 |


#### Mẫu input/output

Mẫu window thuộc matched train; known_output là giá trị tương lai đã có trong nguồn train, không phải dự đoán. Target thiếu không bao giờ được điền.

Bảng A.35. Mẫu input/output

| id | input | known_output |
|---|---|---|
| HOUSEHOLD/2006-12-23T20:00:00 | {"context_start": "2006-12-16T21:00:00", "context_end": "2006-12-23T20:00:00", "last_values": {"Global_active_power": 4.1814, "Global_active_power_missing": 0.0, "Global_reactive_power": 0.12476666666666666, "Global_reactive_power_missing": 0.0}} | {"horizons": [1, 6, 24], "target_times": ["2006-12-23T21:00:00", "2006-12-24T02:00:00", "2006-12-24T20:00:00"], "values": [3.2884333333333333, 2.303033333333333, 0.4741]} |
| HOUSEHOLD/2006-12-23T23:00:00 | {"context_start": "2006-12-17T00:00:00", "context_end": "2006-12-23T23:00:00", "last_values": {"Global_active_power": 5.5624666666666664, "Global_active_power_missing": 0.0, "Global_reactive_power": 0.12806666666666666, "Global_reactive_power_missing": 0.0}} | {"horizons": [1, 6, 24], "target_times": ["2006-12-24T00:00:00", "2006-12-24T05:00:00", "2006-12-24T23:00:00"], "values": [4.0280000000000005, 1.6319000000000001, 0.48633333333333334]} |
| HOUSEHOLD/2006-12-24T00:00:00 | {"context_start": "2006-12-17T01:00:00", "context_end": "2006-12-24T00:00:00", "last_values": {"Global_active_power": 4.0280000000000005, "Global_active_power_missing": 0.0, "Global_reactive_power": 0.09066666666666667, "Global_reactive_power_missing": 0.0}} | {"horizons": [1, 6, 24], "target_times": ["2006-12-24T01:00:00", "2006-12-24T06:00:00", "2006-12-25T00:00:00"], "values": [3.2757, 1.8952, 0.9995666666666667]} |


#### Phân bố và chất lượng dữ liệu

Bảng A.36. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| target_observed_summary | {"count": 34151.0, "mean": 1.0916107761526015, "std": 0.8975997510598066, "min": 0.12400000000000001, "25%": 0.3419, "50%": 0.8026666666666666, "75%": 1.5792666666666666, "max": 6.560533333333334} |
| missing_target_rows | 438 |
| calendar_boundaries | ["2009-09-20T12:00:00", "2010-04-24T16:00:00"] |
| excluded_windows | {"cross_boundary": 46, "missing_target": 611, "unresolved_input": 0} |
| selected_series_count | 1 |
| per_series_counts | {"HOUSEHOLD": 34151} |
| selection | {"raw_minute_rows": 2075259, "observed_minute_threshold": 45, "input_ffill_hours": 6, "target_imputation": "never", "sensor_units": {"Global_active_power": "kW", "Global_reactive_power": "kVAR", "Voltage": "V", "Global_intensity": "A", "Sub_metering_1/2/3": "Wh/min observations, hourly mean not summed kWh"}} |


#### Cách chia tập và tiền xử lý

Split 70/15/15 theo lịch target chung. Mọi horizon của window phải ở cùng partition; context chỉ dùng quan sát trước target. Scaler/imputer chính fit prefix train, riêng từng rolling fold fit prefix của chính fold; không fit validation/test. Matched cap chỉ áp dụng train; giữ full validation/test. TEST RNN/LSTM mở chung ở Phase29 sau khóa cả hai họ.

#### Nhận xét và giới hạn

- Đích là kW trung bình giờ, không phải kWh. Một giờ cần >=45 phút quan sát.
- Không điền nhãn thiếu. Chỉ input ffill tối đa 6 giờ, sau đó imputer fit train và kèm cờ thiếu.
- Một hộ gia đình, không bảo đảm tổng quát hóa cho hộ khác; không shuffle thời gian.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch4_household_power/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch4_household_power](../../references/dataset_cards/v3_eda/ch4_household_power.md).

## A.13. ch5_medquad_diabetes

Phạm vi: **historical_baseline_READ_ONLY**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Abacha, A. and Demner-Fushman, D. (2019). A question-entailment approach to question answering. BMC Bioinformatics 20:511. MedQuAD.](https://github.com/abachaa/MedQuAD)
Phiên bản: 577bd37b96c02d1833b2c9eed2de9f96964e96cb

Giấy phép/phạm vi: CC BY 4.0; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution. Some copyrighted upstream answers were removed by MedQuAD; empty answers must not be reconstructed from another source.

Raw: 37,183,352 byte; 47441 QA pairs in entire preserved upstream corpus, NOT diabetes-only split.

Số đo và schema phần dùng trong V3:

Bảng A.37. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| records | 47441 |
| features | null |
| unit | QA pairs in entire preserved upstream corpus, NOT diabetes-only split |
| frozen_slice | {"candidate_records": 274, "deduplicated_queries": 247, "exact_duplicates_removed": 27, "documents": 247, "chunks": 762, "queries": 247, "evidence": 762, "groups": 62, "split_distribution": {"test": 62, "train": 152, "validation": 33}} |


#### Mẫu input/output

FinQA: raw official train. MedQuAD: ánh xạ ID -> trích đoạn corpus retrieval công khai đã đóng gói, không gán train/test vì bundle không có split, không phải QA gold hay output mô hình. Wikidata: cấu trúc snapshot. Không đọc lại TEST query/prediction để tạo ví dụ hay tính metric.

Bảng A.38. Mẫu input/output

| input | known_output | scope |
|---|---|---|
| med-chunk-007e45eccdb7816d5e0c | - Starting a physical activity program can help you lose weight or keep a healthy weight and keep your blood glucose levels on target. - Always talk with your health care team before you start a new physical activity program. - Ask your health care team if you need to change the amount of medicine you take or the food you eat before any physical activity. - Talk with your health care team about what types of physical (trích; bản đầy đủ trong nguồn) | published retrieval corpus evidence, benchmark question split unknown; not a QA query/gold or model output |
| med-chunk-00bc631490478ac2cf94 | well. Children have a higher risk of type 2 diabetes if they are obese, have a family history of diabetes, or are not active, and do not eat well. To lower the risk of type 2 diabetes in children - Have them maintain a healthy weight - Be sure they are physically active - Have them eat smaller portions of healthy foods - Limit time with the TV, computer, and video Children and teens with type 1 diabetes may need to t (trích; bản đầy đủ trong nguồn) | published retrieval corpus evidence, benchmark question split unknown; not a QA query/gold or model output |
| med-chunk-00d0cff90bb719155edf | healthy tissues by mistake, signaling the body to attack them. At present, scientists do not know exactly what causes the body's immune system to attack the cells, but many believe that both genetic factors and environmental factors, such as viruses, are involved. Studies are now underway to identify these factors and prevent type 1 diabetes in people at risk. Learn more about the causes of type 1 diabetes. Type 2 Di (trích; bản đầy đủ trong nguồn) | published retrieval corpus evidence, benchmark question split unknown; not a QA query/gold or model output |


#### Phân bố và chất lượng dữ liệu

Bảng A.39. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| test | 62 |
| train | 152 |
| validation | 33 |


#### Cách chia tập và tiền xử lý

Kế thừa manifest Phase12 và audit đã khóa; không chia lại, fit lại hay chạy TEST. Ch5 run_count vẫn 1; Wikidata chỉ structural audit.

#### Nhận xét và giới hạn

- Nguồn upstream có 47.441 QAPair, nhưng lát cắt diabetes khóa chỉ 247 query/62 nhóm; không đánh đồng hai mẫu số.
- Kế thừa 27 bản trùng đã loại và split 152/33/62; không rebuild filter/split hoặc đánh giá lại TEST.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch5_medquad_diabetes/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch5_medquad_diabetes](../../references/dataset_cards/v3_eda/ch5_medquad_diabetes.md).

## A.14. ch5_finqa

Phạm vi: **historical_baseline_READ_ONLY**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Chen, Z. et al. (2021). FinQA: A Dataset of Numerical Reasoning over Financial Data. EMNLP. https://aclanthology.org/2021.emnlp-main.300/](https://github.com/czyssrs/FinQA)
Phiên bản: 0f16e2867befa6840783e58be38c9efb9229d742

Giấy phép/phạm vi: MIT; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution.

Raw: 122,256,362 byte; 9200 raw QA records including private_test.

Số đo và schema phần dùng trong V3:

Bảng A.40. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| records | 9200 |
| features | null |
| unit | raw QA records including private_test |
| frozen_slice | {"documents": 2789, "chunks": 86421, "queries": 9200, "evidence": 14108, "split_distribution": {"private_test": 919, "test": 1147, "train": 6251, "validation": 883}, "document_split_distribution": {"test": 380, "train": 2110, "validation": 299}, "page_group_distribution": {"private_test": 303, "test": 380, "train": 2110, "validation": 299}, "public_page_group_overlaps": {"train__validation": 0, "train__test": 0, "val (trích; bản đầy đủ trong nguồn) |


#### Mẫu input/output

FinQA: raw official train. MedQuAD: ánh xạ ID -> trích đoạn corpus retrieval công khai đã đóng gói, không gán train/test vì bundle không có split, không phải QA gold hay output mô hình. Wikidata: cấu trúc snapshot. Không đọc lại TEST query/prediction để tạo ví dụ hay tính metric.

Bảng A.41. Mẫu input/output

| input | known_output |
|---|---|
| what is the the interest expense in 2009? | {"answer": "380", "program": "divide(100, 100), divide(3.8, #0)"} |
| during the 2012 year , did the equity awards in which the prescribed performance milestones were achieved exceed the equity award compensation expense for equity granted during the year? | {"answer": "", "program": "multiply(607, 18.13), multiply(#0, const_1000), multiply(3.3, const_1000000), greater(#1, #2)"} |
| what was the total operating expenses in 2018 in millions | {"answer": "41932", "program": "divide(9896, 23.6%)"} |


#### Phân bố và chất lượng dữ liệu

Bảng A.42. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| private_test | 919 |
| test | 1147 |
| train | 6251 |
| validation | 883 |


#### Cách chia tập và tiền xử lý

Kế thừa manifest Phase12 và audit đã khóa; không chia lại, fit lại hay chạy TEST. Ch5 run_count vẫn 1; Wikidata chỉ structural audit.

#### Nhận xét và giới hạn

- Re-use split/audit Phase12. Private_test tồn tại trong raw nhưng không phải nhãn được phép đánh giá.
- Page-group overlap giữa các public split =0, nhưng report-key overlap khác 0 (197/243/93); không tuyên bố độc lập theo công ty/báo cáo.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch5_finqa/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch5_finqa](../../references/dataset_cards/v3_eda/ch5_finqa.md).

## A.15. ch5_wikidata_subgraphs

Phạm vi: **historical_baseline_READ_ONLY**. Không huấn luyện hay đánh giá TEST trong Phase 24.

#### Nguồn, kích cỡ và cấu trúc

Nguồn: [Wikidata contributors. EntityData snapshots, exact revision IDs in Phase11 snapshot manifest.](https://www.wikidata.org/wiki/Wikidata:Data_access)
Phiên bản: Phase11 exact Wikidata revision IDs

Giấy phép/phạm vi: CC0 1.0; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution.

Raw: 3,528,666 byte; 10 narrow entity snapshots, not a QA benchmark.

Số đo và schema phần dùng trong V3:

Bảng A.43. Nguồn, kích cỡ và cấu trúc

| Trường | Giá trị |
|---|---|
| records | 10 |
| features | null |
| unit | narrow entity snapshots, not a QA benchmark |
| frozen_slice | {"records": 10, "features": null, "unit": "narrow entity snapshots, not a QA benchmark", "columns": [], "claims": 2056, "checks": ["revision_snapshot_hashes", "all_raw_files_match_phase20_baseline"], "deferred": "Structural/provenance audit only; not an invented third QA TEST dataset."} |


#### Mẫu input/output

FinQA: raw official train. MedQuAD: ánh xạ ID -> trích đoạn corpus retrieval công khai đã đóng gói, không gán train/test vì bundle không có split, không phải QA gold hay output mô hình. Wikidata: cấu trúc snapshot. Không đọc lại TEST query/prediction để tạo ví dụ hay tính metric.

Bảng A.44. Mẫu input/output

| input | known_output |
|---|---|
| Q12206 | {"revision": 2554502707, "claim_count": 186, "property_ids": ["P10283", "P1036", "P10376", "P1051", "P10565"]} |
| Q124407 | {"revision": 2556005597, "claim_count": 125, "property_ids": ["P10283", "P10376", "P10380", "P11143", "P11196"]} |
| Q192907 | {"revision": 2556173446, "claim_count": 70, "property_ids": ["P1014", "P10283", "P1036", "P10376", "P10565"]} |


#### Phân bố và chất lượng dữ liệu

Bảng A.45. Phân bố và chất lượng dữ liệu

| Trường | Giá trị |
|---|---|
| Q12206 | 186 |
| Q124407 | 125 |
| Q192907 | 70 |
| Q271993 | 62 |
| Q3025883 | 161 |
| Q312 | 1219 |
| Q50265665 | 125 |
| Q570938 | 18 |
| Q699735 | 51 |
| Q850210 | 39 |


#### Cách chia tập và tiền xử lý

Kế thừa manifest Phase12 và audit đã khóa; không chia lại, fit lại hay chạy TEST. Ch5 run_count vẫn 1; Wikidata chỉ structural audit.

#### Nhận xét và giới hạn

- KG hỗ trợ với 10 entity/2.056 claim, không phải benchmark QA thứ ba.
- Giữ revision/hash nguồn, chỉ audit cấu trúc; không thực hiện truy vấn web mới.

#### Bằng chứng tái lập

Chi tiết: `artifacts/manifests/phase24/ch5_wikidata_subgraphs/eda.json`.
Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.

Bản đầy đủ đã khóa: [ch5_wikidata_subgraphs](../../references/dataset_cards/v3_eda/ch5_wikidata_subgraphs.md).

## A.16. ch6_diabetes_tasks

100 task synthetic-template trên nguồn thật;60/20/20 theo nhóm. Không phải100 người bệnh/căn nhà mới.

Bảng A.46. A.16. ch6_diabetes_tasks

| Parent | Link snapshot | Điều khoản/citation | Raw parent bytes (không copy) |
|---|---|---|---|
| ch2_cdc_diabetes | https://archive.ics.uci.edu/static/public/891/data.csv | UCI directs licensing to upstream Kaggle; public Kaggle API confirms CC0: Public Domain. https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset . Not assumed to inherit UCI's default CC BY license. | 13494568 |
| ch5_medquad_diabetes | https://github.com/abachaa/MedQuAD | CC BY 4.0; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution. Some copyrighted upstream answers were removed by MedQuAD; empty answers must not be reconstructed from another source. | 37183352 |

Task set dùng chung3 miền: `artifacts/manifests/phase31/taskset_v2.json`, 401318 byte, SHA-256 `8741c1165c77fe8d67ba262a193ddebdd044b45eebf3a8bc0318255123ee23ab`.
Catalog canonical input/evidence dùng chung:60 record/miền (40 numeric +20 evidence). Không nhân bản raw.

Schema: request(task_id, domain_hint, question, record_id, operation); split/group/source_group/fault/gold chỉ harness. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có20 task, mỗi split12/4/4. Group nguyên template và source/document, overlap0.

Bảng A.47. A.16. ch6_diabetes_tasks

| Task | Input câu hỏi (synthetic) | Output số thật từ tool | Trích output tool/evidence |
|---|---|---|---|
| diabetes_numeric_f1_1 | tiểu đường: tính đầu ra checkpoint cho bản ghi diabetes_numeric_000. | [0.25386870685992713] | Frozen NumPy CPU tool output: 0.25386871 |
| diabetes_numeric_f1_2 | tiểu đường: tính đầu ra checkpoint cho bản ghi diabetes_numeric_001. | [0.18886305152266863] | Frozen NumPy CPU tool output: 0.18886305 |
| diabetes_numeric_f1_3 | tiểu đường: tính đầu ra checkpoint cho bản ghi diabetes_numeric_002. | [0.5895465273834898] | Frozen NumPy CPU tool output: 0.58954653 |
| diabetes_evidence_f1_1 | tiểu đường: tìm bằng chứng snapshot cho mã diabetes_evidence_000. | [] | - If you have diabetes, you are at least twice as likely as other people to have heart disease or a stroke. - Controlling the ABCs of diabetesA1C (blood glucose |
| diabetes_evidence_f1_2 | tiểu đường: tìm bằng chứng snapshot cho mã diabetes_evidence_001. | [] | are key to a healthy diet. Make healthy food choices. What you eat has a big impact on your weight and overall health. By developing healthy eating habits you c |

Không thiếu task/gold. Numeric dùng parent TRAIN; Gold window có thể chồng context. MedQuAD chỉ corpus evidence, không QA TEST label. Policy/challenge là ca tổng hợp đã gắn nhãn, không phân bố nhu cầu thực. Gold numeric parity là khớp tool, không predictive accuracy.

Nhận xét: thiết kế cân bằng thuận tiện kiểm pipeline nhưng nhỏ, rule/ID-bound, không chứng minh hiểu ngôn ngữ tự do. Ames là USD giá bán lịch sử; BIS là chỉ số danh nghĩa2010=100, không so trực tiếp hai đơn vị. CDC probability không phải chẩn đoán; Pink Sheet không phải giá giao dịch hiện tại. Citation hash kiểm local container, URL cấp nguồn.

Bản đầy đủ đã khóa: [ch6_diabetes_tasks](../../references/dataset_cards/v3_agent/ch6_diabetes_tasks.md).

## A.17. ch6_house_tasks

100 task synthetic-template trên nguồn thật;60/20/20 theo nhóm. Không phải100 người bệnh/căn nhà mới.

Bảng A.48. A.17. ch6_house_tasks

| Parent | Link snapshot | Điều khoản/citation | Raw parent bytes (không copy) |
|---|---|---|---|
| ch2_ames_housing | https://jse.amstat.org/v19n3/decock/AmesHousing.txt | Author-published teaching/research dataset accompanying JSE article; retain attribution; no explicit SPDX license on original TXT. GPL-2 in topepo/AmesHousing applies to that package, not automatically to this original source. Local academic analysis only; no raw redistribution. | 960807 |
| ch4_bis_house_prices | https://data.bis.org/static/bulk/WS_SPP_csv_col.zip | BIS Terms of permitted use of statistics, not CC BY assumed. https://www.bis.org/about/legal/permitted-use-statistics ; attribute BIS and original national sources, label own calculations, do not imply endorsement. No raw redistribution in this repo. | 135216 |

Task set dùng chung3 miền: `artifacts/manifests/phase31/taskset_v2.json`, 401318 byte, SHA-256 `8741c1165c77fe8d67ba262a193ddebdd044b45eebf3a8bc0318255123ee23ab`.
Catalog canonical input/evidence dùng chung:60 record/miền (40 numeric +20 evidence). Không nhân bản raw.

Schema: request(task_id, domain_hint, question, record_id, operation); split/group/source_group/fault/gold chỉ harness. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có20 task, mỗi split12/4/4. Group nguyên template và source/document, overlap0.

Bảng A.49. A.17. ch6_house_tasks

| Task | Input câu hỏi (synthetic) | Output số thật từ tool | Trích output tool/evidence |
|---|---|---|---|
| house_numeric_f1_1 | giá nhà: tính đầu ra checkpoint cho bản ghi house_numeric_000. | [118115.72406888881] | Frozen NumPy CPU tool output: 118115.72 |
| house_numeric_f1_2 | giá nhà: tính đầu ra checkpoint cho bản ghi house_numeric_001. | [177813.23670143556] | Frozen NumPy CPU tool output: 177813.24 |
| house_numeric_f1_3 | giá nhà: tính đầu ra checkpoint cho bản ghi house_numeric_002. | [253889.1433285652] | Frozen NumPy CPU tool output: 253889.14 |
| house_evidence_f1_1 | giá nhà: tìm bằng chứng snapshot cho mã house_evidence_000. | [80.8486] | BIS series Q.AT.N.628; TRAIN origin 2004-10-01T00:00:00: 80.8486 index. |
| house_evidence_f1_2 | giá nhà: tìm bằng chứng snapshot cho mã house_evidence_001. | [69.5063] | BIS series Q.AU.N.628; TRAIN origin 2004-10-01T00:00:00: 69.5063 index. |

Không thiếu task/gold. Numeric dùng parent TRAIN; Gold window có thể chồng context. MedQuAD chỉ corpus evidence, không QA TEST label. Policy/challenge là ca tổng hợp đã gắn nhãn, không phân bố nhu cầu thực. Gold numeric parity là khớp tool, không predictive accuracy.

Nhận xét: thiết kế cân bằng thuận tiện kiểm pipeline nhưng nhỏ, rule/ID-bound, không chứng minh hiểu ngôn ngữ tự do. Ames là USD giá bán lịch sử; BIS là chỉ số danh nghĩa2010=100, không so trực tiếp hai đơn vị. CDC probability không phải chẩn đoán; Pink Sheet không phải giá giao dịch hiện tại. Citation hash kiểm local container, URL cấp nguồn.

Bản đầy đủ đã khóa: [ch6_house_tasks](../../references/dataset_cards/v3_agent/ch6_house_tasks.md).

## A.18. ch6_gold_tasks

100 task synthetic-template trên nguồn thật;60/20/20 theo nhóm. Không phải100 người bệnh/căn nhà mới.

Bảng A.50. A.18. ch6_gold_tasks

| Parent | Link snapshot | Điều khoản/citation | Raw parent bytes (không copy) |
|---|---|---|---|
| ch4_gold_pink_sheet | https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx | World Bank Commodity Prices - History and Projections catalog: CC BY 4.0. https://datacatalog.worldbank.org/search/dataset/0038238/commodity-prices-history-and-projections . Attribute World Bank and preserve unit/source notes. Not a real-time vintage. | 586099 |

Task set dùng chung3 miền: `artifacts/manifests/phase31/taskset_v2.json`, 401318 byte, SHA-256 `8741c1165c77fe8d67ba262a193ddebdd044b45eebf3a8bc0318255123ee23ab`.
Catalog canonical input/evidence dùng chung:60 record/miền (40 numeric +20 evidence). Không nhân bản raw.

Schema: request(task_id, domain_hint, question, record_id, operation); split/group/source_group/fault/gold chỉ harness. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có20 task, mỗi split12/4/4. Group nguyên template và source/document, overlap0.

Bảng A.51. A.18. ch6_gold_tasks

| Task | Input câu hỏi (synthetic) | Output số thật từ tool | Trích output tool/evidence |
|---|---|---|---|
| gold_numeric_f1_1 | giá vàng: tính đầu ra checkpoint cho bản ghi gold_numeric_000. | [34.041584925525314, 32.72447998441302, 35.20187368605272] | Frozen NumPy CPU tool output: 34.041585, 32.72448, 35.201874 |
| gold_numeric_f1_2 | giá vàng: tính đầu ra checkpoint cho bản ghi gold_numeric_001. | [34.118522988282535, 32.64269480383689, 35.25670174007024] | Frozen NumPy CPU tool output: 34.118523, 32.642695, 35.256702 |
| gold_numeric_f1_3 | giá vàng: tính đầu ra checkpoint cho bản ghi gold_numeric_002. | [34.12954819479691, 32.675810153854, 35.27241514250787] | Frozen NumPy CPU tool output: 34.129548, 32.67581, 35.272415 |
| gold_evidence_f1_1 | giá vàng: tìm bằng chứng snapshot cho mã gold_evidence_000. | [35.0] | TRAIN origin 1965-04-01T00:00:00: 35 USD/troy oz. |
| gold_evidence_f1_2 | giá vàng: tìm bằng chứng snapshot cho mã gold_evidence_001. | [35.0] | TRAIN origin 1965-05-01T00:00:00: 35 USD/troy oz. |

Không thiếu task/gold. Numeric dùng parent TRAIN; Gold window có thể chồng context. MedQuAD chỉ corpus evidence, không QA TEST label. Policy/challenge là ca tổng hợp đã gắn nhãn, không phân bố nhu cầu thực. Gold numeric parity là khớp tool, không predictive accuracy.

Nhận xét: thiết kế cân bằng thuận tiện kiểm pipeline nhưng nhỏ, rule/ID-bound, không chứng minh hiểu ngôn ngữ tự do. Ames là USD giá bán lịch sử; BIS là chỉ số danh nghĩa2010=100, không so trực tiếp hai đơn vị. CDC probability không phải chẩn đoán; Pink Sheet không phải giá giao dịch hiện tại. Citation hash kiểm local container, URL cấp nguồn.

Bản đầy đủ đã khóa: [ch6_gold_tasks](../../references/dataset_cards/v3_agent/ch6_gold_tasks.md).

