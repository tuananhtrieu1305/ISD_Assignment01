"""Shared experiment utilities for Assignment 05.

The functions in this module are deliberately dataset-local and side-effect
light: they resolve paths inside the A05 project, preserve raw data files, and
keep test data isolated from validation-driven decisions.
"""

from __future__ import annotations

import csv
import json
import os
import random
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


DEFAULT_SEED = 42


class ExperimentError(RuntimeError):
    """Raised when an experiment utility cannot complete safely."""


def find_project_root(start: str | Path | None = None) -> Path:
    """Find the A05 project root from any nested path.

    The root is identified by `AGENTS.md` plus the expected `datasets/`,
    `models/`, `results/`, and `report/` directories.
    """

    current = Path.cwd() if start is None else Path(start)
    current = current.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (
            (candidate / "AGENTS.md").is_file()
            and (candidate / "datasets").is_dir()
            and (candidate / "models").is_dir()
            and (candidate / "results").is_dir()
            and (candidate / "report").is_dir()
        ):
            return candidate
    raise ExperimentError(f"Could not locate A05 project root from {current}")


def project_path(*parts: str | Path, start: str | Path | None = None) -> Path:
    """Resolve a path relative to the A05 project root."""

    return find_project_root(start).joinpath(*parts)


def ensure_directory(path: str | Path, start: str | Path | None = None) -> Path:
    """Create and return a directory, resolving relative paths under A05."""

    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = project_path(resolved, start=start)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def set_random_seed(seed: int = DEFAULT_SEED, deterministic: bool = True) -> dict[str, bool | int]:
    """Seed Python, NumPy, and TensorFlow/Keras when available."""

    os.environ["PYTHONHASHSEED"] = str(seed)
    if deterministic:
        os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")

    random.seed(seed)
    status: dict[str, bool | int] = {
        "seed": seed,
        "python_random": True,
        "numpy": False,
        "tensorflow": False,
        "deterministic_requested": deterministic,
    }

    try:
        import numpy as np  # type: ignore

        np.random.seed(seed)
        status["numpy"] = True
    except Exception:
        pass

    try:
        import tensorflow as tf  # type: ignore

        tf.keras.utils.set_random_seed(seed)
        if deterministic:
            try:
                tf.config.experimental.enable_op_determinism()
            except Exception:
                pass
        status["tensorflow"] = True
    except Exception:
        pass

    return status


@dataclass(frozen=True)
class ImageLoadResult:
    """Decoded RGB image plus metadata about the source content."""

    data: Any
    path: Path
    detected_format: str | None
    original_size: tuple[int, int]
    final_size: tuple[int, int]
    original_mode: str
    mode: str
    shape: tuple[int, int, int]


def load_image_rgb(
    path: str | Path,
    image_size: tuple[int, int] | None = None,
    *,
    start: str | Path | None = None,
    interpolation: int | None = None,
) -> ImageLoadResult:
    """Decode image content with Pillow, convert to RGB, and return HWC data.

    `image_size` is `(height, width)`. The source file is opened read-only and
    never converted or rewritten on disk. The decoder inspects image content, so
    `.jpg`-named PNG files in Oxford Pets are handled correctly.
    """

    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - exercised by environment
        raise ExperimentError("Pillow is required for robust image decoding.") from exc

    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - expected to exist in tests
        raise ExperimentError("NumPy is required to return image tensors.") from exc

    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = project_path(resolved, start=start)
    if not resolved.is_file():
        raise FileNotFoundError(f"Image file not found: {resolved}")

    with Image.open(resolved) as image:
        detected_format = image.format
        original_mode = image.mode
        original_size = image.size
        rgb = image.convert("RGB")
        if image_size is not None:
            height, width = image_size
            if height <= 0 or width <= 0:
                raise ValueError("image_size must contain positive height and width")
            resample = interpolation if interpolation is not None else Image.Resampling.BILINEAR
            rgb = rgb.resize((width, height), resample=resample)
        array = np.asarray(rgb, dtype=np.uint8)

    if array.ndim != 3 or array.shape[2] != 3:
        raise ExperimentError(f"Decoded image is not RGB/HWC: shape={array.shape}")

    return ImageLoadResult(
        data=array,
        path=resolved,
        detected_format=detected_format,
        original_size=(int(original_size[0]), int(original_size[1])),
        final_size=(int(array.shape[1]), int(array.shape[0])),
        original_mode=original_mode,
        mode="RGB",
        shape=(int(array.shape[0]), int(array.shape[1]), int(array.shape[2])),
    )


def label_from_oxford_image_id(image_id: str) -> str:
    """Extract the Oxford Pets class label from an image id."""

    label, separator, suffix = image_id.rpartition("_")
    return label if separator and suffix.isdigit() else image_id


def parse_oxford_split(
    split: str,
    *,
    root: str | Path | None = None,
) -> list[dict[str, int | str]]:
    """Parse an official Oxford Pets split file.

    Only `trainval` and `test` are valid canonical classification splits for
    this assignment.
    """

    if split not in {"trainval", "test"}:
        raise ValueError("split must be 'trainval' or 'test'")
    base = find_project_root(root) if root is not None else find_project_root()
    path = base / "datasets" / "oxford_pets" / "annotations" / f"{split}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Oxford split file not found: {path}")

    rows: list[dict[str, int | str]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            parts = text.split()
            if len(parts) < 4:
                raise ValueError(f"Malformed Oxford annotation line {line_number}: {text}")
            image_id = parts[0]
            rows.append(
                {
                    "split": split,
                    "image_id": image_id,
                    "filename": f"{image_id}.jpg",
                    "image_path": f"datasets/oxford_pets/images/{image_id}.jpg",
                    "class_id": int(parts[1]),
                    "species": int(parts[2]),
                    "breed_id": int(parts[3]),
                    "class_label": label_from_oxford_image_id(image_id),
                }
            )
    return rows


def load_oxford_official_splits(
    *,
    root: str | Path | None = None,
) -> dict[str, list[dict[str, int | str]] | int | list[str]]:
    """Load canonical Oxford trainval/test records and validate split isolation."""

    trainval = parse_oxford_split("trainval", root=root)
    test = parse_oxford_split("test", root=root)
    train_ids = {str(row["image_id"]) for row in trainval}
    test_ids = {str(row["image_id"]) for row in test}
    overlap = sorted(train_ids & test_ids)
    return {
        "trainval": trainval,
        "test": test,
        "total": len(trainval) + len(test),
        "unique_total": len(train_ids | test_ids),
        "overlap": overlap,
        "class_count": len({int(row["class_id"]) for row in trainval + test}),
    }


def split_train_validation(
    records: Sequence[Mapping[str, Any]],
    *,
    validation_fraction: float,
    seed: int = DEFAULT_SEED,
    stratify_key: str | None = "class_id",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split training records into train/validation without touching test data."""

    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")
    rng = random.Random(seed)
    materialized = [dict(row) for row in records]

    if stratify_key is None:
        shuffled = materialized[:]
        rng.shuffle(shuffled)
        val_count = max(1, round(len(shuffled) * validation_fraction))
        return shuffled[val_count:], shuffled[:val_count]

    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in materialized:
        groups[row[stratify_key]].append(row)

    train: list[dict[str, Any]] = []
    validation: list[dict[str, Any]] = []
    for key in sorted(groups, key=lambda value: str(value)):
        items = groups[key]
        rng.shuffle(items)
        val_count = max(1, round(len(items) * validation_fraction))
        validation.extend(items[:val_count])
        train.extend(items[val_count:])

    rng.shuffle(train)
    rng.shuffle(validation)
    return train, validation


def calculate_classification_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    labels: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Calculate accuracy and macro-averaged precision/recall/F1."""

    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))

    matrix = confusion_matrix(y_true, y_pred, labels)
    total = sum(sum(row) for row in matrix)
    correct = sum(matrix[i][i] for i in range(len(labels)))
    per_class: dict[str, dict[str, float | int]] = {}
    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []

    for i, label in enumerate(labels):
        tp = matrix[i][i]
        fp = sum(matrix[r][i] for r in range(len(labels)) if r != i)
        fn = sum(matrix[i][c] for c in range(len(labels)) if c != i)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        per_class[str(label)] = {
            "support": sum(matrix[i]),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    return {
        "accuracy": correct / total if total else 0.0,
        "macro_precision": sum(precisions) / len(precisions) if precisions else 0.0,
        "macro_recall": sum(recalls) / len(recalls) if recalls else 0.0,
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "labels": list(labels),
        "confusion_matrix": matrix,
        "per_class": per_class,
    }


def confusion_matrix(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    labels: Sequence[int] | None = None,
) -> list[list[int]]:
    """Generate a confusion matrix as nested lists."""

    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))
    label_to_index = {label: index for index, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    for truth, pred in zip(y_true, y_pred):
        if truth not in label_to_index or pred not in label_to_index:
            raise ValueError("Found a class value not present in labels")
        matrix[label_to_index[truth]][label_to_index[pred]] += 1
    return matrix


def history_to_rows(history: Any) -> list[dict[str, int | float | str]]:
    """Convert a Keras History object or history dict to row records."""

    values = history.history if hasattr(history, "history") else history
    if not isinstance(values, Mapping):
        raise TypeError("history must be a mapping or an object with .history")
    max_len = max((len(v) for v in values.values()), default=0)
    rows: list[dict[str, int | float | str]] = []
    for index in range(max_len):
        row: dict[str, int | float | str] = {"epoch": index + 1}
        for key, series in values.items():
            if index < len(series):
                row[str(key)] = series[index]
        rows.append(row)
    return rows


def plot_training_curves(
    history: Any,
    output_path: str | Path,
    *,
    metrics: Sequence[str] = ("loss", "accuracy"),
    start: str | Path | None = None,
) -> Path:
    """Plot training/validation curves and save a figure."""

    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:
        raise ExperimentError("matplotlib is required for plotting training curves.") from exc

    rows = history_to_rows(history)
    values = history.history if hasattr(history, "history") else history
    output = Path(output_path)
    if not output.is_absolute():
        output = project_path(output, start=start)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(len(metrics), 1, figsize=(7, 3 * len(metrics)), squeeze=False)
    epochs = [row["epoch"] for row in rows]
    for axis, metric in zip(axes[:, 0], metrics):
        if metric in values:
            axis.plot(epochs, values[metric], label=metric)
        val_metric = f"val_{metric}"
        if val_metric in values:
            axis.plot(epochs, values[val_metric], label=val_metric)
        axis.set_xlabel("epoch")
        axis.set_ylabel(metric)
        axis.legend()
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def save_json(data: Any, path: str | Path, *, start: str | Path | None = None) -> Path:
    """Save JSON with stable formatting."""

    output = Path(path)
    if not output.is_absolute():
        output = project_path(output, start=start)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_csv(
    rows: Sequence[Mapping[str, Any]],
    path: str | Path,
    *,
    fieldnames: Sequence[str] | None = None,
    start: str | Path | None = None,
) -> Path:
    """Save row dictionaries to CSV."""

    output = Path(path)
    if not output.is_absolute():
        output = project_path(output, start=start)
    output.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(str(key))
        fieldnames = keys
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)
    return output


def count_model_parameters(model: Any) -> dict[str, int]:
    """Count total/trainable/non-trainable parameters for Keras-like models."""

    if hasattr(model, "count_params"):
        total = int(model.count_params())
    else:
        total = 0

    def count_variables(variables: Iterable[Any]) -> int:
        count = 0
        for variable in variables:
            shape = getattr(variable, "shape", ())
            size = 1
            for dimension in shape:
                size *= int(dimension)
            count += size
        return count

    trainable = count_variables(getattr(model, "trainable_variables", []))
    non_trainable = count_variables(getattr(model, "non_trainable_variables", []))
    if total == 0:
        total = trainable + non_trainable
    return {"total": total, "trainable": trainable, "non_trainable": non_trainable}


@contextmanager
def elapsed_timer() -> Iterable[Callable[[], float]]:
    """Context manager returning a callable for elapsed seconds."""

    start = time.perf_counter()
    yield lambda: time.perf_counter() - start


def measure_elapsed_seconds(function: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """Run a callable and return `(result, elapsed_seconds)`."""

    start = time.perf_counter()
    result = function(*args, **kwargs)
    return result, time.perf_counter() - start


def time_inference(
    predict_fn: Callable[[Any], Any],
    inputs: Any,
    *,
    warmup_runs: int = 1,
    timed_runs: int = 5,
) -> dict[str, float | int]:
    """Measure inference latency for a prediction callable."""

    if warmup_runs < 0 or timed_runs <= 0:
        raise ValueError("warmup_runs must be >= 0 and timed_runs must be > 0")
    for _ in range(warmup_runs):
        predict_fn(inputs)
    durations: list[float] = []
    for _ in range(timed_runs):
        _, elapsed = measure_elapsed_seconds(predict_fn, inputs)
        durations.append(elapsed)
    return {
        "warmup_runs": warmup_runs,
        "timed_runs": timed_runs,
        "total_seconds": sum(durations),
        "mean_seconds": sum(durations) / len(durations),
        "min_seconds": min(durations),
        "max_seconds": max(durations),
    }

