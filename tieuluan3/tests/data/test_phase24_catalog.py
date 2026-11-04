"""Read measured local artifacts only; never synthesize dataset counts."""

from scripts.export_phase24_tables import tables_for
from scripts.prepare_phase24 import build_catalog


def test_catalog_connects_all_18_sources_and_only_nine_training_splits():
    catalog = build_catalog()
    assert len(catalog["datasets"]) == 18
    assert sum(row["split"] is not None for row in catalog["datasets"]) == 9
    assert all(row["split"] is None for row in catalog["datasets"] if row["dataset_id"].startswith("ch6_"))


def test_exported_summary_keeps_unknown_distinct_from_zero():
    measured = {
        "scope": "measured_tabular",
        "size_and_schema": {
            "rows": 10,
            "counts": {"train": 7, "validation": 2, "test": 1},
            "matched_train_count": 5,
        },
        "distribution_summary": {"target_by_partition": {"train": {"0": 4, "1": 3}}},
    }
    tables = tables_for("synthetic", measured, None)
    assert tables["summary"][0]["train"] == 7
    assert tables["summary"][0]["matched_train"] == 5
    assert tables["summary"][0]["quarantine"] is None
    assert tables["target_distribution"][0]["value"] == 4
