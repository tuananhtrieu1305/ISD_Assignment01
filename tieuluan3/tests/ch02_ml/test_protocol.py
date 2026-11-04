import pytest

from src.ch02_ml.protocol import dataset_spec, development_data, run_ids


def test_run_matrix_and_data_test_refusal():
    assert len(run_ids()) == 54 and len(set(run_ids())) == 54
    assert len([name for name in run_ids() if "_mlp_" in name]) == 27
    with pytest.raises(ValueError):
        dataset_spec("ch3_idrid")
    with pytest.raises(ValueError):
        development_data("ch2_ames_housing", "test")
    data = development_data("ch2_ames_housing", "validation")
    assert data["x"].shape == (439, 313) and data["y"].shape == (439, 1)
