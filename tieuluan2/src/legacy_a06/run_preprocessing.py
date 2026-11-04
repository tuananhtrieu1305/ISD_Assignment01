"""Command-line entry point for all shared A06 preprocessing artifacts."""

from __future__ import annotations

import platform
import sys

import numpy as np
import pandas as pd
import sklearn

from src.config import (
    PREPROCESSING_METADATA_PATH,
    PROJECT_ROOT,
    RAW_CUSTOMER_PATH,
    RAW_STOCK_PATH,
    SEED,
    SPLIT_RATIOS,
    ensure_output_directories,
)
from src.customer_pipeline import prepare_customer_data
from src.preprocessing_utils import write_json_atomic
from src.reproducibility import set_global_seed
from src.stock_pipeline import prepare_stock_data


def run_all_preprocessing() -> dict[str, object]:
    """Build both tasks once so all later frameworks consume identical arrays."""

    ensure_output_directories()
    set_global_seed(SEED)

    customer_metadata = prepare_customer_data()
    stock_metadata = prepare_stock_data()
    metadata: dict[str, object] = {
        "schema_version": 1,
        "generator": "src.run_preprocessing",
        "seed": SEED,
        "raw_dataset_paths": {
            "customer": RAW_CUSTOMER_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "stock": RAW_STOCK_PATH.relative_to(PROJECT_ROOT).as_posix(),
        },
        "split_ratios_requested": dict(SPLIT_RATIOS),
        "runtime": {
            "python": platform.python_version(),
            "executable": sys.executable,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "customer": customer_metadata,
        "stock": stock_metadata,
    }
    write_json_atomic(PREPROCESSING_METADATA_PATH, metadata)
    return metadata


def _print_summary(metadata: dict[str, object]) -> None:
    print(f"Metadata: {PREPROCESSING_METADATA_PATH}")
    for task in ("customer", "stock"):
        task_metadata = metadata[task]
        print(task.capitalize() + ":")
        for split_name in ("train", "val", "test"):
            shape = task_metadata["splits"][split_name]["X_shape"]
            print(f"  {split_name:>5} X {tuple(shape)}")


if __name__ == "__main__":
    _print_summary(run_all_preprocessing())
