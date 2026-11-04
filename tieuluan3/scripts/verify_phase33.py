"""Phase33 acceptance/release from saved evidence only; no models or TEST forward."""

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase33"
CHECKS = "acceptance-v3"
E2E = "acceptance-e2e-v3"
LIVE_MATRIX = [
    *[(name, "mlp") for name in ["ch2_cdc_diabetes", "ch2_ames_housing", "ch2_bank_marketing"]],
    *[(name, "cnn") for name in ["ch3_idrid", "ch3_eurosat", "ch3_cifar10"]],
    *[
        (name, family)
        for name in ["ch4_gold_pink_sheet", "ch4_bis_house_prices", "ch4_household_power"]
        for family in ["rnn", "lstm"]
    ],
    *[(name, "kg_rag") for name in ["ch5_medquad_diabetes", "ch5_finqa", "ch5_wikidata_subgraphs"]],
    *[(name, "multi_agent") for name in ["ch6_diabetes_tasks", "ch6_house_tasks", "ch6_gold_tasks"]],
]


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def checked(row):
    path = ROOT / row["path"]
    if not path.resolve().is_relative_to(ROOT) or path.is_symlink() or sha256_file(path) != row["sha256"]:
        raise ValueError("Integrity mismatch: " + row["path"])
    return path


def xml_count(paths):
    names = set()
    for path in paths:
        for row in ET.parse(path).findall(".//testcase"):
            name = row.attrib.get("classname", "") + "::" + row.attrib["name"]
            if name in names or any(row.find(tag) is not None for tag in ["failure", "error", "skipped"]):
                raise ValueError("Failed/skipped/duplicate test")
            names.add(name)
    return len(names)


def validate_coverage(summary):
    for name in ["statements", "branches", "functions", "lines"]:
        percent = summary["total"][name]["pct"]
        if not isinstance(percent, (int, float)) or not 80 <= percent <= 100:
            raise ValueError("Coverage threshold: " + name)


def expected_probe_split(dataset):
    if dataset.startswith("ch5_"):
        return "demo_not_benchmark"
    if dataset.startswith("ch6_"):
        return "parent_train"
    return "train"


def acceptance():
    checks = read_json(BASE / (CHECKS + "_checks.json"))
    if (
        checks["status"] != "PASS"
        or checks["models_retrained"]
        or checks["historical_test_evaluation_executed"]
        or checks["cloud_deployed"]
    ):
        raise ValueError("Invalid checks scope")
    for row in checks["source"] + checks["build_outputs"]:
        checked(row)
    expected_source = hashlib.sha256(
        json.dumps(checks["source"], ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    if expected_source != checks["source_sha256"]:
        raise ValueError("Source fingerprint mismatch")
    for row in checks["records"]:
        if row["status"] != 0:
            raise ValueError("Failed frontend action")
        checked(row["log"])
    advisory = read_json(checked(checks["npm_audit"]))
    if advisory["metadata"]["vulnerabilities"]["total"] != 0:
        raise ValueError("Dependency findings")
    coverage = read_json(BASE / (CHECKS + "_unit-coverage/coverage-summary.json"))
    validate_coverage(coverage)
    xml = xml_count([BASE / (CHECKS + "_unit.xml"), BASE / (E2E + ".xml"), BASE / "auditor-final-r4.xml"])
    legacy = (BASE / (CHECKS + "_test_legacy.log")).read_text(encoding="utf-8")
    if not all(
        re.search(r"^# " + text + r"$", legacy, re.MULTILINE)
        for text in ["tests 10", "pass 10", "fail 0", "skipped 0"]
    ):
        raise ValueError("Legacy regression missing")
    e2e = read_json(BASE / (E2E + ".json"))
    if e2e["stats"]["expected"] != 23 or any(e2e["stats"][key] for key in ["unexpected", "skipped", "flaky"]):
        raise ValueError("Browser acceptance incomplete")
    served = read_json(BASE / (E2E + "-served_build.json"))
    if (
        served["status"] != "PASS"
        or served["source_sha256"] != expected_source
        or served["checks_sha256"] != sha256_file(BASE / (CHECKS + "_checks.json"))
    ):
        raise ValueError("Browser/build identity mismatch")
    if sorted(row["sha256"] for row in served["served"]) != sorted(
        row["sha256"] for row in checks["build_outputs"]
    ):
        raise ValueError("Served bundle differs")
    reference = read_json(ROOT / "artifacts/manifests/phase32/http_cpu_v2.json")
    for dataset, family in LIVE_MATRIX:
        receipt = read_json(BASE / f"{E2E}-{dataset}-{family}.json")
        if (
            receipt["source_sha256"] != expected_source
            or receipt["models_retrained"]
            or receipt["historical_test_evaluation_executed"]
        ):
            raise ValueError("Live receipt scope mismatch")
        if receipt["input_split"] != expected_probe_split(dataset):
            raise ValueError("Unexpected UI probe scope")
        job = receipt["job"]
        old = next(
            row for row in reference["results"] if (row["dataset_id"], row["family"]) == (dataset, family)
        )["job"]
        if [row["implementation"] for row in job["results"]] != [
            row["implementation"] for row in old["results"]
        ]:
            raise ValueError("Missing implementation")
        if dataset == "ch5_wikidata_subgraphs":
            if not all(row["status"] == "unavailable" for row in job["results"]):
                raise ValueError("Fabricated Wikidata QA")
        elif job["status"] != "succeeded":
            raise ValueError("Live serving failed")
        if dataset.startswith(("ch2_", "ch3_", "ch4_")):
            for actual, previous in zip(job["results"], old["results"], strict=True):
                if any(
                    actual[key] != previous[key]
                    for key in ["artifact_sha256", "prediction", "actual_backend", "actual_device"]
                ):
                    raise ValueError("Portable checkpoint output mismatch")
            if len({row["input_sha256"] for row in job["results"]}) != 1 or not job["comparison_valid"]:
                raise ValueError("Not a matched-input comparison")
    before, after = [read_json(BASE / name) for name in ["preserve_before.json", "preserve_after.json"]]
    if before != after or after["status"] != "PASS" or after["unique_protected_files"] != 31641:
        raise ValueError("Protected assets changed")
    for row in after["locks"]:
        checked(row)
    qa = read_json(BASE / "visual_qa.json")
    if qa["status"] != "PASS" or len(qa["images"]) < 7:
        raise ValueError("Visual QA incomplete")
    for row in qa["images"]:
        checked(row)
    review = read_json(BASE / "python_review_r2.json")
    if review["status"] != "PASS":
        raise ValueError("Python review incomplete")
    for row in review["source"]:
        checked(row)
    entrypoints = read_json(checked(review["entrypoints"]))
    for row in entrypoints["source"]:
        checked(row)
    return {
        "status": "PASS",
        "tests": xml + 10,
        "coverage": coverage["total"],
        "e2e_cases": 23,
        "live_demo_cases": 18,
        "neural_train_cases": 12,
        "agent_parent_train_cases": 3,
        "kg_nonbenchmark_cases": 3,
        "protected_files": 31641,
        "source_sha256": expected_source,
        "cloud_deployed": False,
        "models_retrained": 0,
        "historical_test_evaluation_executed": False,
    }


def verify_lock():
    lock = read_json(BASE / "experiment_lock.json")
    for row in lock["files"]:
        checked(row)
    print(json.dumps({"status": "PASS", "files": len(lock["files"]), "mode": "hash_only_no_inference"}))


def release():
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Already released; use --verify-only")
    result = acceptance()
    checks = read_json(BASE / (CHECKS + "_checks.json"))
    paths = {checked(row) for row in checks["source"] + checks["build_outputs"]}
    paths.update(ROOT.glob("docs/phase33*.md"))
    paths.update(ROOT.glob("scripts/*phase33*.*"))
    paths.update(ROOT.glob("tests/ui33/*.py"))
    paths.update(ROOT.glob("deploy/web-v3/*"))
    paths.update(ROOT / name for name in ["scripts/bootstrap_web_v3.ps1", "scripts/run_web_v3.ps1"])
    for name in [
        "preserve_before.json",
        "preserve_after.json",
        "contract_fixtures.json",
        "web_before.json",
        "web_before.zip",
        "visual_qa.json",
        "auditor-final-r4.xml",
        "python_review_r2.json",
        "python_review.json",
        "python_review_r1_source.zip",
        "entrypoint_verification.json",
        CHECKS + "_checks.json",
    ]:
        paths.add(BASE / name)
    for prefix in [CHECKS + "_", E2E]:
        for path in BASE.glob(prefix + "*"):
            if path.is_file():
                paths.add(path)
            elif path.is_dir():
                paths.update(p for p in path.rglob("*") if p.is_file())
    paths.update(checked(row) for row in read_json(BASE / "preserve_after.json")["locks"])
    paths.add(ROOT / "apps/web/scripts/diagnose_phase33.mjs")
    archive = ROOT / f"dist/phase33/web-preview-{CHECKS}.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as stream:
        for row in checks["build_outputs"]:
            path = checked(row)
            stream.write(path, path.relative_to(ROOT / f"dist/phase33/web-preview-{CHECKS}"))
    paths.add(archive)
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 33,
            "files": [ref(p) for p in sorted(paths)],
            "scope": "Active frontend source, immutable local preview/API-origin build, evidence; 31641 parent files audited separately",
            "cloud_deployed": False,
            "historical_test_evaluation_executed": False,
        },
    )
    verify_lock()
    write_once(
        BASE / "verification.json",
        {**result, "experiment_lock": ref(BASE / "experiment_lock.json"), "preview_archive": ref(archive)},
    )
    (BASE / "checkpoint.json").write_text(
        json.dumps(
            {
                "phase": 33,
                "status": "COMPLETE",
                "controller_pid": None,
                "experiment_lock": ref(BASE / "experiment_lock.json"),
                "acceptance": ref(BASE / "verification.json"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--release", action="store_true")
    group.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.release:
        release()
    else:
        verify_lock()
