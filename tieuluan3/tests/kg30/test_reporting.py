"""Historical metrics and manuscript are transforms of saved evidence, not TEST reruns."""

import re

from src.ch05_knowledge_rag.reporting import historical_metrics, render_manuscript
from src.common.contracts import ROOT


def test_historical_csv_json_and_saved_prediction_count_match():
    result = historical_metrics()
    assert len(result["rows"]) == 10
    assert result["saved_prediction_rows"] == 6045
    assert result["test_run_count"] == 1
    assert result["new_test_evaluation_executed"] is False
    medical = next(r for r in result["rows"] if r["domain"] == "medical" and r["model_id"] == "B4")
    assert medical["chunk_recall_at_5"] == "0.580645"


def test_manuscript_retains_citations_but_moves_agent_to_short_bridge():
    old = (ROOT / "report/sections/05_knowledge_rag.md").read_text(encoding="utf-8")
    new = render_manuscript(old)
    assert set(re.findall(r"@([A-Za-z0-9_-]+)", old)) == set(re.findall(r"@([A-Za-z0-9_-]+)", new))
    assert "## 5.7. Cầu nối sang hệ đa tác tử" in new
    assert "## 5.8. Triển khai ngắn gọn" in new
    assert "## 5.6. Deploy Agent" not in new
    assert "operatorname{BM25}" not in new
    assert "không phải benchmark QA thứ ba" in new
    assert "../../assets/ch5_knowledge_rag/" in new
    assert "source_sha256" in new


def test_manuscript_figures_point_to_existing_or_generated_phase30_assets():
    old = (ROOT / "report/sections/05_knowledge_rag.md").read_text(encoding="utf-8")
    new = render_manuscript(old)
    parent = ROOT / "report/sections/v3"
    for name in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", new):
        path = (parent / name).resolve()
        assert path.is_relative_to(ROOT)
        assert path.exists() or "/artifacts/figures/phase30/" in str(path)
