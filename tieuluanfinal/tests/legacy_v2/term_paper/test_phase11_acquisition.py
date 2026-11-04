from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from term_paper.tools.phase11_data import (
    aggregate_manifest_sha256,
    audit_finqa_directory,
    audit_medquad_directory,
    build_raw_manifest_rows,
    parse_medquad_xml,
    parse_wikidata_entity,
    validate_raw_manifest,
)
from term_paper.tools.verify_phase11 import verify_phase11


class Phase11AcquisitionTests(unittest.TestCase):
    def test_medquad_parser_preserves_metadata_and_missing_answer(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Document id="d1" source="NIH" url="https://example.test/d1">
  <Focus>Diabetes</Focus>
  <FocusAnnotations><UMLS><CUIs><CUI>C0011849</CUI></CUIs>
  <SemanticTypes><SemanticType>T047</SemanticType></SemanticTypes></UMLS></FocusAnnotations>
  <QAPairs>
    <QAPair pid="1"><Question qid="q1" qtype="information">What is diabetes?</Question>
      <Answer>Diabetes is a metabolic disease.</Answer></QAPair>
    <QAPair pid="2"><Question qid="q2" qtype="treatment">How is it treated?</Question></QAPair>
  </QAPairs>
</Document>"""
        rows = parse_medquad_xml(xml, source_file="fixture.xml")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["focus"], "Diabetes")
        self.assertEqual(rows[0]["cuis"], ["C0011849"])
        self.assertEqual(rows[0]["semantic_types"], ["T047"])
        self.assertEqual(rows[0]["answer"], "Diabetes is a metabolic disease.")
        self.assertIsNone(rows[1]["answer"])

    def test_medquad_audit_counts_missing_and_duplicates_without_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xml = """<Document id="d"><Focus>Diabetes</Focus><QAPairs>
<QAPair><Question qid="q">What is diabetes?</Question><Answer>Answer.</Answer></QAPair>
<QAPair><Question qid="q">What is diabetes?</Question></QAPair>
</QAPairs></Document>"""
            (root / "sample.xml").write_text(xml, encoding="utf-8")
            audit = audit_medquad_directory(root)

            self.assertEqual(audit["qa_pairs"], 2)
            self.assertEqual(audit["answers_present"], 1)
            self.assertEqual(audit["answers_missing"], 1)
            self.assertEqual(audit["duplicate_question_ids"], 1)
            self.assertFalse(audit["removed_answers_recovered"])

    def test_finqa_audit_measures_splits_reports_qa_and_programs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = [
                {
                    "id": "report-1",
                    "pre_text": ["before"],
                    "post_text": ["after"],
                    "table": [["Year", "Value"], ["2025", "10"]],
                    "qa": {
                        "question": "What is the value?",
                        "answer": "10",
                        "program": "table_lookup(Value, 2025)",
                        "gold_inds": {"0": "before"},
                    },
                }
            ]
            for split in ("train", "dev", "test"):
                (root / f"{split}.json").write_text(json.dumps(sample), encoding="utf-8")

            audit = audit_finqa_directory(root)
            self.assertEqual(audit["reports"], 3)
            self.assertEqual(audit["qa_pairs"], 3)
            self.assertEqual(audit["programs_present"], 3)
            self.assertEqual(audit["table_rows"], 6)
            self.assertEqual(audit["split_distribution"], {"dev": 1, "test": 1, "train": 1})

    def test_wikidata_parser_captures_revision_labels_and_claim_counts(self) -> None:
        payload = {
            "entities": {
                "Q12206": {
                    "id": "Q12206",
                    "lastrevid": 123456,
                    "modified": "2026-10-10T00:00:00Z",
                    "labels": {"en": {"language": "en", "value": "diabetes mellitus"}},
                    "descriptions": {"en": {"language": "en", "value": "group of metabolic disorders"}},
                    "claims": {"P31": [{"id": "claim-1"}], "P279": [{"id": "claim-2"}]},
                }
            }
        }
        row = parse_wikidata_entity(payload, expected_qid="Q12206")
        self.assertEqual(row["revision_id"], 123456)
        self.assertEqual(row["label_en"], "diabetes mellitus")
        self.assertEqual(row["claim_count"], 2)
        self.assertEqual(row["property_count"], 2)

    def test_manifest_detects_mutation_and_has_deterministic_aggregate_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "raw" / "sample.txt"
            target.parent.mkdir()
            target.write_text("immutable", encoding="utf-8")
            rows = build_raw_manifest_rows(root, [target])

            self.assertEqual(validate_raw_manifest(root, rows), [])
            expected = aggregate_manifest_sha256(rows)
            self.assertEqual(expected, aggregate_manifest_sha256(list(reversed(rows))))

            target.write_text("changed", encoding="utf-8")
            failures = validate_raw_manifest(root, rows)
            self.assertTrue(any("SHA-256" in failure for failure in failures))

    def test_manifest_csv_round_trip_keeps_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "data.json"
            target.write_text("{}", encoding="utf-8")
            rows = build_raw_manifest_rows(root, [target], dataset_id="wikidata")
            out = root / "manifest.csv"
            with out.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            loaded = list(csv.DictReader(out.open(encoding="utf-8")))
            self.assertEqual(loaded[0]["sha256"], hashlib.sha256(b"{}").hexdigest())

    def test_phase11_verifier_reports_missing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = verify_phase11(Path(tmp))
            self.assertEqual(result["status"], "FAIL")
            self.assertGreater(result["failed_checks"], 0)
            self.assertTrue(any("raw_manifest.csv" in item for item in result["failures"]))

    def test_phase11_verifier_accepts_complete_revision_locked_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            raw = workspace / "term_paper/knowledge_rag/data/raw"
            files = []
            rows = []
            for dataset_id in ("medquad", "finqa", "wikidata"):
                target = raw / dataset_id / "sample.json"
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps({"dataset": dataset_id}), encoding="utf-8")
                files.append(target)
                rows.extend(build_raw_manifest_rows(workspace, [target], dataset_id=dataset_id))

            manifests = workspace / "term_paper/knowledge_rag/artifacts/manifests"
            metrics = workspace / "term_paper/knowledge_rag/artifacts/metrics"
            cards = workspace / "term_paper/sources/dataset_cards"
            manifests.mkdir(parents=True)
            metrics.mkdir(parents=True)
            cards.mkdir(parents=True)
            with (manifests / "raw_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            snapshot = {
                "aggregate_manifest_sha256": aggregate_manifest_sha256(rows),
                "sources": {
                    "medquad": {"official_url": "https://github.com/abachaa/MedQuAD", "license": "CC BY 4.0", "commit_sha": "a"},
                    "finqa": {"official_url": "https://github.com/czyssrs/FinQA", "license": "MIT", "commit_sha": "b"},
                    "wikidata": {"official_url": "https://www.wikidata.org/", "license": "CC0", "revision_ids": {"Q1": 1}},
                },
            }
            (manifests / "phase11_snapshot_manifest.json").write_text(json.dumps(snapshot), encoding="utf-8")
            audit = {
                "medquad": {"removed_answers_recovered": False},
                "wikidata": {"acquisition_mode": "narrow_entity_snapshots"},
            }
            (metrics / "phase11_data_audit.json").write_text(json.dumps(audit), encoding="utf-8")
            for name in ("ch5_medquad.md", "ch5_finqa.md", "ch5_wikidata.md"):
                (cards / name).write_text("dataset card", encoding="utf-8")
            (workspace / "term_paper/sources/source_registry.csv").write_text(
                "ch5_medquad,ch5_finqa,ch5_wikidata", encoding="utf-8"
            )
            report = workspace / "term_paper/report"
            report.mkdir(parents=True)
            (report / "references_ordered.md").write_text("MedQuAD FinQA Wikidata", encoding="utf-8")

            result = verify_phase11(workspace)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["failed_checks"], 0)


if __name__ == "__main__":
    unittest.main()
