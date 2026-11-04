"""CNN evidence auditor: saved predictions only, never repeats TEST forward."""

import argparse
import gzip
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import numpy as np

from scripts.phase27_controller import selections
from scripts.phase27_preflight import dependencies
from src.ch02_ml.experiment import metric_rows, provenance
from src.ch02_ml.test_gate import atomic_json
from src.ch03_cnn.experiment import checked
from src.ch03_cnn.image_cache import development_cache
from src.ch03_cnn.protocol import BASE, IMPLEMENTATIONS, MODELS, check_sources, ref
from src.ch03_cnn.workflow import CnnEvaluationGate
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json, validate_document
from src.common.eda_artifacts import read_rows
from src.common.metric_core import classification_metrics
from src.common.model_core import canonical_weights
from src.common.numpy_engine import NumpyNetwork
from src.common.training_core import batch_order


def test_count(path):
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    if not suites or any(
        int(s.attrib.get(key, 0)) for s in suites for key in ("failures", "errors", "skipped")
    ):
        raise ValueError("Test report has failures/errors/skips")
    count = sum(int(s.attrib["tests"]) for s in suites)
    if count < 1:
        raise ValueError("Empty test report")
    return count


def verify_prediction(record, detail_record, ids, target, *, run_id):
    document = read_json(checked(record))
    details = read_json(checked(detail_record))
    artifact = next(row for row in document["artifacts"] if row["path"].endswith(".jsonl.gz"))
    with gzip.open(checked(artifact), "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    if [row["id"] for row in rows] != ids or document["run_id"] != run_id:
        raise ValueError("Saved prediction ID/order/run mismatch")
    labels = np.asarray([row["target"] for row in rows], dtype="int64")
    if target is not None:
        np.testing.assert_array_equal(labels, target)
    probability = np.asarray([row["prediction"] for row in rows], dtype=details["output_dtype"])
    values = classification_metrics(labels, probability)
    if canonical_sha256(values) != canonical_sha256(details["metrics"]):
        raise ValueError("Saved prediction metric recomputation mismatch")
    expected = metric_rows(values, "multiclass")
    if canonical_sha256(expected) != canonical_sha256(document["metrics"]):
        raise ValueError("Run metric/detail mismatch")
    return len(rows)


def verify(stage="pretest"):
    release = check_sources()
    protection = dependencies()
    selected_artifacts = selections(release)
    runs = []
    test_rows = 0
    for entry in release["runs"]:
        selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
        config = read_json(checked(entry["config"]))
        cache, view = development_cache(entry["dataset_id"])
        if (
            config["provenance"] != view.provenance
            or config["cache_manifest"] != ref(cache.root / "manifest.json")
            or config["training"] != {**read_json(PROTOCOL)["training"], "batch_size": 16}
        ):
            raise ValueError("CNN data/training contract changed")
        train_ids, val_ids = view.ids("train"), view.ids("validation")
        labels = np.asarray([cache.labels[cache.positions[key]] for key in val_ids])
        verify_prediction(
            selected["validation_metrics"], selected["details"], val_ids, labels, run_id=entry["run_id"]
        )
        weights = ArtifactStore(MODELS / entry["run_id"]).load_checkpoint(
            "best",
            provenance(entry, config),
            expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
        )
        x, _ = cache.batch(train_ids[:4])
        demo = read_json(checked(selected["cpu_demo"]))
        if entry["method"] in IMPLEMENTATIONS:
            contract = read_json(checked(entry["model_contract"]))
            validate_document("model", contract, publish=True)
            if (
                contract["family"] != "cnn"
                or sum(
                    layer["kind"] in {"conv2d", "dense"} and layer["parameter_count"] > 0
                    for layer in contract["layers"]
                )
                != 7
            ):
                raise ValueError("CNN learnable layer requirement failed")
            initial = canonical_weights(config["plan"], entry["seed"])
            if (
                canonical_sha256({k: v.tolist() for k, v in initial.items()})
                != config["canonical_initial_weights_sha256"]
            ):
                raise ValueError("Canonical CNN initialization mismatch")
            if all(np.array_equal(initial[k], weights[k]) for k in initial):
                raise ValueError("Initialized checkpoint incorrectly published as trained")
            output = NumpyNetwork(config["plan"], weights).forward(x)
            history = read_json(checked(selected["history"]))
            if (
                not history
                or len(history) > 40
                or selected["best_epoch"]
                != min(range(len(history)), key=lambda i: history[i]["validation_loss"])
            ):
                raise ValueError("Invalid validation checkpoint selection")
            for epoch, row in enumerate(history):
                if (
                    row["epoch"] != epoch
                    or row["batch_order_sha256"]
                    != canonical_sha256(batch_order(len(train_ids), 16, entry["seed"], epoch))
                    or row["augmentation"] != "none"
                ):
                    raise ValueError("CNN batch order/augmentation mismatch")
            parity = read_json(BASE / "runs" / entry["run_id"] / "initial_parity.json")
            if (
                parity["forward"] != "PASS"
                or entry["method"] != "scratch"
                and parity["gradient"]["max_relative_l2_error"] > 1e-3
            ):
                raise ValueError("CNN initial parity missing/failed")
        else:
            train_labels = np.asarray([cache.labels[cache.positions[key]] for key in train_ids])
            expected = int(np.bincount(train_labels, minlength=view.spec["class_count"]).argmax())
            np.testing.assert_array_equal(
                weights["class_probabilities"], np.eye(view.spec["class_count"])[expected]
            )
            output = np.tile(weights["class_probabilities"], (len(x), 1))
        np.testing.assert_allclose(output, np.asarray(demo["raw_output"]), rtol=1e-4, atol=1e-5)
        metric = read_json(checked(selected["validation_metrics"]))
        if entry["method"] in {"keras", "pytorch"} and (
            metric["device"] != "cuda:0" or not 0 < metric["efficiency"]["peak_vram_bytes"] < 8 * 1024**3
        ):
            raise ValueError("Native CNN was not GPU-trained within budget")
        if stage == "full":
            gate = CnnEvaluationGate(BASE / "test_seals" / entry["dataset_id"])
            state = gate.state()
            if (
                state["state"] != "evaluated"
                or state["evaluation_count"] != 1
                or set(state["approved_run_ids"])
                != {e["run_id"] for e in release["runs"] if e["dataset_id"] == entry["dataset_id"]}
            ):
                raise ValueError("Invalid CNN TEST seal")
            result = read_json(gate.root / (entry["run_id"] + ".result.json"))
            if not (gate.root / (entry["run_id"] + ".claimed")).exists() or result["status"] != "PASS":
                raise ValueError("TEST run claim/result mismatch")
            ids = read_rows(view.split_dir / "test.ids.jsonl.gz")
            # Source metadata audit only, no TEST image/model forward.
            view._load()
            targets = np.asarray(
                [view.adapter_contract["source_label_to_id"][str(view._index[k]["target"])] for k in ids]
            )
            test_rows += verify_prediction(
                result["metrics"], result["details"], ids, targets, run_id=entry["run_id"]
            )
        runs.append(entry["run_id"])
    return {
        "status": "PASS",
        "stage": stage,
        "at": datetime.now(UTC).isoformat(),
        "code_sha256": release["code"]["dirty_tree_sha256"],
        "auditor": ref(ROOT / "scripts/verify_phase27.py"),
        "protected_locks": protection,
        "neural_runs": 27,
        "majority_runs": 9,
        "validated_runs": len(runs),
        "selection_artifacts": len(selected_artifacts),
        "test_saved_rows_audited": test_rows,
        "test_forward_executed_by_auditor": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("pretest", "full"), default="pretest")
    args = parser.parse_args()
    result = verify(args.stage)
    if args.stage == "pretest":
        counts = {
            name: test_count(BASE / name)
            for name in (
                "cnn_tests.xml",
                "keras_trainer_tests.xml",
                "demo_tests.xml",
                "regression-tests.xml",
                "preservation-tests.xml",
            )
        }
        coverage = read_json(BASE / "pretest_coverage.json")
        if coverage["totals"]["percent_covered"] < 80:
            raise ValueError("CNN pretest coverage below 80%")
        result.update(
            {
                "tests": counts,
                "coverage_percent": coverage["totals"]["percent_covered"],
                "evidence": [ref(BASE / name) for name in (*counts, "pretest_coverage.json")],
            }
        )
        path = BASE / "pretest_verification.json"
        if path.exists():
            old = read_json(path)
            if any(
                old[key] != result[key]
                for key in (
                    "code_sha256",
                    "auditor",
                    "protected_locks",
                    "tests",
                    "evidence",
                    "coverage_percent",
                )
            ):
                raise ValueError("Immutable pretest evidence changed")
            result = old
        else:
            write_once(path, result)
    else:
        if (
            ref(ROOT / "scripts/verify_phase27.py")
            != read_json(BASE / "pretest_verification.json")["auditor"]
        ):
            raise ValueError("Pre-TEST auditor changed; versioned revision required")
        atomic_json(BASE / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
