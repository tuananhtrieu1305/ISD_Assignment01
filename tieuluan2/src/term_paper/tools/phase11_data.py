"""Acquisition and audit helpers for Phase 11 Knowledge & RAG sources."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    value = " ".join("".join(element.itertext()).split())
    return value or None


def parse_medquad_xml(xml_text: str, source_file: str = "") -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    focus = _text(root.find(".//Focus"))
    cuis = [value for node in root.findall(".//CUI") if (value := _text(node))]
    semantic_types = [
        value for node in root.findall(".//SemanticType") if (value := _text(node))
    ]
    document_id = root.attrib.get("id") or root.attrib.get("docid") or ""
    document_url = root.attrib.get("url") or ""
    rows: list[dict[str, Any]] = []
    for pair in root.findall(".//QAPair"):
        question = pair.find("Question")
        answer = pair.find("Answer")
        rows.append(
            {
                "source_file": source_file,
                "document_id": document_id,
                "document_url": document_url,
                "pair_id": pair.attrib.get("pid") or pair.attrib.get("id") or "",
                "question_id": (question.attrib.get("qid") if question is not None else "") or "",
                "question_type": (question.attrib.get("qtype") if question is not None else "") or "",
                "question": _text(question),
                "answer": _text(answer),
                "focus": focus,
                "cuis": cuis,
                "semantic_types": semantic_types,
            }
        )
    return rows


def audit_medquad_directory(root: Path) -> dict[str, Any]:
    xml_files = sorted(path for path in root.rglob("*.xml") if ".git" not in path.parts)
    rows: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    source_distribution: Counter[str] = Counter()
    for path in xml_files:
        try:
            parsed = parse_medquad_xml(path.read_text(encoding="utf-8"), path.relative_to(root).as_posix())
        except (ET.ParseError, UnicodeDecodeError) as exc:
            parse_errors.append(f"{path.relative_to(root).as_posix()}: {exc}")
            continue
        rows.extend(parsed)
        relative = path.relative_to(root)
        source_distribution[relative.parts[0] if len(relative.parts) > 1 else "."] += len(parsed)

    question_ids = [row["question_id"] for row in rows if row["question_id"]]
    duplicates = sum(count - 1 for count in Counter(question_ids).values() if count > 1)
    question_types = Counter(row["question_type"] or "UNSPECIFIED" for row in rows)
    diabetes_terms = ("diabetes", "diabetic", "insulin", "blood glucose")
    diabetes_candidates = sum(
        1
        for row in rows
        if any(term in " ".join(str(row.get(key) or "") for key in ("focus", "question", "answer")).lower()
               for term in diabetes_terms)
    )
    return {
        "xml_files": len(xml_files),
        "parsed_xml_files": len(xml_files) - len(parse_errors),
        "parse_errors": parse_errors,
        "qa_pairs": len(rows),
        "answers_present": sum(row["answer"] is not None for row in rows),
        "answers_missing": sum(row["answer"] is None for row in rows),
        "duplicate_question_ids": duplicates,
        "focus_present": sum(bool(row["focus"]) for row in rows),
        "cui_present": sum(bool(row["cuis"]) for row in rows),
        "semantic_type_present": sum(bool(row["semantic_types"]) for row in rows),
        "question_type_distribution": dict(sorted(question_types.items())),
        "source_distribution": dict(sorted(source_distribution.items())),
        "diabetes_candidate_qa": diabetes_candidates,
        "removed_answers_recovered": False,
        "answer_recovery_policy": "Never crawl or reconstruct answers removed by the upstream MedQuAD maintainers.",
    }


def _finqa_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "reports"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def _finqa_questions(qa: Any) -> list[dict[str, Any]]:
    if isinstance(qa, list):
        return [item for item in qa if isinstance(item, dict)]
    if isinstance(qa, dict):
        return [qa]
    return []


def audit_finqa_directory(root: Path) -> dict[str, Any]:
    candidates = []
    for split in ("train", "dev", "test", "private_test"):
        matches = sorted(root.rglob(f"{split}.json"))
        if matches:
            candidates.append((split, matches[0]))
    split_distribution: dict[str, int] = {}
    qa_split_distribution: dict[str, int] = {}
    examples = qa_pairs = programs = table_rows = text_segments = 0
    missing_questions = missing_answers = duplicate_ids = 0
    all_ids: list[str] = []
    report_keys: set[str] = set()
    public_report_keys: set[str] = set()
    operation_counts: Counter[str] = Counter()
    for split, path in candidates:
        items = _finqa_items(json.loads(path.read_text(encoding="utf-8")))
        split_distribution[split] = len(items)
        examples += len(items)
        split_qa = 0
        for item in items:
            item_id = str(item.get("id") or item.get("report_id") or "")
            if item_id:
                all_ids.append(f"{split}:{item_id}")
                report_key = item_id.split("/page_", 1)[0]
                report_keys.add(report_key)
                if split != "private_test":
                    public_report_keys.add(report_key)
            table = item.get("table") or []
            table_rows += len(table) if isinstance(table, list) else 0
            text_segments += sum(
                len(item.get(key) or []) if isinstance(item.get(key), list) else 0
                for key in ("pre_text", "post_text")
            )
            for qa in _finqa_questions(item.get("qa")):
                qa_pairs += 1
                split_qa += 1
                missing_questions += not bool(qa.get("question"))
                missing_answers += qa.get("answer", qa.get("exe_ans")) in (None, "")
                program = qa.get("program")
                if program:
                    programs += 1
                    operation = str(program).split("(", 1)[0].strip()
                    operation_counts[operation or "UNKNOWN"] += 1
        qa_split_distribution[split] = split_qa
    duplicate_ids = sum(count - 1 for count in Counter(all_ids).values() if count > 1)
    return {
        "files": {split: path.as_posix() for split, path in candidates},
        "reports": examples,
        "examples": examples,
        "unique_financial_reports": len(report_keys),
        "public_unique_financial_reports": len(public_report_keys),
        "qa_pairs": qa_pairs,
        "programs_present": programs,
        "table_rows": table_rows,
        "text_segments": text_segments,
        "missing_questions": int(missing_questions),
        "missing_answers": int(missing_answers),
        "duplicate_report_ids_within_split": duplicate_ids,
        "split_distribution": dict(sorted(split_distribution.items())),
        "qa_split_distribution": dict(sorted(qa_split_distribution.items())),
        "program_operation_distribution": dict(sorted(operation_counts.items())),
    }


def parse_wikidata_entity(payload: dict[str, Any], expected_qid: str) -> dict[str, Any]:
    entities = payload.get("entities") or {}
    if expected_qid not in entities:
        raise ValueError(f"Entity {expected_qid} is absent from payload")
    entity = entities[expected_qid]
    claims = entity.get("claims") or {}
    labels = entity.get("labels") or {}
    descriptions = entity.get("descriptions") or {}
    return {
        "qid": expected_qid,
        "revision_id": entity.get("lastrevid"),
        "modified": entity.get("modified"),
        "label_en": (labels.get("en") or {}).get("value"),
        "description_en": (descriptions.get("en") or {}).get("value"),
        "property_count": len(claims),
        "claim_count": sum(len(values) for values in claims.values() if isinstance(values, list)),
    }


def build_raw_manifest_rows(
    workspace: Path, paths: Iterable[Path], dataset_id: str = "fixture"
) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(paths, key=lambda value: value.as_posix()):
        rows.append(
            {
                "dataset_id": dataset_id,
                "relative_path": path.relative_to(workspace).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def aggregate_manifest_sha256(rows: Iterable[dict[str, Any]]) -> str:
    canonical = [
        {
            "dataset_id": str(row["dataset_id"]),
            "relative_path": str(row["relative_path"]),
            "size_bytes": int(row["size_bytes"]),
            "sha256": str(row["sha256"]),
        }
        for row in rows
    ]
    canonical.sort(key=lambda row: (row["dataset_id"], row["relative_path"]))
    payload = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_raw_manifest(workspace: Path, rows: Iterable[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for row in rows:
        path = workspace / str(row["relative_path"])
        if not path.is_file():
            failures.append(f"Missing raw file: {row['relative_path']}")
            continue
        if path.stat().st_size != int(row["size_bytes"]):
            failures.append(f"Size mismatch: {row['relative_path']}")
        if sha256_file(path) != row["sha256"]:
            failures.append(f"SHA-256 mismatch: {row['relative_path']}")
    return failures

