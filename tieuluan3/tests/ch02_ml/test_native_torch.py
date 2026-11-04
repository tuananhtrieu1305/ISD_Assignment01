import pytest

from src.ch02_ml.training import TorchTrainer
from tests.ch02_ml.native_checks import check_native


@pytest.mark.parametrize("task", ["binary", "mse"])
@pytest.mark.parametrize("device", ["cpu", "gpu"])
def test_torch_update_and_resume(task, device):
    trainer = check_native(TorchTrainer, device, task)
    assert str(trainer.model.device) == ("cuda:0" if device == "gpu" else "cpu")
