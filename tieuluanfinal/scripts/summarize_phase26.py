"""Generate Chapter2 tables/figures/manuscript from saved results, not new TEST inference."""

from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.ch02_ml.protocol import BASE, DATASETS, IMPLEMENTATIONS, METRICS, ref
from src.ch02_ml.test_gate import atomic_json
from src.ch02_ml.workflow import checked_reference
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json
from src.common.model_core import render_functions

FIGURES = ROOT / "artifacts/figures/phase26"
TABLES = METRICS / "tables"
LABELS = {
    "scratch": "MLP NumPy",
    "keras": "MLP Keras/TF",
    "pytorch": "MLP PyTorch",
    "majority": "Majority",
    "median": "Median",
    "logistic_regression": "Logistic",
    "ridge": "Ridge",
    "random_forest": "Random Forest",
}
NAMES = {
    "ch2_cdc_diabetes": "CDC Diabetes",
    "ch2_ames_housing": "Ames Housing",
    "ch2_bank_marketing": "Bank Marketing",
}


def csv_table(name, rows):
    TABLES.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (TABLES / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def predictions(record):
    with gzip.open(checked_reference(record), "rt", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    return np.asarray([r["target"] for r in rows]), np.asarray([r["prediction"] for r in rows])


def save_figure(name, fig):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / (name + ".png"), dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / (name + ".svg"), bbox_inches="tight", facecolor="white", metadata={"Date": None})
    plt.close(fig)


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        for metric, value in row.items():
            if metric.startswith(("quality_", "efficiency_")) and value is not None:
                groups[(row["dataset_id"], row["method"], row["split"], metric)].append(value)
    return [
        {
            "dataset_id": k[0],
            "method": k[1],
            "split": k[2],
            "metric": k[3],
            "n": len(v),
            "mean": float(np.mean(v)),
            "sample_std": float(np.std(v, ddof=1)) if len(v) > 1 else None,
            "seed_policy": "17,42,73; shared split, not independent dataset samples",
        }
        for k, v in sorted(groups.items())
    ]


def main():
    plt.rcParams["svg.hashsalt"] = "phase26_r2"
    release = read_json(BASE / "release.json")
    rows = []
    groups = []
    layers = []
    references = []
    selected = {}
    details = {}
    for entry in release["runs"]:
        run = entry["run_id"]
        selection = read_json(BASE / "runs" / run / "selection.json")
        selected[run] = selection
        test = read_json(BASE / "test_seals" / entry["dataset_id"] / (run + ".result.json"))
        for record in test.values():
            if isinstance(record, dict) and "path" in record:
                checked_reference(record)
                references.append(record)
        details[run] = read_json(checked_reference(test["details"]))
        for split in ("validation", "test"):
            path = METRICS / split / (run + ".json")
            result = read_json(path)
            references.append(ref(path))
            row = {
                "run_id": run,
                "dataset_id": entry["dataset_id"],
                "method": entry["method"],
                "seed": entry["seed"],
                "split": split,
                "track": "matched_subset",
                "device": result["device"],
                "config_sha256": entry["config"]["sha256"],
                "checkpoint_sha256": selection["checkpoint"]["sha256"],
                "code_sha256": release["code"]["dirty_tree_sha256"],
                "split_sha256": result.get("split_sha256", result.get("provenance", {}).get("split_sha256")),
            }
            row.update({"quality_" + metric["name"]: metric["value"] for metric in result["metrics"]})
            row.update({"efficiency_" + key: value for key, value in result["efficiency"].items()})
            rows.append(row)
        for group, values in details[run]["groups"].items():
            groups.append(
                {
                    "run_id": run,
                    "dataset_id": entry["dataset_id"],
                    "method": entry["method"],
                    "seed": entry["seed"],
                    "split": "test",
                    "group": group,
                    **values,
                    "diagnostic_only": True,
                }
            )
        if entry["seed"] == 42 and entry["method"] == "scratch":
            contract = read_json(checked_reference(entry["model_contract"]))
            for layer in contract["layers"]:
                layers.append(
                    {
                        "dataset_id": entry["dataset_id"],
                        "layer_id": layer["id"],
                        "kind": layer["kind"],
                        "input_shape": json.dumps(layer["input_shape"]),
                        "output_shape": json.dumps(layer["output_shape"]),
                        "parameter_count": layer["parameter_count"],
                    }
                )
            destination = ROOT / "report/references/functions/v3_ch2" / (entry["dataset_id"] + ".md")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(render_functions(contract)["markdown"], encoding="utf-8")
    summary = aggregate(rows)
    csv_table("runs.csv", rows)
    csv_table("aggregate.csv", summary)
    csv_table("test_groups.csv", groups)
    csv_table("layers.csv", layers)
    lookup = {(r["dataset_id"], r["method"], r["split"], r["metric"]): r for r in summary}

    def stat(dataset, method, metric, split="test"):
        return lookup[(dataset, method, split, metric)]

    def formatted(dataset, method, metric, digits=4, scale=1):
        value = stat(dataset, method, metric)
        return f"{value['mean'] / scale:,.{digits}f} ± {value['sample_std'] / scale:,.{digits}f}"

    methods = {
        ds: list(dict.fromkeys(row["method"] for row in rows if row["dataset_id"] == ds)) for ds in DATASETS
    }
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    )
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), layout="constrained")
    for ax, dataset in zip(axes, DATASETS, strict=True):
        metric = "quality_rmse" if dataset == "ch2_ames_housing" else "quality_macro_f1"
        values = [stat(dataset, m, metric) for m in methods[dataset]]
        ax.bar(
            range(6),
            [r["mean"] for r in values],
            yerr=[r["sample_std"] for r in values],
            capsize=3,
            color=["#305f8a"] * 3 + ["#9bafba"] * 3,
        )
        ax.set_xticks(range(6), [LABELS[m] for m in methods[dataset]], rotation=40, ha="right")
        ax.set_title(NAMES[dataset])
        ax.set_ylabel(
            "RMSE (USD), lower is better" if metric == "quality_rmse" else "Macro-F1, higher is better"
        )
        if metric != "quality_rmse":
            ax.set_ylim(0, 1)
    fig.suptitle("TEST • matched train • mean ± sample SD across seeds 17/42/73")
    save_figure("quality", fig)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), layout="constrained")
    for ax, dataset in zip(axes, DATASETS, strict=True):
        for method in IMPLEMENTATIONS:
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            history = read_json(BASE / "runs" / entry["run_id"] / "history.json")
            line = ax.plot(
                [r["epoch"] + 1 for r in history],
                [r["validation_loss"] for r in history],
                label=LABELS[method],
            )[0]
            ax.plot(
                [r["epoch"] + 1 for r in history],
                [r["train_loss"] for r in history],
                ls="--",
                alpha=0.6,
                color=line.get_color(),
            )
        ax.set_title(NAMES[dataset])
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Weighted BCE" if dataset != "ch2_ames_housing" else "MSE (standardized target)")
        ax.legend(fontsize=8)
    fig.suptitle("Seed 42 • solid: full validation • dashed: matched train • no TEST tuning")
    save_figure("learning_curves", fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7), layout="constrained")
    for ax, dataset in zip(axes, [DATASETS[0], DATASETS[2]], strict=True):
        ax.plot([0, 1], [0, 1], color="#888888", ls="--", label="Ideal")
        for method in methods[dataset]:
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            bins = [r for r in details[entry["run_id"]]["calibration"]["bins"] if r["count"]]
            ax.plot(
                [r["mean_probability"] for r in bins],
                [r["observed_rate"] for r in bins],
                marker="o",
                ms=3,
                label=LABELS[method],
            )
        ax.set(
            xlim=(0, 1),
            ylim=(0, 1),
            xlabel="Mean predicted P(class 1)",
            ylabel="Observed positive fraction",
            title=NAMES[dataset],
        )
        ax.legend(fontsize=8)
    fig.suptitle("TEST seed 42 • 10 fixed-width bins • descriptive, no calibrator fit")
    save_figure("calibration", fig)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), layout="constrained")
    for i, dataset in enumerate([DATASETS[0], DATASETS[2]]):
        for j, method in enumerate(IMPLEMENTATIONS):
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            matrix = np.asarray(details[entry["run_id"]]["metrics"]["confusion_matrix"])
            ax = axes[i, j]
            ax.imshow(matrix, cmap="Blues")
            for a in range(2):
                for b in range(2):
                    ax.text(
                        b,
                        a,
                        f"{matrix[a, b]:,}",
                        ha="center",
                        va="center",
                        color="white" if matrix[a, b] > matrix.max() / 2 else "black",
                    )
            ax.set(
                xticks=[0, 1],
                yticks=[0, 1],
                xlabel="Predicted class",
                ylabel="True class",
                title=NAMES[dataset] + " / " + LABELS[method],
            )
    fig.suptitle("TEST confusion counts • seed 42 • threshold > 0.5 (tie → class 0)")
    save_figure("confusion", fig)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), layout="constrained")
    for ax, method in zip(axes, IMPLEMENTATIONS, strict=True):
        entry = next(
            e
            for e in release["runs"]
            if e["dataset_id"] == DATASETS[1] and e["seed"] == 42 and e["method"] == method
        )
        result = read_json(BASE / "test_seals" / DATASETS[1] / (entry["run_id"] + ".result.json"))
        y, p = predictions(result["predictions"])
        bound = max(y.max(), p.max()) / 1000
        ax.scatter(y / 1000, p[:, 0] / 1000, s=12, alpha=0.5, color="#305f8a")
        ax.plot([0, bound], [0, bound], ls="--", color="#888888")
        ax.set(
            xlabel="Actual price (thousand USD)",
            ylabel="Predicted price (thousand USD)",
            title=LABELS[method],
        )
    fig.suptitle("Ames full TEST, n=440 • seed 42 • all points retained")
    save_figure("ames_predictions", fig)
    text = [
        "\n\n## 2.4. Kết quả thực nghiệm\n",
        "Các bảng sau tính từ prediction/metric artifact đã lưu. Mỗi ô là trung bình ± độ lệch chuẩn mẫu trên ba seed 17, 42, 73; mọi phương pháp cùng matched train và full TEST. Hình minh họa cố định seed 42, không chọn seed tốt nhất.\n",
    ]
    context = read_json(BASE / "benchmark_context.json")
    text.append(
        f"\nCấu hình đo: {context['cpu']} (10 lõi/16 luồng), RTX 5050 Laptop {context['gpu_total_mib']} MiB, driver {context['driver']}; WSL2 Ubuntu 24.04/Python {context['python']}; NumPy CPU, PyTorch {context['torch']}, Keras {context['keras']}/TensorFlow {context['tensorflow']}. MLP float32, batch train 32; inference batch 1, warm-up 5/đo 30 lần. Không khóa xung hay trạng thái nhiệt của máy.\n"
    )
    for dataset in DATASETS:
        text.append(f"\n### 2.4.{list(DATASETS).index(dataset) + 1}. {NAMES[dataset]}\n")
        metrics = (
            [("MAE (USD)", "quality_mae", 0), ("RMSE (USD)", "quality_rmse", 0), ("R²", "quality_r2", 4)]
            if dataset == DATASETS[1]
            else [
                ("Macro-F1", "quality_macro_f1", 4),
                ("AUROC", "quality_auroc", 4),
                ("Recall lớp 1", "quality_recall_class_1", 4),
                ("Accuracy", "quality_accuracy", 4),
            ]
        )
        text.append(
            "| Phương pháp | " + " | ".join(k[0] for k in metrics) + " |\n|---|" + "---:|" * len(metrics)
        )
        for method in methods[dataset]:
            text.append(
                "| "
                + LABELS[method]
                + " | "
                + " | ".join(formatted(dataset, method, key, digits) for _, key, digits in metrics)
                + " |"
            )
        key = "quality_rmse" if dataset == DATASETS[1] else "quality_macro_f1"
        ranked = sorted(
            methods[dataset], key=lambda m: stat(dataset, m, key)["mean"], reverse=key != "quality_rmse"
        )
        if dataset == DATASETS[0]:
            text.append(
                f"\nMajority đạt accuracy {stat(dataset, 'majority', 'quality_accuracy')['mean']:.4f} nhưng recall lớp 1 bằng 0. MLP scratch có recall lớp 1 {stat(dataset, 'scratch', 'quality_recall_class_1')['mean']:.4f}, đổi lại accuracy thấp hơn. Vì vậy không chọn mô hình chỉ từ accuracy; cần đọc đồng thời macro-F1, recall và số cảnh báo sai. Xác suất của mô hình có class weighting cũng không được xem trực tiếp là nguy cơ bệnh đã hiệu chỉnh.\n"
            )
        elif dataset == DATASETS[1]:
            difference = abs(
                stat(dataset, "keras", "quality_rmse")["mean"]
                - stat(dataset, "random_forest", "quality_rmse")["mean"]
            )
            text.append(
                f"\nChênh lệch RMSE trung bình giữa MLP Keras và Random Forest chỉ khoảng {difference:,.0f} USD, trong khi độ lệch chuẩn RMSE của Keras là {stat(dataset, 'keras', 'quality_rmse')['sample_std']:,.0f} USD. Không đủ căn cứ để khẳng định Keras thắng ổn định. Với MLP, RMSE lớn hơn nhiều MAE và biểu đồ có điểm lệch xa đường chéo; giữ nguyên những ví dụ sai số lớn này thay vì lọc TEST sau khi thấy kết quả.\n"
            )
        else:
            text.append(
                f"\nMajority đạt accuracy {stat(dataset, 'majority', 'quality_accuracy')['mean']:.4f} nhưng không phát hiện được lớp đăng ký. Ba MLP có macro-F1 gần nhau; khác biệt giữa framework cần đọc cùng độ lệch chuẩn ba seed. Do duration đã bị bỏ để đúng bối cảnh trước cuộc gọi, không so trực tiếp bảng này với thực nghiệm dùng duration như thể cùng điều kiện.\n"
            )
        text.append(
            f"\nTrong cấu hình đã khóa, {LABELS[ranked[0]]} có trung bình {'RMSE thấp nhất' if key == 'quality_rmse' else 'macro-F1 cao nhất'}. Đây là mô tả trên ba seed và một split, không phải kết luận hơn hẳn về mặt thống kê hoặc trên mọi dữ liệu. Không điều chỉnh mô hình theo thứ hạng TEST này.\n"
        )
    text += [
        "\n![So sánh chất lượng TEST](../../../artifacts/figures/phase26/quality.png)\n",
        "Hình 2.1. Chất lượng trên full TEST; error bar là độ lệch chuẩn giữa seed, không phải khoảng tin cậy theo dân số.\n",
        "\n### 2.4.4. Thời gian, bộ nhớ và kích thước\n",
        "| Dataset / phương pháp | Train (s) | Inference p50 (ms) | Peak RSS (MiB) | Peak allocator VRAM (MiB) | NPZ (KiB) |\n|---|---:|---:|---:|---:|---:|",
    ]
    for dataset in DATASETS:
        for method in methods[dataset]:
            cells = [
                formatted(dataset, method, key, digits, scale)
                for key, digits, scale in [
                    ("efficiency_train_seconds", 2, 1),
                    ("efficiency_inference_p50_ms", 3, 1),
                    ("efficiency_peak_ram_bytes", 1, 2**20),
                    ("efficiency_peak_vram_bytes", 1, 2**20),
                    ("efficiency_checkpoint_bytes", 1, 1024),
                ]
            ]
            text.append("| " + NAMES[dataset] + " / " + LABELS[method] + " | " + " | ".join(cells) + " |")
    smoke = read_json(BASE / "cpu_smoke.json")
    if smoke["status"] != "PASS":
        raise ValueError("CPU smoke not approved")
    text.append(
        "\nTiền xử lý đo riêng trên một bản ghi TRAIN đã nạp trong RAM, CPU, warm-up 5 và 30 lần đo; không fit lại scaler và không đọc TEST. Đây là số đo hậu kiểm trong runtime local, không phải chi phí huấn luyện. Trường `preprocessing_seconds` cũ trong validation_details thực tế đo bước nạp/cache development trước run, không phải thời gian fit scaler.\n"
    )
    text.append("| Dataset | Transform p50 (ms) | Transform p95 (ms) |\n|---|---:|---:|")
    for timing in smoke["preprocessing"]:
        text.append(
            f"| {NAMES[timing['dataset_id']]} | {timing['preprocessing_p50_ms']:.3f} | {timing['preprocessing_p95_ms']:.3f} |"
        )
    text += [
        "\nCPU scratch và GPU native khác thiết bị; TensorFlow graph và PyTorch eager khác đường thực thi. Với mạng nhỏ và batch 32, chi phí gọi kernel/đồng bộ/chuyển dữ liệu có thể đáng kể. Không suy từ bảng rằng GPU luôn nhanh hơn CPU hoặc một framework luôn tốt hơn. p95, thời gian tiền xử lý và provenance đầy đủ nằm trong CSV/JSON kèm theo. VRAM bằng 0 biểu thị phương pháp chạy CPU, không phải số đo bị thiếu.\n",
        "\n![Learning curves](../../../artifacts/figures/phase26/learning_curves.png)\n",
        "Hình 2.2. Loss train/validation seed 42. Train loss là trung bình trong lúc trọng số thay đổi; validation tính sau epoch, nên không cần bằng nhau ngay cả khi dùng cùng loss.\n",
        "\n### 2.4.5. Xác suất, sai số và phân tích nhóm\n",
        "\n![Calibration](../../../artifacts/figures/phase26/calibration.png)\n",
        "Hình 2.3. Reliability diagram từ prediction TEST đã lưu; bin rỗng không nối thành số 0. Class weighting làm mục tiêu học khác tần suất tự nhiên, nên phân biệt chất lượng phân lớp với hiệu chỉnh xác suất.\n",
        "\n![Confusion](../../../artifacts/figures/phase26/confusion.png)\n",
        "Hình 2.4. Confusion matrix seed 42, số đếm thật. Đọc false negative cùng recall lớp 1; accuracy cao không đồng nghĩa phát hiện tốt lớp thiểu số.\n",
        "\n![Giá nhà](../../../artifacts/figures/phase26/ames_predictions.png)\n",
        "Hình 2.5. Giá thật và dự đoán của 440 nhà TEST. Điểm lệch xa đường chéo là ví dụ sai số lớn; không loại chúng khỏi metric.\n",
    ]
    text.append(
        "\n| Dataset / nhóm / MLP seed 42 | Support | Recall / MAE | FPR / RMSE |\n|---|---:|---:|---:|"
    )
    for row in groups:
        if row["seed"] != 42 or row["method"] not in IMPLEMENTATIONS:
            continue
        a = row.get("mae", row.get("recall"))
        b = row.get("rmse", row.get("false_positive_rate"))
        text.append(
            f"| {NAMES[row['dataset_id']]} / {row['group']} / {LABELS[row['method']]} | {row['count']} | {'không xác định' if a is None else f'{a:.4f}'} | {'không xác định' if b is None else f'{b:.4f}'} |"
        )
    text += [
        "\nVới Ames, hai cột cuối là MAE và RMSE theo USD; với CDC/Bank là recall lớp 1 và FPR theo tỷ lệ. Chênh lệch giữa nhóm chỉ mô tả snapshot và chịu ảnh hưởng cỡ mẫu, thành phần đặc trưng và nhãn; không đủ để suy quan hệ nhân quả hay chứng nhận công bằng. Kết quả mọi seed, Brier/ECE và lý do metric không xác định nằm trong `test_groups.csv` và `test_details.json`.\n",
        "\n## 2.5. Kiểm chứng mã và hợp đồng mô hình\n",
        "Scratch tự thực hiện forward, loss, backward và Adam bằng NumPy. Keras dùng TensorFlow autodiff và graph step; PyTorch dùng CUDA autodiff. Cả ba đi từ cùng canonical weights; trước train kiểm forward/gradient trên mẫu TRAIN cố định, sau train đối chiếu native với NumPy. Các test tổng hợp kiểm numerical/parity core, cập nhật có trọng số, resume optimizer và dừng sớm; chúng không được trình bày như kết quả dữ liệu thật.\n",
        "\n| Dataset | Learnable layers | Tổng tham số MLP | Input → output |\n|---|---:|---:|---|",
    ]
    for dataset in DATASETS:
        entry = next(
            e
            for e in release["runs"]
            if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == "scratch"
        )
        contract = read_json(checked_reference(entry["model_contract"]))
        text.append(
            f"| {NAMES[dataset]} | {sum(r['parameter_count'] > 0 for r in contract['layers'])} | {contract['parameter_count']:,} | {contract['input_shape']} → {contract['output_shape']} |"
        )
    text += [
        "\nParameter count giống nhau giữa ba implementation; không đếm ReLU như lớp có tham số. Bảng từng lớp/shape nằm trong `layers.csv`; giải thích function ID, signature, công thức cần thiết, input/output và mapping framework nằm trong `report/references/functions/v3_ch2/`, sinh từ cùng contract. Không đưa toàn bộ vòng train dài vào thân tiểu luận.\n",
        "\n## 2.6. Đóng gói và hướng triển khai\n",
        "Mỗi run có NPZ trọng số chỉ chứa dữ liệu số, metadata hash/provenance, model contract và mẫu demo TRAIN. Bộ nạp dùng `allow_pickle=False`, kiểm hash, shape, dtype và giá trị hữu hạn; không dùng pickle/joblib để load mô hình Ch2. Cả checkpoint huấn luyện bằng GPU đều được nạp lại và dự đoán bằng NumPy CPU trên cùng mẫu, phù hợp làm nền cho môi trường deploy không GPU.\n",
        "Demo local chạy `scripts.demo_phase26 --dataset ch2_ames_housing --seed 42` qua runner WSL. Demo hiện dùng bốn mẫu TRAIN cố định và trả kết quả sáu phương pháp; đây không phải đánh giá TEST mới. Nạp checkpoint không có nghĩa ba framework đang chạy native trên Render: backend phục vụ CPU portable phải được ghi nhãn đúng. API/registry/UI mới và kiểm thử Render thuộc Phase 32–33; Phase 26 không thay UI hay tuyên bố trang đã deploy.\n",
        "\n## 2.7. Tiểu kết\n",
        "Chương này hoàn thiện một quy trình ML có dữ liệu, baseline, MLP sáu lớp và bằng chứng so sánh ba implementation. Kết quả cần được đọc cùng track lấy mẫu, đơn vị sai số, mất cân bằng lớp và giới hạn phần cứng. Độ sâu đáp ứng yêu cầu môn học nhưng không tự bảo đảm chất lượng; đánh giá có kiểm soát và khả năng truy nguồn quan trọng hơn việc chỉ chọn số metric đẹp.\n",
    ]
    manuscript = ROOT / "report/sections/v3/ch02_ml.md"
    manuscript.write_text(
        (ROOT / "report/sections/v3/ch02_ml_theory.md").read_text(encoding="utf-8") + "\n".join(text),
        encoding="utf-8",
    )
    for dataset in DATASETS:
        notebook = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "kernelspec": {
                    "display_name": "AI V3 PyTorch (WSL)",
                    "language": "python",
                    "name": "ai-v3-torch",
                }
            },
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# {NAMES[dataset]} — Chương 2 V3\n",
                        "Demo CPU từ checkpoint đã train; không mở TEST, không train lại. Code thuật toán nằm trong src/ch02_ml và core đã khóa. Xem contract/functions.json cho ba implementation.",
                    ],
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "execution_count": None,
                    "outputs": [],
                    "source": [
                        "from pathlib import Path\n",
                        "import os\n",
                        "repo = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / 'TIEU_LUAN_AI_V3_EXECUTION_PLAN.md').exists())\n",
                        "os.chdir(repo)\n",
                        "from scripts.demo_phase26 import demo\n",
                        f"result = demo('{dataset}', seed=42)\n",
                        "result",
                    ],
                },
            ],
        }
        notebook["metadata"]["kernelspec"]["display_name"] = "AI V3 (torch, WSL GPU)"
        for index, cell in enumerate(notebook["cells"]):
            cell["id"] = f"phase26-{index}"
        path = ROOT / "experiments/notebooks/v3/ch02_ml" / (dataset + ".ipynb")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = []
    for entry in release["runs"]:
        run = entry["run_id"]
        selection = selected[run]
        registry.append(
            {
                **entry,
                "lifecycle": "trained_evaluated_cpu_parity_verified",
                "inference_ready": True,
                "serving_backend": "numpy_cpu_portable",
                "checkpoint": selection["checkpoint"],
                "checkpoint_metadata": selection["checkpoint_metadata"],
                "cpu_demo": selection["cpu_demo"],
                "classical_metadata": selection["classical_metadata"],
                "test_metrics": ref(METRICS / "test" / (run + ".json")),
                "test_seal": ref(BASE / "test_seals" / entry["dataset_id"] / "seal.json"),
                "functions": ref(BASE / "runs" / run / "functions.json")
                if entry["method"] in IMPLEMENTATIONS
                else None,
            }
        )
    write_once(
        BASE / "trained_registry.json",
        {
            "registry_version": "phase26.trained.1",
            "release": ref(BASE / "release.json"),
            "primary_demo_seed": 42,
            "models": registry,
            "test_prediction_replay_forbidden": True,
            "cpu_serving_is_not_native_framework_inference": True,
        },
    )
    atomic_json(
        BASE / "report_generation.json",
        {
            "status": "PASS",
            "input_results": references,
            "generator": ref(Path(__file__)),
            "supporting_files": [
                ref(BASE / "cpu_smoke.json"),
                ref(ROOT / "scripts/smoke_phase26.py"),
                ref(BASE / "preservation-tests.xml"),
                ref(ROOT / "tests/test_phase26_preservation.py"),
                ref(BASE / "audit_revision.json"),
                ref(BASE / "benchmark_context.json"),
                ref(BASE / "report-acceptance-tests.xml"),
                ref(ROOT / "tests/test_phase26_report_acceptance.py"),
            ],
            "manuscript": ref(manuscript),
            "figures": [ref(path) for path in sorted(FIGURES.glob("*.png"))],
            "tables": [ref(path) for path in sorted(TABLES.glob("*.csv"))],
            "test_inference_executed": False,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "measured_run_rows": len(rows),
                "aggregate_rows": len(summary),
                "figures": 5,
                "tables": len(list(TABLES.glob("*.csv"))),
                "test_inference_executed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
