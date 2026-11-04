"""Selection integrity and sealed batch orchestration, independent of UI services."""

from src.ch02_ml.protocol import BASE, DATASETS, check_sources, ref, run_ids
from src.ch02_ml.test_gate import EvaluationGate
from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json, validate_document


def checked_reference(record):
    path = (ROOT / record["path"]).resolve()
    if not path.is_relative_to(ROOT.resolve()) or sha256_file(path) != record["sha256"]:
        raise ValueError("Missing, changed or escaping approved artifact")
    return path


def selections(release):
    if set(release["expected_run_ids"]) != set(run_ids()) or len(release["runs"]) != 54:
        raise ValueError("Incomplete declared experiment matrix")
    artifacts = {}
    for entry in release["runs"]:
        path = BASE / "runs" / entry["run_id"] / "selection.json"
        selected = read_json(path)
        if (
            selected["status"] != "succeeded"
            or selected["selection_split"] != "validation"
            or not selected["inference_ready"]
        ):
            raise ValueError("Run lacks a validation-selected checkpoint")
        for key in (
            "config",
            "model_contract",
            "checkpoint",
            "checkpoint_metadata",
            "validation_metrics",
            "validation_predictions",
            "history",
            "details",
            "cpu_demo",
            "classical_metadata",
        ):
            record = selected.get(key)
            if record is not None:
                checked_reference(record)
                artifacts[record["path"]] = record
        if selected["config"] != entry["config"] or selected["model_contract"] != entry["model_contract"]:
            raise ValueError("Selected configuration/contract does not match release")
        metric = read_json(checked_reference(selected["validation_metrics"]))
        if metric["split"] != "validation" or metric["run_id"] != entry["run_id"]:
            raise ValueError("Invalid validation record")
        if entry["method"] in {"scratch", "keras", "pytorch"}:
            validate_document("run", metric, publish=True)
            contract = read_json(checked_reference(entry["model_contract"]))
            validate_document("model", contract, publish=True)
        demo = read_json(checked_reference(selected["cpu_demo"]))
        if demo["status"] != "PASS" or demo["input_split"] != "train":
            raise ValueError("Missing CPU deployment parity")
        artifacts[path.relative_to(ROOT).as_posix()] = ref(path)
    return list(artifacts.values())


def lock_tests():
    release = check_sources()
    artifacts = selections(release)
    evidence = read_json(BASE / "pretest_verification.json")
    if evidence["status"] != "PASS" or evidence["code_sha256"] != release["code"]["dirty_tree_sha256"]:
        raise ValueError("Pre-TEST verification not approved")
    artifacts.append(ref(BASE / "pretest_verification.json"))
    artifacts.append(ref(BASE / "release.json"))
    for dataset in DATASETS:
        gate = EvaluationGate(BASE / "test_seals" / dataset)
        if (gate.root / "seal.json").exists():
            if gate.state()["state"] in {"failed_sealed", "evaluating", "evaluated"}:
                continue
            old = read_json(gate.root / "manifest.json")
            for record in old["artifacts"]:
                checked_reference(record)
            continue
        entries = [entry for entry in release["runs"] if entry["dataset_id"] == dataset]
        config = read_json(checked_reference(entries[0]["config"]))
        gate.lock(
            {
                "dataset_id": dataset,
                "split_sha256": config["provenance"]["split_sha256"],
                "runs": [row["run_id"] for row in entries],
                "code_sha256": release["code"]["dirty_tree_sha256"],
                "artifacts": artifacts,
                "policy": "One batch of 18 predeclared runs. Claim consumes authorization even on interruption. No tuning, refit or retries.",
            }
        )
    return {"status": "PASS", "datasets_locked": 3, "approved_runs": 54, "test_predictions_executed": False}


def pending_test_runs(gate):
    """Resume only unclaimed runs; never repeat even an interrupted forward pass."""
    state = gate.state()
    if state["state"] == "evaluated":
        return []
    if state["state"] != "evaluating":
        raise ValueError("No active TEST batch")
    pending = []
    for run in state["approved_run_ids"]:
        result = gate.root / (run + ".result.json")
        claimed = gate.root / (run + ".claimed")
        if result.exists():
            if not claimed.exists() or read_json(result)["status"] != "PASS":
                raise ValueError("Unclaimed or failed TEST result")
            for key in ("metrics", "predictions", "details"):
                checked_reference(read_json(result)[key])
        elif claimed.exists():
            gate.fail("Interrupted claimed run has no complete result; automatic TEST retry prohibited")
            raise ValueError("Incomplete consumed TEST claim; batch permanently sealed")
        else:
            pending.append(run)
    return pending
