import unittest

from src.common.environment import assess_storage, compare_shared_packages, validate_smoke


class EnvironmentContractTests(unittest.TestCase):
    def good_report(self):
        return {
            "status": "PASS",
            "device": "gpu",
            "python_minor": "3.11",
            "checks": [
                {"name": name, "passed": True, "actual_device": "cuda:0", "gradients_finite": True}
                for name in ("matmul", "cnn", "rnn", "lstm")
            ],
            "peak_vram_bytes": 1024,
        }

    def test_storage_boundary(self):
        self.assertTrue(assess_storage(20 * 1024**3)["ready"])
        self.assertFalse(assess_storage(20 * 1024**3 - 1)["ready"])

    def test_negative_storage_is_rejected(self):
        with self.assertRaises(ValueError):
            assess_storage(-1)

    def test_valid_gpu_report(self):
        self.assertEqual(validate_smoke(self.good_report()), [])

    def test_available_gpu_without_real_work_is_not_enough(self):
        report = self.good_report()
        report["checks"] = []
        self.assertTrue(validate_smoke(report))

    def test_hidden_cpu_execution_is_rejected(self):
        report = self.good_report()
        report["checks"][1]["actual_device"] = "cpu"
        self.assertTrue(validate_smoke(report))

    def test_bad_gradient_is_rejected(self):
        report = self.good_report()
        report["checks"][2]["gradients_finite"] = False
        self.assertTrue(validate_smoke(report))

    def test_vram_over_budget_is_rejected(self):
        report = self.good_report()
        report["peak_vram_bytes"] = 9 * 1024**3
        self.assertTrue(validate_smoke(report))

    def test_zero_gpu_memory_is_rejected(self):
        report = self.good_report()
        report["peak_vram_bytes"] = 0
        self.assertTrue(validate_smoke(report))

    def test_invalid_metadata_is_rejected(self):
        for key, value in [
            ("status", "FAIL"),
            ("python_minor", "3.14"),
            ("device", "tpu"),
            ("peak_vram_bytes", None),
        ]:
            report = self.good_report()
            report[key] = value
            self.assertTrue(validate_smoke(report))

    def test_cpu_request_must_not_run_on_gpu(self):
        report = self.good_report()
        report["device"] = "cpu"
        self.assertTrue(validate_smoke(report))

    def test_cpu_fallback_is_accepted_only_as_cpu(self):
        report = self.good_report()
        report["device"] = "cpu"
        for check in report["checks"]:
            check["actual_device"] = "cpu"
        self.assertEqual(validate_smoke(report), [])

    def test_shared_versions_must_match(self):
        self.assertEqual(compare_shared_packages({"numpy": "2.4"}, {"numpy": "2.4"}), [])
        self.assertTrue(compare_shared_packages({"numpy": "2.4"}, {"numpy": "2.3"}))
        self.assertTrue(compare_shared_packages({"numpy": "2.4"}, {}))


if __name__ == "__main__":
    unittest.main()
