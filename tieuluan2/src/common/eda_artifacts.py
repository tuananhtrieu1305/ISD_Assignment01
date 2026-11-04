"""Reproducible EDA artifacts. Raw values stay separate from transformations."""

from __future__ import annotations

import gzip
import json
import math
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.acquisition import file_digest
from src.common.contracts import ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase24"
CARDS = ROOT / "report/references/dataset_cards/v3_eda"
FIGURES = ROOT / "artifacts/figures/phase24"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.hashsalt": "ai_v3_phase24_42"})


def clean(value):
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return clean(value.item())
    if value is pd.NA or value is pd.NaT or isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(clean(value), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as target, gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as stream:
        for row in rows:
            stream.write(
                (json.dumps(clean(row), ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()
            )


def read_rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def reference(path):
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": file_digest(path),
        "size_bytes": path.stat().st_size,
    }


def describe_frame(frame, ids, train_ids):
    train = frame.loc[np.isin(ids, train_ids)]
    numeric = {}
    categories = {}
    for name in frame:
        if pd.api.types.is_numeric_dtype(frame[name]):
            full = frame[name].replace([np.inf, -np.inf], np.nan)
            q1, q3 = train[name].quantile([0.25, 0.75])
            lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
            numeric[name] = {
                "min": full.min(),
                "median": full.median(),
                "max": full.max(),
                "iqr_lower_train": lower,
                "iqr_upper_train": upper,
                "outlier_count_full_source": int(((full < lower) | (full > upper)).sum()),
            }
        else:
            categories[name] = frame[name].fillna("__missing__").astype(str).value_counts().to_dict()
    return clean(
        {
            "records": len(frame),
            "columns": list(frame.columns),
            "missing": frame.isna().sum().to_dict(),
            "numeric": numeric,
            "categories": categories,
            "frame_memory_bytes": int(frame.memory_usage(deep=True).sum()),
            "outlier_policy": "1.5 IQR bounds from train only; descriptive flags, no automatic row deletion",
        }
    )


def save_figure(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    result = []
    for suffix in ("png", "svg"):
        path = FIGURES / f"{name}.{suffix}"
        metadata = (
            {"Date": None, "Creator": "AI V3 Phase24"} if suffix == "svg" else {"Software": "AI V3 Phase24"}
        )
        fig.savefig(path, dpi=300, bbox_inches="tight", metadata=metadata)
        result.append(reference(path))
    plt.close(fig)
    return result


def distribution_figure(dataset_id, distribution):
    names, values = list(distribution), list(distribution.values())
    fig, ax = plt.subplots(figsize=(7, max(3, len(names) * 0.3)))
    ax.barh(list(map(str, names)), values, color="#326A9B")
    ax.invert_yaxis()
    ax.set_xlabel(
        "Số mẫu (thống kê mô tả, không phải metric mô hình)"
        if "wikidata" not in dataset_id
        else "Số claim trong từng entity snapshot"
    )
    titles = {
        "ch1_iris_history": "Iris: số mẫu theo loài",
        "ch1_mnist_history": "MNIST: số ảnh theo chữ số",
        "ch1_imagenet_history": "ImageNet: chỉ kiểm kê metadata local, không có ảnh",
        "ch2_cdc_diabetes": "CDC Diabetes: phân bố nhãn nhị phân",
        "ch2_bank_marketing": "Bank Marketing: phân bố nhãn đăng ký",
        "ch3_cifar10": "CIFAR-10: phân bố lớp",
        "ch3_eurosat": "EuroSAT: phân bố lớp phủ đất",
        "ch3_idrid": "IDRiD: phân bố DR grade",
        "ch5_finqa": "FinQA: split đã khóa từ Phase12",
        "ch5_medquad_diabetes": "MedQuAD: 247 query diabetes đã khóa",
        "ch5_wikidata_subgraphs": "Wikidata: phân bố 2.056 claim",
    }
    ax.set_title(titles.get(dataset_id, dataset_id.replace("_", " ")))
    ax.spines[["top", "right"]].set_visible(False)
    return save_figure(fig, dataset_id + "_distribution")


def render_card(spec, source, measured):
    """Keep inherited/deferred evidence unmistakably separate from measured training data."""
    dataset = spec["dataset_id"]
    scope = measured["scope"]
    lines = [
        f"# {dataset} — dữ liệu và kiểm tra Phase 24",
        "",
        f"Phạm vi: **{scope}**. Không huấn luyện hay đánh giá TEST trong Phase 24.",
        "",
        "## Nguồn, kích cỡ và cấu trúc",
        "",
        f"Nguồn: [{source['source']['citation']}]({source['source']['url'] or spec['source_url'] or '#'})",
        f"Phiên bản: {source['source']['version']}",
        "",
        f"Giấy phép/phạm vi: {source['source']['license_note']}",
        "",
        (
            f"Raw: {sum(f['size_bytes'] for f in source['files']):,} byte; "
            f"{source['logical_size']['records']} {source['logical_size']['unit']}."
        ),
        "",
        "Số đo và schema phần dùng trong V3:",
        "",
        "```json",
        json.dumps(clean(measured["size_and_schema"]), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Mẫu input/output",
        "",
        measured["sample_note"],
        "",
        "```json",
        json.dumps(clean(measured["samples"]), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Phân bố và chất lượng dữ liệu",
        "",
        "```json",
        json.dumps(clean(measured["distribution_summary"]), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Cách chia tập và tiền xử lý",
        "",
        measured["split_note"],
        "",
        "## Nhận xét và giới hạn",
        "",
    ]
    lines += [f"- {note}" for note in measured["comments"]]
    if spec["parent_dataset_ids"]:
        lines += ["", "Nguồn và điều khoản của từng parent:", ""]
        for parent in spec["parent_dataset_ids"]:
            parent_source = read_json(ROOT / f"artifacts/manifests/datasets/{parent}.json")["contract"][
                "source"
            ]
            lines += [f"- [{parent}]({parent}.md): [{parent_source['citation']}]({parent_source['url']})."]
    lines += [
        "",
        "## Bằng chứng tái lập",
        "",
        f"Chi tiết: `artifacts/manifests/phase24/{dataset}/eda.json`.",
        "Nguồn Phase23, raw và TEST Ch5 giữ nguyên; số đo mới không ghi ngược vào protocol.",
    ]
    for ref in measured.get("figures", []):
        if ref["path"].endswith(".png"):
            lines += ["", f"![{dataset}]({('../../../../' + ref['path'])})"]
    CARDS.mkdir(parents=True, exist_ok=True)
    path = CARDS / f"{dataset}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return reference(path)
