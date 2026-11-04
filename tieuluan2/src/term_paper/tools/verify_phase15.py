"""Independent integrity and reproducibility verifier for Phase 15."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from term_paper.tools.phase14_rag import prediction_metrics


DOMAINS = ("medical", "finance")
MODELS = ("B0", "B1", "B2", "B3", "B4")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _required_deliverables(base: Path) -> list[Path]:
    figures = (
        "test_recall_at_5.svg", "test_mrr_at_10.svg", "test_answer_f1.svg",
        "test_latency_p95.svg", "validation_ablation.svg", "error_distribution.svg",
    )
    paths = [
        base / "config/phase15.json",
        base / "config/phase15_locked.json",
        base / "artifacts/manifests/phase15_validation_manifest.json",
        base / "artifacts/manifests/phase15_test_run.json",
        base / "artifacts/metrics/phase15_tuning.json",
        base / "artifacts/metrics/phase15_validation_metrics.json",
        base / "artifacts/metrics/phase15_ablation_validation.csv",
        base / "artifacts/metrics/phase15_test_metrics.json",
        base / "artifacts/metrics/phase15_test_metrics.csv",
        base / "artifacts/metrics/phase15_bootstrap_ci.csv",
        base / "artifacts/metrics/phase15_error_analysis.csv",
        base / "artifacts/metrics/phase15_case_studies.jsonl",
        base / "notebooks/ch5_kgrag_b0_b4.ipynb",
        base / "phase15_experiment_report.md",
    ]
    paths.extend(base / "artifacts/figures/phase15" / name for name in figures)
    return paths


def _validate_notebook(path: Path, failures: list[str], checks: list[str]) -> None:
    if not path.exists():
        return
    try:
        notebook = _read_json(path)
        code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
        if not code_cells or any(cell.get("execution_count") is None for cell in code_cells):
            failures.append("notebook is not fully executed")
        elif any(output.get("output_type") == "error" for cell in code_cells for output in cell.get("outputs", [])):
            failures.append("notebook contains an execution error")
        else:
            checks.append("executed notebook validated")
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"invalid notebook JSON: {exc}")


def _validate_prediction_row(
    row: Mapping[str, Any], domain: str, model: str, locked_hash: str, expected_split: str
) -> str | None:
    if row.get("domain") != domain or row.get("model_id") != model:
        return "domain/model mismatch"
    if row.get("split") != expected_split or row.get("split") == "private_test":
        return "forbidden or incorrect split"
    if row.get("config_sha256") != locked_hash:
        return "locked config hash mismatch"
    ranked = list(row.get("ranked_chunk_ids", []))
    if any(citation not in ranked for citation in row.get("citations", [])):
        return "citation is absent from retrieved evidence"
    if not isinstance(row.get("input_artifact_hashes"), dict) or not row["input_artifact_hashes"]:
        return "missing input artifact provenance"
    return None


def verify_phase15(workspace: Path) -> dict[str, Any]:
    base = workspace / "term_paper/knowledge_rag"
    manifest_path = base / "artifacts/manifests/phase15_experiment_manifest.json"
    if not manifest_path.exists():
        return {"status": "FAIL", "checks": [], "failures": ["missing phase15_experiment_manifest.json"]}
    failures: list[str] = []
    checks: list[str] = []
    try:
        manifest = _read_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "checks": [], "failures": [f"invalid phase15_experiment_manifest.json: {exc}"]}

    for path in _required_deliverables(base):
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"missing or empty deliverable: {path.relative_to(workspace).as_posix()}")
    if not failures:
        checks.append("core deliverables present")

    if manifest.get("status") != "PASS":
        failures.append("manifest status is not PASS")
    if manifest.get("models") != list(MODELS) or manifest.get("domains") != list(DOMAINS):
        failures.append("manifest model/domain contract mismatch")
    if manifest.get("test_run_count") != 1 or manifest.get("test_run_status") != "COMPLETE":
        failures.append("manifest does not record exactly one completed TEST run")

    locked_path = base / "config/phase15_locked.json"
    locked_hash = _sha256(locked_path) if locked_path.exists() else ""
    if locked_hash != manifest.get("locked_config_sha256"):
        failures.append("locked config hash mismatch")

    run_path = base / "artifacts/manifests/phase15_test_run.json"
    run: dict[str, Any] = {}
    if run_path.exists():
        try:
            run = _read_json(run_path)
            if run.get("status") != "COMPLETE" or run.get("run_count") != 1:
                failures.append("TEST run manifest is not COMPLETE with run_count=1")
            if run.get("locked_config_sha256") != locked_hash:
                failures.append("TEST run locked config hash mismatch")
            if run.get("query_set_sha256") != manifest.get("test_query_set_sha256"):
                failures.append("TEST query-set hash mismatch")
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"invalid TEST run manifest: {exc}")

    metrics_path = base / "artifacts/metrics/phase15_test_metrics.json"
    metrics: dict[str, Any] = {}
    if metrics_path.exists():
        try:
            metrics = _read_json(metrics_path)
            if metrics.get("config_sha256") != locked_hash:
                failures.append("metrics locked config hash mismatch")
            if metrics.get("test_run_status") != "COMPLETE_ONE_SHOT":
                failures.append("metrics do not record the one-shot TEST contract")
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"invalid TEST metrics JSON: {exc}")

    prediction_hashes = {item.get("path"): item.get("sha256") for item in run.get("prediction_artifacts", [])}
    for domain in DOMAINS:
        query_sets: dict[str, set[str]] = {}
        for model in MODELS:
            path = base / f"artifacts/predictions/phase15/{domain}/{model}_test.jsonl"
            if not path.exists():
                failures.append(f"missing TEST predictions: {domain}/{model}")
                continue
            try:
                rows = _read_jsonl(path)
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"invalid TEST predictions {domain}/{model}: {exc}")
                continue
            if not rows:
                failures.append(f"empty TEST predictions: {domain}/{model}")
                continue
            query_sets[model] = {str(row.get("query_id")) for row in rows}
            for row in rows:
                issue = _validate_prediction_row(row, domain, model, locked_hash, "test")
                if issue:
                    failures.append(f"{domain}/{model}: {issue}")
                    break
            relative = path.relative_to(workspace).as_posix()
            if prediction_hashes.get(relative) != _sha256(path):
                failures.append(f"{domain}/{model}: TEST prediction hash mismatch")
            if rows and metrics:
                recomputed = prediction_metrics(rows, manifest.get("top_k", [1, 3, 5, 10]))
                stored = metrics.get("test", {}).get(domain, {}).get(model, {})
                for key, value in recomputed.items():
                    if stored.get(key) != value:
                        failures.append(f"{domain}/{model}: metric drift for {key}")
                        break
        if query_sets and len({frozenset(ids) for ids in query_sets.values()}) != 1:
            failures.append(f"{domain}: B0-B4 TEST query sets differ")
        elif set(query_sets) == set(MODELS):
            checks.append(f"{domain}: B0-B4 TEST rows and metrics validated")

        for model in ("B3", "B4"):
            challenge_path = base / f"artifacts/predictions/phase15/{domain}/{model}_challenge.jsonl"
            if not challenge_path.exists():
                failures.append(f"missing challenge predictions: {domain}/{model}")
                continue
            challenge = _read_jsonl(challenge_path)
            if not challenge:
                failures.append(f"empty challenge predictions: {domain}/{model}")
                continue
            for row in challenge:
                issue = _validate_prediction_row(row, domain, model, locked_hash, "challenge")
                if issue:
                    failures.append(f"{domain}/{model} challenge: {issue}")
                    break
            stored = metrics.get("challenge", {}).get(domain, {}).get(model, {})
            expected_matches = sum(
                row.get("expected_behavior") == "abstain" and row.get("abstained") and not row.get("citations")
                for row in challenge
            ) / len(challenge)
            if stored.get("expected_behavior_match_rate") != round(expected_matches, 6):
                failures.append(f"{domain}/{model}: challenge metric drift")

    _validate_notebook(base / "notebooks/ch5_kgrag_b0_b4.ipynb", failures, checks)

    for artifact in manifest.get("artifacts", []):
        path = workspace / str(artifact.get("path", ""))
        if not path.exists():
            failures.append(f"manifest artifact missing: {artifact.get('path')}")
        elif artifact.get("size_bytes") != path.stat().st_size or artifact.get("sha256") != _sha256(path):
            failures.append(f"manifest integrity mismatch: {artifact.get('path')}")
    if manifest.get("artifacts"):
        checks.append("artifact hashes validated")

    prediction_root = base / "artifacts/predictions/phase15"
    if prediction_root.exists():
        for path in prediction_root.rglob("*.jsonl"):
            if any(row.get("split") == "private_test" for row in _read_jsonl(path)):
                failures.append(f"forbidden private_test row: {path.relative_to(workspace).as_posix()}")

    return {"status": "PASS" if not failures else "FAIL", "checks": checks, "failures": failures}


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = verify_phase15(workspace)
    output = workspace / "term_paper/knowledge_rag/artifacts/manifests/phase15_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
