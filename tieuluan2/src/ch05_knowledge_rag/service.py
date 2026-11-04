"""V3 local request/job contract. No evaluator, fitting, network or arbitrary tools."""

import time
from datetime import UTC, datetime, timedelta

from apps.api.knowledge_rag_service import guardrail_reason, validate_question
from src.ch05_knowledge_rag.preservation import RUNTIME_SHA, checked
from src.ch05_knowledge_rag.runtime import LazyBundle, compare_rankings, graph_candidates, load_bundle
from src.common.contracts import canonical_sha256, read_json, validate_document
from term_paper.tools.phase14_rag import grounded_answer

DATASETS = ("ch5_medquad_diabetes", "ch5_finqa", "ch5_wikidata_subgraphs")
METHODS = ("B0", "B1", "B2", "B3", "B4")
DOMAINS = {DATASETS[0]: "medical", DATASETS[1]: "finance"}
SOURCES = {
    DATASETS[0]: "https://github.com/abachaa/MedQuAD/tree/577bd37b96c02d1833b2c9eed2de9f96964e96cb",
    DATASETS[1]: "https://github.com/czyssrs/FinQA/tree/0f16e2867befa6840783e58be38c9efb9229d742",
}
WARNING = "Academic retrospective demo, not medical or investment advice. Citations identify the preserved runtime chunk container, not verified original per-chunk URLs."
SCOPE = "phase30.compact_free_question_demo.1"


def sample_request(dataset):
    if dataset not in DATASETS:
        raise ValueError("Unknown Chapter5 dataset")
    question = {
        DATASETS[0]: "Diabetes complications include kidney disease: find supporting evidence.",
        DATASETS[1]: "what is the the interest expense in 2009?",
        DATASETS[2]: "Q12206",
    }[dataset]
    return {
        "schema_version": "3.0.0",
        "chapter": 5,
        "dataset_id": dataset,
        "family": "kg_rag",
        "implementations": list(METHODS),
        "input": {"kind": "question", "text": question, "domain": DOMAINS.get(dataset, "auto")},
    }


def validate_request(request):
    validate_document("api", request)
    if request["chapter"] != 5 or request["dataset_id"] not in DATASETS or request["family"] != "kg_rag":
        raise ValueError("Require Chapter5 KG–RAG request")
    expected = DOMAINS.get(request["dataset_id"])
    if expected and request["input"]["domain"] not in {expected, "auto"}:
        raise ValueError("Dataset/domain mismatch")
    if not expected and request["input"]["domain"] != "auto":
        raise ValueError("Wikidata structural view requires domain=auto")
    return validate_question(request["input"]["text"])


class KgRagService:
    def __init__(self, loader=load_bundle, artifact_sha256=RUNTIME_SHA, chunks_sha256=None):
        self.runtime = LazyBundle(loader)
        self.artifact_sha256 = artifact_sha256
        self.chunks_sha256 = (
            chunks_sha256 or "42f025f955852567436dc7cd7efde701ca014429f47dacae7d7c0ba23ab51f29"
        )
        self.sparse_weight = 0.75

    def compare(self, request):
        question = validate_request(request)
        dataset = request["dataset_id"]
        domain = DOMAINS.get(dataset)
        input_hash = canonical_sha256(request["input"])
        group = canonical_sha256({"scope": SCOPE, "dataset": dataset, "artifact": self.artifact_sha256})
        suffix = canonical_sha256(request)[:16]
        now = datetime.now(UTC)
        structural = domain is None
        reason = guardrail_reason(question, domain)
        results, evidence, paths = [], {}, {}
        rankings, bundle, timing = {}, None, {method: 0.0 for method in METHODS}
        unavailable = False
        if not structural and not reason:
            try:
                config_path = checked(
                    {
                        "path": "experiments/configs/ch5/phase14_locked.json",
                        "sha256": "ea5b3546a8e408648f5024d62bd0cb3584784ead2f594e126d2dea356240653d",
                    }
                )
                self.sparse_weight = read_json(config_path)["selected_sparse_weight"]
                bundle = self.runtime.get()
            except (OSError, ValueError, KeyError, ImportError, RuntimeError):
                unavailable = True
        if bundle is not None:
            config = bundle.manifest["retrieval"]
            start = time.perf_counter()
            sparse = bundle.indexes[domain]["sparse"].search(question, config["candidate_depth"])
            sparse_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            dense = bundle.indexes[domain]["dense"].search(question, config["candidate_depth"])
            dense_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            candidates, paths = graph_candidates(question, bundle.graph[domain])
            graph_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter()
            rankings = compare_rankings(
                sparse,
                dense,
                candidates,
                self.sparse_weight,
                config["weights"],
                config["top_k"],
                config["rrf_k"],
            )
            fusion_ms = (time.perf_counter() - start) * 1000
            timing = {
                "B0": sparse_ms,
                "B1": dense_ms,
                "B2": sparse_ms + dense_ms + fusion_ms,
                "B3": sparse_ms + graph_ms,
                "B4": sparse_ms + dense_ms + graph_ms + fusion_ms,
            }
        for method in METHODS:
            row = {
                "implementation": method,
                "status": "succeeded",
                "model_id": f"{dataset}_{method.lower()}_compact_demo",
                "actual_device": "cpu",
                "actual_backend": "numpy",
                "inference_ms": timing[method],
                "artifact_sha256": self.artifact_sha256,
                "input_sha256": input_hash,
                "comparison_group_sha256": group,
                "error": None,
            }
            if structural or unavailable:
                row.update(
                    status="unavailable",
                    actual_device="not_run",
                    actual_backend="not_run",
                    inference_ms=None,
                    artifact_sha256=None,
                    prediction=None,
                    comparison_group_sha256=None,
                    error={
                        "code": "artifact_unavailable" if unavailable else "structural_dataset_only",
                        "message": "Verified runtime unavailable."
                        if unavailable
                        else "Wikidata is a snapshot browser, not a third B0–B4 QA benchmark.",
                    },
                )
                results.append(row)
                continue
            rank = rankings.get(method, [])
            evidence[method] = []
            if reason:
                answer = {
                    "answer": "Refused: " + reason,
                    "citations": [],
                    "abstained": True,
                    "reason": reason,
                }
            else:
                start = time.perf_counter()
                chunks = bundle.chunks[domain]
                answer_config = bundle.manifest["answer_layer"]
                answer = grounded_answer(
                    question,
                    rank,
                    {key: chunks[key]["text"] for key, _ in rank},
                    answer_config["minimum_overlap_terms"],
                    answer_config["minimum_overlap_ratio"],
                    answer_config["unsafe_patterns"],
                    answer_config["maximum_characters"],
                )
                row["inference_ms"] += (time.perf_counter() - start) * 1000
                evidence[method] = [
                    {
                        "chunk_id": key,
                        "document_id": chunks[key]["document_id"],
                        "text": chunks[key]["text"],
                        "score": float(score),
                    }
                    for key, score in rank
                ]
            citations = [
                {
                    "evidence_id": "chunk_" + canonical_sha256(key)[:24],
                    "source_url": SOURCES[dataset],
                    "locator": f"kg_chunks.jsonl.gz#{key};document={bundle.chunks[domain][key]['document_id']}",
                    "source_sha256": self.chunks_sha256,
                }
                for key in answer["citations"]
            ]
            row["prediction"] = {
                "kind": "answer",
                "text": answer["answer"] or "Insufficient evidence.",
                "abstained": answer["abstained"],
                "citations": citations,
            }
            results.append(row)
        job = {
            "schema_version": "3.0.0",
            "request_id": "kg_request_" + suffix,
            "job_id": "kg_demo_" + suffix,
            "request_sha256": canonical_sha256(request),
            "status": "failed" if structural or unavailable else "succeeded",
            "dataset_id": dataset,
            "family": "kg_rag",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "results": results,
            "comparison_valid": not structural and not reason and not unavailable,
            "comparison_blockers": ["Structural view only"]
            if structural
            else (
                ["Verified runtime unavailable"]
                if unavailable
                else (["Safety refusal; no ranker executed"] if reason else [])
            ),
            "trace_ids": [],
            "metric_artifacts": [],
            "input_sha256": input_hash,
        }
        validate_document("api#job", job)
        retrieved = {row["chunk_id"] for rows in evidence.values() for row in rows}
        paths = {key: path for key, path in paths.items() if key in retrieved}
        return {
            "job": job,
            "evidence": evidence,
            "graph_paths": paths,
            "warning": WARNING,
            "scope": SCOPE,
            "refusal_reason": reason,
            "public_test_evaluation_executed": False,
            "timing_scope": "Shared retrieval components + answer CPU milliseconds; excludes cold load and serialization; not independent per-method benchmark",
        }
