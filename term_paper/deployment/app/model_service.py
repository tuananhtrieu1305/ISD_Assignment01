"""Load verified artifacts and provide deterministic inference services."""

import base64
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from PIL import Image

from term_paper.deployment.app.schemas import (
    DIABETES_FEATURES, validate_diabetes, validate_image_base64, validate_sequence,
)
from term_paper.src.scratch.cnn import NumpyCNN
from term_paper.src.scratch.mlp import NumpyMLP
from term_paper.src.scratch.rnn import NumpyRNN


MODEL_REGISTRY = {
    "diabetes": {
        "version": "ch2-numpy-seed42", "chapter": 2,
        "model": "term_paper/artifacts/models/ch2/ch2_diabetes_binary_numpy_seed42.npz",
        "model_sha256": "3dfc9d072f0c7f57a17f67ae756eb9e24553ceaf98fe64fde58f86294490766d",
        "preprocessors": [{"path": "term_paper/artifacts/models/ch2/ch2_diabetes_binary_preprocessor.joblib",
                           "sha256": "f7d520543655ea27d45d88d939c1458e2afc471a98c6038b67fe1bdc22b117f0"}],
        "threshold": 0.37,
    },
    "eurosat": {
        "version": "ch3-numpy-seed42", "chapter": 3,
        "model": "term_paper/artifacts/models/ch3/ch3_eurosat_numpy_seed42.npz",
        "model_sha256": "1a9ecd7dc6cfce75655e9a4646c0355449989d506d733d8a4b28d96df92bcc9b",
        "preprocessors": [{"path": "term_paper/artifacts/models/ch3/ch3_eurosat_preprocessor.json",
                           "sha256": "e7ebf26ecc7cdc788f150e15b160c2a09c7071a083868fa4172ed6731c334063"}],
    },
    "customer_rnn": {
        "version": "ch4-customer-numpy-seed42", "chapter": 4,
        "model": "term_paper/artifacts/models/ch4/ch4_online_retail_customer_week_numpy_seed42.npz",
        "model_sha256": "8f2516cea7fcaa68d1125fc0a41c885984af749e1a0f42df668a966f5ad43299",
        "preprocessors": [{"path": "A06/models/preprocessing/customer_feature_scaler.joblib",
                           "sha256": "4da83eacfcca7758d9d4289d9e0671b2e560d70b38a701cd42fd5fd86dddb7ee"}],
        "threshold": 0.655,
    },
    "aapl_rnn": {
        "version": "ch4-aapl-numpy-seed42", "chapter": 4,
        "model": "term_paper/artifacts/models/ch4/ch4_aapl_next_close_numpy_seed42.npz",
        "model_sha256": "23d385a66a9a5b0171f2d9930afa024838d09aa25b0773ca883ffc4c65dbd086",
        "preprocessors": [
            {"path": "A06/models/preprocessing/stock_feature_scaler.joblib",
             "sha256": "150970d87ebd1b04fa55b56e89002cc9462fb7b6e29255fd6ab54778e3567f80"},
            {"path": "A06/models/preprocessing/stock_target_scaler.joblib",
             "sha256": "153a0aa8ac97885b07d5fb0eacf461e5882ab1bb7fb6da9df53486116ff937cb"},
        ],
    },
}

EUROSAT_CLASSES = [
    "AnnualCrop", "Forest", "HerbaceousVegetation", "Highway", "Industrial",
    "Pasture", "PermanentCrop", "Residential", "River", "SeaLake",
]


def sha256_file(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        # Git stores text with LF on Render/Linux while the original locked
        # artifact was produced with CRLF on Windows. Hash JSON using the
        # original CRLF representation so integrity checks are OS-stable.
        data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return hashlib.sha256(data.replace(b"\n", b"\r\n")).hexdigest()

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ModelService:
    def __init__(self, workspace_root):
        self.root = Path(workspace_root).resolve()
        self.registry = json.loads(json.dumps(MODEL_REGISTRY))
        self._verify_registry()
        self.diabetes_model = NumpyMLP.load(self.root / self.registry["diabetes"]["model"])
        self.diabetes_preprocessor = joblib.load(self.root / self.registry["diabetes"]["preprocessors"][0]["path"])
        self.eurosat_model = NumpyCNN.load(self.root / self.registry["eurosat"]["model"])
        self.customer_model = NumpyRNN.load(self.root / self.registry["customer_rnn"]["model"])
        self.customer_scaler = joblib.load(self.root / self.registry["customer_rnn"]["preprocessors"][0]["path"])
        self.aapl_model = NumpyRNN.load(self.root / self.registry["aapl_rnn"]["model"])
        self.stock_feature_scaler = joblib.load(self.root / self.registry["aapl_rnn"]["preprocessors"][0]["path"])
        self.stock_target_scaler = joblib.load(self.root / self.registry["aapl_rnn"]["preprocessors"][1]["path"])

    def _verify_registry(self):
        for model_id, entry in self.registry.items():
            model_path = self.root / entry["model"]
            if not model_path.is_file() or sha256_file(model_path) != entry["model_sha256"]:
                raise RuntimeError(f"Artifact hash mismatch: {model_id}/model")
            entry["model_bytes"] = model_path.stat().st_size
            for preprocessor in entry["preprocessors"]:
                path = self.root / preprocessor["path"]
                if not path.is_file() or sha256_file(path) != preprocessor["sha256"]:
                    raise RuntimeError(f"Artifact hash mismatch: {model_id}/preprocessor")
                preprocessor["bytes"] = path.stat().st_size
            entry["hash_verified"] = True

    def health(self):
        models = {
            model_id: {
                "version": entry["version"], "chapter": entry["chapter"],
                "hash_verified": entry["hash_verified"], "model_sha256": entry["model_sha256"],
            }
            for model_id, entry in self.registry.items()
        }
        return {"status": "ok", "service_version": "phase6-1.0.0", "models": models}

    def public_registry(self):
        return self.registry

    @staticmethod
    def _provenance(entry):
        return {"version": entry["version"], "model_sha256": entry["model_sha256"],
                "preprocessor_sha256": [item["sha256"] for item in entry["preprocessors"]]}

    def predict_diabetes(self, payload):
        values = validate_diabetes(payload)
        frame = pd.DataFrame([[values[name] for name in DIABETES_FEATURES]], columns=DIABETES_FEATURES)
        transformed = self.diabetes_preprocessor.transform(frame)
        if hasattr(transformed, "toarray"):
            transformed = transformed.toarray()
        probability = float(self.diabetes_model.predict_score(np.asarray(transformed, dtype=np.float32))[0])
        threshold = float(self.registry["diabetes"]["threshold"])
        predicted = int(probability >= threshold)
        return {
            "probability": probability, "threshold": threshold, "predicted_class": predicted,
            "label": "Nguy cơ theo mô hình: cao" if predicted else "Nguy cơ theo mô hình: thấp",
            "warning": "Kết quả học thuật, không phải chẩn đoán y khoa. Hãy tham khảo chuyên gia y tế.",
            "provenance": self._provenance(self.registry["diabetes"]),
        }

    def predict_eurosat(self, encoded):
        image = validate_image_base64(encoded)
        if image.size != (64, 64):
            image = image.resize((64, 64), resample=Image.Resampling.BILINEAR)
        array = np.asarray(image, dtype=np.float32)[None, ...] / 255.0
        probabilities = self.eurosat_model.predict_proba(array)[0]
        order = np.argsort(probabilities)[::-1][:3]
        top = [{"class_index": int(index), "class_name": EUROSAT_CLASSES[index],
                "confidence": float(probabilities[index])} for index in order]
        return {"predicted_class_index": top[0]["class_index"], "predicted_class": top[0]["class_name"],
                "top_classes": top, "input_shape": [64, 64, 3],
                "warning": "Phân loại minh họa trên EuroSAT; không thay thế phân tích viễn thám chuyên nghiệp.",
                "provenance": self._provenance(self.registry["eurosat"])}

    def predict_customer(self, sequence):
        raw = validate_sequence(sequence, "customer")
        scaled = self.customer_scaler.transform(raw).astype(np.float32)[None, ...]
        probability = float(self.customer_model.predict_score(scaled)[0])
        threshold = float(self.registry["customer_rnn"]["threshold"])
        predicted = int(probability >= threshold)
        return {"probability": probability, "threshold": threshold, "predicted_class": predicted,
                "label": "Có khả năng mua tuần kế tiếp" if predicted else "Chưa ghi nhận tín hiệu mua tuần kế tiếp",
                "sequence_shape": [8, 5],
                "warning": "Kết quả chỉ mô tả pattern trong dữ liệu lịch sử và không bảo đảm hành vi tương lai.",
                "provenance": self._provenance(self.registry["customer_rnn"])}

    def predict_aapl(self, sequence):
        raw = validate_sequence(sequence, "aapl")
        scaled = self.stock_feature_scaler.transform(raw).astype(np.float32)[None, ...]
        model_scale = self.aapl_model.predict_score(scaled).reshape(-1, 1)
        prediction = float(self.stock_target_scaler.inverse_transform(model_scale)[0, 0])
        naive = float(raw[-1, 3])
        return {"rnn_prediction_usd": prediction, "naive_last_close_usd": naive,
                "delta_rnn_vs_naive_usd": prediction - naive, "sequence_shape": [30, 5],
                "warning": "Kết quả học thuật, không phải khuyến nghị đầu tư. Naive last-Close là baseline bắt buộc và đã vượt RNN trên TEST.",
                "provenance": self._provenance(self.registry["aapl_rnn"])}

    def demo(self, use_case):
        if use_case == "diabetes":
            return {"use_case": use_case, "input": {
                "HighBP": 1.0, "HighChol": 0.0, "CholCheck": 1.0, "BMI": 26.0,
                "Smoker": 0.0, "Stroke": 0.0, "HeartDiseaseorAttack": 0.0,
                "PhysActivity": 1.0, "Fruits": 0.0, "Veggies": 1.0,
                "HvyAlcoholConsump": 0.0, "AnyHealthcare": 1.0, "NoDocbcCost": 0.0,
                "GenHlth": 3.0, "MentHlth": 5.0, "PhysHlth": 30.0, "DiffWalk": 0.0,
                "Sex": 1.0, "Age": 4.0, "Education": 6.0, "Income": 8.0,
            }}
        if use_case == "eurosat":
            keys = pd.read_csv(self.root / "term_paper/artifacts/manifests/ch3/ch3_eurosat_subset_keys.csv")
            relative = keys[keys["split"] == "test"].iloc[0]["sample_key"]
            encoded = base64.b64encode((self.root / "A05" / Path(relative)).read_bytes()).decode("ascii")
            return {"use_case": use_case, "input": {"image_base64": encoded}, "sample_key": relative}
        if use_case == "customer":
            data = np.load(self.root / "term_paper/artifacts/manifests/ch4/ch4_online_retail_customer_week_processed.npz")
            raw = self.customer_scaler.inverse_transform(data["x_test"][0]).tolist()
            return {"use_case": use_case, "input": {"sequence": raw}, "sample_key": str(data["keys_test"][0])}
        if use_case == "aapl":
            data = np.load(self.root / "term_paper/artifacts/manifests/ch4/ch4_aapl_next_close_processed.npz")
            raw = self.stock_feature_scaler.inverse_transform(data["x_test"][0]).tolist()
            return {"use_case": use_case, "input": {"sequence": raw}, "sample_key": str(data["keys_test"][0])}
        raise KeyError(use_case)
