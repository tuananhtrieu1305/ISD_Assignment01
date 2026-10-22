"""Reviewed IDRiD manual-import revision. Keep the initial Phase23 lock immutable."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import yaml

from scripts.build_phase23_registry import data_card, hash_archive, write_json
from scripts.verify_idrid_manual import inspect_idrid, inspection_summary
from scripts.verify_phase23 import provenance_records, verify_registry
from src.common.acquisition import file_digest
from src.common.contracts import ROOT, read_json, validate_document
from src.common.provenance import check_revision_scope, preserve_snapshot
from src.common.source_inspection import require


def check_rename_evidence(original, current):
    """Accept only a single outer filename change with identical archive bytes."""
    require(len(original) == len(current) == 1, "Expected exactly one original ZIP")
    require(
        all(original[0][key] == current[0][key] for key in ("size_bytes", "sha256")),
        "Outer filename normalization must not change ZIP bytes",
    )


def main():
    registry_path = ROOT / "data/registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if registry.get("provenance_revision", "").startswith("idrid_"):
        result = verify_registry(deep=True)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "action": "reused_existing_IDRiD_revision",
                    "lock": registry["provenance_lock"],
                },
                indent=2,
            )
        )
        return 0
    # Old evidence must still pass before a permitted, scoped update is created.
    verify_registry()
    measured = inspect_idrid()
    require(
        measured["status"] == "ready" and measured["license_status"] == "approved",
        "Need complete grading images/labels and bundled license evidence before importing",
    )
    require(
        len(measured["files"]) == 1 and measured["files"][0]["path"].lower().endswith(".zip"),
        "This reviewed import accepts one original Disease Grading ZIP; no repacked/extracted duplicates",
    )
    raw = measured["files"][0]
    revision = "idrid_20261017_" + raw["sha256"][:12]
    directory = ROOT / "artifacts/manifests/phase23/updates" / revision
    directory.mkdir(parents=True, exist_ok=True)
    old_lock = ROOT / "artifacts/manifests/phase23/dataset_lock.json"
    parent = preserve_snapshot(ROOT, old_lock, "artifacts/manifests/phase23/snapshots/pre_idrid_v1")
    receipt_path = directory / "import_receipt.json"
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        check_rename_evidence(receipt["raw_files"], measured["files"])
    else:
        receipt = {
            "schema_version": "3.0.0",
            "at": datetime.now(UTC).isoformat(),
            "acquisition_mode": "user_downloaded_original_official_ZIP",
            "raw_files": measured["files"],
            "source_url": "https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid",
            "license_identifier": "CC-BY-4.0",
            "license_evidence": measured["license_evidence"],
            "official_split_counts": measured["official_split_counts"],
            "authorization": "User requested 'đã tải IDRiD, cập nhật Phase 23'; only IDRiD acquisition state is changed",
            "upstream_checksum_available": False,
            "note": "Timestamp is local import time, not an asserted browser download time. SHA-256 pins supplied bytes; no claim of publisher checksum verification.",
        }
        write_json(receipt_path, receipt)
    receipt_paths = [receipt_path.relative_to(ROOT).as_posix()]
    if receipt["raw_files"] != measured["files"]:
        # Preserve the initial supplied-name receipt, including an interrupted import.
        canonical_path = directory / "canonical_import_receipt.json"
        canonical = {
            **receipt,
            "raw_files": measured["files"],
            "original_supplied_files": receipt["raw_files"],
            "original_receipt_sha256": file_digest(receipt_path),
            "normalization": "Outer ZIP filename only, to satisfy locked Phase22 path schema; archive bytes and internal names unchanged",
        }
        if canonical_path.exists():
            require(read_json(canonical_path) == canonical, "Canonical receipt changed; never overwrite")
        else:
            write_json(canonical_path, canonical)
        receipt = canonical
        receipt_paths.append(canonical_path.relative_to(ROOT).as_posix())
    index_path = directory / "image_index.json"
    write_json(
        index_path,
        {
            "schema_version": "3.0.0",
            "identity_policy": measured["identity_policy"],
            "labels": measured["labels"],
            "image_members": measured["image_members"],
        },
    )
    archive = hash_archive("ch3_idrid", ROOT / raw["path"])
    summary = inspection_summary(measured)
    card_path = "report/references/dataset_cards/v3/ch3_idrid.md"
    source = {
        "url": receipt["source_url"],
        "version": "IDRiD original B. Disease Grading ZIP; sha256:" + raw["sha256"],
        "accessed_at": receipt["at"],
        "citation": "Porwal, P., Pachade, S., and Kokare, M. (2018). Indian Diabetic Retinopathy Image Dataset (IDRiD). IEEE DataPort. DOI:10.21227/H25W98.",
        "license_status": "approved",
        "license_note": "CC BY 4.0, established from bundled IDRiD LICENSE.txt and CC-BY-4.0.txt; exact member hashes in import receipt. Retain authors/citation/license, identify adaptations; no clinical-use claims.",
    }
    contract = {
        "schema_version": "3.0.0",
        "evidence_kind": "measured",
        "dataset_id": "ch3_idrid",
        "chapter": 3,
        "kind": "image",
        "status": "ready",
        "source": source,
        "files": measured["files"],
        "logical_size": {key: summary[key] for key in ("records", "features", "unit")},
        "target": "dr_grade",
        "columns": summary["columns"],
        "parent_dataset_ids": [],
        "data_card_path": card_path,
    }
    validate_document("dataset", contract)
    envelope = {
        "contract": contract,
        "inspection": summary,
        "archive_inventory": archive,
        "protocol_sha256": file_digest(ROOT / "experiments/configs/v3/protocol_v3.json"),
        "training_executed": False,
        "test_evaluation_executed": False,
    }
    manifest_path = ROOT / "artifacts/manifests/datasets/ch3_idrid.json"
    write_json(manifest_path, envelope)
    (ROOT / card_path).write_text(data_card(contract, summary, archive), encoding="utf-8")
    entry = next(row for row in registry["datasets"] if row["id"] == "ch3_idrid")
    entry.update(
        status="ready",
        source_url=source["url"],
        revision=source["version"],
        local_path="data/raw/ch3/idrid/manual",
        manifest_sha256=file_digest(manifest_path),
        byte_size=raw["size_bytes"],
        logical_size=contract["logical_size"],
    )
    new_lock = directory / "dataset_lock.json"
    registry.update(
        provenance_revision=revision,
        provenance_lock=new_lock.relative_to(ROOT).as_posix(),
        provenance_evidence_paths=[
            *receipt_paths,
            index_path.relative_to(ROOT).as_posix(),
        ],
        policy="All physical sources verified, including user-provided IDRiD original grading ZIP. Archives remain unextracted; Ch5/Ch6 raw not duplicated. Initial Phase23 metadata snapshot and lock preserved.",
    )
    registry_path.write_text(yaml.safe_dump(registry, allow_unicode=True, sort_keys=False), encoding="utf-8")
    files = provenance_records(registry)
    check_revision_scope(ROOT, parent, files)
    document = {
        "schema_version": "3.0.0",
        "at": receipt["at"],
        "revision": revision,
        "parent": parent,
        "change_scope": "IDRiD manual import only; other 17 registry entries and unrelated evidence unchanged",
        "files": files,
    }
    if new_lock.exists():
        require(
            read_json(new_lock) == document, "Revision lock exists with different content; never overwrite"
        )
    else:
        with new_lock.open("x", encoding="utf-8") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    write_json(
        directory / "import_result.json",
        {
            "status": "PASS",
            "revision": revision,
            "records": 516,
            "official_split_counts": measured["official_split_counts"],
            "license": "CC-BY-4.0",
            "old_lock_sha256": parent["sha256"],
            "new_lock": registry["provenance_lock"],
            "locked_files": len(files),
            "training_executed": False,
            "test_evaluation_executed": False,
        },
    )
    print(json.dumps(read_json(directory / "import_result.json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
