"""Smoke tests for Assignment 05 CNN architecture builders."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np
import tensorflow as tf


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import architectures


EXPECTED_PYTHON = "C:/Users/anhca/anaconda3/envs/tf312/python.exe"


class ArchitectureSmokeTests(unittest.TestCase):
    def test_uses_permanent_tensorflow_environment(self):
        actual = sys.executable.replace("\\", "/")
        self.assertEqual(actual.lower(), EXPECTED_PYTHON.lower())
        self.assertEqual(tf.__version__, "2.21.0")

    def test_2d_models_build_and_run_for_eurosat_and_oxford_like_inputs(self):
        builders = [
            architectures.build_basic_cnn_2d,
            architectures.build_alexnet_inspired_2d,
            architectures.build_vgg_inspired_2d,
            architectures.build_resnet_inspired_2d,
        ]
        checks = [((64, 64, 3), 10), ((128, 128, 3), 37)]
        summary = {}

        for builder in builders:
            builder_summary = {}
            for input_shape, num_classes in checks:
                with self.subTest(builder=builder.__name__, input_shape=input_shape):
                    model = builder(input_shape=input_shape, num_classes=num_classes)
                    dummy = np.zeros((1, *input_shape), dtype=np.float32)
                    output = model(dummy, training=False)
                    self.assertEqual(tuple(output.shape), (1, num_classes))
                    self.assertGreater(model.count_params(), 0)
                    builder_summary[str(input_shape)] = {
                        "output_shape": tuple(output.shape),
                        "parameters": int(model.count_params()),
                    }
            summary[builder.__name__] = builder_summary

        print("2D_SHAPE_CHECKS=" + json.dumps(summary, sort_keys=True))

    def test_1d_models_build_run_and_record_valid_sequence_lengths(self):
        builders = [
            architectures.build_basic_cnn_1d,
            architectures.build_alexnet_inspired_1d,
            architectures.build_vgg_inspired_1d,
            architectures.build_resnet_inspired_1d,
        ]
        summary = {}

        for builder in builders:
            with self.subTest(builder=builder.__name__):
                model = builder(input_shape=(21, 1), num_classes=3)
                dummy = np.zeros((1, 21, 1), dtype=np.float32)
                output = model(dummy, training=False)
                self.assertEqual(tuple(output.shape), (1, 3))
                self.assertGreater(model.count_params(), 0)

                progression = getattr(model, "shape_progression", None)
                self.assertIsInstance(progression, list)
                self.assertGreater(len(progression), 0)
                lengths = [step["length"] for step in progression if step["length"] is not None]
                self.assertEqual(lengths[0], 21)
                self.assertTrue(all(length > 0 for length in lengths))

                summary[builder.__name__] = {
                    "parameters": int(model.count_params()),
                    "shape_progression": progression,
                }

        print("1D_SHAPE_PROGRESSIONS=" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
