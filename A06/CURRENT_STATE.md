# Assignment 06 — Current State

**Last updated:** 2026-09-29  
**Initialization status:** complete and verified  
**Verification result:** PASS

**Full-project audit status:** PASSED — all 8 notebooks clean-executed, 50/50 tests passed, no data leakage found

**Final assignment report status:** complete, rendered, and verified

**Notebook 01 status:** complete, executed, and verified

**Notebook 02 status:** complete, executed, and verified

**Notebook 03 status:** complete, executed, and verified

**Shared preprocessing status:** complete, executed, deterministic, and verified

**Notebook 04 status:** complete, executed, trained, and verified

**Notebook 05 status:** complete, executed, trained, and verified

**Notebook 06 status:** complete, executed, trained, and verified

**Notebook 07 status:** complete, executed, trained, and verified

**Notebook 08 status:** complete, executed, artifact-only, and verified

## Environment reality

- Conda environment: `rnn312`
- Interpreter: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Python: `3.12.14`
- Platform: Windows 11 (`Windows-11-10.0.26200-SP0`)
- PyTorch device availability: CPU available; CUDA unavailable (`torch.cuda.is_available() == False`)
- TensorFlow device availability: `/physical_device:CPU:0`; no TensorFlow GPU device detected
- Native Windows TensorFlow 2.21 is expected to run on CPU for this project.

### Installed direct-package versions

| Package | Installed version |
|---|---:|
| numpy | 2.5.3 |
| pandas | 3.0.6 |
| matplotlib | 3.11.2 |
| scikit-learn | 1.9.1 |
| openpyxl | 3.1.5 |
| jupyter | 1.1.1 |
| ipykernel | 7.3.0 |
| pytest | 9.1.1 |
| joblib | 1.6.0 |
| torch | 2.14.0 |
| tensorflow | 2.21.0 |
| keras | 3.15.1 |
| yfinance | 1.7.0 |

## Dataset reality

### UCI Online Retail II

- Status: downloaded from UCI Dataset 502 and readable
- Raw path: `C:\DATA\assign\A06\datasets\customer\online_retail_II.xlsx`
- Size: 45,622,278 bytes
- SHA-256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- Total data rows across sheets: 1,067,371
- The raw workbook has not been edited.

| Sheet | Data rows | Actual raw columns |
|---|---:|---|
| Year 2009-2010 | 525,461 | Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country |
| Year 2010-2011 | 541,910 | Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country |

The 200-row inspection sample for each sheet inferred `Invoice` and `StockCode` as object, `Description` and `Country` as string, `Quantity` and sampled `Customer ID` as integer, `InvoiceDate` as datetime, and `Price` as float. These sample dtypes are inspection metadata only; later EDA must audit full-column missingness and types. Expected in-memory normalization for later work is `Invoice -> InvoiceNo`, `Price -> UnitPrice`, and `Customer ID -> CustomerID`; no normalization has yet been applied.

Notebook 02 completed the full-data audit and applied those three renames in memory only. Actual findings:

- Raw shape: 1,067,371 rows × 8 columns.
- Actual timestamp range: 2009-12-01 07:45:00 through 2011-12-09 12:50:00.
- Exact duplicate rows: 34,335.
- Missing values: `CustomerID` 243,007; `Description` 4,382; every other normalized column 0.
- Invalid/missing parsed dates: 0.
- Raw distinct counts: 5,942 customers, 53,628 invoices, and 43 countries.
- Cancellation convention: normalized `InvoiceNo` starts with `C` (case-insensitive).
- Cancellation findings before filtering: 19,494 lines across 8,292 cancellation invoices; 19,493 cancellation lines have negative quantity.
- Other integrity findings: 22,950 negative-quantity lines and 6,207 lines with non-positive `UnitPrice`.
- Modeling-cleaning result after exact-deduplication, valid positive integer `CustomerID`, valid date, non-cancellation invoice, `Quantity > 0`, and `UnitPrice > 0`: 779,425 transaction lines, 5,878 customers, 36,969 invoices, and the same timestamp range.

### AAPL historical prices

- Status: downloaded once through `yfinance==1.7.0` with `auto_adjust=False`, `actions=False`, and `repair=False`; readable locally
- Raw path: `C:\DATA\assign\A06\datasets\stock\AAPL_2015_2025.csv`
- Rows: 2,766
- Columns: `Date`, `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`
- Locked calendar interval requested: 2015-01-01 through 2025-12-31 inclusive
- Actual first trading date: 2015-01-02 (2015-01-01 was not a trading session)
- Actual last trading date: 2025-12-31
- Missing values: 0 in every column
- Duplicate dates: 0
- Date order: strictly non-decreasing / chronological
- Size: 305,816 bytes
- SHA-256: `2c8eef3c6a3836e2217bf3e99faaeec37d30e60298f7319e8f3748b71e5bd2b8`
- All later notebooks must use this CSV and must not invoke `yfinance`.

Notebook 03 independently re-audited the locked CSV and confirmed its raw shape of 2,766 rows × 7 columns. After parsing `Date`, the price columns are floating-point, `Volume` is integer, all expected columns are present, and there are no missing or invalid dates, duplicate dates, non-positive OHLC prices, inconsistent `High`/`Low` bounds, or non-positive volume values. The source was already chronological before sorting; the notebook nevertheless performs a stable ascending sort and asserts monotonic dates.

## Completed milestones

- Created the isolated A06 directory tree without modifying A05.
- Created Conda environment `rnn312` with Python 3.12.
- Installed and imported all required direct packages.
- Acquired both locked raw datasets without substitution.
- Inspected and recorded workbook sheet names, row counts, raw columns, and sample dtypes.
- Validated stock schema, date interval, ordering, duplicates, and missing values.
- Recorded CPU/GPU device availability for PyTorch and TensorFlow.
- Created the permanent experiment contract and repeatable environment verification scripts/reports.
- Passed Python bytecode compilation, `pip check`, and 4 project contract tests.
- Completed and executed `notebooks/01_RNN_Fundamentals.ipynb` with the `rnn312` interpreter.
- Completed and executed `notebooks/02_Customer_Behavior_Data.ipynb` with the `rnn312` interpreter.
- Completed and executed `notebooks/03_Stock_Data.ipynb` with the `rnn312` interpreter.
- Implemented and executed the shared deterministic customer/stock preprocessing pipeline consumed by both frameworks.
- Completed and executed `notebooks/04_PyTorch_Customer_RNN.ipynb` with the `rnn312` interpreter.
- The PyTorch and Keras customer and stock baselines have all been trained.
- Completed and executed `notebooks/08_Framework_Comparison.ipynb` using only the stored metrics and prediction artifacts; no model was retrained.
- Completed the full-project correctness audit on 2026-09-27; report: `report/A06_AUDIT_REPORT.md`.

## Notebook 01 execution record

- Notebook: `notebooks/01_RNN_Fundamentals.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 10/10 code cells ran in order with execution counts 1–10 and no error output.
- Structure: 31 total cells, including 21 Markdown cells and 10 code cells.
- Coverage: all 20 required RNN fundamentals sections are present.
- Design notes:
  - Vietnamese narrative with standard English technical terms where natural.
  - Explicit NumPy forward pass shows `x1 -> h1`, `x2 -> h2`, and `x3 -> h3` with shared weights.
  - PyTorch demo uses `torch.nn.RNN(..., batch_first=True)` and explains `output` versus `h_n` shapes.
  - Keras demo covers `SimpleRNN`, `return_sequences`, and `return_state` shapes.
  - BPTT, vanishing/exploding gradient, gradient clipping, LSTM, and GRU are explained with small numerical demonstrations.
  - One embedded semilog figure compares repeated factors `0.5^t` and `1.5^t`; it is a mathematical illustration, not an experimental result.
  - The notebook uses toy arrays only. It does not read assignment datasets, create preprocessing artifacts, train a forecasting model, or modify dataset pipelines.

## Notebook 02 execution record

- Notebook: `notebooks/02_Customer_Behavior_Data.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 14/14 code cells ran in order with execution counts 1–14 and no error output.
- Structure: 35 total cells, including 21 Markdown cells and 14 code cells.
- Raw workbook remained read-only and retained its locked checksum.
- Active-only weekly aggregation contains 31,362 customer-week rows from week start 2009-11-30 through 2011-12-05.
- Prototype next-week label preview contains 350,864 eligible customer-week targets: 328,444 class 0 (93.61%) and 22,420 class 1 (6.39%). This is EDA only; no class weight was calculated.
- Five reusable figures were generated under `results/figures/customer_eda/`.
- No cleaned transaction file, production weekly table, final sequence file, scaler, split, model, or model-selection artifact was created.

### Decisions carried forward to Prompt 5

- Normalize `Invoice -> InvoiceNo`, `Price -> UnitPrice`, and `Customer ID -> CustomerID` in memory; never change the raw workbook.
- Remove exact duplicate rows before modeling aggregation to avoid duplicate contribution to quantity/revenue.
- Purchase-only cleaning requires a valid positive integer `CustomerID`, a valid `InvoiceDate`, non-cancellation invoice, `Quantity > 0`, and `UnitPrice > 0`.
- Define weeks as Monday–Sunday using pandas period `W-SUN`; stored `WeekStart` is Monday.
- Weekly `order_count` uses unique `InvoiceNo`, not invoice-line count.
- Inactive weeks receive zero for `total_spent`, `total_quantity`, `order_count`, `unique_products`, and `active_flag`.
- `CustomerID` is a grouping/index key only and must not be a numerical input feature.
- The prototype excludes boundary weeks beginning 2009-11-30 and 2011-12-05 because the raw observation window does not cover them completely.
- The prototype timeline begins no earlier than each customer's first purchase week and requires eight prior weeks before an eligible target. Prompt 5 must test and explicitly lock this production eligibility rule.
- Chronological split must use target week. Scalers and any class weights must be fit/calculated from TRAIN only.

## Notebook 03 execution record

- Notebook: `notebooks/03_Stock_Data.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 9/9 code cells ran in order with execution counts 1–9 and no error output.
- Structure: 30 total cells, including 21 Markdown cells and 9 code cells.
- Actual source range: 2015-01-02 through 2025-12-31; 2015-01-01 was not a trading session.
- Integrity result: 2,766 rows, no missing values, no duplicate dates, chronological order confirmed, no non-positive OHLC prices, no inconsistent `High`/`Low` bounds, and no non-positive volume.
- Four reusable figures were generated under `results/figures/stock_eda/` and visually checked.
- The notebook did not redownload data, call `yfinance`, train a model, fit a scaler, finalize split boundaries, or create production sequence files.

### Decisions carried forward to stock preprocessing

- Preserve the feature order `Open`, `High`, `Low`, `Close`, `Volume`.
- Each input contains exactly 30 previous trading observations with shape `(30, 5)`; its target is the immediately following trading day's `Close`.
- Split chronologically by target date into TRAIN, validation, and TEST; exact boundary dates remain a later preprocessing responsibility.
- Moving averages and daily returns are EDA aids only and are not locked model features.
- Fit every feature scaler on TRAIN only; validation and TEST use transform only. If the target is scaled, its scaler must also be fit on TRAIN only and predictions must be inverse-transformed for price-unit metrics.
- Use the persistence baseline `predicted next Close = last Close in the 30-day input window` and compare it with learned models on the same TEST targets using MAE, RMSE, and R².

## Shared preprocessing execution record

- Entry point: `python -m src.run_preprocessing`
- Seed: `42`
- Split method: deterministic chronological grouping by target timestamp, with boundaries selected nearest the requested 70%/15%/15% cumulative sample counts without splitting one target week/date across datasets.
- Execution result: success; both tasks were generated twice and all 9 binary artifacts (6 NPZ files and 3 joblib scalers) had identical SHA-256 hashes across the two runs.
- Validation result: 19/19 pytest tests passed. Standard-library tracing measured 86.8% line coverage across the five new preprocessing modules.
- Raw checksums remained unchanged after both runs.
- No PyTorch or Keras model was trained.

### Final customer preprocessing protocol

- In-memory normalization remains `Invoice -> InvoiceNo`, `Price -> UnitPrice`, and `Customer ID -> CustomerID`; the raw workbook is never rewritten.
- Final purchase-only cleaning remains: remove exact duplicates; require positive integer `CustomerID`; require valid `InvoiceDate`; exclude case-insensitive `InvoiceNo` prefix `C`; require `Quantity > 0` and `UnitPrice > 0`; then define `Revenue = Quantity * UnitPrice`.
- Confirmed counts: 1,067,371 raw rows; 34,335 exact duplicates removed; 779,425 cleaned transaction lines; 5,878 customers; 36,969 invoices.
- Weekly features, in locked order: `total_spent`, `total_quantity`, `order_count`, `unique_products`, `active_flag`.
- `order_count` is unique `InvoiceNo`; `active_flag` is 1 for an active purchase week and 0 for an inactive week. All five behavior values are zero-filled for inactive weeks.
- Week convention: Monday–Sunday. Complete production target calendar excludes partial weeks 2009-11-30 and 2011-12-05, so it spans 2009-12-07 through 2011-11-28.
- Each customer timeline begins at the later of that customer's first purchase week and 2009-12-07, extends through 2011-11-28, and requires eight earlier weeks before a target is eligible.
- Every sample has `X.shape == (8, 5)` and predicts the immediately following week's `active_flag`. `CustomerID` and `target_week` are metadata only; `CustomerID` is not present in the feature tensor.
- Total eligible samples: 350,864.

| Split | Target-week range | X shape | Class 0 | Class 1 | Positive rate |
|---|---|---:|---:|---:|---:|
| TRAIN | 2010-02-01 to 2011-07-11 | `(247458, 8, 5)` | 231,206 | 16,252 | 6.57% |
| Validation | 2011-07-18 to 2011-09-19 | `(50354, 8, 5)` | 47,893 | 2,461 | 4.89% |
| TEST | 2011-09-26 to 2011-11-28 | `(53052, 8, 5)` | 49,345 | 3,707 | 6.99% |

- Customer feature scaler: `StandardScaler`, fit on flattened TRAIN `X` only (`247458 × 8 = 1,979,664` weekly observations). Validation and TEST call transform only.
- TRAIN-only positive-class weight recorded for later frameworks: `231206 / 16252 = 14.226310607925178`. It was not calculated from validation or TEST labels.

### Final stock preprocessing protocol

- Locked feature order: `Open`, `High`, `Low`, `Close`, `Volume`.
- Every sample has `X.shape == (30, 5)` and predicts raw `Close` on the immediately following trading day. Each artifact also retains `target_date`, raw `y`, scaled `y_scaled`, and raw `naive_last_close`.
- Total eligible samples: 2,736.

| Split | Target-date range | X shape | Raw Close target range |
|---|---|---:|---:|
| TRAIN | 2015-02-17 to 2022-09-22 | `(1915, 30, 5)` | 22.5850–182.0100 |
| Validation | 2022-09-23 to 2024-05-13 | `(411, 30, 5)` | 125.0200–198.1100 |
| TEST | 2024-05-14 to 2025-12-31 | `(410, 30, 5)` | 172.4200–286.1900 |

- Stock feature scaler: `StandardScaler`, fit on flattened TRAIN `X` only (`1915 × 30 = 57,450` trading-day observations).
- Stock target scaler: separate `StandardScaler`, fit on the 1,915 TRAIN targets only. Later model notebooks should train against `y_scaled` and inverse-transform predictions before reporting price-unit metrics; raw `y` remains available in every artifact.
- Validation and TEST never participate in fitting either scaler. Their windows may include immediately preceding historical observations from an earlier split because those values are known at prediction time; target dates remain strictly separated.

## Notebook 04 execution record

- Notebook: `notebooks/04_PyTorch_Customer_RNN.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 11/11 code cells ran in order with execution counts 1–11 and no error output.
- Structure: 24 total cells, including 13 Markdown cells and 11 code cells.
- Data source: only the finalized `customer_train.npz`, `customer_val.npz`, and `customer_test.npz` artifacts. Their SHA-256 hashes remained unchanged after training.
- Model: one-layer `torch.nn.RNN`, `batch_first=True`, input size 5, hidden size 64, `tanh`, final hidden state to `Linear(64, 1)`, no Sigmoid inside the model; 4,609 trainable parameters.
- Training: CPU, Adam with learning rate 0.001, `BCEWithLogitsLoss`, batch size 1,024, gradient clipping norm 1.0, maximum 30 epochs, patience 5, seed 42.
- Imbalance handling: `pos_weight = 14.226310607925178`, calculated from TRAIN only (`231,206 / 16,252`).
- The 2026-09-27 clean audit run trained for 11 epochs in 151.06 seconds. Early stopping restored the raw minimum validation-loss checkpoint from epoch 9; best validation loss was 0.9559116967739453. Predictive metrics remained identical to the earlier run; duration is environment/runtime-dependent.
- TEST was evaluated once after model selection with fixed threshold 0.5. TEST was not used for checkpoint selection or threshold tuning.

| TEST metric | Value |
|---|---:|
| Accuracy | 0.7581618035 |
| Precision | 0.1586980920 |
| Recall | 0.5721607769 |
| F1-score | 0.2484770384 |
| ROC-AUC | 0.7009347868 |

- TEST confusion matrix: TN 38,101; FP 11,244; FN 1,586; TP 2,121.
- Predictions contain 53,052 rows with `CustomerID`, `target_week`, `true_label`, `probability`, and `predicted_label`; no missing values or duplicate customer-week keys were found.
- Three reusable figures were generated under `results/figures/pytorch_customer/` and visually checked.
- Verification: 25/25 project tests passed; `src/pytorch_customer.py` measured 92.5% line coverage with the standard-library tracer.

## Notebook 05 execution record

- Notebook: `notebooks/05_PyTorch_Stock_RNN.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 13/13 code cells ran in order with execution counts 1–13 and no error output.
- Structure: 27 total cells, including 14 Markdown cells and 13 code cells.
- Data source: only the finalized `stock_train.npz`, `stock_val.npz`, and `stock_test.npz` artifacts plus the finalized stock target scaler. All four SHA-256 hashes remained unchanged after training.
- Verified shapes: TRAIN `(1915, 30, 5)`, validation `(411, 30, 5)`, and TEST `(410, 30, 5)`. Target dates are strictly increasing within each split and satisfy `TRAIN < validation < TEST`.
- Model: one-layer `torch.nn.RNN`, `batch_first=True`, input size 5, hidden size 64, `tanh`, final hidden state to `Linear(64, 1)`; 4,609 trainable parameters. No LSTM or GRU was used.
- Training: CPU, Adam with learning rate 0.001, `MSELoss` on the standardized target, batch size 64, gradient clipping norm 1.0, maximum 30 epochs, patience 5, seed 42.
- The 2026-09-27 clean audit run trained for 14 epochs in 5.61 seconds. Early stopping restored the raw minimum validation-loss checkpoint from epoch 9; best validation MSE in scaled target space was 0.0065248434. Predictive metrics remained identical to the earlier run; duration is environment/runtime-dependent.
- TEST was evaluated once after model selection. RNN outputs and TEST labels were inverse-transformed with the locked TRAIN-only target scaler before real-scale metrics were calculated.

| TEST model | MAE (USD) | RMSE (USD) | R² |
|---|---:|---:|---:|
| Vanilla RNN | 20.3393 | 23.5788 | -0.0269 |
| Naive: next Close = last observed Close | 2.6177 | 3.8789 | 0.9722 |

- The naive baseline decisively outperformed the Vanilla RNN on the same 410 TEST samples. No RNN-superiority claim is made; the result illustrates the importance of a persistence baseline and the difficulty of extrapolating a non-stationary price level beyond the TRAIN range.
- Predictions contain 410 chronological rows from 2024-05-14 through 2025-12-31 with `target_date`, `actual_close`, `predicted_close`, and `naive_close`; no missing values or duplicate dates were found.
- Three reusable figures were generated under `results/figures/pytorch_stock/` and visually checked.
- Verification: 31/31 project tests passed; `src/pytorch_stock.py` measured 86% line coverage with the standard-library tracer. Python bytecode compilation and `pip check` also passed.

## Notebook 06 execution record

- Notebook: `notebooks/06_Keras_Customer_RNN.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 11/11 code cells ran in order with execution counts 1–11 and no error output.
- Structure: 24 total cells, including 13 Markdown cells and 11 code cells.
- Fair-comparison data source: exactly the same finalized `customer_train.npz`, `customer_val.npz`, and `customer_test.npz` artifacts used by PyTorch. Shapes remain TRAIN `(247458, 8, 5)`, validation `(50354, 8, 5)`, and TEST `(53052, 8, 5)`; all three SHA-256 hashes remained unchanged.
- Model: one-layer `keras.layers.SimpleRNN(64, activation="tanh")` followed by `Dense(1, activation="sigmoid")`; 4,545 trainable parameters. The small parameter-count difference from PyTorch is caused by framework-specific RNN bias parameterization, not a change in model intent. No LSTM or GRU was used.
- Training: CPU, Adam with learning rate 0.001, binary cross-entropy, batch size 1,024, maximum 30 epochs, patience 5, seed 42, and `EarlyStopping(restore_best_weights=True)`.
- Class imbalance handling is equivalent in intent to PyTorch: Keras `class_weight={0: 1.0, 1: 14.226310607925178}` uses the same TRAIN-only negative/positive ratio. Validation sample weights reuse this TRAIN-derived mapping so validation-loss model selection is weighted consistently; validation labels do not define new weights.
- The 2026-09-27 clean audit run trained for 18 epochs in 86.01 seconds. The saved raw minimum validation-loss model came from epoch 16; best weighted validation binary cross-entropy was 0.9599091411. Predictive metrics remained identical to the earlier run; duration is environment/runtime-dependent.
- TEST was predicted once after model selection with the same fixed threshold 0.5 used by PyTorch. TEST did not participate in early stopping, class weighting, or threshold selection.

| TEST metric | Value |
|---|---:|
| Accuracy | 0.7600467466 |
| Precision | 0.1594323243 |
| Recall | 0.5697329377 |
| F1-score | 0.2491447446 |
| ROC-AUC | 0.7004916961 |

- TEST confusion matrix: TN 38,210; FP 11,135; FN 1,595; TP 2,112.
- Predictions contain 53,052 rows with `CustomerID`, `target_week`, `true_label`, `probability`, and `predicted_label`; no missing values or duplicate customer-week keys were found.
- Three reusable figures were generated under `results/figures/keras_customer/` and visually checked.
- No cross-framework winner is declared in Notebook 06; comparative interpretation remains reserved for Notebook 08.
- Verification: 38/38 project tests passed; `src/keras_customer.py` measured 87% line coverage with the standard-library tracer. The model reloaded successfully, CSV-derived metrics matched JSON, Python bytecode compilation passed, and `pip check` reported no broken requirements.

## Notebook 07 execution record

- Notebook: `notebooks/07_Keras_Stock_RNN.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 12/12 code cells ran in order with execution counts 1–12 and no error output.
- Structure: 25 total cells, including 13 Markdown cells and 12 code cells.
- Fair-comparison data source: exactly the same finalized `stock_train.npz`, `stock_val.npz`, and `stock_test.npz` artifacts and the same TRAIN-only stock target scaler used by PyTorch. Shapes remain TRAIN `(1915, 30, 5)`, validation `(411, 30, 5)`, and TEST `(410, 30, 5)`; all input/scaler SHA-256 hashes remained unchanged.
- The Keras and PyTorch prediction CSVs were independently verified to contain identical `target_date`, `actual_close`, and `naive_close` values on all 410 TEST rows.
- Model: one-layer `keras.layers.SimpleRNN(64, activation="tanh")` followed by `Dense(1, activation="linear")`; 4,545 trainable parameters. No sigmoid, LSTM, or GRU was used.
- Training: CPU, Adam with learning rate 0.001, MSE on the standardized target, batch size 64, maximum 30 epochs, patience 5, seed 42, and `EarlyStopping(restore_best_weights=True)`.
- Validation loss continued to improve through the maximum epoch, so EarlyStopping did not stop early. The 2026-09-27 clean audit run trained for all 30 epochs in 21.47 seconds; best epoch was 30 and best validation MSE in scaled target space was 0.0048658913. Predictive metrics remained identical to the earlier run; duration is environment/runtime-dependent.
- TEST was predicted once after model selection. Prediction and TEST target were inverse-transformed using the locked target scaler before real-scale metrics were calculated.

| TEST model | MAE (USD) | RMSE (USD) | R² |
|---|---:|---:|---:|
| Keras Vanilla RNN | 23.1947 | 27.8703 | -0.4347 |
| Naive: next Close = last observed Close | 2.6177 | 3.8789 | 0.9722 |

- The naive baseline decisively outperformed the Keras Vanilla RNN on the same 410 TEST samples. No RNN-superiority or investment claim is made.
- Predictions contain 410 chronological rows from 2024-05-14 through 2025-12-31 with `target_date`, `actual_close`, `predicted_close`, and `naive_close`; no missing values or duplicate dates were found.
- Three reusable figures were generated under `results/figures/keras_stock/` and visually checked.
- Verification: 44/44 project tests passed; `src/keras_stock.py` measured 89% line coverage with the standard-library tracer. The model reloaded successfully with a linear output, CSV-derived metrics matched JSON, Python bytecode compilation passed, and `pip check` reported no broken requirements.

## Notebook 08 execution record

- Notebook: `notebooks/08_Framework_Comparison.ipynb`
- Execution environment: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Execution result: success; 11/11 code cells ran in order with execution counts 1-11 and no error output.
- Structure: 26 total cells, including 15 Markdown cells and 11 code cells.
- Scope: artifact-only comparison. The notebook loads the four finalized metric JSON files, four prediction CSV files, and `preprocessing_metadata.json`; it contains no model construction, checkpoint loading, training, or optimizer execution.
- Provenance and fairness checks: customer prediction keys/labels align exactly across 53,052 TEST rows; stock `target_date`, `actual_close`, and `naive_close` align exactly across 410 chronological TEST rows; stored artifact hashes and preprocessing references were validated.
- Customer results are nearly identical rather than yielding a universal framework winner. PyTorch/Keras respectively achieved Accuracy 0.7582/0.7600, Precision 0.1587/0.1594, Recall 0.5722/0.5697, F1 0.2485/0.2491, and ROC-AUC 0.7009/0.7005. Their thresholded labels agree on 99.2536% of TEST rows and their predicted probabilities have correlation 0.9919.
- Customer implementation metadata is reported descriptively: PyTorch/Keras used 4,609/4,545 parameters, ran 11/18 epochs, took 151.06/86.01 seconds in the 2026-09-27 clean audit run, and both used CPU. Runtime is not treated as a universal framework benchmark.
- Stock baseline consistency was verified exactly between framework artifacts: naive MAE 2.6177 USD, RMSE 3.8789 USD, and R2 0.9722. PyTorch RNN recorded MAE 20.3393, RMSE 23.5788, R2 -0.0269; Keras SimpleRNN recorded MAE 23.1947, RMSE 27.8703, R2 -0.4347. Therefore neither RNN beat the naive baseline on this locked TEST set.
- Six reusable comparison figures were generated and visually checked under `results/figures/comparison/`.
- Machine-readable summary: `results/metrics/framework_comparison.json`; it records source paths and SHA-256 hashes, recomputed comparisons, agreement statistics, limitations, and the explicit flags `artifact_only_comparison=true` and `retraining_performed=false`.
- Verification: 50/50 project tests passed; `src/framework_comparison.py` measured 90% line coverage. Python bytecode compilation and `pip check` also passed.

## Full-project audit record

- Audit date: 2026-09-27.
- Report: `report/A06_AUDIT_REPORT.md`.
- Environment verifier: PASS using the locked `rnn312` interpreter; all required direct imports passed, PyTorch/TensorFlow both used CPU, and raw dataset hashes remained locked.
- Clean execution: outputs were cleared first; Notebooks 01–08 then ran in order using a new Jupyter kernel per notebook and a 1,800-second execution timeout. All 91/91 code cells ran with contiguous execution counts and zero error outputs.
- Final test suite: 50/50 passed. `compileall` passed and `pip check` reported no broken requirements.
- Leakage audit: exhaustive customer-window comparison confirmed inputs use only weeks `t-8...t-1` and labels use week `t`; exhaustive stock-window comparison confirmed inputs use only the 30 trading rows before the target row and `y` uses target-row Close.
- Chronology: customer TRAIN/VAL/TEST target ranges are 2010-02-01–2011-07-11, 2011-07-18–2011-09-19, and 2011-09-26–2011-11-28; stock ranges are 2015-02-17–2022-09-22, 2022-09-23–2024-05-13, and 2024-05-14–2025-12-31. No target overlap exists.
- TRAIN-only controls: customer and stock feature scaler statistics were independently recomputed from raw TRAIN windows; the stock target scaler was recomputed from TRAIN targets; customer class weight remained `14.226310607925178` from TRAIN labels only.
- Fairness: both frameworks use identical processed artifacts and aligned TEST rows. Customer keys/labels match across 53,052 rows; stock target dates, actual values and naive values match across 410 rows.
- Artifact consistency: all four saved models reload and reproduce their current prediction files within expected floating-point serialization precision; thresholded labels and all reported metrics match exactly. Notebook 08 was rerun last and references current metric/prediction hashes.
- Figure QA: 27/27 saved PNGs plus the embedded Notebook 01 gradient figure were checked and are nonblank, labeled and readable.
- Correctness fixes required: none. No source, protocol, split, scaler, model architecture or dataset change was needed. Audit execution refreshed notebooks, trained-model artifacts, metrics, predictions, figures and environment verification outputs.

## Generated artifacts

- `PROJECT_SPEC.md`
- `README.md`
- `src/download_stock_data.py` — one-time acquisition helper; refuses to overwrite the locked CSV
- `src/verify_environment.py`
- `tests/test_project_setup.py`
- `results/metrics/environment_verification.json`
- `results/metrics/environment_verification.md`
- `datasets/customer/online_retail_II.xlsx`
- `datasets/stock/AAPL_2015_2025.csv`
- `notebooks/01_RNN_Fundamentals.ipynb`
- `notebooks/02_Customer_Behavior_Data.ipynb`
- `notebooks/03_Stock_Data.ipynb`
- `src/config.py`
- `src/reproducibility.py`
- `src/preprocessing_utils.py`
- `src/customer_pipeline.py`
- `src/stock_pipeline.py`
- `src/run_preprocessing.py`
- `tests/test_preprocessing.py`
- `datasets/processed/customer_train.npz`
- `datasets/processed/customer_val.npz`
- `datasets/processed/customer_test.npz`
- `datasets/processed/stock_train.npz`
- `datasets/processed/stock_val.npz`
- `datasets/processed/stock_test.npz`
- `models/preprocessing/customer_feature_scaler.joblib`
- `models/preprocessing/stock_feature_scaler.joblib`
- `models/preprocessing/stock_target_scaler.joblib`
- `results/metrics/preprocessing_metadata.json`
- `notebooks/04_PyTorch_Customer_RNN.ipynb`
- `src/pytorch_customer.py`
- `tests/test_pytorch_customer.py`
- `models/pytorch/pytorch_customer_rnn_best.pt`
- `results/metrics/pytorch_customer_metrics.json`
- `results/predictions/pytorch_customer_predictions.csv`
- `results/figures/pytorch_customer/training_validation_loss.png`
- `results/figures/pytorch_customer/test_confusion_matrix.png`
- `results/figures/pytorch_customer/test_roc_curve.png`
- `notebooks/05_PyTorch_Stock_RNN.ipynb`
- `src/pytorch_stock.py`
- `tests/test_pytorch_stock.py`
- `models/pytorch/pytorch_stock_rnn_best.pt`
- `results/metrics/pytorch_stock_metrics.json`
- `results/predictions/pytorch_stock_predictions.csv`
- `results/figures/pytorch_stock/training_validation_loss.png`
- `results/figures/pytorch_stock/test_actual_vs_predicted.png`
- `results/figures/pytorch_stock/rnn_vs_naive_metrics.png`
- `notebooks/06_Keras_Customer_RNN.ipynb`
- `src/keras_customer.py`
- `tests/test_keras_customer.py`
- `models/keras/keras_customer_rnn_best.keras`
- `results/metrics/keras_customer_metrics.json`
- `results/predictions/keras_customer_predictions.csv`
- `results/figures/keras_customer/training_validation_loss.png`
- `results/figures/keras_customer/test_confusion_matrix.png`
- `results/figures/keras_customer/test_roc_curve.png`
- `notebooks/07_Keras_Stock_RNN.ipynb`
- `src/keras_stock.py`
- `tests/test_keras_stock.py`
- `models/keras/keras_stock_rnn_best.keras`
- `results/metrics/keras_stock_metrics.json`
- `results/predictions/keras_stock_predictions.csv`
- `results/figures/keras_stock/training_validation_loss.png`
- `results/figures/keras_stock/test_actual_vs_predicted.png`
- `results/figures/keras_stock/rnn_vs_naive_metrics.png`
- `notebooks/08_Framework_Comparison.ipynb`
- `src/framework_comparison.py`
- `tests/test_framework_comparison.py`
- `results/metrics/framework_comparison.json`
- `results/figures/comparison/customer_metrics_comparison.png`
- `results/figures/comparison/customer_confusion_matrices.png`
- `results/figures/comparison/customer_roc_comparison.png`
- `results/figures/comparison/customer_probability_behavior.png`
- `results/figures/comparison/stock_metrics_comparison.png`
- `results/figures/comparison/stock_actual_vs_predicted.png`
- `report/A06_AUDIT_REPORT.md`
- `results/figures/customer_eda/monthly_activity.png`
- `results/figures/customer_eda/customer_distributions.png`
- `results/figures/customer_eda/top_countries.png`
- `results/figures/customer_eda/inactive_week_example.png`
- `results/figures/customer_eda/prototype_label_balance.png`
- `results/figures/stock_eda/close_volume_history.png`
- `results/figures/stock_eda/ohlc_q4_2025.png`
- `results/figures/stock_eda/close_moving_averages.png`
- `results/figures/stock_eda/daily_return_distribution.png`
- `report/A06_Assignment_Report.docx`
- `report/A06_REPORT_BUILD_SUMMARY.md`

## Final assignment report

- Final Vietnamese academic report: `report/A06_Assignment_Report.docx`.
- Build summary and source traceability: `report/A06_REPORT_BUILD_SUMMARY.md`.
- The report uses the eight executed notebooks, current preprocessing metadata, current metrics JSON files, and 24 actual saved result figures.
- It contains 33 A4 pages, 20 report tables, 24 experimental/EDA figures, and 2 explanatory diagrams.
- The DOCX was reopened and validated programmatically, rendered with `artifact-tool`, and all 33 pages were inspected visually.
- Accessibility audit result: 0 high, 0 medium, and 0 low findings.
- No training, resplitting, model replacement, metric editing, or prediction editing was performed while building the report.
- Report build status: **PASSED**.

## Pending milestones

- None. The planned notebooks 01-08 and their supporting artifacts are complete.

## Deviations and manual action

- Deviations from `PROJECT_SPEC.md`: none.
- Manual action currently required: none.
- All planned artifact directories are populated; temporary audit/runtime files are not part of the deliverable.
