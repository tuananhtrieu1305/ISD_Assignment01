import pytest

from src.ch02_ml.training import KerasTrainer
from tests.ch02_ml.native_checks import check_native


@pytest.mark.parametrize("task", ["binary", "mse"])
@pytest.mark.parametrize("device", ["cpu", "gpu"])
def test_keras_graph_update_and_resume(task, device):
    trainer = check_native(KerasTrainer, device, task)
    assert trainer.model.device == ("/GPU:0" if device == "gpu" else "/CPU:0")
