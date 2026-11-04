import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from term_paper.deployment.app.model_service import ModelService
from term_paper.deployment.app.server import create_server


ROOT = Path(__file__).resolve().parents[3]


class DeploymentServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0, ModelService(ROOT))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=3)

    def request(self, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.base + path, data=data,
                                         headers={"Content-Type": "application/json"} if data else {},
                                         method="POST" if data else "GET")
        return urllib.request.urlopen(request, timeout=10)

    def test_health_static_ui_and_security_headers(self):
        with self.request("/health") as response:
            payload = json.load(response)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        with self.request("/") as response:
            html = response.read().decode("utf-8")
            self.assertIn("Phòng thí nghiệm mô hình", html)
            self.assertIn("data-tab=\"cnn\"", html)
            self.assertIn("không phải chẩn đoán y khoa", html.lower())

    def test_demo_to_prediction_flow_for_every_use_case(self):
        expected_fields = {
            "diabetes": "probability", "eurosat": "top_classes",
            "customer": "probability", "aapl": "naive_last_close_usd",
        }
        for use_case, expected_field in expected_fields.items():
            with self.subTest(use_case=use_case):
                with self.request(f"/api/demo/{use_case}") as response:
                    demo = json.load(response)
                with self.request(f"/api/predict/{use_case}", demo["input"]) as response:
                    result = json.load(response)
                    self.assertIn(expected_field, result)
                    self.assertTrue(result["request_id"].startswith("req_"))

    def test_invalid_input_and_routes_return_friendly_errors(self):
        with self.assertRaises(urllib.error.HTTPError) as captured:
            self.request("/api/predict/customer", {"sequence": [[0] * 5]})
        self.assertEqual(captured.exception.code, 400)
        error = json.loads(captured.exception.read())
        self.assertEqual(error["error"]["code"], "invalid_input")
        self.assertNotIn("Traceback", json.dumps(error))
        with self.assertRaises(urllib.error.HTTPError) as missing:
            self.request("/not-found")
        self.assertEqual(missing.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
