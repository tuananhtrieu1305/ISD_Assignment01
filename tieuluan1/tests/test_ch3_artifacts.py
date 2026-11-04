import unittest

import numpy as np

from term_paper.src.common.ch3_experiment import build_prediction_frame
from term_paper.src.common.ch3_metrics import multiclass_metrics


class Chapter3ArtifactTests(unittest.TestCase):
    def test_multiclass_metrics_match_known_values(self):
        y_true = np.asarray([0, 0, 1, 1, 2, 2])
        y_pred = np.asarray([0, 1, 1, 1, 2, 0])
        result = multiclass_metrics(y_true, y_pred, labels=[0, 1, 2])
        self.assertAlmostEqual(result["accuracy"], 4 / 6)
        self.assertIn("macro_f1", result)
        self.assertEqual(result["support_class_1"], 2)
        self.assertAlmostEqual(result["recall_class_1"], 1.0)

    def test_prediction_frame_preserves_probabilities_and_provenance(self):
        probabilities = np.asarray([[0.7, 0.2, 0.1], [0.1, 0.3, 0.6]])
        frame = build_prediction_frame(
            dataset_id="toy",
            framework="numpy",
            keys=["a", "b"],
            y_true=[0, 2],
            probabilities=probabilities,
            model_sha256="model",
            preprocessor_sha256="prep",
            split_sha256="split",
            seed=42,
        )
        self.assertEqual(frame["y_pred"].tolist(), [0, 2])
        self.assertEqual(frame["sample_key"].tolist(), ["a", "b"])
        self.assertEqual(frame["chapter"].unique().tolist(), [3])
        np.testing.assert_allclose(frame[["prob_0", "prob_1", "prob_2"]].sum(axis=1), 1.0)


if __name__ == "__main__":
    unittest.main()
