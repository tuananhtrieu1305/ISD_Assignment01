"""Verify partition/subset IDs and fitted states survive EDA QA regeneration."""

import argparse

from src.common.contracts import ROOT, read_json
from src.common.eda_artifacts import BASE, reference, write_json
from src.common.source_inspection import require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    snapshot = BASE / "reproducibility_before.json"
    if args.capture:
        require(not snapshot.exists(), "Keep the original reproducibility snapshot; never overwrite")
        paths = list((ROOT / "data/splits/v3").rglob("*.ids.jsonl.gz"))
        paths += list((ROOT / "data/splits/v3").rglob("preprocessing.json"))
        for dataset in read_json(ROOT / "experiments/configs/v3/protocol_v3.json")["datasets"]:
            if dataset["chapter"] in (2, 4):
                paths.append(BASE / dataset["dataset_id"] / "preprocessing.json")
            if dataset["chapter"] == 4:
                paths.append(ROOT / read_json(BASE / dataset["dataset_id"] / "series_cache.json")["path"])
        write_json(
            snapshot,
            {
                "scope": "Existing partition/subset IDs, fitted numeric states and canonical caches before plot/metadata QA refinements; new fold-subset files may be added",
                "files": [reference(p) for p in sorted(set(paths))],
            },
        )
        print(f"Captured {len(set(paths))} immutable data decisions", flush=True)
        return 0
    records = read_json(snapshot)["files"]
    for record in records:
        require(
            reference(ROOT / record["path"]) == record, f"Data decision changed during QA: {record['path']}"
        )
    write_json(
        BASE / "reproducibility.json",
        {
            "status": "PASS",
            "unchanged_files": len(records),
            "snapshot_sha256": reference(snapshot)["sha256"],
            "training_executed": False,
            "test_evaluation_executed": False,
            "scope": "Regeneration preserved every captured partition/subset ID hash, fitted state and canonical cache; plots/metadata refined before first Phase24 lock",
        },
    )
    print(f"PASS: {len(records)} data decision artifacts unchanged", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
