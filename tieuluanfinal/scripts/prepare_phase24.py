"""Measure EDA and freeze data-only contracts. No model, tuning or TEST evaluation.

Run through scripts/run_experiment.ps1. Sources/spec/Phase23 cards are read-only.
Derived artifacts live in Phase24/v3_eda/v3 split directories, never overwrite a lock.
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
import zipfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.acquisition import file_digest
from src.common.contracts import ROOT, canonical_sha256, read_json, validate_document
from src.common.data_v3 import (
    PARTITIONS,
    audit_partitions,
    causal_windows,
    fit_tabular,
    grouped_split,
    linked_groups,
    matched_subset,
    rolling_folds,
    temporal_boundaries,
    transform_tabular,
)
from src.common.eda_artifacts import (
    BASE,
    clean,
    describe_frame,
    distribution_figure,
    reference,
    render_card,
    save_figure,
    write_json,
    write_rows,
)
from src.common.eda_sources import image_for_row, load_images, load_series, load_tabular, source
from src.common.source_inspection import require

PROTOCOL_PATH = ROOT / "experiments/configs/v3/protocol_v3.json"
PROTOCOL = read_json(PROTOCOL_PATH)
SPECS = {row["dataset_id"]: row for row in PROTOCOL["datasets"]}
SPLITS = ROOT / "data/splits/v3"

COMMENTS = {
    "ch2_cdc_diabetes": [
        "CDC bản nhị phân: 1 gộp tiền tiểu đường/tiểu đường, không diễn giải thành ba lớp.",
        "Khảo sát tự báo cáo, quan sát chứ không chứng minh quan hệ nhân quả; không dùng để chẩn đoán.",
        "Không có patient ID được xác minh. Gom trùng feature không chứng minh độc lập bệnh nhân.",
    ],
    "ch2_ames_housing": [
        "Giá bán tính bằng USD; thiếu ở một số trường có thể biểu thị không có tiện ích, không mặc định bằng 0.",
        "PID/Order không làm feature. Gom PID và trùng feature theo liên kết bắc cầu.",
        "Chia theo nhóm/ngẫu nhiên không đại diện cho triển khai dự báo giá nhà tương lai hay địa phương khác.",
    ],
    "ch2_bank_marketing": [
        "Bỏ duration vì chỉ biết sau cuộc gọi; giữ nhãn y: yes=1, no=0.",
        "Chuỗi 'unknown' là mức danh mục nguồn, không tự coi là số 0.",
        "Không có mã khách hàng để bảo đảm độc lập theo khách; giữ hạn chế này.",
    ],
    "ch3_idrid": [
        "Dữ liệu nhỏ và mất cân bằng; nhãn DR grade không phải chẩn đoán cho người dùng.",
        "Giảm về 128×128 cho track so sánh đã khóa có thể mất chi tiết tổn thương.",
        "ID gồm split/basename. Không có patient key xác minh; chỉ bảo đảm không trùng pixel giữa tập.",
    ],
    "ch3_eurosat": [
        "Ảnh RGB 64×64 gốc, track so sánh dùng 32×32 như protocol.",
        "Không có tọa độ/group địa lý được xác minh trong gói này; split không chứng minh độc lập không gian.",
        "Kiểm trùng pixel gốc và sau resize, không tự lọc ảnh theo kết quả mô hình.",
    ],
    "ch3_cifar10": [
        "Giữ nguyên 10.000 ảnh official TEST, kể cả bản trùng trong chính TEST.",
        "Ảnh official train trùng pixel với TEST phải quarantine, không được âm thầm chuyển/xóa TEST.",
        "Đọc binary, không dùng pickle; test chỉ được đánh giá sau khi khóa release thí nghiệm.",
    ],
    "ch4_gold_pink_sheet": [
        "Giá vàng USD/troy ounce; silver/platinum/crude oil giữ đơn vị nguồn và trễ một tháng.",
        "Snapshot đã chỉnh sửa hồi tố, không phải mô phỏng dữ liệu sẵn có theo vintage tại thời điểm thật.",
        "Chuỗi tháng ít mẫu; không tuyên bố khả năng giao dịch hoặc khuyến nghị đầu tư.",
    ],
    "ch4_bis_house_prices": [
        "Chỉ VALUE=N và UNIT_MEASURE=628, chỉ số danh nghĩa 2010=100, không trộn Real/YoY.",
        "Loại aggregate; điều kiện coverage >=80, chọn lịch sử chung theo độ phủ 80% quốc gia, không theo giá trị/metric TEST.",
        "Bản đã revision, không có vintage/release calendar thật; kết quả là hồi cứu. Chỉ số khác giá nhà USD của Ames.",
    ],
    "ch4_household_power": [
        "Đích là kW trung bình giờ, không phải kWh. Một giờ cần >=45 phút quan sát.",
        "Không điền nhãn thiếu. Chỉ input ffill tối đa 6 giờ, sau đó imputer fit train và kèm cờ thiếu.",
        "Một hộ gia đình, không bảo đảm tổng quát hóa cho hộ khác; không shuffle thời gian.",
    ],
}


def iso_utc(value):
    return pd.Timestamp(value).tz_localize("UTC").isoformat()


def check_capacity():
    free = shutil.disk_usage(ROOT).free
    require(free >= 5 * 1024**3, "Host filesystem below 5 GiB reserve; do not lower guard")
    return free


def freeze_split(dataset, partitions, matched, audit, windows=None):
    directory = SPLITS / dataset
    directory.mkdir(parents=True, exist_ok=True)
    audit_path = BASE / dataset / "leakage_audit.json"
    write_json(audit_path, audit)
    parts = []
    for name in PARTITIONS:
        path = directory / f"{name}.ids.jsonl.gz"
        write_rows(path, sorted(partitions[name]))
        selected = [r for r in windows or [] if r["partition"] == name]
        times = [t for row in selected for t in row["target_times"]]
        parts.append(
            {
                "name": name,
                "count": len(partitions[name]),
                "ids": {k: v for k, v in reference(path).items() if k != "size_bytes"},
                "target_start": iso_utc(min(times)) if times else None,
                "target_end": iso_utc(max(times)) if times else None,
            }
        )
    write_rows(directory / "matched_train.ids.jsonl.gz", matched)
    write_rows(directory / "quarantine.ids.jsonl.gz", partitions.get("quarantine", []))
    spec = SPECS[dataset]
    contract = {
        "schema_version": "3.0.0",
        "evidence_kind": "measured",
        "dataset_id": dataset,
        "split_id": dataset + "_v3_seed42",
        "dataset_sha256": file_digest(ROOT / f"artifacts/manifests/datasets/{dataset}.json"),
        "method": "temporal"
        if windows is not None
        else "official"
        if "official" in spec["split_method"]
        else "group_stratified",
        "seed": 42,
        "train_only_preprocessing": True,
        "group_key": "global_target_time"
        if windows is not None
        else "transitive_feature_or_pixel_or_verified_property_identity",
        "partitions": parts,
        "leakage_audit": {k: v for k, v in reference(audit_path).items() if k != "size_bytes"},
    }
    validate_document("split", contract)
    write_json(directory / "split_contract.json", contract)
    write_json(
        directory / "data_holdout.json",
        {
            "status": "DATA_PARTITIONS_FROZEN_NOT_MODEL_EVALUATION_AUTHORIZATION",
            "dataset_id": dataset,
            "split_sha256": file_digest(directory / "split_contract.json"),
            "evaluation_count": 0,
            "test_evaluation_allowed_now": False,
            "later_gate": "Freeze model/config/evaluator and approved run IDs before one authorized TEST batch; RNN+LSTM jointly at Phase29",
        },
    )
    return {
        "split": reference(directory / "split_contract.json"),
        "matched_subset": reference(directory / "matched_train.ids.jsonl.gz"),
        "counts": {name: len(partitions[name]) for name in PARTITIONS},
        "matched_train_count": len(matched),
        "quarantine_count": len(partitions.get("quarantine", [])),
    }


def prepare_tabular(dataset):
    frame, target, ids, hashes, properties = load_tabular(dataset)
    spec = SPECS[dataset]
    strata = (
        pd.qcut(target, 10, labels=False, duplicates="drop").astype(str).tolist()
        if spec["task"] == "regression"
        else target.astype(str).tolist()
    )
    groups = linked_groups(hashes, properties)
    partitions = grouped_split(ids, groups, strata)
    matched = matched_subset(
        partitions["train"], dict(zip(ids, strata, strict=True)), spec["matched_train_cap"]
    )
    selected = np.isin(ids, matched)
    prep = fit_tabular(frame.loc[selected], matched)
    prep.update(
        excluded_features=spec["exclude_features"],
        fit_track="matched_subset_train",
        target_name=spec["target"],
        target_is_not_a_feature=True,
        fit_scope_note="IDs hash is sorted; statistics use the same set of source rows regardless of row order",
    )
    if spec["task"] == "regression":
        prep["target_transform"] = {
            "name": "standardize",
            "mean": float(target[selected].mean()),
            "std": float(target[selected].std(ddof=0)),
            "inverse_units": "USD",
        }
    else:
        counts = target[selected].astype(str).value_counts().to_dict()
        prep["class_weights"] = {k: len(matched) / (len(counts) * v) for k, v in counts.items()}
    # Verify the contract on heldout inputs without changing any fitted statistic.
    transformed = transform_tabular(frame, prep)
    audit = {
        **audit_partitions(partitions, dict(zip(ids, groups, strict=True))),
        "status": "PASS",
        "feature_identity_groups": len(set(hashes)),
        "linked_groups": len(set(groups)),
        "duplicate_feature_rows": len(ids) - len(set(hashes)),
        "conflicting_target_feature_groups": int(
            pd.DataFrame({"h": hashes, "y": target}).groupby("h").y.nunique().gt(1).sum()
        ),
        "excluded_features": spec["exclude_features"],
        "preprocessing_fit_ids_sha256": prep["fit_ids_sha256"],
        "stratification": "group-majority binary class or sale-price decile (split only, never a feature)",
        "patient_or_client_independence_claimed": False,
        "property_linkage_used": properties is not None,
        "test_evaluation_executed": False,
    }
    split_info = freeze_split(dataset, partitions, matched, audit)
    write_json(BASE / dataset / "preprocessing.json", prep)
    write_rows(
        BASE / dataset / "index.jsonl.gz",
        [
            {
                "id": key,
                "group": str(group),
                "feature_sha256": h,
                "stratum": label,
                "target": value,
                "raw_row": i,
                "partition": next(n for n in PARTITIONS if key in part_sets[n]),
            }
            for part_sets in [{n: set(partitions[n]) for n in PARTITIONS}]
            for i, (key, group, h, label, value) in enumerate(
                zip(ids, groups, hashes, strata, target, strict=True)
            )
        ],
    )
    profile = describe_frame(frame, ids, partitions["train"])
    write_json(BASE / dataset / "feature_profile.json", profile)
    sample_ids = matched_subset(matched, dict(zip(ids, strata, strict=True)), 3)
    positions = {key: i for i, key in enumerate(ids)}
    full_samples = [
        {
            "id": key,
            "input": clean(frame.iloc[positions[key]].to_dict()),
            "known_output": clean(target.iloc[positions[key]]),
        }
        for key in sample_ids
    ]
    write_json(BASE / dataset / "samples.json", full_samples)
    samples = [{**row, "input": dict(list(row["input"].items())[:8])} for row in full_samples]
    distributions = (
        {n: target[np.isin(ids, partitions[n])].astype(str).value_counts().to_dict() for n in PARTITIONS}
        if spec["task"] != "regression"
        else {n: clean(target[np.isin(ids, partitions[n])].describe().to_dict()) for n in PARTITIONS}
    )
    if spec["task"] == "regression":
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(target, bins=35, color="#326A9B")
        ax.set(xlabel="Giá bán nhà (USD)", ylabel="Số bất động sản", title="Ames: phân bố giá nguồn")
        figures = save_figure(fig, dataset + "_distribution")
    else:
        figures = distribution_figure(dataset, target.astype(str).value_counts().sort_index().to_dict())
    return {
        "scope": "measured_tabular",
        "size_and_schema": {
            "rows": len(frame),
            "features": list(frame.columns),
            "model_input_width": prep["output_width"],
            "target": spec["target"],
            **split_info,
        },
        "samples": samples,
        "sample_note": "Ba mẫu thuộc matched train, output là nhãn/giá nguồn, không phải dự đoán. Input hiển thị tối đa 8 biến; samples.json chứa đủ biến.",
        "distribution_summary": {
            "target_by_partition": distributions,
            "missing_by_feature": profile["missing"],
            "duplicate_rows": audit["duplicate_feature_rows"],
            "outliers": "feature_profile.json, ngưỡng IQR từ train",
        },
        "split_note": "Gom exact feature duplicates và PID nếu có, rồi stratify theo nhóm 70/15/15 (xấp xỉ theo số dòng). Imputer/scaler/vocabulary/target scaler/class weight chỉ fit matched train; unknown category -> all-zero. Không tự xóa outlier.",
        "comments": COMMENTS[dataset],
        "figures": figures,
        "memory": {
            "eda_frame_bytes": profile["frame_memory_bytes"],
            "transformed_all_rows_bytes": transformed.nbytes,
            "input_batch_float32_bytes": spec and 32 * prep["output_width"] * 4,
            "vram_peak": None,
            "note": "Input-only planning bound, not measured GPU training peak; probe at Phase25",
        },
    }


def prepare_images(dataset):
    spec = SPECS[dataset]
    frame = load_images(dataset, spec["resolution"])
    groups = linked_groups(frame.pixel_sha256.tolist(), frame.model_pixel_sha256.tolist())
    ids, labels = frame.id.tolist(), frame.target.tolist()
    official = (
        frame.loc[frame.official_split == "test", "id"].tolist()
        if "official" in spec["split_method"]
        else None
    )
    partitions = grouped_split(
        ids,
        groups,
        labels,
        official_test=official,
        validation_fraction=0.1 if dataset == "ch3_cifar10" else 0.15,
    )
    matched = matched_subset(
        partitions["train"], dict(zip(ids, labels, strict=True)), spec["matched_train_cap"]
    )
    audit = {
        **audit_partitions(partitions, dict(zip(ids, groups, strict=True))),
        "status": "PASS",
        "native_pixel_duplicate_rows": len(ids) - frame.pixel_sha256.nunique(),
        "conflicting_label_pixel_groups": int(
            pd.DataFrame({"g": groups, "y": labels}).groupby("g").y.nunique().gt(1).sum()
        ),
        "model_pixel_duplicate_rows": len(ids) - frame.model_pixel_sha256.nunique(),
        "official_test_preserved": official is not None,
        "official_test_count": len(official or []),
        "train_test_duplicate_quarantine_count": len(partitions["quarantine"]),
        "verified_patient_key": False,
        "verified_spatial_key": False,
        "independence_claim": "exact native/model pixel groups only; patient/geographic independence NOT established",
        "test_evaluation_executed": False,
    }
    split_info = freeze_split(dataset, partitions, matched, audit)
    counts = frame.loc[frame.id.isin(matched)].target.value_counts().to_dict()
    prep = {
        "schema_version": "3.0.0",
        "fit_scope": "train_only",
        "fit_count": len(matched),
        "fit_ids_sha256": canonical_sha256(matched),
        "class_weights": {k: len(matched) / (len(counts) * v) for k, v in counts.items()},
        "decode": "Pillow RGB; CIFAR binary channels-first -> HWC",
        "resize": "Pillow BILINEAR",
        "input_shape_hwc": [*spec["resolution"], 3],
        "rescale": "float32 / 255",
        "augmentation": "none for the locked matched comparison; any extra track needs separate config",
        "normalization_fit": "no fitted channel mean/std; same 0..1 scaling for all frameworks",
    }
    if "class_name" in frame:
        prep["class_names"] = frame.groupby("target").class_name.first().sort_index().to_dict()
    write_json(BASE / dataset / "preprocessing.json", prep)
    part_map = {key: name for name in PARTITIONS for key in partitions[name]}
    for key in partitions["quarantine"]:
        part_map[key] = "quarantine"
    frame["group"] = list(map(str, groups))
    frame["partition"] = frame.id.map(part_map)
    write_rows(BASE / dataset / "index.jsonl.gz", frame.to_dict(orient="records"))
    profile = describe_frame(
        frame[["width", "height", "mean_intensity", "std_intensity", "black_fraction"]],
        ids,
        partitions["train"],
    )
    write_json(BASE / dataset / "feature_profile.json", profile)
    examples = frame.loc[frame.id.isin(matched)].sort_values("id").groupby("target", sort=True).head(1)
    fig, axes = plt.subplots(2, 5, figsize=(10, 4.8))
    for ax in axes.flat:
        ax.axis("off")
    for ax, row in zip(axes.flat, examples.to_dict(orient="records")):
        ax.imshow(image_for_row(dataset, row, spec["resolution"]))
        ax.set_title(
            f"{row['target']}: {row['class_name']}" if "class_name" in row else str(row["target"]), fontsize=9
        )
    fig.suptitle("Mẫu train tại resolution so sánh; tiêu đề là nhãn nguồn")
    figures = save_figure(fig, dataset + "_samples")
    figures += distribution_figure(dataset, frame.target.value_counts().sort_index().to_dict())
    samples = [
        {
            "id": row["id"],
            "input": {
                "member": row["member"],
                "native_shape": [row["height"], row["width"], 3],
                "model_shape": prep["input_shape_hwc"],
            },
            "known_output": row["target"],
        }
        for row in examples.head(3).to_dict(orient="records")
    ]
    write_json(BASE / dataset / "samples.json", samples)
    return {
        "scope": "measured_image",
        "size_and_schema": {
            "images": len(frame),
            "classes": len(counts),
            "native_shapes": frame[["height", "width"]].drop_duplicates().values.tolist(),
            "model_shape_hwc": prep["input_shape_hwc"],
            "label_mapping": prep.get("class_names", {label: label for label in sorted(counts)}),
            **split_info,
        },
        "samples": samples,
        "sample_note": "Mẫu và hình chỉ lấy matched train. known_output là nhãn gốc, không phải dự đoán.",
        "distribution_summary": {
            "class_counts": frame.target.value_counts().sort_index().to_dict(),
            "class_by_partition": {
                n: frame.loc[frame.partition == n].target.value_counts().to_dict() for n in PARTITIONS
            },
            "decode_or_label_missing": 0,
            "pixel_duplicate_rows": audit["native_pixel_duplicate_rows"],
            "quarantine": len(partitions["quarantine"]),
            "outlier_note": "IQR brightness/black fraction, no clinical quality claim or row deletion; feature_profile.json",
        },
        "split_note": "Gom trùng pixel gốc và sau resize. Nếu có official TEST: giữ nguyên TEST, loại bản trùng TEST khỏi development bằng quarantine; validation chỉ lấy official train. Các phép fit/class weight dùng train. Không có augmentation khác nhau giữa framework.",
        "comments": COMMENTS[dataset],
        "figures": figures,
        "memory": {
            "one_native_decoded_rgb_bytes": int(frame.width.max() * frame.height.max() * 3),
            "input_batch_float32_bytes": 16 * int(np.prod(prep["input_shape_hwc"])) * 4,
            "cache_all_images": False,
            "vram_peak": None,
            "note": "Stream/decode per image; input-only lower bound, no claim about GPU peak",
        },
    }


def prepare_temporal(dataset):
    spec = SPECS[dataset]
    frame, features, selection = load_series(dataset)
    frame = frame.sort_values(["series", "time"]).reset_index(drop=True)
    cuts = temporal_boundaries(frame.time)
    row_ids = [f"{s}/{t.isoformat()}" for s, t in zip(frame.series, frame.time, strict=True)]
    prefix = frame.time <= pd.Timestamp(cuts[0])
    prep = fit_tabular(frame.loc[prefix, features], np.asarray(row_ids)[prefix].tolist())
    prep.update(
        fit_track="all_observed_training_prefix_times_only; same contract for all implementations",
        features=features,
        lookback=spec["lookback"],
        horizons=spec["horizons"],
        target_imputation="never",
        target_transform={
            "name": "standardize",
            "mean": float(frame.loc[prefix, "target"].mean()),
            "std": float(frame.loc[prefix, "target"].std(ddof=0)),
        },
    )
    transformed = frame.copy()
    transformed[features] = transform_tabular(frame[features], prep)
    windows, excluded = causal_windows(transformed, features, spec["lookback"], spec["horizons"], cuts)
    partitions = {name: sorted(r["id"] for r in windows if r["partition"] == name) for name in PARTITIONS}
    require(all(partitions.values()), "Temporal source has an empty partition")
    require(
        {r["series"] for r in windows if r["partition"] == "train"} == set(frame.series),
        "An eligible economy has no training windows",
    )
    matched = matched_subset(
        partitions["train"], {r["id"]: r["series"] for r in windows}, spec["matched_train_cap"]
    )
    audit = {
        "status": "PASS",
        "id_overlap_count": 0,
        "group_overlap_count": None,
        "series_overlap_expected": "forecast seen series, NOT unseen-country holdout",
        "target_time_overlap_count": 0,
        "all_horizons_inside_partition": True,
        "context_may_precede_boundary": True,
        "future_input_used": False,
        "calendar_boundaries": cuts,
        "source_clock": "calendar markers; power civil clock as recorded, timezone/DST not reconstructed",
        "contract_time_encoding": "+00:00 is a normalized calendar coordinate for schema/ordering, NOT a claim that source measurements were timestamped in UTC",
        "excluded_windows": excluded,
        "target_missing_rows_not_imputed": int(frame.target.isna().sum()),
        "selection": selection,
        "test_evaluation_executed": False,
    }
    split_info = freeze_split(dataset, partitions, matched, audit, windows)
    write_json(BASE / dataset / "preprocessing.json", prep)
    write_rows(BASE / dataset / "index.jsonl.gz", windows)
    # One small causal-series table, not expanded [window,lookback,feature] copies.
    cache = ROOT / "data/processed/v3" / dataset / "series.csv.gz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    with (
        cache.open("wb") as outgoing,
        gzip.GzipFile(filename="", mode="wb", fileobj=outgoing, mtime=0) as packed,
    ):
        packed.write(
            frame.to_csv(index=False, date_format="%Y-%m-%dT%H:%M:%S", float_format="%.12g").encode()
        )
    write_json(BASE / dataset / "series_cache.json", reference(cache))
    folds = rolling_folds(frame.time, cuts[1])
    for fold in folds:
        own_prefix = frame.time <= pd.Timestamp(fold["train_end"])
        own_prep = fit_tabular(frame.loc[own_prefix, features], np.asarray(row_ids)[own_prefix].tolist())
        own_prep["target_transform"] = {
            "mean": float(frame.loc[own_prefix, "target"].mean()),
            "std": float(frame.loc[own_prefix, "target"].std(ddof=0)),
        }
        own_prep["features"] = features
        folder = SPLITS / dataset / f"rolling_fold_{fold['fold']}"
        folder.mkdir(parents=True, exist_ok=True)
        own_frame = frame.copy()
        own_frame[features] = transform_tabular(frame[features], own_prep)
        own_windows, _ = causal_windows(
            own_frame,
            features,
            spec["lookback"],
            spec["horizons"],
            [fold["train_end"], fold["validation_end"]],
        )
        for name in ("train", "validation"):
            own_ids = sorted(r["id"] for r in own_windows if r["partition"] == name)
            require(bool(own_ids), "Empty rolling fold")
            write_rows(folder / f"{name}.ids.jsonl.gz", own_ids)
            fold[name + "_count"] = len(own_ids)
            if name == "train":
                own_matched = matched_subset(
                    own_ids, {r["id"]: r["series"] for r in own_windows}, spec["matched_train_cap"]
                )
                write_rows(folder / "matched_train.ids.jsonl.gz", own_matched)
                fold["matched_train_count"] = len(own_matched)
                fold["matched_train_sha256"] = file_digest(folder / "matched_train.ids.jsonl.gz")
        write_json(folder / "preprocessing.json", own_prep)
    write_json(SPLITS / dataset / "rolling_folds.json", folds)
    observed = frame.loc[frame.target.notna()]
    profile = describe_frame(frame[features], row_ids, np.asarray(row_ids)[prefix].tolist())
    write_json(BASE / dataset / "feature_profile.json", profile)
    selected_rows = [r for r in windows if r["id"] in set(matched[:3])]
    samples = [
        {
            "id": row["id"],
            "input": {
                "context_start": row["context_start"],
                "context_end": row["context_end"],
                "last_values": clean(frame.loc[row["origin_index"], features[:4]].to_dict()),
            },
            "known_output": {
                "horizons": spec["horizons"],
                "target_times": row["target_times"],
                "values": frame.loc[row["target_indices"], "target"].tolist(),
            },
        }
        for row in selected_rows
    ]
    write_json(BASE / dataset / "samples.json", samples)
    fig, ax = plt.subplots(figsize=(8, 4))
    representatives = [s for s in ("Q.US.N.628", "Q.GB.N.628", "Q.JP.N.628") if s in set(frame.series)] or [
        frame.series.iloc[0]
    ]
    for sid in representatives:
        group = frame.loc[frame.series == sid].set_index("time").target
        if len(group) > 5000:
            group = group.resample("7D").mean()
        ax.plot(group.index, group.values, label=sid, linewidth=0.8)
    for i, cut in enumerate(cuts):
        ax.axvline(
            pd.Timestamp(cut),
            color=("#D08C2B", "#775CA6")[i],
            linestyle="--",
            label=("Train kết thúc", "Validation kết thúc")[i],
        )
    plot_titles = {
        "ch4_gold_pink_sheet": "Giá vàng theo tháng",
        "ch4_bis_house_prices": "BIS: ba chuỗi quốc gia minh họa đã chọn trước",
        "ch4_household_power": "Điện: trung bình 7 ngày từ chuỗi giờ (chỉ để vẽ)",
    }
    units = {
        "ch4_gold_pink_sheet": "USD/troy ounce",
        "ch4_bis_house_prices": "Chỉ số danh nghĩa (2010 = 100)",
        "ch4_household_power": "Công suất trung bình (kW)",
    }
    ax.set(title=plot_titles[dataset], ylabel=units[dataset], xlabel="Thời gian theo lịch nguồn")
    ax.legend(fontsize=8)
    figures = save_figure(fig, dataset + "_time")
    return {
        "scope": "measured_timeseries",
        "size_and_schema": {
            "canonical_time_rows": len(frame),
            "series": frame.series.nunique(),
            "features": features,
            "lookback": spec["lookback"],
            "horizons": spec["horizons"],
            "range": [str(frame.time.min()), str(frame.time.max())],
            "source_clock": audit["source_clock"],
            "contract_time_encoding": audit["contract_time_encoding"],
            "valid_windows": len(windows),
            **split_info,
        },
        "samples": samples,
        "sample_note": "Mẫu window thuộc matched train; known_output là giá trị tương lai đã có trong nguồn train, không phải dự đoán. Target thiếu không bao giờ được điền.",
        "distribution_summary": {
            "target_observed_summary": clean(observed.target.describe().to_dict()),
            "missing_target_rows": int(frame.target.isna().sum()),
            "calendar_boundaries": cuts,
            "excluded_windows": excluded,
            "selected_series_count": frame.series.nunique(),
            "per_series_counts": frame.groupby("series").target.count().to_dict(),
            "selection": selection,
        },
        "split_note": "Split 70/15/15 theo lịch target chung. Mọi horizon của window phải ở cùng partition; context chỉ dùng quan sát trước target. Scaler/imputer chính fit prefix train, riêng từng rolling fold fit prefix của chính fold; không fit validation/test. Matched cap chỉ áp dụng train; giữ full validation/test. TEST RNN/LSTM mở chung ở Phase29 sau khóa cả hai họ.",
        "comments": COMMENTS[dataset],
        "figures": figures,
        "memory": {
            "canonical_frame_bytes": int(frame.memory_usage(deep=True).sum()),
            "input_batch_float32_bytes": 32 * spec["lookback"] * len(features) * 4,
            "materialize_all_windows": False,
            "all_windows_input_float32_bytes_if_materialized": len(windows)
            * spec["lookback"]
            * len(features)
            * 4,
            "vram_peak": None,
            "note": "Lazily slice ranges; input-only bound, actual peak requires Phase25 probe",
        },
    }


def prepare_history(dataset):
    contract = source(dataset)["contract"]
    path = ROOT / contract["files"][0]["path"]
    figures = []
    if dataset == "ch1_iris_history":
        with zipfile.ZipFile(path) as archive:
            frame = pd.read_csv(
                archive.open("iris.data"),
                header=None,
                names=["sepal_length", "sepal_width", "petal_length", "petal_width", "species"],
            )
        distribution = frame.species.value_counts().to_dict()
        samples = [
            {"input": row[:4].to_list(), "known_output": row.iloc[4]} for _, row in frame.head(3).iterrows()
        ]
        write_json(
            BASE / dataset / "feature_profile.json",
            describe_frame(frame.iloc[:, :4], list(map(str, frame.index)), list(map(str, frame.index))),
        )
        comments = ["Benchmark nhỏ, cân bằng; chỉ minh họa lịch sử phân loại, không có thí nghiệm V3 Ch1."]
    elif dataset == "ch1_mnist_history":
        with np.load(path, allow_pickle=False) as arrays:
            distribution = {
                str(i): int((arrays["y_train"] == i).sum() + (arrays["y_test"] == i).sum()) for i in range(10)
            }
            samples = [
                {"input": f"official train index {i}, uint8 28x28", "known_output": int(arrays["y_train"][i])}
                for i in range(3)
            ]
            fig, axes = plt.subplots(2, 5, figsize=(8, 4))
            for label, ax in enumerate(axes.flat):
                i = int(np.flatnonzero(arrays["y_train"] == label)[0])
                ax.imshow(arrays["x_train"][i], cmap="gray", vmin=0, vmax=255)
                ax.set_title(str(label))
                ax.axis("off")
            figures = save_figure(fig, dataset + "_samples")
            hashes = [canonical_sha256(image.tolist()) for image in arrays["x_train"]]
            duplicate_count = len(hashes) - len(set(hashes))
        comments = [
            "MNIST là case study lịch sử; không thay IDRiD/EuroSAT/CIFAR trong ma trận CNN V3.",
            f"Official train có {duplicate_count} ảnh trùng pixel; không tạo random split mới hay train Ch1.",
        ]
    else:
        distribution = {"local_metadata_page": 1, "local_images": 0}
        samples = [
            {
                "input": "Trang metadata ILSVRC2012 đã lưu",
                "known_output": "1000 categories công bố; không có ảnh local",
            }
        ]
        comments = [
            "Chỉ metadata/citation lịch sử. Không bịa ảnh mẫu, phân bố ảnh hay thí nghiệm trên full ImageNet.",
            "Quy mô ảnh công bố trong source card không phải số mẫu đo trên máy.",
        ]
    figures += distribution_figure(dataset, distribution)
    return {
        "scope": "historical_case_metadata_only" if "imagenet" in dataset else "historical_case",
        "size_and_schema": contract["logical_size"],
        "samples": samples,
        "sample_note": "Mẫu nguồn phục vụ lịch sử, không phải output của mô hình được train trong Phase24.",
        "distribution_summary": distribution,
        "split_note": "Ch1 không huấn luyện. Giữ official split nếu có; không tạo TEST hay preprocessing fit cho chương lịch sử.",
        "comments": comments,
        "figures": figures,
    }


def prepare_frozen_or_view(dataset):
    spec, envelope = SPECS[dataset], source(dataset)
    if spec["chapter"] == 6:
        parents = [read_json(BASE / parent / "eda.json") for parent in spec["parent_dataset_ids"]]
        return {
            "scope": "declared_parent_view_NOT_AGENT_BENCHMARK",
            "size_and_schema": {
                "agent_tasks": None,
                "parent_dataset_ids": spec["parent_dataset_ids"],
                "additional_raw_bytes": 0,
            },
            "samples": [
                {"from_parent": spec["parent_dataset_ids"][0], "parent_sample": parents[0]["samples"][:1]}
            ],
            "sample_note": "Chỉ dẫn lại mẫu thật từ parent, KHÔNG phải task/gold answer của hệ agent. Task input/output schema và benchmark sẽ khóa Phase31.",
            "distribution_summary": {
                "agent_distribution": None,
                "parent_distribution_references": [
                    f"{parent}/eda.json" for parent in spec["parent_dataset_ids"]
                ],
            },
            "split_note": "Chưa tạo task/split Ch6. Phase31 gom paraphrase/template/source ID và kế thừa TEST seal; không copy raw hay mở TEST parent để tuning.",
            "comments": [
                "Không coi declared là dataset đã train/đánh giá.",
                "Ba miền ưu tiên giữ diabetes, house, gold; không bịa số task hoặc metric.",
            ],
            "figures": [],
        }
    stats = read_json(ROOT / "artifacts/manifests/ch5/preprocessing_manifest.json")["statistics"]
    if dataset == "ch5_finqa":
        raw_train = read_json(ROOT / "data/raw/ch5/finqa/dataset/train.json")
        samples = [
            {
                "input": row["qa"]["question"],
                "known_output": {"answer": row["qa"].get("answer"), "program": row["qa"].get("program")},
            }
            for row in raw_train[:3]
        ]
        distribution = stats["finqa"]["split_distribution"]
        comments = [
            "Re-use split/audit Phase12. Private_test tồn tại trong raw nhưng không phải nhãn được phép đánh giá.",
            "Page-group overlap giữa các public split =0, nhưng report-key overlap khác 0 (197/243/93); không tuyên bố độc lập theo công ty/báo cáo.",
        ]
    elif dataset == "ch5_medquad_diabetes":
        # Public retrieval corpus, NOT sealed benchmark question/gold labels.
        # Bundle has no split column: never mislabel a corpus chunk as TRAIN.
        samples = []
        with gzip.open(ROOT / "apps/api/models/kg_chunks.jsonl.gz", "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                if row.get("domain") == "medical":
                    samples.append(
                        {
                            "input": row["chunk_id"],
                            "known_output": str(row.get("text", ""))[:500],
                            "scope": "published retrieval corpus evidence, benchmark question split unknown; not a QA query/gold or model output",
                        }
                    )
                    if len(samples) == 3:
                        break
        require(bool(samples), "Need frozen public corpus evidence for MedQuAD examples")
        distribution = stats["medquad"]["split_distribution"]
        comments = [
            "Nguồn upstream có 47.441 QAPair, nhưng lát cắt diabetes khóa chỉ 247 query/62 nhóm; không đánh đồng hai mẫu số.",
            "Kế thừa 27 bản trùng đã loại và split 152/33/62; không rebuild filter/split hoặc đánh giá lại TEST.",
        ]
    else:
        files = [
            row
            for row in envelope["contract"]["files"]
            if "/entities/" in row["path"] and row["path"].endswith(".json")
        ]
        distribution, samples = {}, []
        for file in files:
            document = read_json(ROOT / file["path"])
            entities = document.get("entities", {document.get("id", "unknown"): document})
            for key, entity in entities.items():
                claims = entity.get("claims", {})
                distribution[key] = sum(map(len, claims.values()))
                if len(samples) < 3:
                    samples.append(
                        {
                            "input": key,
                            "known_output": {
                                "revision": entity.get("lastrevid"),
                                "claim_count": distribution[key],
                                "property_ids": sorted(claims)[:5],
                            },
                        }
                    )
        require(len(distribution) == 10, "Wikidata entity snapshot path/schema mismatch")
        comments = [
            "KG hỗ trợ với 10 entity/2.056 claim, không phải benchmark QA thứ ba.",
            "Giữ revision/hash nguồn, chỉ audit cấu trúc; không thực hiện truy vấn web mới.",
        ]
    figures = distribution_figure(dataset, distribution)
    return {
        "scope": "historical_baseline_READ_ONLY",
        "size_and_schema": {
            **envelope["contract"]["logical_size"],
            "frozen_slice": stats["medquad"]
            if "medquad" in dataset
            else stats["finqa"]
            if "finqa" in dataset
            else envelope["inspection"],
        },
        "samples": samples,
        "sample_note": "FinQA: raw official train. MedQuAD: ánh xạ ID -> trích đoạn corpus retrieval công khai đã đóng gói, không gán train/test vì bundle không có split, không phải QA gold hay output mô hình. Wikidata: cấu trúc snapshot. Không đọc lại TEST query/prediction để tạo ví dụ hay tính metric.",
        "distribution_summary": distribution,
        "split_note": "Kế thừa manifest Phase12 và audit đã khóa; không chia lại, fit lại hay chạy TEST. Ch5 run_count vẫn 1; Wikidata chỉ structural audit.",
        "comments": comments,
        "figures": figures,
    }


def prepare_one(dataset):
    check_capacity()
    spec = SPECS[dataset]
    if spec["chapter"] == 2:
        measured = prepare_tabular(dataset)
    elif spec["chapter"] == 3:
        measured = prepare_images(dataset)
    elif spec["chapter"] == 4:
        measured = prepare_temporal(dataset)
    elif spec["chapter"] == 1:
        measured = prepare_history(dataset)
    else:
        measured = prepare_frozen_or_view(dataset)
    measured.update(
        schema_version="3.0.0",
        dataset_id=dataset,
        protocol_sha256=file_digest(PROTOCOL_PATH),
        source_manifest_sha256=file_digest(ROOT / f"artifacts/manifests/datasets/{dataset}.json"),
        training_executed=False,
        test_evaluation_executed=False,
    )
    write_json(BASE / dataset / "eda.json", measured)
    render_card(spec, source(dataset)["contract"], measured)
    print(
        json.dumps(
            {
                "dataset": dataset,
                "scope": measured["scope"],
                "split_counts": measured["size_and_schema"].get("counts"),
            }
        ),
        flush=True,
    )


def build_catalog():
    datasets = []
    for dataset, spec in SPECS.items():
        measured = read_json(BASE / dataset / "eda.json")
        row = {
            "dataset_id": dataset,
            "chapter": spec["chapter"],
            "scope": measured["scope"],
            "source_manifest": reference(ROOT / f"artifacts/manifests/datasets/{dataset}.json"),
            "eda": reference(BASE / dataset / "eda.json"),
            "data_card": reference(ROOT / "report/references/dataset_cards/v3_eda" / f"{dataset}.md"),
            "split": None,
            "preprocessing": None,
            "parent_dataset_ids": spec["parent_dataset_ids"],
        }
        if spec["chapter"] in (2, 3, 4):
            row["split"] = reference(SPLITS / dataset / "split_contract.json")
            row["preprocessing"] = reference(BASE / dataset / "preprocessing.json")
        datasets.append(row)
    return {
        "schema_version": "3.0.0",
        "phase": 24,
        "datasets": datasets,
        "source_registry": reference(ROOT / "data/registry.yaml"),
        "protocol_sha256": file_digest(PROTOCOL_PATH),
        "training_executed": False,
        "test_evaluation_executed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=list(SPECS))
    args = parser.parse_args()
    if (BASE / "data_lock.json").exists():
        from scripts.verify_phase24 import verify

        print(json.dumps({"action": "reused_locked_Phase24", **verify()}))
        return 0
    for dataset in [args.dataset] if args.dataset else SPECS:
        prepare_one(dataset)
    if all((BASE / dataset / "eda.json").exists() for dataset in SPECS):
        write_json(ROOT / "data/catalog_v3.json", build_catalog())
        write_json(
            BASE / "memory_plan.json",
            {
                "schema_version": "3.0.0",
                "estimates": {
                    dataset: read_json(BASE / dataset / "eda.json").get("memory") for dataset in SPECS
                },
                "gpu_peak_measured_in_phase24": False,
                "policy": "Exact input tensor/canonical frame byte counts, not total training peak. Stream images and lazily slice windows. CPU/GPU activations/optimizer/peak probes are acceptance gates in Phase25, with 8 GiB device limit and 5 GiB host disk reserve.",
                "canonical_series_cache": "data/processed/v3 is ignored and optional; verify cache hash when present, otherwise reconstruct canonical frame from frozen raw with load_series and stable sort. Never refit preprocessing.",
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
