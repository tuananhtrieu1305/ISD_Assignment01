"""Small row-feature cache; only causal development windows materialize as batches."""

import numpy as np

from src.common.artifact_core import sha256_file
from src.common.contracts import canonical_sha256, read_json
from src.common.data_access import DatasetView


class WindowData:
    def __init__(self, dataset_id, fold=None):
        self.view = DatasetView(dataset_id, fold)
        if self.view.kind != "timeseries":
            raise ValueError("Require a frozen time-series dataset")
        self.dataset_id, self.fold, self.adapter = dataset_id, fold, self.view.adapter
        self.train_ids = self.view.ids("train")
        self.validation_ids = self.view.ids("validation")
        self.allowed = set(self.view.ids("train", matched=False)) | set(self.validation_ids)
        self.view._load()
        self.frame = self.view._frame
        self.rows = {key: row.copy() for key, row in self.view._index.items()}
        self.lookback = self.view.spec["lookback"]
        self.horizons = self.view.spec["horizons"]
        self.reconstructed_fold_ids = sorted(self.allowed - set(self.rows))
        if self.reconstructed_fold_ids and fold is None:
            raise ValueError("Main split contains missing frozen window IDs")
        origin_positions = {
            f"{series}/{timestamp.isoformat()}": index
            for index, (series, timestamp) in enumerate(zip(self.frame.series, self.frame.time, strict=True))
        }
        validation_set = set(self.validation_ids)
        for key in self.reconstructed_fold_ids:
            origin = origin_positions[key]
            targets = [origin + horizon for horizon in self.horizons]
            start = origin - self.lookback + 1
            if start < 0 or max(targets) >= len(self.frame):
                raise ValueError("Reconstructed fold window outside source")
            self.rows[key] = {
                "id": key,
                "series": str(self.frame.series.iloc[origin]),
                "partition": "validation" if key in validation_set else "train",
                "context_start": self.frame.time.iloc[start].isoformat(),
                "context_end": self.frame.time.iloc[origin].isoformat(),
                "target_times": [self.frame.time.iloc[i].isoformat() for i in targets],
                "start_index": start,
                "origin_index": origin,
                "target_indices": targets,
            }
        self.features = np.full((len(self.frame), self.adapter.state["output_width"]), np.nan, "float32")
        context_rows = set()
        series_values = self.frame.series.to_numpy()
        if fold is not None:
            limits = read_json(self.view.split_dir.parent / "rolling_folds.json")[fold - 1]
            train_end = np.datetime64(limits["train_end"])
            val_end = np.datetime64(limits["validation_end"])
        else:
            parts = read_json(self.view.split_dir / "split_contract.json")["partitions"]
            train_end = np.datetime64(
                next(p["target_end"] for p in parts if p["name"] == "train").replace("+00:00", "")
            )
            val_end = np.datetime64(
                next(p["target_end"] for p in parts if p["name"] == "validation").replace("+00:00", "")
            )
        times = self.frame.time.to_numpy(dtype="datetime64[ns]")
        for key in self.allowed:
            row = self.rows[key]
            indices = list(range(row["start_index"], row["origin_index"] + 1))
            target_times = times[row["target_indices"]]
            is_val = key in validation_set
            if (
                len(indices) != self.lookback
                or min(row["target_indices"]) <= row["origin_index"]
                or max(row["target_indices"]) >= len(self.frame)
                or not np.all(series_values[indices + row["target_indices"]] == row["series"])
                or np.any(target_times > val_end)
                or (np.any(target_times <= train_end) if is_val else np.any(target_times > train_end))
            ):
                raise ValueError("Noncausal, cross-series or invalid frozen window")
            row["partition"] = "validation" if is_val else "train"
            context_rows.update(indices)
        positions = sorted(context_rows)
        self.features[positions] = self.adapter.transform(
            self.frame.iloc[positions][self.adapter.state["input_columns"]]
        )
        self.feature_bytes = self.features.nbytes
        if self.feature_bytes > 64 * 1024**2:
            raise ValueError("Row feature cache exceeds 64 MiB budget")
        self.provenance = self.view.provenance.copy()
        if fold is not None:
            self.provenance["split_sha256"] = canonical_sha256(
                {
                    name: sha256_file(self.view.split_dir / f"{name}.ids.jsonl.gz")
                    for name in ("train", "validation", "matched_train")
                }
            )

    def selected(self, ids):
        if not ids or len(ids) != len(set(ids)) or any(key not in self.allowed for key in ids):
            raise ValueError("Empty/duplicate/unknown/TEST window IDs")
        return [self.rows[key] for key in ids]

    def targets(self, ids):
        rows = self.selected(ids)
        values = self.frame.target.to_numpy(dtype="float64")
        result = np.asarray([values[row["target_indices"]] for row in rows])
        if not np.isfinite(result).all():
            raise ValueError("Missing labels must never be imputed")
        return result

    def batch(self, ids):
        rows = self.selected(ids)
        positions = np.asarray([np.arange(row["start_index"], row["origin_index"] + 1) for row in rows])
        x = np.ascontiguousarray(self.features[positions])
        if not np.isfinite(x).all():
            raise ValueError("Nonfinite/sealed input features")
        return x, self.adapter.target(self.targets(ids))

    def series(self, ids):
        return [row["series"] for row in self.selected(ids)]

    def baseline(self, ids, method):
        if method not in {"last_value", "seasonal_naive"}:
            raise ValueError("Unknown causal baseline")
        values = self.frame.target.to_numpy(dtype="float64")
        result = []
        for row in self.selected(ids):
            start, origin = row["start_index"], row["origin_index"]
            history = values[start : origin + 1]
            observed = history[np.isfinite(history)]
            if not len(observed):
                raise ValueError("No observed history for causal baseline")
            last = observed[-1]
            seasonal = []
            for horizon in self.horizons:
                index = (
                    origin
                    + horizon
                    - int(np.ceil(horizon / self.view.spec["seasonality"])) * self.view.spec["seasonality"]
                )
                value = values[index] if start <= index <= origin else np.nan
                seasonal.append(float(value) if np.isfinite(value) else float(last))
            result.append(seasonal if method == "seasonal_naive" else [float(last)] * len(self.horizons))
        return np.asarray(result, dtype="float64")

    def contract(self):
        return {
            "dataset_id": self.dataset_id,
            "fold": self.fold,
            "train_count": len(self.train_ids),
            "validation_count": len(self.validation_ids),
            "train_ids_sha256": canonical_sha256(self.train_ids),
            "validation_ids_sha256": canonical_sha256(self.validation_ids),
            "feature_bytes": self.feature_bytes,
            "provenance": self.provenance,
            "input_shape": [self.lookback, self.features.shape[1]],
            "horizons": self.horizons,
            "adapter": self.view.contract(),
            "test_windows_materialized": False,
            "fold_index_revision": "phase28.1; source-index gaps reconstructed from immutable IDs/calendar, never alter splits/scalers",
            "reconstructed_fold_ids": self.reconstructed_fold_ids,
            "raw_read_scope": "Frozen full row table is read; transform/gather only development context rows; no TEST window predictions or labels used for selection",
            "baseline_policy": "Observed target history at/before origin; missing seasonal source falls back to last observed within lookback; no target imputation",
        }
