import numpy as np
import pytest

from src.ch02_ml.diagnostics import calibration, group_diagnostics, groups_for_frame


def test_cdc_group_array_is_pickle_free(tmp_path):
    import pandas as pd

    groups = groups_for_frame("ch2_cdc_diabetes", pd.DataFrame({"sex": [0, 1]}))
    assert groups.dtype.kind == "U"
    path = tmp_path / "groups.npz"
    np.savez_compressed(path, groups=groups)
    with np.load(path, allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["groups"], groups)


def test_calibration_support_and_group_metrics():
    y = np.array([0, 1, 0, 1])
    prob = np.array([0.1, 0.8, 0.4, 0.6])
    result = calibration(y, prob, bins=5)
    assert sum(row["count"] for row in result["bins"]) == 4
    assert result["brier"] == pytest.approx(np.mean((y - prob) ** 2))
    groups = group_diagnostics(y, prob, np.array(["a", "a", "b", "b"]), "binary")
    assert groups["a"]["count"] == 2 and groups["a"]["recall"] == 1
    undefined = group_diagnostics([0], [0.2], ["a"], "binary")
    assert undefined["a"]["recall"] is None
    with pytest.raises(ValueError):
        calibration(y, prob, bins=0)
