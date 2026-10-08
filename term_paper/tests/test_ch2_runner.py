import tempfile
import unittest
from pathlib import Path

import numpy as np

from term_paper.src.common.ch2_experiment import (
    artifact_suffix,
    build_prediction_frame,
    select_binary_threshold,
    sha256_file,
)


class ExperimentArtifactTests(unittest.TestCase):
    def test_seed_suffix_preserves_primary_names_and_separates_repeats(self):
        self.assertEqual(artifact_suffix(42), "")
        self.assertEqual(artifact_suffix(52), "_seed52")
        self.assertEqual(artifact_suffix(62), "_seed62")

    def test_threshold_is_selected_only_from_given_validation_values(self):
        y_true = np.array([0, 0, 1, 1, 1, 0])
        score = np.array([0.10, 0.20, 0.45, 0.55, 0.80, 0.40])
        threshold, table = select_binary_threshold(y_true, score)
        self.assertAlmostEqual(threshold, 0.41, places=12)
        self.assertEqual(len(table), 61)
        self.assertIn("F1", table.columns)

    def test_prediction_frame_contains_provenance_columns(self):
        frame = build_prediction_frame(
            dataset_id="demo",
            framework="numpy",
            task="binary",
            keys=np.array(["a", "b"]),
            y_true=np.array([0, 1]),
            y_score=np.array([0.2, 0.8]),
            y_pred=np.array([0, 1]),
            threshold=0.5,
            model_sha256="m" * 64,
            preprocessor_sha256="p" * 64,
            split_sha256="s" * 64,
        )
        required = {
            "chapter",
            "dataset_id",
            "framework",
            "seed",
            "split",
            "sample_key",
            "task",
            "y_true",
            "y_score",
            "y_pred",
            "threshold",
            "model_sha256",
            "preprocessor_sha256",
            "split_sha256",
        }
        self.assertTrue(required.issubset(frame.columns))
        self.assertEqual(frame["sample_key"].tolist(), ["a", "b"])

    def test_file_hash_changes_when_content_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.bin"
            path.write_bytes(b"first")
            first = sha256_file(path)
            path.write_bytes(b"second")
            second = sha256_file(path)
        self.assertNotEqual(first, second)
        self.assertEqual(len(first), 64)
        self.assertEqual(len(second), 64)


if __name__ == "__main__":
    unittest.main()
