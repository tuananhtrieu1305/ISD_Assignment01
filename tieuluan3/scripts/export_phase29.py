"""Generate/execute three six-checkpoint CPU notebooks on fixed TRAIN windows."""

import contextlib
import io
import runpy
import sys

import nbformat

from scripts.demo_phase29 import sample_request
from scripts.summarize_phase29 import test_result
from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json


def registry():
    models = []
    for dataset in DATASETS:
        manifest = read_json(BASE / "test_seals" / dataset / "manifest.json")
        for member in manifest["members"]:
            selected = read_json(checked(member["selection"]))
            contract = read_json(checked(member["model_contract"]))
            result = test_result(dataset, member["run_id"])
            audit = read_json(BASE / "test_verification.json")
            models.append(
                {
                    **member,
                    "lifecycle": "trained_evaluated"
                    if member["family"] != "classical"
                    else "fixed_causal_baseline_evaluated",
                    "inference_ready": True,
                    "checkpoint": selected["checkpoint"],
                    "checkpoint_metadata": selected["checkpoint_metadata"],
                    "test_result": audit["result_refs"][member["run_id"]],
                    "test_metrics": result["metrics"],
                    "serving_backend": "numpy_cpu_portable"
                    if member["family"] != "classical"
                    else "causal_history_baseline",
                    "parameter_count": contract.get("parameter_count"),
                    "learnable_layers": sum(
                        layer["kind"] in {"rnn", "lstm", "dense"} for layer in contract.get("layers", [])
                    ),
                }
            )
    write_once(
        BASE / "trained_registry.json",
        {
            "phase": 29,
            "default_seed": 42,
            "models": models,
            "initialized_registry_replaced": False,
            "test_audit": ref(BASE / "test_verification.json"),
        },
    )


def main():
    output = BASE / "demo/export.json"
    if output.exists():
        result = read_json(output)
        for row in result["artifacts"]:
            checked(row)
        print({"status": "PASS", "mode": "reused_verified"})
        return
    registry()
    rows, evidence, slots = [], [ref(BASE / "trained_registry.json")], 0
    for dataset in DATASETS:
        path = ROOT / "experiments/notebooks/v3/ch04_rnn_lstm" / (dataset + ".ipynb")
        if path.exists():
            raise ValueError("Existing partial notebook requires inspection, not overwrite")
        notebook = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(
                    f"# RNN–LSTM / {dataset}\n\nHai họ ×ba checkpoint train độc lập. Serving thực tế NumPy CPU; "
                    "không train hoặc mở TEST. Mẫu TRAIN, seed42 cố định; không chọn model bằng TEST. "
                    "CLI/notebook chưa phải HTTP/React/Render live, không khuyến nghị đầu tư."
                ),
                nbformat.v4.new_code_cell(
                    "from pathlib import Path\nimport sys\n"
                    "root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())\n"
                    "if str(root) not in sys.path: sys.path.insert(0, str(root))\n"
                    "from scripts.demo_phase29 import sample_request, infer\n"
                    "from src.common.contracts import read_json\n"
                ),
                nbformat.v4.new_code_cell(
                    f"dataset = {dataset!r}\njobs = {{}}\n"
                    "for family in ('rnn', 'lstm'):\n"
                    "    request, sample_id = sample_request(dataset, family)\n"
                    "    jobs[family] = infer(request)\n"
                    "    print('TRAIN sample:', sample_id, family)\n"
                    "    for row in jobs[family]['results']:\n"
                    "        print(row['implementation'], row['actual_backend'], row['actual_device'], row['prediction'])\n"
                    "    assert jobs[family]['comparison_valid']\n"
                    "assert jobs['rnn']['input_sha256'] == jobs['lstm']['input_sha256']"
                ),
                nbformat.v4.new_code_cell(
                    "for family, phase in (('rnn',28), ('lstm',29)):\n"
                    "    model_id = jobs[family]['results'][0]['model_id']\n"
                    "    contract = read_json(root / f'artifacts/manifests/phase{phase}/runs' / model_id / 'model_contract.json')\n"
                    "    print(family, contract['composition_plain'], 'parameters=',contract['parameter_count'])\n"
                    "    assert sum(layer['kind'] in {'rnn','lstm','dense'} for layer in contract['layers']) == 6"
                ),
                nbformat.v4.new_code_cell(
                    "audit = read_json(root / 'artifacts/manifests/phase29/test_verification.json')\n"
                    "print('Saved TEST audit:', audit['status'], audit['test_prediction_rows'])\n"
                    "assert audit['status'] == 'PASS'\n"
                    "assert not any(name in sys.modules for name in ('torch','tensorflow','keras'))\n"
                    "print('No TEST forward or training was executed by this notebook.')"
                ),
            ]
        )
        notebook.metadata.kernelspec = {
            "display_name": "AI V3 (torch, WSL GPU)",
            "language": "python",
            "name": "ai-v3-torch",
        }
        for i, cell in enumerate(notebook.cells):
            cell.id = f"rnn-lstm-{dataset}-{i}"
        path.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(notebook, path)
        # Execute only our own generated literal cells, never an uploaded/external notebook.
        script_path = BASE / "demo" / (dataset + "_notebook_cells.py")
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with script_path.open("x", encoding="utf-8") as stream:
            stream.write("\n\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code"))
        script_ref = ref(script_path)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            scope = runpy.run_path(str(checked(script_ref)))
        for family in ("rnn", "lstm"):
            request, sample_id = sample_request(dataset, family)
            job = scope["jobs"][family]
            prefix = BASE / "demo" / f"{dataset}_{family}"
            request_path, job_path = (
                prefix.with_name(prefix.name + "_request.json"),
                prefix.with_name(prefix.name + "_job.json"),
            )
            write_once(request_path, request)
            write_once(job_path, job)
            if len(job["results"]) != 3 or any(
                r["actual_device"] != "cpu" or r["actual_backend"] != "numpy" for r in job["results"]
            ):
                raise ValueError("Expected three independently-trained portable CPU checkpoints per family")
            evidence += [ref(request_path), ref(job_path)]
            slots += 3
        log_path = BASE / "demo" / (dataset + "_notebook_execution.json")
        write_once(
            log_path,
            {
                "status": "PASS",
                "execution": "all generated code cells compiled/executed sequentially in Python namespace; not a Jupyter UI test",
                "stdout": captured.getvalue(),
                "input_split": "train",
                "model_slots": 6,
                "new_test_forward_executed": False,
            },
        )
        evidence += [ref(path), ref(log_path), script_ref]
        rows.append({"dataset_id": dataset, "notebook": ref(path), "sample_id": sample_id, "model_slots": 6})
    if any(name in sys.modules for name in ("torch", "tensorflow", "keras")):
        raise ValueError("Unexpected native framework import in CPU notebook export")
    result = {
        "phase": 29,
        "status": "PASS",
        "notebooks": rows,
        "models_loaded": slots,
        "actual_backend": "numpy",
        "actual_device": "cpu",
        "artifacts": evidence,
        "new_test_forward_executed": False,
        "training_executed": False,
    }
    write_once(output, result)
    print({"status": "PASS", "notebooks": 3, "model_slots": slots, "new_test_forward_executed": False})


if __name__ == "__main__":
    main()
