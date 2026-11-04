import unittest

import pandas as pd

from term_paper.src.common.ch4_reporting import aggregate_framework_results


class Chapter4ReportingTests(unittest.TestCase):
    def test_aggregation_uses_sample_standard_deviation(self):
        frame = pd.DataFrame({
            "dataset_id": ["d"] * 3, "framework": ["numpy"] * 3,
            "seed": [42, 52, 62], "primary_metric": [0.2, 0.4, 0.6],
            "secondary_metric": [1.0, 2.0, 3.0], "training_seconds": [1, 2, 3],
            "inference_ms_per_sample": [0.1, 0.2, 0.3], "parameter_count": [10] * 3,
        })
        row = aggregate_framework_results(frame).iloc[0]
        self.assertAlmostEqual(row["primary_metric_mean"], 0.4)
        self.assertAlmostEqual(row["primary_metric_std"], 0.2)
        self.assertEqual(row["run_count"], 3)


if __name__ == "__main__":
    unittest.main()
