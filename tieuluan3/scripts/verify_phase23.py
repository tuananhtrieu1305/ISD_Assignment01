"""Offline acceptance: source hashes/contracts, protected snapshots, explicit gates."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import yaml

from src.common.acquisition import file_digest
from src.common.contracts import ROOT, read_json, validate_document
from src.common.provenance import check_revision_scope, repo_path
from src.common.source_inspection import inspect_source, require


def check_acquisition_state(contract):
    """Do not let an unacquired automatic source pass as a declared placeholder."""
    if contract["chapter"] == 6:
        require(
            not contract["files"] and contract["status"] == "declared",
            "Ch6 task views must remain declared without duplicate raw files",
        )
    elif contract["dataset_id"] == "ch3_idrid" and contract["status"] == "pending_user_download":
        require(not contract["files"], "Pending IDRiD must not claim unverified file evidence")
    else:
        require(contract["status"] == "ready", "Every automatically acquired source must be ready")


def check_provenance_lock(path, files, create_lock=False):
    """Create the first lock only. A repeat call cannot bless changed evidence."""
    if path.exists():
        require(
            read_json(path)["files"] == files,
            "Provenance changed after Phase23 lock; use a reviewed versioned update, never overwrite lock",
        )
    else:
        require(create_lock, "No dataset lock; first successful acceptance requires --lock")
        with path.open("x", encoding="utf-8") as handle:
            json.dump(
                {"schema_version": "3.0.0", "at": datetime.now(UTC).isoformat(), "files": files},
                handle,
                indent=2,
            )
            handle.write("\n")


def provenance_records(registry):
    paths = [
        ROOT / "data/registry.yaml",
        ROOT / registry["source_catalog"],
        ROOT / "artifacts/manifests/phase23/source_discovery.json",
    ]
    paths += list((ROOT / "artifacts/manifests/phase23/receipts").glob("*.json"))
    paths += [repo_path(ROOT, path) for path in registry.get("provenance_evidence_paths", [])]
    for entry in registry["datasets"]:
        envelope = read_json(ROOT / entry["manifest"])
        paths += [ROOT / entry["manifest"], ROOT / envelope["contract"]["data_card_path"]]
        if envelope["archive_inventory"]:
            paths.append(ROOT / envelope["archive_inventory"]["path"])
    return [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": file_digest(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(set(paths))
    ]


def verify_registry(deep=False, create_lock=False):
    registry = yaml.safe_load((ROOT / "data/registry.yaml").read_text(encoding="utf-8"))
    specs = {
        spec["dataset_id"]: spec
        for spec in read_json(ROOT / "experiments/configs/v3/protocol_v3.json")["datasets"]
    }
    require(registry["schema_version"] == "3.0.0", "Registry schema/version mismatch")
    require({row["id"] for row in registry["datasets"]} == set(specs), "Registry IDs incomplete")
    require(
        file_digest(ROOT / registry["source_catalog"]) == registry["source_catalog_sha256"],
        "Source catalog changed",
    )
    errors, files, archives, statuses = [], [], [], Counter()

    def check_file(row):
        path = ROOT / row["path"]
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != row["size_bytes"]
            or file_digest(path) != row["sha256"]
        ):
            return row["path"]
        return None

    for entry in registry["datasets"]:
        envelope = read_json(ROOT / entry["manifest"])
        require(file_digest(ROOT / entry["manifest"]) == entry["manifest_sha256"], "Dataset manifest changed")
        contract = envelope["contract"]
        validate_document("dataset", contract)
        check_acquisition_state(contract)
        spec = specs[entry["id"]]
        require(
            all(
                contract[key] == spec[key]
                for key in ("dataset_id", "chapter", "kind", "target", "parent_dataset_ids")
            ),
            "Dataset/protocol mismatch",
        )
        require(
            contract["status"] == entry["status"] and contract["logical_size"] == entry["logical_size"],
            "Registry status/count drift",
        )
        require((ROOT / contract["data_card_path"]).is_file(), "Missing source data card")
        statuses[contract["status"]] += 1
        files.extend(contract["files"])
        if envelope["archive_inventory"]:
            archive = envelope["archive_inventory"]
            files.append({key: archive[key] for key in ("path", "size_bytes", "sha256")})
            archives.append(archive)
        require(
            not envelope["training_executed"] and not envelope["test_evaluation_executed"],
            "Phase23 cannot train/evaluate",
        )
        require(
            envelope["protocol_sha256"] == file_digest(ROOT / "experiments/configs/v3/protocol_v3.json"),
            "Protocol drift",
        )
        if deep and entry["id"] in read_json(ROOT / registry["source_catalog"])["sources"]:
            inspection = inspect_source(entry["id"], ROOT / contract["files"][0]["path"])
            require(inspection == envelope["inspection"], f"Logical inspection drift: {entry['id']}")
        if deep and entry["id"] == "ch3_idrid" and contract["status"] == "ready":
            from scripts.verify_idrid_manual import inspect_idrid, inspection_summary

            require(inspection_summary(inspect_idrid()) == envelope["inspection"], "IDRiD inspection drift")
        if spec["chapter"] == 6:
            require(
                not contract["files"] and contract["status"] == "declared",
                "Ch6 must be an unmaterialized parent view at Phase23",
            )
        if spec["dataset_id"] == "ch1_imagenet_history":
            require(
                contract["kind"] == "metadata" and contract["logical_size"]["records"] == 1,
                "ImageNet must stay metadata only",
            )
        if contract["status"] == "pending_user_download":
            require(entry["id"] == "ch3_idrid" and not contract["files"], "Unexpected source access gate")
    with ThreadPoolExecutor(max_workers=6) as pool:
        errors.extend(failure for failure in pool.map(check_file, files) if failure)
    raw_paths = [row["path"] for row in files if row["path"].startswith("data/raw/")]
    ignored = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        input="\n".join(raw_paths) + "\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    require(set(ignored.stdout.splitlines()) == set(raw_paths), "Some raw files are not ignored")
    spec_lock = read_json(ROOT / "artifacts/manifests/phase22/spec_lock.json")
    errors.extend(failure for failure in map(check_file, spec_lock["files"]) if failure)
    env = read_json(ROOT / "artifacts/manifests/environment.json")
    require(file_digest(ROOT / "uv.lock") == env["uv_lock_sha256"], "Environment lock changed")
    # Hash-only regression of V2 DOCX and sealed TEST; no labels/predictions evaluated.
    v2 = ROOT / "releases/v2/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx"
    require(
        file_digest(v2) == "d7286dd4867e6216f197414e42fc112a3759621c017839fa9b1491b7c5dbfa51",
        "V2 DOCX changed",
    )
    seal = read_json(ROOT / "artifacts/manifests/ch5/phase15_test_run.json")
    require(seal["run_count"] == 1, "Ch5 TEST evaluation count changed")
    for artifact in seal["prediction_artifacts"]:
        path = ROOT / artifact["path"].replace(
            "term_paper/knowledge_rag/artifacts/predictions/phase15/", "artifacts/predictions/ch5/phase15/", 1
        )
        require(file_digest(path) == artifact["sha256"], "Ch5 sealed predictions changed")
    require(not errors, f"Integrity failures: {errors[:10]}")
    lock_path = repo_path(
        ROOT, registry.get("provenance_lock", "artifacts/manifests/phase23/dataset_lock.json")
    )
    provenance_files = provenance_records(registry)
    parent_files = 0
    if "provenance_lock" in registry:
        require(lock_path.is_file(), "Versioned lock must be created by the reviewed import workflow")
        parent_files = check_revision_scope(ROOT, read_json(lock_path)["parent"], provenance_files)
    check_provenance_lock(lock_path, provenance_files, create_lock)
    return {
        "status": "PASS",
        "at": datetime.now(UTC).isoformat(),
        "datasets": len(specs),
        "statuses": dict(statuses),
        "physical_files_hashed": len(raw_paths),
        "raw_bytes": sum(row["size_bytes"] for row in files if row["path"].startswith("data/raw/")),
        "archive_inventories": len(archives),
        "archive_members_hashed": sum(row["members"] for row in archives),
        "all_raw_files_ignored": True,
        "deep_source_inspection": deep,
        "locked_spec_files_unchanged": len(spec_lock["files"]),
        "environment_lock_unchanged": True,
        "locked_provenance_files": len(provenance_files),
        "parent_snapshot_files_verified": parent_files,
        "active_provenance_lock": lock_path.relative_to(ROOT).as_posix(),
        "ch5_sealed_prediction_files_unchanged": len(seal["prediction_artifacts"]),
        "ch5_test_run_count": 1,
        "training_executed": False,
        "test_evaluation_executed": False,
        "deferred_gates": (
            ["IDRiD manual import/license confirmation"] if statuses["pending_user_download"] else []
        )
        + ["Ch6 tasks generated at Phase31, no duplicate raw now"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deep", action="store_true", help="Recompute raw source counts/schema, still no EDA/training"
    )
    parser.add_argument(
        "--lock", action="store_true", help="Create first provenance lock only; never overwrite"
    )
    args = parser.parse_args()
    try:
        result = verify_registry(args.deep, args.lock)
    except (ValueError, OSError, KeyError) as error:
        result = {"status": "FAIL", "error": f"{type(error).__name__}: {error}"}
    path = ROOT / "artifacts/manifests/phase23/verification.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result["status"] != "PASS"


if __name__ == "__main__":
    raise SystemExit(main())
