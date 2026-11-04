"""Content assembly integration tests read locked artifacts, not model predictions."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts import build_phase34 as builder
from scripts.phase34_editor import markdown_blocks


def test_value_rendering_and_tables():
    assert builder.cell("a|b\nc") == "a&#124;b c"
    assert "bản đầy đủ" in builder.cell("x" * 500)
    assert "Không có bản ghi" in builder.json_table([])
    assert "| Trường |" in builder.json_table({"x": 1})
    assert "| a | b |" in builder.json_table([{"a": 1}, {"b": 2}])
    assert "| Giá trị |" in builder.json_table([1])
    assert builder.json_table("x") == "x\n"


def test_bibliography_rejects_incomplete():
    with pytest.raises(ValueError, match="Incomplete"):
        builder.bibliography_text({"x": "@misc{x,title={A}}"}, {"x": 1})


def test_integration_is_deterministic_without_inference(monkeypatch, tmp_path):
    production = builder.OUT
    with TemporaryDirectory(prefix=".phase34-fixture-", dir=builder.ROOT / "report") as disposable:
        output = Path(disposable)
        assert output.parent.resolve() == (builder.ROOT / "report").resolve()
        assert output != production, "Integration test must not overwrite publication"
        base = output / "evidence"
        (output / "inputs").mkdir()
        for path in (production / "inputs").iterdir():
            if path.is_file():
                (output / "inputs" / path.name).write_bytes(path.read_bytes())
        monkeypatch.setattr(builder, "OUT", output)
        monkeypatch.setattr(builder, "BASE", base)
        base.mkdir()
        (base / "preserve_before.json").write_text("{}")
        builder.build()
        first = (output / "manuscript.md").read_bytes()
        builder.build()
        assert (output / "manuscript.md").read_bytes() == first
        manifest = json.loads((base / "manuscript_manifest.json").read_text())
        assert len(manifest["chapters"]) == 6
        assert len(manifest["data_cards"]) == 18 and len(manifest["model_contracts"]) == 36
        assert manifest["models_retrained"] == 0 and not manifest["historical_test_evaluation_executed"]
        assert manifest["docx_authored"] is False and manifest["page_count"] is None
        headings = [
            b["text"]
            for b in markdown_blocks(first.decode())
            if b["kind"] == "heading" and b["text"].startswith("# CHƯƠNG")
        ]
        assert len(headings) == 6
    # Only the newly owned, validated disposable directory is cleaned by tempfile.


def test_released_writer_refuses_overwrite(monkeypatch, tmp_path):
    monkeypatch.setattr(builder, "BASE", tmp_path)
    (tmp_path / "experiment_lock.json").write_text("{}")
    with pytest.raises(ValueError, match="released"):
        builder.save(tmp_path / "new.md", "x")


def test_missing_parent_audit_refuses_build(monkeypatch, tmp_path):
    monkeypatch.setattr(builder, "BASE", tmp_path)
    with pytest.raises(ValueError, match="Parent audit"):
        builder.build()
