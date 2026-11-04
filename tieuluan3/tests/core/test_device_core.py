import numpy as np
import pytest

from src.common.device_core import DeviceMonitor
from src.common.training_core import inference_timing


def test_cpu_memory_and_synchronized_timing():
    monitor = DeviceMonitor("numpy", "cpu")
    monitor.start()
    block = np.ones((100, 100), dtype="float32")
    observed = monitor.finish()
    assert observed["peak_vram_bytes"] == 0
    assert observed["process_peak_ram_bytes"] > 0
    assert block.sum() == 10000
    timing = inference_timing(lambda: block.sum(), warmup=1, repeats=3)
    assert timing["inference_p95_ms"] >= timing["inference_p50_ms"] >= 0
    with pytest.raises(ValueError):
        inference_timing(lambda: None, repeats=0)
    with pytest.raises(ValueError):
        DeviceMonitor("numpy", "gpu")
    with pytest.raises(ValueError):
        DeviceMonitor("unknown", "cpu")
