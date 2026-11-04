"""CPU serving is separated from native training implementation."""

import pytest

from scripts.demo_phase29 import infer, sample_request


@pytest.mark.parametrize("family", ["cnn", "mlp", "rag"])
def test_demo_rejects_wrong_family_before_loading_data(family):
    with pytest.raises(ValueError):
        sample_request("ch4_gold_pink_sheet", family)


def test_demo_rejects_undeclared_seed_before_loading_models():
    with pytest.raises(ValueError):
        infer({}, seed=99)
