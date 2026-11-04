"""Versioned visual/scope correction; saved metrics, predictions and citations unchanged."""

import re

from src.ch05_knowledge_rag.presentation_r2 import error_scope, render_manuscript_r2
from src.common.contracts import ROOT


def test_entity_linking_counts_separate_test_and_challenge():
    result = error_scope()
    assert result["test"]["medical"].get("entity_linking", 0) == 0
    assert result["test"]["finance"]["entity_linking"] == 1053
    assert result["challenge"]["medical"]["entity_linking"] == 8
    assert result["challenge"]["finance"]["entity_linking"] == 8
    assert result["aggregate"]["medical"]["entity_linking"] == 8
    assert result["aggregate"]["finance"]["entity_linking"] == 1061
    assert result["counts"] == {
        "medical": {"test": 62, "challenge": 8},
        "finance": {"test": 1147, "challenge": 8},
    }


def test_r2_corrects_scope_not_scores_or_citation_ids():
    old = (ROOT / "report/sections/05_knowledge_rag.md").read_text(encoding="utf-8")
    new = render_manuscript_r2(old)
    assert set(re.findall(r"@([A-Za-z0-9_-]+)", old)) == set(re.findall(r"@([A-Za-z0-9_-]+)", new))
    assert "0 nhãn entity linking" in new
    assert "1.053" in new
    assert "TEST+challenge" in new
    assert "không phải benchmark QA thứ ba" in new
    assert "r2/dataset_overview.png" in new
    assert "r2/graph_paths.png" in new
    assert "r2/validation_ablation.png" in new
    assert "r2/test_errors.png" in new
    assert "toàn corpus compact" in new
