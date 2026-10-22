"""Read frozen sources without extraction or mutation; deterministic V3 aliases."""

from __future__ import annotations

import hashlib
import io
import re
import tarfile
import zipfile

import numpy as np
import pandas as pd
from PIL import Image

from src.common.contracts import ROOT, read_json
from src.common.source_inspection import normalize_column, require


def source(dataset_id):
    return read_json(ROOT / f"artifacts/manifests/datasets/{dataset_id}.json")


def load_tabular(dataset_id):
    envelope = source(dataset_id)
    path = ROOT / envelope["contract"]["files"][0]["path"]
    if dataset_id == "ch2_cdc_diabetes":
        raw = pd.read_csv(path)
        raw.columns = [normalize_column(c) for c in raw]
        target = raw.pop("diabetes_binary")
        raw = raw.drop(columns="id")
        properties = None
    elif dataset_id == "ch2_ames_housing":
        raw = pd.read_csv(path, sep="\t")
        raw.columns = [normalize_column(c) for c in raw]
        target = raw.pop("sale_price")
        properties = raw.pid.astype(str).tolist()
        raw = raw.drop(columns=["pid", "order"])
    elif dataset_id == "ch2_bank_marketing":
        with zipfile.ZipFile(path) as outer, zipfile.ZipFile(io.BytesIO(outer.read("bank.zip"))) as inner:
            raw = pd.read_csv(inner.open("bank-full.csv"), sep=";")
        target = raw.pop("y").map({"no": 0, "yes": 1})
        raw = raw.drop(columns="duration")
        properties = None
    else:
        raise ValueError(f"Not a Ch2 source: {dataset_id}")
    require(target.notna().all(), "Missing source target")
    ids = [f"row_{i:07d}" for i in range(len(raw))]
    # SHA-256 includes named, typed scalar features, never labels or excluded IDs.
    hashes = [
        hashlib.sha256(line.encode()).hexdigest()
        for line in raw.to_json(orient="records", lines=True).splitlines()
    ]
    return raw, target.reset_index(drop=True), ids, hashes, properties


def gold_features(raw):
    result = pd.DataFrame({"time": raw.time, "series": "GOLD", "target": raw.gold, "gold": raw.gold})
    for name in ("silver", "platinum", "crude_oil"):
        result[name + "_lag1"] = raw[name].shift(1)
    return result, ["gold", "silver_lag1", "platinum_lag1", "crude_oil_lag1"]


def select_bis_panel(raw):
    """BIS coded VALUE=N, UNIT_MEASURE=628, exclude aggregates, >=80 observations.

    Eligibility uses coverage/identifiers, never price performance or TEST metrics.
    No mixing nominal/real or index/YoY; preserve missing targets in a regular grid.
    """
    time_columns = [c for c in raw if re.fullmatch(r"\d{4}-Q[1-4]", c)]
    selected = raw.loc[(raw.FREQ == "Q") & (raw.VALUE == "N") & (raw.UNIT_MEASURE.astype(str) == "628")]
    selected = selected.loc[
        selected.REF_AREA.str.fullmatch(r"[A-Z]{2}") & ~selected.REF_AREA.isin(["XM", "XW"])
    ]
    require(not selected.REF_AREA.duplicated().any(), "Multiple nominal national series per economy")
    panels, retained, excluded = [], [], []
    coverage = {}
    for _, row in selected.sort_values("REF_AREA").iterrows():
        values = pd.to_numeric(row[time_columns], errors="coerce")
        sid = f"Q.{row.REF_AREA}.N.628"
        coverage[sid] = int(values.notna().sum())
        if coverage[sid] < 80:
            excluded.append({"series": sid, "reason": "fewer_than_80_nonmissing_observations"})
            continue
        first, last = np.flatnonzero(values.notna().to_numpy())[[0, -1]]
        values = values.iloc[first : last + 1]
        times = pd.PeriodIndex(values.index.str.replace("-Q", "Q"), freq="Q").to_timestamp()
        panel = pd.DataFrame({"time": times, "series": sid, "target": values.to_numpy(dtype=float)})
        # A window ends at its last observed quarter; no future revised quarter is an input.
        panel["house_index"] = panel.target
        panel["index_change"] = panel.target.diff()
        panel["economy"] = row.REF_AREA
        panels.append(panel)
        retained.append(sid)
    require(bool(panels), "No admissible nominal BIS series")
    panel = pd.concat(panels, ignore_index=True)
    # Freeze a calendar by coverage, not values: avoid one century-long series
    # setting the global cutoff while most economies did not yet publish data.
    simultaneous = panel.groupby("time").target.count()
    common_start = simultaneous.index[simultaneous >= int(np.ceil(0.8 * len(retained)))][0]
    panel = panel.loc[panel.time >= common_start].reset_index(drop=True)
    for economy in sorted(panel.economy.unique()):
        panel["country_" + economy] = (panel.economy == economy).astype(float)
    features = ["house_index", "index_change"] + [c for c in panel if c.startswith("country_")]
    panel = panel.drop(columns="economy")
    return (
        panel,
        features,
        {
            "retained_series": retained,
            "excluded_series": excluded,
            "coverage": coverage,
            "common_history_start": common_start.isoformat(),
            "history_rule": "earliest quarter with >=80% retained economies observed; schema/coverage only",
            "unit": "nominal index, 2010=100",
            "selection": "Q, N, 628; national economies only; >=80 nonmissing; no performance filter",
        },
    )


def hourly_power(raw):
    times = pd.to_datetime(raw.Date + " " + raw.Time, format="%d/%m/%Y %H:%M:%S")
    values = raw.drop(columns=["Date", "Time"]).apply(pd.to_numeric, errors="coerce")
    values.index = times
    require(not values.index.duplicated().any(), "Duplicate power minute timestamp")
    observed = values.resample("h").count()
    hourly = values.resample("h").mean().where(observed >= 45)
    result = pd.DataFrame(
        {"time": hourly.index, "series": "HOUSEHOLD", "target": hourly.Global_active_power.to_numpy()}
    )
    features = []
    for name in hourly:
        # Target remains untouched. Only input sensor aggregates use bounded causal ffill.
        result[name] = hourly[name].ffill(limit=6).to_numpy()
        result[name + "_missing"] = hourly[name].isna().astype(float).to_numpy()
        features.extend([name, name + "_missing"])
    return result, features


def load_series(dataset_id):
    path = ROOT / source(dataset_id)["contract"]["files"][0]["path"]
    if dataset_id == "ch4_gold_pink_sheet":
        import openpyxl

        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            rows = list(book["Monthly Prices"].values)
        finally:
            book.close()
        header = next(i for i, row in enumerate(rows) if "Gold" in row)
        positions = {
            name: rows[header].index(name) for name in ("Gold", "Silver", "Platinum", "Crude oil, average")
        }
        records = [row for row in rows[header + 1 :] if re.fullmatch(r"\d{4}M\d{2}", str(row[0]))]
        raw = pd.DataFrame({"time": pd.to_datetime([r[0] for r in records], format="%YM%m")})
        for old, new in zip(positions, ("gold", "silver", "platinum", "crude_oil"), strict=True):
            raw[new] = [r[positions[old]] for r in records]
        frame, features = gold_features(raw)
        return (
            frame,
            features,
            {"publication_lag": "explanatory commodities lagged one month; revised vintage, not realtime"},
        )
    with zipfile.ZipFile(path) as archive:
        if dataset_id == "ch4_bis_house_prices":
            name = next(n for n in archive.namelist() if n.endswith(".csv"))
            return select_bis_panel(pd.read_csv(archive.open(name), low_memory=False))
        require(dataset_id == "ch4_household_power", "Unknown time-series source")
        raw = pd.read_csv(
            archive.open("household_power_consumption.txt"), sep=";", na_values="?", low_memory=False
        )
    frame, features = hourly_power(raw)
    return (
        frame,
        features,
        {
            "raw_minute_rows": len(raw),
            "observed_minute_threshold": 45,
            "input_ffill_hours": 6,
            "target_imputation": "never",
            "sensor_units": {
                "Global_active_power": "kW",
                "Global_reactive_power": "kVAR",
                "Voltage": "V",
                "Global_intensity": "A",
                "Sub_metering_1/2/3": "Wh/min observations, hourly mean not summed kWh",
            },
        },
    )


def _image_record(image, *, key, label, member, official, resolution, **extra):
    require(image.mode == "RGB", "Require RGB source images")
    native_hash = hashlib.sha256(np.asarray(image).tobytes()).hexdigest()
    resized = image.resize(tuple(resolution), Image.Resampling.BILINEAR)
    model_pixels = np.asarray(resized)
    return {
        "id": key,
        "target": str(label),
        "member": member,
        "official_split": official,
        "pixel_sha256": native_hash,
        "model_pixel_sha256": hashlib.sha256(np.asarray(resized).tobytes()).hexdigest(),
        "width": image.width,
        "height": image.height,
        "mean_intensity": float(model_pixels.mean()),
        "std_intensity": float(model_pixels.std()),
        "black_fraction": float((model_pixels.max(axis=2) == 0).mean()),
        **extra,
    }


def parse_cifar_classes(text):
    names = [line.strip() for line in text.splitlines() if line.strip()]
    require(len(names) == len(set(names)) == 10, "Require ten unique CIFAR class names")
    return names


def load_images(dataset_id, resolution):
    path = ROOT / source(dataset_id)["contract"]["files"][0]["path"]
    rows = []
    if dataset_id == "ch3_cifar10":
        with tarfile.open(path, "r:gz") as archive:
            with archive.extractfile("cifar-10-batches-bin/batches.meta.txt") as stream:
                class_names = parse_cifar_classes(stream.read().decode("utf-8"))
            for member in archive:
                if not re.fullmatch(r"cifar-10-batches-bin/(data_batch_[1-5]|test_batch)\.bin", member.name):
                    continue
                with archive.extractfile(member) as stream:
                    records = np.frombuffer(stream.read(), dtype=np.uint8).reshape(-1, 3073)
                official = "test" if "test_batch" in member.name else "train"
                for i, record in enumerate(records):
                    pixels = record[1:].reshape(3, 32, 32).transpose(1, 2, 0)
                    image = Image.fromarray(pixels)
                    rows.append(
                        _image_record(
                            image,
                            key=f"{member.name.split('/')[-1]}/{i:05d}",
                            label=record[0],
                            member=member.name,
                            official=official,
                            resolution=resolution,
                            record_offset=i,
                            class_name=class_names[int(record[0])],
                        )
                    )
        return pd.DataFrame(rows)
    index = None
    if dataset_id == "ch3_idrid":
        import yaml

        registry = yaml.safe_load((ROOT / "data/registry.yaml").read_text())
        index_path = next(p for p in registry["provenance_evidence_paths"] if p.endswith("image_index.json"))
        index = read_json(ROOT / index_path)
        members = {row["member"]: key for key, row in index["image_members"].items()}
    else:
        require(dataset_id == "ch3_eurosat", "Unknown CNN source")
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.lower().endswith(".jpg"):
                continue
            key = members[name] if index else name
            label = index["labels"][key]["grade"] if index else name.split("/")[-2]
            official = index["labels"][key]["official_split"] if index else None
            with archive.open(name) as stream, Image.open(stream) as image:
                image.load()
                rows.append(
                    _image_record(
                        image, key=key, label=label, member=name, official=official, resolution=resolution
                    )
                )
    return pd.DataFrame(rows)


def image_for_row(dataset_id, row, resolution=None):
    path = ROOT / source(dataset_id)["contract"]["files"][0]["path"]
    if dataset_id == "ch3_cifar10":
        with tarfile.open(path, "r:gz") as archive, archive.extractfile(row["member"]) as stream:
            stream.read(int(row["record_offset"]) * 3073)
            record = np.frombuffer(stream.read(3073), dtype=np.uint8)
        image = Image.fromarray(record[1:].reshape(3, 32, 32).transpose(1, 2, 0))
    else:
        with (
            zipfile.ZipFile(path) as archive,
            archive.open(row["member"]) as stream,
            Image.open(stream) as raw,
        ):
            image = raw.copy()
    return image.resize(tuple(resolution), Image.Resampling.BILINEAR) if resolution else image
