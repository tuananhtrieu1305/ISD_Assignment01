"""Read-only forensic audit of saved TEST bytes after a schema-only finalization failure.

Never constructs a model, changes a seal/claim, writes a metric or forwards TEST.
"""

import copy
import gzip
import json
from pathlib import Path

from scripts.phase29_joint_test import evaluator_code
from scripts.verify_phase29_test import audit_saved_rows
from src.ch04_rnn_lstm.export_r2 import ORPHAN, validate_run
from src.ch04_rnn_lstm.phase29.holdout_cache import CachedHoldout
from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json


def main():
    dataset = "ch4_household_power"
    gate = BASE / "test_seals" / dataset
    state, manifest = read_json(gate / "seal.json"), read_json(gate / "manifest.json")
    if state["state"] != "failed_sealed" or state["evaluation_count"] != 1:
        raise ValueError("Expected preserved failed-sealed original batch")
    code = evaluator_code()
    if code != manifest["evaluator_sha256"] or code != read_json(BASE / "pretest_verification.json")["evaluator_sha256"]:
        raise ValueError("Frozen evaluator identity changed")
    member = next(m for m in manifest["members"] if m["run_id"] == ORPHAN)
    selected = read_json(checked(member["selection"]))
    details_path = BASE / "test_details" / (ORPHAN + ".json")
    predictions_path = ROOT / "artifacts/predictions/phase29/test" / (ORPHAN + ".jsonl.gz")
    details = read_json(details_path)
    receipt = read_json(gate / "cache_receipt.json")
    cache = CachedHoldout(receipt["metadata"], state["manifest_sha256"])
    with gzip.open(predictions_path, "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    audited = audit_saved_rows(cache, rows, details["metrics"])
    if (audited != 4911 or details["optimizer_updates"] != 0 or details["test_forward_passes_per_window"] != 1
            or details["checkpoint"] != selected["checkpoint"]):
        raise ValueError("Partial prediction/checkpoint/inference identity mismatch")
    original = read_json(checked(selected["validation_metrics"]))
    if any(original["efficiency"][k] is not None for k in ("train_seconds", "peak_ram_bytes", "peak_vram_bytes")):
        raise ValueError("Original missing telemetry must stay null")
    candidate = copy.deepcopy(original)
    candidate["split"] = "test"
    try:
        validate_run(candidate)
    except ValueError as error:
        schema_error = str(error)
    else:
        raise ValueError("Expected validation-only recovery schema rejection")
    states, complete, claimed, unclaimed, evidence = {}, 0, 0, [], []
    for ds in DATASETS:
        folder = BASE / "test_seals" / ds
        seal = read_json(folder / "seal.json")
        declarations = read_json(folder / "manifest.json")
        states[ds] = {"state": seal["state"], "evaluation_count": seal["evaluation_count"]}
        evidence += [ref(folder / "seal.json"), ref(folder / "manifest.json")]
        for run in declarations["approved_run_ids"]:
            claim = folder / (run + ".claimed")
            result = folder / (run + ".result.json")
            if claim.exists():
                claimed += 1
                evidence.append(ref(claim))
            else:
                unclaimed.append(run)
            if result.exists():
                value = read_json(result)
                for name in ("metrics", "predictions", "details", "checkpoint"):
                    checked(value[name])
                    evidence.append(value[name])
                complete += 1
                evidence.append(ref(result))
    if complete != 42 or claimed != 43 or len(unclaimed) != 17:
        raise ValueError("Unexpected incident claim/result counts; inspect without retry")
    if (gate / (ORPHAN + ".result.json")).exists() or (ROOT / "artifacts/metrics/phase29/test" / (ORPHAN + ".json")).exists():
        raise ValueError("Do not overwrite a metric/result")
    log = BASE / "test_logs/ch4_household_power_ch4_household_power_rnn_pytorch_s17_main_20261019T232946861015Z.log"
    evidence += [ref(details_path), ref(predictions_path), ref(log), receipt["metadata"], cache.metadata["arrays"],
                 member["selection"], selected["checkpoint"], selected["validation_metrics"],
                 ref(ROOT / "src/ch04_rnn_lstm/export_r2.py"), ref(BASE / "pretest_verification.json"), ref(Path(__file__))]
    result = {"phase": 29, "incident": "phase29.test_recovery_schema.v1", "diagnosis_status": "PASS",
              "phase_status": "IN_PROGRESS_AWAITING_REVISION_APPROVAL", "evaluator_sha256": code,
              "failed_run": ORPHAN, "stage": "metric schema validation AFTER saved predictions/details",
              "schema_error": schema_error, "saved_partial_rows_audited": audited,
              "original_checkpoint": selected["checkpoint"], "native_optimizer_updates_recorded": 0,
              "original_train_ram_vram": {k: original["efficiency"][k] for k in ("train_seconds", "peak_ram_bytes", "peak_vram_bytes")},
              "completed_results": complete, "consumed_claims": claimed, "unclaimed_runs": unclaimed,
              "seals": states, "new_test_forward_executed": False, "seals_or_claims_modified": False,
              "proposal_not_authorized": "Versioned TEST recovery schema for this orphan only; finalize from saved4911 predictions with no repeat; preserve original failed seal and all existing bytes; versioned continuation only for17 unclaimed members, no cache rebuild/retraining/tuning",
              "evidence": list({row["path"]: row for row in evidence}.values())}
    path = BASE / "incidents/test_recovery_schema_v1/diagnosis.json"
    write_once(path, result)
    print(json.dumps({k: v for k, v in result.items() if k not in {"evidence", "unclaimed_runs"}}, indent=2))


if __name__ == "__main__":
    main()
