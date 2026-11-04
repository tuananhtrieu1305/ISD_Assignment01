"""Queue transitions, artifact tamper/path budgets and process cleanup."""

import json
import subprocess
import sys

import pytest

from apps.api.v3.inference import failure_job
from apps.api.v3.jobs import JobError, JobStore
from apps.api.v3.registry import ArtifactError, Registry
from apps.api.v3.supervisor import Supervisor, rss_bytes, terminate_tree
from src.common.artifact_core import sha256_file

REQUEST = {
    "dataset_id": "ch2_cdc_diabetes",
    "family": "mlp",
    "input": {},
    "implementations": ["scratch", "keras", "pytorch"],
}


def test_bounded_queue_expiry_claim_recovery(tmp_path):
    store = JobStore(tmp_path / "jobs.db", ttl=30, capacity=1)
    item = store.create(REQUEST, "first-key", "owner")
    with pytest.raises(JobError, match="queue_full"):
        store.create(REQUEST, "other-key", "owner")
    assert store.claim()[0] == item["job_id"]
    assert store.claim() is None
    store.recover()
    assert store.get(item["job_id"], "owner")["comparison_blockers"] == ["worker_restarted"]
    with store.connection() as db:
        db.execute("UPDATE jobs SET expires=0")
    with pytest.raises(JobError):
        store.get(item["job_id"], "owner")
    second = store.create(REQUEST, "second-key", "owner")
    store.claim()
    store.finish(second["job_id"], failure_job(REQUEST, "expected"))
    assert store.cancel(second["job_id"], "owner")["status"] == "failed"


def test_output_budget_and_cancel_race(tmp_path):
    store = JobStore(tmp_path / "jobs.db")
    item = store.create(REQUEST, "first-key", "owner")
    store.claim()
    with pytest.raises(JobError):
        store.finish(item["job_id"], failure_job(REQUEST, "expected"), {"large": "x" * (2 * 1024**2)})
    store.cancel(item["job_id"], "owner")
    store.finish(item["job_id"], failure_job(REQUEST, "late_result"))
    assert store.get(item["job_id"], "owner")["status"] == "cancelled"


def registry_fixture(tmp_path):
    asset = tmp_path / "data.json"
    asset.write_text("{}", encoding="utf-8")
    record = {"path": "data.json", "sha256": sha256_file(asset), "size_bytes": 2}
    document = {
        "files": [record],
        "models": [],
        "datasets": [],
        "chapters": [],
        "components": [{"id": "demo", "assets": [record]}],
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return Registry(path, root=tmp_path, expected_sha256=sha256_file(path)), record, asset


def test_tamper_and_path_fail_closed(tmp_path):
    registry, record, asset = registry_fixture(tmp_path)
    assert registry.components()[0]["status"] == "ready"
    for name in ["../data.json", "/tmp/data.json", "C:\\data.json", "unknown"]:
        with pytest.raises(ArtifactError):
            registry.checked({**record, "path": name})
    asset.write_text("[]", encoding="utf-8")
    assert registry.components()[0]["status"] == "unavailable"
    with pytest.raises(ArtifactError):
        registry.checked(record)


def test_symlink_rejected(tmp_path):
    registry, record, asset = registry_fixture(tmp_path)
    alias = tmp_path / "alias.json"
    alias.symlink_to(asset)
    registry.files["alias.json"] = {**record, "path": "alias.json"}
    with pytest.raises(ArtifactError):
        registry.checked({**record, "path": "alias.json"})


def test_process_termination_reaps_child():
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    assert rss_bytes(process.pid) >= 0
    terminate_tree(process)
    assert process.poll() is not None
    terminate_tree(process)
    assert rss_bytes(99999999) == 0


def test_supervisor_deadline_and_restart_lock(tmp_path, monkeypatch):
    store = JobStore(tmp_path / "jobs.db")
    item = store.create(REQUEST, "first-key", "owner")
    claim = store.claim()
    original = subprocess.Popen

    def slow_process(*args, **kwargs):
        return original([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)

    monkeypatch.setattr("apps.api.v3.supervisor.subprocess.Popen", slow_process)
    supervisor = Supervisor(store, deadline=0.1)
    supervisor.execute(*claim)
    result = store.get(item["job_id"], "owner")
    assert result["comparison_blockers"] == ["deadline_exceeded"]
    supervisor.start()
    try:
        with pytest.raises(RuntimeError):
            Supervisor(store).start()
    finally:
        supervisor.close()
