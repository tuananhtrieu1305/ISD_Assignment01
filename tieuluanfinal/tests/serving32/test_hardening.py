"""Final catalog/worker/privacy checks, with no mutation of any real asset."""

import copy
import os
import stat

from apps.api.v3.jobs import JobStore
from apps.api.v3.registry import ArtifactError
from apps.api.v3.server import create_app

HEADERS = {"X-Client-Token": "c" * 48, "Idempotency-Key": "hardening_key"}


def test_job_database_is_private(tmp_path):
    before = os.umask(0o022)
    try:
        store = JobStore(tmp_path / "private" / "jobs.db")
    finally:
        os.umask(before)
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600


def test_short_question_is_422(tmp_path):
    app = create_app(database=tmp_path / "jobs.db", start_worker=False)
    registry = app.extensions["registry"]
    payload = copy.deepcopy(registry.json(registry.document["samples"])["ch5_finqa"]["request"])
    payload["input"]["text"] = "hi"
    assert app.test_client().post("/api/v3/comparisons", json=payload, headers=HEADERS).status_code == 422


def test_catalog_marks_only_unavailable_neural_slot(tmp_path, monkeypatch):
    app = create_app(database=tmp_path / "jobs.db", start_worker=False)
    registry = app.extensions["registry"]
    model = next(
        r
        for r in registry.models.values()
        if r["dataset_id"] == "ch2_cdc_diabetes" and r["implementation"] == "keras"
    )
    original = registry.checked

    def checked(record):
        if record["path"] == model["checkpoint"]["path"]:
            raise ArtifactError("Synthetic mismatch without touching real files")
        return original(record)

    monkeypatch.setattr(registry, "checked", checked)
    reply = app.test_client().get("/api/v3/models?dataset_id=ch2_cdc_diabetes")
    assert reply.status_code == 200
    statuses = {r["implementation"]: r["status"] for r in reply.json["data"]}
    assert statuses == {"scratch": "ready", "keras": "unavailable", "pytorch": "ready"}
    assert app.test_client().get("/health").status_code == 200


def test_dead_worker_does_not_accept_jobs(tmp_path):
    app = create_app(database=tmp_path / "jobs.db")
    app.extensions["supervisor"].close()
    registry = app.extensions["registry"]
    payload = registry.json(registry.document["samples"])["ch2_cdc_diabetes"]["request"]
    client = app.test_client()
    assert client.get("/ready").status_code == 503
    assert client.post("/api/v3/comparisons", json=payload, headers=HEADERS).status_code == 503


def test_valid_agent_task_is_accepted(tmp_path):
    app = create_app(database=tmp_path / "jobs.db", start_worker=False)
    reply = app.test_client().post(
        "/api/v3/agent-tasks",
        json={
            "schema_version": "3.0.0",
            "dataset_id": "ch6_diabetes_tasks",
            "question": "tiểu đường record=diabetes_numeric_000",
            "variants": ["A0", "A1", "A2"],
        },
        headers=HEADERS,
    )
    assert reply.status_code == 202
