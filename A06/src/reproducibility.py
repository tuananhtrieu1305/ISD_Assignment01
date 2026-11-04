"""Seed helpers shared by preprocessing and later framework notebooks."""

from __future__ import annotations

import os
import random

import numpy as np

from src.config import SEED


def set_global_seed(seed: int = SEED, *, include_frameworks: bool = False) -> None:
    """Seed Python/NumPy and optionally the installed deep-learning frameworks.

    Framework imports are opt-in so preprocessing does not pay TensorFlow/PyTorch
    startup cost. Later training notebooks can call ``include_frameworks=True``.
    """

    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)

    if not include_frameworks:
        return

    import torch
    import tensorflow as tf

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    tf.keras.utils.set_random_seed(seed)

