"""Read-only preservation audit after training; never run a TEST evaluator."""

import csv
import gzip

from scripts.verify_phase23 import verify_registry
from src.common.artifact_core import sha256_file
from src.common.contracts import ROOT, read_json


def test_phase26_preserves_raw_sources_v2_and_ch5_frozen_results():
    result = verify_registry(deep=False)
    assert result["status"] == "PASS"
    assert result["physical_files_hashed"] == 11357
    assert result["ch5_test_run_count"] == 1
    assert result["ch5_sealed_prediction_files_unchanged"] == 10
    assert (
        sha256_file(ROOT / "releases/v2/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx")
        == "d7286dd4867e6216f197414e42fc112a3759621c017839fa9b1491b7c5dbfa51"
    )
    counts = {"configs": 0, "metrics": 0}
    with gzip.open(
        ROOT / "artifacts/manifests/phase20/before-files.csv.gz", "rt", encoding="utf-8-sig", newline=""
    ) as stream:
        for row in csv.DictReader(stream):
            for kind, old, new in (
                ("configs", "term_paper/knowledge_rag/config/", "experiments/configs/ch5/"),
                ("metrics", "term_paper/knowledge_rag/artifacts/metrics/", "artifacts/metrics/ch5/"),
            ):
                if row["path"].startswith(old):
                    assert sha256_file(ROOT / (new + row["path"][len(old) :])) == row["sha256"]
                    counts[kind] += 1
    assert counts == {"configs": 7, "metrics": 23}
    assert read_json(ROOT / "artifacts/manifests/ch5/phase15_test_run.json")["run_count"] == 1
