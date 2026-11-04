"""Build Word-readable Phase 19 raster assets from locked metric artifacts."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "term_paper/knowledge_rag/artifacts/metrics/phase15_error_analysis.csv"
OUTPUT = ROOT / "term_paper/report/assets/ch5_knowledge_rag/ch5_error_distribution.png"


def load_counts() -> dict[str, Counter[str]]:
    counts = {"medical": Counter(), "finance": Counter()}
    with SOURCE.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            domain = row["domain"]
            if row["split"] != "test" or domain not in counts:
                continue
            for category in filter(None, row["categories"].split("|")):
                counts[domain][category] += 1
    return counts


def label(category: str) -> str:
    return category.replace("_", " ")


def main() -> None:
    counts = load_counts()
    categories = sorted(set(counts["medical"]) | set(counts["finance"]))
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 5.2), dpi=200, sharey=True)
    colors = {"medical": "#2F75B5", "finance": "#64748B"}
    for axis, domain in zip(axes, ("medical", "finance")):
        values = [counts[domain].get(category, 0) for category in categories]
        bars = axis.barh(range(len(categories)), values, color=colors[domain])
        axis.set_title("Medical" if domain == "medical" else "Finance", fontweight="bold")
        axis.set_yticks(range(len(categories)), [label(category) for category in categories])
        axis.invert_yaxis()
        axis.set_xlabel("Số truy vấn")
        axis.grid(axis="x", alpha=0.18)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.bar_label(bars, padding=3, fontsize=8)
        axis.set_xlim(0, max(values or [1]) * 1.15 + 1)
    fig.suptitle("Nhóm lỗi B4 trên public TEST", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Built {OUTPUT} from {SOURCE}")


if __name__ == "__main__":
    main()
