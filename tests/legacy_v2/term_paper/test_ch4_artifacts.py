import unittest

import numpy as np

from term_paper.src.common.ch4_experiment import build_prediction_frame
from term_paper.src.common.ch4_metrics import (
    binary_metrics,
    regression_metrics,
    select_f1_threshold,
)


class Chapter4ArtifactTests(unittest.TestCase):
    def test_threshold_is_selected_only_from_supplied_validation_values(self):
        threshold, table = select_f1_threshold(
            [0, 0, 1, 1], [0.1, 0.4, 0.6, 0.9], thresholds=[0.3, 0.5, 0.7]
        )
        self.assertEqual(threshold, 0.5)
        self.assertEqual(len(table), 3)

    def test_binary_metrics_include_imbalance_outputs(self):
        result = binary_metrics([0, 0, 1, 1], [0.1, 0.7, 0.6, 0.9], 0.5)
        self.assertIn("roc_auc", result)
        self.assertIn("pr_auc", result)
        self.assertEqual(result["tp"], 2)

    def test_regression_metrics_and_prediction_frame(self):
        result = regression_metrics([10, 12], [9, 13])
        self.assertAlmostEqual(result["mae"], 1.0)
        frame = build_prediction_frame(
            "stock", "numpy", ["d1", "d2"], [10, 12], [9, 13],
            seed=42, task="regression", threshold=None, model_sha256="m",
            preprocessor_sha256="p", split_sha256="s", baseline=[9.5, 11.5]
        )
        self.assertEqual(frame["sample_key"].tolist(), ["d1", "d2"])
        self.assertIn("naive_last_close", frame)


if __name__ == "__main__":
    unittest.main()
