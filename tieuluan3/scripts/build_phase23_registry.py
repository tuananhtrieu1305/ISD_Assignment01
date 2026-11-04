"""Generate measured dataset contracts/cards from verified raw bytes; never trains."""

from __future__ import annotations

import csv
import gzip
import io
import json
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import yaml

from scripts.verify_idrid_manual import inspect_idrid
from src.common.acquisition import archive_members, file_digest
from src.common.contracts import ROOT, read_json, validate_document
from src.common.source_inspection import inspect_source, require

DESTINATION = ROOT / "artifacts/manifests/datasets"
CARDS = ROOT / "report/references/dataset_cards/v3"
PROTOCOL = ROOT / "experiments/configs/v3/protocol_v3.json"
CATALOG = ROOT / "experiments/configs/v3/acquisition_sources.json"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def physical_file(path):
    require(not path.is_symlink(), f"Symlink not accepted: {path}")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": file_digest(path),
        "size_bytes": path.stat().st_size,
    }


def hash_archive(dataset_id, path):
    if not (zipfile.is_zipfile(path) or path.name.endswith(".tar.gz")):
        return None
    destination = DESTINATION / dataset_id / "archive_members.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    count, expanded = 0, 0
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for row in archive_members(path, max_expanded_bytes=2 * 1024**3):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
            expanded += row["size_bytes"]
            # Bank comes as two nested archives; hash every inner member too.
            if dataset_id == "ch2_bank_marketing" and row["name"].endswith(".zip"):
                with zipfile.ZipFile(path) as outer:
                    nested = io.BytesIO(outer.read(row["name"]))
                for inner in archive_members(nested, max_expanded_bytes=64 * 1024**2):
                    inner["name"] = row["name"] + "!" + inner["name"]
                    handle.write(json.dumps(inner, ensure_ascii=False) + "\n")
                    count += 1
                    expanded += inner["size_bytes"]
    return {**physical_file(destination), "members": count, "expanded_bytes": expanded, "extracted": False}


def protected_ch5_files(name):
    old_prefix = f"term_paper/knowledge_rag/data/raw/{name}/"
    with gzip.open(
        ROOT / "artifacts/manifests/phase20/before-files.csv.gz", "rt", encoding="utf-8-sig", newline=""
    ) as handle:
        baseline = [row for row in csv.DictReader(handle) if row["path"].startswith(old_prefix)]

    def check(row):
        path = ROOT / row["path"].replace("term_paper/knowledge_rag/data/raw/", "data/raw/ch5/", 1)
        measured = physical_file(path)
        require(
            measured["sha256"] == row["sha256"] and measured["size_bytes"] == int(row["bytes"]),
            f"Protected Ch5 bytes changed: {path}",
        )
        return measured

    with ThreadPoolExecutor(max_workers=6) as pool:
        files = list(pool.map(check, baseline))
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / f"data/raw/ch5/{name}").rglob("*")
        if path.is_file()
    }
    require(actual == {row["path"] for row in files}, f"Ch5 unexpected/missing files in {name}")
    return sorted(files, key=lambda row: row["path"])


def ch5_source(spec):
    name = {"ch5_medquad_diabetes": "medquad", "ch5_finqa": "finqa", "ch5_wikidata_subgraphs": "wikidata"}[
        spec["dataset_id"]
    ]
    baseline = read_json(ROOT / "artifacts/manifests/ch5/phase11_snapshot_manifest.json")
    source = baseline["sources"][name]
    files = protected_ch5_files(name)
    if name == "medquad":
        count, nonempty = 0, 0
        for file in files:
            if file["path"].endswith(".xml"):
                tree = ET.parse(ROOT / file["path"])
                pairs = tree.findall(".//QAPair")
                count += len(pairs)
                nonempty += sum(bool((pair.findtext("Answer") or "").strip()) for pair in pairs)
        inspection = {
            "records": count,
            "features": None,
            "unit": "QA pairs in entire preserved upstream corpus, NOT diabetes-only split",
            "columns": [],
            "nonempty_answers": nonempty,
            "historical_diabetes_queries_phase12": 247,
            "deferred": "Phase30 reuses the locked diabetes filter/split; never reconstruct or tune TEST here.",
        }
    elif name == "finqa":
        counts = {
            Path(file["path"]).stem: len(read_json(ROOT / file["path"]))
            for file in files
            if file["path"]
            in {
                f"data/raw/ch5/finqa/dataset/{split}.json"
                for split in ("train", "dev", "test", "private_test")
            }
        }
        require(set(counts) == {"train", "dev", "test", "private_test"}, "FinQA split files missing")
        inspection = {
            "records": sum(counts.values()),
            "features": None,
            "unit": "raw QA records including private_test",
            "columns": [],
            "official_split_counts": counts,
            "deferred": "No evaluation; private/public label policies remain the locked Ch5 protocol.",
        }
    else:
        entities = sorted((ROOT / "data/raw/ch5/wikidata/entities").glob("Q*.json"))
        claims = sum(
            sum(len(v) for v in next(iter(read_json(path)["entities"].values()))["claims"].values())
            for path in entities
        )
        inspection = {
            "records": len(entities),
            "features": None,
            "unit": "narrow entity snapshots, not a QA benchmark",
            "columns": [],
            "claims": claims,
            "checks": ["revision_snapshot_hashes"],
            "deferred": "Structural/provenance audit only; not an invented third QA TEST dataset.",
        }
    inspection.setdefault("checks", []).append("all_raw_files_match_phase20_baseline")
    descriptor = {
        "url": source["official_url"],
        "version": source.get("commit_sha", "Phase11 exact Wikidata revision IDs"),
        "accessed_at": baseline["acquired_at"],
        "citation": {
            "medquad": "Abacha, A. and Demner-Fushman, D. (2019). A question-entailment approach to question answering. BMC Bioinformatics 20:511. MedQuAD.",
            "finqa": "Chen, Z. et al. (2021). FinQA: A Dataset of Numerical Reasoning over Financial Data. EMNLP. https://aclanthology.org/2021.emnlp-main.300/",
            "wikidata": "Wikidata contributors. EntityData snapshots, exact revision IDs in Phase11 snapshot manifest.",
        }[name],
        "license_status": "approved",
        "license_note": source["license"]
        + "; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution.",
    }
    if name == "medquad":
        descriptor["license_note"] += (
            " Some copyrighted upstream answers were removed by MedQuAD; empty answers must not be reconstructed from another source."
        )
    return descriptor, files, inspection


def data_card(contract, inspection, archive):
    source, logical = contract["source"], contract["logical_size"]
    files = contract["files"]
    lines = [
        f"# {contract['dataset_id']} — thẻ nguồn Phase 23",
        "",
        f"- Chương: {contract['chapter']}; loại: `{contract['kind']}`; trạng thái: `{contract['status']}`.",
        f"- Nguồn: {source['url']}",
        f"- Phiên bản: {source['version']}",
        f"- Thời điểm truy cập gốc (UTC): {source['accessed_at']}",
        f"- Trích dẫn: {source['citation']}",
        f"- Giấy phép/quyền truy cập: `{source['license_status']}` — {source['license_note']}",
        f"- Dung lượng vật lý: {sum(row['size_bytes'] for row in files):,} byte / {len(files):,} file; không tính bản giải nén vì không tạo bản giải nén.",
        f"- Kích cỡ logic: {logical['records'] if logical['records'] is not None else 'chưa có'} {logical['unit']}; số đặc trưng nguồn: {logical['features']}.",
        f"- Target theo protocol: `{contract['target']}`.",
        f"- Manifest đầy đủ SHA-256 từng file: `artifacts/manifests/datasets/{contract['dataset_id']}.json`.",
        "",
        "Đây là thẻ phiên bản nguồn, không phải EDA hay kết quả mô hình. Mẫu input/output, phân bố, thiếu dữ liệu, trùng lặp và split/leakage được thực hiện ở Phase 24.",
        "",
    ]
    if archive:
        lines += [
            f"Kiểm tra archive: {archive['members']:,} thành viên, {archive['expanded_bytes']:,} byte nội dung được đọc/hash trực tiếp; không giải nén. Danh sách: `{archive['path']}`.",
            "",
        ]
    if contract["parent_dataset_ids"]:
        lines += [
            "Nguồn cha (tham chiếu, không sao chép raw): " + ", ".join(contract["parent_dataset_ids"]),
            "",
        ]
    lines += [
        "## Kiểm tra và giới hạn",
        "",
        "```json",
        json.dumps(inspection, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    current_path = ROOT / "data/registry.yaml"
    if current_path.exists() and yaml.safe_load(current_path.read_text(encoding="utf-8")).get(
        "provenance_lock"
    ):
        # A sealed revision must not be rewritten by the original all-source builder.
        from scripts.verify_phase23 import verify_registry

        result = verify_registry()
        print("Versioned registry preserved; integrity", result["status"], flush=True)
        return 0
    specs = read_json(PROTOCOL)["datasets"]
    catalog = read_json(CATALOG)["sources"]
    registry, errors = [], []
    CARDS.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        dataset_id = spec["dataset_id"]
        archive = None
        try:
            evidence = "historical_baseline" if spec["chapter"] == 5 else "measured"
            if dataset_id in catalog:
                entry = catalog[dataset_id]
                receipt = read_json(ROOT / f"artifacts/manifests/phase23/receipts/{dataset_id}.json")
                files = [physical_file(ROOT / entry["path"])]
                require(files[0]["sha256"] == receipt["sha256"], "Raw receipt hash mismatch")
                source = {
                    key: entry[key]
                    for key in ("url", "version", "citation", "license_status", "license_note")
                }
                source["accessed_at"] = receipt["accessed_at"]
                source["version"] += "; sha256:" + files[0]["sha256"]
                archive = hash_archive(dataset_id, ROOT / entry["path"])
                inspection = inspect_source(dataset_id, ROOT / entry["path"])
                status = "ready"
            elif dataset_id == "ch3_idrid":
                inspection = inspect_idrid()
                files, status = inspection["files"], inspection["status"]
                source = {
                    "url": "https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid",
                    "version": "IDRiD B. Disease Grading (awaiting user-supplied original release)",
                    "accessed_at": "2026-10-17T01:11:19.634796+00:00",
                    "citation": "Porwal, P. et al. (2018). Indian Diabetic Retinopathy Image Dataset (IDRiD). IEEE DataPort. DOI:10.21227/H25W98.",
                    "license_status": "pending",
                    "license_note": "Manual access/terms confirmation required; user chose to download later. Do not assert a license or invent a local 516-image snapshot.",
                }
                inspection.update(
                    features=None,
                    unit="grading images; published 516 NOT measured until imported",
                    columns=[],
                )
                # A successful manual import still requires recording accepted source terms.
                if status == "ready":
                    source["license_status"] = "pending"
                    status = "declared"
                    inspection["deferred"] = "Record/approve the source license terms before marking ready."
            elif spec["chapter"] == 5:
                source, files, inspection = ch5_source(spec)
                status = "ready"
            else:
                parent = spec["parent_dataset_ids"][0]
                parent_contract = read_json(DESTINATION / f"{parent}.json")["contract"]
                source = {
                    **parent_contract["source"],
                    "version": "Declared task view over pinned parent sources; tasks generated Phase31",
                    "license_note": "Inherits ALL parent source terms; no duplicate raw files and no generated benchmark yet.",
                }
                files, status = [], "declared"
                inspection = {
                    "records": None,
                    "features": None,
                    "unit": "agent task view, not generated yet",
                    "columns": [],
                    "checks": ["parent_ids_match_locked_protocol"],
                    "deferred": "Phase31 creates fixed task families and benchmark; parent TEST seals remain intact.",
                }
            card = f"report/references/dataset_cards/v3/{dataset_id}.md"
            contract = {
                "schema_version": "3.0.0",
                "evidence_kind": evidence,
                "dataset_id": dataset_id,
                "chapter": spec["chapter"],
                "kind": spec["kind"],
                "status": status,
                "source": source,
                "files": files,
                "logical_size": {key: inspection[key] for key in ("records", "features", "unit")},
                "target": spec["target"],
                "columns": inspection["columns"],
                "parent_dataset_ids": spec["parent_dataset_ids"],
                "data_card_path": card,
            }
            validate_document("dataset", contract)
            envelope = {
                "contract": contract,
                "inspection": inspection,
                "archive_inventory": archive,
                "protocol_sha256": file_digest(PROTOCOL),
                "training_executed": False,
                "test_evaluation_executed": False,
            }
            output = DESTINATION / f"{dataset_id}.json"
            write_json(output, envelope)
            (ROOT / card).write_text(data_card(contract, inspection, archive), encoding="utf-8")
            registry.append(
                {
                    "id": dataset_id,
                    "chapter": spec["chapter"],
                    "kind": spec["kind"],
                    "status": status,
                    "source_url": source["url"],
                    "revision": source["version"],
                    "local_path": str(Path(files[0]["path"]).parent.as_posix()) if files else None,
                    "manifest": output.relative_to(ROOT).as_posix(),
                    "manifest_sha256": file_digest(output),
                    "byte_size": sum(row["size_bytes"] for row in files),
                    "logical_size": contract["logical_size"],
                    "parent_dataset_ids": spec["parent_dataset_ids"],
                    "preservation": "locked_v2_preserved" if spec["chapter"] == 5 else None,
                }
            )
            print(dataset_id, status, inspection["records"], inspection["unit"], flush=True)
        except (ValueError, OSError, KeyError, StopIteration, zipfile.BadZipFile) as error:
            errors.append({"dataset_id": dataset_id, "error": f"{type(error).__name__}: {error}"})
            print(errors[-1], flush=True)
    result = {
        "schema_version": "3.0.0",
        "status": "phase23_sources_verified" if not errors else "phase23_incomplete",
        "source_catalog": CATALOG.relative_to(ROOT).as_posix(),
        "source_catalog_sha256": file_digest(CATALOG),
        "policy": "Raw archives retained once; no extraction, no full ImageNet, no Ch5/Ch6 duplication; IDRiD manual deferral explicitly approved by user.",
        "datasets": registry,
    }
    # Incomplete work never replaces a previously complete registry.
    if not errors:
        (ROOT / "data/registry.yaml").write_text(
            yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
    write_json(
        ROOT / "artifacts/manifests/phase23/registry_build.json",
        {
            "at": datetime.now(UTC).isoformat(),
            "datasets": len(registry),
            "errors": errors,
            "status": "FAIL" if errors else "PASS",
        },
    )
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
