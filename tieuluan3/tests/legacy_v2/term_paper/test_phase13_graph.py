from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from term_paper.tools.phase13_graph import (
    build_adjacency,
    extract_financial_concepts,
    graph_stats,
    link_wikidata,
    make_edge,
    make_node,
    make_provenance,
    shortest_path,
    stable_graph_id,
    validate_evaluation_safety,
    validate_graph,
    write_graphml,
)
from term_paper.tools.verify_phase13 import verify_phase13


class Phase13GraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provenance = make_provenance(
            source_record_id="record-1",
            source_path="data/source.json",
            source_sha256="a" * 64,
            extractor_version="phase13-test-v1",
            confidence=1.0,
        )

    def test_stable_graph_ids_are_deterministic_and_order_sensitive(self) -> None:
        self.assertEqual(
            stable_graph_id("node", "medical", "Entity", "diabetes"),
            stable_graph_id("node", "medical", "Entity", "diabetes"),
        )
        self.assertNotEqual(
            stable_graph_id("edge", "a", "b"),
            stable_graph_id("edge", "b", "a"),
        )

    def test_provenance_rejects_invalid_confidence_or_missing_source(self) -> None:
        with self.assertRaises(ValueError):
            make_provenance("", "source.json", "a" * 64, "v1", 0.5)
        with self.assertRaises(ValueError):
            make_provenance("r1", "source.json", "a" * 64, "v1", 1.01)
        with self.assertRaises(ValueError):
            make_provenance("r1", "source.json", "not-a-hash", "v1", 0.5)

    def test_entity_linking_links_exact_alias_and_keeps_ambiguous_unresolved(self) -> None:
        rules = [
            {"qid": "Q3025883", "aliases": ["type 2 diabetes"], "candidate_terms": ["diabetes"]},
            {"qid": "Q12206", "aliases": ["diabetes mellitus"], "candidate_terms": ["diabetes"]},
        ]
        exact = link_wikidata("Type 2 Diabetes", rules)
        self.assertEqual(exact["decision"], "linked")
        self.assertEqual(exact["linked_qid"], "Q3025883")
        ambiguous = link_wikidata("diabetes care", rules)
        self.assertEqual(ambiguous["decision"], "unresolved")
        self.assertEqual(ambiguous["linked_qid"], None)
        self.assertEqual(ambiguous["candidate_qids"], ["Q12206", "Q3025883"])

    def test_entity_linking_never_forces_duplicate_exact_alias(self) -> None:
        rules = [
            {"qid": "Q1", "aliases": ["annual report"], "candidate_terms": []},
            {"qid": "Q2", "aliases": ["annual report"], "candidate_terms": []},
        ]
        result = link_wikidata("Annual report", rules)
        self.assertEqual(result["decision"], "unresolved")
        self.assertEqual(result["candidate_qids"], ["Q1", "Q2"])

    def test_financial_concept_extraction_is_deterministic_and_deduplicated(self) -> None:
        lexicon = {
            "net_income": ["net income", "net earnings"],
            "revenue": ["revenue", "revenues"],
        }
        text = "Revenue increased. Net income and revenues were reported; net income improved."
        self.assertEqual(extract_financial_concepts(text, lexicon), ["net_income", "revenue"])
        self.assertEqual(extract_financial_concepts(text, lexicon), extract_financial_concepts(text, lexicon))

    def _toy_graph(self):
        nodes = [
            make_node("medical", "Entity", "entity:a", "A", self.provenance),
            make_node("medical", "Document", "document:b", "B", self.provenance),
            make_node("medical", "Chunk", "chunk:c", "C", self.provenance),
        ]
        edges = [
            make_edge("medical", "DESCRIBED_BY", nodes[0]["node_id"], nodes[1]["node_id"], "a-b", self.provenance),
            make_edge("medical", "HAS_CHUNK", nodes[1]["node_id"], nodes[2]["node_id"], "b-c", self.provenance),
        ]
        return nodes, edges

    def test_graph_validator_accepts_valid_graph_and_detects_dangling_edge(self) -> None:
        nodes, edges = self._toy_graph()
        self.assertEqual(validate_graph(nodes, edges), [])
        broken = dict(edges[0], target_id="node-does-not-exist")
        failures = validate_graph(nodes, [broken])
        self.assertTrue(any("dangling" in failure for failure in failures))

    def test_retrieval_graph_rejects_gold_answer_edges(self) -> None:
        nodes, _ = self._toy_graph()
        leaked = make_edge(
            "medical", "ANSWERED_BY", nodes[0]["node_id"], nodes[2]["node_id"], "gold-leak", self.provenance
        )
        failures = validate_evaluation_safety([leaked])
        self.assertTrue(any("gold-derived" in failure for failure in failures))

    def test_adjacency_supports_offline_path_query(self) -> None:
        nodes, edges = self._toy_graph()
        adjacency = build_adjacency(nodes, edges)
        path = shortest_path(adjacency, nodes[0]["node_id"], nodes[2]["node_id"], max_hops=2)
        self.assertEqual(path, [nodes[0]["node_id"], nodes[1]["node_id"], nodes[2]["node_id"]])
        self.assertEqual(shortest_path(adjacency, nodes[0]["node_id"], nodes[2]["node_id"], max_hops=1), [])

    def test_graph_statistics_include_types_components_duplicates_and_link_coverage(self) -> None:
        nodes, edges = self._toy_graph()
        wiki = make_node("medical", "WikidataEntity", "wikidata:Q1", "Q1", self.provenance)
        nodes.append(wiki)
        edges.append(make_edge("medical", "SAME_AS", nodes[0]["node_id"], wiki["node_id"], "link", self.provenance))
        stats = graph_stats(nodes, edges, linkable_node_types={"Entity"})
        self.assertEqual(stats["node_count"], 4)
        self.assertEqual(stats["edge_count"], 3)
        self.assertEqual(stats["component_count"], 1)
        self.assertEqual(stats["entity_link_coverage"], 1.0)
        self.assertEqual(stats["duplicate_node_rate"], 0.0)
        self.assertIn("Entity", stats["node_type_counts"])

    def test_graphml_round_trip_has_all_nodes_and_edges(self) -> None:
        nodes, edges = self._toy_graph()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "graph.graphml"
            write_graphml(target, nodes, edges)
            root = ET.parse(target).getroot()
            namespace = {"g": "http://graphml.graphdrawing.org/xmlns"}
            self.assertEqual(len(root.findall(".//g:node", namespace)), 3)
            self.assertEqual(len(root.findall(".//g:edge", namespace)), 2)

    def test_phase13_verifier_reports_missing_deliverables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = verify_phase13(Path(tmp))
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("phase13_graph_manifest.json" in item for item in result["failures"]))

    def test_phase13_verifier_accepts_a_minimal_consistent_fixture(self) -> None:
        nodes, edges = self._toy_graph()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            base = workspace / "term_paper/knowledge_rag"
            graph_dir = base / "data/processed/phase13/medical"
            graph_dir.mkdir(parents=True)
            for name, rows in (("nodes.jsonl", nodes), ("edges.jsonl", edges)):
                (graph_dir / name).write_text(
                    "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
                    encoding="utf-8",
                )
            write_graphml(graph_dir / "graph.graphml", nodes, edges)
            adjacency = build_adjacency(nodes, edges)
            (graph_dir / "adjacency.json").write_text(json.dumps(adjacency), encoding="utf-8")
            metrics = base / "artifacts/metrics"
            figures = base / "artifacts/figures/phase13"
            config = base / "config"
            manifest_dir = base / "artifacts/manifests"
            for directory in (metrics, figures, config, manifest_dir):
                directory.mkdir(parents=True, exist_ok=True)
            (metrics / "phase13_graph_statistics.json").write_text(
                json.dumps({"medical": graph_stats(nodes, edges, {"Entity"})}), encoding="utf-8"
            )
            (metrics / "phase13_entity_link_audit.csv").write_text(
                "domain,local_node_id,local_label,candidate_qids,decision,linked_qid,method,confidence,rationale,source_record_id\n",
                encoding="utf-8",
            )
            (config / "phase13.json").write_text("{}", encoding="utf-8")
            (base / "graph_schema.md").write_text("# Graph schema", encoding="utf-8")
            for name in ("graph_schema.svg", "medical_sample_subgraph.svg", "finance_sample_subgraph.svg"):
                (figures / name).write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>", encoding="utf-8")
            artifacts = []
            for path in sorted(base.rglob("*")):
                if path.is_file() and "manifests" not in path.parts:
                    artifacts.append({"path": path.relative_to(workspace).as_posix()})
            (manifest_dir / "phase13_graph_manifest.json").write_text(
                json.dumps({"status": "PASS", "domains": ["medical"], "artifacts": artifacts}), encoding="utf-8"
            )
            result = verify_phase13(workspace)
            self.assertEqual(result["status"], "PASS", result["failures"])


if __name__ == "__main__":
    unittest.main()
