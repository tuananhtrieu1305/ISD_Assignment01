"""Allowlisted frozen NumPy predictors and exact evidence/series lookup tools."""

import copy

import numpy as np

from src.ch05_knowledge_rag.preservation import checked, ref
from src.common.artifact_core import ArtifactStore
from src.common.contracts import ROOT, read_json
from src.common.numpy_engine import NumpyNetwork
from src.common.tensor_adapters import TensorAdapter


class ToolCatalog:
    def __init__(self, document):
        self.records = document["records"]
        self.models = {}
        if len(self.records) > 200 or len(document["models"]) != 3:
            raise ValueError("Catalog exceeds fixed local budget")
        for domain, spec in document["models"].items():
            config = read_json(checked(spec["config"]))
            metadata_path = checked(spec["checkpoint_metadata"])
            checkpoint_path = checked(spec["checkpoint"])
            metadata = read_json(metadata_path)
            adapter_contract = read_json(checked(config["adapter"]))
            adapter = TensorAdapter(read_json(checked(adapter_contract["preprocessing"])))
            if adapter.output_feature_names != adapter_contract["output_feature_names"]:
                raise ValueError("Canonical feature order changed")
            weights = ArtifactStore(checkpoint_path.parent).load_checkpoint(
                "best", metadata["provenance"], expected_manifest_sha256=spec["checkpoint_metadata"]["sha256"]
            )
            self.models[domain] = (NumpyNetwork(config["plan"], weights), adapter)
        references = {
            item["path"]: item for record in self.records.values() for item in record["artifact_refs"]
        }
        for item in references.values():
            checked(item)

    def call(self, tool, record_id, attempt=0, fault=None):
        if fault == "transient" and attempt == 0:
            return {"status": "error", "code": "transient"}
        if fault == "permanent":
            return {"status": "error", "code": "unavailable"}
        record = self.records.get(record_id)
        if record is None or record["tool"] != tool:
            raise ValueError("Record/tool not authorized")
        result = {
            k: copy.deepcopy(record[k]) for k in ("values", "unit", "text", "citations", "artifact_refs")
        }
        # Common V3 trace paths intentionally exclude apps/. Keep the original citation
        # container hash and point trace refs through its already locked preservation index.
        result["artifact_refs"] = [
            ref(ROOT / "artifacts/manifests/phase30/preserved_snapshot.json")
            if item["path"].startswith("apps/")
            else item
            for item in result["artifact_refs"]
        ]
        if record["operation"] == "numeric":
            model, adapter = self.models[record["domain"]]
            x = np.asarray(record["input"], dtype="float32")[None]
            if not np.isfinite(x).all() or list(x.shape[1:]) != list(model.plan["input_shape"]):
                raise ValueError("Invalid canonical model input")
            raw = model.forward(x).astype("float64")
            if record["domain"] == "diabetes":
                result["values"] = [float(1 / (1 + np.exp(-np.clip(raw[0, 0], -60, 60))))]
            else:
                result["values"] = adapter.inverse_target(raw)[0].reshape(-1).tolist()
            result["text"] = "Frozen NumPy CPU tool output: " + ", ".join(
                format(v, ".8g") for v in result["values"]
            )
        return result
