"""Versioned scientific figures/manuscript; preserve every r1 file and baseline byte."""

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from scripts.build_phase30 import text_once
from src.ch05_knowledge_rag.presentation_r2 import error_scope, render_manuscript_r2
from src.ch05_knowledge_rag.preservation import BASE, ROOT, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import read_json

REV = BASE / "revisions/presentation_r2"
FIG = ROOT / "artifacts/figures/phase30/r2"
MANUSCRIPT = ROOT / "report/sections/v3/ch05_knowledge_rag_r2.md"


def save(fig, name):
    records = []
    for extension in ("png", "svg"):
        path = FIG / (name + "." + extension)
        if path.exists():
            raise ValueError("Existing presentation r2 figure; inspect/version, never overwrite")
        fig.savefig(path, dpi=300, metadata={"Date": None} if extension == "svg" else None)
        records.append(ref(path))
    plt.close(fig)
    return records


def dataset_overview():
    audit = read_json(ROOT / "artifacts/metrics/ch5/phase11_data_audit.json")
    fig, axes = plt.subplots(1, 3, figsize=(14, 6.3), layout="constrained")
    types = sorted(audit["medquad"]["question_type_distribution"].items(), key=lambda r: (-r[1], r[0]))[:10]
    labels = [textwrap.fill(k, 22) for k, _ in types]
    axes[0].barh(labels, [v for _, v in types], color="#24558c")
    axes[0].invert_yaxis()
    axes[0].set(title="Whole MedQuAD: top10 question types", xlabel="QA pairs (not diabetes-only)")
    counts = read_json(ROOT / "artifacts/manifests/phase24/ch5_finqa/eda.json")["distribution_summary"]
    keys = ["train", "validation", "test", "private_test"]
    bars = axes[1].bar(
        ["Train", "Validation", "Public test", "Private test"],
        [counts[k] for k in keys],
        color=["#24558c", "#388078", "#bc8f32", "#a6bac4"],
    )
    axes[1].bar_label(bars, padding=3, fontsize=8)
    axes[1].tick_params(axis="x", labelrotation=35)
    axes[1].set(title="FinQA: official query split", ylabel="QA records", ylim=(0, 7200))
    entities = sorted(
        read_json(ROOT / "data/raw/ch5/wikidata/snapshot_index.json")["entities"],
        key=lambda r: (-r["claim_count"], r["qid"]),
    )
    axes[2].barh([r["qid"] for r in entities], [r["claim_count"] for r in entities], color="#388078")
    axes[2].invert_yaxis()
    axes[2].set(title="Wikidata:10 frozen entities", xlabel="Claims (not QA examples)")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8)
    fig.suptitle("Preserved data distributions: three sources, different roles", fontsize=12)
    return save(fig, "dataset_overview")


def graph_paths():
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout="constrained")
    for ax, domain in zip(axes, ("Medical", "Finance")):
        ax.set(xlim=(0, 1), ylim=(0, 1), title=domain)
        ax.axis("off")
        nodes = {
            "Question": (0.12, 0.79),
            "Entity" if domain == "Medical" else "Concept": (0.5, 0.79),
            "Wikidata": (0.86, 0.79),
            "Document" if domain == "Medical" else "Page": (0.5 if domain == "Medical" else 0.12, 0.25),
            "Chunk": (0.86 if domain == "Medical" else 0.5, 0.25),
        }
        for label, (x, y) in nodes.items():
            ax.text(
                x,
                y,
                label,
                ha="center",
                va="center",
                fontsize=10,
                bbox={"boxstyle": "round,pad=.5", "facecolor": "#e4edf3", "edgecolor": "#24558c"},
            )
        edges = (
            [
                ("Question", "Entity", "ASKS_ABOUT"),
                ("Document", "Entity", "DESCRIBES"),
                ("Document", "Chunk", "HAS_CHUNK"),
                ("Entity", "Wikidata", "SAME_AS"),
            ]
            if domain == "Medical"
            else [
                ("Question", "Concept", "MENTIONS"),
                ("Chunk", "Concept", "MENTIONS"),
                ("Page", "Chunk", "HAS_CHUNK"),
                ("Concept", "Wikidata", "SAME_AS"),
            ]
        )
        for source, target, label in edges:
            a, b = nodes[source], nodes[target]
            ax.annotate(
                "",
                xy=b,
                xytext=a,
                arrowprops={"arrowstyle": "->", "color": "#388078", "lw": 1.5, "shrinkA": 38, "shrinkB": 38},
            )
            x, y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ax.text(
                x + (0.10 if a[0] == b[0] else 0),
                y + (0.065 if a[1] == b[1] else 0),
                label,
                ha="center",
                fontsize=8,
            )
        ax.text(
            0.5, 0.02, "Subset only; SAME_AS requires one validated exact alias.", ha="center", fontsize=8
        )
    fig.suptitle(
        "Retrieval-bearing schema edges — query anchors come from question text, not gold", fontsize=11
    )
    return save(fig, "graph_paths")


def validation_ablation():
    import csv

    with (ROOT / "artifacts/metrics/ch5/phase15_ablation_validation.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    variants = ["full", "no_graph", "no_dense", "no_sparse", "hop_1", "hop_2"]
    labels = ["Full B4", "No graph", "No dense", "No sparse", "1 hop", "2 hops"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), layout="constrained")
    for ax, domain in zip(axes, ("medical", "finance")):
        values = [
            float(
                next(
                    r["value"]
                    for r in rows
                    if r["domain"] == domain and r["variant"] == name and r["metric"] == "chunk_recall_at_5"
                )
            )
            for name in variants
        ]
        bars = ax.bar(np.arange(6), values, color=["#24558c"] + ["#6495b1"] * 5)
        ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
        ax.set(title=domain, ylabel="Chunk Recall@5", ylim=(0, 1), xticks=np.arange(6), xticklabels=labels)
        ax.tick_params(axis="x", labelrotation=30)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Historical VALIDATION ablation — fixed k=5, no re-evaluation", fontsize=12)
    return save(fig, "validation_ablation")


def test_errors(scope):
    categories = [
        "retrieval_miss",
        "unsupported_answer",
        "numerical_reasoning",
        "entity_linking",
        "correct_or_other",
    ]
    labels = [
        "Retrieval miss",
        "Unsupported-answer proxy",
        "Numerical reasoning",
        "Entity linking",
        "Correct or other",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), layout="constrained")
    for ax, domain in zip(axes, ("medical", "finance")):
        points = [scope["test"][domain].get(key, 0) for key in categories]
        bars = ax.barh(labels, points, color="#24558c" if domain == "medical" else "#388078")
        ax.invert_yaxis()
        ax.bar_label(bars, padding=3, fontsize=9)
        ax.set(
            title=f"{domain} (n={62 if domain == 'medical' else 1147})",
            xlabel="Queries (labels can overlap)",
            xlim=(0, 42 if domain == "medical" else 1250),
        )
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("B4 error labels on public TEST only — challenge excluded", fontsize=12)
    return save(fig, "test_errors")


def main():
    path = REV / "report_generation.json"
    if path.exists():
        document = read_json(path)
        for row in document["figures"] + [document["manuscript"]]:
            checked(row)
        print("Phase30 presentation r2 reused/verified")
        return
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "svg.hashsalt": "phase30-r2-fixed"})
    scope = error_scope()
    write_once(REV / "error_scope.json", scope)
    figures = dataset_overview() + graph_paths() + validation_ablation() + test_errors(scope)
    parent = read_json(BASE / "report_generation.json")
    figures.extend(parent["figures"])
    old = (ROOT / "report/sections/05_knowledge_rag.md").read_text(encoding="utf-8")
    text_once(MANUSCRIPT, render_manuscript_r2(old))
    docs = [ref(p) for p in sorted((ROOT / "docs/ch5").glob("*.md"))]
    write_once(REV / "preserved_legacy_docs.json", {"files": docs, "modified": False})
    write_once(
        path,
        {
            "phase": 30,
            "revision": "presentation_r2",
            "status": "PASS",
            "supersedes": ref(BASE / "report_generation.json"),
            "manuscript": ref(MANUSCRIPT),
            "figures": figures,
            "error_scope": ref(REV / "error_scope.json"),
            "preserved_docs": ref(REV / "preserved_legacy_docs.json"),
            "new_test_evaluation_executed": False,
            "policy": "Original images/metrics/predictions/citations unchanged; correct fonts, legibility, graph edges and TEST/challenge prose scope only",
        },
    )
    print("Phase30 presentation r2:4 new figures +3 existing, manuscript generated")


if __name__ == "__main__":
    main()
