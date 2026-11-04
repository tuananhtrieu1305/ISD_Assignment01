"""Export CPU/API demos and executable notebooks, not a new evaluation."""

import json
import sys

import nbformat

from scripts.demo_phase27 import infer, saliency, sample_request
from src.ch02_ml.experiment import provenance
from src.ch03_cnn.experiment import checked
from src.ch03_cnn.image_cache import development_cache
from src.ch03_cnn.protocol import BASE, DATASETS, IMPLEMENTATIONS, MODELS, check_sources, ref
from src.common.artifact_core import ArtifactStore, write_once
from src.common.contracts import ROOT, read_json


def main():
    release = check_sources()
    demos = []
    for dataset in DATASETS:
        request, key = sample_request(dataset)
        job = infer(request, 42)
        write_once(BASE / "demo" / f"{dataset}_request.json", request)
        # Timing/timestamps are captured once, not overwritten on rerun.
        path = BASE / "demo" / f"{dataset}_job.json"
        if not path.exists():
            write_once(path, job)
        cache, _view = development_cache(dataset)
        x, _ = cache.batch([key])
        for method in IMPLEMENTATIONS:
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
            config = read_json(checked(entry["config"]))
            weights = ArtifactStore(MODELS / entry["run_id"]).load_checkpoint(
                "best",
                provenance(entry, config),
                expected_manifest_sha256=selected["checkpoint_metadata"]["sha256"],
            )
            result = saliency(config["plan"], weights, x)
            write_once(
                BASE / "saliency" / f"{entry['run_id']}.json",
                {
                    **{k: v for k, v in result.items() if k != "map"},
                    "map": result["map"].tolist(),
                    "input_split": "train",
                    "sample_id": key,
                    "checkpoint": selected["checkpoint"],
                    "input_shape": list(x.shape),
                },
            )
        notebook = nbformat.v4.new_notebook()
        notebook.metadata = {
            "kernelspec": {
                "display_name": "AI V3 (torch, WSL GPU)",
                "language": "python",
                "name": "ai-v3-torch",
            },
            "language_info": {"name": "python"},
        }
        notebook.cells = [
            nbformat.v4.new_markdown_cell(
                f"# CNN — {dataset}\n\nDemo CPU của **3 checkpoint đã train riêng**: scratch/Keras/PyTorch.\nKhông train hoặc gọi TEST. Bộ dự đoán serving thực tế là NumPy portable, không phải ba native GPU runtime.\n\nLý thuyết, mẫu/distribution và metric: `report/sections/v3/ch03_cnn.md`.\nHàm CNN: `src/common/numpy_engine.py`, `src/common/backend_models.py`; trainer: `src/ch03_cnn/training.py`.\nDữ liệu y khoa chỉ dùng học thuật, không chẩn đoán."
            ),
            nbformat.v4.new_code_cell(
                "from pathlib import Path\nimport os, sys\nroot = Path.cwd().resolve()\nwhile not (root / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists():\n    if root.parent == root:\n        raise RuntimeError('Open notebook inside the repository')\n    root = root.parent\nos.chdir(root)\nif str(root) not in sys.path:\n    sys.path.insert(0, str(root))\nfrom scripts.demo_phase27 import infer, sample_request\nfrom src.common.contracts import read_json\nfrom src.ch03_cnn.protocol import BASE\nimport pandas as pd"
            ),
            nbformat.v4.new_code_cell(
                f"request, train_id = sample_request('{dataset}')\njob = infer(request, seed=42)\nprint('Fixed TRAIN sample:', train_id)\npd.DataFrame([{{'training_implementation': r['implementation'], 'serving_backend': r['actual_backend'], 'device': r['actual_device'], 'label': r['prediction']['label'], 'inference_ms_single_call': r['inference_ms']}} for r in job['results']])"
            ),
            nbformat.v4.new_markdown_cell(
                "Một lời gọi demo không thay thế benchmark 5 warmup/30 repeats. Bảng quality/efficiency dưới đây chỉ đọc metric đã lưu; không đánh giá lại TEST."
            ),
            nbformat.v4.new_code_cell(
                f"release = read_json(BASE / 'release.json')\nrows = []\nfor e in release['runs']:\n    if e['dataset_id'] != '{dataset}':\n        continue\n    path = root / 'artifacts/metrics/phase27/test' / (e['run_id'] + '.json')\n    if not path.exists():\n        continue\n    record = read_json(path)\n    values = {{m['name']: m['value'] for m in record['metrics']}}\n    rows.append({{'method': e['method'], 'seed': e['seed'], 'macro_f1': values['macro_f1'], 'accuracy': values['accuracy'], 'train_seconds': record['efficiency']['train_seconds']}})\npd.DataFrame(rows)"
            ),
            nbformat.v4.new_code_cell(
                "assert not any(name in sys.modules for name in ('torch', 'tensorflow', 'keras'))\nassert job['comparison_valid']\nprint('CPU/API-contract PASS. TEST was not executed.')"
            ),
        ]
        for i, cell in enumerate(notebook.cells):
            cell["id"] = f"cnn_{dataset}_{i}"
        path = ROOT / f"experiments/notebooks/v3/ch03_cnn/{dataset}.ipynb"
        payload = nbformat.writes(notebook) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_text(encoding="utf-8") != payload:
                raise ValueError("CNN notebook differs on rerun")
        else:
            path.write_text(payload, encoding="utf-8", newline="\n")
        demos.append(
            {
                "dataset_id": dataset,
                "sample_id": key,
                "api_job": ref(BASE / "demo" / f"{dataset}_job.json"),
                "notebook": ref(path),
                "model_slots": 3,
                "serving_backend": "numpy_cpu_portable",
                "test_executed": False,
            }
        )
    if any(name in sys.modules for name in ("torch", "tensorflow", "keras")):
        raise RuntimeError("CPU export imported GPU framework")
    write_once(
        BASE / "demo" / "export.json",
        {"status": "PASS", "datasets": demos, "test_evaluation_executed": False},
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "datasets": 3,
                "cpu_model_slots": 9,
                "notebooks": 3,
                "saliency_train_examples": 9,
            }
        )
    )


if __name__ == "__main__":
    main()
