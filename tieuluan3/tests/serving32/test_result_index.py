"""All chapters must expose saved result references, including recovered null costs."""

import pytest

from apps.api.v3.registry import Registry
from apps.api.v3.server import create_app


def test_recovered_orphan_metric_is_not_dropped():
    registry = Registry()
    identity = "ch4_household_power_rnn_pytorch_s17_main_test"
    row = next(r for r in registry.document["runs"] if r["run_id"] == identity)
    metric = registry.json(row["record"])
    assert metric["split"] == "test"
    assert metric["efficiency"]["train_seconds"] is None


@pytest.mark.parametrize(
    "dataset", ["ch2_cdc_diabetes", "ch3_cifar10", "ch4_gold_pink_sheet", "ch5_finqa", "ch6_house_tasks"]
)
def test_read_only_result_index(tmp_path, dataset):
    app = create_app(database=tmp_path / "jobs.db", start_worker=False)
    reply = app.test_client().get(f"/api/v3/datasets/{dataset}/results")
    assert reply.status_code == 200
    assert reply.json["data"]["historical_test_evaluation_executed"] is False
    assert reply.json["data"]["artifacts"]


def test_wikidata_has_structural_results_not_qa_scorecards(tmp_path):
    app = create_app(database=tmp_path / "jobs.db", start_worker=False)
    reply = app.test_client().get("/api/v3/datasets/ch5_wikidata_subgraphs/results")
    assert reply.status_code == 200
    assert all("graph_statistics" in r["path"] for r in reply.json["data"]["artifacts"])
