"""Presentation-only r2: preserve r1 and use readable count heatmaps (no TEST forward)."""

import io
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.ch03_cnn.protocol import BASE, DATASETS, IMPLEMENTATIONS, check_sources, ref
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

LABELS = {"ch3_idrid": "IDRiD", "ch3_eurosat": "EuroSAT", "ch3_cifar10": "CIFAR-10"}
DEST = ROOT / "artifacts/figures/phase27/revisions/r2"


def count_figure(matrices, label):
    """Common count scale; dense 10-class grids omit overlapping cell text."""
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 5.2), layout="constrained")
    maximum = max(int(matrix.max()) for matrix in matrices)
    for ax, method, matrix in zip(axes, IMPLEMENTATIONS, matrices, strict=True):
        im = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max(1, maximum))
        if len(matrix) <= 5:
            for i in range(len(matrix)):
                for j in range(len(matrix)):
                    ax.text(
                        j,
                        i,
                        str(matrix[i, j]),
                        ha="center",
                        va="center",
                        fontsize=14,
                        color="white" if matrix[i, j] > maximum * 0.5 else "#18252C",
                    )
        ax.set(
            xticks=range(len(matrix)),
            yticks=range(len(matrix)),
            xlabel="Predicted class ID",
            ylabel="True class ID",
            title=method,
        )
        ax.tick_params(labelsize=14)
        ax.xaxis.label.set_size(15)
        ax.yaxis.label.set_size(15)
        ax.title.set_size(18)
    bar = fig.colorbar(im, ax=axes, shrink=0.72, pad=0.02)
    bar.set_label("Image count (shared scale)", fontsize=14)
    bar.ax.tick_params(labelsize=12)
    fig.suptitle(f"{label} — full TEST counts, fixed seed42", fontsize=18)
    return fig


def immutable_bytes(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError(f"Presentation revision already differs: {path}") from None


def main():
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Release is locked; use a new revision, not this producer")
    release = check_sources()
    original_path = BASE / "report_generation.json"
    original = read_json(original_path)
    for item in [original["manuscript"], *original["figures"], *original["tables"]]:
        if sha256_file(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("Original report evidence changed")
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.hashsalt": "cnn_phase27_report_r2"})
    replacements = {}
    for dataset in DATASETS:
        matrices = []
        for method in IMPLEMENTATIONS:
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            details = read_json(BASE / "runs" / entry["run_id"] / "test_details.json")
            matrices.append(np.asarray(details["metrics"]["confusion_matrix"]))
        fig = count_figure(matrices, LABELS[dataset])
        for extension in ("png", "svg"):
            payload = io.BytesIO()
            fig.savefig(
                payload,
                format=extension,
                dpi=300,
                metadata={"Date": None} if extension == "svg" else {"Software": "AI V3 Phase27 r2"},
            )
            path = DEST / f"{dataset}_confusion.{extension}"
            immutable_bytes(path, payload.getvalue())
            replacements[f"artifacts/figures/phase27/{path.name}"] = ref(path)
        plt.close(fig)
    text = (ROOT / original["manuscript"]["path"]).read_text(encoding="utf-8")
    for old, new in replacements.items():
        if old.endswith(".png"):
            text = text.replace("../../../" + old, "../../../" + new["path"])
    text = text.replace(
        "Hàng là nhãn thật, cột là dự đoán.",
        "Hàng là nhãn thật, cột là dự đoán. Ba triển khai dùng cùng thang màu số đếm "
        "trong mỗi dataset. Với 10 lớp, không in số ở từng ô để tránh chồng chữ; "
        "ma trận số đầy đủ nằm trong `runs/<run_id>/test_details.json` của manifest Phase27.",
    )
    path = ROOT / "report/sections/v3/ch03_cnn_r2.md"
    immutable_bytes(path, text.encode("utf-8"))
    generation_path = BASE / "revisions/r2/report_generation.json"
    write_once(
        generation_path,
        {
            **original,
            "revision": "r2",
            "supersedes": ref(original_path),
            "reason": "Visual QA found overlapping count annotations on 10-class confusion grids",
            "change_scope": "Three figure layouts/common count scales, links and explanatory caption only",
            "test_forward_executed": False,
            "figures": [replacements.get(item["path"], item) for item in original["figures"]],
            "manuscript": ref(path),
            "producer": ref(ROOT / "scripts/revise_phase27_report.py"),
        },
    )
    write_once(BASE / "active_report.json", {"revision": "r2", "generation": ref(generation_path)})
    print(json.dumps({"status": "PASS", "revision": "r2", "report": ref(path), "test_forward": False}))


if __name__ == "__main__":
    main()
