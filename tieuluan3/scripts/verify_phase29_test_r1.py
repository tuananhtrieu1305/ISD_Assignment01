"""Unified saved-output audit, original failed seal retained; no model/TEST forward."""

import gzip
import json

from scripts.phase29_test_r1 import OLD, REV, check_revision, code
from scripts.verify_phase28 import audit_metric_rows
from scripts.verify_phase29_test import EXPECTED, audit_saved_rows
from src.ch04_rnn_lstm.export_r2 import ORPHAN, validate_run
from src.ch04_rnn_lstm.phase29.experiment import metric_rows
from src.ch04_rnn_lstm.phase29.holdout_cache import CachedHoldout
from src.ch04_rnn_lstm.phase29.joint_evaluation import pending
from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, IMPLEMENTATIONS, checked, ref
from src.ch04_rnn_lstm.phase29_revision.recovery import ContinuationGate, validate_recovery_test
from src.common.artifact_core import write_once
from src.common.contracts import canonical_sha256, read_json


def verify():
    document = check_revision()
    gate = ContinuationGate(REV / "gate")
    gate._check(code(), {"evaluated"})
    if pending(gate, code()):
        raise ValueError("Continuation incomplete")
    future = set(document["approved_run_ids"])
    sources, evidence, total, states, claim_ids = {}, [ref(REV / "declaration.json")], 0, {}, set()
    for dataset in DATASETS:
        folder = BASE / "test_seals" / dataset
        state, manifest = read_json(folder / "seal.json"), read_json(folder / "manifest.json")
        expected_state = "failed_sealed" if folder == OLD else "evaluated"
        if state["state"] != expected_state or state["evaluation_count"] != 1:
            raise ValueError("Original seal/count changed")
        states[dataset] = {
            "original_state": state["state"],
            "evaluation_count": 1,
            "effective_state": "completed_with_authorized_continuation" if folder == OLD else "evaluated",
        }
        receipt = read_json(folder / "cache_receipt.json")
        cache = CachedHoldout(receipt["metadata"], state["manifest_sha256"])
        if len(cache.ids) != EXPECTED[dataset] or len(manifest["members"]) != 20:
            raise ValueError("Incomplete TEST count/members")
        evidence += [
            ref(folder / "seal.json"),
            ref(folder / "manifest.json"),
            receipt["metadata"],
            cache.metadata["arrays"],
        ]
        for member in manifest["members"]:
            run = member["run_id"]
            original_claim = (folder / (run + ".claimed")).exists()
            revised_claim = (REV / "gate" / (run + ".claimed")).exists()
            if original_claim == revised_claim or run in claim_ids:
                raise ValueError("Every member must have exactly one unique original/revised claim")
            claim_ids.add(run)
            result_path = (
                REV / "orphan/result.json"
                if run == ORPHAN
                else (
                    REV / "gate" / (run + ".result.json")
                    if run in future
                    else folder / (run + ".result.json")
                )
            )
            result = read_json(result_path)
            if result["status"] != "PASS" or result["run_id"] != run or result["optimizer_updates"] != 0:
                raise ValueError("Invalid inference-only result")
            for key in ("metrics", "details", "predictions", "checkpoint"):
                checked(result[key])
                evidence.append(result[key])
            selected = read_json(checked(member["selection"]))
            metric, details = read_json(checked(result["metrics"])), read_json(checked(result["details"]))
            original = read_json(checked(selected["validation_metrics"]))
            config = read_json(checked(member["config"]))
            expected_code = (
                code() if run in future or run == ORPHAN else document["original_evaluator_sha256"]
            )
            if (
                result["checkpoint"] != selected["checkpoint"]
                or details["checkpoint"] != selected["checkpoint"]
                or details["training_selection"] != member["selection"]
                or details["evaluator_sha256"] != expected_code
                or details["test_seal_manifest_sha256"] != state["manifest_sha256"]
                or details["test_count"] != len(cache.ids)
                or details["test_forward_passes_per_window"] != 1
                or details["optimizer_updates"] != 0
                or metric["run_id"] != run
                or metric["dataset_id"] != dataset
                or metric["family"] != member["family"]
                or metric["split"] != "test"
                or metric["seed"] != member["seed"]
                or metric["test_seal_id"] != manifest["seal_id"]
                or metric["implementation"]
                != (member["method"] if member["method"] in IMPLEMENTATIONS else "numpy")
                or metric["config_sha256"] != member["config"]["sha256"]
                or metric["evidence_kind"] != "measured"
            ):
                raise ValueError("Result provenance differs from frozen selection: " + run)
            if any(
                canonical_sha256(value) != canonical_sha256(original["efficiency"])
                for value in (metric["efficiency"], details["training_efficiency"])
            ):
                raise ValueError("Original training cost/null telemetry changed")
            if run == ORPHAN:
                validate_recovery_test(metric)
                if not result["schema_recovery_only"] or result["new_test_forward_executed"]:
                    raise ValueError("Orphan must only finalize saved outputs")
            elif member["method"] in IMPLEMENTATIONS:
                validate_run(metric)
            elif metric["schema_version"] != "phase29.causal_baseline_test_run.1":
                raise ValueError("Baseline schema mismatch")
            with gzip.open(checked(result["predictions"]), "rt", encoding="utf-8") as stream:
                rows = [json.loads(line) for line in stream]
            total += audit_saved_rows(cache, rows, details["metrics"])
            audit_metric_rows(metric["metrics"], metric_rows(details["metrics"], config["unit"]))
            sources[run] = ref(result_path)
            evidence.append(ref(result_path))
    if len(sources) != 60 or total != 111900 or len(claim_ids) != 60:
        raise ValueError("Require60 unique once-only members and111900 saved rows")
    result = {
        "phase": 29,
        "revision": "test_schema_r1",
        "status": "PASS",
        "runs": 60,
        "test_prediction_rows": total,
        "test_batches": 3,
        "evaluation_count_per_dataset": 1,
        "original_completed_results": 42,
        "schema_only_recovered_results": 1,
        "unclaimed_continued_results": 17,
        "original_seals": states,
        "continuation": ref(REV / "gate/state.json"),
        "result_refs": sources,
        "evaluator_sha256": code(),
        "new_test_forward_executed": False,
        "optimizer_updates": 0,
        "evidence": list({r["path"]: r for r in evidence}.values()),
    }
    for path in (REV / "verification.json", BASE / "test_verification.json"):
        if path.exists():
            if canonical_sha256(read_json(path)) != canonical_sha256(result):
                raise ValueError("Unified saved-output audit changed; new revision required")
        else:
            write_once(path, result)
    return {k: v for k, v in result.items() if k not in {"evidence", "result_refs"}}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
