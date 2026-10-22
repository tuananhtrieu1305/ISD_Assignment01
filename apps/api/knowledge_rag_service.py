"""Lazy, hash-verified KG-RAG runtime for the Phase 16 API."""

from __future__ import annotations

import gzip
import hashlib
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import joblib

from term_paper.tools.phase13_graph import normalize_label
from term_paper.tools.phase14_rag import grounded_answer
from term_paper.tools.phase15_kgrag import graph_filter_ranking, weighted_rrf


ALLOWED_DOMAINS = {"auto", "medical", "finance"}
ALLOWED_TOOLS = {"medical": "medical_retriever", "finance": "finance_retriever"}
MAX_QUESTION_CHARACTERS = 500

MEDICAL_TERMS = {
    "diabetes", "diabetic", "insulin", "glucose", "blood sugar", "a1c",
    "kidney", "neuropathy", "retinopathy", "hypoglycemia", "hyperglycemia",
}
FINANCE_TERMS = {
    "revenue", "expense", "profit", "income", "asset", "liability", "cash flow",
    "margin", "fiscal", "annual report", "acquisition", "lease", "tax", "equity",
    "shares", "ebitda", "debt", "cost", "percentage change",
}
PROMPT_INJECTION_PATTERNS = {
    "ignore previous", "ignore all instructions", "system prompt", "developer message",
    "reveal prompt", "show hidden", "execute code", "run command", "shell command",
    "rm rf", "override safety", "bypass guardrail",
}
MEDICAL_SAFETY_PATTERNS = {
    "personalized insulin dose", "insulin dose", "dosage", "diagnose me", "diagnose my",
    "prescribe", "stop prescribed", "stop my medicine", "medical emergency",
}
FINANCIAL_SAFETY_PATTERNS = {
    "best stock to buy", "should i buy", "should i sell", "recommend a stock",
    "investment advice", "stock price tomorrow", "guaranteed return", "buy this week",
}


class AgentInputError(ValueError):
    """Safe validation error for an Agent request."""


class ArtifactUnavailableError(RuntimeError):
    """Packaged runtime is absent or fails integrity checks."""


class AgentTimeoutError(TimeoutError):
    """Local inference exceeded its configured deadline."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_question(value: Any) -> str:
    if not isinstance(value, str):
        raise AgentInputError("question phải là chuỗi văn bản.")
    question = " ".join(value.split())
    if len(question) < 3:
        raise AgentInputError("question phải có ít nhất 3 ký tự.")
    if len(question) > MAX_QUESTION_CHARACTERS:
        raise AgentInputError(f"question không được vượt quá {MAX_QUESTION_CHARACTERS} ký tự.")
    return question


def route_domain(question: str, requested_domain: str = "auto") -> str | None:
    domain = str(requested_domain or "auto").casefold().strip()
    if domain not in ALLOWED_DOMAINS:
        raise AgentInputError("domain chỉ nhận auto, medical hoặc finance.")
    if domain != "auto":
        return domain
    normalized = normalize_label(question)
    medical_score = sum(term in normalized for term in MEDICAL_TERMS)
    finance_score = sum(term in normalized for term in FINANCE_TERMS)
    if medical_score == finance_score:
        return None
    return "medical" if medical_score > finance_score else "finance"


def guardrail_reason(question: str, domain: str | None) -> str | None:
    normalized = normalize_label(question)
    if any(pattern in normalized for pattern in PROMPT_INJECTION_PATTERNS):
        return "prompt_injection"
    if domain == "medical" and any(pattern in normalized for pattern in MEDICAL_SAFETY_PATTERNS):
        return "medical_safety"
    if domain == "finance" and any(pattern in normalized for pattern in FINANCIAL_SAFETY_PATTERNS):
        return "financial_safety"
    return None


@dataclass
class RuntimeBundle:
    manifest: dict[str, Any]
    chunks: dict[str, dict[str, dict[str, Any]]]
    indexes: dict[str, dict[str, Any]]
    graph: dict[str, dict[str, dict[str, Any]]]


class KnowledgeRagService:
    """Thread-safe lazy loader and deterministic two-tool Agent router."""

    def __init__(
        self,
        workspace: Path,
        runtime_dir: Path | None = None,
        loader: Callable[[], RuntimeBundle] | None = None,
        timeout_ms: int = 8_000,
    ):
        self.workspace = Path(workspace)
        self.runtime_dir = runtime_dir or self.workspace / "apps/api/models"
        self.manifest_path = self.runtime_dir / "kg_manifest.json"
        self.timeout_ms = int(timeout_ms)
        self._custom_loader = loader
        self._bundle: RuntimeBundle | None = None
        self._lock = threading.Lock()
        self._integrity: dict[str, Any] | None = None

    def status(self) -> dict[str, Any]:
        version = None
        if self.manifest_path.exists():
            try:
                version = json.loads(self.manifest_path.read_text(encoding="utf-8")).get("artifact_version")
            except (OSError, json.JSONDecodeError):
                pass
        state = "ready" if self._bundle is not None else ("cold" if self.manifest_path.exists() else "unavailable")
        return {
            "status": state,
            "artifact_version": version,
            "loaded": self._bundle is not None,
            "allowed_tools": sorted(ALLOWED_TOOLS.values()),
        }

    def readiness(self) -> dict[str, Any]:
        try:
            return {"status": "ready", **self._verify_artifacts()}
        except (ArtifactUnavailableError, OSError, ValueError, json.JSONDecodeError):
            return {
                "status": "unavailable",
                "artifact_version": None,
                "hash_verified": False,
                "message": "KG-RAG runtime artifact is unavailable or invalid.",
            }

    def _verify_artifacts(self) -> dict[str, Any]:
        if self._integrity is not None:
            return dict(self._integrity)
        if not self.manifest_path.exists():
            raise ArtifactUnavailableError("runtime manifest missing")
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        files = manifest.get("files")
        if not isinstance(files, list) or not files:
            raise ArtifactUnavailableError("runtime manifest has no files")
        total = 0
        for item in files:
            path = (self.runtime_dir / str(item.get("path", ""))).resolve()
            if self.runtime_dir.resolve() not in path.parents:
                raise ArtifactUnavailableError("runtime artifact escaped package directory")
            if not path.is_file() or _sha256(path) != item.get("sha256"):
                raise ArtifactUnavailableError("runtime artifact hash mismatch")
            if path.stat().st_size != item.get("size_bytes"):
                raise ArtifactUnavailableError("runtime artifact size mismatch")
            total += path.stat().st_size
        if total > int(manifest.get("artifact_budget_bytes", 0)):
            raise ArtifactUnavailableError("runtime package exceeds artifact budget")
        self._integrity = {
            "artifact_version": manifest.get("artifact_version"),
            "hash_verified": True,
            "package_bytes": total,
            "budget_bytes": manifest.get("artifact_budget_bytes"),
        }
        return dict(self._integrity)

    def _load_bundle(self) -> RuntimeBundle:
        self._verify_artifacts()
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        chunks: dict[str, dict[str, dict[str, Any]]] = {"medical": {}, "finance": {}}
        with gzip.open(self.runtime_dir / manifest["chunks_file"], "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    chunks[row["domain"]][row["chunk_id"]] = row
        with gzip.open(self.runtime_dir / manifest["graph_file"], "rt", encoding="utf-8") as handle:
            graph = json.load(handle)
        indexes = {
            domain: {
                kind: joblib.load(self.runtime_dir / relative)
                for kind, relative in manifest["indexes"][domain].items()
            }
            for domain in ("medical", "finance")
        }
        return RuntimeBundle(manifest=manifest, chunks=chunks, indexes=indexes, graph=graph)

    def _get_bundle(self) -> RuntimeBundle:
        if self._bundle is None:
            with self._lock:
                if self._bundle is None:
                    self._bundle = self._custom_loader() if self._custom_loader else self._load_bundle()
        return self._bundle

    @staticmethod
    def _graph_candidates(
        question: str, graph: Mapping[str, Mapping[str, Any]]
    ) -> tuple[set[str], list[str]]:
        normalized = normalize_label(question)
        query_terms = set(normalized.split())
        matched: list[tuple[str, Mapping[str, Any]]] = []
        for key, item in graph.items():
            key_terms = set(key.split())
            if key and (key in normalized or (len(key_terms) > 1 and key_terms <= query_terms)):
                matched.append((key, item))
        matched.sort(key=lambda pair: (-len(pair[0]), pair[0]))
        candidates: set[str] = set()
        path: list[str] = []
        for key, item in matched[:4]:
            candidates.update(str(value) for value in item.get("chunk_ids", []))
            if not path:
                path = ["user_question", str(item.get("label", key)), str(item.get("node_id", "entity"))]
        return candidates, path

    def _abstention(
        self, requested_domain: str, domain: str | None, reason: str, started: float
    ) -> dict[str, Any]:
        tool = ALLOWED_TOOLS.get(domain) if domain else None
        warning = (
            "Thông tin học thuật, không thay thế chẩn đoán hoặc tư vấn y khoa."
            if domain == "medical"
            else "Thông tin học thuật, không phải khuyến nghị đầu tư."
            if domain == "finance"
            else "Câu hỏi nằm ngoài hai miền dữ liệu medical và finance."
        )
        return {
            "answer": "",
            "domain": domain,
            "citations": [],
            "evidence": [],
            "route": {"requested_domain": requested_domain, "selected_domain": domain, "tool": tool},
            "graph_path": [],
            "abstained": True,
            "abstention_reason": reason,
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
            "artifact_version": self.status().get("artifact_version"),
            "warning": warning,
        }

    def query(self, question: Any, domain: str = "auto") -> dict[str, Any]:
        started = time.perf_counter()
        clean_question = validate_question(question)
        requested = str(domain or "auto").casefold().strip()
        selected = route_domain(clean_question, requested)
        reason = guardrail_reason(clean_question, selected)
        if reason:
            return self._abstention(requested, selected, reason, started)
        if selected is None:
            return self._abstention(requested, None, "out_of_domain", started)

        bundle = self._get_bundle()
        if (time.perf_counter() - started) * 1000.0 > self.timeout_ms:
            raise AgentTimeoutError("KG-RAG request exceeded its deadline")
        config = bundle.manifest["retrieval"]
        sparse = bundle.indexes[selected]["sparse"].search(clean_question, top_k=config["candidate_depth"])
        dense = bundle.indexes[selected]["dense"].search(clean_question, top_k=config["candidate_depth"])
        candidates, graph_path = self._graph_candidates(clean_question, bundle.graph[selected])
        graph_ranking = graph_filter_ranking(sparse, candidates, config["candidate_depth"])
        ranking = weighted_rrf(
            {"sparse": sparse, "dense": dense, "graph": graph_ranking},
            config["weights"], config["top_k"], config["rrf_k"],
        )
        chunk_lookup = bundle.chunks[selected]
        answer_config = bundle.manifest["answer_layer"]
        answer = grounded_answer(
            clean_question,
            ranking,
            {chunk_id: chunk_lookup[chunk_id]["text"] for chunk_id, _ in ranking if chunk_id in chunk_lookup},
            answer_config["minimum_overlap_terms"], answer_config["minimum_overlap_ratio"],
            answer_config["unsafe_patterns"], answer_config["maximum_characters"],
        )
        scores = {chunk_id: float(score) for chunk_id, score in ranking}
        evidence = [
            {
                "chunk_id": chunk_id,
                "document_id": chunk_lookup[chunk_id]["document_id"],
                "text": chunk_lookup[chunk_id]["text"],
                "score": round(scores[chunk_id], 8),
            }
            for chunk_id, _ in ranking[:5]
            if chunk_id in chunk_lookup
        ]
        citations = [
            {"chunk_id": chunk_id, "document_id": chunk_lookup[chunk_id]["document_id"]}
            for chunk_id in answer["citations"]
            if chunk_id in chunk_lookup
        ]
        if graph_path and ranking:
            graph_path = [*graph_path, ranking[0][0]]
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if elapsed_ms > self.timeout_ms:
            raise AgentTimeoutError("KG-RAG request exceeded its deadline")
        return {
            "answer": answer["answer"],
            "domain": selected,
            "citations": citations,
            "evidence": evidence,
            "route": {"requested_domain": requested, "selected_domain": selected, "tool": ALLOWED_TOOLS[selected]},
            "graph_path": graph_path,
            "abstained": bool(answer["abstained"]),
            "abstention_reason": answer["reason"] if answer["abstained"] else None,
            "latency_ms": round(elapsed_ms, 3),
            "artifact_version": bundle.manifest["artifact_version"],
            "warning": (
                "Thông tin học thuật, không thay thế chẩn đoán hoặc tư vấn y khoa."
                if selected == "medical"
                else "Thông tin học thuật, không phải khuyến nghị đầu tư."
            ),
        }
