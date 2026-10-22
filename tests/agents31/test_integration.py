"""TRAIN-only local artifacts; no parent TEST evaluator or training entry point."""

import copy

import pytest

from scripts.phase31_benchmark import load_inputs
from src.ch06_multi_agent.benchmark import audit_groups
from src.ch06_multi_agent.executor import ProcessExecutor, _child
from src.ch06_multi_agent.tools import ToolCatalog
from tests.agents31.test_core import broken_call, good_call


def test_real_catalog_and_six_tools_cpu():
    view, catalog, rows = load_inputs()
    tools = ToolCatalog(catalog)
    assert audit_groups(rows)["tasks"] == 300
    for domain in ("diabetes", "house", "gold"):
        for kind in ("numeric", "evidence"):
            record = tools.records[f"{domain}_{kind}_000"]
            payload = tools.call(record["tool"], f"{domain}_{kind}_000")
            assert payload["text"] and payload["citations"]
            assert all(not r["path"].startswith("apps/") for r in payload["artifact_refs"])
    assert view["taskset"]["sha256"]


class MemoryConnection:
    def __init__(self):
        self.closed = False

    def send(self, value):
        self.value = value

    def close(self):
        self.closed = True


@pytest.mark.parametrize("fault", [None, "numeric", "citation"])
def test_child_payload_receipt_fault_injection(fault):
    connection = MemoryConnection()
    _child(connection, good_call, "predict_diabetes", "record_1", 0, fault)
    assert connection.closed and connection.value["status"] == "ok"
    assert connection.value["peak_rss_bytes"] > 0


def test_child_error_sanitization_and_error_reply():
    connection = MemoryConnection()
    _child(connection, broken_call, "predict_diabetes", "record_1", 0, None)
    assert connection.value["code"] == "tool_error"

    def transient(*args):
        return {"status": "error", "code": "transient"}

    _child(connection, transient, "predict_diabetes", "record_1", 0, None)
    assert connection.value["code"] == "transient"


def test_executor_active_and_expired_guards():
    executor = ProcessExecutor(good_call)
    assert executor.execute("predict_diabetes", "record_1", 0, None, 0)["status"] == "timeout"
    executor.active = True
    with pytest.raises(ValueError):
        executor.execute("predict_diabetes", "record_1", 0, None, 1)


def test_counts_and_duplicate_source_guards():
    _, _, rows = load_inputs()
    with pytest.raises(ValueError):
        audit_groups(rows[:299])
    clone = copy.deepcopy(rows)
    clone[0]["request"]["task_id"] = clone[1]["request"]["task_id"]
    with pytest.raises(ValueError):
        audit_groups(clone)
