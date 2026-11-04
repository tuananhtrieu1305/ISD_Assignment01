import unittest

import pandas as pd

from term_paper.src.common.ch3_reporting import aggregate_framework_results


class Chapter3ReportingTests(unittest.TestCase):
    def test_aggregation_uses_sample_standard_deviation(self):
        frame = pd.DataFrame(
            {
                "dataset_id": ["d", "d", "d"],
                "framework": ["numpy", "numpy", "numpy"],
                "seed": [42, 52, 62],
                "macro_f1": [0.2, 0.4, 0.6],
                "accuracy": [0.3, 0.5, 0.7],
                "training_seconds": [1.0, 2.0, 3.0],
                "inference_ms_per_sample": [0.1, 0.2, 0.3],
                "parameter_count": [10, 10, 10],
            }
        )
        result = aggregate_framework_results(frame).iloc[0]
        self.assertAlmostEqual(result["macro_f1_mean"], 0.4)
        self.assertAlmostEqual(result["macro_f1_std"], 0.2)
        self.assertEqual(result["run_count"], 3)
        self.assertEqual(result["parameter_count"], 10)


if __name__ == "__main__":
    unittest.main()
