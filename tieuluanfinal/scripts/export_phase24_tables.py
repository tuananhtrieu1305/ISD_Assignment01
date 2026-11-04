"""Flat CSV intermediates for the report/UI, generated from measured EDA only."""

import csv

from src.common.contracts import ROOT, read_json
from src.common.eda_artifacts import BASE


def tables_for(dataset, measured, profile):
    size = measured["size_and_schema"]
    summary = {
        "dataset_id": dataset,
        "scope": measured["scope"],
        "rows": size.get("rows", size.get("images", size.get("canonical_time_rows", size.get("records")))),
        "train": size.get("counts", {}).get("train"),
        "validation": size.get("counts", {}).get("validation"),
        "test": size.get("counts", {}).get("test"),
        "matched_train": size.get("matched_train_count"),
        "quarantine": size.get("quarantine_count"),
        "windows": size.get("valid_windows"),
        "agent_tasks": size.get("agent_tasks"),
    }
    tables = {"summary": [summary], "target_distribution": [], "missing": [], "numeric": [], "categories": []}
    if profile:
        for name, count in profile["missing"].items():
            tables["missing"].append(
                {
                    "feature": name,
                    "missing_count": count,
                    "source_rows": profile["records"],
                    "missing_fraction": count / profile["records"],
                }
            )
        for name, values in profile["numeric"].items():
            tables["numeric"].append({"feature": name, **values})
        for name, values in profile["categories"].items():
            for category, count in sorted(values.items()):
                tables["categories"].append({"feature": name, "category": category, "source_count": count})
    distribution = measured["distribution_summary"]
    by_partition = distribution.get("target_by_partition", distribution.get("class_by_partition"))
    if by_partition:
        for partition, values in sorted(by_partition.items()):
            for key, value in sorted(values.items()):
                tables["target_distribution"].append(
                    {"partition": partition, "category_or_statistic": key, "value": value}
                )
    else:
        values = distribution.get("target_observed_summary", distribution)
        for key, value in sorted(values.items()):
            if isinstance(value, (int, float)):
                tables["target_distribution"].append(
                    {"partition": "source_or_frozen_baseline", "category_or_statistic": key, "value": value}
                )
    return tables


def main():
    if (BASE / "data_lock.json").exists():
        from scripts.verify_phase24 import verify

        print(verify()["status"])
        return 0
    catalog = read_json(ROOT / "data/catalog_v3.json")
    count = 0
    for item in catalog["datasets"]:
        dataset = item["dataset_id"]
        measured = read_json(BASE / dataset / "eda.json")
        profile_path = BASE / dataset / "feature_profile.json"
        profile = read_json(profile_path) if profile_path.exists() else None
        for name, rows in tables_for(dataset, measured, profile).items():
            if not rows:
                continue
            path = BASE / dataset / "tables" / f"{name}.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            count += 1
    print(f"Exported {count} CSV EDA tables; blank means unavailable, never a fabricated zero", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
