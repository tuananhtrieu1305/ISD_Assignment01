"""Deterministic preprocessing contracts for Phase 12 Knowledge & RAG."""

from __future__ import annotations

import hashlib
import re
import string
from collections import Counter, defaultdict
from typing import Any, Iterable


DIABETES_TERMS = (
    "diabetes mellitus",
    "type 1 diabetes",
    "type-1 diabetes",
    "type 2 diabetes",
    "type-2 diabetes",
    "gestational diabetes",
    "prediabetes",
    "pre-diabetes",
    "diabetic",
    "diabetes",
    "hyperglycemia",
    "hyperglycaemia",
    "blood glucose",
    "blood sugar",
    "insulin resistance",
    "glycated hemoglobin",
    "glycated haemoglobin",
    "hemoglobin a1c",
    "haemoglobin a1c",
    "hba1c",
    "diabetic ketoacidosis",
)
EXCLUDED_CONDITIONS = ("diabetes insipidus",)


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def stable_id(prefix: str, *parts: Any, length: int = 20) -> str:
    canonical = "\x1f".join(normalize_text(part) for part in parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}-{digest}"


def _matched_terms(text: str) -> list[str]:
    return [term for term in DIABETES_TERMS if term in text]


def diabetes_decision(record: dict[str, Any]) -> dict[str, Any]:
    focus = normalize_text(record.get("focus"))
    question = normalize_text(record.get("question"))
    answer = normalize_text(record.get("answer"))
    inspected = f"{focus} {question}".strip()
    excluded = [term for term in EXCLUDED_CONDITIONS if term in inspected]
    if not answer:
        return {"include": False, "reason": "missing_answer", "matched_terms": _matched_terms(inspected)}
    if excluded:
        return {"include": False, "reason": "excluded_condition", "matched_terms": excluded}
    focus_terms = _matched_terms(focus)
    if focus_terms:
        return {"include": True, "reason": "focus_term", "matched_terms": focus_terms}
    question_terms = _matched_terms(question)
    if question_terms:
        return {"include": True, "reason": "question_term", "matched_terms": question_terms}
    answer_terms = _matched_terms(answer)
    if answer_terms:
        return {"include": False, "reason": "answer_only_not_allowed", "matched_terms": answer_terms}
    return {"include": False, "reason": "no_diabetes_signal", "matched_terms": []}


def assign_group_split(
    group_id: str,
    seed: int = 42,
    train_ratio: float = 0.70,
    validation_ratio: float = 0.15,
) -> str:
    if not 0 < train_ratio < 1 or not 0 <= validation_ratio < 1 or train_ratio + validation_ratio >= 1:
        raise ValueError("Invalid split ratios")
    bucket = int(hashlib.sha256(f"{seed}:{group_id}".encode("utf-8")).hexdigest()[:12], 16) % 10_000
    if bucket < round(train_ratio * 10_000):
        return "train"
    if bucket < round((train_ratio + validation_ratio) * 10_000):
        return "validation"
    return "test"


def _dedupe_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize_text(row.get("focus")),
        normalize_text(row.get("question")),
        normalize_text(row.get("answer")),
    )


def deduplicate_medquad_records(
    records: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(records, key=lambda row: (str(row.get("source_file", "")), str(row.get("pair_id", ""))))
    kept_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    duplicates: list[dict[str, Any]] = []
    for row in ordered:
        key = _dedupe_key(row)
        if key not in kept_by_key:
            kept_by_key[key] = row
            continue
        kept = kept_by_key[key]
        duplicates.append(
            {
                "kept_source_file": kept.get("source_file"),
                "kept_pair_id": kept.get("pair_id"),
                "duplicate_source_file": row.get("source_file"),
                "duplicate_pair_id": row.get("pair_id"),
                "question": row.get("question"),
            }
        )
    return list(kept_by_key.values()), duplicates


def chunk_text(text: str, max_words: int = 120, overlap_words: int = 20) -> list[dict[str, Any]]:
    if max_words <= 0 or overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("Require max_words > overlap_words >= 0")
    matches = list(re.finditer(r"\S+", text or ""))
    if not matches:
        return []
    chunks: list[dict[str, Any]] = []
    step = max_words - overlap_words
    for word_start in range(0, len(matches), step):
        word_end = min(word_start + max_words, len(matches))
        char_start = matches[word_start].start()
        char_end = matches[word_end - 1].end()
        chunks.append(
            {
                "chunk_index": len(chunks),
                "text": text[char_start:char_end],
                "word_start": word_start,
                "word_end": word_end,
                "word_count": word_end - word_start,
                "char_start": char_start,
                "char_end": char_end,
            }
        )
        if word_end == len(matches):
            break
    return chunks


def finqa_table_row_to_text(header: list[Any], row: list[Any]) -> str:
    parts = [str(header[0])] if header and str(header[0]) else []
    for head, cell in zip(header[1:], row[1:]):
        parts.append(f"the {row[0]} of {head} is {cell} ;")
    return " ".join(" ".join(parts).split())


def finqa_context_segments(item: dict[str, Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    all_text = list(item.get("pre_text") or []) + list(item.get("post_text") or [])
    for index, text in enumerate(all_text):
        segments.append({"source_locator": f"text_{index}", "segment_type": "text", "text": str(text)})
    table = item.get("table") or []
    if table:
        header = table[0]
        for index, row in enumerate(table):
            segments.append(
                {
                    "source_locator": f"table_{index}",
                    "segment_type": "table",
                    "text": finqa_table_row_to_text(header, row),
                    "table_row": row,
                }
            )
    return segments


def validate_no_group_leakage(records: Iterable[dict[str, Any]]) -> list[str]:
    splits_by_group: defaultdict[str, set[str]] = defaultdict(set)
    for row in records:
        split = str(row["split"])
        if split in {"private_test", "challenge"}:
            continue
        splits_by_group[str(row["group_id"])].add(split)
    return sorted(group_id for group_id, splits in splits_by_group.items() if len(splits) > 1)


def recall_at_k(ranked_ids: list[str], gold_ids: set[str], k: int) -> float:
    if not gold_ids:
        return 0.0
    return len(set(ranked_ids[:k]) & gold_ids) / len(gold_ids)


def reciprocal_rank(ranked_ids: list[str], gold_ids: set[str], k: int) -> float:
    for rank, item_id in enumerate(ranked_ids[:k], start=1):
        if item_id in gold_ids:
            return 1.0 / rank
    return 0.0


def normalize_answer(text: Any) -> str:
    value = normalize_text(text)
    value = "".join(character for character in value if character not in string.punctuation)
    return " ".join(token for token in value.split() if token not in {"a", "an", "the"})


def token_f1(prediction: Any, gold: Any) -> float:
    predicted = normalize_answer(prediction).split()
    expected = normalize_answer(gold).split()
    if not predicted or not expected:
        return float(predicted == expected)
    common = Counter(predicted) & Counter(expected)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(predicted)
    recall = overlap / len(expected)
    return 2 * precision * recall / (precision + recall)

