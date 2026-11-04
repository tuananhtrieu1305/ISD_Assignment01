"""Acquire Wikidata snapshots and build the measured Phase 11 source audit."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from term_paper.tools.phase11_data import (
    aggregate_manifest_sha256,
    audit_finqa_directory,
    audit_medquad_directory,
    build_raw_manifest_rows,
    parse_medquad_xml,
    parse_wikidata_entity,
    sha256_file,
)


USER_AGENT = "AI-Term-Paper-KG-RAG/1.0 (academic reproducibility snapshot)"
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
WIKIDATA_TERMS = {
    "medical": (
        "diabetes mellitus",
        "type-1 diabetes",
        "type 2 diabetes",
        "insulin",
        "hyperglycemia",
    ),
    "finance": (
        "financial statement",
        "annual report",
        "revenue",
        "net income",
        "Apple Inc.",
    ),
}


def _fetch_json(url: str, attempts: int = 4) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt + 1 == attempts:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def _search_wikidata(term: str) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        {
            "action": "wbsearchentities",
            "search": term,
            "language": "en",
            "uselang": "en",
            "type": "item",
            "limit": 10,
            "format": "json",
        }
    )
    return _fetch_json(f"{WIKIDATA_SEARCH_URL}?{query}")


def _choose_search_result(term: str, payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("search") or []
    def matches(item: dict[str, Any]) -> bool:
        candidates = [item.get("label", ""), *(item.get("aliases") or [])]
        match = item.get("match") or {}
        candidates.append(match.get("text", ""))
        return any(str(value).casefold() == term.casefold() for value in candidates)

    exact = [item for item in results if matches(item)]
    if not exact:
        raise ValueError(f"No exact Wikidata label match for {term!r}")
    return exact[0]


def acquire_wikidata(raw_root: Path, acquired_at: str) -> dict[str, Any]:
    wikidata_root = raw_root / "wikidata"
    entities_root = wikidata_root / "entities"
    searches_root = wikidata_root / "searches"
    index_path = wikidata_root / "snapshot_index.json"
    if index_path.is_file():
        return json.loads(index_path.read_text(encoding="utf-8"))

    entities_root.mkdir(parents=True, exist_ok=True)
    searches_root.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    used_qids: set[str] = set()
    for domain, terms in WIKIDATA_TERMS.items():
        for position, term in enumerate(terms, start=1):
            search_payload = _search_wikidata(term)
            search_path = searches_root / f"{domain}_{position:02d}.json"
            search_path.write_text(json.dumps(search_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            selected = _choose_search_result(term, search_payload)
            qid = str(selected["id"])
            if qid in used_qids:
                raise ValueError(f"Duplicate QID selected for narrow snapshot: {qid}")
            used_qids.add(qid)
            endpoint = WIKIDATA_ENTITY_URL.format(qid=qid)
            payload = _fetch_json(endpoint)
            entity_path = entities_root / f"{qid}.json"
            entity_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            parsed = parse_wikidata_entity(payload, expected_qid=qid)
            records.append(
                {
                    "domain": domain,
                    "search_term": term,
                    "selected_qid": qid,
                    "selected_search_label": selected.get("label"),
                    "entity_endpoint": endpoint,
                    "entity_relative_path": entity_path.relative_to(raw_root).as_posix(),
                    "entity_sha256": sha256_file(entity_path),
                    **parsed,
                }
            )
            time.sleep(0.2)
    index = {
        "schema_version": 1,
        "acquired_at": acquired_at,
        "official_api": WIKIDATA_SEARCH_URL,
        "data_access_page": "https://www.wikidata.org/wiki/Wikidata:Data_access",
        "license": "CC0 1.0",
        "user_agent": USER_AGENT,
        "acquisition_mode": "narrow_entity_snapshots",
        "full_dump_used": False,
        "entities": records,
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def _git_value(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def _source_snapshot(repo: Path) -> dict[str, Any]:
    metadata_path = repo / "source_snapshot.json"
    if metadata_path.is_file():
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    if (repo / ".git").is_dir():
        return {
            "commit_sha": _git_value(repo, "rev-parse", "HEAD"),
            "commit_time": _git_value(repo, "log", "-1", "--format=%cI"),
        }
    raise FileNotFoundError(f"Missing source_snapshot.json and Git metadata: {repo}")


def _raw_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    )


def _dataset_manifest_hash(rows: list[dict[str, Any]], dataset_id: str) -> str:
    return aggregate_manifest_sha256(row for row in rows if row["dataset_id"] == dataset_id)


def _medquad_examples(root: Path) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.xml")):
        for row in parse_medquad_xml(path.read_text(encoding="utf-8"), path.relative_to(root).as_posix()):
            if row["answer"] and len(row["question"] or "") < 180:
                examples.append(
                    {
                        "source_file": row["source_file"],
                        "question": row["question"],
                        "answer_excerpt": row["answer"][:240],
                        "focus": row["focus"],
                        "question_type": row["question_type"],
                    }
                )
            if len(examples) == 2:
                return examples
    return examples


def _finqa_examples(root: Path) -> list[dict[str, Any]]:
    data = json.loads((root / "train.json").read_text(encoding="utf-8"))
    examples = []
    for item in data[:2]:
        qa = item.get("qa") or {}
        examples.append(
            {
                "id": item.get("id"),
                "question": qa.get("question"),
                "answer": qa.get("exe_ans"),
                "program": qa.get("program"),
                "gold_evidence_count": len(qa.get("gold_inds") or {}),
            }
        )
    return examples


def _wikidata_audit(index: dict[str, Any]) -> dict[str, Any]:
    entities = index["entities"]
    domain_distribution = Counter(item["domain"] for item in entities)
    return {
        "acquisition_mode": index["acquisition_mode"],
        "full_dump_used": index["full_dump_used"],
        "entity_count": len(entities),
        "domain_distribution": dict(sorted(domain_distribution.items())),
        "revision_ids": {item["selected_qid"]: item["revision_id"] for item in entities},
        "claim_count": sum(item["claim_count"] for item in entities),
        "property_count": sum(item["property_count"] for item in entities),
        "claim_count_by_entity": {item["selected_qid"]: item["claim_count"] for item in entities},
        "entities": [
            {
                key: item[key]
                for key in ("domain", "search_term", "selected_qid", "label_en", "description_en", "revision_id", "modified", "claim_count")
            }
            for item in entities
        ],
    }


def _write_figures(workspace: Path, audit: dict[str, Any]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = workspace / "term_paper/knowledge_rag/artifacts/figures/phase11"
    out.mkdir(parents=True, exist_ok=True)
    specifications = [
        (
            "medquad_question_types.png",
            audit["medquad"]["question_type_distribution"],
            "MedQuAD: top question types",
            "QA pairs",
            12,
        ),
        (
            "finqa_split_distribution.png",
            audit["finqa"]["qa_split_distribution"],
            "FinQA: QA examples by official split",
            "QA examples",
            None,
        ),
        (
            "wikidata_claim_distribution.png",
            audit["wikidata"]["claim_count_by_entity"],
            "Wikidata narrow snapshot: claims by entity",
            "Claims",
            None,
        ),
    ]
    for filename, values, title, ylabel, limit in specifications:
        items = sorted(values.items(), key=lambda pair: pair[1], reverse=True)
        if limit:
            items = items[:limit]
        labels = [item[0] for item in items]
        counts = [item[1] for item in items]
        fig, axis = plt.subplots(figsize=(9, 4.8))
        axis.bar(labels, counts, color="#2563eb")
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.tick_params(axis="x", rotation=42)
        axis.grid(axis="y", alpha=0.22)
        fig.tight_layout()
        fig.savefig(out / filename, dpi=180)
        plt.close(fig)


def build(workspace: Path) -> dict[str, Any]:
    acquired_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    raw_root = workspace / "term_paper/knowledge_rag/data/raw"
    medquad_root = raw_root / "medquad"
    finqa_root = raw_root / "finqa"
    medquad_source = _source_snapshot(medquad_root)
    finqa_source = _source_snapshot(finqa_root)
    wikidata_index = acquire_wikidata(raw_root, acquired_at)

    dataset_roots = {"medquad": medquad_root, "finqa": finqa_root, "wikidata": raw_root / "wikidata"}
    rows: list[dict[str, Any]] = []
    for dataset_id, root in dataset_roots.items():
        rows.extend(build_raw_manifest_rows(workspace, _raw_files(root), dataset_id=dataset_id))

    manifest_root = workspace / "term_paper/knowledge_rag/artifacts/manifests"
    metrics_root = workspace / "term_paper/knowledge_rag/artifacts/metrics"
    manifest_root.mkdir(parents=True, exist_ok=True)
    metrics_root.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_root / "raw_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("dataset_id", "relative_path", "size_bytes", "sha256"))
        writer.writeheader()
        writer.writerows(rows)

    medquad_audit = audit_medquad_directory(medquad_root)
    finqa_audit = audit_finqa_directory(finqa_root / "dataset")
    medquad_audit["examples"] = _medquad_examples(medquad_root)
    finqa_audit["examples"] = _finqa_examples(finqa_root / "dataset")
    audit = {
        "schema_version": 1,
        "generated_at": acquired_at,
        "medquad": medquad_audit,
        "finqa": finqa_audit,
        "wikidata": _wikidata_audit(wikidata_index),
    }
    audit_path = metrics_root / "phase11_data_audit.json"
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_figures(workspace, audit)

    sources = {
        "medquad": {
            "official_url": "https://github.com/abachaa/MedQuAD",
            "commit_sha": medquad_source["commit_sha"],
            "commit_time": medquad_source["commit_time"],
            "license": "CC BY 4.0",
            "license_evidence": "term_paper/knowledge_rag/data/raw/medquad/readme.txt and LICENSE.txt",
            "physical_size_bytes": sum(path.stat().st_size for path in _raw_files(medquad_root)),
            "file_count": len(_raw_files(medquad_root)),
            "manifest_sha256": _dataset_manifest_hash(rows, "medquad"),
        },
        "finqa": {
            "official_url": "https://github.com/czyssrs/FinQA",
            "paper_url": "https://aclanthology.org/2021.emnlp-main.300/",
            "commit_sha": finqa_source["commit_sha"],
            "commit_time": finqa_source["commit_time"],
            "license": "MIT",
            "license_evidence": "term_paper/knowledge_rag/data/raw/finqa/LICENSE",
            "physical_size_bytes": sum(path.stat().st_size for path in _raw_files(finqa_root)),
            "file_count": len(_raw_files(finqa_root)),
            "manifest_sha256": _dataset_manifest_hash(rows, "finqa"),
        },
        "wikidata": {
            "official_url": "https://www.wikidata.org/wiki/Wikidata:Data_access",
            "api_url": WIKIDATA_SEARCH_URL,
            "license": "CC0 1.0",
            "license_evidence": "https://www.wikidata.org/wiki/Wikidata:Copyright",
            "revision_ids": audit["wikidata"]["revision_ids"],
            "physical_size_bytes": sum(path.stat().st_size for path in _raw_files(raw_root / "wikidata")),
            "file_count": len(_raw_files(raw_root / "wikidata")),
            "manifest_sha256": _dataset_manifest_hash(rows, "wikidata"),
        },
    }
    snapshot = {
        "schema_version": 1,
        "acquired_at": acquired_at,
        "raw_immutability_policy": "Files listed in raw_manifest.csv are immutable; any content change requires a new snapshot and manifest.",
        "aggregate_manifest_sha256": aggregate_manifest_sha256(rows),
        "sources": sources,
    }
    snapshot_path = manifest_root / "phase11_snapshot_manifest.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"audit": audit, "snapshot": snapshot, "manifest_rows": len(rows)}


def main() -> int:
    workspace = Path(__file__).resolve().parents[2]
    result = build(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
