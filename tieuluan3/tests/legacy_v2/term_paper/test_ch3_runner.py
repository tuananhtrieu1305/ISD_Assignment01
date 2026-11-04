import unittest

import pandas as pd

from term_paper.src.common.run_ch3_experiments import validate_matched_prediction_keys


class Chapter3RunnerTests(unittest.TestCase):
    def test_matched_prediction_keys_accept_identical_ordered_samples(self):
        frames = {
            framework: pd.DataFrame(
                {"sample_key": ["a", "b"], "y_true": [0, 1], "seed": [42, 42]}
            )
            for framework in ("numpy", "keras", "pytorch")
        }
        validate_matched_prediction_keys(frames)

    def test_matched_prediction_keys_reject_mismatch(self):
        frames = {
            "numpy": pd.DataFrame({"sample_key": ["a", "b"], "y_true": [0, 1]}),
            "keras": pd.DataFrame({"sample_key": ["a", "c"], "y_true": [0, 1]}),
            "pytorch": pd.DataFrame({"sample_key": ["a", "b"], "y_true": [0, 1]}),
        }
        with self.assertRaises(ValueError):
            validate_matched_prediction_keys(frames)


if __name__ == "__main__":
    unittest.main()
