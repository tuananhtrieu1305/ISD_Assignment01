"""Metrics derived from Chapter 3 prediction artifacts."""

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def multiclass_metrics(y_true, y_pred, labels):
    y_true = np.asarray(y_true, dtype=int).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=int).reshape(-1)
    labels = [int(value) for value in labels]
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    result = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(macro_precision),
        "macro_recall": float(macro_recall),
        "macro_f1": float(macro_f1),
    }
    for index, label in enumerate(labels):
        result[f"precision_class_{label}"] = float(precision[index])
        result[f"recall_class_{label}"] = float(recall[index])
        result[f"f1_class_{label}"] = float(f1[index])
        result[f"support_class_{label}"] = int(support[index])
    return result
