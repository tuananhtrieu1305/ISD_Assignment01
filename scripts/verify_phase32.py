"""Serving acceptance/release auditor. Never constructs a model or opens TEST."""

import argparse
import ast
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

from apps.api.v3.openapi import specification
from apps.api.v3.registry import Registry
from scripts.package_phase32 import cpu_requirements
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase32"


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def checked(record):
    path = ROOT / record["path"]
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT) or sha256_file(path) != record["sha256"]:
        raise ValueError("Release integrity check failed: " + record["path"])
    return path


def source_files():
    return sorted(
        {
            *list((ROOT / "apps/api/v3").glob("*.py")),
            *list((ROOT / "scripts").glob("*phase32*.py")),
            *list((ROOT / "tests/serving32").glob("*.py")),
        }
    )


def preflight():
    files = source_files()
    secrets_found = []
    for path in files:
        content = path.read_text(encoding="utf-8")
        ast.parse(content)
        # Scan source only, never .env, job databases, user profiles or Git history.
        for pattern in [r"sk-[A-Za-z0-9]{24,}", r"AKIA[A-Z0-9]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]:
            if re.search(pattern, content):
                secrets_found.append(path.relative_to(ROOT).as_posix())
    if secrets_found:
        raise ValueError("Potential credential pattern in scoped new source")
    lint = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *[str(p) for p in files], "--output-format", "json"],
        check=True,
        text=True,
        capture_output=True,
    )
    if json.loads(lint.stdout):
        raise ValueError("Lint findings")
    if cpu_requirements().encode() != (ROOT / "deploy/v3/requirements-cpu.lock").read_bytes():
        raise ValueError("CPU subset differs from locked runtime")
    api = specification()

    def walk(value):
        if isinstance(value, dict):
            if "$ref" in value:
                target = api
                if not value["$ref"].startswith("#/"):
                    raise ValueError("External API schema ref")
                for part in value["$ref"][2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(api)
    write_once(BASE / "openapi.json", api)
    package = read_json(BASE / "package_v2.json")
    write_once(
        BASE / "active_package.json",
        {
            "revision": "v2",
            "package_receipt": ref(BASE / "package_v2.json"),
            "project": package["project"],
            "archive": package["archive"],
            "registry": ref(Registry().path),
            "openapi": ref(BASE / "openapi.json"),
            "cloud_deployed": False,
        },
    )
    review = {
        "status": "PASS",
        "source": [ref(p) for p in files],
        "ast": "PASS",
        "ruff": "PASS",
        "scoped_secret_patterns": 0,
        "secret_scan_scope": "New Python source only; not history or a CVE database audit",
        "static_type_checker": "not configured; AST/runtime/schema verification used",
        "external_schema_fetch": False,
        "requirements": ref(ROOT / "deploy/v3/requirements-cpu.lock"),
        "uv_lock": ref(ROOT / "uv.lock"),
        "models_retrained": 0,
        "historical_test_evaluation_executed": False,
    }
    write_once(BASE / "code_review.json", review)
    print(json.dumps({"status": "PASS", "source_files": len(files), "stage": "preflight"}))


def xml_count(paths):
    identities = set()
    for path in paths:
        tree = ET.parse(path)
        for case in tree.findall(".//testcase"):
            identity = case.attrib["classname"] + "::" + case.attrib["name"]
            if identity in identities or any(
                case.find(tag) is not None for tag in ["failure", "error", "skipped"]
            ):
                raise ValueError("Duplicate, failed or skipped acceptance testcase")
            identities.add(identity)
    return len(identities)


def acceptance():
    registry = Registry()
    if len(registry.models) != 60 or len(registry.document["runs"]) != 480 or registry.document["seed"] != 42:
        raise ValueError("Registry matrix/count mismatch")
    if any(row["status"] != "ready" for row in registry.components()):
        raise ValueError("Serving assets unavailable")
    for row in registry.files.values():
        registry.checked(row)
    cpu = read_json(BASE / "http_cpu_v2.json")
    gpu = read_json(BASE / "http_gpu_v2.json")
    if (
        cpu["status"] != "PASS"
        or gpu["status"] != "PASS"
        or len(cpu["results"]) != 18
        or len(gpu["results"]) != 12
    ):
        raise ValueError("Live HTTP acceptance incomplete")
    for receipt in [cpu, gpu]:
        for case in receipt["results"]:
            telemetry = case["details"]["serving_telemetry"]
            if telemetry["web_plus_job_peak_sampled_pss_or_rss_bytes"] > telemetry["budget_bytes"]:
                raise ValueError("Serving memory budget exceeded")
            if case["details"]["serving_runtime"]["native_frameworks_imported_in_driver"]:
                raise ValueError("Native framework imported into serving driver")
        if (
            receipt["cloud_deployed"]
            or receipt["models_retrained"]
            or receipt["historical_test_evaluation_executed"]
        ):
            raise ValueError("Serving scope mismatch")
    for case in gpu["results"]:
        if len(case["cpu_gpu_parity"]) != 3 or case["job"]["status"] != "succeeded":
            raise ValueError("Native GPU parity missing")
        for result in case["job"]["results"]:
            expected = {
                "scratch": ("numpy", "cpu"),
                "keras": ("tensorflow", "cuda:0"),
                "pytorch": ("torch", "cuda:0"),
            }[result["implementation"]]
            if (result["actual_backend"], result["actual_device"]) != expected:
                raise ValueError("Backend/device mislabeled")
    checked(gpu["cpu_reference"])
    for case in cpu["results"]:
        if case["dataset_id"] == "ch5_wikidata_subgraphs":
            if not all(r["status"] == "unavailable" for r in case["job"]["results"]):
                raise ValueError("Fabricated Wikidata QA slot")
        elif case["job"]["status"] != "succeeded":
            raise ValueError("CPU slot unavailable")
    orphan = next(
        r for r in registry.document["runs"] if r["run_id"] == "ch4_household_power_rnn_pytorch_s17_main_test"
    )
    metric = registry.json(orphan["record"])
    if any(
        metric["efficiency"][k] is not None for k in ["train_seconds", "peak_ram_bytes", "peak_vram_bytes"]
    ):
        raise ValueError("Original null training costs changed")
    count = xml_count(
        [BASE / "acceptance-tests-v1.xml", BASE / "regression-tests.xml", BASE / "release-unit-final.xml"]
    )
    coverage = read_json(BASE / "acceptance_coverage_v1.json")["totals"]
    if coverage["percent_covered"] < 80:
        raise ValueError("Coverage below80%")
    before, after = [
        read_json(BASE / name) for name in ["preservation_before.json", "preservation_after.json"]
    ]
    if (
        before["status"] != "PASS"
        or after["status"] != "PASS"
        or before["locks"] != after["locks"]
        or before["unique_protected_files"] != after["unique_protected_files"]
    ):
        raise ValueError("Protected baseline changed")
    for record in after["locks"]:
        checked(record)
    review = read_json(BASE / "code_review.json")
    for record in review["source"]:
        checked(record)
    if read_json(BASE / "entrypoint_verification.json")["status"] != "PASS":
        raise ValueError("Entrypoint verification missing")
    package = read_json(BASE / "package_v2.json")
    archive = checked(package["archive"])
    project = ROOT / package["project"]
    manifest = read_json(project / "bundle_manifest.json")
    if sha256_file(project / "bundle_manifest.json") != package["manifest_sha256"]:
        raise ValueError("Package manifest changed")
    for record in manifest["files"]:
        path = project / record["path"]
        if (
            not path.resolve().is_relative_to(project)
            or path.is_symlink()
            or sha256_file(path) != record["sha256"]
        ):
            raise ValueError("Packaged file changed")
        if sha256_file(ROOT / record["path"]) != record["sha256"]:
            raise ValueError("Packaged source differs from current serving source")
    for name in ["http_cpu_v2", "http_gpu_v2"]:
        proof = read_json(BASE / (name + "_bundle_verification.json"))
        if proof["status"] != "PASS" or proof["package_manifest_sha256"] != package["manifest_sha256"]:
            raise ValueError("HTTP probe/package identity mismatch")
    return {
        "status": "PASS",
        "tests": count,
        "coverage": coverage,
        "registry_models": 60,
        "neural_models": 36,
        "historical_runs": 480,
        "cpu_cases": 18,
        "gpu_cases": 12,
        "preserved_files": after["unique_protected_files"],
        "package": ref(archive),
        "cloud_deployed": False,
        "models_retrained": 0,
        "historical_test_evaluation_executed": False,
    }


def verify_lock():
    lock = read_json(BASE / "experiment_lock.json")
    for record in lock["files"]:
        checked(record)
    print(json.dumps({"status": "PASS", "files": len(lock["files"]), "mode": "hash_only_no_inference"}))


def release():
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Release exists; use --verify-only")
    result = acceptance()
    registry = Registry()
    paths = {ROOT / name for name in registry.files}
    paths.add(registry.path)
    paths.update(source_files())
    paths.update((ROOT / "docs").glob("phase32*.md"))
    paths.update((ROOT / "deploy/v3").glob("*"))
    paths.update((ROOT / "scripts").glob("*phase32*.ps1"))
    paths.update(
        ROOT / name
        for name in [
            "scripts/run_api_v3.ps1",
            "scripts/run_api_v3.sh",
            "experiments/configs/v3/phase32_coverage.ini",
        ]
    )
    for name in [
        "preservation_before.json",
        "preservation_after.json",
        "acceptance-tests-v1.xml",
        "regression-tests.xml",
        "release-unit-final.xml",
        "acceptance_coverage_v1.json",
        "http_cpu_v2.json",
        "http_gpu_v2.json",
        "http_cpu_v2_bundle_verification.json",
        "http_gpu_v2_bundle_verification.json",
        "http_cpu_v2.gunicorn.log",
        "http_gpu_v2.gunicorn.log",
        "package_v2.json",
        "openapi.json",
        "code_review.json",
        "entrypoint_verification.json",
        "active_package.json",
    ]:
        paths.add(BASE / name)
    project = ROOT / read_json(BASE / "package_v2.json")["project"]
    paths.update(p for p in project.rglob("*") if p.is_file())
    paths.add(checked(read_json(BASE / "package_v2.json")["archive"]))
    paths.update(checked(r) for r in read_json(BASE / "preservation_after.json")["locks"])
    write_once(
        BASE / "experiment_lock.json",
        {
            "phase": 32,
            "files": [ref(p) for p in sorted(paths)],
            "scope": "Serving source/active compact package/acceptance evidence; old30713 protected files audited separately",
            "historical_test_evaluation_executed": False,
        },
    )
    verify_lock()
    write_once(BASE / "verification.json", {**result, "experiment_lock": ref(BASE / "experiment_lock.json")})
    (BASE / "checkpoint.json").write_text(
        json.dumps(
            {
                "phase": 32,
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
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--release", action="store_true")
    group.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.release:
        release()
    else:
        verify_lock()
