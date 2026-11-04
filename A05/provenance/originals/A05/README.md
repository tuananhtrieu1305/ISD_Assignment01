# Assignment 05: So sánh các kiến trúc CNN

## 1. Mục tiêu

Assignment 05 xây dựng và so sánh bốn family kiến trúc CNN được triển khai từ đầu:

- Basic CNN
- AlexNet-inspired CNN
- VGG-inspired CNN
- ResNet-inspired CNN

Hai dataset ảnh dùng biến thể Conv2D. Dataset CDC Diabetes là dữ liệu tabular nên dùng các adaptation Conv1D theo yêu cầu assignment; báo cáo nêu rõ rằng tabular feature adjacency không có locality không gian tự nhiên như pixel ảnh.

## 2. Cấu trúc thư mục

```text
A05/
├── AGENTS.md
├── datasets/
│   ├── diabetes/
│   ├── eurosat/
│   └── oxford_pets/
├── models/
│   ├── __init__.py
│   ├── architectures.py
│   ├── checkpoints/
│   ├── experiment_utils.py
│   ├── test_architectures.py
│   └── test_experiment_utils.py
├── notebooks/
│   ├── 01_CNN_Fundamentals.ipynb
│   ├── 02_EuroSAT_CNN.ipynb
│   ├── 03_Oxford_Pets_CNN.ipynb
│   ├── 04_CDC_Diabetes_CNN.ipynb
│   └── 05_Model_Comparison.ipynb
├── report/
│   ├── A05_report.md
│   ├── architecture_design.md
│   ├── audit_report.md
│   ├── dataset_audit.md
│   └── experiment_protocol.md
├── requirements_a05.txt
└── results/
    ├── figures/
    ├── hyperparameters/
    ├── metrics/
    └── splits/
```

## 3. Cấu trúc dataset

- EuroSAT: `datasets/eurosat/EuroSAT_RGB/`, gồm 27,000 ảnh RGB `64x64` và 10 lớp.
- Oxford-IIIT Pet: `datasets/oxford_pets/`, chỉ dùng official samples từ `annotations/trainval.txt` và `annotations/test.txt`. Tổng official samples là 7,349; 41 raw images không nằm trong annotation chính thức bị loại khỏi thí nghiệm. Bốn file `.jpg` có nội dung PNG được decode theo nội dung ảnh và vẫn được dùng nếu có trong official annotations.
- CDC Diabetes Health Indicators: `datasets/diabetes/diabetes_012_health_indicators_BRFSS2015.csv`, gồm 253,680 rows, target `Diabetes_012`, 21 predictor features và 3 lớp.

Raw datasets được giữ nguyên, không sửa, không convert và không ghi đè.

## 4. Environment

Môi trường cố định:

```text
C:/Users/anhca/anaconda3/envs/tf312/python.exe
```

Phiên bản đã xác minh:

- TensorFlow 2.21.0
- Keras 3.15.1
- NumPy 2.5.3
- Pandas 3.0.5
- scikit-learn 1.9.1
- matplotlib 3.11.2
- Pillow 12.3.0

CPU-only TensorFlow là chủ ý và được chấp nhận. Không cần CUDA, cuDNN, TensorFlow DirectML, WSL, `uv`, hoặc môi trường ảo khác.

## 5. Thứ tự chạy notebook

Chạy bằng Jupyter kernel `Python 3.12 - TensorFlow` theo thứ tự:

1. `notebooks/01_CNN_Fundamentals.ipynb`
2. `notebooks/02_EuroSAT_CNN.ipynb`
3. `notebooks/03_Oxford_Pets_CNN.ipynb`
4. `notebooks/04_CDC_Diabetes_CNN.ipynb`
5. `notebooks/05_Model_Comparison.ipynb`

Notebook 05 không retrain model; nó chỉ load kết quả đã lưu từ `results/`.

## 6. Hyperparameter results

Kết quả tuning được lưu tại:

- `results/hyperparameters/eurosat_hyperparameters.csv`
- `results/hyperparameters/eurosat_selected_protocol.csv`
- `results/hyperparameters/oxford_pets_hyperparameters.csv`
- `results/hyperparameters/oxford_pets_selected_protocol.csv`
- `results/hyperparameters/diabetes_hyperparameters.csv`
- `results/hyperparameters/diabetes_selected_protocol.csv`

Tổng số hyperparameter experiment rows đã lưu: 44.

## 7. Final metrics

Final metrics được lưu tại:

- `results/metrics/eurosat_models.csv`
- `results/metrics/oxford_pets_models.csv`
- `results/metrics/diabetes_models.csv`
- `results/metrics/eurosat_per_class_metrics.csv`
- `results/metrics/oxford_pets_per_class_metrics.csv`
- `results/metrics/diabetes_per_class_metrics.csv`
- `results/metrics/eurosat_confusion_pairs.csv`
- `results/metrics/oxford_pets_confusion_pairs.csv`

Final trained CNN models: 12, gồm 4 model cho EuroSAT, 4 model cho Oxford-IIIT Pet, và 4 model Conv1D cho CDC Diabetes. Majority-class baseline của Diabetes là baseline không train.

## 8. Figures

Figures được lưu dưới:

- `results/figures/eurosat/`
- `results/figures/oxford_pets/`
- `results/figures/diabetes/`
- `results/figures/model_comparison/`

Các figure chính gồm hyperparameter comparisons, training curves, confusion matrices, error grids, final metric plots, và model comparison plots.

## 9. Checkpoints

Checkpoints cuối được lưu dưới `models/checkpoints/`:

- `eurosat_basic.keras`
- `eurosat_alexnet_inspired.keras`
- `eurosat_vgg_inspired.keras`
- `eurosat_resnet_inspired.keras`
- `oxford_pets_basic.keras`
- `oxford_pets_alexnet_inspired.keras`
- `oxford_pets_vgg_inspired.keras`
- `oxford_pets_resnet_inspired.keras`
- `diabetes_basic.keras`
- `diabetes_alexnet_inspired.keras`
- `diabetes_vgg_inspired.keras`
- `diabetes_resnet_inspired.keras`

## 10. Reproducibility notes

- Seed chính: 42.
- Split files được lưu trong `results/splits/` và được dùng lại cho final comparisons.
- Test set không được dùng để chọn hyperparameters.
- Mọi preprocessing có bước fit đều chỉ fit trên train split; với Diabetes, `StandardScaler` được fit trên train rồi áp dụng cho validation/test.
- Oxford experiments chỉ dùng official annotation samples, không glob toàn bộ thư mục ảnh.
- Image decoding dùng chiến lược content-aware để không loại nhầm các file PNG-content có tên `.jpg`.
- Báo cáo cuối nằm ở `report/A05_report.md`.
