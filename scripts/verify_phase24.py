"""Offline acceptance of EDA, train-only preprocessing and immutable split evidence."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from itertools import combinations

import numpy as np
import pandas as pd
from PIL import Image

from scripts.export_phase24_tables import tables_for
from scripts.verify_phase23 import verify_registry
from src.common.acquisition import file_digest, safe_member_name
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.data_v3 import PARTITIONS, audit_partitions, fit_tabular, linked_groups, matched_subset
from src.common.eda_artifacts import BASE, CARDS, FIGURES, read_rows, reference, write_json
from src.common.eda_sources import load_series, load_tabular, source
from src.common.source_inspection import require


def write_lock_once(path, document):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def check_preprocessor(prep, frame, ids):
    expected = fit_tabular(frame, ids)
    require(prep["fit_scope"] == "train_only", "Invalid preprocessing scope")
    for key in ("fit_ids_sha256", "fit_count", "input_columns", "categorical", "output_width"):
        require(prep[key] == expected[key], f"Preprocessing train provenance mismatch: {key}")
    require(set(prep["numeric"]) == set(expected["numeric"]), "Numeric feature schema mismatch")
    for name, values in expected["numeric"].items():
        for key, value in values.items():
            require(
                np.isclose(prep["numeric"][name][key], value, rtol=1e-8, atol=1e-8),
                f"Numeric preprocessing not from train: {name}/{key}",
            )


def audit_window_index(windows, frame, lookback, horizons, cuts):
    require(len({r["id"] for r in windows}) == len(windows), "Duplicate window IDs")
    time_strings = [pd.Timestamp(t).isoformat() for t in frame.time]
    series = frame.series.astype(str).to_numpy()
    targets = frame.target.to_numpy(dtype=float)
    target_sets = {n: set() for n in PARTITIONS}
    for row in windows:
        start, origin, positions = row["start_index"], row["origin_index"], row["target_indices"]
        require(
            0 <= start <= origin < len(frame) and start + lookback - 1 == origin,
            "Wrong window context offsets",
        )
        require(
            positions == [origin + h for h in horizons] and max(positions) < len(frame),
            "Wrong horizon offsets",
        )
        require(all(series[i] == row["series"] for i in [start, origin, *positions]), "Window crossed series")
        require(
            row["context_start"] == time_strings[start] and row["context_end"] == time_strings[origin],
            "Context timestamp does not match source",
        )
        actual = [time_strings[i] for i in positions]
        require(
            actual == row["target_times"] and row["context_end"] < min(actual),
            "Future/context timestamp mismatch",
        )
        require(row["id"] == f"{row['series']}/{time_strings[origin]}", "Window identity mismatch")
        names = {"train" if t <= cuts[0] else "validation" if t <= cuts[1] else "test" for t in actual}
        require(names == {row["partition"]}, "Window targets cross split boundary or wrong partition")
        require(np.isfinite(targets[positions]).all(), "Missing target was imputed or not excluded")
        target_sets[row["partition"]].update(actual)
    overlap = sum(len(target_sets[a] & target_sets[b]) for a, b in combinations(PARTITIONS, 2))
    require(overlap == 0, "Temporal target leakage")
    return {"target_time_overlap_count": overlap, "windows_verified": len(windows)}


def check_reference(record):
    path = ROOT / safe_member_name(record["path"])
    require(
        path.resolve().is_relative_to(ROOT.resolve()) and not path.is_symlink(),
        "Artifact path escaped repository",
    )
    require(
        path.is_file() and file_digest(path) == record["sha256"],
        f"Artifact integrity failure: {record['path']}",
    )
    if "size_bytes" in record:
        require(path.stat().st_size == record["size_bytes"], "Artifact byte size changed")


def verify(create_lock=False):
    protected = verify_registry()
    protocol = read_json(ROOT / "experiments/configs/v3/protocol_v3.json")
    protocol_hash = file_digest(ROOT / "experiments/configs/v3/protocol_v3.json")
    lock_path = BASE / "data_lock.json"
    if lock_path.exists():
        for record in read_json(lock_path)["files"]:
            check_reference(record)
    counts = {}
    split_count, verified_windows = 0, 0
    for spec in protocol["datasets"]:
        dataset = spec["dataset_id"]
        measured = read_json(BASE / dataset / "eda.json")
        require(
            measured["protocol_sha256"] == protocol_hash
            and not measured["training_executed"]
            and not measured["test_evaluation_executed"],
            "EDA scope/protocol drift",
        )
        require(
            measured["source_manifest_sha256"]
            == file_digest(ROOT / f"artifacts/manifests/datasets/{dataset}.json"),
            "Source manifest changed",
        )
        card = (CARDS / f"{dataset}.md").read_text(encoding="utf-8")
        require(
            all(
                title in card
                for title in ("Nguồn", "kích cỡ", "Mẫu input/output", "Phân bố", "Nhận xét", "giới hạn")
            ),
            "Incomplete data card",
        )
        require(bool(measured["samples"]) and bool(measured["comments"]), "Missing examples/comments")
        profile_path = BASE / dataset / "feature_profile.json"
        profile = read_json(profile_path) if profile_path.exists() else None
        for name, expected_rows in tables_for(dataset, measured, profile).items():
            if expected_rows:
                with (BASE / dataset / "tables" / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
                    actual_rows = list(csv.DictReader(stream))
                expected = [{k: "" if v is None else str(v) for k, v in row.items()} for row in expected_rows]
                require(actual_rows == expected, f"CSV table disagrees with EDA: {dataset}/{name}")
        for figure in measured["figures"]:
            check_reference(figure)
            if figure["path"].endswith(".png"):
                with Image.open(ROOT / figure["path"]) as image:
                    require(image.width >= 1000 and image.height >= 700, "Figure resolution too small")
                    image.verify()
        if spec["chapter"] not in (2, 3, 4):
            require(
                not (SPLITS_PATH := ROOT / "data/splits/v3" / dataset).exists(),
                f"Unexpected new split for frozen/deferred/historical scope: {SPLITS_PATH}",
            )
            if spec["chapter"] == 6:
                require(
                    measured["scope"] == "declared_parent_view_NOT_AGENT_BENCHMARK"
                    and measured["size_and_schema"]["agent_tasks"] is None,
                    "Fabricated Ch6 task evidence",
                )
            continue
        directory = ROOT / "data/splits/v3" / dataset
        split = read_json(directory / "split_contract.json")
        validate_document("split", split)
        require(
            split["dataset_sha256"] == measured["source_manifest_sha256"], "Split not tied to source version"
        )
        check_reference(split["leakage_audit"])
        partitions = {}
        for part in split["partitions"]:
            check_reference(part["ids"])
            partitions[part["name"]] = read_rows(ROOT / part["ids"]["path"])
            require(
                len(partitions[part["name"]]) == part["count"] and part["count"] > 0,
                "Partition count mismatch",
            )
        matched = read_rows(directory / "matched_train.ids.jsonl.gz")
        matched_ids = set(matched)
        require(
            set(matched) <= set(partitions["train"]) and len(matched) == len(set(matched)),
            "Matched subset escapes train",
        )
        require(
            len(matched) <= (spec["matched_train_cap"] or len(partitions["train"])), "Subset cap exceeded"
        )
        holdout = read_json(directory / "data_holdout.json")
        require(
            holdout["split_sha256"] == file_digest(directory / "split_contract.json")
            and holdout["evaluation_count"] == 0
            and not holdout["test_evaluation_allowed_now"],
            "Data holdout falsely authorizes TEST",
        )
        rows = read_rows(BASE / dataset / "index.jsonl.gz")
        prep = read_json(BASE / dataset / "preprocessing.json")
        for name in PARTITIONS:
            require(
                {r["id"] for r in rows if r["partition"] == name} == set(partitions[name]),
                "Index partition disagrees with frozen IDs",
            )
        strata = {
            r["id"]: r["series"]
            if spec["chapter"] == 4
            else r["stratum"]
            if spec["chapter"] == 2
            else r["target"]
            for r in rows
        }
        require(
            matched == matched_subset(partitions["train"], strata, spec["matched_train_cap"]),
            "Matched subset SHA ordering/quota changed",
        )
        for sample in measured["samples"]:
            require(sample["id"] in matched_ids, "Displayed sample is outside matched train")
        counts[dataset] = {name: len(partitions[name]) for name in PARTITIONS} | {
            "matched_train": len(matched)
        }
        if spec["chapter"] == 4:
            cache = read_json(BASE / dataset / "series_cache.json")
            original, features, _ = load_series(dataset)
            original = original.sort_values(["series", "time"]).reset_index(drop=True)
            if (ROOT / cache["path"]).is_file():
                check_reference(cache)
                frame = pd.read_csv(ROOT / cache["path"], parse_dates=["time"])
            else:
                frame = original.copy()
            require(
                np.array_equal(
                    frame.time.to_numpy(dtype="datetime64[ns]"),
                    original.time.to_numpy(dtype="datetime64[ns]"),
                )
                and frame.series.astype(str).tolist() == original.series.astype(str).tolist(),
                "Cached calendar/series differ from raw",
            )
            require(
                features == prep["features"]
                and np.allclose(
                    frame[[*features, "target"]],
                    original[[*features, "target"]],
                    rtol=1e-8,
                    atol=1e-8,
                    equal_nan=True,
                ),
                "Cached features/labels differ from raw; missing targets cannot be imputed",
            )
            audit = read_json(BASE / dataset / "leakage_audit.json")
            verified_windows += audit_window_index(
                rows, frame, spec["lookback"], spec["horizons"], audit["calendar_boundaries"]
            )["windows_verified"]
            prefix = frame.time <= pd.Timestamp(audit["calendar_boundaries"][0])
            ids = [f"{s}/{t.isoformat()}" for s, t in zip(frame.series, frame.time, strict=True)]
            check_preprocessor(prep, frame.loc[prefix, prep["features"]], np.asarray(ids)[prefix].tolist())
            require(
                np.isclose(prep["target_transform"]["mean"], frame.loc[prefix, "target"].mean())
                and np.isclose(prep["target_transform"]["std"], frame.loc[prefix, "target"].std(ddof=0)),
                "Temporal target scaling not from train",
            )
            groups = {sid: group for sid, group in frame.groupby("series")}
            origins = {
                sid: {t.isoformat(): i for i, t in enumerate(group.time)} for sid, group in groups.items()
            }
            for fold in read_json(directory / "rolling_folds.json"):
                require(
                    fold["train_end"]
                    < fold["validation_start"]
                    <= fold["validation_end"]
                    <= audit["calendar_boundaries"][1],
                    "Rolling fold reaches final TEST",
                )
                fold_dir = directory / f"rolling_fold_{fold['fold']}"
                mask = frame.time <= pd.Timestamp(fold["train_end"])
                check_preprocessor(
                    read_json(fold_dir / "preprocessing.json"),
                    frame.loc[mask, prep["features"]],
                    np.asarray(ids)[mask].tolist(),
                )
                fold_train = read_rows(fold_dir / "train.ids.jsonl.gz")
                fold_matched_path = fold_dir / "matched_train.ids.jsonl.gz"
                fold_matched = read_rows(fold_matched_path)
                require(
                    file_digest(fold_matched_path) == fold["matched_train_sha256"]
                    and len(fold_matched) == fold["matched_train_count"],
                    "Rolling matched subset checksum/count mismatch",
                )
                require(
                    fold_matched
                    == matched_subset(
                        fold_train,
                        {key: key.split("/", 1)[0] for key in fold_train},
                        spec["matched_train_cap"],
                    ),
                    "Rolling subset not from own fold train",
                )
                for part in ("train", "validation"):
                    fold_ids = read_rows(fold_dir / f"{part}.ids.jsonl.gz")
                    require(len(fold_ids) == fold[part + "_count"], "Rolling fold count mismatch")
                    for key in fold_ids:
                        sid, origin = key.split("/", 1)
                        group = groups[sid]
                        require(origin in origins[sid], "Unknown rolling origin")
                        origin_index = origins[sid][origin]
                        targets = [group.time.iloc[origin_index + h].isoformat() for h in spec["horizons"]]
                        require(
                            np.isfinite(
                                [group.target.iloc[origin_index + h] for h in spec["horizons"]]
                            ).all(),
                            "Missing label in rolling fold",
                        )
                        require(
                            max(targets) <= fold["train_end"]
                            if part == "train"
                            else min(targets) >= fold["validation_start"]
                            and max(targets) <= fold["validation_end"],
                            "Rolling window target crosses fold boundary",
                        )
        else:
            group_map = {row["id"]: row["group"] for row in rows}
            audit_partitions(partitions, group_map)
            require(
                len(group_map) == source(dataset)["contract"]["logical_size"]["records"],
                "Source rows lost from index",
            )
            if spec["chapter"] == 2:
                frame, target, ids, hashes, properties = load_tabular(dataset)
                expected_groups = linked_groups(hashes, properties)
                require(
                    group_map == dict(zip(ids, map(str, expected_groups), strict=True)),
                    "Feature/property linkage drift",
                )
                require(
                    not set(spec["exclude_features"]) & set(prep["input_columns"]),
                    "Excluded feature reappeared",
                )
                check_preprocessor(prep, frame.loc[np.isin(ids, matched)], matched)
                train_target = target[np.isin(ids, matched)]
                if spec["task"] == "regression":
                    require(
                        np.isclose(prep["target_transform"]["mean"], train_target.mean())
                        and np.isclose(prep["target_transform"]["std"], train_target.std(ddof=0)),
                        "Target scaling not fitted to matched train",
                    )
                else:
                    weights = train_target.astype(str).value_counts().to_dict()
                    expected = {k: len(matched) / (len(weights) * v) for k, v in weights.items()}
                    require(prep["class_weights"] == expected, "Class weights not fitted to matched train")
            else:
                expected_groups = linked_groups(
                    [row["pixel_sha256"] for row in rows], [row["model_pixel_sha256"] for row in rows]
                )
                require(
                    list(map(str, expected_groups)) == [row["group"] for row in rows], "Pixel linkage drift"
                )
                if "official" in spec["split_method"]:
                    require(
                        set(partitions["test"]) == {r["id"] for r in rows if r["official_split"] == "test"},
                        "Official TEST changed",
                    )
                require(
                    prep["fit_ids_sha256"] == canonical_sha256(matched),
                    "Image class weights not tied to train",
                )
                support = (
                    pd.Series([r["target"] for r in rows if r["id"] in matched_ids]).value_counts().to_dict()
                )
                require(
                    prep["class_weights"]
                    == {k: len(matched) / (len(support) * v) for k, v in support.items()},
                    "Image class weights do not match train labels",
                )
        split_count += 1
    # Lock stable derived artifacts/code only. Mutable checkpoints/test logs remain separate.
    paths = []
    for spec in protocol["datasets"]:
        dataset = spec["dataset_id"]
        paths += [p for p in (BASE / dataset).rglob("*") if p.is_file()]
        paths += [CARDS / f"{dataset}.md"]
        paths += [p for p in (ROOT / "data/splits/v3" / dataset).rglob("*") if p.is_file()]
    paths += [ROOT / "data/catalog_v3.json", BASE / "memory_plan.json"]
    catalog = read_json(ROOT / "data/catalog_v3.json")
    require(
        {r["dataset_id"] for r in catalog["datasets"]} == {s["dataset_id"] for s in protocol["datasets"]},
        "Incomplete EDA catalog",
    )
    for row in catalog["datasets"]:
        for key in ("source_manifest", "eda", "data_card", "split", "preprocessing"):
            if row[key] is not None:
                check_reference(row[key])
    paths += [p for p in FIGURES.glob("*") if p.is_file()]
    paths += [
        ROOT / name
        for name in (
            "src/common/data_v3.py",
            "src/common/eda_sources.py",
            "src/common/eda_artifacts.py",
            "scripts/prepare_phase24.py",
            "scripts/verify_phase24.py",
            "scripts/phase24_reproducibility.py",
            "scripts/export_phase24_tables.py",
        )
    ]
    paths += list((ROOT / "tests/data").glob("test_phase24_*.py"))
    records = [reference(path) for path in sorted(set(paths))]
    if lock_path.exists():
        require(
            read_json(lock_path)["files"] == records,
            "Phase24 artifact set changed; use a versioned revision, never overwrite",
        )
    elif create_lock:
        write_lock_once(
            lock_path,
            {
                "schema_version": "3.0.0",
                "phase": 24,
                "files": records,
                "protocol_sha256": protocol_hash,
                "phase23_lock": reference(ROOT / protected["active_provenance_lock"]),
                "test_evaluation_executed": False,
            },
        )
    return {
        "status": "PASS",
        "at": datetime.now(UTC).isoformat(),
        "cards": 18,
        "new_split_contracts": split_count,
        "split_counts": counts,
        "temporal_windows_verified": verified_windows,
        "stable_artifacts": len(records),
        "phase24_lock_created": lock_path.exists(),
        "phase23_provenance_files_unchanged": protected["locked_provenance_files"],
        "phase23_parent_snapshot_files_verified": protected["parent_snapshot_files_verified"],
        "phase22_spec_files_unchanged": protected["locked_spec_files_unchanged"],
        "ch5_test_run_count": protected["ch5_test_run_count"],
        "training_executed": False,
        "test_evaluation_executed": False,
        "ch6_task_benchmarks_deferred_to_phase31": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.lock)
    except (ValueError, OSError, KeyError, IndexError) as error:
        result = {"status": "FAIL", "error": f"{type(error).__name__}: {error}"}
    write_json(BASE / "verification.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result["status"] != "PASS"


if __name__ == "__main__":
    raise SystemExit(main())
