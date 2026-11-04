"""Run the reproducible matched NumPy/Keras/PyTorch CNN benchmark for Chapter 3."""

import argparse
import gc
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from term_paper.src.common.ch3_data import (
    WORKSPACE_ROOT,
    prepare_diabetes_benchmark,
    prepare_eurosat_benchmark,
)
from term_paper.src.common.ch3_experiment import (
    artifact_suffix,
    build_prediction_frame,
    sha256_file,
)
from term_paper.src.common.ch3_metrics import multiclass_metrics


TERM_ROOT = WORKSPACE_ROOT / "term_paper"
CONFIG_PATH = TERM_ROOT / "config" / "ch3_experiment.json"
MANIFEST_DIR = TERM_ROOT / "artifacts" / "manifests" / "ch3"
MODEL_DIR = TERM_ROOT / "artifacts" / "models" / "ch3"
METRIC_DIR = TERM_ROOT / "artifacts" / "metrics"
PREDICTION_DIR = TERM_ROOT / "artifacts" / "predictions"


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value).__name__)


def validate_matched_prediction_keys(frames):
    required = {"numpy", "keras", "pytorch"}
    if set(frames) != required:
        raise ValueError(f"framework set must be {sorted(required)}")
    reference = frames["numpy"][["sample_key", "y_true"]].reset_index(drop=True)
    for framework in ("keras", "pytorch"):
        candidate = frames[framework][["sample_key", "y_true"]].reset_index(drop=True)
        if not reference.equals(candidate):
            raise ValueError(f"sample keys or targets differ for {framework}")


def _create_model(framework, prepared, config, seed, learning_rate):
    common = {
        "input_shape": prepared["input_shape"],
        "num_classes": prepared["num_classes"],
        "mode": prepared["mode"],
        "filters": tuple(config["topology"]["filters"]),
        "kernel_size": config["topology"]["kernel_size"],
        "seed": int(seed),
        "learning_rate": float(learning_rate),
    }
    if framework == "numpy":
        from term_paper.src.scratch.cnn import NumpyCNN

        return NumpyCNN(**common)
    if framework == "keras":
        from term_paper.src.keras_impl.cnn import KerasCNN

        return KerasCNN(**common)
    if framework == "pytorch":
        from term_paper.src.pytorch_impl.cnn import TorchCNN

        return TorchCNN(**common)
    raise ValueError(framework)


def _load_model(framework, path):
    if framework == "numpy":
        from term_paper.src.scratch.cnn import NumpyCNN

        return NumpyCNN.load(path)
    if framework == "keras":
        from term_paper.src.keras_impl.cnn import KerasCNN

        return KerasCNN.load(path)
    if framework == "pytorch":
        from term_paper.src.pytorch_impl.cnn import TorchCNN

        return TorchCNN.load(path)
    raise ValueError(framework)


def _model_path(dataset_id, framework, seed):
    extensions = {"numpy": ".npz", "keras": ".keras", "pytorch": ".pt"}
    return MODEL_DIR / f"{dataset_id}_{framework}_seed{int(seed)}{extensions[framework]}"


def prepare_datasets(config):
    subset_seed = int(config["subset_seed"])
    datasets = config["datasets"]
    return {
        "ch3_eurosat": prepare_eurosat_benchmark(
            datasets["ch3_eurosat"]["subset_sizes"], seed=subset_seed
        ),
        "ch3_diabetes_012": prepare_diabetes_benchmark(
            datasets["ch3_diabetes_012"]["subset_sizes"], seed=subset_seed
        ),
    }


def save_prepared_dataset(prepared):
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dataset_id = prepared["dataset_id"]
    processed_path = MANIFEST_DIR / f"{dataset_id}_processed.npz"
    np.savez_compressed(
        processed_path,
        x_train=prepared["x_train"],
        y_train=prepared["y_train"],
        x_val=prepared["x_val"],
        y_val=prepared["y_val"],
        x_test=prepared["x_test"],
        y_test=prepared["y_test"],
        keys_train=np.asarray(prepared["keys"]["train"]),
        keys_val=np.asarray(prepared["keys"]["val"]),
        keys_test=np.asarray(prepared["keys"]["test"]),
    )
    split_rows = []
    for split in ("train", "val", "test"):
        for key, label in zip(prepared["keys"][split], prepared[f"y_{split}"]):
            split_rows.append({"split": split, "sample_key": str(key), "label": int(label)})
    split_path = MANIFEST_DIR / f"{dataset_id}_subset_keys.csv"
    pd.DataFrame(split_rows).to_csv(split_path, index=False)
    if prepared["mode"] == "1d":
        preprocessor_path = MODEL_DIR / f"{dataset_id}_preprocessor.joblib"
        joblib.dump(prepared["preprocessor"], preprocessor_path)
    else:
        preprocessor_path = MODEL_DIR / f"{dataset_id}_preprocessor.json"
        preprocessor_path.write_text(
            json.dumps(prepared["preprocessor"], indent=2), encoding="utf-8"
        )
    metadata = {
        "dataset_id": dataset_id,
        "mode": prepared["mode"],
        "input_shape": list(prepared["input_shape"]),
        "num_classes": prepared["num_classes"],
        "class_names": prepared["class_names"],
        "split_sizes": {
            split: int(len(prepared[f"y_{split}"])) for split in ("train", "val", "test")
        },
        "class_distribution": {
            split: {
                str(label): int(count)
                for label, count in zip(
                    *np.unique(prepared[f"y_{split}"], return_counts=True)
                )
            }
            for split in ("train", "val", "test")
        },
        "class_weight": prepared["class_weight"],
        "split_sha256": prepared["split_sha256"],
        "processed_sha256": sha256_file(processed_path),
        "preprocessor_sha256": sha256_file(preprocessor_path),
        "split_manifest_sha256": sha256_file(split_path),
    }
    metadata_path = MANIFEST_DIR / f"{dataset_id}_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    return metadata


def _fit_candidate(framework, prepared, config, dataset_config, seed, learning_rate):
    model = _create_model(framework, prepared, config, seed, learning_rate)
    start = time.perf_counter()
    history = model.fit(
        prepared["x_train"],
        prepared["y_train"],
        prepared["x_val"],
        prepared["y_val"],
        epochs=dataset_config["max_epochs"],
        batch_size=dataset_config["batch_size"],
        patience=dataset_config["patience"],
        min_delta=config["min_delta"],
        class_weight=prepared["class_weight"] if dataset_config["class_weight"] else None,
    )
    training_seconds = time.perf_counter() - start
    val_probability = model.predict_proba(
        prepared["x_val"], batch_size=dataset_config["batch_size"]
    )
    val_prediction = np.argmax(val_probability, axis=1)
    val_metric = multiclass_metrics(
        prepared["y_val"], val_prediction, labels=range(prepared["num_classes"])
    )
    return {
        "model": model,
        "history": history,
        "training_seconds": training_seconds,
        "learning_rate": float(learning_rate),
        "val_macro_f1": val_metric["macro_f1"],
        "val_accuracy": val_metric["accuracy"],
        "val_loss": float(min(history["val_loss"])),
    }


def run_one(prepared, metadata, framework, seed, config):
    dataset_id = prepared["dataset_id"]
    dataset_config = config["datasets"][dataset_id]
    candidates = []
    search_start = time.perf_counter()
    for learning_rate in config["learning_rate_candidates"]:
        candidates.append(
            _fit_candidate(
                framework, prepared, config, dataset_config, seed, learning_rate
            )
        )
    search_seconds = time.perf_counter() - search_start
    selected = sorted(
        candidates,
        key=lambda row: (-row["val_macro_f1"], row["val_loss"], row["learning_rate"]),
    )[0]
    model = selected["model"]
    suffix = artifact_suffix(seed)
    stem = f"ch3_{dataset_id}_{framework}{suffix}"
    model_path = _model_path(dataset_id, framework, seed)
    model.save(model_path)
    model_sha256 = sha256_file(model_path)
    model.predict_proba(prepared["x_test"][: min(8, len(prepared["x_test"]))])
    inference_start = time.perf_counter()
    probabilities = model.predict_proba(
        prepared["x_test"], batch_size=dataset_config["batch_size"]
    )
    inference_seconds = time.perf_counter() - inference_start
    loaded = _load_model(framework, model_path)
    np.testing.assert_allclose(
        probabilities[:8],
        loaded.predict_proba(prepared["x_test"][:8]),
        atol=1e-6,
        rtol=0,
    )
    prediction_frame = build_prediction_frame(
        dataset_id=dataset_id,
        framework=framework,
        keys=prepared["keys"]["test"],
        y_true=prepared["y_test"],
        probabilities=probabilities,
        model_sha256=model_sha256,
        preprocessor_sha256=metadata["preprocessor_sha256"],
        split_sha256=metadata["split_sha256"],
        seed=seed,
    )
    PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    prediction_path = PREDICTION_DIR / f"{stem}_test.csv"
    prediction_frame.to_csv(prediction_path, index=False)
    metrics = multiclass_metrics(
        prediction_frame["y_true"],
        prediction_frame["y_pred"],
        labels=range(prepared["num_classes"]),
    )
    history = selected["history"]
    history_path = METRIC_DIR / f"{stem}_history.csv"
    pd.DataFrame(
        {
            "epoch": np.arange(1, len(history["train_loss"]) + 1),
            "train_loss": history["train_loss"],
            "val_loss": history["val_loss"],
        }
    ).to_csv(history_path, index=False)
    search_path = METRIC_DIR / f"{stem}_lr_search.csv"
    pd.DataFrame(
        [
            {
                "learning_rate": row["learning_rate"],
                "val_macro_f1": row["val_macro_f1"],
                "val_accuracy": row["val_accuracy"],
                "best_val_loss": row["val_loss"],
                "epochs_run": len(row["history"]["train_loss"]),
                "training_seconds": row["training_seconds"],
                "selected": row is selected,
            }
            for row in candidates
        ]
    ).to_csv(search_path, index=False)
    row = {
        "dataset_id": dataset_id,
        "framework": framework,
        "seed": int(seed),
        "split": "test",
        "topology_id": f"cnn_{prepared['mode']}_8_16_gap",
        "learning_rate": selected["learning_rate"],
        "parameter_count": model.parameter_count,
        "epochs_run": len(history["train_loss"]),
        "best_epoch": int(history["best_epoch"]),
        "training_seconds": float(selected["training_seconds"]),
        "search_seconds": float(search_seconds),
        "inference_seconds": float(inference_seconds),
        "inference_ms_per_sample": float(1000 * inference_seconds / len(prediction_frame)),
        "sample_count": len(prediction_frame),
        **metrics,
        "prediction_path": str(prediction_path.relative_to(TERM_ROOT)).replace("\\", "/"),
        "prediction_sha256": sha256_file(prediction_path),
        "model_path": str(model_path.relative_to(TERM_ROOT)).replace("\\", "/"),
        "model_sha256": model_sha256,
        "preprocessor_sha256": metadata["preprocessor_sha256"],
        "split_sha256": metadata["split_sha256"],
    }
    run_path = METRIC_DIR / f"{stem}_run.json"
    run_path.write_text(
        json.dumps(row, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8"
    )
    del loaded
    for candidate in candidates:
        candidate["model"] = None
    gc.collect()
    return row, prediction_frame


def _environment_manifest():
    import keras
    import tensorflow as tf
    import torch

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "tensorflow": tf.__version__,
        "keras": keras.__version__,
        "torch": torch.__version__,
        "device": "CPU",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int)
    args = parser.parse_args(argv)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    seeds = args.seeds or [int(value) for value in config["model_seeds"]]
    datasets = prepare_datasets(config)
    metadata = {key: save_prepared_dataset(value) for key, value in datasets.items()}
    all_rows = []
    for seed in seeds:
        for dataset_id, prepared in datasets.items():
            prediction_frames = {}
            for framework in config["frameworks"]:
                print(f"RUN {dataset_id} {framework} seed={seed}", flush=True)
                row, frame = run_one(prepared, metadata[dataset_id], framework, seed, config)
                all_rows.append(row)
                prediction_frames[framework] = frame
                print(
                    f"DONE macro_f1={row['macro_f1']:.4f} lr={row['learning_rate']} "
                    f"train={row['training_seconds']:.1f}s",
                    flush=True,
                )
            validate_matched_prediction_keys(prediction_frames)
    comparison_path = METRIC_DIR / "ch3_framework_comparison.csv"
    new_rows = pd.DataFrame(all_rows)
    if comparison_path.exists():
        existing = pd.read_csv(comparison_path)
        mask = ~existing["seed"].astype(int).isin(seeds)
        new_rows = pd.concat([existing.loc[mask], new_rows], ignore_index=True)
    new_rows.sort_values(["dataset_id", "framework", "seed"]).to_csv(
        comparison_path, index=False
    )
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (MANIFEST_DIR / "environment.json").write_text(
        json.dumps(_environment_manifest(), indent=2), encoding="utf-8"
    )
    print(f"WROTE {len(all_rows)} run rows to {comparison_path}", flush=True)


if __name__ == "__main__":
    main()
