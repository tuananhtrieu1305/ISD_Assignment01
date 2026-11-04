"""Generate V3 contracts, trusted CPU notebook smoke and saved-evidence manuscript."""

import argparse
import contextlib
import io
import json
import platform
import resource
import runpy
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import numpy as np
import scipy
import sklearn

from src.ch05_knowledge_rag.catalog import catalog, pipeline_contract, validate_pipeline
from src.ch05_knowledge_rag.preservation import BASE, ROOT, checked, ref, verify_records
from src.ch05_knowledge_rag.reporting import historical_metrics, render_manuscript
from src.ch05_knowledge_rag.service import DATASETS, METHODS, KgRagService
from src.common.artifact_core import write_once
from src.common.contracts import canonical_sha256, read_json

NOTEBOOKS = ROOT / "experiments/notebooks/v3/ch05_knowledge_rag"
MANUSCRIPT = ROOT / "report/sections/v3/ch05_knowledge_rag.md"


def text_once(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = text.encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError(
                "Existing generated content differs; inspect/version, never overwrite: " + path.name
            )
    else:
        with path.open("xb") as stream:
            stream.write(encoded)


def contracts():
    write_once(BASE / "catalog.json", catalog())
    models = []
    for dataset in DATASETS:
        for method in METHODS:
            contract = pipeline_contract(dataset, method)
            validate_pipeline(contract)
            path = BASE / "contracts" / dataset / method / "model_contract.json"
            write_once(path, contract)
            models.append(
                {
                    "model_id": contract["model_id"],
                    "dataset_id": dataset,
                    "method": method,
                    "contract": ref(path),
                    "available": contract["available"],
                    "lifecycle": contract["lifecycle"],
                    "new_training_executed": False,
                }
            )
    write_once(
        BASE / "reused_registry.json",
        {"phase": 30, "models": models, "initialized_registry_replaced": False, "public_test_rerun": False},
    )
    print("Phase30: catalog/15 contract slots (10 QA +5 unavailable structural) PASS", flush=True)


def notebook_source(dataset):
    prelude = "from pathlib import Path\nimport sys\nroot = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())\nif str(root) not in sys.path: sys.path.insert(0, str(root))\n"
    if dataset == DATASETS[2]:
        code = (
            prelude
            + "from src.ch05_knowledge_rag.structural import inspect_entity\nfrom src.common.contracts import read_json\nindex = read_json(root / 'data/raw/ch5/wikidata/snapshot_index.json')\nresult = [inspect_entity(r['qid']) for r in index['entities']]\nfor row in result: print(row['qid'], row['revision_id'], row['claim_count'], row['citation']['source_sha256'])\nassert len(result) == 10 and sum(r['claim_count'] for r in result) == 2056\nassert all(not r['qa_benchmark'] for r in result)\n"
        )
    else:
        code = (
            prelude
            + f"from src.ch05_knowledge_rag.service import KgRagService, sample_request\nservice = globals().get('phase30_service') or KgRagService()\nrequest = sample_request({dataset!r})\nresult = service.compare(request)\nassert result['job']['status'] == 'succeeded'\nassert result['job']['comparison_valid']\nassert len(result['job']['results']) == 5\nfor row in result['job']['results']:\n    print(row['implementation'], row['actual_backend'], row['actual_device'], row['prediction']['abstained'], row['prediction']['text'], row['prediction']['citations'])\nassert not result['public_test_evaluation_executed']\n"
        )
    code += "assert not any(name in sys.modules for name in ('torch','tensorflow','keras'))\nprint('No TEST evaluation, fit, download or external API call executed.')\n"
    return code


def demo_export():
    export_path = BASE / "export.json"
    if export_path.exists():
        document = read_json(export_path)
        verify_records(document["artifacts"])
        print("Phase30: existing demo export verified, not re-executed", flush=True)
        return
    service = KgRagService()
    started = time.perf_counter()
    bundle = service.runtime.get()
    cold_seconds = time.perf_counter() - started
    files = [ref(BASE / "catalog.json"), ref(BASE / "reused_registry.json")]
    for dataset in DATASETS:
        receipt_path = BASE / "demos" / f"{dataset}_receipt.json"
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            verify_records(receipt["artifacts"])
            files.extend(receipt["artifacts"])
            continue
        code = notebook_source(dataset)
        script_path = BASE / "demos" / f"{dataset}_generated_cells.py"
        text_once(script_path, code)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            # Code is generated above from fixed allowlisted dataset IDs, not an uploaded notebook.
            namespace = runpy.run_path(str(script_path), init_globals={"phase30_service": service})
        result = namespace["result"]
        output = BASE / "demos" / f"{dataset}.json"
        write_once(output, result)
        title = (
            "Snapshot Wikidata: cấu trúc, không phải QA TEST"
            if dataset == DATASETS[2]
            else f"KG–RAG / {dataset}: B0–B4 CPU"
        )
        cells = [
            nbformat.v4.new_markdown_cell(
                f"# {title}\n\nDemo dùng snapshot/index đã khóa, không fit hoặc mở TEST. Medical là câu minh họa tự soạn không gán split; FinQA là câu TRAIN từ EDA card. Wikidata chỉ duyệt entity/revision/hash. Chạy trong kernel WSL V3; không cần API key. Graph compact/free-question không đồng nhất evaluator TEST lịch sử; timing không phải benchmark độc lập. Không tư vấn y khoa/tài chính."
            ),
            nbformat.v4.new_code_cell(code),
        ]
        for index, cell in enumerate(cells):
            cell["id"] = canonical_sha256([dataset, index])[:16]
        notebook = nbformat.v4.new_notebook(cells=cells)
        notebook.metadata["kernelspec"] = {
            "display_name": "Python V3 (WSL CPU tools)",
            "language": "python",
            "name": "python3",
        }
        notebook.cells[1]["execution_count"] = 1
        notebook.cells[1]["outputs"] = [
            nbformat.v4.new_output("stream", name="stdout", text=stdout.getvalue())
        ]
        path = NOTEBOOKS / (dataset + ".ipynb")
        text_once(path, nbformat.writes(notebook))
        execution = BASE / "demos" / f"{dataset}_execution.json"
        write_once(
            execution,
            {
                "status": "PASS",
                "dataset_id": dataset,
                "code": ref(script_path),
                "notebook": ref(path),
                "stdout": stdout.getvalue(),
                "execution": "runpy of generator-owned cells; Jupyter UI/kernel picker not tested",
                "new_test_evaluation_executed": False,
            },
        )
        records = [ref(output), ref(script_path), ref(path), ref(execution)]
        write_once(receipt_path, {"status": "PASS", "artifacts": records})
        files.extend(records + [ref(receipt_path)])
        print("Phase30: CPU notebook smoke PASS " + dataset, flush=True)
    runtime = BASE / "runtime_compatibility.json"
    write_once(
        runtime,
        {
            "status": "PASS",
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "bundle": ref(ROOT / "apps/api/models/kg_manifest.json"),
            "index_classes": {
                domain: {
                    key: type(index).__module__ + "." + type(index).__name__ for key, index in rows.items()
                }
                for domain, rows in bundle.indexes.items()
            },
            "chunk_counts": {domain: len(rows) for domain, rows in bundle.chunks.items()},
            "cold_load_seconds": cold_seconds,
            "peak_lifetime_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "telemetry_scope": "Whole exporter process high-water RSS; not per-method benchmark, no GPU used",
            "reserialized_or_refitted": False,
            "new_test_evaluation_executed": False,
        },
    )
    files.append(ref(runtime))
    write_once(
        export_path,
        {
            "phase": 30,
            "status": "PASS",
            "notebooks_executed": 3,
            "qa_slots_executed": 10,
            "wikidata_entities_inspected": 10,
            "new_test_evaluation_executed": False,
            "actual_backend": "NumPy CPU QA / local JSON structural browser",
            "artifacts": files,
        },
    )


def figures(rows):
    output = ROOT / "artifacts/figures/phase30"
    output.mkdir(parents=True, exist_ok=True)
    colors = ["#24558c", "#6495b1", "#bc8f32", "#6d597a", "#388078"]
    evidence = []
    plt.rcParams.update({"font.size": 10, "svg.hashsalt": "phase30-historical-fixed"})
    for key, metric, title, ylabel in (
        (
            "historical_recall",
            "chunk_recall_at_5",
            "Historical public TEST: retrieval quality",
            "Chunk Recall@5",
        ),
        (
            "historical_latency",
            "latency_ms_p95",
            "Historical public TEST: latency (not V3 remeasurement)",
            "p95 milliseconds",
        ),
        (
            "historical_citations",
            "citation_gold_precision",
            "Historical public TEST: valid reference ≠ gold evidence",
            "Fraction",
        ),
    ):
        paths = [output / (key + suffix) for suffix in (".png", ".svg")]
        if any(path.exists() for path in paths):
            raise ValueError("Existing figure requires inspection, not overwrite")
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.1), layout="constrained")
        for ax, domain in zip(axes, ("medical", "finance")):
            values = [
                next(r for r in rows if r["domain"] == domain and r["model_id"] == method)
                for method in METHODS
            ]
            points = [float(r[metric]) for r in values]
            x = np.arange(5)
            if key == "historical_citations":
                ax.bar(
                    x - 0.18,
                    [float(r["citation_validity"]) for r in values],
                    0.35,
                    color="#a6bac4",
                    label="Validity",
                )
                bars = ax.bar(x + 0.18, points, 0.35, color="#24558c", label="Gold precision")
                ax.legend(loc="upper right", fontsize=8, ncol=2)
            else:
                bars = ax.bar(x, points, color=colors, width=0.7)
            ax.bar_label(bars, fmt="%.3f" if key != "historical_latency" else "%.2f", padding=3, fontsize=8)
            ax.set(
                title=f"{domain} (n={62 if domain == 'medical' else 1147} queries)",
                ylabel=ylabel,
                xticks=x,
                xticklabels=METHODS,
            )
            ax.set_ylim(
                0, 140 if key == "historical_latency" else (1.25 if key == "historical_citations" else 1.05)
            )
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(axis="y", alpha=0.15)
            ax.set_axisbelow(True)
        fig.suptitle(title, fontsize=12)
        fig.savefig(paths[0], dpi=300)
        fig.savefig(paths[1], metadata={"Date": None})
        plt.close(fig)
        evidence.extend(ref(p) for p in paths)
    return evidence


def report():
    path = BASE / "report_generation.json"
    if path.exists():
        result = read_json(path)
        for row in result["figures"] + [result["manuscript"]]:
            checked(row)
        print("Phase30: existing report verified", flush=True)
        return
    metrics = historical_metrics()
    write_once(BASE / "historical_consistency.json", metrics)
    charts = figures(metrics["rows"])
    old = ROOT / "report/sections/05_knowledge_rag.md"
    text_once(MANUSCRIPT, render_manuscript(old.read_text(encoding="utf-8")))
    write_once(
        path,
        {
            "phase": 30,
            "status": "PASS",
            "historical_consistency": ref(BASE / "historical_consistency.json"),
            "original_manuscript": ref(old),
            "manuscript": ref(MANUSCRIPT),
            "figures": charts,
            "new_test_evaluation_executed": False,
            "docx_rendered": False,
        },
    )
    write_once(
        BASE / "active_report.json",
        {"revision": "v3_kg_rag_1", "generation": ref(path), "manuscript": ref(MANUSCRIPT)},
    )
    print("Phase30: manuscript /3 PNG+SVG figures generated from saved metrics", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("contracts", "demo", "report", "all"), default="all")
    args = parser.parse_args()
    if not (BASE / "preserved_snapshot.json").exists():
        raise ValueError("Preservation snapshot must PASS first")
    for name, operation in (("contracts", contracts), ("demo", demo_export), ("report", report)):
        if args.stage in {name, "all"}:
            operation()
    print(json.dumps({"phase": 30, "stage": args.stage, "status": "PASS", "test_evaluation_executed": False}))


if __name__ == "__main__":
    main()
