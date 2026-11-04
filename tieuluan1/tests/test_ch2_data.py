import unittest
from pathlib import Path

import numpy as np

from term_paper.src.common.ch2_data import prepare_dataset
from term_paper.src.common.ch2_protocol import split_key_digest, validate_split_keys


WORKSPACE = Path(__file__).resolve().parents[2]


class Chapter2DataIntegrationTests(unittest.TestCase):
    def _assert_common(self, dataset, total, split_sizes):
        self.assertEqual(sum(len(dataset.keys[name]) for name in ("train", "val", "test")), total)
        self.assertEqual(
            {name: len(dataset.keys[name]) for name in ("train", "val", "test")},
            split_sizes,
        )
        validate_split_keys(dataset.keys, expected_total=total)
        self.assertEqual(len(split_key_digest(dataset.keys)), 64)
        for name in ("train", "val", "test"):
            self.assertEqual(len(dataset.x[name]), len(dataset.y_model[name]))
            self.assertEqual(len(dataset.x[name]), len(dataset.y_true[name]))
            self.assertTrue(np.isfinite(dataset.x[name]).all())
            self.assertTrue(np.isfinite(dataset.y_model[name]).all())

    def test_diabetes_cleaning_split_and_train_fitted_scaler(self):
        dataset = prepare_dataset(WORKSPACE, "ch2_diabetes_binary")
        self._assert_common(
            dataset,
            total=69057,
            split_sizes={"train": 44196, "val": 11049, "test": 13812},
        )
        self.assertEqual(dataset.task, "binary")
        self.assertEqual(dataset.x["train"].shape[1], 21)
        np.testing.assert_allclose(dataset.x["train"].mean(axis=0), 0.0, atol=2e-5)
        counts = np.bincount(dataset.y_true["train"].astype(int))
        self.assertLess(abs(counts[0] - counts[1]) / counts.sum(), 0.03)

    def test_housing_cleaning_split_and_target_round_trip(self):
        dataset = prepare_dataset(WORKSPACE, "ch2_vietnam_housing")
        self._assert_common(
            dataset,
            total=30223,
            split_sizes={"train": 19342, "val": 4836, "test": 6045},
        )
        self.assertEqual(dataset.task, "regression")
        self.assertGreater(dataset.x["train"].shape[1], 100)
        recovered = dataset.inverse_target(dataset.y_model["test"])
        np.testing.assert_allclose(recovered, dataset.y_true["test"], atol=1e-5, rtol=0)

    def test_customer_feature_build_split_and_class_weight(self):
        dataset = prepare_dataset(WORKSPACE, "ch2_ecommerce_behavior")
        self._assert_common(
            dataset,
            total=10000,
            split_sizes={"train": 6400, "val": 1600, "test": 2000},
        )
        self.assertEqual(dataset.task, "binary")
        self.assertGreater(dataset.x["train"].shape[1], 300)
        self.assertIsNotNone(dataset.class_weight)
        self.assertGreater(dataset.class_weight[1], dataset.class_weight[0])
        self.assertTrue(all(str(key).startswith("C") for key in dataset.keys["test"][:5]))


if __name__ == "__main__":
    unittest.main()
