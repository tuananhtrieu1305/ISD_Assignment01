"""Temp-directory snapshot workflow only; no fake evidence is published to real artifacts."""

import json

from src.ch05_knowledge_rag import preservation as module


def test_synthetic_snapshot_creation_and_idempotent_verification(tmp_path, monkeypatch):
    original_ref, original_verify = module.ref, module.verify_records
    names = [
        "term_paper/__init__.py",
        "apps/api/knowledge_rag_service.py",
        "report/sections/05_knowledge_rag.md",
        "report/references/bibliography.bib",
        "uv.lock",
        "pyproject.toml",
        "artifacts/manifests/environment.json",
        "artifacts/manifests/phase29/experiment_lock.json",
        "releases/v2/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx",
    ]
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic fixture, not a real artifact")
    for name in ("phase22/spec_lock.json", "phase24/data_lock.json", "phase25/core_lock.json"):
        path = tmp_path / "artifacts/manifests" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"files": []}))
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "BASE", tmp_path / "artifacts/manifests/phase30")
    monkeypatch.setattr(module, "historical_baseline", lambda: {"synthetic_fixture": True})
    monkeypatch.setattr(module, "ref", lambda path: original_ref(path, tmp_path))
    monkeypatch.setattr(module, "verify_records", lambda records: original_verify(records, tmp_path))
    first = module.create_snapshot()
    second = module.create_snapshot()
    assert first == second
    assert first["baseline"] == {"synthetic_fixture": True}
    assert len(first["files"]) == 12
