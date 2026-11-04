"""Export three TRAIN-only CPU comparison notebooks and request/job examples."""

import json
import sys

import nbformat

from scripts.demo_phase28 import decode_request, infer, sample_request
from src.ch04_rnn_lstm.protocol import BASE, DATASETS, ROOT, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import read_json
from src.common.training_core import inference_timing


def main():
    output = BASE / "demo/export.json"
    if output.exists():
        existing = read_json(output)
        for row in existing["datasets"]:
            for key in ("notebook", "request", "job"):
                checked(row[key])
        print(json.dumps({"status": "PASS", "mode": "reused_verified", "test_executed": False}))
        return
    rows, smoke = [], []
    for dataset in DATASETS:
        request, sample_id = sample_request(dataset)
        job = infer(request)
        request_path = BASE / "demo" / f"{dataset}_request.json"
        job_path = BASE / "demo" / f"{dataset}_job.json"
        write_once(request_path, request)
        write_once(job_path, job)
        timing = inference_timing(lambda request=request: decode_request(request))
        smoke.append(
            {
                "dataset_id": dataset,
                "input_split": "train",
                "id": sample_id,
                "models_loaded": 3,
                "actual_backend": "numpy",
                "actual_device": "cpu",
                "preprocessing_timing": timing,
                "preprocessing_scope": "Preloaded engineered raw feature matrix to schema checks, frozen metadata lookup and scaling; includes metadata I/O, excludes source-file/network/feature-engineering and model loading",
            }
        )
        path = ROOT / "experiments/notebooks/v3/ch04_rnn" / f"{dataset}.ipynb"
        notebook = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(
                    f"# RNN — {dataset}\n\nPhase28: VALIDATION ONLY. Ba checkpoint train độc lập, serving NumPy CPU; không phải ba native GPU runtime. Notebook không train hoặc mở TEST. Thứ tự feature/lookback/horizons theo contracts Phase24–28; không dùng để khuyến nghị đầu tư."
                ),
                nbformat.v4.new_code_cell(
                    "from pathlib import Path\nimport sys\nroot = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())\nif str(root) not in sys.path: sys.path.insert(0, str(root))\nfrom scripts.demo_phase28 import sample_request, infer\nfrom src.common.contracts import read_json\nfrom src.ch04_rnn_lstm.protocol import BASE\n"
                ),
                nbformat.v4.new_code_cell(
                    f"dataset = {dataset!r}\nrequest, sample_id = sample_request(dataset)\nprint('TRAIN sample:', sample_id)\nprint('Sequence shape:', len(request['input']['values']), len(request['input']['values'][0]))"
                ),
                nbformat.v4.new_code_cell(
                    "job = infer(request)\nfor result in job['results']:\n    print(result['implementation'], result['actual_backend'], result['actual_device'], result['prediction'])\nassert job['comparison_valid']"
                ),
                nbformat.v4.new_code_cell(
                    "model_id = job['results'][0]['model_id']\ncontract = read_json(BASE / 'runs' / model_id / 'model_contract.json')\nprint('Learnable layers:', sum(layer['kind'] in {'rnn','dense'} for layer in contract['layers']))\nprint(contract['composition_plain'])\nprint('Parameters:', contract['parameter_count'])"
                ),
                nbformat.v4.new_code_cell(
                    "release = read_json(BASE / 'release.json')\nrows = [read_json(root / 'artifacts/metrics/phase28/validation' / (e['run_id'] + '.json')) for e in release['runs'] if e['dataset_id'] == dataset and e['fold'] is None]\nprint('Saved main VALIDATION records:', len(rows))\nprint('TEST was not executed. RNN/LSTM TEST belongs to Phase29.')\nassert len(rows) == 11\nassert not any(name in sys.modules for name in ('torch','tensorflow','keras'))"
                ),
            ]
        )
        notebook.metadata.kernelspec = {
            "display_name": "AI V3 (torch, WSL GPU)",
            "language": "python",
            "name": "ai-v3-torch",
        }
        for index, cell in enumerate(notebook.cells):
            cell.id = f"rnn-{dataset}-{index}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise ValueError(
                "Notebook exists without export manifest; inspect partial output instead of overwriting"
            )
        nbformat.write(notebook, path)
        rows.append(
            {
                "dataset_id": dataset,
                "input_split": "train",
                "sample_id": sample_id,
                "request": ref(request_path),
                "job": ref(job_path),
                "notebook": ref(path),
            }
        )
    if any(name in sys.modules for name in ("torch", "keras", "tensorflow")):
        raise ValueError("CPU export imported a native framework")
    write_once(
        BASE / "cpu_smoke.json",
        {"status": "PASS", "cases": smoke, "models_loaded": 9, "test_evaluation_executed": False},
    )
    write_once(output, {"status": "PASS", "datasets": rows, "test_evaluation_executed": False})
    print(json.dumps({"status": "PASS", "notebooks": 3, "cpu_model_slots": 9, "test_executed": False}))


if __name__ == "__main__":
    main()
