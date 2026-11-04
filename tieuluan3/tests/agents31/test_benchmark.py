"""Prospective task split, independent scoring and irreversible TEST claims."""

import copy

import pytest

from src.ch06_multi_agent.benchmark import audit_groups, claim, score
from src.ch06_multi_agent.core import Orchestrator
from tests.agents31.test_core import FakeTools, payload, task


def row():
    return {
        "request": task(),
        "domain": "diabetes",
        "category": "numeric",
        "split": "train",
        "group_id": "numeric_family_1",
        "source_group": "source_a",
        "fault": None,
        "gold": {"status": "succeeded", "payload": payload()},
    }


def test_numeric_and_citation_scoring_independent_of_verifier_label():
    record = row()
    out = Orchestrator(FakeTools()).run(record["request"], "A2", "a" * 64)
    assert score(record, out)["task_success"] == 1
    out["values"][0] += 1
    assert score(record, out)["task_success"] == 0
    assert score(record, out)["numeric_parity"] == 0
    out["values"] = [0.25]
    out["trace"]["citations"] = []
    assert score(record, out)["citation_correctness"] == 0


@pytest.mark.parametrize(
    "fault,variant,success",
    [
        ("numeric", "A1", 0),
        ("numeric", "A2", 1),
        ("citation", "A0", 0),
        ("citation", "A2", 1),
        ("permanent", "A0", 1),
        ("transient", "A2", 1),
    ],
)
def test_fault_rubric(fault, variant, success):
    record = row()
    record.update(category="tool_failure", fault=fault)
    record["gold"]["status"] = {
        "numeric": "abstained",
        "citation": "abstained",
        "permanent": "failed",
        "transient": "succeeded",
    }[fault]
    out = Orchestrator(FakeTools()).run(record["request"], variant, "a" * 64, fault=fault)
    assert score(record, out)["task_success"] == success


def test_group_and_source_overlap_rejected():
    a, b = row(), copy.deepcopy(row())
    b["request"]["task_id"] = "task_b"
    b["split"] = "test"
    with pytest.raises(ValueError):
        audit_groups([a, b], require_counts=False)
    b["group_id"] = "test_family"
    with pytest.raises(ValueError):
        audit_groups([a, b], require_counts=False)
    b["source_group"] = "source_b"
    assert audit_groups([a, b], require_counts=False)["overlap"] == 0


def test_claim_write_once_and_fail_closed(tmp_path):
    path = tmp_path / "claim.json"
    claim(path, {"taskset_sha256": "a" * 64})
    with pytest.raises(FileExistsError):
        claim(path, {"taskset_sha256": "a" * 64})
