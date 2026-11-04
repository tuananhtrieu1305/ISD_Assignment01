import unittest

import pandas as pd

from term_paper.src.common.ch2_reporting import aggregate_framework_metrics


class Chapter2ReportingTests(unittest.TestCase):
    def test_framework_aggregation_uses_sample_standard_deviation(self):
        frame = pd.DataFrame(
            {
                "dataset_id": ["d", "d", "d"],
                "framework": ["numpy", "numpy", "numpy"],
                "seed": [42, 52, 62],
                "task": ["binary", "binary", "binary"],
                "parameter_count": [10, 10, 10],
                "F1": [0.70, 0.80, 0.90],
                "Accuracy": [0.75, 0.85, 0.95],
                "training_seconds": [1.0, 2.0, 3.0],
                "inference_ms_per_sample": [0.1, 0.2, 0.3],
            }
        )
        result = aggregate_framework_metrics(frame)
        self.assertEqual(len(result), 1)
        row = result.iloc[0]
        self.assertEqual(row["seed_count"], 3)
        self.assertAlmostEqual(row["F1_mean"], 0.8, places=12)
        self.assertAlmostEqual(row["F1_std"], 0.1, places=12)
        self.assertEqual(row["parameter_count"], 10)


if __name__ == "__main__":
    unittest.main()
