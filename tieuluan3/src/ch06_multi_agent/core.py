"""Deterministic roles and bounded state transitions; gold labels never enter this module."""

import math
import re
import time
import unicodedata

from src.common.contracts import canonical_sha256, validate_document

DOMAINS = ("diabetes", "house", "gold")
VARIANTS = ("A0", "A1", "A2")
WARNING = "Học thuật trên snapshot cũ; không chẩn đoán, kê đơn, định giá hiện tại hoặc tư vấn đầu tư."
TOOLS = {
    ("diabetes", "numeric"): "predict_diabetes",
    ("house", "numeric"): "predict_house",
    ("gold", "numeric"): "forecast_gold",
    ("diabetes", "evidence"): "retrieve_medical",
    ("house", "evidence"): "lookup_series",
    ("gold", "evidence"): "lookup_series",
}


def normalized(text):
    text = unicodedata.normalize("NFKD", text.casefold()).replace("đ", "d")
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


def route(question):
    text = normalized(question)
    matches = [
        domain
        for domain, terms in {
            "diabetes": ("tieu duong", "diabetes", "cdc", "medquad"),
            "house": ("gia nha", "housing", "ames", "bis"),
            "gold": ("gia vang", "gold", "pink sheet"),
        }.items()
        if any(re.search(r"\b" + re.escape(term) + r"\b", text) for term in terms)
    ]
    return matches[0] if len(matches) == 1 else None


def policy_reason(question, operation):
    text = normalized(question)
    if any(
        term in text
        for term in (
            "ke don",
            "lieu insulin",
            "chan doan cho toi",
            "diagnose me",
            "prescribe",
            "chac chan sinh loi",
            "dam bao loi nhuan",
            "tu van dau tu",
            "guaranteed profit",
            "ignore previous",
            "reveal secrets",
            "bo qua quy tac",
            "tiet lo bi mat",
        )
    ):
        return "unsafe_request"
    return "unsupported_operation" if operation == "unsupported" else None


def validate_task(task):
    keys = {"task_id", "domain_hint", "question", "record_id", "operation"}
    if not isinstance(task, dict) or set(task) != keys:
        raise ValueError("Require a bounded structured task, not arbitrary instructions")
    if task["domain_hint"] not in DOMAINS or task["operation"] not in {"numeric", "evidence", "unsupported"}:
        raise ValueError("Undeclared domain or operation")
    if any(
        not isinstance(task[k], str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,95}", task[k])
        for k in ("task_id", "record_id")
    ):
        raise ValueError("Invalid task/record ID")
    question = task["question"]
    if (
        not isinstance(question, str)
        or not 1 <= len(question.strip()) <= 500
        or any(ord(c) < 32 for c in question)
    ):
        raise ValueError("Question must be plain bounded text")


def verify_payload(payload, receipt_sha256):
    if canonical_sha256(payload) != receipt_sha256:
        raise ValueError("Tool receipt integrity mismatch")
    if set(payload) != {"values", "unit", "text", "citations", "artifact_refs"}:
        raise ValueError("Unexpected tool fields")
    if (
        not isinstance(payload["values"], list)
        or len(payload["values"]) > 3
        or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            for v in payload["values"]
        )
        or not payload["text"]
        or len(payload["text"]) > 5000
        or not payload["unit"]
        or not 1 <= len(payload["citations"]) <= 5
        or not 1 <= len(payload["artifact_refs"]) <= 20
    ):
        raise ValueError("Missing evidence or invalid numeric values")
    for citation in payload["citations"]:
        if not citation["source_url"].startswith("https://") or not re.fullmatch(
            r"[a-f0-9]{64}", citation["source_sha256"]
        ):
            raise ValueError("Invalid citation provenance")
    return True


class Orchestrator:
    """One request owns its DAG, 15-second deadline and at most eight tool attempts."""

    def __init__(self, tools, *, deadline_seconds=15.0):
        if not 0 < deadline_seconds <= 15:
            raise ValueError("Deadline outside locked budget")
        self.tools, self.deadline_seconds = tools, deadline_seconds

    def run(self, task, variant, taskset_sha256, *, fault=None):
        validate_task(task)
        if variant not in VARIANTS or not re.fullmatch(r"[a-f0-9]{64}", taskset_sha256):
            raise ValueError("Invalid variant/taskset identity")
        if fault not in {None, "transient", "permanent", "numeric", "citation", "timeout"}:
            raise ValueError("Undeclared internal fault")
        start, nodes, messages = time.perf_counter(), [], []
        deadline = start + self.deadline_seconds
        calls, peak = 0, 0
        values, citations, answer = [], [], "Không đủ bằng chứng để trả lời."
        status, verification = "abstained", "not_run"
        reason = policy_reason(task["question"], task["operation"])
        routed = task["domain_hint"] if variant == "A0" else route(task["question"])
        if routed != task["domain_hint"]:
            reason = reason or "routing_ambiguous_or_mismatch"

        def add(agent, tool, incoming, outgoing, outcome="ok", refs=None, elapsed=0):
            node_id = f"node_{len(nodes) + 1}"
            nodes.append(
                {
                    "node_id": node_id,
                    "agent": agent,
                    "parent_ids": [nodes[-1]["node_id"]] if nodes else [],
                    "tool": tool,
                    "input_sha256": canonical_sha256(incoming),
                    "output_sha256": canonical_sha256(outgoing),
                    "artifact_refs": refs or [],
                    "duration_ms": max(0, elapsed),
                    "outcome": outcome,
                }
            )
            messages.append({"node_id": node_id, "input": incoming, "output": outgoing})

        if variant != "A0":
            add("router", "none", task, {"route": routed, "policy": reason})
        tool = TOOLS.get((routed, task["operation"]), "none")
        reply = None
        role = "direct" if variant == "A0" else "specialist"
        if not reason:
            for attempt in range(2):
                seconds = deadline - time.perf_counter()
                if seconds <= 0:
                    status, reason = "timeout", "deadline"
                    break
                tick = time.perf_counter()
                reply = self.tools.execute(tool, task["record_id"], attempt, fault, seconds)
                calls += 1
                peak = max(peak, reply.get("peak_rss_bytes", 0))
                ok = reply["status"] == "ok"
                add(
                    role,
                    tool,
                    {"record_id": task["record_id"], "attempt": attempt},
                    reply,
                    "ok" if ok else ("timeout" if reply["status"] == "timeout" else "error"),
                    reply.get("payload", {}).get("artifact_refs", []),
                    (time.perf_counter() - tick) * 1000,
                )
                if ok:
                    p = reply["payload"]
                    values, citations, answer = p["values"], p["citations"], p["text"]
                    status = "succeeded"
                    break
                if reply["status"] == "timeout":
                    status, reason = "timeout", "deadline"
                    break
                if reply.get("code") != "transient" or attempt == 1:
                    status, reason = "failed", "tool_unavailable"
                    break
        else:
            add(role, "none", {"request_sha256": canonical_sha256(task)}, {"refusal": reason}, "abstain")
        if variant == "A2":
            tick = time.perf_counter()
            verification = "not_applicable"
            if status == "succeeded":
                try:
                    verify_payload(reply["payload"], reply["receipt_sha256"])
                    verification = "passed"
                except (ValueError, KeyError, TypeError):
                    status, reason, verification = "abstained", "invalid_tool_evidence", "rejected"
                    values, citations, answer = [], [], "Bằng chứng công cụ không hợp lệ; từ chối suy diễn."
            add(
                "verifier",
                "none",
                {"receipt": reply},
                {"verification": verification, "reason": reason},
                "abstain" if verification == "rejected" else "ok",
                elapsed=(time.perf_counter() - tick) * 1000,
            )
            add(
                "reporter",
                "none",
                {"status": status, "values": values, "citations": citations},
                {"answer": answer, "warning": WARNING},
            )
        if time.perf_counter() > deadline:
            status, reason, values, citations = "timeout", "deadline", [], []
        if status != "succeeded":
            answer = f"Không thực hiện yêu cầu: {reason or 'insufficient_evidence'}."
        trace = {
            "schema_version": "3.0.0",
            "evidence_kind": "measured",
            "trace_id": f"trace_{canonical_sha256(task)[:20]}_{variant.lower()}",
            "task_id": task["task_id"],
            "task_set_sha256": taskset_sha256,
            "variant": variant,
            "domain": task["domain_hint"],
            "status": status,
            "nodes": nodes,
            "answer": answer,
            "citations": citations,
            "limitations": [WARNING],
            "latency_ms": (time.perf_counter() - start) * 1000,
        }
        validate_document("agent", trace, publish=True)
        return {
            "trace": trace,
            "messages": messages,
            "values": values,
            "route": routed,
            "verification": verification,
            "reason": reason,
            "tool_calls": calls,
            "peak_child_rss_bytes": peak,
            "message_count": len(nodes),
        }
