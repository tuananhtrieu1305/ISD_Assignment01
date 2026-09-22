# A05 Strict Audit Report

This audit was performed against the completed Assignment 05 project artifacts without retraining any neural network.

## Environment Audit

- Python executable: `C:\Users\anhca\anaconda3\envs\tf312\python.exe`
- Python version: `3.12.14`
- TensorFlow version: `2.21.0`
- TensorFlow devices: `['CPU:/physical_device:CPU:0']`
- CPU-only TensorFlow is expected and was not treated as an issue.
- No active evidence of temporary uv execution, backend `.venv` execution, WSL execution, CUDA/cuDNN dependency usage, or pretrained architecture imports was found in executable project source.

## Data Integrity

- EuroSAT raw/split samples: `27000` raw JPEGs; splits `{'train': 18900, 'val': 4050, 'test': 4050}`.
- Oxford official annotations: `{'trainval': 3680, 'test': 3669, 'official_unique': 7349}`; split rows `{'train': 2944, 'val': 736, 'test': 3669}`.
- Oxford unreferenced raw images excluded: `41`.
- Oxford PNG-content `.jpg` files decoded as: `{'Egyptian_Mau_14.jpg': 'PNG', 'Egyptian_Mau_156.jpg': 'PNG', 'Egyptian_Mau_186.jpg': 'PNG', 'Abyssinian_5.jpg': 'PNG'}`.
- Diabetes raw rows: `253680`; split rows `{'train': 177576, 'val': 38052, 'test': 38052}`.
- Diabetes duplicate rows observed and documented: `23899`.
- Raw dataset directories contain no generated result/checkpoint artifacts.

## Data Leakage

- Split overlap checks: `{'EuroSAT': {'train_val': 0, 'train_test': 0, 'val_test': 0}, 'Oxford Pets': {'train_val': 0, 'train_test': 0, 'val_test': 0}, 'Diabetes': {'train_val': 0, 'train_test': 0, 'val_test': 0}}`.
- Hyperparameter protocol files contain explicit decision categories and evidence text.
- Diabetes preprocessing code contains train-fitted scaler patterns.
- Final workflows use saved split files and isolate test prediction outputs to final evaluation artifacts.

## Split Consistency

- The final dataset workflows load the saved split CSVs. All four model rows per dataset are stored in one metrics file per dataset, reflecting a shared split/preprocessing protocol.

## Fair Model Comparison

- Within each dataset, selected protocol CSVs record shared preprocessing, optimizer protocol, learning rate, batch size, EarlyStopping, seeds, and class-weight policy where applicable.
- Architecture family is the primary changed variable in the final comparison metrics.

## Hyperparameter Justification

- Selected protocol files include `decision`, `selected_value`, `classification`, and `evidence_or_reason` columns.
- Important values for resolution, learning rate, batch size, dropout/regularization, class weighting, max epochs, and patience are categorized as data-determined, architecture-determined, experimentally selected, operational bound, or controlled protocol choice with rationale.

## Architecture Correctness

- Existing architecture smoke tests passed.
- Additional audit forward passes confirmed output shapes and nonzero parameter counts:

  - `BasicCNN2D`: input `(64, 64, 3)`, output `(1, 10)`, parameters `24202`
  - `AlexNetInspired2D`: input `(64, 64, 3)`, output `(1, 10)`, parameters `260170`
  - `VGGInspired2D`: input `(64, 64, 3)`, output `(1, 10)`, parameters `304810`
  - `ResNetInspired2D`: input `(64, 64, 3)`, output `(1, 10)`, parameters `324490`
  - `BasicCNN1D`: input `(21, 1)`, output `(1, 3)`, parameters `2787`
  - `AlexNetInspired1D`: input `(21, 1)`, output `(1, 3)`, parameters `29635`
  - `VGGInspired1D`: input `(21, 1)`, output `(1, 3)`, parameters `38299`
  - `ResNetInspired1D`: input `(21, 1)`, output `(1, 3)`, parameters `44387`

## Notebook Quality

- `01_CNN_Fundamentals.ipynb`: `9` code cells, clean execution order, no error outputs, kernelspec `Python 3.12 - TensorFlow`.
- `02_EuroSAT_CNN.ipynb`: `25` code cells, clean execution order, no error outputs, kernelspec `Python 3.12 - TensorFlow`.
- `03_Oxford_Pets_CNN.ipynb`: `24` code cells, clean execution order, no error outputs, kernelspec `Python 3.12 - TensorFlow`.
- `04_CDC_Diabetes_CNN.ipynb`: `23` code cells, clean execution order, no error outputs, kernelspec `Python 3.12 - TensorFlow`.
- `05_Model_Comparison.ipynb`: `20` code cells, clean execution order, no error outputs, kernelspec `Python 3.12 - TensorFlow`.

## Result Integrity

- Required metric CSVs, per-class CSVs, checkpoints, confusion matrices, error figures, and comparison figures exist and are nonempty.
- The comparison notebook loads metrics from CSV files and does not contain manually typed final metric literals.

## Scientific Interpretation

- Project Markdown/notebooks include caveats against a universal best model.
- Diabetes discussion covers class imbalance and minority-class recall.
- CNN-on-tabular limitations are stated.
- Image error analysis is tied to measured confusion patterns and visible characteristics.

## Critical Issues Found

- None.

## Issues Fixed

- None. No project-content correction was required by this audit.

## Experiments Rerun

- None. Only lightweight smoke tests and audit checks were executed; no model training was rerun.

## Remaining Manual Concerns

- None identified.

## Kiểm tra ngôn ngữ và encoding

Pass chuẩn hóa ngôn ngữ được thực hiện trên các notebook cuối cùng của A05. Nội dung Markdown giải thích đã được viết lại bằng tiếng Việt tự nhiên, giữ nguyên technical terms tiếng Anh khi cần rõ nghĩa.

| Notebook | Markdown cells | Cell mojibake trước sửa | Cell prose tiếng Anh trước sửa | Cell đã viết lại | UTF-8 hợp lệ | Mojibake còn lại | Code cells sửa đổi |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `01_CNN_Fundamentals.ipynb` | 15 | 15 | 0 | 15 | có | không | không |
| `02_EuroSAT_CNN.ipynb` | 26 | 19 | 7 | 26 | có | không | không |
| `03_Oxford_Pets_CNN.ipynb` | 23 | 0 | 23 | 23 | có | không | không |
| `04_CDC_Diabetes_CNN.ipynb` | 28 | 0 | 28 | 28 | có | không | không |
| `05_Model_Comparison.ipynb` | 16 | 0 | 16 | 16 | có | không | không |

- Không retrain neural network.
- Không chạy cell đắt tiền hoặc `model.fit()`.
- Không thay đổi saved metrics, model weights, training histories, hyperparameter decisions, dataset splits, checkpoints, hoặc result CSV.
- Code cells không bị sửa đổi; các output đã lưu được giữ nguyên.
- Notebook JSON được đọc/ghi bằng `encoding="utf-8"` và `ensure_ascii=False` để giữ nguyên ký tự tiếng Việt.
- Sau khi sửa, không phát hiện các mẫu mojibake đã quy định hoặc mẫu dấu hỏi nghi mojibake trong Markdown notebook.
- Không còn Markdown cell giải thích chủ yếu bằng tiếng Anh; technical terms như CNN, learning rate, validation, macro F1, confusion matrix được giữ khi phù hợp.
