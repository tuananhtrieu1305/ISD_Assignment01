"""Lightweight tests for Assignment 05 experiment utilities."""

from __future__ import annotations

import os
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import experiment_utils as utils


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class ExperimentUtilsTests(unittest.TestCase):
    def test_imports_successfully(self):
        self.assertTrue(hasattr(utils, "find_project_root"))
        self.assertTrue(hasattr(utils, "load_image_rgb"))

    def test_project_root_detection_from_expected_locations(self):
        for relative in [".", "notebooks", "models"]:
            with self.subTest(relative=relative):
                with working_directory(ROOT / relative):
                    self.assertEqual(utils.find_project_root(), ROOT)

    def test_image_loader_decodes_jpeg_and_png_content_jpg_names(self):
        cases = [
            ("datasets/eurosat/EuroSAT_RGB/AnnualCrop/AnnualCrop_1.jpg", "JPEG"),
            ("datasets/oxford_pets/images/Abyssinian_1.jpg", "JPEG"),
            ("datasets/oxford_pets/images/Abyssinian_5.jpg", "PNG"),
            ("datasets/oxford_pets/images/Egyptian_Mau_14.jpg", "PNG"),
            ("datasets/oxford_pets/images/Egyptian_Mau_156.jpg", "PNG"),
            ("datasets/oxford_pets/images/Egyptian_Mau_186.jpg", "PNG"),
        ]
        for relative_path, expected_format in cases:
            with self.subTest(relative_path=relative_path):
                image = utils.load_image_rgb(relative_path, image_size=(32, 32), start=ROOT)
                self.assertEqual(image.detected_format, expected_format)
                self.assertEqual(image.mode, "RGB")
                self.assertEqual(image.shape, (32, 32, 3))
                self.assertEqual(image.data.shape[-1], 3)

    def test_oxford_annotation_parser_counts(self):
        splits = utils.load_oxford_official_splits(root=ROOT)
        self.assertEqual(len(splits["trainval"]), 3680)
        self.assertEqual(len(splits["test"]), 3669)
        self.assertEqual(splits["total"], 7349)
        self.assertEqual(splits["unique_total"], 7349)
        self.assertEqual(len(splits["overlap"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

