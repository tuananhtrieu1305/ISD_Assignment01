"""Build the Vietnamese Chapter 3 evidence notebook from saved artifacts."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "term_paper" / "notebooks" / "ch3_cnn_framework_comparison.ipynb"


def markdown(text):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text):
    return nbf.v4.new_code_cell(text.strip())


def main():
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    }
    notebook["cells"] = [
        markdown(
            """
# Chương 3 — So sánh CNN scratch, Keras và PyTorch

Notebook này đọc lại artifact đã được tạo bởi Phase 4. Notebook **không huấn luyện lại** và không chọn mô hình từ TEST. Mục tiêu là kiểm tra split/provenance, tái tính metric từ prediction CSV, trình bày kết quả matched trên EuroSAT và CDC Diabetes, sau đó đặt kết quả A05 full-data ở một bảng ablation riêng.
"""
        ),
        code(
            """
from pathlib import Path
import json
import numpy as np
import pandas as pd
from IPython.display import display, Image
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

start = Path.cwd().resolve()
ROOT = next(path for path in (start, *start.parents) if (path / "term_paper").exists())
TERM = ROOT / "term_paper"
METRICS = TERM / "artifacts" / "metrics"
PREDICTIONS = TERM / "artifacts" / "predictions"
FIGURES = TERM / "artifacts" / "figures" / "ch3"
MANIFESTS = TERM / "artifacts" / "manifests" / "ch3"
print("Workspace:", ROOT)
"""
        ),
        markdown(
            """
## 1. Protocol và benchmark subset

- EuroSAT: 500 TRAIN / 150 VALIDATION / 150 TEST, ảnh RGB 64×64×3.
- CDC Diabetes 012: 6.000 / 1.500 / 1.500, 21 feature chuẩn hóa theo TRAIN và reshape `(21,1)`.
- Topology: Conv(8, kernel 3) → ReLU → MaxPool(2) → Conv(16, kernel 3) → ReLU → Global Average Pooling → Dense logits.
- Learning-rate candidates: 0,01 và 0,003; chọn bằng VALIDATION macro-F1.
- Model seeds: 42, 52 và 62; subset seed luôn là 42.
"""
        ),
        code(
            """
dataset_summary = pd.read_csv(METRICS / "ch3_dataset_summary.csv")
display(dataset_summary)
for dataset in ("ch3_eurosat", "ch3_diabetes_012"):
    metadata = json.loads((MANIFESTS / f"{dataset}_metadata.json").read_text(encoding="utf-8"))
    print(dataset, "split hash:", metadata["split_sha256"])
    print("class distribution:", metadata["class_distribution"])
"""
        ),
        markdown("## 2. Phân bố ba dataset"),
        code('display(Image(filename=str(FIGURES / "ch3_dataset_distributions.png")))'),
        markdown(
            """
EuroSAT gần cân bằng nhưng Pasture ít hơn các lớp 3.000 ảnh. Oxford có 37 lớp gần cân bằng. CDC lệch mạnh: Prediabetes chỉ chiếm khoảng 1,83%, vì vậy accuracy không thể thay thế macro-F1 và recall theo lớp.
"""
        ),
        markdown("## 3. Tái tính metric từ prediction artifact"),
        code(
            """
comparison = pd.read_csv(METRICS / "ch3_framework_comparison.csv")
checks = []
for _, row in comparison.iterrows():
    prediction = pd.read_csv(TERM / row["prediction_path"])
    labels = sorted(prediction["y_true"].unique())
    precision, recall, f1, _ = precision_recall_fscore_support(
        prediction["y_true"], prediction["y_pred"], labels=labels,
        average="macro", zero_division=0
    )
    accuracy = accuracy_score(prediction["y_true"], prediction["y_pred"])
    checks.append({
        "dataset": row["dataset_id"], "framework": row["framework"], "seed": row["seed"],
        "accuracy_delta": abs(accuracy - row["accuracy"]),
        "macro_f1_delta": abs(f1 - row["macro_f1"]),
        "samples": len(prediction),
    })
checks = pd.DataFrame(checks)
display(checks.head(9))
assert checks[["accuracy_delta", "macro_f1_delta"]].to_numpy().max() < 1e-12
print("PASS: metric của 18 run tái tính khớp CSV tổng hợp.")
"""
        ),
        markdown("## 4. Sample-key parity giữa ba framework"),
        code(
            """
for dataset in comparison["dataset_id"].unique():
    for seed in sorted(comparison["seed"].unique()):
        selected = comparison[(comparison.dataset_id == dataset) & (comparison.seed == seed)]
        keys = []
        for _, row in selected.iterrows():
            frame = pd.read_csv(TERM / row["prediction_path"])
            keys.append(frame[["sample_key", "y_true"]].astype(str).reset_index(drop=True))
        assert len(keys) == 3 and keys[0].equals(keys[1]) and keys[0].equals(keys[2])
print("PASS: cùng TEST sample và target cho mọi dataset/seed/framework.")
"""
        ),
        markdown("## 5. Kết quả matched trên ba seed"),
        code(
            """
summary = pd.read_csv(METRICS / "ch3_framework_summary.csv")
columns = [
    "dataset_id", "framework", "run_count", "parameter_count",
    "accuracy_mean", "accuracy_std", "macro_f1_mean", "macro_f1_std",
    "recall_class_1_mean", "recall_class_2_mean",
    "training_seconds_mean", "inference_ms_per_sample_mean",
]
display(summary[[column for column in columns if column in summary]])
display(Image(filename=str(FIGURES / "ch3_matched_macro_f1.png")))
"""
        ),
        markdown(
            """
Keras có mean macro-F1 EuroSAT cao nhất nhưng biến động seed lớn. Trên CDC, ba framework chỉ lệch nhau dưới 0,008 macro-F1; PyTorch cao nhất theo mean nhưng không đủ cơ sở để tuyên bố ưu thế phổ quát. Parameter count bằng nhau tuyệt đối: 1.562 cho EuroSAT và 483 cho CDC.
"""
        ),
        markdown("## 6. Learning dynamics và confusion matrix"),
        code(
            """
display(Image(filename=str(FIGURES / "ch3_validation_loss_curves.png")))
display(Image(filename=str(FIGURES / "ch3_matched_confusion_matrices.png")))
"""
        ),
        markdown(
            """
CDC Prediabetes vẫn là failure case chính dù dùng class weighting. Confusion matrix gộp ba seed cho thấy phần lớn lớp 1 bị dự đoán thành No diabetes hoặc Diabetes. Với EuroSAT subset, lỗi phân tán trên nhiều lớp và độ nhạy seed lớn hơn.
"""
        ),
        markdown("## 7. A05 architecture ablation và Oxford case study"),
        code(
            """
ablation = pd.read_csv(METRICS / "ch3_a05_architecture_ablation.csv")
display(ablation[["dataset_id", "model_family", "macro_f1", "test_accuracy", "parameter_count", "training_seconds"]])
display(Image(filename=str(FIGURES / "ch3_a05_architecture_ablation.png")))
"""
        ),
        markdown(
            """
Basic CNN đạt macro-F1 0,7256 trên EuroSAT full data. AlexNet/VGG/ResNet-inspired đều collapse ở 0,0200 dưới common protocol. Oxford rất yếu ở cả bốn family; Basic cao nhất cũng chỉ 0,0198 macro-F1. Các kết quả này được giữ nguyên như bằng chứng về giới hạn optimizer/budget, không bị loại khỏi báo cáo.

## 8. Kết luận kiểm chứng

1. Scratch CNN có backward thực cho Conv2D/Conv1D, pooling, GAP và Dense; numerical-gradient/toy-overfit được kiểm tra bằng unit test.
2. Ba framework dùng cùng benchmark samples, topology và validation search space trên EuroSAT/CDC.
3. Matched metric được tái tính từ 18 prediction files; sample-key parity đạt.
4. Oxford và architecture ablation được giữ ở track A05 riêng, không trộn với bảng matched subset.
5. Kết quả collapse/near-random được trình bày đầy đủ và giới hạn suy diễn được nêu rõ.
"""
        ),
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
