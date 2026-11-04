"""Versioned deterministic function contracts and local V3 request adapter."""

import re

from src.ch06_multi_agent.core import DOMAINS, VARIANTS, Orchestrator, validate_task
from src.common.contracts import canonical_sha256, validate_document

FUNCTIONS = {
    "validate": (
        "validate_task(task)",
        "Kiểm tra đầu vào",
        "JSON5 trường",
        "task hợp lệ",
        "Sai ID/độ dài/trường lạ: từ chối",
    ),
    "policy": (
        "policy_reason(question, operation)",
        "Áp dụng an toàn chung",
        "question + operation",
        "reason hoặc null",
        "Rule hữu hạn, không chứng nhận an toàn toàn diện",
    ),
    "route": (
        "route(question)",
        "Chọn một miền",
        "text tối đa500 ký tự",
        "diabetes/house/gold hoặc null",
        "Không biết hoặc trộn miền: abstain",
    ),
    "direct_tool": (
        "ToolCatalog.call(tool, record_id)",
        "Gọi tool theo miền đã chọn",
        "allowlisted record",
        "payload + provenance",
        "Không chạy shell/URL/path từ câu hỏi",
    ),
    "specialist": (
        "ProcessExecutor.execute(...)",
        "Thực hiện tool trong process có hạn giờ",
        "tool + record + deadline",
        "receipt hoặc lỗi",
        "Retry transient1 lần; terminate/join khi timeout",
    ),
    "verify": (
        "verify_payload(payload, receipt_sha256)",
        "Kiểm chứng bằng chứng",
        "payload + receipt hash",
        "pass hoặc từ chối",
        "Kiểm integrity/finite/citation, không xác nhận chuyên môn",
    ),
    "report": (
        "Orchestrator.run(...): reporter",
        "Tổng hợp phản hồi có giới hạn",
        "status + values + citations",
        "answer + cảnh báo",
        "Không tự thêm lời khuyên hoặc con số",
    ),
    "emit": (
        "validate_document('agent', trace)",
        "Đóng gói trace V3",
        "DAG + action messages",
        "agent.schema3.0.0",
        "Không ghi chain-of-thought; DAG phải topo",
    ),
}
COMPOSITIONS = {
    "A0": ["validate", "policy", "direct_tool", "emit"],
    "A1": ["validate", "policy", "route", "specialist", "emit"],
    "A2": ["validate", "policy", "route", "specialist", "verify", "report", "emit"],
}


def pipeline_contract(domain, variant):
    if domain not in DOMAINS or variant not in VARIANTS:
        raise ValueError("Unknown pipeline")
    return {
        "schema_version": "phase31.agent_pipeline.1",
        "domain": domain,
        "variant": variant,
        "parameter_count": None,
        "learnable_layers": None,
        "composition": COMPOSITIONS[variant],
        "composition_plain": " → ".join(FUNCTIONS[k][1] for k in COMPOSITIONS[variant]),
        "functions": [
            {
                "id": key,
                **dict(zip(("signature", "role", "input", "output", "corner_case"), FUNCTIONS[key])),
                "source": "src/ch06_multi_agent/"
                + (
                    "executor.py"
                    if key == "specialist"
                    else ("tools.py" if key == "direct_tool" else "core.py")
                ),
                "formula": None,
                "learned_parameters": None,
            }
            for key in COMPOSITIONS[variant]
        ],
        "budget": {"deadline_seconds": 15, "max_tool_calls": 8, "retry_per_tool": 1},
        "actual_backend": "numpy_cpu_deterministic",
        "api_key_required": False,
    }


def sample_request(domain):
    if domain not in DOMAINS:
        raise ValueError("Unknown domain")
    topic = {"diabetes": "tiểu đường", "house": "giá nhà", "gold": "giá vàng"}[domain]
    return {
        "schema_version": "3.0.0",
        "dataset_id": f"ch6_{domain}_tasks",
        "question": f"{topic}: xem kết quả học thuật record={domain}_numeric_000",
        "variants": list(VARIANTS),
    }


def decode_question(domain, question):
    if domain not in DOMAINS or not isinstance(question, str) or len(question) > 500:
        raise ValueError("Unsupported local request")
    matches = re.findall(r"record=([^\s;,]+)", question)
    operation, key = "unsupported", "no_record"
    if matches:
        if len(matches) != 1 or not re.fullmatch(
            r"(?:diabetes|house|gold)_(?:numeric|evidence)_\d{3}", matches[0]
        ):
            raise ValueError("Require exactly one approved record ID")
        key = matches[0]
        if not key.startswith(domain + "_"):
            raise ValueError("Record/domain mismatch")
        operation = "numeric" if "_numeric_" in key else "evidence"
    task = {
        "task_id": "demo_" + canonical_sha256(question)[:16],
        "domain_hint": domain,
        "question": question,
        "record_id": key,
        "operation": operation,
    }
    validate_task(task)
    return task


class AgentService:
    def __init__(self, tools, taskset_sha256):
        self.engine, self.taskset_sha256 = Orchestrator(tools), taskset_sha256

    def compare(self, request):
        validate_document("api#agent_task", request)
        dataset = request["dataset_id"]
        if dataset not in {f"ch6_{d}_tasks" for d in DOMAINS}:
            raise ValueError("Unknown agent dataset")
        domain = dataset.removeprefix("ch6_").removesuffix("_tasks")
        task = decode_question(domain, request["question"])
        return {
            "scope": "local_task_demo_not_http",
            "dataset_id": dataset,
            "outputs": {v: self.engine.run(task, v, self.taskset_sha256) for v in VARIANTS},
            "historical_test_evaluation_executed": False,
            "limitation": "Structured record-bound demo, not arbitrary natural-language reasoning or a clinical/investment assistant",
        }
