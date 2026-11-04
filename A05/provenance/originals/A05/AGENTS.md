# Assignment 05 Rules

These rules apply to all work inside `A05/`.

## Workspace Boundaries

- Work only inside `A05/`.
- Do not modify `pipeline04/`, `pipeline/`, `datasets/`, `backend/`, `mobile/`, `web/`, `A03/`, or any existing folder/file outside `A05/`.
- Use relative paths based on `A05/`; do not hard-code absolute paths.

## Dataset Handling

- Do not download any dataset from the Internet.
- The datasets have already been downloaded manually into `A05/datasets/`.
- Never silently replace a missing dataset with TensorFlow Datasets, Kaggle API, Hugging Face, torchvision, `keras.datasets`, or any online source.
- If a dataset is missing, raise a clear error and stop.
- Preserve the raw datasets. Never modify original dataset files.

## Reproducibility and Evaluation

- Use random seed `42` unless there is a justified reason otherwise.
- The test set must never be used for hyperparameter selection.
- Final reported numbers must come from actually executed experiments.
- Do not fabricate model results, metrics, figures, training histories, or conclusions.

## Notebook and Report Style

- Analysis and explanation belong in Markdown cells.
- Code cells should contain code, concise diagnostics, tables, or plots only.
- Do not put long explanations into `print()` statements.

## Parameter Decisions

Every meaningful parameter decision must be classified as one of:

1. data-determined,
2. architecture-determined,
3. experimentally selected,
4. operational bound.

If a meaningful parameter cannot be justified mathematically by the data or by the architecture, perform a validation-set experiment and select it from evidence.

Learning rate and similar optimization parameters must be compared across candidate values instead of being chosen by statements such as "commonly used", "popular choice", "people usually use this", or personal intuition.

## Model Requirements

The four model families are:

1. Basic CNN
2. AlexNet-inspired CNN
3. VGG-inspired CNN
4. ResNet-inspired CNN

All models must be implemented from scratch for this assignment.

- Do not use pretrained weights.
- Do not use transfer learning.
- The goal is a controlled comparison of CNN architectures.

## Dataset-Specific Modeling Notes

- For image datasets, use Conv2D variants.
- For the tabular diabetes dataset, use carefully explained Conv1D adaptations.
- Explicitly discuss the limitation that CNNs have no natural 2D spatial structure on tabular features.

## Environment Policy

A05 must reuse the existing permanent TensorFlow environment:

`C:/Users/anhca/anaconda3/envs/tf312/python.exe`

Jupyter kernel:

`Python 3.12 - TensorFlow`

Verified environment:

- TensorFlow 2.21.0
- NumPy 2.5.3
- Pandas 3.0.5
- scikit-learn 1.9.1
- matplotlib 3.11.2
- Pillow 12.3.0

CPU-only TensorFlow is intentional and acceptable.

For every remaining A05 task involving Python execution:

- Use exactly: `C:/Users/anhca/anaconda3/envs/tf312/python.exe`
- Reuse packages already installed in this environment.
- Do not use `C:/DATA/assign/backend/.venv`.
- Do not use temporary uv environments.
- Do not use `uv run --with`.
- Do not create new virtual environments.
- Do not use WSL environments.
- Do not install packages automatically.
- Do not install CUDA.
- Do not install cuDNN.
- Do not install NVIDIA packages.
- Do not install `tensorflow[and-cuda]`.
- Do not install TensorFlow DirectML.
- Do not install GPU-related dependencies.
- Absence of a GPU must not be treated as an error.

Before executing any notebook, script, test, hyperparameter experiment, or model training:

1. Determine the exact Python executable.
2. Verify that it is `C:/Users/anhca/anaconda3/envs/tf312/python.exe`.
3. Verify all required imports.
4. Only then execute the task.

If a required package is missing:

- Stop.
- Report exactly which package is missing.
- Do not install anything automatically.

## Language and Encoding Policy

All explanatory notebook content must be written in Vietnamese. This includes notebook titles, section headings, Markdown explanations, dataset descriptions, mathematical explanations, experiment descriptions, hyperparameter analysis, observations, error analysis, conclusions, manually defined figure titles, and explanatory table headings.

Technical terms may remain in English where that is clearer and more standard. Examples include CNN, convolution, kernel, feature map, ReLU, pooling, Flatten, Global Average Pooling, Dense, Softmax, Cross-Entropy, learning rate, batch size, dropout, optimizer, EarlyStopping, validation, test set, train set, macro F1, precision, recall, accuracy, confusion matrix, residual block, Basic CNN, AlexNet-inspired, VGG-inspired, ResNet-inspired, EuroSAT, Oxford-IIIT Pet, and CDC Diabetes Health Indicators.

Do not translate technical terms into unnatural Vietnamese merely for consistency. Prefer phrasing such as "learning rate được chọn dựa trên validation macro F1" or "Tốc độ học (learning rate) được chọn dựa trên validation macro F1" over forced translations that reduce clarity.

Programming elements remain unchanged:

- Python keywords
- module names
- API names
- function names
- class names
- variable names
- file paths
- formulas
- code syntax

Code comments should preferably be Vietnamese when they explain assignment logic. Short technical comments may remain English if translating them would reduce clarity.

Framework-generated output such as epoch logs, `loss`, `accuracy`, and `val_loss` does not need to be translated.

All notebook files must be valid UTF-8. Vietnamese characters must display correctly. Never write Vietnamese notebook content using an encoding that replaces characters with literal question marks, Unicode replacement characters, or common mojibake byte-sequence renderings.

When programmatically reading or writing `.ipynb` JSON, use `encoding="utf-8"` and preserve Unicode correctly. When `json.dump` is used, use `ensure_ascii=False` unless there is a concrete reason not to.
