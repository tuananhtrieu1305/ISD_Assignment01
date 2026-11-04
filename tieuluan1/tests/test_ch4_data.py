import unittest

import numpy as np

from term_paper.src.common.ch4_data import (
    class_weights,
    prepare_customer_benchmark,
    prepare_stock_benchmark,
    stratified_subset,
)
from term_paper.src.common.ch4_protocol import split_digest, validate_temporal_splits


class Chapter4DataTests(unittest.TestCase):
    def test_stratified_subset_is_reproducible(self):
        y = np.asarray([0] * 80 + [1] * 20)
        first = stratified_subset(y, 40, 42)
        second = stratified_subset(y, 40, 42)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(int(y[first].sum()), 8)

    def test_customer_shapes_keys_and_temporal_boundaries(self):
        data = prepare_customer_benchmark({"train": 300, "val": 100, "test": 100})
        self.assertEqual(data["x_train"].shape, (300, 8, 5))
        self.assertEqual(data["x_test"].shape, (100, 8, 5))
        self.assertEqual(len(np.unique(data["keys"]["test"])), 100)
        validate_temporal_splits(data["dates"])
        self.assertEqual(data["split_sha256"], split_digest(data["keys"]))
        self.assertGreater(class_weights(data["y_train"])[1], 1.0)

    def test_stock_uses_complete_a06_arrays_and_inverse_target(self):
        data = prepare_stock_benchmark()
        self.assertEqual(data["x_train"].shape, (1915, 30, 5))
        self.assertEqual(data["x_val"].shape, (411, 30, 5))
        self.assertEqual(data["x_test"].shape, (410, 30, 5))
        restored = data["target_scaler"].inverse_transform(
            data["y_test"].reshape(-1, 1)
        ).reshape(-1)
        np.testing.assert_allclose(restored, data["y_test_real"], atol=1e-4)
        validate_temporal_splits(data["dates"])


if __name__ == "__main__":
    unittest.main()
