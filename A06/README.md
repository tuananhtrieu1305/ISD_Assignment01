# Assignment 06 — RNN on Customer Behavior and AAPL

A06 is an isolated project for learning and applying Vanilla RNN models with PyTorch and Keras. The two locked tasks are next-week customer purchase classification and next-trading-day AAPL Close regression.

Initialization is complete. Raw data and environment checks pass; no notebook has been implemented and no model has been trained yet.

## Source of truth

- `PROJECT_SPEC.md` is the permanent experiment contract.
- `CURRENT_STATE.md` records actual versions, data metadata, completed work, and pending work.
- Every later milestone must read both files before making changes.

## Environment

```powershell
& 'C:\Users\anhca\anaconda3\shell\condabin\conda-hook.ps1'
conda activate rnn312
Set-Location 'C:\DATA\assign\A06'
```

If shell activation is unavailable, call the interpreter directly:

```powershell
& 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe' --version
```

## Verify the initialization

```powershell
& 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe' .\src\verify_environment.py
```

This rewrites the small verification reports at:

- `results/metrics/environment_verification.json`
- `results/metrics/environment_verification.md`

## Locked raw data

- `datasets/customer/online_retail_II.xlsx`: UCI Online Retail II, Dataset ID 502
- `datasets/stock/AAPL_2015_2025.csv`: fixed unadjusted-download snapshot for 2015-01-01 through 2025-12-31 inclusive

Do not edit either raw file. Later notebooks must use the local AAPL CSV and must not redownload market data. The acquisition helper in `src/download_stock_data.py` refuses to overwrite an existing snapshot.

## Planned notebooks

```text
01_RNN_Fundamentals.ipynb
02_Customer_Behavior_Data.ipynb
03_Stock_Data.ipynb
04_PyTorch_Customer_RNN.ipynb
05_PyTorch_Stock_RNN.ipynb
06_Keras_Customer_RNN.ipynb
07_Keras_Stock_RNN.ipynb
08_Framework_Comparison.ipynb
```

Notebook narrative must be in Vietnamese, with standard English technical terms retained where natural. The next authorized milestone is Notebook 01 only.
