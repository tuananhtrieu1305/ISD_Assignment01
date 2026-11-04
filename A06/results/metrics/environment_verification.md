# A06 Environment Verification

- Status: **PASS**
- Generated: `2026-09-27T18:40:31+07:00`
- Interpreter: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Python: `3.12.14`
- Direct package imports: `PASS`
- PyTorch CUDA available: `False`
- TensorFlow physical devices: `[{'name': '/physical_device:CPU:0', 'type': 'CPU'}]`

## Required package versions

- `numpy==2.5.3`
- `pandas==3.0.6`
- `matplotlib==3.11.2`
- `scikit-learn==1.9.1`
- `openpyxl==3.1.5`
- `jupyter==1.1.1`
- `ipykernel==7.3.0`
- `pytest==9.1.1`
- `joblib==1.6.0`
- `torch==2.14.0`
- `tensorflow==2.21.0`
- `keras==3.15.1`
- `yfinance==1.7.0`

## Dataset checks

- Customer workbook: `2` sheets, `1067371` data rows, SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
  - `Year 2009-2010`: `525461` rows; columns: `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`
  - `Year 2010-2011`: `541910` rows; columns: `Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`
- Stock CSV: `2766` rows, `2015-01-02` through `2025-12-31`, SHA-256 `2c8eef3c6a3836e2217bf3e99faaeec37d30e60298f7319e8f3748b71e5bd2b8`.
  - Columns: `Date`, `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`
  - Chronological: `True`; duplicate dates: `0`.
