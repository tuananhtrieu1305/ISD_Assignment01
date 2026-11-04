"""Read-only task/trace/result audit, prospective lint proof, and immutable release lock."""

import argparse
import ast
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from scripts.phase31_benchmark import BASE, SOURCE_FILES, load_inputs, verify_declaration
from src.ch05_knowledge_rag.preservation import checked, ref
from src.ch06_multi_agent.benchmark import score
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document


def lint():
    paths = sorted(
        {
            p
            for p in SOURCE_FILES + ["scripts/demo_phase31.py", "scripts/verify_phase31.py"]
            if p.endswith(".py")
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *paths], cwd=ROOT, capture_output=True, text=True, check=True
    )
    for path in paths:
        ast.parse((ROOT / path).read_text(encoding="utf-8"))
    write_once(
        BASE / "lint.json",
        {
            "status": "PASS",
            "files": [ref(ROOT / p) for p in paths],
            "ruff": result.stdout.strip(),
            "ast_parse": True,
            "type_checker": "not_run; no new dependency installed",
        },
    )


def audit_results(*, include_test):
    view, _, tasks = load_inputs()
    lookup = {r["request"]["task_id"]: r for r in tasks}
    documents = [read_json(BASE / "development_v2_complete.json")]
    if include_test:
        verify_declaration()
        documents.append(read_json(BASE / "test_complete.json"))
        claim = read_json(BASE / "agent_test.claimed.json")
        if claim["evaluation_count"] != 1 or claim["historical_model_test_batches"] != 0:
            raise ValueError("Task TEST claim count changed")
    seen, rows = set(), []
    for document in documents:
        if document["parent_test_forward"] or document["base_models_retrained"] or document["api_keys_used"]:
            raise ValueError("Illegal benchmark scope")
        for reference in document["result_refs"]:
            row = read_json(checked(reference))
            pair = (row["task_id"], row["variant"])
            if pair in seen:
                raise ValueError("Duplicate task/variant result")
            seen.add(pair)
            task = lookup[row["task_id"]]
            output = row["output"]
            trace = output["trace"]
            validate_document("agent", trace, publish=True)
            if (
                trace["task_set_sha256"] != view["taskset"]["sha256"]
                or trace["task_id"] != row["task_id"]
                or trace["variant"] != row["variant"]
                or task["split"] != row["split"]
                or trace["domain"] != task["domain"]
                or output["tool_calls"] > 8
                or trace["latency_ms"] > 15050
            ):
                raise ValueError("Trace identity or budget mismatch")
            if (
                len(trace["nodes"]) != len(output["messages"])
                or len(trace["nodes"]) != output["message_count"]
            ):
                raise ValueError("Message count mismatch")
            for node, message in zip(trace["nodes"], output["messages"], strict=True):
                if (
                    node["node_id"] != message["node_id"]
                    or node["input_sha256"] != canonical_sha256(message["input"])
                    or node["output_sha256"] != canonical_sha256(message["output"])
                ):
                    raise ValueError("Message/action hash mismatch")
            expected = score(task, output)
            expected["latency_ms"] = output["wall_latency_ms"]
            if expected != row["metrics"]:
                raise ValueError("Saved metric row does not reproduce from frozen rubric")
            if (
                not math.isfinite(output["wall_latency_ms"])
                or output["wall_latency_ms"] < trace["latency_ms"]
            ):
                raise ValueError("Invalid measured latency")
            rows.append(row)
    expected_pairs = {
        (r["request"]["task_id"], v)
        for r in tasks
        for v in ("A0", "A1", "A2")
        if include_test or r["split"] != "test"
    }
    if seen != expected_pairs:
        raise ValueError("Incomplete benchmark matrix")
    if include_test and set(map(tuple, claim["approved_pairs"])) != {
        p for p in seen if lookup[p[0]]["split"] == "test"
    }:
        raise ValueError("Claim/results matrix mismatch")
    return rows


def xml_count(paths):
    keys = set()
    for path in paths:
        suites = ET.parse(path).getroot()
        if any(int(s.get(k, 0)) for s in suites.iter("testsuite") for k in ("failures", "errors", "skipped")):
            raise ValueError("Failed/skipped acceptance test")
        for case in suites.iter("testcase"):
            key = (case.get("classname"), case.get("name"))
            if key in keys:
                raise ValueError("Duplicate acceptance XML testcase")
            keys.add(key)
    if not keys:
        raise ValueError("Empty test report")
    return len(keys)


def audit_release():
    rows = audit_results(include_test=True)
    print("Verifying all protected parent files; no inference", flush=True)
    protected = read_json(BASE / "protected_snapshot.json")
    for i, record in enumerate(protected["files"]):
        checked(record)
        if i % 5000 == 0:
            print(f"Protected {i}/{len(protected['files'])}", flush=True)
    for record in protected["locks"]:
        checked(record)
    count = xml_count([BASE / "pretest-tests.xml", BASE / "regression-tests.xml", BASE / "report-tests.xml"])
    totals = read_json(BASE / "pretest_coverage.json")["totals"]
    if totals["percent_covered"] < 80:
        raise ValueError("Coverage below80")
    export = read_json(BASE / "report_generation.json")
    qa = read_json(BASE / "visual_qa.json")
    pngs = {r["path"] for r in export["figures"] if r["path"].endswith(".png")}
    if qa["status"] != "PASS" or set(qa["reviewed_pngs"]) != pngs or len(pngs) != 5:
        raise ValueError("Require visual review of all five PNGs")
    if export["notebooks_executed"] != 3 or export["demo_variant_slots"] != 9:
        raise ValueError("Notebook real CPU demo incomplete")
    for record in export["files"]:
        checked(record)
    manuscript = checked(export["manuscript"]).read_text(encoding="utf-8")
    for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", manuscript):
        path = (checked(export["manuscript"]).parent / target).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Broken manuscript figure reference")
    for name in ("docs/phase31_report.md", "docs/phase31_operations.md", "docs/phase31_protocol.md"):
        if not (ROOT / name).is_file():
            raise ValueError("Missing handoff")
    return {
        "phase": 31,
        "status": "PASS",
        "results": len(rows),
        "tasks": 300,
        "agent_test_evaluation_count": 1,
        "historical_model_test_batches_added": 0,
        "tests": count,
        "skipped": 0,
        "coverage": totals,
        "protected_files": len(protected["files"]),
        "declaration": ref(BASE / "declaration.json"),
        "report": ref(BASE / "report_generation.json"),
    }


def release():
    result = audit_release()
    write_once(BASE / "verification.json", result)
    names = set()
    for folder in (
        BASE,
        ROOT / "data/processed/v3/phase31",
        ROOT / "artifacts/figures/phase31",
        ROOT / "artifacts/metrics/phase31",
        ROOT / "report/references/dataset_cards/v3_agent",
        ROOT / "experiments/notebooks/v3/ch06_multi_agent",
    ):
        names.update(
            p
            for p in folder.rglob("*")
            if p.is_file()
            and not p.name.startswith(".")
            and p.name not in {"experiment_lock.json", "checkpoint.json", "lock_verification.json"}
        )
    names.update(ROOT / p for p in SOURCE_FILES)
    names.update(
        ROOT / p
        for p in (
            "scripts/demo_phase31.py",
            "scripts/verify_phase31.py",
            "scripts/build_phase31.py",
            "scripts/check_phase31.ps1",
            "tests/agents31_report/test_report.py",
            "docs/phase31_report.md",
            "docs/phase31_operations.md",
            "report/sections/v3/ch06_multi_agent.md",
        )
    )
    members = [ref(path) for path in sorted(names)]
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 31,
            "files": members,
            "acceptance": ref(BASE / "verification.json"),
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    verify_lock()
    write_once(
        BASE / "checkpoint.json",
        {
            "phase": 31,
            "status": "COMPLETE",
            "controller_pid": None,
            "experiment_lock": ref(BASE / "experiment_lock.json"),
            "acceptance": ref(BASE / "verification.json"),
        },
    )
    print(result, flush=True)


def verify_lock():
    path = BASE / "experiment_lock.json"
    lock = read_json(path)
    for record in lock["files"]:
        checked(record)
    print({"status": "PASS", "files": len(lock["files"]), "lock": ref(path)}, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", choices=("lint", "development", "audit", "release", "verify-lock"), required=True
    )
    args = parser.parse_args()
    if args.stage == "lint":
        lint()
    elif args.stage == "development":
        print({"development_results": len(audit_results(include_test=False)), "status": "PASS"})
    elif args.stage == "audit":
        print({"results": len(audit_results(include_test=True)), "status": "PASS"})
    elif args.stage == "release":
        release()
    else:
        verify_lock()


if __name__ == "__main__":
    main()
