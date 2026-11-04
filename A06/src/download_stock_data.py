"""Download the locked AAPL snapshot exactly once for Assignment 06."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "datasets" / "stock" / "AAPL_2015_2025.csv"
START_DATE = "2015-01-01"
# yfinance treats `end` as exclusive, so 2026-01-01 includes 2025-12-31.
END_DATE_EXCLUSIVE = "2026-01-01"
EXPECTED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]


def main() -> None:
    if OUTPUT_PATH.exists():
        raise FileExistsError(
            f"Refusing to overwrite the locked local snapshot: {OUTPUT_PATH}"
        )

    data = yf.download(
        "AAPL",
        start=START_DATE,
        end=END_DATE_EXCLUSIVE,
        auto_adjust=False,
        actions=False,
        repair=False,
        progress=False,
        threads=False,
        multi_level_index=False,
    )
    if data.empty:
        raise RuntimeError("yfinance returned no AAPL rows for the locked interval")

    data = data.reset_index()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise").dt.date
    missing = [column for column in EXPECTED_COLUMNS if column not in data.columns]
    if missing:
        raise RuntimeError(f"Downloaded data is missing required columns: {missing}")

    data = data.loc[:, EXPECTED_COLUMNS]
    dates = pd.to_datetime(data["Date"])
    if dates.min() < pd.Timestamp(START_DATE) or dates.max() > pd.Timestamp("2025-12-31"):
        raise RuntimeError("Downloaded dates fall outside the locked interval")
    if dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise RuntimeError("Downloaded dates are duplicated or not chronological")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_PATH, index=False, date_format="%Y-%m-%d")
    print(f"Saved {len(data):,} rows to {OUTPUT_PATH}")
    print(f"Trading-date range: {dates.min().date()} through {dates.max().date()}")


if __name__ == "__main__":
    main()
