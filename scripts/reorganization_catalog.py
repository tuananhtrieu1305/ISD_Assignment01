"""Build Phase1 catalogs from restored bytes and the read-only live baseline."""
from __future__ import annotations

import ast
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/reorganization"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def destination(project, path):
    parts = path.split("/")
    if project in {"A05", "A06"}:
        return project + "/" + "/".join(parts[1:])
    if path.endswith(".ipynb"):
        if project == "A01" and path.startswith("Assignment01_"):
            return project + "/provenance/previous_notebooks/" + parts[-1]
        if project == "A04" and path.startswith("pipeline/"):
            return project + "/provenance/dependencies/A03/" + path
        return project + "/notebooks/" + parts[-1]
    if path.startswith("datasets/"):
        return project + "/" + path
    if project == "A01" and path in {"diabetes.csv", "vietnam_housing_dataset.csv"}:
        return project + "/datasets/" + ("diabetes/" if path == "diabetes.csv" else "housing_price/") + path
    if path.startswith("web/"):
        return project + "/web/" + ("frontend/" if project == "tieuluan1" else "reference_ui/") + path[4:]
    if path.startswith("backend/"):
        return project + "/web/" + ("backend/" if project == "tieuluan1" else "reference_backend/") + path[8:]
    if path.startswith("pipeline/") and project == "A04":
        return project + "/provenance/dependencies/A03/" + path
    if path.startswith(("pipeline/", "pipeline04/")):
        return project + "/artifacts/" + path
    if path.startswith("term_paper/"):
        tail = path[len("term_paper/"):]
        if tail.startswith("src/"):
            return project + "/src/term_paper/" + tail[4:]
        if tail.startswith("deployment/"):
            return project + "/web/legacy_runtime/" + tail[len("deployment/"):]
        return project + "/" + tail
    if path.startswith("neo4j_scripts/"):
        return project + "/src/" + path
    if path.startswith("mobile/"):
        return project + "/provenance/reference_mobile/" + path[7:]
    if project == "tieuluan1" and path == "README.md":
        return project + "/provenance/root_README.md"
    if path.endswith((".pdf", ".docx", ".html")) and "/" not in path:
        return project + "/report/" + path
    return project + "/" + path


def live_destination(path):
    if path.startswith("discovering_ai_agent/"):
        project = "agent01"
        tail = path[len("discovering_ai_agent/"):]
    elif path.startswith("agent02_assignment/"):
        project = "agent02"
        tail = path[len("agent02_assignment/"):]
    else:
        project = "tieuluan3"
        tail = path
    if tail.startswith("web-demo/"):
        tail = "web/" + tail[len("web-demo/"):]
        if project == "agent01" and tail.startswith("web/dist/"):
            tail = "web/" + tail[len("web/dist/"):]
    if project.startswith("agent"):
        if tail.startswith("data/"):
            tail = "datasets/" + tail[5:]
        if "/" not in tail and tail.endswith(".py"):
            tail = "src/" + tail
        return project, project + "/" + tail
    if path.startswith("apps/web/"):
        tail = "web/frontend/" + path[len("apps/web/"):]
    elif path.startswith("apps/api/"):
        tail = "web/backend/" + path[len("apps/api/"):]
    elif path.startswith("data/"):
        tail = "datasets/" + path[5:]
    elif path.startswith("experiments/notebooks/v3/"):
        tail = "notebooks/" + path[len("experiments/notebooks/v3/"):]
    elif path.startswith("experiments/notebooks/legacy/"):
        tail = "provenance/notebooks_legacy/" + path[len("experiments/notebooks/legacy/"):]
    return project, project + "/" + tail


def inspect_notebook(path, logical):
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    assert doc.get("nbformat") == 4 and isinstance(doc["cells"], list), logical
    errors = []
    code_count = 0
    magic_cells = []
    training = []
    imports = set()
    for index, cell in enumerate(doc["cells"]):
        if cell.get("cell_type") != "code":
            continue
        code_count += 1
        source = "".join(cell.get("source", []))
        if re.search(r"(?m)^\s*[!%]", source):
            magic_cells.append(index)
            source = "\n".join("" if re.match(r"\s*[!%]", line) else line for line in source.splitlines())
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(n.name.split(".")[0] for n in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
        except SyntaxError as exc:
            errors.append({"cell": index, "line": exc.lineno, "message": exc.msg})
        if re.search(r"\.fit\(|\btrain\(|run_training|TrainSession", source):
            training.append(index)
    outputs = [out for c in doc["cells"] if c.get("cell_type") == "code" for out in c.get("outputs", []) if out.get("output_type") == "error"]
    name = path.name.lower()
    if "discovering_ai_agent/notebooks/" in logical:
        role = "actual Q-learning training and plots; do not RunAll during migration"
    elif "agent02_assignment/notebooks/" in logical:
        role = "read-only sealed results/source/figures, no training"
    elif "experiments/notebooks/v3/" in logical:
        role = "checkpoint/results demo, not original training runner"
    elif "comparison" in name:
        role = "read saved comparisons/results; inspect guard/write behavior before RunAll"
    elif "fundamentals" in name:
        role = "fundamentals and toy/data demonstrations"
    elif "_data.ipynb" in name:
        role = "EDA and preprocessing"
    else:
        role = "historical training/evaluation pipeline; static check only"
    return {"path": logical, "sha256": digest(path), "cells": len(doc["cells"]), "code_cells": code_count, "imports": sorted(imports), "role": role, "mixed_tensorflow_torch_imports": {"tensorflow", "torch"}.issubset(imports), "training_signal_cells": training, "historical_error_outputs": [{"ename": r.get("ename"), "evalue": r.get("evalue")} for r in outputs], "static_syntax_errors": errors, "magic_cells_filtered_for_AST": magic_cells, "execution": "NOT_EXECUTED", "kernel": doc.get("metadata", {}).get("kernelspec")}


def csv_info(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(20000)
        handle.seek(0)
        sep = ";" if sample.splitlines()[0].count(";") > sample.splitlines()[0].count(",") else ","
        rows = csv.reader(handle, delimiter=sep)
        columns = next(rows)
        count = sum(1 for _ in rows)
    payload = path.read_bytes()
    return {"rows": count, "columns": columns, "delimiter": sep, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "crlf_equivalent_sha256": hashlib.sha256(payload.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()}


def main():
    restore = read("restoration_manifest.json")
    supplementary = read("supplementary_manifest.json")
    baseline = read("live_baseline_manifest.json")
    backup = read("backup_manifest.json")
    sourcefiles = restore["files"] + supplementary["files"]
    per_project = collections.defaultdict(list)
    notebook_audit = []
    python_audit = []
    mappings = []
    for row in sourcefiles:
        project = row["project"]
        per_project[project].append(row)
        target = destination(project, row["path"])
        mappings.append({"project": project, "source_kind": "git-restored", "source_commit": row["commit"], "old_path": row["path"], "physical_source": row["staging_path"], "new_path": target, "sha256": row["sha256"], "bytes": row["bytes"], "action": "copy-after-phase2-gates", "requires_revision_on_edit": True})
        path = ROOT / row["staging_path"]
        if row["path"].endswith(".ipynb"):
            notebook_audit.append(dict(inspect_notebook(path, row["staging_path"]), project=project, target=target))
        elif row["path"].endswith(".py"):
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"))
                status = "PASS"
            except SyntaxError as exc:
                status = str(exc)
            python_audit.append({"path": row["staging_path"], "AST": status, "executed": False})
    live = list(baseline["files"])
    # Root docs belong to V3 except the new reorganization work area.
    for path in sorted((ROOT / "docs").rglob("*")):
        if path.is_file() and OUT not in path.parents:
            live.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)})
    seen = set()
    for row in live:
        project, target = live_destination(row["path"])
        key = (project, row["path"])
        if key in seen:
            continue
        seen.add(key)
        per_project[project].append(row)
        mappings.append({"project": project, "source_kind": "live-original", "old_path": row["path"], "physical_source": row["path"], "new_path": target, "sha256": row["sha256"], "bytes": row["bytes"], "action": "relocate-after-phase2-gates", "requires_revision_on_edit": True})
    for row in backup["files"]:
        if row["nested_metadata"] or "/web-demo/" not in row["path"]:
            continue
        project, target = live_destination(row["path"])
        if (project, row["path"]) not in seen:
            per_project[project].append(row)
            mappings.append({"project": project, "source_kind": "uncommitted-preserved", "old_path": row["path"], "physical_source": row["path"], "new_path": target, "sha256": row["sha256"], "bytes": row["bytes"], "action": "relocate-after-phase2-gates", "requires_revision_on_edit": False})
            seen.add((project, row["path"]))
    for project, prefix in [("tieuluan3", "experiments/notebooks/v3"), ("agent01", "discovering_ai_agent/notebooks"), ("agent02", "agent02_assignment/notebooks")]:
        for path in sorted((ROOT / prefix).rglob("*.ipynb")):
            notebook_audit.append(dict(inspect_notebook(path, path.relative_to(ROOT).as_posix()), project=project))
    errors = [r for r in notebook_audit if r["static_syntax_errors"]]
    py_errors = [r for r in python_audit if r["AST"] != "PASS"]
    write("notebook_static_audit.json", {"notebooks": notebook_audit, "python_sources": python_audit, "notebook_count": len(notebook_audit), "restored_notebook_count": sum("staging/" in r["path"] for r in notebook_audit), "python_source_count": len(python_audit), "AST_failures": errors + py_errors, "training_executed": False, "historical_error_outputs_are_preserved": True})
    collisions = collections.defaultdict(list)
    for row in mappings:
        collisions[row["new_path"].casefold()].append(row)
    conflict = {key: vals for key, vals in collisions.items() if len({r["sha256"] for r in vals}) > 1}
    write("migration_map.json", {"schema": "assign.reorganization.map.v1", "status": "PROPOSED_NOT_APPLIED", "files": mappings, "file_count": len(mappings), "target_conflicts": conflict, "policy": "paths change only inPhase2; preserve original bytes before compatibility revisions; old locks use original logical paths via versioned resolver; never rewrite old seals", "tieuluan2": {"action": "derive-from-tieuluan3-in-phase2", "include_chapters": [1,2,3,4,5], "exclude": ["ch06_multi_agent", "ch6_*_tasks", "/agents", "multi_agent serving catalog and payload"], "provenance_not_a_historical_commit": True}})
    projects = []
    for project in ["A01","A02","A03","A04","A05","A06","tieuluan1","tieuluan2","tieuluan3","agent01","agent02"]:
        rows = per_project[project]
        notes_path = OUT / f"survey/{project}_notes.json"
        notes = json.loads(notes_path.read_text()) if notes_path.exists() else {}
        projects.append({"project": project, "source_kind": "derived" if project == "tieuluan2" else "git-restored" if project in ["A01","A02","A03","A04","A05","A06","tieuluan1"] else "live-preserved", "source_head": read("phase1_preflight.json")["head"] if not notes else None, "commits": sorted({r["commit"] for r in rows if "commit" in r}), "file_count": len(rows), "bytes": sum(r["bytes"] for r in rows), "restoration_status": "DERIVATION_PENDING_PHASE2" if project == "tieuluan2" else "RESTORED_EXACT_GIT_BLOBS" if notes else "LIVE_HASH_INVENTORIED_NOT_MOVED", "notebooks": [r for r in notebook_audit if r["project"] == project], "dependency_notes": f"survey/{project}_notes.json" if notes else "runtime_matrix.md and web_matrix.md", "dataset_status": "see dataset_catalog.json; source restoration is not runtime acceptance", "ready_to_run_all": False})
    write("source_inventory.json", {"schema": "assign.reorganization.inventory.v1", "head": read("phase1_preflight.json")["head"], "projects": projects, "restored_files": len(sourcefiles), "restored_bytes": sum(r["bytes"] for r in sourcefiles), "live_files": baseline["count"], "backup_members": len(backup["files"]), "source_originals_unchanged": "verify live_preservation_receipt.json", "notebook_runtime_acceptance": "Phase2; no notebook executed in Phase1", "selection_decisions": read("selection.json")["decisions"], "static_AST_failure_count": len(errors) + len(py_errors)})
    catalog = []

    def historical(project, name, paths, source, note=""):
        rows = [r for r in per_project[project] if r.get("staging_path") and any(r["path"] == p or p.endswith("/") and r["path"].startswith(p) for p in paths)]
        item = {"project": project, "dataset": name, "original_paths": paths, "source_reference": source, "availability": "RESTORED" if rows else "MISSING_ORIGINAL_FORMAT", "files": [{"path": r["staging_path"], "sha256": r["sha256"], "bytes": r["bytes"]} for r in rows], "file_count": len(rows), "bytes": sum(r["bytes"] for r in rows), "note": note, "split_policy": "preserve each assignment's split artifacts; do not substitute V3 splits"}
        if len(rows) <= 8:
            item["csv_observations"] = {r["path"]: csv_info(ROOT / r["staging_path"]) for r in rows if r["path"].endswith(".csv") and r["bytes"] < 30_000_000}
        catalog.append(item)

    historical("A01","Pima diabetes",["diabetes.csv"],"https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database")
    historical("A01","Vietnam house prices",["vietnam_housing_dataset.csv"],"notebook source/metadata; preserve the original local snapshot")
    historical("A02","Pima diabetes",["datasets/diabetes/diabetes.csv"],"same source family asA01, exact hash comparison required")
    historical("A02","Vietnam house prices",["datasets/housing_price/vietnam_housing_dataset.csv"],"notebook source/metadata")
    historical("A02","Customer behavior",["datasets/customer_behavior/"],"datasets/customer_behavior/README.md", "synthetic/source nature must follow historical README, do not call it Olist")
    historical("A03","CDC BRFSS2015 balanced diabetes",["datasets/diabetes/diabetes.csv"],"https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset")
    historical("A03","Vietnam house prices",["datasets/housing_price/vietnam_housing_dataset.csv"],"pipeline/house_price/metadata.json")
    historical("A03","Customer behavior",["datasets/customer_behavior/"],"datasets/customer_behavior/README.md")
    historical("A04","CDC BRFSS2021 binary",["datasets/diabetes/a04/"],"metadata.json in dataset directory")
    historical("A04","King County house sales",["datasets/housing_price/a04/"],"https://www.kaggle.com/datasets/harlfoxem/housesalesprediction")
    historical("A04","Olist churn derived",["datasets/customer_behavior/a04/"],"https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
    historical("A04","MNIST",["datasets/mnist/mnist.npz"],"https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz")
    historical("A04","CIFAR10 Python archive",["datasets/cifar10/cifar-10-python.tar.gz"],"https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz", "not in selected historical tree or local index; V3 binary-format archive exists but is not byte-identical/interchangeable; Phase2 acquire historical Python archive or implement validated explicit format adapter, never rename binary archive")
    historical("A05","CDC BRFSS2015 three-class",["A05/datasets/diabetes/"],"A05/report/dataset_audit.md")
    historical("A05","EuroSAT RGB",["A05/datasets/eurosat/"],"A05/README.md; retain all27000raw JPGs")
    historical("A05","Oxford-IIIT Pet classification",["A05/datasets/oxford_pets/"],"A05/README.md + official annotation txt", "7390rawimages;7349official samples;41outside annotation excluded by original experiment; trimaps/xmls not required for classification")
    historical("A06","UCI Online RetailII",["A06/datasets/customer/online_retail_II.xlsx"],"UCI dataset502; A06/PROJECT_SPEC.md")
    historical("A06","AAPL 2015–2025",["A06/datasets/stock/AAPL_2015_2025.csv"],"A06/PROJECT_SPEC.md; use fixed snapshot without downloading again")
    historical("A06","Original processed windows/scalers",["A06/datasets/processed/"],"A06/results/metrics/preprocessing_metadata.json", "retain original train/val/test, never regenerate while reorganizing")
    cards = [r for r in per_project["tieuluan1"] if r.get("path", "").startswith("term_paper/sources/dataset_cards/") and r["path"].endswith(".md") and not r["path"].endswith("README.md")]
    catalog.append({"project": "tieuluan1", "dataset": "original four-chapter dataset views", "availability": "RESTORED_CARDS_AND_PROCESSED_PAYLOADS_RAW_REFERENCES_REQUIRE_MAPPING", "cards": [{"path": r["staging_path"], "sha256": r["sha256"]} for r in cards], "raw_dependencies": ["A03 original CDC/Vietnam/customer snapshots", "A05 original EuroSAT/three-classCDC/Pet", "A06 original OnlineRetail/AAPL/windows"], "note": "follow card identity/sizes/splits; Git CSV LF vs original Windows CRLF can explain raw SHA mismatch; validate exact normalization before any materialization; no fit or new split"})
    v3 = json.loads((ROOT / "data/catalog_v3.json").read_text())
    for project in ("tieuluan3", "tieuluan2"):
        catalog.append({"project": project, "dataset": "V3 locked chapter views", "availability": "EXISTING_LOCAL_NOT_MOVED" if project == "tieuluan3" else "DERIVE_REFERENCES_PHASE2", "datasets": [r for r in v3["datasets"] if project == "tieuluan3" or r["chapter"] <= 5], "raw_storage": "data/raw/ch1–ch5/", "raw_index": "local_resource_index.json", "split_policy": "reuse frozen V3 split/scaler/IDs; no new TEST", "note": "ImageNet is metadata only; Wikidata structural browser is not a third QA benchmark"})
    catalog.append({"project": "agent01", "dataset": "10x10 maze defined in code", "availability": "EXISTING_LOCAL", "source": "discovering_ai_agent/experiment.py", "result": "discovering_ai_agent/evidence/results.json", "sha256": digest(ROOT / "discovering_ai_agent/experiment.py"), "note": "synthetic fixed maze, no external download"})
    catalog.append({"project": "agent02", "dataset": "e-commerce simulation + Gold TRAIN calibration", "availability": "EXISTING_LOCAL", "files": [{"path": p, "sha256": digest(ROOT / p), "bytes": (ROOT/p).stat().st_size} for p in ["agent02_assignment/data/derived/gold_train_prefix_v1.csv", "agent02_assignment/data/derived/gold_regime_kernel_v1.json"]], "note": "Gold proxy TRAINonly; do not use V3 future/TEST or force static diabetes/house data into causal RL"})
    write("dataset_catalog.json", {"schema": "assign.reorganization.datasets.v1", "datasets": catalog, "coverage": sorted({r["project"] for r in catalog}), "missing_original_format": [r for r in catalog if r.get("availability") == "MISSING_ORIGINAL_FORMAT"], "binary_archive_available": {"path": "data/raw/ch3/cifar10/cifar-10-binary.tar.gz", "sha256": digest(ROOT / "data/raw/ch3/cifar10/cifar-10-binary.tar.gz")}, "ready_for_training": False, "dataset_materialization": "Phase2 only; shared storage only for exact SHA256 identities"})
    print(json.dumps({"projects": len(projects), "mapped_files": len(mappings), "target_conflicts": len(conflict), "notebooks": len(notebook_audit), "restored_notebooks": sum("staging/" in r["path"] for r in notebook_audit), "python_sources": len(python_audit), "AST_failures": len(errors) + len(py_errors), "datasets": len(catalog)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
