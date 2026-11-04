"""Fail-closed Phase29 joint TEST journal; claims precede input materialization.

This is an offline ledger, not an authentication boundary against a workspace
owner. Real evaluation additionally requires pinned selections/evaluator/proof.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

from src.ch02_ml.test_gate import atomic_json
from src.common.artifact_core import write_once
from src.common.contracts import canonical_sha256, read_json

DATASETS = {"ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power"}


class JointGate:
    def __init__(self, root):
        self.root = Path(root)

    def state(self):
        return read_json(self.root / "seal.json")

    def lock(self, manifest):
        runs = manifest.get("approved_run_ids", [])
        if (
            manifest.get("phase") != 29
            or manifest.get("dataset_id") not in DATASETS
            or set(manifest.get("families_locked", [])) != {"rnn", "lstm"}
            or not runs
            or len(runs) != len(set(runs))
            or any(not isinstance(r, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,95}", r) for r in runs)
            or any(
                not isinstance(manifest.get(k), str) or not re.fullmatch(r"[a-f0-9]{64}", manifest[k])
                for k in ("evaluator_sha256", "pretest_verification_sha256")
            )
        ):
            raise ValueError("Invalid/incomplete joint TEST declaration")
        if (self.root / "manifest.json").exists() or (self.root / "seal.json").exists():
            raise ValueError("Joint TEST already locked")
        stamp = datetime.now(UTC).isoformat()
        write_once(self.root / "manifest.json", manifest)
        write_once(
            self.root / "seal.json",
            {
                "phase": 29,
                "dataset_id": manifest["dataset_id"],
                "state": "locked",
                "evaluation_count": 0,
                "manifest_sha256": canonical_sha256(manifest),
                "events": [{"at": stamp, "event": "lock"}],
            },
        )

    def _check(self, code, allowed):
        state = self.state()
        manifest = read_json(self.root / "manifest.json")
        if (
            state["state"] not in allowed
            or code != manifest.get("evaluator_sha256")
            or canonical_sha256(manifest) != state["manifest_sha256"]
        ):
            raise ValueError("Joint TEST state/code/manifest mismatch")
        return state, manifest

    def _consume(self, filename):
        try:
            with (self.root / filename).open("x", encoding="utf-8") as stream:
                stream.write(datetime.now(UTC).isoformat())
        except FileExistsError:
            raise ValueError("Joint TEST claim already consumed; no retry") from None

    def _update(self, state, target, reason):
        state.update(state=target, evaluation_count=1)
        state["events"].append({"at": datetime.now(UTC).isoformat(), "event": target, "reason": reason})
        atomic_json(self.root / "seal.json", state)

    def begin(self, code):
        state, _ = self._check(code, {"locked"})
        self._consume("evaluation.started")
        self._update(state, "evaluating", "One joint batch; claim consumed before materialization")

    def materialize(self, code):
        self._check(code, {"evaluating"})
        self._consume("inputs.materialized")

    def claim(self, run, code):
        _, manifest = self._check(code, {"evaluating"})
        if run not in manifest["approved_run_ids"]:
            raise ValueError("Run not approved")
        self._consume(run + ".claimed")

    def record(self, run, result):
        manifest = read_json(self.root / "manifest.json")
        self._check(manifest.get("evaluator_sha256"), {"evaluating"})
        if run not in manifest["approved_run_ids"] or not (self.root / (run + ".claimed")).is_file():
            raise ValueError("Result without an approved consumed claim")
        path = self.root / (run + ".result.json")
        if path.exists() or result.get("status") != "PASS":
            raise ValueError("Duplicate or unsuccessful TEST result")
        write_once(path, result)

    def complete(self, code):
        state, manifest = self._check(code, {"evaluating"})
        for run in manifest["approved_run_ids"]:
            path = self.root / (run + ".result.json")
            if not path.exists() or read_json(path).get("status") != "PASS":
                raise ValueError("Incomplete joint TEST batch")
        self._update(
            state, "evaluated", "All approved predictions saved; no tuning or TEST forward after this"
        )

    def fail(self, reason):
        manifest = read_json(self.root / "manifest.json")
        state, _ = self._check(manifest.get("evaluator_sha256"), {"evaluating"})
        self._update(state, "failed_sealed", reason)
