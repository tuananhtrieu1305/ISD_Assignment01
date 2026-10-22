"""Controller guards prohibit orphan model execution and missing finalization."""

import pytest

from scripts import phase29_test_r1 as runner
from src.ch04_rnn_lstm.export_r2 import ORPHAN


def test_orphan_cannot_enter_native_worker(monkeypatch):
    monkeypatch.setattr(runner, "check_revision", lambda: {"approved_run_ids": ["future_run"]})
    monkeypatch.setattr(runner, "evaluate_member", lambda *a: pytest.fail("Never forward orphan again"))
    with pytest.raises(ValueError, match="whitelist"):
        runner.worker(ORPHAN)


def test_continue_requires_saved_orphan_finalization(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "REV", tmp_path)
    monkeypatch.setattr(runner, "check_revision", dict)
    with pytest.raises(ValueError, match="Finalize"):
        runner.continue_batch()
