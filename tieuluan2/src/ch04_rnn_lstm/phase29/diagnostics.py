"""Fixed TRAIN gates/carry diagnostics; not causal attribution or TEST tuning."""

import numpy as np

from src.ch04_rnn_lstm.diagnostics import gradient_diagnostics
from src.common.numpy_engine import NumpyNetwork


def gate_diagnostics(plan, weights, x, y):
    if plan.get("family") != "lstm":
        raise ValueError("LSTM plan required for gate diagnostics")
    network = NumpyNetwork(plan, weights)
    network.forward(x)
    layers = []
    for step, _, _, states in network.cache:
        if step["kind"] != "lstm":
            continue
        gates = {}
        for name, pos in (("input", 3), ("forget", 4), ("candidate", 5), ("output", 6)):
            values = np.stack([s[pos] for s in states], axis=1).astype("float64")
            gates[name] = {
                "min": float(values.min()),
                "max": float(values.max()),
                "mean": float(values.mean()),
                "mean_by_time": values.mean(axis=(0, 2)).tolist(),
                "saturation_fraction": float(np.mean(np.abs(values) > 0.95))
                if name == "candidate"
                else float(np.mean((values < 0.05) | (values > 0.95))),
            }
        carry_errors = [np.max(np.abs(s[7] - (s[4] * s[2] + s[3] * s[5]))) for s in states]
        hidden_errors = [
            np.max(np.abs(states[t + 1][1] - s[6] * np.tanh(s[7]))) for t, s in enumerate(states[:-1])
        ]
        layers.append(
            {
                "layer_id": step["id"],
                "gates": gates,
                "carry_equation_max_absolute_error": float(max(carry_errors)),
                "hidden_equation_max_absolute_error": float(max(hidden_errors, default=0)),
                "initial_hidden_max_absolute": float(np.max(np.abs(states[0][1]))),
                "initial_carry_max_absolute": float(np.max(np.abs(states[0][2]))),
            }
        )
    return {
        **gradient_diagnostics(plan, weights, x, y),
        "layers": layers,
        "state_reset_per_window": True,
        "scope": "First fixed TRAIN windows only; sigmoid gates in [0,1], tanh candidate in [-1,1]. Saturation descriptive at .05/.95; no causal or long-memory superiority claim.",
    }
