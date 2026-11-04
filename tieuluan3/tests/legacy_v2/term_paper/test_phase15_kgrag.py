from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from term_paper.tools.phase13_graph import make_edge, make_node, make_provenance
from term_paper.tools.phase15_kgrag import (
    GraphRetriever,
    bootstrap_mean_ci,
    categorize_error,
    classify_kg_effect,
    graph_filter_ranking,
    decide_test_run,
    weighted_rrf,
)
from term_paper.tools.verify_phase15 import verify_phase15


class Phase15KGRagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provenance = make_provenance("r1", "source.json", "a" * 64, "test", 1.0)

    def _medical_graph(self):
        question = make_node("medical", "Question", "q1", "What is diabetes?", self.provenance, source_id="query-1")
        entity = make_node("medical", "MedicalEntity", "e1", "Diabetes", self.provenance)
        document = make_node("medical", "Document", "d1", "Diabetes document", self.provenance)
        chunk = make_node("medical", "Chunk", "c1", "Diabetes chunk", self.provenance, source_id="chunk-1")
        edges = [
            make_edge("medical", "ASKS_ABOUT", question["node_id"], entity["node_id"], "q-e", self.provenance),
            make_edge("medical", "DESCRIBES", document["node_id"], entity["node_id"], "d-e", self.provenance),
            make_edge("medical", "HAS_CHUNK", document["node_id"], chunk["node_id"], "d-c", self.provenance),
        ]
        return [question, entity, document, chunk], edges

    def test_medical_graph_expansion_respects_hop_limit_and_returns_trace(self) -> None:
        nodes, edges = self._medical_graph()
        retriever = GraphRetriever.from_records("medical", nodes, edges)
        shallow = retriever.expand("query-1", max_hops=1)
        self.assertEqual(shallow["chunk_ids"], [])
        expanded = retriever.expand("query-1", max_hops=2)
        self.assertEqual(expanded["chunk_ids"], ["chunk-1"])
        self.assertEqual(expanded["paths"]["chunk-1"][0], nodes[0]["node_id"])
        self.assertEqual(expanded["paths"]["chunk-1"][-1], nodes[3]["node_id"])

    def test_finance_concept_expansion_follows_reverse_mentions(self) -> None:
        question = make_node("finance", "Question", "q", "revenue?", self.provenance, source_id="query-1")
        concept = make_node("finance", "FinancialConcept", "revenue", "Revenue", self.provenance)
        chunk = make_node("finance", "Chunk", "c", "revenue chunk", self.provenance, source_id="chunk-1")
        edges = [
            make_edge("finance", "MENTIONS", question["node_id"], concept["node_id"], "q-c", self.provenance),
            make_edge("finance", "MENTIONS", chunk["node_id"], concept["node_id"], "chunk-c", self.provenance),
        ]
        retriever = GraphRetriever.from_records("finance", [question, concept, chunk], edges)
        result = retriever.expand("query-1", max_hops=1)
        self.assertEqual(result["chunk_ids"], ["chunk-1"])

    def test_graph_filter_keeps_only_candidates_and_stable_fallback(self) -> None:
        sparse = [("c3", 3.0), ("c2", 2.0), ("c1", 1.0)]
        ranked = graph_filter_ranking(sparse, {"c1", "c2", "c4"}, top_k=3)
        self.assertEqual([item[0] for item in ranked], ["c2", "c1", "c4"])
        self.assertGreater(ranked[0][1], ranked[-1][1])

    def test_weighted_rrf_validates_weights_and_is_deterministic(self) -> None:
        rankings = {
            "sparse": [("a", 1.0), ("b", 0.5)],
            "dense": [("b", 1.0), ("a", 0.5)],
            "graph": [("c", 1.0), ("b", 0.5)],
        }
        fused = weighted_rrf(rankings, {"sparse": 0.6, "dense": 0.2, "graph": 0.2}, top_k=3, rrf_k=10)
        self.assertEqual(fused, weighted_rrf(rankings, {"sparse": 0.6, "dense": 0.2, "graph": 0.2}, 3, 10))
        self.assertEqual(fused[0][0], "b")
        with self.assertRaises(ValueError):
            weighted_rrf(rankings, {"sparse": 0.5, "dense": 0.5}, 3, 10)

    def test_bootstrap_ci_is_deterministic_and_contains_mean(self) -> None:
        first = bootstrap_mean_ci([0.0, 1.0, 1.0, 0.0], seed=42, n_resamples=500)
        second = bootstrap_mean_ci([0.0, 1.0, 1.0, 0.0], seed=42, n_resamples=500)
        self.assertEqual(first, second)
        self.assertLessEqual(first["lower"], first["mean"])
        self.assertGreaterEqual(first["upper"], first["mean"])

    def test_kg_effect_classification(self) -> None:
        gold = {"gold"}
        self.assertEqual(classify_kg_effect(["miss"], ["gold"], gold, 1), "helps")
        self.assertEqual(classify_kg_effect(["gold"], ["miss"], gold, 1), "hurts")
        self.assertEqual(classify_kg_effect(["gold"], ["gold"], gold, 1), "neutral")

    def test_error_categories_cover_linking_retrieval_numeric_and_unsupported(self) -> None:
        linking = categorize_error(
            {"domain": "medical", "ranked_chunk_ids": [], "gold_chunk_ids": ["g"], "answer": "", "gold_answer": "x", "abstained": True, "citations": []},
            graph_candidate_count=0,
        )
        self.assertIn("entity_linking", linking)
        miss = categorize_error(
            {"domain": "medical", "ranked_chunk_ids": ["x"], "gold_chunk_ids": ["g"], "answer": "x", "gold_answer": "y", "abstained": False, "citations": ["x"]},
            graph_candidate_count=3,
        )
        self.assertIn("retrieval_miss", miss)
        self.assertIn("unsupported_answer", miss)
        numeric = categorize_error(
            {"domain": "finance", "ranked_chunk_ids": ["g"], "gold_chunk_ids": ["g"], "answer": "10", "gold_answer": "20", "abstained": False, "citations": ["g"]},
            graph_candidate_count=2,
        )
        self.assertIn("numerical_reasoning", numeric)

        ood = categorize_error(
            {
                "domain": "medical",
                "split": "challenge",
                "challenge_type": "ood",
                "ranked_chunk_ids": [],
                "gold_chunk_ids": [],
                "answer": "",
                "gold_answer": "",
                "abstained": True,
                "citations": [],
            },
            graph_candidate_count=0,
        )
        self.assertIn("ood", ood)

    def test_test_run_gate_executes_once_then_only_reuses_exact_lock(self) -> None:
        self.assertEqual(decide_test_run(None, "a" * 64, "q" * 64), "execute")
        complete = {"status": "COMPLETE", "run_count": 1, "locked_config_sha256": "a" * 64, "query_set_sha256": "q" * 64}
        self.assertEqual(decide_test_run(complete, "a" * 64, "q" * 64), "reuse")
        with self.assertRaises(ValueError):
            decide_test_run(dict(complete, locked_config_sha256="b" * 64), "a" * 64, "q" * 64)
        with self.assertRaises(ValueError):
            decide_test_run(dict(complete, run_count=2), "a" * 64, "q" * 64)

    def test_verifier_reports_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = verify_phase15(Path(tmp))
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("phase15_experiment_manifest.json" in item for item in result["failures"]))

    def test_verifier_does_not_trust_pass_status_without_deliverables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "term_paper/knowledge_rag/artifacts/manifests/phase15_experiment_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
            result = verify_phase15(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("deliverable" in item for item in result["failures"]))

    def test_generated_phase15_artifacts_pass_independent_verification(self) -> None:
        workspace = Path(__file__).resolve().parents[2]
        result = verify_phase15(workspace)
        self.assertEqual(result["status"], "PASS", result["failures"])
        self.assertIn("medical: B0-B4 TEST rows and metrics validated", result["checks"])
        self.assertIn("finance: B0-B4 TEST rows and metrics validated", result["checks"])


if __name__ == "__main__":
    unittest.main()
