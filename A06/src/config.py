"""Single source of truth for deterministic A06 preprocessing."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SEED = 42
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}

RAW_CUSTOMER_PATH = PROJECT_ROOT / "datasets" / "customer" / "online_retail_II.xlsx"
RAW_STOCK_PATH = PROJECT_ROOT / "datasets" / "stock" / "AAPL_2015_2025.csv"
PROCESSED_DIR = PROJECT_ROOT / "datasets" / "processed"
PREPROCESSING_MODEL_DIR = PROJECT_ROOT / "models" / "preprocessing"
METRICS_DIR = PROJECT_ROOT / "results" / "metrics"
PREPROCESSING_METADATA_PATH = METRICS_DIR / "preprocessing_metadata.json"

EXPECTED_CUSTOMER_SHA256 = (
    "bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980"
)
EXPECTED_STOCK_SHA256 = (
    "2c8eef3c6a3836e2217bf3e99faaeec37d30e60298f7319e8f3748b71e5bd2b8"
)

CUSTOMER_COLUMN_ALIASES = {
    "Invoice": "InvoiceNo",
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
}
CUSTOMER_REQUIRED_COLUMNS = (
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
)
CUSTOMER_FEATURES = (
    "total_spent",
    "total_quantity",
    "order_count",
    "unique_products",
    "active_flag",
)
CUSTOMER_SEQUENCE_LENGTH = 8
CUSTOMER_WEEK_FREQUENCY = "W-MON"

STOCK_REQUIRED_COLUMNS = (
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
)
STOCK_FEATURES = ("Open", "High", "Low", "Close", "Volume")
STOCK_SEQUENCE_LENGTH = 30


def ensure_output_directories() -> None:
    """Create only the directories owned by the preprocessing milestone."""

    for directory in (PROCESSED_DIR, PREPROCESSING_MODEL_DIR, METRICS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

