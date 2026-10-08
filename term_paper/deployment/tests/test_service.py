import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from term_paper.deployment.app.model_service import ModelService, sha256_file


ROOT = Path(__file__).resolve().parents[3]


class DeploymentServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = ModelService(ROOT)

    def test_health_and_registry_expose_verified_hashes(self):
        health = self.service.health()
        self.assertEqual(health["status"], "ok")
        self.assertEqual(set(health["models"]), {"diabetes", "eurosat", "customer_rnn", "aapl_rnn"})
        self.assertTrue(all(item["hash_verified"] for item in health["models"].values()))

    def test_json_artifact_hash_is_stable_across_line_endings(self):
        lf = b'{\n  "scale": "divide_by_255",\n  "fit_scope": "none"\n}'
        crlf = lf.replace(b"\n", b"\r\n")
        expected = hashlib.sha256(crlf).hexdigest()

        with tempfile.TemporaryDirectory() as directory:
            lf_path = Path(directory) / "lf.json"
            crlf_path = Path(directory) / "crlf.json"
            lf_path.write_bytes(lf)
            crlf_path.write_bytes(crlf)

            self.assertEqual(sha256_file(lf_path), expected)
            self.assertEqual(sha256_file(crlf_path), expected)

    def test_diabetes_prediction_matches_saved_test_artifact(self):
        processed = np.load(ROOT / "term_paper/artifacts/manifests/ch2/ch2_diabetes_binary_processed.npz")
        preprocessor = joblib.load(ROOT / "term_paper/artifacts/models/ch2/ch2_diabetes_binary_preprocessor.joblib")
        columns = json.loads((ROOT / "term_paper/artifacts/manifests/ch2/ch2_diabetes_binary_metadata.json").read_text())["raw_feature_names"]
        # The source questionnaire stores all 21 fields as integer-valued answers.
        # Round the tiny float32 inverse-transform noise back to the original domain.
        raw = np.rint(preprocessor.named_transformers_["numeric"].named_steps["scaler"].inverse_transform(processed["x_test"][:1])[0])
        payload = dict(zip(columns, raw.tolist()))
        result = self.service.predict_diabetes(payload)
        expected = pd.read_csv(ROOT / "term_paper/artifacts/predictions/ch2_ch2_diabetes_binary_numpy_test.csv").iloc[0]
        self.assertAlmostEqual(result["probability"], float(expected["y_score"]), places=6)
        self.assertEqual(result["predicted_class"], int(expected["y_pred"]))
        self.assertIn("không phải chẩn đoán", result["warning"].lower())

    def test_eurosat_prediction_matches_saved_test_artifact(self):
        keys = pd.read_csv(ROOT / "term_paper/artifacts/manifests/ch3/ch3_eurosat_subset_keys.csv")
        relative = keys[keys.split == "test"].iloc[0].sample_key
        raw = (ROOT / "A05" / Path(relative)).read_bytes()
        result = self.service.predict_eurosat(base64.b64encode(raw).decode("ascii"))
        expected = pd.read_csv(ROOT / "term_paper/artifacts/predictions/ch3_ch3_eurosat_numpy_test.csv").iloc[0]
        self.assertEqual(result["predicted_class_index"], int(expected["y_pred"]))
        self.assertAlmostEqual(result["top_classes"][0]["confidence"], float(expected[f"prob_{int(expected['y_pred'])}"]), places=6)

    def test_customer_prediction_matches_saved_test_artifact(self):
        processed = np.load(ROOT / "term_paper/artifacts/manifests/ch4/ch4_online_retail_customer_week_processed.npz")
        scaler = joblib.load(ROOT / "A06/models/preprocessing/customer_feature_scaler.joblib")
        raw = scaler.inverse_transform(processed["x_test"][0]).tolist()
        result = self.service.predict_customer(raw)
        expected = pd.read_csv(ROOT / "term_paper/artifacts/predictions/ch4_ch4_online_retail_customer_week_numpy_test.csv").iloc[0]
        self.assertAlmostEqual(result["probability"], float(expected["score_or_prediction"]), places=6)
        self.assertEqual(result["predicted_class"], int(expected["y_pred"]))

    def test_aapl_prediction_and_naive_match_saved_artifact(self):
        processed = np.load(ROOT / "term_paper/artifacts/manifests/ch4/ch4_aapl_next_close_processed.npz")
        scaler = joblib.load(ROOT / "A06/models/preprocessing/stock_feature_scaler.joblib")
        raw = scaler.inverse_transform(processed["x_test"][0]).tolist()
        result = self.service.predict_aapl(raw)
        expected = pd.read_csv(ROOT / "term_paper/artifacts/predictions/ch4_ch4_aapl_next_close_numpy_test.csv").iloc[0]
        self.assertAlmostEqual(result["rnn_prediction_usd"], float(expected["score_or_prediction"]), places=4)
        self.assertAlmostEqual(result["naive_last_close_usd"], float(expected["naive_last_close"]), places=4)
        self.assertIn("không phải khuyến nghị đầu tư", result["warning"].lower())


if __name__ == "__main__":
    unittest.main()
