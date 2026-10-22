"""Phase32 contract-first tests; no training or historical TEST execution."""

import pytest

from apps.api.v3.jobs import JobError, JobStore
from apps.api.v3.registry import ArtifactError, Registry
from apps.api.v3.server import create_app


def test_missing_registry_keeps_liveness(tmp_path):
    app = create_app(
        registry_path=tmp_path / "missing.json", database=tmp_path / "jobs.db", start_worker=False
    )
    client = app.test_client()
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 503
    assert client.get("/api/v3/chapters").status_code == 503


def test_registry_rejects_unpinned_document(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ArtifactError):
        Registry(path, expected_sha256="0" * 64)


def test_job_idempotency_and_owner_isolation(tmp_path):
    store = JobStore(tmp_path / "jobs.db")
    request = {"dataset_id": "ch2_cdc_diabetes", "family": "mlp", "input": {}}
    first = store.create(request, "idempotent-key", "owner-a")
    assert store.create(request, "idempotent-key", "owner-a")["job_id"] == first["job_id"]
    assert store.create(request, "idempotent-key", "owner-b")["job_id"] != first["job_id"]
    with pytest.raises(JobError):
        store.get(first["job_id"], "owner-b")
    with pytest.raises(JobError):
        store.create({**request, "family": "cnn"}, "idempotent-key", "owner-a")
    assert store.cancel(first["job_id"], "owner-a")["status"] == "cancelled"


@pytest.mark.parametrize("path", ["/no-such-route", "/api/v3/jobs/unknown"])
def test_errors_are_structured(tmp_path, path):
    app = create_app(
        registry_path=tmp_path / "missing.json", database=tmp_path / "jobs.db", start_worker=False
    )
    reply = app.test_client().get(path)
    assert reply.status_code in {400, 404}
    assert reply.json["schema_version"] == "3.0.0"
    assert "error" in reply.json
