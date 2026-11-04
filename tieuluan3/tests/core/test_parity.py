import numpy as np
import pytest

from src.common.parity import gradient_parity


def test_normwise_gradient_error_and_zero_case():
    reference = {"w": np.array([1.0, 0.00037]), "b": np.zeros(2)}
    actual = {"w": np.array([1.0, 0.000373]), "b": np.zeros(2)}
    result = gradient_parity(reference, actual)
    assert result["max_relative_l2_error"] < 1e-3
    assert result["max_abs_error"] > 0
    with pytest.raises(ValueError):
        gradient_parity(reference, {"w": np.ones(2), "b": np.ones(2)})
    with pytest.raises(ValueError):
        gradient_parity(reference, {"w": np.ones(3), "b": np.zeros(2)})
    with pytest.raises(ValueError):
        gradient_parity(reference, {"w": np.array([np.nan, 1]), "b": np.zeros(2)})
