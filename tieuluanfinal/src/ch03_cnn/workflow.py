"""Phase27-specific TEST authorization, independent from Ch2/Ch5 seals."""

import hashlib
import shutil
from datetime import UTC, datetime

import numpy as np

from src.ch02_ml.test_gate import EvaluationGate, atomic_json
from src.ch03_cnn.image_cache import ImageCache, decode_rows, storage_budget
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, canonical_sha256, check_seal_transition, read_json, validate_document
from src.common.data_access import DatasetView
from src.common.eda_artifacts import read_rows
from src.common.eda_sources import source


class CnnEvaluationGate(EvaluationGate):
    def lock(self, manifest):
        if (self.root / "manifest.json").exists() or (self.root / "seal.json").exists():
            raise ValueError("TEST manifest already locked")
        if not manifest["runs"] or len(set(manifest["runs"])) != len(manifest["runs"]):
            raise ValueError("Missing/duplicate approved runs")
        stamp = datetime.now(UTC).isoformat()
        seal = {
            "schema_version": "3.0.0",
            "evidence_kind": "measured",
            "seal_id": manifest["dataset_id"] + "_phase27_test_v1",
            "dataset_id": manifest["dataset_id"],
            "split_sha256": manifest["split_sha256"],
            "locked_config_sha256": canonical_sha256(manifest),
            "evaluator_sha256": manifest["code_sha256"],
            "state": "locked",
            "evaluation_count": 0,
            "approved_run_ids": manifest["runs"],
            "created_at": stamp,
            "events": [
                {
                    "at": stamp,
                    "event": "lock",
                    "actor": "phase27_offline_controller",
                    "reason": "All CNN configurations/selections/evaluator frozen before TEST",
                }
            ],
        }
        validate_document("seal", seal)
        write_once(self.root / "manifest.json", manifest)
        write_once(self.root / "seal.json", seal)

    def _transition(self, target, event, reason):
        seal = self.state()
        check_seal_transition(
            seal, target, config_sha256=canonical_sha256(read_json(self.root / "manifest.json"))
        )
        seal["state"], seal["evaluation_count"] = target, 0 if target == "locked" else 1
        seal["events"].append(
            {
                "at": datetime.now(UTC).isoformat(),
                "event": event,
                "actor": "phase27_offline_controller",
                "reason": reason,
            }
        )
        validate_document("seal", seal)
        atomic_json(self.root / "seal.json", seal)

    def record(self, run, result):
        if not self._run_path(run, ".claimed").exists():
            raise ValueError("Cannot record an unclaimed prediction")
        super().record(run, result)


def test_partition_cache(dataset, gate, run):
    """Only called after this run has consumed its one-shot claim."""
    state = gate.state()
    if (
        state["state"] != "evaluating"
        or state["dataset_id"] != dataset
        or run not in state["approved_run_ids"]
        or not (gate.root / (run + ".claimed")).exists()
    ):
        raise ValueError("TEST cache access requires consumed active claim")
    view = DatasetView(dataset)
    if state["split_sha256"] != view.provenance["split_sha256"]:
        raise ValueError("TEST split hash mismatch")
    ids = read_rows(view.split_dir / "test.ids.jsonl.gz")
    root = ROOT / f"data/processed/v3/phase27/{dataset}_sealed_test"
    provenance = {**view.provenance, "seal_id": state["seal_id"]}
    if root.exists():
        cache = ImageCache(root)
        if cache.ids != ids or cache.receipt["provenance"] != provenance:
            raise ValueError("Sealed cache provenance mismatch")
        return cache, view, ids
    view._load()
    rows = [view._index[key] for key in ids]
    shape = view.preprocessing["input_shape_hwc"]
    storage_budget(len(ids), shape, free_bytes=shutil.disk_usage(ROOT).free)
    pixels = np.empty((len(ids), *shape), dtype="uint8")
    positions = {k: i for i, k in enumerate(ids)}
    indexed = {row["id"]: row for row in rows}
    path = ROOT / source(dataset)["contract"]["files"][0]["path"]
    for key, image in decode_rows(dataset, path, rows, shape[:2]):
        if hashlib.sha256(image.tobytes()).hexdigest() != indexed[key]["model_pixel_sha256"]:
            raise ValueError("TEST pixel hash mismatch")
        pixels[positions[key]] = image
    labels = np.asarray(
        [view.adapter_contract["source_label_to_id"][str(row["target"])] for row in rows], dtype="int64"
    )
    return (
        ImageCache.create(root, ids, pixels, labels, provenance, free_bytes=shutil.disk_usage(ROOT).free),
        view,
        ids,
    )


test_partition_cache.__test__ = False
