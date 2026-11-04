from __future__ import annotations

import json
import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from term_paper.tools.phase12_preprocessing import (
    assign_group_split,
    chunk_text,
    deduplicate_medquad_records,
    diabetes_decision,
    finqa_context_segments,
    normalize_answer,
    reciprocal_rank,
    recall_at_k,
    stable_id,
    token_f1,
    validate_no_group_leakage,
)
from term_paper.tools.verify_phase12 import verify_phase12


class Phase12PreprocessingTests(unittest.TestCase):
    def test_diabetes_filter_uses_focus_or_question_and_rejects_insipidus(self) -> None:
        included = diabetes_decision(
            {"focus": "Type 2 diabetes", "question": "How is it treated?", "answer": "A"}
        )
        self.assertTrue(included["include"])
        self.assertEqual(included["reason"], "focus_term")

        excluded = diabetes_decision(
            {"focus": "Diabetes insipidus", "question": "What is diabetes insipidus?", "answer": "A"}
        )
        self.assertFalse(excluded["include"])
        self.assertEqual(excluded["reason"], "excluded_condition")

    def test_diabetes_filter_never_uses_answer_only_or_missing_gold(self) -> None:
        answer_only = diabetes_decision(
            {"focus": "Kidney disease", "question": "What is it?", "answer": "Diabetes may cause it."}
        )
        self.assertFalse(answer_only["include"])
        self.assertEqual(answer_only["reason"], "answer_only_not_allowed")

        missing = diabetes_decision(
            {"focus": "Diabetes", "question": "What is diabetes?", "answer": None}
        )
        self.assertFalse(missing["include"])
        self.assertEqual(missing["reason"], "missing_answer")

    def test_stable_ids_and_group_split_are_deterministic(self) -> None:
        self.assertEqual(stable_id("doc", "A", "B"), stable_id("doc", "A", "B"))
        self.assertNotEqual(stable_id("doc", "A", "B"), stable_id("doc", "B", "A"))
        splits = {assign_group_split("diabetes:C001", seed=42) for _ in range(5)}
        self.assertEqual(len(splits), 1)
        self.assertIn(splits.pop(), {"train", "validation", "test"})

    def test_medquad_deduplication_keeps_lexicographically_first_provenance(self) -> None:
        base = {"focus": "Diabetes", "question": "What is diabetes?", "answer": "Answer"}
        rows = [dict(base, source_file="z.xml"), dict(base, source_file="a.xml")]
        kept, duplicates = deduplicate_medquad_records(rows)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["source_file"], "a.xml")
        self.assertEqual(duplicates[0]["duplicate_source_file"], "z.xml")

    def test_chunk_text_has_overlap_stable_offsets_and_no_empty_chunks(self) -> None:
        text = "one two three four five six seven"
        chunks = chunk_text(text, max_words=4, overlap_words=2)
        self.assertEqual([chunk["text"] for chunk in chunks], ["one two three four", "three four five six", "five six seven"])
        self.assertEqual(chunks[0]["word_start"], 0)
        self.assertEqual(chunks[1]["word_start"], 2)
        self.assertEqual(chunks[-1]["word_end"], 7)

    def test_finqa_segments_match_official_text_and_table_locators(self) -> None:
        item = {
            "pre_text": ["before"],
            "post_text": ["after"],
            "table": [["Year", "Revenue"], ["2025", "10"]],
        }
        segments = finqa_context_segments(item)
        by_locator = {row["source_locator"]: row["text"] for row in segments}
        self.assertEqual(by_locator["text_0"], "before")
        self.assertEqual(by_locator["text_1"], "after")
        self.assertEqual(by_locator["table_1"], "Year the 2025 of Revenue is 10 ;")
        self.assertIn("table_0", by_locator)

    def test_group_leakage_validator_detects_cross_split_group(self) -> None:
        clean = [
            {"group_id": "g1", "split": "train"},
            {"group_id": "g2", "split": "test"},
        ]
        self.assertEqual(validate_no_group_leakage(clean), [])
        leaked = clean + [{"group_id": "g1", "split": "test"}]
        self.assertEqual(validate_no_group_leakage(leaked), ["g1"])

    def test_retrieval_and_answer_metrics_on_toy_cases(self) -> None:
        ranked = ["d2", "d1", "d3"]
        self.assertEqual(recall_at_k(ranked, {"d1"}, 1), 0.0)
        self.assertEqual(recall_at_k(ranked, {"d1"}, 2), 1.0)
        self.assertEqual(reciprocal_rank(ranked, {"d1"}, 10), 0.5)
        self.assertEqual(normalize_answer("The, Revenue!"), "revenue")
        self.assertAlmostEqual(token_f1("net income was 10", "net income is 10"), 0.75)

    def test_phase12_verifier_reports_missing_deliverables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = verify_phase12(Path(tmp))
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("preprocessing_manifest.json" in failure for failure in result["failures"]))

    def test_phase12_verifier_rejects_dangling_gold_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            base = workspace / "term_paper/knowledge_rag"
            processed = base / "data/processed/phase12"
            processed.mkdir(parents=True)
            document = {"document_id": "d1", "raw_source_path": "raw.txt", "raw_source_sha256": hashlib.sha256(b"raw").hexdigest()}
            chunk = {"chunk_id": "c1", "document_id": "d1"}
            query = {
                "query_id": "q1", "domain": "medical", "dataset": "medquad", "split": "train",
                "group_id": "g1", "question": "q", "answer_available": True,
                "gold_document_ids": ["d1"], "gold_chunk_ids": ["missing"], "gold_evidence_ids": ["e1"],
            }
            evidence = {"evidence_id": "e1", "query_id": "q1", "document_id": "d1", "chunk_id": "c1"}
            payloads = {
                "documents.jsonl": [document], "chunks.jsonl": [chunk], "queries.jsonl": [query],
                "evidence.jsonl": [evidence],
                "challenge_queries.jsonl": [{"query_id": "challenge-1", "expected_behavior": "abstain"}],
                "medquad_filter_audit.jsonl": [], "duplicate_audit.jsonl": [],
            }
            for name, rows in payloads.items():
                (processed / name).write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            (workspace / "raw.txt").write_bytes(b"raw")
            (base / "evaluation_contract.md").write_text("sealed TEST contract", encoding="utf-8")
            config = base / "config/phase12.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({"manual_audit": {"minimum_inclusion_precision": 0.9}}), encoding="utf-8")
            manual = base / "artifacts/metrics/phase12_diabetes_manual_audit.csv"
            manual.parent.mkdir(parents=True)
            with manual.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=("record_key", "review_label"))
                writer.writeheader()
                writer.writerows({"record_key": f"r{i}", "review_label": "TP"} for i in range(40))
            artifacts = []
            for path in payloads:
                target = processed / path
                artifacts.append({
                    "path": target.relative_to(workspace).as_posix(),
                    "size_bytes": target.stat().st_size,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                })
            manifest = base / "artifacts/manifests/preprocessing_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"test_split_status": "SEALED_NOT_USED_FOR_TUNING", "artifacts": artifacts}), encoding="utf-8")

            result = verify_phase12(workspace)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("gold chunk" in failure for failure in result["failures"]))


if __name__ == "__main__":
    unittest.main()
