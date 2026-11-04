"""Joint-gate-only reader. Not invoked on real holdout until the evaluator lock.

Reuse the frozen main adapter; do not add an override flag to development data.
Observation-origin forecasting may use actual observations at/before each origin.
"""

import numpy as np

from src.ch04_rnn_lstm.phase29.joint_gate import DATASETS
from src.ch04_rnn_lstm.window_data import WindowData
from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json
from src.common.eda_artifacts import read_rows


class HoldoutData(WindowData):
    def __init__(self, gate, evaluator_sha256):
        # Exclusive persisted token is consumed before reading/gathering any TEST windows.
        gate.materialize(evaluator_sha256)
        _, manifest = gate._check(evaluator_sha256, {"evaluating"})
        dataset = manifest["dataset_id"]
        if dataset not in DATASETS:
            raise ValueError("Not a declared joint recurrent dataset")
        super().__init__(dataset)
        contract = read_json(self.view.split_dir / "split_contract.json")
        part = next(p for p in contract["partitions"] if p["name"] == "test")
        ids_path = (ROOT / part["ids"]["path"]).resolve()
        if not ids_path.is_relative_to(ROOT.resolve()) or sha256_file(ids_path) != part["ids"]["sha256"]:
            raise ValueError("Frozen TEST ID hash/path mismatch")
        self.test_ids = read_rows(ids_path)
        if not self.test_ids or len(set(self.test_ids)) != len(self.test_ids):
            raise ValueError("Empty/duplicate TEST IDs")
        self.allowed = set(self.test_ids)
        times = self.frame.time.to_numpy(dtype="datetime64[ns]")
        series = self.frame.series.to_numpy()
        val_end = np.datetime64(
            next(p for p in contract["partitions"] if p["name"] == "validation")["target_end"].replace(
                "+00:00", ""
            )
        )
        lower = np.datetime64(part["target_start"].replace("+00:00", ""))
        upper = np.datetime64(part["target_end"].replace("+00:00", ""))
        positions = set()
        for key in self.test_ids:
            if key not in self.rows:
                raise ValueError("Missing frozen TEST window index")
            row = self.rows[key]
            start, origin = row["start_index"], row["origin_index"]
            targets = row["target_indices"]
            if (
                row["partition"] != "test"
                or start < 0
                or origin >= len(times)
                or origin - start + 1 != self.lookback
                or targets != [origin + h for h in self.horizons]
                or max(targets) >= len(times)
            ):
                raise ValueError("Noncausal/invalid frozen TEST index")
            context = list(range(start, origin + 1))
            calendar = np.asarray([np.datetime64(t.replace("+00:00", "")) for t in row["target_times"]])
            if (
                not np.all(series[context + targets] == row["series"])
                or np.any(times[targets] <= val_end)
                or np.any(times[targets] < lower)
                or np.any(times[targets] > upper)
                or not np.array_equal(calendar, times[targets])
                or np.datetime64(row["context_start"].replace("+00:00", "")) != times[start]
                or np.datetime64(row["context_end"].replace("+00:00", "")) != times[origin]
            ):
                raise ValueError("Cross-series, calendar or partition violation")
            positions.update(context)
        # Float64 original targets are checked, never imputed or inverse-rounded labels.
        self.targets(self.test_ids)
        positions = sorted(positions)
        self.features[positions] = self.adapter.transform(
            self.frame.iloc[positions][self.adapter.state["input_columns"]]
        )
        if not np.isfinite(self.features[positions]).all():
            raise ValueError("Nonfinite TEST context after frozen transform")

    def contract(self):
        return {
            "dataset_id": self.dataset_id,
            "fold": None,
            "split": "test",
            "test_count": len(self.test_ids),
            "test_windows_materialized": True,
            "policy": "Joint Phase29 gate consumed before materialization; frozen main scaler, causal observed history only",
        }
