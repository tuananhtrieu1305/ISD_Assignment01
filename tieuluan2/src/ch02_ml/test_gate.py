"""One-shot TEST journal. Crashes consume a claim; terminal seals cannot reopen."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.common.artifact_core import write_once
from src.common.contracts import canonical_sha256, check_seal_transition, read_json, validate_document


def atomic_json(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class EvaluationGate:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def state(self):
        return read_json(self.root / "seal.json")

    def lock(self, manifest):
        if (self.root / "manifest.json").exists() or (self.root / "seal.json").exists():
            raise ValueError("TEST manifest already locked")
        if not manifest["runs"] or len(set(manifest["runs"])) != len(manifest["runs"]):
            raise ValueError("Missing/duplicate approved runs")
        stamp = datetime.now(UTC).isoformat()
        seal = {
            "schema_version": "3.0.0",
            "evidence_kind": manifest.get("evidence_kind", "measured"),
            "seal_id": manifest["dataset_id"] + "_phase26_test_v1",
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
                    "actor": "phase26_offline_controller",
                    "reason": "All configurations, model selections and code frozen before TEST",
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
        seal["state"] = target
        seal["evaluation_count"] = 0 if target == "locked" else 1
        seal["events"].append(
            {
                "at": datetime.now(UTC).isoformat(),
                "event": event,
                "actor": "phase26_offline_controller",
                "reason": reason,
            }
        )
        validate_document("seal", seal)
        atomic_json(self.root / "seal.json", seal)

    def begin(self, code_sha256):
        seal = self.state()
        if seal["state"] != "locked" or code_sha256 != seal["evaluator_sha256"]:
            raise ValueError("TEST state/code mismatch; cannot begin")
        try:
            with (self.root / "evaluation.started").open("x", encoding="utf-8") as stream:
                stream.write(datetime.now(UTC).isoformat())
        except FileExistsError:
            raise ValueError("TEST batch was already claimed") from None
        self._transition("evaluating", "start", "One authorized evaluation batch; no retry or tuning")

    def _run_path(self, run, suffix):
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,95}", run) or run not in self.state()["approved_run_ids"]:
            raise ValueError("Run not approved")
        return self.root / (run + suffix)

    def claim(self, run, code_sha256):
        seal = self.state()
        if seal["state"] != "evaluating" or code_sha256 != seal["evaluator_sha256"]:
            raise ValueError("No active authorized TEST evaluation")
        try:
            with self._run_path(run, ".claimed").open("x", encoding="utf-8") as stream:
                stream.write(datetime.now(UTC).isoformat())
        except FileExistsError:
            raise ValueError("TEST prediction already claimed; do not repeat") from None

    def record(self, run, result):
        if self.state()["state"] != "evaluating":
            raise ValueError("TEST is not evaluating")
        path = self._run_path(run, ".result.json")
        if path.exists():
            raise ValueError("TEST result already recorded")
        write_once(path, result)

    def complete(self):
        if self.state()["state"] != "evaluating":
            raise ValueError("TEST is not evaluating")
        for run in self.state()["approved_run_ids"]:
            path = self._run_path(run, ".result.json")
            if not path.exists() or read_json(path).get("status") != "PASS":
                raise ValueError("Incomplete/failed TEST batch")
        self._transition("evaluated", "complete", "All approved predictions and metrics saved once")

    def fail(self, reason):
        self._transition("failed_sealed", "fail", reason)
