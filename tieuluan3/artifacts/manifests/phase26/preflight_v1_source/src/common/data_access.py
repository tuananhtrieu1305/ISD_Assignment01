"""Read-only model data views over Phase24. TEST is deliberately unavailable.

Future TEST evaluation must use a separately sealed evaluator in Phases26–29,
not a boolean override on this development loader.
"""

from __future__ import annotations

import copy
import io

import numpy as np
import pandas as pd

from src.common.artifact_core import sha256_file
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.eda_artifacts import read_rows
from src.common.eda_sources import image_for_row, load_series, load_tabular
from src.common.tensor_adapters import TensorAdapter, image_batch, select_rows, window_batch


class DatasetView:
    def __init__(self, dataset_id, fold=None):
        catalog = read_json(ROOT / "data/catalog_v3.json")
        entry = next((row for row in catalog["datasets"] if row["dataset_id"] == dataset_id), None)
        if entry is None or entry["chapter"] not in {2, 3, 4}:
            raise ValueError("Not a V3 trainable dataset")
        if fold not in {None, 1, 2, 3} or fold is not None and entry["chapter"] != 4:
            raise ValueError("Invalid rolling fold")
        self.dataset_id = dataset_id
        self.kind = {2: "tabular", 3: "image", 4: "timeseries"}[entry["chapter"]]
        self.spec = next(row for row in read_json(PROTOCOL)["datasets"] if row["dataset_id"] == dataset_id)
        self.base = ROOT / f"artifacts/manifests/phase24/{dataset_id}"
        self.split_dir = ROOT / f"data/splits/v3/{dataset_id}"
        for key in ("source_manifest", "split", "preprocessing"):
            ref = entry[key]
            if sha256_file(ROOT / ref["path"]) != ref["sha256"]:
                raise ValueError(f"Catalog hash mismatch: {key}")
        self.preprocessing = read_json(ROOT / entry["preprocessing"]["path"])
        prep_path = ROOT / entry["preprocessing"]["path"]
        if fold is not None:
            self.split_dir /= f"rolling_fold_{fold}"
            prep_path = self.split_dir / "preprocessing.json"
            self.preprocessing = read_json(prep_path)
        self.adapter = None if self.kind == "image" else TensorAdapter(self.preprocessing)
        labels = self.preprocessing.get("class_names")
        if labels is None and dataset_id == "ch3_eurosat":
            labels = {str(i): name for i, name in enumerate(sorted(self.preprocessing["class_weights"]))}
        if labels is None and self.kind == "image":
            labels = {str(i): f"DR grade {i}" for i in range(self.spec["class_count"])}
        if labels is None and self.spec["task"] == "binary_classification":
            labels = (
                {"0": "no diabetes", "1": "prediabetes or diabetes"}
                if dataset_id == "ch2_cdc_diabetes"
                else {"0": "no", "1": "yes"}
            )
        source_labels = (
            sorted(self.preprocessing["class_weights"]) if dataset_id == "ch3_eurosat" else list(labels or {})
        )
        label_to_id = {key: i for i, key in enumerate(source_labels)}
        if labels and dataset_id != "ch3_eurosat":
            label_to_id = {key: int(key) for key in labels}
        self.adapter_contract = {
            "adapter_version": "phase25.1",
            "dataset_id": dataset_id,
            "fold": fold,
            "kind": self.kind,
            "dtype": "float32",
            "feature_order_policy": "numeric input_columns order; then categorical input_columns/vocabulary order",
            "output_feature_names": self.adapter.output_feature_names
            if self.adapter
            else ["red", "green", "blue"],
            "class_names": labels or {},
            "source_label_to_id": label_to_id,
            "class_weights_by_id": {
                str(label_to_id[k]): v for k, v in self.preprocessing.get("class_weights", {}).items()
            },
            "canonical_layout": "NHWC"
            if self.kind == "image"
            else "NTF"
            if self.kind == "timeseries"
            else "NF",
            "pytorch_image_layout": "NCHW" if self.kind == "image" else None,
            "preprocessing": {
                "path": prep_path.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(prep_path),
            },
        }
        self.provenance = {
            "dataset_sha256": read_json(ROOT / entry["split"]["path"])["dataset_sha256"],
            "split_sha256": entry["split"]["sha256"],
            "subset_sha256": sha256_file(self.split_dir / "matched_train.ids.jsonl.gz"),
            "preprocessing_sha256": sha256_file(prep_path),
            "adapter_sha256": canonical_sha256(self.adapter_contract),
        }
        self._frame = None
        self._targets = None
        self._source_ids = None
        self._index = None
        self._allowed = set(self.ids("train", matched=False)) | set(self.ids("validation"))

    def ids(self, partition, matched=True):
        if partition not in {"train", "validation"}:
            raise ValueError("TEST/quarantine is sealed; development loader accepts only train/validation")
        filename = "matched_train" if partition == "train" and matched else partition
        return read_rows(self.split_dir / f"{filename}.ids.jsonl.gz")

    def _load(self):
        if self._frame is not None:
            return
        if self.kind == "tabular":
            frame, target, ids, _, _ = load_tabular(self.dataset_id)
            self._frame, self._targets, self._source_ids = frame, target.to_numpy(), ids
        elif self.kind == "image":
            self._index = {row["id"]: row for row in read_rows(self.base / "index.jsonl.gz")}
            self._frame = pd.DataFrame()  # decoded lazily; no image tensor cache
        else:
            receipt = read_json(self.base / "series_cache.json")
            path = ROOT / receipt["path"]
            if path.exists():
                if sha256_file(path) != receipt["sha256"]:
                    raise ValueError("Series cache hash mismatch")
                self._frame = pd.read_csv(path, parse_dates=["time"])
            else:
                frame, _, _ = load_series(self.dataset_id)
                frame = frame.sort_values(["series", "time"]).reset_index(drop=True)
                # Match the frozen cache's decimal serialization before scaling.
                self._frame = pd.read_csv(
                    io.StringIO(
                        frame.to_csv(index=False, date_format="%Y-%m-%dT%H:%M:%S", float_format="%.12g")
                    ),
                    parse_dates=["time"],
                )
            self._index = {row["id"]: row for row in read_rows(self.base / "index.jsonl.gz")}

    def batch(self, ids, implementation):
        if implementation not in {"scratch", "keras", "pytorch"}:
            raise ValueError("Unknown implementation")
        if not ids or len(ids) != len(set(ids)) or any(value not in self._allowed for value in ids):
            raise ValueError("Unknown/duplicate/sealed batch IDs")
        self._load()
        if self.kind == "tabular":
            positions = select_rows(self._source_ids, ids)
            x = self.adapter.transform(self._frame.iloc[positions])
            y = self._targets[positions]
            y = self.adapter.target(y).reshape(-1, 1)
        elif self.kind == "image":
            rows = [self._index[key] for key in ids]
            images = np.stack(
                [
                    np.asarray(
                        image_for_row(
                            self.dataset_id, row, self.preprocessing["input_shape_hwc"][:2]
                        ).convert("RGB")
                    )
                    for row in rows
                ]
            )
            x = image_batch(images, implementation)
            y = np.asarray(
                [self.adapter_contract["source_label_to_id"][str(row["target"])] for row in rows],
                dtype=np.int64,
            )
        else:
            x, y = window_batch(self._frame, [self._index[key] for key in ids], self.adapter)
        return x, y

    def contract(self):
        return copy.deepcopy(self.adapter_contract)
