import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from term_paper.src.common.ch2_metrics import (
    compute_classification_metrics,
    compute_regression_metrics,
    metrics_from_prediction_csv,
)
from term_paper.src.common.ch2_protocol import split_key_digest, validate_split_keys


class MetricReproductionTests(unittest.TestCase):
    def test_classification_metrics_reproduce_from_prediction_csv(self):
        frame = pd.DataFrame(
            {
                "task": ["binary"] * 6,
                "y_true": [0, 0, 1, 1, 1, 0],
                "y_score": [0.1, 0.4, 0.8, 0.7, 0.2, 0.3],
                "y_pred": [0, 0, 1, 1, 0, 0],
            }
        )
        expected = compute_classification_metrics(
            frame["y_true"], frame["y_pred"], frame["y_score"]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.csv"
            frame.to_csv(path, index=False)
            actual = metrics_from_prediction_csv(path)
        for key, value in expected.items():
            self.assertAlmostEqual(value, actual[key], places=12)

    def test_regression_metrics_reproduce_from_prediction_csv(self):
        frame = pd.DataFrame(
            {
                "task": ["regression"] * 4,
                "y_true": [1.0, 2.0, 3.0, 4.0],
                "y_pred": [1.1, 1.8, 3.2, 3.9],
            }
        )
        expected = compute_regression_metrics(frame["y_true"], frame["y_pred"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.csv"
            frame.to_csv(path, index=False)
            actual = metrics_from_prediction_csv(path)
        for key, value in expected.items():
            self.assertAlmostEqual(value, actual[key], places=12)


class SplitProtocolTests(unittest.TestCase):
    def test_split_keys_are_disjoint_and_digest_is_deterministic(self):
        split_keys = {
            "train": np.array(["a", "b", "c"]),
            "val": np.array(["d", "e"]),
            "test": np.array(["f", "g"]),
        }
        validate_split_keys(split_keys, expected_total=7)
        digest_1 = split_key_digest(split_keys)
        digest_2 = split_key_digest({key: values.copy() for key, values in split_keys.items()})
        self.assertEqual(digest_1, digest_2)
        self.assertEqual(len(digest_1), 64)

    def test_split_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_split_keys(
                {
                    "train": np.array(["a", "b"]),
                    "val": np.array(["b", "c"]),
                    "test": np.array(["d"]),
                },
                expected_total=5,
            )


if __name__ == "__main__":
    unittest.main()
