"""Declaration/holdout boundary and hash guards."""

import json

import pytest

from src.ch04_rnn_lstm import protocol
from src.common.artifact_core import write_once


def test_declared_matrix_and_no_test_controller_mode():
    neural = [
        protocol.run_id(d, m, s, f)
        for d in protocol.DATASETS
        for f in protocol.FOLDS
        for s in protocol.SEEDS
        for m in protocol.IMPLEMENTATIONS
    ]
    baseline = [
        protocol.run_id(d, m, 42, f)
        for d in protocol.DATASETS
        for f in protocol.FOLDS
        for m in ("last_value", "seasonal_naive")
    ]
    assert len(set(neural)) == 108 and len(set(baseline)) == 24
    assert sum(name.endswith("_main") for name in neural) == 27
    assert not set(neural) & set(baseline)
    text = (protocol.ROOT / "scripts/phase28_controller.py").read_text()
    assert 'choices=("train", "status")' in text
    assert "evaluate_run" not in text and "test_seals" not in text


def test_hash_guards_refuse_tampering_and_path_escape(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "ROOT", tmp_path)
    monkeypatch.setattr(protocol, "BASE", tmp_path / "artifacts/phase28")
    spec = tmp_path / "experiments/protocol.json"
    write_once(spec, {"synthetic": True})
    monkeypatch.setattr(protocol, "PROTOCOL", spec)
    write_once(tmp_path / "uv.lock", {"synthetic": True})
    monkeypatch.setattr(protocol, "code_info", lambda: {"synthetic": True})
    config = tmp_path / "experiments/config.json"
    model = tmp_path / "artifacts/model.json"
    write_once(config, {"synthetic": True})
    write_once(model, {"synthetic": True})
    release = {
        "code": {"synthetic": True},
        "protocol": protocol.ref(spec),
        "environment": protocol.ref(tmp_path / "uv.lock"),
        "source_files": [],
        "runs": [{"config": protocol.ref(config), "model_contract": protocol.ref(model)}],
    }
    write_once(protocol.BASE / "release.json", release)
    assert protocol.check_sources() == release
    config.write_text(json.dumps({"tampered": True}))
    with pytest.raises(ValueError):
        protocol.check_sources()
    with pytest.raises(ValueError):
        protocol.checked({"path": "../outside", "sha256": "a" * 64})
