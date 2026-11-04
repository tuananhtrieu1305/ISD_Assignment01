"""Source-level counts and schema validation only. No EDA, splits or TEST evaluation."""

from __future__ import annotations

import io
import re
import tarfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from src.common.acquisition import AcquisitionError


def require(condition, message):
    if not condition:
        raise AcquisitionError(message)


def normalize_column(name):
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(name).strip())
    name = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return name if name and name[0].isalpha() else "v_" + name


def column_contracts(frame, target, ids=frozenset(), times=frozenset()):
    result = []
    for raw in frame.columns:
        name = normalize_column(raw)
        series = frame[raw]
        dtype = (
            "integer"
            if pd.api.types.is_integer_dtype(series)
            else ("number" if pd.api.types.is_numeric_dtype(series) else "string")
        )
        role = (
            "target"
            if name == target
            else ("id" if name in ids else ("time" if name in times else "feature"))
        )
        result.append({"name": name, "dtype": dtype, "role": role})
    require(len({row["name"] for row in result}) == len(result), "Column alias collision")
    return result


def _table(frame, *, rows, target, ids=frozenset(), exclude=frozenset(), aliases=None):
    require(len(frame) == rows, f"Unexpected record count: {len(frame)} != {rows}")
    columns = column_contracts(frame, target, ids)
    require(any(row["role"] == "target" for row in columns), f"Missing target {target}")
    return {
        "records": len(frame),
        "features": sum(row["role"] == "feature" and row["name"] not in exclude for row in columns),
        "unit": "raw rows",
        "columns": columns,
        "observed_columns": list(frame.columns),
        "raw_to_contract_aliases": aliases or {raw: normalize_column(raw) for raw in frame.columns},
        "excluded_feature_columns": sorted(ids | exclude),
        "checks": ["row_count", "column_schema"],
    }


def inspect_source(dataset_id, path):
    path = Path(path)
    if dataset_id == "ch1_iris_history":
        with zipfile.ZipFile(path) as archive:
            frame = pd.read_csv(
                archive.open("iris.data"),
                header=None,
                names=["sepal_length", "sepal_width", "petal_length", "petal_width", "species"],
            )
        require(frame.shape == (150, 5) and frame.species.nunique() == 3, "Invalid Iris schema")
        return _table(frame, rows=150, target="species")
    if dataset_id == "ch1_mnist_history":
        with np.load(path, allow_pickle=False) as data:
            require(set(data.files) == {"x_train", "y_train", "x_test", "y_test"}, "MNIST keys changed")
            for split, count in (("train", 60000), ("test", 10000)):
                require(data[f"x_{split}"].shape == (count, 28, 28), "Invalid MNIST images")
                require(data[f"x_{split}"].dtype == np.uint8, "Invalid MNIST pixel dtype")
                require(
                    data[f"y_{split}"].shape == (count,)
                    and set(np.unique(data[f"y_{split}"])) == set(range(10)),
                    "Invalid MNIST labels",
                )
        return {
            "records": 70000,
            "features": 784,
            "unit": "images (official 60000 train + 10000 test)",
            "columns": [],
            "checks": ["npz_no_pickle", "shape", "dtype", "label_range"],
            "native_shape": [28, 28, 1],
        }
    if dataset_id == "ch1_imagenet_history":
        text = path.read_text(encoding="utf-8")
        require("ILSVRC2012" in text and "1000" in text, "Not the ILSVRC2012 page")
        return {
            "records": 1,
            "features": None,
            "unit": "official metadata webpage, ZERO local images",
            "columns": [],
            "checks": ["official_page_identity"],
            "published_not_measured": {"categories": 1000, "training_images_approx": 1200000},
        }
    if dataset_id == "ch2_cdc_diabetes":
        frame = pd.read_csv(path)
        require(
            frame.shape == (253680, 23) and "Diabetes_binary" in frame and "ID" in frame,
            "UCI CDC schema changed; do not substitute a three-class or balanced variant",
        )
        require(set(frame.Diabetes_binary.unique()) == {0, 1}, "CDC binary labels changed")
        return _table(frame, rows=253680, target="diabetes_binary", ids={"id"})
    if dataset_id == "ch2_ames_housing":
        frame = pd.read_csv(path, sep="\t")
        require(
            frame.shape == (2930, 82) and "SalePrice" in frame,
            "Require original Ames, not processed 2929 rows",
        )
        require((frame.SalePrice > 0).all(), "Ames invalid target")
        return _table(frame, rows=2930, target="sale_price", ids={"pid", "order"})
    if dataset_id == "ch2_bank_marketing":
        with zipfile.ZipFile(path) as outer, zipfile.ZipFile(io.BytesIO(outer.read("bank.zip"))) as inner:
            frame = pd.read_csv(inner.open("bank-full.csv"), sep=";")
        require(frame.shape == (45211, 17) and set(frame.y.unique()) == {"yes", "no"}, "Wrong Bank variant")
        frame = frame.rename(columns={"y": "subscription"})
        result = _table(frame, rows=45211, target="subscription", exclude={"duration"})
        result["selected_member"] = "bank.zip!bank-full.csv"
        result["observed_columns"] = ["y" if name == "subscription" else name for name in frame.columns]
        result["raw_to_contract_aliases"].pop("subscription")
        result["raw_to_contract_aliases"]["y"] = "subscription"
        return result
    if dataset_id == "ch3_eurosat":
        classes, shapes, images = set(), set(), 0
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.lower().endswith(".jpg"):
                    continue
                with archive.open(name) as handle, Image.open(handle) as picture:
                    picture.load()
                    shapes.add((*picture.size, picture.mode))
                classes.add(Path(name).parent.name)
                images += 1
        require(
            images == 27000 and len(classes) == 10 and shapes == {(64, 64, "RGB")},
            "EuroSAT RGB schema mismatch",
        )
        return {
            "records": images,
            "features": 64 * 64 * 3,
            "unit": "RGB image patches",
            "columns": [],
            "native_shape": [64, 64, 3],
            "class_names": sorted(classes),
            "checks": ["all_images_decode", "image_count", "class_count", "native_shape"],
        }
    if dataset_id == "ch3_cifar10":
        counts = {}
        with tarfile.open(path, "r:gz") as archive:
            for member in archive:
                if not re.fullmatch(r"cifar-10-batches-bin/(data_batch_[1-5]|test_batch)\.bin", member.name):
                    continue
                with archive.extractfile(member) as handle:
                    array = np.frombuffer(handle.read(), dtype=np.uint8)
                require(array.size == 10000 * 3073, "CIFAR binary record length mismatch")
                require(
                    set(np.unique(array.reshape(10000, 3073)[:, 0])) == set(range(10)), "CIFAR labels invalid"
                )
                counts[member.name] = 10000
        require(len(counts) == 6, "CIFAR missing official batches")
        return {
            "records": sum(counts.values()),
            "features": 3072,
            "unit": "images (50000 train + 10000 test)",
            "columns": [],
            "native_shape": [32, 32, 3],
            "batch_counts": counts,
            "checks": ["binary_not_pickle", "record_length", "batch_count", "label_range"],
        }
    if dataset_id == "ch4_gold_pink_sheet":
        return _gold(path)
    if dataset_id == "ch4_bis_house_prices":
        return _bis(path)
    if dataset_id == "ch4_household_power":
        with zipfile.ZipFile(path) as archive:
            name = "household_power_consumption.txt"
            records, headers = 0, None
            with io.TextIOWrapper(archive.open(name), encoding="utf-8") as handle:
                headers = handle.readline().strip().split(";")
                for line in handle:
                    require(len(line.rstrip().split(";")) == 9, "Power malformed record")
                    records += 1
        require(
            records == 2075259 and len(headers) == 9 and "Global_active_power" in headers,
            "Power release mismatch",
        )
        return {
            "records": records,
            "features": 7,
            "unit": "raw minute rows, NOT hourly training windows",
            "columns": [
                {
                    "name": normalize_column(c),
                    "dtype": "string" if i < 2 else "number",
                    "role": "time" if i < 2 else ("target" if i == 2 else "feature"),
                }
                for i, c in enumerate(headers)
            ],
            "observed_columns": headers,
            "checks": ["raw_line_count", "row_width", "column_schema"],
            "deferred": "Phase24 causal hourly aggregation and missingness handling; raw '?' retained.",
        }
    raise AcquisitionError(f"No source inspector: {dataset_id}")


def _gold(path):
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        require("Monthly Prices" in workbook.sheetnames, f"Gold sheets changed: {workbook.sheetnames}")
        rows = list(workbook["Monthly Prices"].values)
        header_index = next(i for i, row in enumerate(rows) if "Gold" in row)
        headers = rows[header_index]
        indices = {name: headers.index(name) for name in ("Gold", "Silver", "Platinum", "Crude oil, average")}
        records = [row for row in rows[header_index + 1 :] if re.fullmatch(r"\d{4}M\d{2}", str(row[0]))]
        require(len(records) > 600, "Gold history unexpectedly short")
        require(
            all(isinstance(row[indices["Gold"]], (int, float)) for row in records),
            "Gold target missing/nonnumeric",
        )
        return {
            "records": len(records),
            "features": 4,
            "unit": "monthly observations, latest revised vintage",
            "columns": [{"name": "month", "dtype": "datetime", "role": "time"}]
            + [
                {
                    "name": {"Gold": "gold_usd_per_troy_ounce", "Crude oil, average": "crude_oil"}.get(
                        name, normalize_column(name)
                    ),
                    "dtype": "number",
                    "role": "target" if name == "Gold" else "feature",
                }
                for name in indices
            ],
            "observed_columns": [str(name) for name in headers],
            "raw_to_contract_aliases": {"Gold": "gold_usd_per_troy_ounce", "Crude oil, average": "crude_oil"},
            "time_range": [str(records[0][0]), str(records[-1][0])],
            "selected_column_indices": indices,
            "checks": ["sheet_schema", "required_commodity_columns", "numeric_gold", "history_length"],
            "deferred": "Phase24 uses gold plus explanatory commodities with one-period lag; no windows fitted here.",
        }
    finally:
        workbook.close()


def _bis(path):
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        require(len(names) == 1, f"BIS archive schema changed: {names}")
        frame = pd.read_csv(archive.open(names[0]), low_memory=False)
    time_columns = [name for name in frame if re.fullmatch(r"\d{4}-Q[1-4]", name)]
    require(
        len(time_columns) >= 80 and "FREQ" in frame and "REF_AREA" in frame,
        f"BIS unexpected columns: {list(frame)[:25]}",
    )
    observations = int(frame[time_columns].apply(pd.to_numeric, errors="coerce").notna().sum().sum())
    return {
        "records": observations,
        "features": None,
        "unit": "nonmissing quarterly series-observations in entire raw bulk (not selected nominal panel)",
        "columns": [
            {"name": "ref_area", "dtype": "category", "role": "group"},
            {"name": "quarter", "dtype": "datetime", "role": "time"},
            {"name": "nominal_house_price_index", "dtype": "number", "role": "target"},
        ],
        "raw_series_rows": len(frame),
        "raw_series_dimensions": {
            str(name): sorted(str(v) for v in frame[name].dropna().unique())
            for name in frame.columns[:10]
            if frame[name].nunique() < 100
        },
        "time_range": [time_columns[0], time_columns[-1]],
        "observed_columns": list(frame.columns),
        "selected_member": names[0],
        "checks": ["wide_csv_schema", "quarter_columns", "nonmissing_observation_count"],
        "deferred": "Phase24 freezes nominal national series and coverage >=80; no selection by TEST performance.",
    }
