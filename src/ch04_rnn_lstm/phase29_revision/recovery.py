"""Versioned recovery schema/journal; never resets the original failed TEST seal."""

import copy
from datetime import UTC, datetime

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from src.ch02_ml.test_gate import atomic_json
from src.ch04_rnn_lstm.export_r2 import RECOVERY_VERSION, recovery_schema
from src.ch04_rnn_lstm.phase29.experiment import metric_rows
from src.ch04_rnn_lstm.phase29.joint_evaluation import pending
from src.ch04_rnn_lstm.phase29.protocol import PREDICTIONS, checked
from src.common.artifact_core import write_once
from src.common.contracts import _finite, _run, canonical_sha256, load_schemas, read_json

SCHEMA_VERSION = "phase29.recovery_test_run.1"


def test_recovery_schema():
    schema = recovery_schema()
    schema["$id"] = "urn:ai-paper:phase29:recovery-test:1"
    schema["title"] = "Exact Phase28 orphan TEST record, missing original cost kept null"
    schema["properties"]["schema_version"] = {"const": SCHEMA_VERSION}
    schema["properties"]["split"] = {"const": "test"}
    return schema


def validate_recovery_test(document):
    registry = Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in load_schemas().values()
    )
    _finite(document)
    errors = list(
        Draft202012Validator(
            test_recovery_schema(), registry=registry, format_checker=FormatChecker()
        ).iter_errors(document)
    )
    if errors:
        raise ValueError("Exact orphan TEST recovery schema: " + errors[0].message)
    _run(document)


def build_orphan_record(
    original, details, selected, predictions_ref, original_details_ref, code, record_time, seal_id, unit
):
    if (
        original["schema_version"] != RECOVERY_VERSION
        or details["optimizer_updates"] != 0
        or details["test_forward_passes_per_window"] != 1
    ):
        raise ValueError("Require already-saved inference-only exact recovery record")
    metric, revised = copy.deepcopy(original), copy.deepcopy(details)
    warning = (
        "Schema-only TEST finalization from saved predictions, no new forward. "
        "started_at/finished_at are recovery record creation time; original TEST inference timestamps unavailable."
    )
    revised.update(
        schema_recovery_only=True,
        original_details=original_details_ref,
        inference_evaluator_sha256=details["evaluator_sha256"],
        evaluator_sha256=code,
        record_finalized_at=record_time,
        timestamp_scope=warning,
    )
    metric.update(
        schema_version=SCHEMA_VERSION,
        split="test",
        test_seal_id=seal_id,
        started_at=record_time,
        finished_at=record_time,
        metrics=metric_rows(details["metrics"], unit),
        artifacts=[
            selected["checkpoint"],
            selected["checkpoint_metadata"],
            predictions_ref,
            original_details_ref,
        ],
    )
    metric["warnings"] = [
        w for w in metric["warnings"] if not w.startswith(("Validation only", "Validation-selected"))
    ]
    metric["warnings"].append(warning)
    validate_recovery_test(metric)
    return metric, revised


def create_gate(root, manifest):
    runs = manifest["approved_run_ids"]
    if not runs or len(runs) != len(set(runs)) or manifest["dataset_id"] != "ch4_household_power":
        raise ValueError("Invalid continuation whitelist")
    old = read_json(checked(manifest["original_seal"]))
    if old["state"] != "failed_sealed" or old["evaluation_count"] != 1:
        raise ValueError("Only a preserved failed original batch may continue")
    checked(manifest["original_manifest"])
    write_once(root / "manifest.json", manifest)
    write_once(
        root / "state.json",
        {
            "state": "prepared",
            "evaluation_count": 1,
            "additional_test_batches": 0,
            "manifest_sha256": old["manifest_sha256"],
            "revision_manifest_sha256": canonical_sha256(manifest),
            "events": [],
        },
    )


class ContinuationGate:
    def __init__(self, root):
        self.root = root

    def state(self):
        return read_json(self.root / "state.json")

    def _check(self, code, allowed):
        state, manifest = self.state(), read_json(self.root / "manifest.json")
        if (
            state["state"] not in allowed
            or code != manifest["evaluator_sha256"]
            or state["revision_manifest_sha256"] != canonical_sha256(manifest)
            or state["evaluation_count"] != 1
            or state["additional_test_batches"] != 0
        ):
            raise ValueError("Continuation state/code/manifest/count mismatch")
        old = read_json(checked(manifest["original_seal"]))
        original = read_json(checked(manifest["original_manifest"]))
        if (
            old["state"] != "failed_sealed"
            or old["evaluation_count"] != 1
            or old["manifest_sha256"] != canonical_sha256(original)
            or state["manifest_sha256"] != old["manifest_sha256"]
        ):
            raise ValueError("Original failed seal/manifest must remain unchanged")
        return state, manifest

    def _consume(self, name):
        try:
            with (self.root / name).open("x", encoding="utf-8") as stream:
                stream.write(datetime.now(UTC).isoformat())
        except FileExistsError:
            raise ValueError("Continuation claim consumed; never repeat TEST") from None

    def _update(self, state, target, reason):
        state["state"] = target
        state["events"].append({"event": target, "reason": reason, "at": datetime.now(UTC).isoformat()})
        atomic_json(self.root / "state.json", state)

    def begin(self, code):
        state, _ = self._check(code, {"prepared"})
        self._consume("continuation.started")
        self._update(
            state, "evaluating", "Continue17 original unclaimed members; no additional TEST batch/cache"
        )

    def materialize(self, code):
        raise ValueError("Original inputs already consumed; TEST cache rematerialization forbidden")

    def claim(self, run, code):
        _, manifest = self._check(code, {"evaluating"})
        original = checked(manifest["original_manifest"]).parent
        if (
            run not in manifest["approved_run_ids"]
            or (original / (run + ".claimed")).exists()
            or (original / (run + ".result.json")).exists()
            or (PREDICTIONS / "test" / (run + ".jsonl.gz")).exists()
        ):
            raise ValueError("Run not unclaimed/approved or already has TEST output")
        self._consume(run + ".claimed")

    def record(self, run, result):
        manifest = read_json(self.root / "manifest.json")
        self._check(manifest["evaluator_sha256"], {"evaluating"})
        if (
            run not in manifest["approved_run_ids"]
            or not (self.root / (run + ".claimed")).exists()
            or result.get("status") != "PASS"
            or result.get("run_id") != run
        ):
            raise ValueError("Invalid or unclaimed continuation result")
        if manifest.get("evidence_kind") != "synthetic_fixture":
            for key in ("metrics", "predictions", "details", "checkpoint"):
                checked(result[key])
        write_once(self.root / (run + ".result.json"), result)

    def complete(self, code):
        state, _ = self._check(code, {"evaluating"})
        if pending(self, code):
            raise ValueError("Incomplete continuation")
        self._update(state, "evaluated", "All unclaimed-only outputs saved; original failure retained")

    def fail(self, reason):
        manifest = read_json(self.root / "manifest.json")
        state, _ = self._check(manifest["evaluator_sha256"], {"evaluating"})
        self._update(state, "failed_sealed", reason)
