from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from term_paper.tools.build_phase10_baseline import (
    build_migration_rows,
    parse_manuscript_inventory,
    run_smoke_benchmark,
)
from term_paper.tools.verify_phase10 import (
    sha256_file,
    validate_baseline_records,
    validate_environment_audit,
    validate_migration_rows,
)


class Phase10VerifierTests(unittest.TestCase):
    def test_parse_manuscript_and_migration_cover_every_existing_item(self) -> None:
        manuscript = """# CHƯƠNG 4. RECURRENT NEURAL NETWORK
## 4.1. Khái niệm
![RNN plot](assets/ch4/rnn.png)
*Hình 4.1. Minh họa RNN.*
**Bảng 4.1. Kết quả RNN**
| A | B |
|---|---|
| 1 | 2 |
# PHẦN 5. TRIỂN KHAI MÔ HÌNH
## 5.2. Use case ML: diabetes risk
"""
        inventory = parse_manuscript_inventory(manuscript)
        self.assertEqual(len(inventory["headings"]), 4)
        self.assertEqual(len(inventory["figures"]), 1)
        self.assertEqual(len(inventory["tables"]), 1)

        rows = build_migration_rows(inventory)
        kinds = [row["source_kind"] for row in rows]
        self.assertEqual(kinds.count("heading"), 4)
        self.assertEqual(kinds.count("figure"), 1)
        self.assertEqual(kinds.count("table"), 1)
        self.assertEqual(kinds.count("deployment_use_case"), 8)
        self.assertTrue(any(row["destination"] == "Chương 2 — mục deploy ngắn" for row in rows))

    def test_smoke_benchmark_is_cpu_only_and_retrieves_gold_documents(self) -> None:
        result = run_smoke_benchmark()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["document_count"], 6)
        self.assertEqual(result["query_count"], 3)
        self.assertEqual(result["bm25"]["top1_correct"], 3)
        self.assertEqual(result["tfidf_svd_lsa"]["top1_correct"], 3)

    def test_sha256_file_matches_known_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sample.bin"
            target.write_bytes(b"phase-10")

            self.assertEqual(
                sha256_file(target),
                hashlib.sha256(b"phase-10").hexdigest(),
            )

    def test_validate_baseline_records_detects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            target = workspace / "report.md"
            target.write_text("baseline", encoding="utf-8")
            good_record = {
                "path": "report.md",
                "size_bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "role": "manuscript",
            }

            self.assertEqual(validate_baseline_records(workspace, [good_record]), [])

            bad_record = dict(good_record, sha256="0" * 64)
            failures = validate_baseline_records(workspace, [bad_record])
            self.assertTrue(any("SHA-256" in failure for failure in failures))

    def test_validate_migration_rows_requires_complete_safe_mapping(self) -> None:
        rows = [
            {
                "source_kind": kind,
                "source_id": f"{kind}-1",
                "source_path": "term_paper/report/manuscript.md",
                "source_label": f"sample {kind}",
                "action": "KEEP",
                "destination": "Chương 4",
                "status": "LOCKED",
                "notes": "covered",
            }
            for kind in ("heading", "figure", "table")
        ]
        for source_id in (
            "dep-architecture",
            "dep-provenance",
            "dep-diabetes",
            "dep-eurosat",
            "dep-rnn",
            "dep-tests",
            "dep-runtime",
            "dep-limitations",
        ):
            rows.append(
                {
                    "source_kind": "deployment_use_case",
                    "source_id": source_id,
                    "source_path": "term_paper/report/sections/05_trien_khai.md",
                    "source_label": source_id,
                    "action": "DISTRIBUTE",
                    "destination": "target",
                    "status": "LOCKED",
                    "notes": "covered",
                }
            )
        self.assertEqual(validate_migration_rows(rows), [])

        rows[0]["destination"] = ""
        failures = validate_migration_rows(rows)
        self.assertTrue(any("destination" in failure for failure in failures))

    def test_validate_environment_audit_requires_locked_cpu_stack(self) -> None:
        audit = {
            "schema_version": 1,
            "render_target": {
                "runtime": "python",
                "plan": "free",
                "region": "singapore",
            },
            "selected_stack": {
                "sparse_retriever": "rank_bm25",
                "dense_retriever": "tfidf_svd_lsa",
                "graph_runtime": "networkx_optional_pure_python_fallback",
                "answer_mode": "extractive_grounded",
                "external_api_required": False,
            },
            "selection_rationale": ["CPU-only", "no API key"],
            "smoke_benchmark": {
                "status": "PASS",
                "document_count": 6,
                "query_count": 3,
            },
        }
        self.assertEqual(validate_environment_audit(audit), [])

        invalid = json.loads(json.dumps(audit))
        invalid["selected_stack"]["external_api_required"] = True
        failures = validate_environment_audit(invalid)
        self.assertTrue(any("API" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
