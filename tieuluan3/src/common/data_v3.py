"""Deterministic data policy shared by V3 EDA and later framework adapters.

No framework, autograd, model fitting or TEST evaluation is used here.
"""

from __future__ import annotations

import hashlib
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.common.contracts import canonical_sha256
from src.common.source_inspection import require

PARTITIONS = ("train", "validation", "test")


def linked_groups(hashes, property_ids=None):
    """Union exact-feature/pixel identities and verified property IDs transitively."""
    parent = list(range(len(hashes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for keys in (hashes, property_ids if property_ids is not None else []):
        seen = {}
        for i, key in enumerate(keys):
            if key is None or pd.isna(key) or str(key).strip() == "":
                continue
            if key in seen:
                left, right = find(i), find(seen[key])
                parent[max(left, right)] = min(left, right)
            else:
                seen[key] = i
    return [find(i) for i in range(len(hashes))]


def _divide(groups, fraction, seed):
    require(len(groups) >= 4, "Insufficient independent groups for a three-way split")
    keys = sorted(groups)
    labels = [groups[key] for key in keys]
    counts = pd.Series(labels).value_counts()
    size = int(np.ceil(len(keys) * fraction))
    stratify = labels if counts.min() >= 2 and min(size, len(keys) - size) >= len(counts) else None
    return train_test_split(keys, test_size=fraction, random_state=seed, stratify=stratify)


def _group_strata(frame):
    counts = frame.groupby(["group", "label"]).size().rename("count").reset_index()
    majority = counts.sort_values(["group", "count", "label"], ascending=[True, False, True])
    return majority.drop_duplicates("group").set_index("group").label.to_dict()


def grouped_split(ids, groups, labels, *, official_test=None, validation_fraction=0.15, seed=42):
    """Split group units, keeping official TEST intact and quarantining dev duplicates.

    Stratification uses the majority stratum of each group (not label for linkage).
    Conflicting targets never break an exact-feature identity into separate groups.
    """
    require(len(ids) == len(set(ids)) == len(groups) == len(labels), "Nonunique IDs or length mismatch")
    frame = pd.DataFrame({"id": ids, "group": list(map(str, groups)), "label": list(map(str, labels))})
    quarantine = []
    if official_test is not None:
        test = sorted(official_test)
        require(set(test) <= set(ids), "Unknown official TEST ID")
        test_groups = set(frame.loc[frame.id.isin(test), "group"])
        quarantine = sorted(frame.loc[~frame.id.isin(test) & frame.group.isin(test_groups), "id"])
        eligible = frame.loc[~frame.id.isin(test + quarantine)]
        strata = _group_strata(eligible)
        train_groups, val_groups = _divide(strata, validation_fraction, seed)
    else:
        eligible = frame
        strata = _group_strata(frame)
        train_groups, remaining = _divide(strata, 0.3, seed)
        val_groups, test_groups = _divide({key: strata[key] for key in remaining}, 0.5, seed)
        test = sorted(frame.loc[frame.group.isin(test_groups), "id"])
    result = {
        "train": sorted(eligible.loc[eligible.group.isin(train_groups), "id"]),
        "validation": sorted(eligible.loc[eligible.group.isin(val_groups), "id"]),
        "test": test,
        "quarantine": quarantine,
    }
    audit_partitions(result, dict(zip(ids, map(str, groups), strict=True)))
    require(sum(map(len, result.values())) == len(ids), "Some source records were lost")
    return result


def audit_partitions(partitions, groups):
    ids = {name: set(partitions[name]) for name in PARTITIONS}
    require(all(len(ids[n]) == len(partitions[n]) for n in PARTITIONS), "Duplicate IDs inside partition")
    identity_overlap = sum(len(ids[a] & ids[b]) for a, b in combinations(PARTITIONS, 2))
    units = {name: {groups[key] for key in ids[name]} for name in PARTITIONS}
    group_overlap = sum(len(units[a] & units[b]) for a, b in combinations(PARTITIONS, 2))
    require(identity_overlap == group_overlap == 0, "ID/group leakage across partitions")
    return {"id_overlap_count": identity_overlap, "group_overlap_count": group_overlap}


def matched_subset(ids, strata, cap, seed=42):
    """Stable seeded SHA ordering within strata, proportional largest-remainder quota."""
    ids = sorted(ids)
    if cap is None or len(ids) <= cap:
        return ids
    require(cap > 0, "Subset cap must be positive")
    buckets = {}
    for key in ids:
        buckets.setdefault(str(strata[key]), []).append(key)
    ideal = {label: cap * len(keys) / len(ids) for label, keys in buckets.items()}
    quotas = {label: int(value) for label, value in ideal.items()}
    for label in sorted(buckets, key=lambda s: (-(ideal[s] - quotas[s]), s))[: cap - sum(quotas.values())]:
        quotas[label] += 1
    result = []
    for label, keys in sorted(buckets.items()):
        keys.sort(key=lambda key: hashlib.sha256(f"{seed}:{label}:{key}".encode()).hexdigest())
        result.extend(keys[: quotas[label]])
    return sorted(result)


def fit_tabular(frame, fit_ids):
    """Fit medians, standardization and category vocabularies only to supplied train."""
    require(len(frame) > 0 and len(frame) == len(fit_ids), "Empty train or fit-ID mismatch")
    numeric, categorical = {}, {}
    for name in frame:
        column = frame[name]
        if pd.api.types.is_numeric_dtype(column):
            values = pd.to_numeric(column).replace([np.inf, -np.inf], np.nan)
            median = float(values.median()) if values.notna().any() else 0.0
            values = values.fillna(median)
            std = float(values.std(ddof=0))
            numeric[name] = {
                "median": median,
                "mean": float(values.mean()),
                "std": std if std > 0 else 1.0,
                "all_missing_fallback": bool(column.isna().all()),
            }
        else:
            categorical[name] = sorted(column.fillna("__missing__").astype(str).unique().tolist())
    return {
        "schema_version": "3.0.0",
        "fit_scope": "train_only",
        "fit_ids_sha256": canonical_sha256(sorted(fit_ids)),
        "fit_count": len(fit_ids),
        "input_columns": list(frame.columns),
        "numeric": numeric,
        "categorical": categorical,
        "unknown_category": "all_zero_one_hot",
        "output_dtype": "float32",
        "output_width": len(numeric) + sum(map(len, categorical.values())),
    }


def transform_tabular(frame, contract):
    require(set(frame.columns) == set(contract["input_columns"]), "Feature schema mismatch")
    columns = []
    for name, rule in contract["numeric"].items():
        values = pd.to_numeric(frame[name]).replace([np.inf, -np.inf], np.nan).fillna(rule["median"])
        columns.append(((values - rule["mean"]) / rule["std"]).to_numpy(dtype=np.float32)[:, None])
    for name, categories in contract["categorical"].items():
        values = frame[name].fillna("__missing__").astype(str).to_numpy()
        columns.append((values[:, None] == np.asarray(categories)[None, :]).astype(np.float32))
    result = np.concatenate(columns, axis=1)
    require(np.isfinite(result).all(), "Nonfinite transformed input")
    return result


def temporal_boundaries(times):
    times = sorted({pd.Timestamp(t).isoformat() for t in times})
    require(len(times) >= 20, "Insufficient time points")
    return [times[int(len(times) * fraction) - 1] for fraction in (0.7, 0.85)]


def rolling_folds(times, pretest_end):
    times = sorted({pd.Timestamp(t).isoformat() for t in times if pd.Timestamp(t).isoformat() <= pretest_end})
    require(len(times) >= 20, "Insufficient pre-TEST times for rolling folds")
    stops = [int(len(times) * fraction) for fraction in (0.55, 0.7, 0.85, 1.0)]
    return [
        {
            "fold": i + 1,
            "train_end": times[stops[i] - 1],
            "validation_start": times[stops[i]],
            "validation_end": times[stops[i + 1] - 1],
            "preprocessing_fit_scope": "own_fold_train_prefix_only",
        }
        for i in range(3)
    ]


def causal_windows(frame, features, lookback, horizons, cuts):
    """Emit IDs/index ranges, not duplicated tensors. Never fill missing target labels."""
    require(not frame.duplicated(["series", "time"]).any(), "Duplicate series/time")
    windows = []
    excluded = {"cross_boundary": 0, "missing_target": 0, "unresolved_input": 0}
    for series, group in frame.groupby("series", sort=True):
        group = group.sort_values("time")
        times = pd.DatetimeIndex(group.time)
        frequency = pd.infer_freq(times)
        require(frequency is not None, f"Series {series} has missing calendar periods")
        target = group.target.to_numpy(dtype=float)
        values = group[features].to_numpy(dtype=float)
        indices = group.index.to_numpy()
        for origin in range(lookback - 1, len(group) - max(horizons)):
            positions = [origin + h for h in horizons]
            target_times = [times[j].isoformat() for j in positions]
            partitions = [
                "train" if t <= cuts[0] else "validation" if t <= cuts[1] else "test" for t in target_times
            ]
            if len(set(partitions)) != 1:
                excluded["cross_boundary"] += 1
                continue
            if not np.isfinite(target[positions]).all():
                excluded["missing_target"] += 1
                continue
            if not np.isfinite(values[origin - lookback + 1 : origin + 1]).all():
                excluded["unresolved_input"] += 1
                continue
            windows.append(
                {
                    "id": f"{series}/{times[origin].isoformat()}",
                    "series": str(series),
                    "partition": partitions[0],
                    "context_start": times[origin - lookback + 1].isoformat(),
                    "context_end": times[origin].isoformat(),
                    "target_times": target_times,
                    "start_index": int(indices[origin - lookback + 1]),
                    "origin_index": int(indices[origin]),
                    "target_indices": [int(indices[j]) for j in positions],
                }
            )
    return windows, excluded
