# Dataset card — EuroSAT RGB

## Nhận dạng và nguồn

- Dataset ID: `ch3_eurosat_rgb`.
- Chương/bài toán: Chương 3, 10-class land-use/land-cover image classification.
- Nguồn chính thức: <https://zenodo.org/records/7711097>, DOI `10.5281/zenodo.7711097`.
- Paper: DOI `10.1109/JSTARS.2019.2918242`; citation keys `helber2023eurosatdata`, `helber2019eurosat`.
- Truy cập: 2026-10-05.
- License/terms: Zenodo record truy xuất không hiện giá trị license riêng; record yêu cầu lưu ý Copernicus Sentinel Data Terms. Không gán một open-source license không có bằng chứng.
- Local: `A05/datasets/eurosat/EuroSAT_RGB/`; 91,844,360 bytes; manifest SHA-256 `c88f965867984809f83aadfc2bfefa9e5622d583c19f82cbd254a4681d8255ee`.

## Kích thước và phân bố

- 27,000 ảnh JPEG RGB, shape 64×64×3, 10 lớp.

| Lớp | Số ảnh | Lớp | Số ảnh |
|---|---:|---|---:|
| AnnualCrop | 3,000 | Forest | 3,000 |
| HerbaceousVegetation | 3,000 | Highway | 2,500 |
| Industrial | 2,500 | Pasture | 2,000 |
| PermanentCrop | 2,500 | Residential | 3,000 |
| River | 2,500 | SeaLake | 3,000 |

- Split A05 khóa: TRAIN 18,900; VAL 4,050; TEST 4,050, stratified seed 42.

## Mẫu input/output

- Mẫu local: `AnnualCrop/AnnualCrop_1.jpg` → label `AnnualCrop`.
- Tensor decode trong notebook có shape `(64,64,3)`, `float32`, pixel scale `[0,1]`.
- DOCX sẽ dùng grid 10 ảnh đại diện có caption lớp và ghi nguồn dataset, không dùng ảnh sinh lại.

## Tiền xử lý và protocol

- Decode RGB, bắt buộc shape 64×64, scale pixel về `[0,1]`.
- Matched framework track dùng augmentation `none` để giữ input tương đương.
- Nếu scratch phải dùng subset do CPU, lưu đường dẫn ảnh subset stratified và áp dụng cùng keys cho Keras/PyTorch.

## Nhận xét và giới hạn

- Phân bố gần cân bằng nhưng lớp Pasture ít nhất (2,000), vì vậy báo macro-F1 ngoài accuracy.
- Ảnh là crop vệ tinh nhỏ; mô hình có thể học texture/màu và có rủi ro spatial leakage nếu patch lân cận rơi vào nhiều split. Dataset hiện không cung cấp geographic grouping trong local artifact.
- RGB chỉ dùng 3/13 bands của Sentinel-2, nên kết quả không đại diện đầy đủ cho bản multispectral.

## Bằng chứng local

- Notebook: `A05/notebooks/02_EuroSAT_CNN.ipynb`.
- Splits: `A05/results/splits/eurosat_{train,val,test}.csv`.
- Keras metrics/checkpoints/figures hiện có trong `A05/results/` và `A05/models/checkpoints/`.
