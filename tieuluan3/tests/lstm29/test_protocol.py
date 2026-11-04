"""New LSTM declaration is separate from immutable RNN evidence."""

import itertools

import pytest

from src.ch04_rnn_lstm.phase29 import protocol
from src.common.artifact_core import write_once


def test_complete_lstm_matrix_and_separate_paths():
    ids = {
        protocol.run_id(d, m, s, f)
        for d, m, s, f in itertools.product(
            protocol.DATASETS, protocol.IMPLEMENTATIONS, protocol.SEEDS, protocol.FOLDS
        )
    }
    assert len(ids) == 108
    assert sum(x.endswith("_main") for x in ids) == 27
    assert all("_lstm_" in x for x in ids)
    assert protocol.BASE.name == "phase29" and protocol.MODELS.name == "ch04_lstm"
    assert len(protocol.SOURCE_FILES) == len(set(protocol.SOURCE_FILES))
    assert all((protocol.ROOT / p).exists() for p in protocol.SOURCE_FILES)


def test_artifact_paths_cannot_escape_or_change(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "ROOT", tmp_path)
    path = tmp_path / "artifact.json"
    write_once(path, {"synthetic": True})
    ref = protocol.ref(path)
    assert protocol.checked(ref) == path
    with pytest.raises(ValueError):
        protocol.checked({**ref, "sha256": "0" * 64})
    with pytest.raises(ValueError):
        protocol.checked({"path": "../escape.json", "sha256": "0" * 64})


def test_controller_never_reports_finished_after_worker_failure():
    source = (protocol.ROOT / "scripts/phase29_controller.py").read_text()
    assert 'outcome = "failed"' in source and '"status": outcome' in source
    assert "scripts.phase29_worker" in source and "phase29_coverage.ini" in source


def test_pretraining_declaration_reuses_no_test_and_cpu_gate_policy():
    source = (protocol.ROOT / "scripts/prepare_phase29.py").read_text()
    assert "methods = IMPLEMENTATIONS" in source
    assert '"reference": "native_cpu"' in source
    assert '"baseline_runs": 0' in source
    assert '"baseline_runs": 24' not in source
    assert '"test_evaluation_executed": False' in source
