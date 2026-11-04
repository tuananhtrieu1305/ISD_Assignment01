"""Read-only result-index overlay, including the authorized recovered TEST metric."""

import copy
import json

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json


def main():
    base = ROOT / "artifacts/manifests/phase32"
    source = base / "registry_v2.json"
    if sha256_file(source) != "66d22f8658822b05a8d25262e4cc53b248a502c16dd368aa6667140a2a980431":
        raise ValueError("Unexpected registry parent")
    document = copy.deepcopy(read_json(source))
    frozen = {}
    for name in ["phase26/revisions/r2", "phase27", "phase29", "phase30", "phase31"]:
        for row in read_json(ROOT / f"artifacts/manifests/{name}/experiment_lock.json")["files"]:
            if row["path"] in frozen and frozen[row["path"]] != row["sha256"]:
                raise ValueError("Conflicting frozen reference")
            frozen[row["path"]] = row["sha256"]
    files = {r["path"]: r for r in document["files"]}

    def add(name):
        path = ROOT / name
        if name not in frozen or sha256_file(path) != frozen[name]:
            raise ValueError("Result not present in parent lock: " + name)
        record = {"path": name, "sha256": frozen[name]}
        files[name] = {**record, "size_bytes": path.stat().st_size}
        identity = "asset_" + record["sha256"][:24]
        document["public_artifacts"][identity] = record
        return {
            "artifact_id": identity,
            **record,
            "size_bytes": path.stat().st_size,
            "content_url": f"/api/v3/artifacts/{identity}/content",
        }

    name = "artifacts/manifests/phase29/revisions/test_schema_r1/orphan/metric.json"
    item = add(name)
    metric = read_json(ROOT / name)
    if any(
        metric["efficiency"][key] is not None
        for key in ["train_seconds", "peak_ram_bytes", "peak_vram_bytes"]
    ):
        raise ValueError("Orphan null training telemetry changed")
    identity = metric["run_id"] + "_test"
    if any(r["run_id"] == identity for r in document["runs"]):
        raise ValueError("Recovered metric already registered")
    document["runs"].append(
        {
            "run_id": identity,
            "original_run_id": metric["run_id"],
            "dataset_id": metric["dataset_id"],
            "chapter": 4,
            "record": {k: item[k] for k in ["path", "sha256"]},
        }
    )
    by_chapter = {2: [], 3: [], 4: [], 5: [], 6: []}
    for name in sorted(frozen):
        if name.startswith("artifacts/metrics/phase26/tables/") and name.endswith((".csv", ".json")):
            by_chapter[2].append(add(name))
        if name.startswith(
            ("artifacts/metrics/phase27/tables/", "artifacts/manifests/phase27/tables/")
        ) and name.endswith((".csv", ".json")):
            by_chapter[3].append(add(name))
    for row in read_json(ROOT / "artifacts/manifests/phase29/report_statistics.json")["tables"]:
        by_chapter[4].append(add(row["path"]))
    for filename in [
        "phase14_metrics.json",
        "phase15_test_metrics.json",
        "phase15_test_metrics.csv",
        "phase15_bootstrap_ci.csv",
        "phase15_error_analysis.csv",
        "phase13_graph_statistics.json",
    ]:
        by_chapter[5].append(add("artifacts/metrics/ch5/" + filename))
    by_chapter[6] = [
        add("artifacts/metrics/phase31/grouped_metrics.json"),
        add("artifacts/metrics/phase31/grouped_metrics.csv"),
    ]
    document["result_indexes"] = {}
    for dataset in document["datasets"]:
        chapter = dataset["chapter"]
        if chapter == 1:
            continue
        document["result_indexes"][dataset["dataset_id"]] = {
            "schema_version": "phase32.result_index.1",
            "dataset_id": dataset["dataset_id"],
            "artifacts": by_chapter[chapter],
            "scope": "Saved historical outputs/tables only; not live inference or a new TEST batch. Shared tables retain dataset/domain/unit/split columns; filter before comparing.",
            "cost_scope": "Original train costs only; recovered RNN Power Torch seed17 train/RAM/VRAM null, quality n3/cost n2. Serving telemetry is separate.",
            "row_filter_hint": {"dataset_id": dataset["dataset_id"]}
            if chapter < 5
            else {
                "domain": "medical"
                if dataset["dataset_id"] == "ch5_medquad_diabetes"
                else "finance"
                if dataset["dataset_id"] == "ch5_finqa"
                else dataset.get("derived_view", {}).get("domain", "structural_only")
            },
            "historical_test_evaluation_executed": False,
        }
    document["files"] = sorted(files.values(), key=lambda r: r["path"])
    document["registry_version"] = "phase32.3"
    write_once(base / "registry_v3.json", document)
    print(
        json.dumps(
            {
                "sha256": sha256_file(base / "registry_v3.json"),
                "files": len(files),
                "runs": len(document["runs"]),
                "bytes": sum(r["size_bytes"] for r in files.values()),
            }
        )
    )


if __name__ == "__main__":
    main()
