"""Explicit device selection and allocator measurements, never byte estimates."""

from __future__ import annotations

import resource
import time


class DeviceMonitor:
    def __init__(self, backend, device):
        if (
            backend not in {"numpy", "torch", "tensorflow"}
            or device not in {"cpu", "gpu"}
            or backend == "numpy"
            and device != "cpu"
        ):
            raise ValueError("Unsupported backend/device")
        self.backend = backend
        self.device = device
        self.started = None
        if backend == "torch":
            import torch

            self.framework = torch
            if device == "gpu" and not torch.cuda.is_available():
                raise RuntimeError("GPU requested but unavailable")
        elif backend == "tensorflow":
            import tensorflow as tf

            self.framework = tf
            if device == "gpu" and not tf.config.list_physical_devices("GPU"):
                raise RuntimeError("GPU requested but unavailable")

    def synchronize(self):
        if self.device == "gpu":
            if self.backend == "torch":
                self.framework.cuda.synchronize()
            else:
                self.framework.constant(0.0).numpy()  # workload probes also materialize the returned tensor

    def start(self):
        self.synchronize()
        if self.device == "gpu":
            if self.backend == "torch":
                self.framework.cuda.reset_peak_memory_stats()
            else:
                self.framework.config.experimental.reset_memory_stats("GPU:0")
        self.started = time.perf_counter()

    def finish(self):
        if self.started is None:
            raise ValueError("Memory monitor was not started")
        self.synchronize()
        peak = reserved = 0
        if self.device == "gpu":
            if self.backend == "torch":
                peak = self.framework.cuda.max_memory_allocated()
                reserved = self.framework.cuda.max_memory_reserved()
            else:
                peak = self.framework.config.experimental.get_memory_info("GPU:0")["peak"]
        return {
            "backend": self.backend,
            "requested_device": self.device,
            "wall_seconds": time.perf_counter() - self.started,
            "peak_vram_bytes": int(peak),
            "peak_vram_reserved_bytes": int(reserved),
            "process_peak_ram_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
            "ram_scope": "Linux process lifetime high-water RSS; not per-model incremental RAM",
            "vram_scope": "Framework allocator peak since reset; excludes driver/other processes; TensorFlow reserved not reported",
        }
