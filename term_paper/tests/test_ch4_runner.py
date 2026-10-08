import unittest

import pandas as pd

from term_paper.src.common.run_ch4_experiments import validate_matched_prediction_keys


class Chapter4RunnerTests(unittest.TestCase):
    def test_identical_keys_and_targets_pass(self):
        frames = {
            name: pd.DataFrame({"sample_key": ["a", "b"], "y_true": [0, 1]})
            for name in ("numpy", "keras", "pytorch")
        }
        validate_matched_prediction_keys(frames)

    def test_different_order_fails(self):
        frames = {
            "numpy": pd.DataFrame({"sample_key": ["a", "b"], "y_true": [0, 1]}),
            "keras": pd.DataFrame({"sample_key": ["b", "a"], "y_true": [1, 0]}),
            "pytorch": pd.DataFrame({"sample_key": ["a", "b"], "y_true": [0, 1]}),
        }
        with self.assertRaises(ValueError):
            validate_matched_prediction_keys(frames)


if __name__ == "__main__":
    unittest.main()
