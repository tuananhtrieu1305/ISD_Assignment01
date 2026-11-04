"""Freeze passing development evidence before any real joint TEST claim."""

import argparse
import math
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.phase29_joint_test import EVAL_SOURCE_FILES, ensure_training_complete, evaluator_code
from src.ch04_rnn_lstm.phase29.protocol import BASE, check_sources, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json


def test_evidence(paths):
    unique = set()
    for path in paths:
        root = ET.parse(path).getroot()
        if any(int(s.get(k, 0)) for s in root.iter("testsuite") for k in ("failures", "errors", "skipped")):
            raise ValueError("Pretest suite has failures/errors/skips")
        cases = list(root.iter("testcase"))
        if not cases:
            raise ValueError("Empty pretest suite")
        for case in cases:
            key = (case.get("classname"), case.get("name"))
            if key in unique or any(case.find(k) is not None for k in ("failure", "error", "skipped")):
                raise ValueError("Duplicate/failed/skipped pretest case")
            unique.add(key)
    return len(unique)


def verified_coverage(path):
    total = float(read_json(path)["totals"]["percent_covered"])
    if not math.isfinite(total) or total < 80:
        raise ValueError("Global line/branch coverage below80%")
    return total


def prepare():
    release = check_sources()
    ensure_training_complete(release)
    code = evaluator_code()
    path = BASE / "pretest_verification.json"
    if path.exists():
        result = read_json(path)
        if result["evaluator_sha256"] != code:
            raise ValueError("Pretest proof/evaluator changed; versioned revision required")
        for row in result["evidence"]:
            checked(row)
        return result
    if list((BASE / "test_seals").glob("*/seal.json")):
        raise ValueError("Cannot create prospective proof after TEST seals exist")
    audit_path = BASE / "validation_verification.json"
    audit = read_json(audit_path)
    if (
        audit["status"] != "PASS"
        or audit["runs"] != 108
        or audit["native_cpu_receipts"] != 108
        or audit["evaluator_sha256"] != code
        or audit["test_forward_executed"]
    ):
        raise ValueError("Complete validation/CPU audit missing for this evaluator")
    runtime = BASE / "runtime_recovery/r1/verification.json"
    if read_json(runtime)["status"] != "PASS" or read_json(runtime)["keras_backend"] != "tensorflow":
        raise ValueError("Independent restored GPU runtime not verified")
    names = (
        "development-torch-tests.xml",
        "development-keras-tests.xml",
        "development-regression-tests.xml",
        "development-preservation-tests.xml",
    )
    count = test_evidence([BASE / name for name in names])
    coverage_path = BASE / "development_coverage.json"
    coverage = verified_coverage(coverage_path)
    files = [
        str(ROOT / p)
        for p in EVAL_SOURCE_FILES
        if p.endswith(".py")
        and (
            p.startswith("src/ch04_rnn_lstm/phase29/")
            and p not in {r["path"] for r in release["source_files"]}
            or p.startswith("tests/lstm29/")
            and p not in {r["path"] for r in release["source_files"]}
            or p.startswith("scripts/")
            and p not in {r["path"] for r in release["source_files"]}
        )
    ]
    lint = subprocess.run(
        [str(Path(sys.executable).parent / "ruff"), "check", *files],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    write_once(
        BASE / "development_lint.json", {"status": "PASS", "output": lint.stdout.strip(), "files": files}
    )
    evidence = [ref(BASE / name) for name in names] + [
        ref(coverage_path),
        ref(audit_path),
        ref(runtime),
        ref(BASE / "runtime_recovery/r1/declaration.json"),
        ref(BASE / "development_lint.json"),
        ref(BASE / "trained_validation_registry.json"),
    ]
    for entry in release["runs"]:
        folder = BASE / "runs" / entry["run_id"]
        selected = read_json(folder / "selection.json")
        evidence += [ref(folder / "selection.json"), ref(BASE / "cpu_receipts" / (entry["run_id"] + ".json"))]
        evidence += [v for v in selected.values() if isinstance(v, dict) and set(v) == {"path", "sha256"}]
    deduplicated = {row["path"]: row for row in evidence}
    for row in deduplicated.values():
        checked(row)
    result = {
        "phase": 29,
        "proof_version": "phase29.pretest.1",
        "status": "PASS",
        "evaluator_sha256": code,
        "tests": count,
        "skipped": 0,
        "coverage_percent": coverage,
        "coverage_scope": "src.ch04_rnn_lstm.phase29, lines+branches; frozen core has separate Phase25 evidence",
        "evidence": list(deduplicated.values()),
        "test_evaluation_executed": False,
    }
    write_once(path, result)
    return result


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    document = prepare()
    print({k: document[k] for k in ("status", "tests", "coverage_percent", "evaluator_sha256")})
