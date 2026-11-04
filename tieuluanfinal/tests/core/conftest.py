"""Bound CPU oversubscription for synthetic tests; no dependency/env changes."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")


def pytest_sessionstart(session):
    # Keras has its own independent environment, so never import torch here.
    if os.environ.get("KERAS_BACKEND") == "torch":
        import torch

        torch.set_num_threads(2)
