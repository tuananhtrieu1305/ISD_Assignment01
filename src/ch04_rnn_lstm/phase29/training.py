"""LSTM adapters reuse frozen canonical recurrent Adam and window training.

Keras uses an ordinary tf.function (not XLA): native LSTM may dispatch cuDNN.
This execution policy is probed and declared before training, not a backend swap.
"""

from src.ch04_rnn_lstm.training import RnnKerasTrainer, RnnTorchTrainer


class LstmTorchTrainer(RnnTorchTrainer):
    def __init__(self, plan, weights, device="gpu"):
        if plan.get("family") != "lstm":
            raise ValueError("LSTM plan required")
        super().__init__(plan, weights, device)


class LstmKerasTrainer(RnnKerasTrainer):
    def __init__(self, plan, weights, device="gpu"):
        if plan.get("family") != "lstm":
            raise ValueError("LSTM plan required")
        super().__init__(plan, weights, device, jit_compile=False)
