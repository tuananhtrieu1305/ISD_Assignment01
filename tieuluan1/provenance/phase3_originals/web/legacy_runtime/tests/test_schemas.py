import base64
import io
import unittest

from PIL import Image

from term_paper.deployment.app.schemas import (
    ValidationError,
    validate_diabetes,
    validate_image_base64,
    validate_sequence,
)


class DeploymentSchemaTests(unittest.TestCase):
    def setUp(self):
        self.diabetes = {
            "HighBP": 1, "HighChol": 0, "CholCheck": 1, "BMI": 26,
            "Smoker": 0, "Stroke": 0, "HeartDiseaseorAttack": 0,
            "PhysActivity": 1, "Fruits": 0, "Veggies": 1,
            "HvyAlcoholConsump": 0, "AnyHealthcare": 1, "NoDocbcCost": 0,
            "GenHlth": 3, "MentHlth": 5, "PhysHlth": 10, "DiffWalk": 0,
            "Sex": 1, "Age": 4, "Education": 6, "Income": 8,
        }

    def test_diabetes_accepts_exact_finite_schema(self):
        result = validate_diabetes(self.diabetes)
        self.assertEqual(list(result), list(self.diabetes))
        self.assertEqual(result["BMI"], 26.0)

    def test_diabetes_rejects_missing_extra_and_out_of_range(self):
        for invalid in (
            {key: value for key, value in self.diabetes.items() if key != "BMI"},
            {**self.diabetes, "patient_name": "private"},
            {**self.diabetes, "Age": 14},
            {**self.diabetes, "BMI": float("nan")},
        ):
            with self.assertRaises(ValidationError):
                validate_diabetes(invalid)

    def test_customer_and_stock_sequence_shape_and_domain(self):
        customer = [[0, 0, 0, 0, 0] for _ in range(8)]
        stock = [[100, 102, 99, 101, 1_000_000] for _ in range(30)]
        self.assertEqual(validate_sequence(customer, "customer").shape, (8, 5))
        self.assertEqual(validate_sequence(stock, "aapl").shape, (30, 5))
        for invalid, kind in ((customer[:-1], "customer"), (stock + [[1] * 5], "aapl"),
                              ([[0, 0, 0, 0, 2]] * 8, "customer"),
                              ([[100, 99, 102, 101, 10]] * 30, "aapl")):
            with self.assertRaises(ValidationError):
                validate_sequence(invalid, kind)

    def test_image_validation_accepts_png_and_rejects_non_image(self):
        image = Image.new("RGB", (32, 24), (30, 90, 140))
        buffer = io.BytesIO(); image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        loaded = validate_image_base64(encoded)
        self.assertEqual(loaded.mode, "RGB")
        with self.assertRaises(ValidationError):
            validate_image_base64(base64.b64encode(b"not-an-image").decode("ascii"))
        oversized = Image.new("1", (4_473, 4_473), 0)
        buffer = io.BytesIO(); oversized.save(buffer, format="PNG")
        with self.assertRaisesRegex(ValidationError, "20 triệu pixel"):
            validate_image_base64(base64.b64encode(buffer.getvalue()).decode("ascii"))


if __name__ == "__main__":
    unittest.main()
