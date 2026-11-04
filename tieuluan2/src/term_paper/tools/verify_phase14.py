"""Independent verifier for Phase 14 baseline artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from term_paper.tools.phase14_rag import prediction_metrics, validate_cache_manifest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def verify_phase14(workspace: Path) -> dict[str, Any]:
    base = workspace / "term_paper/knowledge_rag"
    manifest_path = base / "artifacts/manifests/phase14_baseline_manifest.json"
    if not manifest_path.exists():
        return {"status": "FAIL", "checks": [], "failures": ["missing phase14_baseline_manifest.json"]}
    failures: list[str] = []
    checks: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "checks": [], "failures": [f"invalid phase14_baseline_manifest.json: {exc}"]}
    required = [
        base / "config/phase14.json",
        base / "config/phase14_locked.json",
        base / "artifacts/metrics/phase14_metrics.json",
        base / "artifacts/metrics/phase14_metrics.csv",
        base / "artifacts/metrics/phase14_tuning.json",
        base / "notebooks/ch5_rag_baselines_b0_b2.ipynb",
        base / "artifacts/figures/phase14/retrieval_recall_at_k.svg",
        base / "artifacts/figures/phase14/answer_quality.svg",
        base / "artifacts/figures/phase14/latency.svg",
    ]
    for path in required:
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"missing or empty deliverable: {path.relative_to(workspace).as_posix()}")
    if not failures:
        checks.append("core deliverables present")
    config_hash = manifest.get("config_sha256")
    base_config_hash = manifest.get("base_config_sha256")
    if (base / "config/phase14.json").exists() and _sha256(base / "config/phase14.json") != base_config_hash:
        failures.append("base config hash mismatch")
    if (base / "config/phase14_locked.json").exists() and _sha256(base / "config/phase14_locked.json") != config_hash:
        failures.append("locked config hash mismatch")
    metrics: dict[str, Any] = {}
    metrics_path = base / "artifacts/metrics/phase14_metrics.json"
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            if metrics.get("config_sha256") != config_hash:
                failures.append("metrics config hash mismatch")
        except json.JSONDecodeError as exc:
            failures.append(f"invalid metrics JSON: {exc}")
    model_set: dict[str, set[str]] = {domain: set() for domain in ("medical", "finance")}
    for domain in ("medical", "finance"):
        index_manifest = base / f"data/processed/phase14/indexes/{domain}/cache_manifest.json"
        if not index_manifest.exists():
            failures.append(f"{domain}: missing cache manifest")
        else:
            try:
                cache = json.loads(index_manifest.read_text(encoding="utf-8"))
                expected_corpus = manifest.get("corpus_sha256", {}).get(domain)
                validate_cache_manifest(cache, expected_corpus, base_config_hash)
                for relative, expected_hash in cache["artifact_files"].items():
                    artifact_path = index_manifest.parent / relative
                    if not artifact_path.exists() or _sha256(artifact_path) != expected_hash:
                        failures.append(f"{domain}: cache artifact hash mismatch: {relative}")
            except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
                failures.append(f"{domain}: invalid cache manifest ({exc})")
        query_sets: dict[str, set[str]] = {}
        for model in ("B0", "B1", "B2"):
            prediction_path = base / f"artifacts/predictions/phase14/{domain}/{model}_validation.jsonl"
            if not prediction_path.exists():
                failures.append(f"{domain}/{model}: missing validation predictions")
                continue
            rows = _read_jsonl(prediction_path)
            model_set[domain].add(model)
            query_sets[model] = {str(row.get("query_id")) for row in rows}
            for row in rows:
                if row.get("config_sha256") != config_hash:
                    failures.append(f"{domain}/{model}: prediction config hash mismatch")
                    break
                ranked = set(row.get("ranked_chunk_ids", []))
                if any(citation not in ranked for citation in row.get("citations", [])):
                    failures.append(f"{domain}/{model}: fake citation")
                    break
                if row.get("corpus_sha256") != manifest.get("corpus_sha256", {}).get(domain):
                    failures.append(f"{domain}/{model}: prediction corpus hash mismatch")
                    break
            if rows:
                recomputed = prediction_metrics(rows, manifest.get("top_k", [1, 3, 5, 10]))
                stored = metrics.get("validation", {}).get(domain, {}).get(model, {})
                for key, value in recomputed.items():
                    if stored.get(key) != value:
                        failures.append(f"{domain}/{model}: metric drift for {key}")
                        break
            challenge_path = base / f"artifacts/predictions/phase14/{domain}/{model}_challenge.jsonl"
            if not challenge_path.exists():
                failures.append(f"{domain}/{model}: missing challenge predictions")
            else:
                challenge = _read_jsonl(challenge_path)
                if not challenge or any(not row.get("abstained") or row.get("citations") for row in challenge):
                    failures.append(f"{domain}/{model}: challenge abstention contract failed")
        if query_sets and len({frozenset(value) for value in query_sets.values()}) != 1:
            failures.append(f"{domain}: B0-B2 validation query sets differ")
        if model_set[domain] == {"B0", "B1", "B2"}:
            checks.append(f"{domain}: B0-B2 prediction rows validated")
    if manifest.get("test_split_status") != "SEALED_NOT_RUN":
        failures.append("TEST split was not kept sealed")
    else:
        checks.append("TEST remained sealed")
    prediction_root = base / "artifacts/predictions/phase14"
    if prediction_root.exists():
        for path in prediction_root.rglob("*.jsonl"):
            if "_test" in path.name.casefold():
                failures.append(f"forbidden TEST prediction artifact: {path.name}")
            elif any(row.get("split") in {"test", "private_test"} for row in _read_jsonl(path)):
                failures.append(f"forbidden TEST prediction row: {path.name}")
    notebook_path = base / "notebooks/ch5_rag_baselines_b0_b2.ipynb"
    if notebook_path.exists():
        try:
            notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
            code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
            if not code_cells or any(cell.get("execution_count") is None for cell in code_cells):
                failures.append("notebook is not fully executed")
            if any(output.get("output_type") == "error" for cell in code_cells for output in cell.get("outputs", [])):
                failures.append("notebook contains execution error")
            if code_cells and not failures:
                checks.append("notebook execution state validated")
        except json.JSONDecodeError as exc:
            failures.append(f"invalid notebook JSON: {exc}")
    for artifact in manifest.get("artifacts", []):
        path = workspace / artifact.get("path", "")
        if not path.exists():
            failures.append(f"manifest artifact missing: {artifact.get('path')}")
            continue
        if artifact.get("size_bytes") != path.stat().st_size or artifact.get("sha256") != _sha256(path):
            failures.append(f"manifest integrity mismatch: {artifact.get('path')}")
    if manifest.get("artifacts"):
        checks.append("artifact hashes validated")
    return {"status": "PASS" if not failures else "FAIL", "checks": checks, "failures": failures}


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = verify_phase14(workspace)
    output = workspace / "term_paper/knowledge_rag/artifacts/manifests/phase14_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
