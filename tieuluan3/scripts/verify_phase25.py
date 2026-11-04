"""Read-only acceptance gates for Phase25; no model TEST execution."""

from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from scripts.prepare_phase25 import BASE, CORE_FILES, FUNCTIONS, architecture_for, validate_adapter
from src.common.artifact_core import code_fingerprint, sha256_file, write_once
from src.common.contracts import PROTOCOL, ROOT, canonical_sha256, read_json
from src.common.data_access import DatasetView
from src.common.eda_artifacts import reference, write_json
from src.common.model_core import canonical_weights, validate_model


def verify_files(root, records):
    for row in records:
        if sha256_file(root / row["path"]) != row["sha256"]:
            raise ValueError(f"Locked hash mismatch: {row['path']}")
    return len(records)


def check_xml(path):
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    if not suites or any(
        int(row.attrib.get(k, 0)) for row in suites for k in ("failures", "errors", "skipped")
    ):
        raise ValueError("Test evidence has failures/errors/skips")
    total = sum(int(row.attrib["tests"]) for row in suites)
    if total < 1:
        raise ValueError("Empty test evidence")
    return total


def verify(create_lock=False):
    protected = {}
    for phase, filename in ((22, "spec_lock.json"), (24, "data_lock.json")):
        lock = read_json(ROOT / f"artifacts/manifests/phase{phase}/{filename}")
        protected[str(phase)] = verify_files(ROOT, lock["files"])
    protocol = read_json(PROTOCOL)
    registry = read_json(BASE / "initialized_contract_registry.json")
    if registry["code_sha256"] != code_fingerprint(ROOT, CORE_FILES):
        raise ValueError("Core changed after contract generation")
    verify_files(ROOT, registry["code_files"])
    if (
        registry["inference_ready"]
        or registry["lifecycle"] != "initialized_only"
        or len(registry["models"]) != 36
        or len(registry["adapters"]) != 9
    ):
        raise ValueError("Wrong registry lifecycle/count")
    seen = set()
    groups = {}
    summary = {}
    for ref in registry["adapters"]:
        verify_files(ROOT, [ref])
        document = read_json(ROOT / ref["path"])
        validate_adapter(document)
        if document != DatasetView(document["dataset_id"]).contract():
            raise ValueError("Adapter differs from locked data state")
    for entry in registry["models"]:
        verify_files(ROOT, [entry["contract"], entry["config"], entry["adapter"]])
        contract = read_json(ROOT / entry["contract"]["path"])
        validate_model(contract)
        if contract["model_id"] in seen or entry["inference_ready"]:
            raise ValueError("Duplicate/incorrectly published model")
        seen.add(contract["model_id"])
        view = DatasetView(entry["dataset_id"])
        plan = architecture_for(view, entry["family"])
        config = read_json(ROOT / entry["config"]["path"])
        for seed in protocol["seeds"]["stability"]:
            digest = canonical_sha256({k: v.tolist() for k, v in canonical_weights(plan, seed).items()})
            if config["canonical_initial_weights_by_seed_sha256"][str(seed)] != digest:
                raise ValueError("Canonical initialization changed")
        if (
            contract["config_sha256"] != entry["config"]["sha256"]
            or contract["dataset_sha256"] != view.provenance["dataset_sha256"]
        ):
            raise ValueError("Model provenance mismatch")
        key = (entry["dataset_id"], entry["family"])
        groups.setdefault(key, []).append(
            (contract["implementation"], contract["comparison_group_sha256"], contract["parameter_count"])
        )
        summary[key] = contract["parameter_count"]
        folder = (ROOT / entry["contract"]["path"]).parent
        if read_json(folder / "functions.json")["plain"] != contract["composition_plain"]:
            raise ValueError("Function renderer differs")
        with (folder / "functions.csv").open(encoding="utf-8", newline="") as stream:
            if len(list(csv.DictReader(stream))) != len(contract["functions"]):
                raise ValueError("Function CSV row mismatch")
    if len(groups) != 12 or any(
        {v[0] for v in values} != {"scratch", "keras", "pytorch"}
        or len({v[1] for v in values}) != 1
        or len({v[2] for v in values}) != 1
        for values in groups.values()
    ):
        raise ValueError("Comparison groups differ")
    probes = {}
    for implementation in ("keras", "pytorch"):
        for device in ("cpu", "gpu"):
            probe = read_json(BASE / f"probe_{implementation}_{device}.json")
            if probe["code_sha256"] != registry["code_sha256"] or probe["probe_code_sha256"] != sha256_file(
                ROOT / "scripts/phase25_backend_probe.py"
            ):
                raise ValueError("Probe ran different code")
            if (
                probe["status"] != "PASS"
                or len(probe["parity"]) != 4
                or probe["real_dataset_training_executed"]
                or probe["test_evaluation_executed"]
            ):
                raise ValueError("Probe did not pass safely")
            if probe["protocol_sha256"] != sha256_file(PROTOCOL) or probe[
                "phase24_lock_sha256"
            ] != sha256_file(ROOT / "artifacts/manifests/phase24/data_lock.json"):
                raise ValueError("Probe dependency mismatch")
            for row in probe["parity"]:
                if (
                    row["gradient_parity"]["max_relative_l2_error"]
                    > protocol["comparison"]["numeric_parity"]["gradient_relative_error"]
                ):
                    raise ValueError("Gradient parity above locked tolerance")
            if device == "gpu":
                if len(probe["memory_probes"]) != 12:
                    raise ValueError("Missing real-dimension GPU probes")
                for row in probe["memory_probes"]:
                    if (
                        row["parameter_count"] != summary[(row["dataset_id"], row["family"])]
                        or not 0 < row["peak_vram_bytes"] < 8 * 1024**3
                    ):
                        raise ValueError("Memory/parameter probe mismatch")
                    if not any(tag in row["actual_device"].lower() for tag in ("gpu", "cuda")):
                        raise ValueError("GPU placement mismatch")
            probes[f"{implementation}_{device}"] = {
                "parity_families": len(probe["parity"]),
                "dimension_probes": len(probe["memory_probes"]),
                "max_peak_vram_bytes": max([r["peak_vram_bytes"] for r in probe["memory_probes"]], default=0),
            }
    tests = {
        name: check_xml(BASE / filename)
        for name, filename in (
            ("core_torch", "core-tests-torch.xml"),
            ("core_keras", "core-tests-keras.xml"),
            ("regression", "regression-tests.xml"),
        )
    }
    coverage = read_json(BASE / "core_coverage_combined.json")
    module_coverage = {name: row["summary"]["percent_covered"] for name, row in coverage["files"].items()}
    if len(module_coverage) != len(CORE_FILES) or min(module_coverage.values()) < 80:
        raise ValueError(f"Core module coverage below 80%: {module_coverage}")
    seal = read_json(ROOT / "artifacts/manifests/ch5/phase15_test_run.json")
    if seal["run_count"] != 1:
        raise ValueError("Ch5 TEST run count changed")
    files = []
    for name in ("adapters", "configs", "contracts", "plans"):
        files.extend((BASE / name).rglob("*.*"))
    files += list(FUNCTIONS.glob("*.md")) + [ROOT / path for path in CORE_FILES]
    files += list((ROOT / "tests/core").glob("*.py")) + list(
        (ROOT / "src/common/schemas/phase25").glob("*.json")
    )
    files += [
        ROOT / "scripts" / name
        for name in ("prepare_phase25.py", "phase25_backend_probe.py", "verify_phase25.py")
    ]
    files += [
        ROOT / "experiments/configs/v3/phase25_coverage.ini",
        BASE / "initialized_contract_registry.json",
    ]
    files += [ROOT / "scripts/check_phase25.ps1", ROOT / "docs/model_core_v3.md"]
    files += [BASE / f"probe_{i}_{d}.json" for i in ("keras", "pytorch") for d in ("cpu", "gpu")]
    files += [
        BASE / filename
        for filename in (
            "core-tests-torch.xml",
            "core-tests-keras.xml",
            "regression-tests.xml",
            "core_coverage_combined.json",
        )
    ]
    records = [reference(path) for path in sorted(set(files))]
    lock_path = BASE / "core_lock.json"
    if lock_path.exists():
        if read_json(lock_path)["files"] != records:
            raise ValueError("Phase25 changed after lock; create a versioned revision")
    elif create_lock:
        write_once(
            lock_path,
            {
                "phase": 25,
                "files": records,
                "phase22_lock_sha256": sha256_file(ROOT / "artifacts/manifests/phase22/spec_lock.json"),
                "phase24_lock_sha256": sha256_file(ROOT / "artifacts/manifests/phase24/data_lock.json"),
                "real_dataset_training_executed": False,
                "test_evaluation_executed": False,
            },
        )
    return {
        "phase": 25,
        "status": "PASS",
        "at": datetime.now(UTC).isoformat(),
        "model_contracts": 36,
        "adapters": 9,
        "architecture_plans": 12,
        "canonical_seed_initializations": 36,
        "protected_files": protected,
        "tests": tests,
        "coverage_percent": coverage["totals"]["percent_covered"],
        "module_coverage": module_coverage,
        "probes": probes,
        "ch5_test_run_count": 1,
        "locked_files": len(records),
        "core_lock_created": lock_path.exists(),
        "real_dataset_training_executed": False,
        "test_evaluation_executed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.lock)
    except (OSError, ValueError, KeyError, IndexError) as error:
        result = {"phase": 25, "status": "FAIL", "error": f"{type(error).__name__}: {error}"}
    write_json(BASE / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result["status"] != "PASS"


if __name__ == "__main__":
    raise SystemExit(main())
