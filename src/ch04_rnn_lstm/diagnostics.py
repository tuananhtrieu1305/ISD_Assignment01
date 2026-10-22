"""Fixed TRAIN input-gradient illustration, not causal importance or TEST tuning."""

import numpy as np

from src.common.numpy_engine import NumpyNetwork


def gradient_diagnostics(plan, weights, x, y):
    model = NumpyNetwork(plan, weights)
    loss, gradients, dx = model.loss_gradients(x, y, "mse")
    per_time = np.sqrt(np.mean(dx.astype("float64") ** 2, axis=(0, 2)))
    first, last = float(per_time[0]), float(per_time[-1])
    return {
        "input_split": "train",
        "loss": loss,
        "input_gradient_rms_by_time_oldest_to_newest": per_time.tolist(),
        "oldest_to_newest_ratio": first / last if last > 0 else None,
        "ratio_undefined_reason": None if last > 0 else "Newest input gradient is zero",
        "weight_gradient_l2": {
            key: float(np.linalg.norm(value.astype("float64"))) for key, value in gradients.items()
        },
        "recurrent_spectral_norms": {
            key: float(np.linalg.norm(value.astype("float64"), 2))
            for key, value in weights.items()
            if key.endswith("/u")
        },
        "scope": "Gradient of normalized MSE on first fixed TRAIN windows; descriptive local sensitivity, not causal attribution or proof of long-memory ability",
    }
