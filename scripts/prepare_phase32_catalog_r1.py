"""Serving-only catalog overlay; keep registry_v1 and Phase23 manifests unchanged."""

import copy
import json

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json, validate_document


def main():
    base = ROOT / "artifacts/manifests/phase32"
    source = base / "registry_v1.json"
    if sha256_file(source) != "63df52932bd1f9cd0c35ce2e850b0cb147952642b54bcd87bdbe8d82eea5a5e8":
        raise ValueError("Unexpected v1 registry")
    document = copy.deepcopy(read_json(source))
    for row in document["datasets"]:
        if row["chapter"] != 6:
            continue
        original = read_json(ROOT / row["source_manifest"]["path"])["contract"]
        contract = copy.deepcopy(original)
        view = row["derived_view"]
        taskset = view["taskset"]
        contract.update(
            status="ready",
            logical_size={
                "records": view["tasks"],
                "features": None,
                "unit": "synthetic-template task per domain over real parent TRAIN tool/evidence records",
            },
            files=[{**taskset, "size_bytes": (ROOT / taskset["path"]).stat().st_size}],
            data_card_path=row["data_card"]["path"],
        )
        contract["source"].update(
            version="Phase31 taskset_v2; sha256:" + taskset["sha256"],
            license_note="Derived task view inherits all parent source terms; templates/OOD/unsafe/fault questions are synthetic, numeric/evidence inputs are frozen parent TRAIN records. Not new clinical/financial truth labels.",
        )
        validate_document("dataset", contract)
        path = base / "catalog_r1" / (row["dataset_id"] + ".json")
        write_once(
            path,
            {
                "contract": contract,
                "parent_declared_manifest": row["source_manifest"],
                "source_phase": 31,
                "historical_test_evaluation_executed": False,
            },
        )
        record = {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}
        row["source_manifest_original"] = row["source_manifest"]
        row["source_manifest"] = record
        document["files"].append({**record, "size_bytes": path.stat().st_size})
        document["public_artifacts"]["asset_" + record["sha256"][:24]] = record
    document["registry_version"] = "phase32.2"
    document["files"].sort(key=lambda r: r["path"])
    write_once(base / "registry_v2.json", document)
    print(
        json.dumps(
            {
                "sha256": sha256_file(base / "registry_v2.json"),
                "files": len(document["files"]),
                "bytes": sum(r["size_bytes"] for r in document["files"]),
            }
        )
    )


if __name__ == "__main__":
    main()
