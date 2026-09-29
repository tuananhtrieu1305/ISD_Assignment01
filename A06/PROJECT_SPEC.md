# Assignment 06 — Permanent Experiment Contract

**Contract status:** locked for A06  
**Established:** 2026-09-26  
**Project root:** `C:\DATA\assign\A06`

## 1. Scope and governance

A06 is independent from A05. Nothing in `C:\DATA\assign\A05` or its Python environment may be changed for this assignment.

This file defines the intended experiment. `CURRENT_STATE.md` records what actually exists. If reality changes, update `CURRENT_STATE.md`; never silently undo an explicit decision from a successful earlier milestone. Preserve both raw datasets unchanged after acquisition.

The assignment must explain the basic concepts, equations, and code needed to understand RNNs, then analyze, predict, and visualize both locked datasets with PyTorch and Keras.

## 2. Environment contract

- Conda environment: `rnn312`
- Python major/minor: `3.12`
- Expected interpreter: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Required direct packages: `numpy`, `pandas`, `matplotlib`, `scikit-learn`, `openpyxl`, `jupyter`, `ipykernel`, `pytest`, `joblib`, `torch`, `tensorflow`, and `yfinance`
- Actual versions belong in `CURRENT_STATE.md` and the environment verification report; version numbers must never be invented.

## 3. Locked datasets

### 3.1 Customer behavior

- Dataset: **Online Retail II**, UCI Machine Learning Repository, Dataset ID 502
- Raw path: `datasets/customer/online_retail_II.xlsx`
- The workbook may contain multiple sheets and historical column names that differ from newer UCI documentation.
- Inspect and record actual sheets and columns before processing.
- Never silently substitute a different retail dataset.
- Never overwrite or normalize the raw workbook in place. Column normalization is permitted only in derived DataFrames or processed artifacts and must be documented.

### 3.2 Stock prices

- Ticker: `AAPL`
- Locked calendar interval: 2015-01-01 through 2025-12-31, inclusive
- Permanent local path: `datasets/stock/AAPL_2015_2025.csv`
- Download once with unadjusted behavior explicitly selected where supported (`auto_adjust=False`).
- Required columns: `Date`, `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`
- Market holidays may make the actual first or last trading date differ from the calendar boundary; record the actual dates.
- Every later notebook must read this local CSV and must not redownload current market data.

## 4. Locked machine-learning tasks

### 4.1 Customer-week classification

- Unit of time: week
- Observation unit: customer-week sequence
- Candidate input features per week:
  - `total_spent`
  - `total_quantity`
  - `order_count`
  - `unique_products`
  - `active_flag`
- Sequence length: 8 weeks
- Target: whether the same customer purchases in the next week
- Task: binary classification
- `CustomerID` identifies/group sequences but must not be an input feature.

### 4.2 Stock regression

- Input features: `Open`, `High`, `Low`, `Close`, `Volume`
- Sequence length: 30 trading days
- Target: `Close` price on the following trading day
- Task: regression

## 5. Chronological splitting contract

Never use a random train/test split. Assign samples to approximately 70% train, 15% validation, and 15% test according to each sample's **target timestamp/date**.

All training targets must precede validation targets, and all validation targets must precede test targets. Future observations must never influence earlier samples. The same customer may occur in multiple splits because the customer task forecasts later behavior for known customers, but target weeks must remain chronologically separated. Stock target dates must also remain chronological.

Exact boundary dates will be recorded when the production sequence pipeline is created.

## 6. Anti-data-leakage contract

1. Fit every scaler and preprocessing statistic with training information only.
2. Validation and test data may call only `transform()` on fitted preprocessing objects.
3. Information from week/day `t+1` must never be included in features that predict `t+1`.
4. Calculate class weights from training labels only.
5. Do not use test data for model selection, threshold selection, or early stopping.
6. Preserve raw source datasets untouched.

## 7. Reproducibility contract

- Global seed: `SEED = 42`
- Set appropriate seeds for Python, NumPy, PyTorch, and TensorFlow/Keras.
- Record relevant preprocessing, split boundaries, package versions, and generated artifacts.
- Do not promise bit-for-bit deterministic equality across different frameworks or hardware.

## 8. Baseline training contract

- Primary architecture: Vanilla RNN / Keras `SimpleRNN`
- Do not silently replace the main model with LSTM or GRU.
- LSTM and GRU are optional extensions only.
- Use small CPU-suitable models.
- Baseline maximum: 30 epochs.
- Use validation-based early stopping with patience around 5 where appropriate.

## 9. Notebook plan

1. `notebooks/01_RNN_Fundamentals.ipynb`
2. `notebooks/02_Customer_Behavior_Data.ipynb`
3. `notebooks/03_Stock_Data.ipynb`
4. `notebooks/04_PyTorch_Customer_RNN.ipynb`
5. `notebooks/05_PyTorch_Stock_RNN.ipynb`
6. `notebooks/06_Keras_Customer_RNN.ipynb`
7. `notebooks/07_Keras_Stock_RNN.ipynb`
8. `notebooks/08_Framework_Comparison.ipynb`

Notebook explanations must be in Vietnamese. Standard English technical terms such as RNN, hidden state, sequence, time step, BPTT, vanishing gradient, LSTM, GRU, batch, epoch, and DataLoader may remain in English. Theory belongs in Markdown cells, not long `print()` strings; code cells must remain clean and executable in notebook order.

## 10. Project structure

```text
A06/
├── datasets/
│   ├── customer/
│   ├── stock/
│   └── processed/
├── notebooks/
├── src/
├── tests/
├── models/
│   ├── pytorch/
│   └── keras/
├── results/
│   ├── figures/
│   ├── metrics/
│   └── predictions/
├── report/
├── PROJECT_SPEC.md
├── CURRENT_STATE.md
└── README.md
```

## 11. Milestone rule

The initialization milestone creates and verifies the environment, project structure, immutable raw datasets, and documentation only. It must not train a model or implement the planned notebooks. Each later prompt must first read this contract and `CURRENT_STATE.md`, implement only its named milestone, execute and validate its notebook, then update `CURRENT_STATE.md`.
