"""Deterministic customer-week preprocessing shared by both frameworks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import (
    CUSTOMER_COLUMN_ALIASES,
    CUSTOMER_FEATURES,
    CUSTOMER_REQUIRED_COLUMNS,
    CUSTOMER_SEQUENCE_LENGTH,
    CUSTOMER_WEEK_FREQUENCY,
    EXPECTED_CUSTOMER_SHA256,
    PREPROCESSING_MODEL_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_CUSTOMER_PATH,
    SPLIT_RATIOS,
)
from src.preprocessing_utils import (
    artifact_record,
    chronological_split_indices,
    fit_feature_scaler,
    iso_date,
    save_joblib_atomic,
    save_npz_atomic,
    sha256_file,
    transform_sequences,
)


def load_customer_workbook(path: Path = RAW_CUSTOMER_PATH) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read all raw sheets only after validating their actual schemas."""

    source = Path(path)
    frames: list[pd.DataFrame] = []
    sheet_info: list[dict[str, Any]] = []
    schemas: list[tuple[str, ...]] = []
    with pd.ExcelFile(source) as excel_file:
        sheet_names = list(excel_file.sheet_names)
        for sheet_name in sheet_names:
            frame = pd.read_excel(excel_file, sheet_name=sheet_name)
            frames.append(frame)
            schema = tuple(map(str, frame.columns))
            schemas.append(schema)
            sheet_info.append(
                {
                    "name": sheet_name,
                    "rows": int(len(frame)),
                    "columns": list(schema),
                    "dtypes": {
                        column: str(dtype) for column, dtype in frame.dtypes.items()
                    },
                }
            )

    if not frames:
        raise ValueError("customer workbook has no sheets")
    if any(schema != schemas[0] for schema in schemas[1:]):
        raise ValueError("customer workbook sheets have incompatible schemas")

    combined = pd.concat(frames, ignore_index=True)
    return combined, {"sheet_names": sheet_names, "sheets": sheet_info}


def normalize_customer_columns(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Normalize historical names in memory and validate the required schema."""

    rename_map = {
        source: target
        for source, target in CUSTOMER_COLUMN_ALIASES.items()
        if source in raw.columns
    }
    normalized = raw.rename(columns=rename_map).copy()
    if normalized.columns.duplicated().any():
        raise ValueError("column normalization produced duplicate column names")
    missing = sorted(set(CUSTOMER_REQUIRED_COLUMNS) - set(normalized.columns))
    if missing:
        raise ValueError(f"customer data is missing required columns: {missing}")
    return normalized, rename_map


def clean_customer_transactions(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply the purchase-only cleaning rules confirmed in Notebook 02."""

    data, _ = normalize_customer_columns(raw)
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    for column in ("CustomerID", "Quantity", "UnitPrice"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    invoice_text = data["InvoiceNo"].astype("string").str.strip()
    cancellation = invoice_text.str.upper().str.startswith("C", na=False)
    customer_integer = data["CustomerID"].mod(1).eq(0).fillna(False)
    valid_customer = data["CustomerID"].notna() & data["CustomerID"].gt(0) & customer_integer

    duplicate_count = int(data.duplicated().sum())
    counts = {
        "raw_rows": int(len(data)),
        "exact_duplicates_removed": duplicate_count,
        "invalid_or_missing_customer_id_raw": int((~valid_customer).sum()),
        "invalid_invoice_date_raw": int(data["InvoiceDate"].isna().sum()),
        "cancellation_lines_raw": int(cancellation.sum()),
        "nonpositive_quantity_lines_raw": int(data["Quantity"].le(0).fillna(True).sum()),
        "nonpositive_unit_price_lines_raw": int(data["UnitPrice"].le(0).fillna(True).sum()),
    }

    deduplicated = data.drop_duplicates().copy()
    dedup_invoice_text = deduplicated["InvoiceNo"].astype("string").str.strip()
    dedup_cancellation = dedup_invoice_text.str.upper().str.startswith("C", na=False)
    dedup_integer_customer = deduplicated["CustomerID"].mod(1).eq(0).fillna(False)
    clean_mask = (
        deduplicated["CustomerID"].notna()
        & deduplicated["CustomerID"].gt(0)
        & dedup_integer_customer
        & deduplicated["InvoiceDate"].notna()
        & ~dedup_cancellation
        & deduplicated["Quantity"].gt(0)
        & deduplicated["UnitPrice"].gt(0)
    )

    clean = deduplicated.loc[clean_mask].copy()
    clean["InvoiceNo"] = clean["InvoiceNo"].astype("string").str.strip()
    clean["CustomerID"] = clean["CustomerID"].astype("int64")
    clean["Revenue"] = clean["Quantity"] * clean["UnitPrice"]
    if not clean["Revenue"].gt(0).all():
        raise AssertionError("cleaned customer Revenue must be strictly positive")

    counts.update(
        {
            "cleaned_rows": int(len(clean)),
            "cleaned_customers": int(clean["CustomerID"].nunique()),
            "cleaned_invoices": int(clean["InvoiceNo"].nunique()),
        }
    )
    return clean, counts


def aggregate_customer_weeks(clean: pd.DataFrame) -> pd.DataFrame:
    """Aggregate valid purchase lines to active customer-week rows."""

    required = {"CustomerID", "InvoiceDate", "InvoiceNo", "StockCode", "Quantity", "Revenue"}
    missing = sorted(required - set(clean.columns))
    if missing:
        raise ValueError(f"clean customer data is missing columns: {missing}")

    data = clean.copy()
    data["WeekStart"] = data["InvoiceDate"].dt.to_period("W-SUN").dt.start_time
    weekly = (
        data.groupby(["CustomerID", "WeekStart"], observed=True, sort=True)
        .agg(
            total_spent=("Revenue", "sum"),
            total_quantity=("Quantity", "sum"),
            order_count=("InvoiceNo", "nunique"),
            unique_products=("StockCode", "nunique"),
        )
        .reset_index()
        .sort_values(["CustomerID", "WeekStart"], kind="stable")
        .reset_index(drop=True)
    )
    weekly["active_flag"] = np.int8(1)
    if weekly.duplicated(["CustomerID", "WeekStart"]).any():
        raise AssertionError("customer-week aggregation produced duplicate keys")
    if not weekly["order_count"].ge(1).all():
        raise AssertionError("active customer weeks must contain at least one unique invoice")
    return weekly


def full_week_bounds(active_weekly: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Exclude the two partial boundary weeks identified in Notebook 02."""

    first_observed = pd.Timestamp(active_weekly["WeekStart"].min())
    last_observed = pd.Timestamp(active_weekly["WeekStart"].max())
    first_full = first_observed + pd.Timedelta(weeks=1)
    last_full = last_observed - pd.Timedelta(weeks=1)
    if first_full >= last_full:
        raise ValueError("customer observation period has too few complete weeks")
    return first_full, last_full


def build_customer_sequences(
    active_weekly: pd.DataFrame,
    *,
    sequence_length: int = CUSTOMER_SEQUENCE_LENGTH,
    first_full_week: pd.Timestamp,
    last_full_week: pd.Timestamp,
) -> dict[str, np.ndarray]:
    """Create regular zero-filled histories and next-week binary targets."""

    if sequence_length <= 0:
        raise ValueError("sequence_length must be positive")
    missing = sorted(
        {"CustomerID", "WeekStart", *CUSTOMER_FEATURES} - set(active_weekly.columns)
    )
    if missing:
        raise ValueError(f"active weekly data is missing columns: {missing}")

    weekly = active_weekly.copy()
    weekly["WeekStart"] = pd.to_datetime(weekly["WeekStart"], errors="raise")
    weekly = weekly.sort_values(["CustomerID", "WeekStart"], kind="stable")
    if weekly.duplicated(["CustomerID", "WeekStart"]).any():
        raise ValueError("active_weekly must contain one row per customer-week")
    if not weekly["active_flag"].eq(1).all():
        raise ValueError("active_weekly rows must all have active_flag=1")

    first_full = pd.Timestamp(first_full_week)
    last_full = pd.Timestamp(last_full_week)
    feature_arrays: list[np.ndarray] = []
    target_arrays: list[np.ndarray] = []
    customer_arrays: list[np.ndarray] = []
    week_arrays: list[np.ndarray] = []

    for customer_id, customer_rows in weekly.groupby("CustomerID", sort=True, observed=True):
        timeline_start = max(pd.Timestamp(customer_rows["WeekStart"].min()), first_full)
        if timeline_start > last_full:
            continue
        week_index = pd.date_range(timeline_start, last_full, freq=CUSTOMER_WEEK_FREQUENCY)
        if len(week_index) <= sequence_length:
            continue

        timeline = (
            customer_rows.set_index("WeekStart")
            .reindex(week_index)[list(CUSTOMER_FEATURES)]
            .fillna(0.0)
        )
        values = timeline.to_numpy(dtype=np.float32)
        windows = np.lib.stride_tricks.sliding_window_view(
            values, window_shape=sequence_length, axis=0
        )[:-1].transpose(0, 2, 1).copy()
        targets = values[sequence_length:, CUSTOMER_FEATURES.index("active_flag")].astype(
            np.int8
        )
        target_weeks = week_index[sequence_length:].to_numpy(dtype="datetime64[D]")

        if len(windows) != len(targets):
            raise AssertionError("customer windows and targets are misaligned")
        feature_arrays.append(windows)
        target_arrays.append(targets)
        customer_arrays.append(np.full(len(targets), int(customer_id), dtype=np.int64))
        week_arrays.append(target_weeks)

    if not feature_arrays:
        raise ValueError("no eligible customer sequences were generated")

    result = {
        "X": np.concatenate(feature_arrays),
        "y": np.concatenate(target_arrays),
        "customer_id": np.concatenate(customer_arrays),
        "target_week": np.concatenate(week_arrays),
    }
    if result["X"].shape[1:] != (sequence_length, len(CUSTOMER_FEATURES)):
        raise AssertionError("customer sequence shape does not match the contract")
    return result


def _class_distribution(labels: np.ndarray) -> dict[str, Any]:
    counts = np.bincount(labels.astype(np.int64), minlength=2)
    total = int(counts.sum())
    return {
        "class_0": int(counts[0]),
        "class_1": int(counts[1]),
        "class_0_rate": float(counts[0] / total),
        "class_1_rate": float(counts[1] / total),
    }


def prepare_customer_data(
    raw_path: Path = RAW_CUSTOMER_PATH,
    processed_dir: Path = PROCESSED_DIR,
    scaler_dir: Path = PREPROCESSING_MODEL_DIR,
) -> dict[str, Any]:
    """Run the complete customer preprocessing stage and save shared artifacts."""

    source = Path(raw_path)
    source_hash_before = sha256_file(source)
    if source_hash_before != EXPECTED_CUSTOMER_SHA256:
        raise ValueError("locked customer workbook checksum does not match PROJECT_SPEC state")

    raw, workbook_info = load_customer_workbook(source)
    normalized_preview, rename_map = normalize_customer_columns(raw.iloc[:0])
    del normalized_preview
    clean, cleaning_counts = clean_customer_transactions(raw)
    del raw
    active_weekly = aggregate_customer_weeks(clean)
    clean_date_min = pd.Timestamp(clean["InvoiceDate"].min())
    clean_date_max = pd.Timestamp(clean["InvoiceDate"].max())
    del clean

    first_full_week, last_full_week = full_week_bounds(active_weekly)
    sequences = build_customer_sequences(
        active_weekly,
        sequence_length=CUSTOMER_SEQUENCE_LENGTH,
        first_full_week=first_full_week,
        last_full_week=last_full_week,
    )
    active_week_rows = int(len(active_weekly))
    del active_weekly

    split_indices = chronological_split_indices(sequences["target_week"])
    raw_split_x: dict[str, np.ndarray] = {}
    split_payloads: dict[str, dict[str, np.ndarray]] = {}
    for split_name, indices in split_indices.items():
        order = np.lexsort(
            (sequences["customer_id"][indices], sequences["target_week"][indices])
        )
        ordered_indices = indices[order]
        raw_split_x[split_name] = sequences["X"][ordered_indices]
        split_payloads[split_name] = {
            "y": sequences["y"][ordered_indices],
            "customer_id": sequences["customer_id"][ordered_indices],
            "target_week": sequences["target_week"][ordered_indices],
        }
    del sequences

    feature_scaler = fit_feature_scaler(raw_split_x["train"])
    feature_scaler_path = Path(scaler_dir) / "customer_feature_scaler.joblib"
    save_joblib_atomic(feature_scaler_path, feature_scaler)

    artifact_paths: dict[str, Path] = {}
    for split_name in ("train", "val", "test"):
        artifact_path = Path(processed_dir) / f"customer_{split_name}.npz"
        payload = split_payloads[split_name]
        save_npz_atomic(
            artifact_path,
            X=transform_sequences(feature_scaler, raw_split_x[split_name]),
            y=payload["y"].astype(np.int8, copy=False),
            customer_id=payload["customer_id"].astype(np.int64, copy=False),
            target_week=payload["target_week"].astype("datetime64[D]", copy=False),
        )
        artifact_paths[split_name] = artifact_path

    train_distribution = _class_distribution(split_payloads["train"]["y"])
    if train_distribution["class_1"] == 0:
        raise ValueError("TRAIN customer split has no positive labels")
    positive_weight = train_distribution["class_0"] / train_distribution["class_1"]

    source_hash_after = sha256_file(source)
    if source_hash_after != source_hash_before:
        raise AssertionError("raw customer workbook changed during preprocessing")

    split_metadata: dict[str, Any] = {}
    for split_name in ("train", "val", "test"):
        payload = split_payloads[split_name]
        split_metadata[split_name] = {
            "X_shape": [
                int(len(payload["y"])),
                CUSTOMER_SEQUENCE_LENGTH,
                len(CUSTOMER_FEATURES),
            ],
            "y_shape": [int(len(payload["y"]))],
            "target_week_min": iso_date(payload["target_week"].min()),
            "target_week_max": iso_date(payload["target_week"].max()),
            "sample_ratio": float(
                len(payload["y"]) / sum(len(v["y"]) for v in split_payloads.values())
            ),
            "class_distribution": _class_distribution(payload["y"]),
        }

    return {
        "raw_source": {
            "path": source.relative_to(PROJECT_ROOT).as_posix(),
            "sha256_before": source_hash_before,
            "sha256_after": source_hash_after,
            "workbook": workbook_info,
        },
        "column_normalization": rename_map,
        "cleaning_rules": [
            "remove exact duplicate rows",
            "require positive integer CustomerID",
            "require valid InvoiceDate",
            "exclude InvoiceNo values beginning with C (case-insensitive)",
            "require Quantity > 0",
            "require UnitPrice > 0",
            "Revenue = Quantity * UnitPrice",
        ],
        "cleaning_counts": cleaning_counts,
        "cleaned_date_range": {
            "min": clean_date_min.isoformat(),
            "max": clean_date_max.isoformat(),
        },
        "weekly_definition": {
            "week": "Monday through Sunday; WeekStart is Monday",
            "total_spent": "sum of Revenue within customer-week",
            "total_quantity": "sum of positive Quantity within customer-week",
            "order_count": "number of unique InvoiceNo values within customer-week",
            "unique_products": "number of unique StockCode values within customer-week",
            "active_flag": "1 for at least one valid purchase, otherwise 0 after reindexing",
            "active_customer_week_rows": active_week_rows,
        },
        "eligibility_policy": {
            "first_full_week": iso_date(first_full_week),
            "last_full_week": iso_date(last_full_week),
            "timeline_start": "max(customer first purchase week, first_full_week)",
            "timeline_end": "last_full_week for every eligible customer",
            "inactive_week_fill": 0,
            "required_history_weeks": CUSTOMER_SEQUENCE_LENGTH,
        },
        "feature_names": list(CUSTOMER_FEATURES),
        "sequence_length": CUSTOMER_SEQUENCE_LENGTH,
        "target_definition": "active_flag of the immediately following week",
        "task": "binary classification",
        "split_strategy": {
            "basis": "target_week",
            "ratios_requested": dict(SPLIT_RATIOS),
            "boundary_rule": "nearest cumulative sample count without splitting a target_week",
            "context_rule": "validation/test inputs may use earlier known history",
        },
        "splits": split_metadata,
        "feature_scaler": {
            "type": "sklearn.preprocessing.StandardScaler",
            "fit_scope": "flattened TRAIN X only",
            "n_samples_seen": int(feature_scaler.n_samples_seen_),
            "mean": feature_scaler.mean_.tolist(),
            "scale": feature_scaler.scale_.tolist(),
            **artifact_record(feature_scaler_path, PROJECT_ROOT),
        },
        "class_weight": {
            "positive_weight": float(positive_weight),
            "formula": "TRAIN class_0 count / TRAIN class_1 count",
            "fit_scope": "TRAIN y only",
        },
        "artifacts": {
            name: artifact_record(path, PROJECT_ROOT) for name, path in artifact_paths.items()
        },
    }
