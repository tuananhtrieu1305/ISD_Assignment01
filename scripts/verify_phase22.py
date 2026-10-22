"""Offline SRS/schema/traceability audit and content-hash lock. Never evaluates TEST."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from src.common.contracts import ROOT, audit_specification, load_schemas, read_json, validate_document


def spec_files(root: Path):
    explicit = [
        "docs/srs_v3.md",
        "docs/traceability_v3.csv",
        "docs/report_style_v3.md",
        "docs/architecture_v3.mmd",
        "docs/risk_register_v3.csv",
        "docs/contracts/v3/README.md",
        "docs/contracts/v3/openapi.json",
        "experiments/configs/v3/protocol_v3.json",
        "report/outline_v3.json",
    ]
    return sorted(
        [root / path for path in explicit]
        + list((root / "docs/adr").glob("000*-v3-*.md"))
        + list((root / "src/common/schemas/v3").glob("*.schema.json"))
        + list((root / "docs/contracts/v3/examples").glob("*.json"))
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lock", action="store_true", help="Create the first lock only; never overwrite an existing lock"
    )
    args = parser.parse_args()
    audit = audit_specification(ROOT)
    schemas = load_schemas()
    examples = []
    for path in sorted((ROOT / "docs/contracts/v3/examples").glob("*.json")):
        name = path.stem.replace("api_", "api#") if path.stem.startswith("api_") else path.stem
        validate_document(name, read_json(path))
        examples.append(path.relative_to(ROOT).as_posix())
    env = read_json(ROOT / "artifacts/manifests/environment.json")
    env_lock = hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    if env["status"] != "PASS" or env["uv_lock_sha256"] != env_lock:
        audit["errors"].append("Phase21 environment/lock precondition failed")
    ch5_seal = read_json(ROOT / "artifacts/manifests/ch5/phase15_test_run.json")
    if (
        ch5_seal["run_count"] != 1
        or ch5_seal["locked_config_sha256"]
        != read_json(ROOT / "experiments/configs/v3/protocol_v3.json")["ch5"]["test_config_sha256"]
    ):
        audit["errors"].append("Ch5 baseline seal identity changed")
    protected_counts = {"configs": 0, "metrics": 0}
    baseline = ROOT / "artifacts/manifests/phase20/before-files.csv.gz"
    mappings = [
        ("configs", "term_paper/knowledge_rag/config/", "experiments/configs/ch5/"),
        ("metrics", "term_paper/knowledge_rag/artifacts/metrics/", "artifacts/metrics/ch5/"),
    ]
    with gzip.open(baseline, "rt", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            for kind, old_prefix, new_prefix in mappings:
                if row["path"].startswith(old_prefix):
                    protected_counts[kind] += 1
                    target = ROOT / row["path"].replace(old_prefix, new_prefix, 1)
                    if (
                        not target.is_file()
                        or hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256"]
                    ):
                        audit["errors"].append(f"Protected Ch5 {kind} changed: {target.relative_to(ROOT)}")
    if not all(protected_counts.values()):
        audit["errors"].append("Missing protected Ch5 baseline inventory")
    directory = ROOT / "artifacts/manifests/phase22"
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / "spec_lock.json"
    files = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
        }
        for path in spec_files(ROOT)
    ]
    if lock_path.exists():
        if read_json(lock_path)["files"] != files:
            audit["errors"].append(
                "Specification changed after lock; record/approve a versioned deviation, do not overwrite the lock"
            )
    elif args.lock and not audit["errors"]:
        lock_path.write_text(
            json.dumps(
                {"schema_version": "3.0.0", "locked_at": datetime.now(UTC).isoformat(), "files": files},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        audit["errors"].append("No specification lock; first Phase22 acceptance requires --lock")
    result = {
        "phase": 22,
        "status": "PASS" if not audit["errors"] else "FAIL",
        "generated_at": datetime.now(UTC).isoformat(),
        **audit,
        "schemas": len(schemas),
        "validated_examples": examples,
        "locked_files": len(files),
        "test_evaluation_executed": False,
        "environment_lock_unchanged": env["uv_lock_sha256"] == env_lock,
        "protected_ch5_files_checked": protected_counts,
    }
    (directory / "verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
