"""CNN tables/figures/manuscript derived from saved measurements only."""

import json
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.ch03_cnn.protocol import BASE, DATASETS, IMPLEMENTATIONS, METRICS, check_sources, ref
from src.ch03_cnn.workflow import CnnEvaluationGate
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

FIGURES = ROOT / "artifacts/figures/phase27"
LABELS = {"ch3_idrid": "IDRiD", "ch3_eurosat": "EuroSAT", "ch3_cifar10": "CIFAR-10"}
METHODS = (*IMPLEMENTATIONS, "majority")
COLORS = {"scratch": "#236C9C", "keras": "#C1792C", "pytorch": "#7656A0", "majority": "#929A9F"}


def figures(records, release):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.hashsalt": "cnn_phase27_v1",
        }
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    outputs = []

    def save(fig, name):
        fig.tight_layout()
        for extension in ("png", "svg"):
            path = FIGURES / f"{name}.{extension}"
            fig.savefig(
                path,
                dpi=300,
                metadata={"Date": None} if extension == "svg" else {"Software": "AI V3 Phase27"},
            )
            outputs.append(ref(path))
        plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 7.8))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        groups = [
            [
                r["macro_f1"]
                for r in records
                if r["dataset_id"] == dataset and r["method"] == method and r["split"] == "test"
            ]
            for method in METHODS
        ]
        means, deviations = [np.mean(g) for g in groups], [np.std(g, ddof=1) for g in groups]
        ax.bar(METHODS, means, yerr=deviations, capsize=4, color=[COLORS[m] for m in METHODS])
        ax.set(title=LABELS[dataset] + " — full TEST", ylim=(0, 1), ylabel="Macro-F1")
        ax.tick_params(axis="x", labelrotation=20)
    save(fig, "quality")

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 7.8))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        groups = [
            [
                r["train_seconds"]
                for r in records
                if r["dataset_id"] == dataset and r["method"] == method and r["split"] == "validation"
            ]
            for method in IMPLEMENTATIONS
        ]
        means = [np.mean(g) for g in groups]
        ax.bar(
            ["scratch\nCPU", "Keras\nGPU graph", "PyTorch\nGPU eager"],
            means,
            color=[COLORS[m] for m in IMPLEMENTATIONS],
        )
        ax.set(title=LABELS[dataset], ylabel="Train seconds (log)", yscale="log")
        for i, value in enumerate(means):
            ax.text(i, value * 1.05, f"{value:.1f}", ha="center", va="bottom", fontsize=9)
        ax.margins(y=0.25)
    save(fig, "train_time")

    for dataset in DATASETS:
        fig, axes = plt.subplots(1, 3, figsize=(12.6, 5.2))
        for ax, method in zip(axes, IMPLEMENTATIONS, strict=True):
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            details = read_json(BASE / "runs" / entry["run_id"] / "test_details.json")
            cm = np.asarray(details["metrics"]["confusion_matrix"])
            im = ax.imshow(cm, cmap="Blues", vmin=0)
            for i in range(len(cm)):
                for j in range(len(cm)):
                    ax.text(
                        j,
                        i,
                        str(cm[i, j]),
                        ha="center",
                        va="center",
                        fontsize=14,
                        color="white" if cm[i, j] > cm.max() * 0.5 else "#18252C",
                    )
            ax.set(
                xticks=range(len(cm)),
                yticks=range(len(cm)),
                xticklabels=range(len(cm)),
                yticklabels=range(len(cm)),
                xlabel="Predicted class ID",
                ylabel="True class ID",
                title=f"{method} — seed42",
            )
            ax.xaxis.label.set_size(18)
            ax.yaxis.label.set_size(18)
            ax.title.set_size(20)
            ax.tick_params(axis="both", labelsize=16)
            bar = fig.colorbar(im, ax=ax, shrink=0.7)
            bar.ax.tick_params(labelsize=14)
        fig.suptitle(LABELS[dataset] + " — full TEST counts, fixed seed42", y=0.99, fontsize=18)
        save(fig, dataset + "_confusion")

    fig, axes = plt.subplots(3, 3, figsize=(12.6, 10.0))
    for row, dataset in enumerate(DATASETS):
        for col, method in enumerate(IMPLEMENTATIONS):
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            history = read_json(BASE / "runs" / entry["run_id"] / "history.json")
            selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
            ax = axes[row, col]
            ax.plot(
                [h["epoch"] + 1 for h in history],
                [h["train_loss"] for h in history],
                label="train",
                color=COLORS[method],
            )
            ax.plot(
                [h["epoch"] + 1 for h in history],
                [h["validation_loss"] for h in history],
                label="validation",
                color=COLORS[method],
                linestyle="--",
            )
            ax.axvline(selected["best_epoch"] + 1, color="#6B7175", linestyle=":", linewidth=1)
            ax.set(title=f"{LABELS[dataset]} / {method}", xlabel="Epoch", ylabel="Cross-entropy")
            ax.tick_params(axis="both", labelsize=16)
            ax.xaxis.label.set_size(16)
            ax.yaxis.label.set_size(16)
            ax.title.set_size(18)
            ax.legend(fontsize=16)
    save(fig, "learning_curves")

    fig, axes = plt.subplots(3, 4, figsize=(12.6, 9.5))
    from src.ch03_cnn.image_cache import development_cache

    for row, dataset in enumerate(DATASETS):
        cache, view = development_cache(dataset)
        key = view.ids("train")[0]
        axes[row, 0].imshow(cache.pixels[cache.positions[key]])
        axes[row, 0].set_title(LABELS[dataset] + " / TRAIN", fontsize=18)
        axes[row, 0].axis("off")
        for col, method in enumerate(IMPLEMENTATIONS, start=1):
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["seed"] == 42 and e["method"] == method
            )
            data = read_json(BASE / "saliency" / f"{entry['run_id']}.json")
            axes[row, col].imshow(data["map"], cmap="magma", vmin=0, vmax=1)
            axes[row, col].set_title(f"{method} / predicted ID {data['predicted_class_id']}", fontsize=18)
            axes[row, col].axis("off")
    fig.suptitle("TRAIN-only sensitivity, seed42; normalized per image, not lesion maps", y=0.99, fontsize=18)
    save(fig, "train_saliency")
    return outputs


def main():
    lock_path = BASE / "experiment_lock.json"
    if lock_path.exists():
        for item in read_json(lock_path)["files"]:
            if sha256_file(ROOT / item["path"]) != item["sha256"]:
                raise ValueError("Locked CNN artifact changed")
        print(json.dumps({"status": "PASS", "mode": "locked_read_only"}))
        return
    release = check_sources()
    for dataset in DATASETS:
        gate = CnnEvaluationGate(BASE / "test_seals" / dataset)
        if gate.state()["state"] != "evaluated" or gate.state()["evaluation_count"] != 1:
            raise ValueError("Cannot summarize an incomplete CNN TEST matrix")
    records, registry = [], []
    for entry in release["runs"]:
        selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
        contract = read_json(ROOT / entry["model_contract"]["path"])
        for split in ("validation", "test"):
            document = read_json(METRICS / split / f"{entry['run_id']}.json")
            row = {
                "run_id": entry["run_id"],
                "dataset_id": entry["dataset_id"],
                "method": entry["method"],
                "seed": entry["seed"],
                "split": split,
                "device": document["device"],
                **{m["name"]: m["value"] for m in document["metrics"]},
                **document["efficiency"],
                "parameter_count": contract.get("parameter_count"),
                "best_epoch_1based": selected["best_epoch"] + 1
                if selected["best_epoch"] is not None
                else None,
                "metric_artifact": ref(METRICS / split / f"{entry['run_id']}.json"),
            }
            records.append(row)
        registry.append(
            {
                "model_id": entry["run_id"],
                "dataset_id": entry["dataset_id"],
                "family": "cnn" if entry["method"] in IMPLEMENTATIONS else "classical",
                "training_implementation": entry["method"],
                "training_backend": {
                    "scratch": "numpy",
                    "keras": "tensorflow",
                    "pytorch": "torch",
                    "majority": "numpy",
                }[entry["method"]],
                "serving_backend": "numpy_cpu_portable",
                "seed": entry["seed"],
                "lifecycle": "trained_evaluated",
                "inference_ready": True,
                "checkpoint": selected["checkpoint"],
                "checkpoint_metadata": selected["checkpoint_metadata"],
                "config": selected["config"],
                "model_contract": selected["model_contract"],
                "comparison_group_sha256": entry["comparison_group_sha256"],
                "test_metrics": ref(METRICS / "test" / f"{entry['run_id']}.json"),
            }
        )
    fields = [
        "accuracy",
        "macro_f1",
        "weighted_f1",
        "auroc",
        "average_precision",
        "train_seconds",
        "inference_p50_ms",
        "inference_p95_ms",
        "peak_ram_bytes",
        "peak_vram_bytes",
        "checkpoint_bytes",
        "parameter_count",
    ]
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["dataset_id"], row["method"], row["split"])].append(row)
    aggregate = []
    for (dataset, method, split), rows in sorted(grouped.items()):
        if {r["seed"] for r in rows} != {17, 42, 73}:
            raise ValueError("Incomplete CNN seed aggregation")
        for field in fields:
            values = [r[field] for r in rows if r[field] is not None]
            aggregate.append(
                {
                    "dataset_id": dataset,
                    "method": method,
                    "split": split,
                    "metric": field,
                    "n": len(values),
                    "mean": float(np.mean(values)) if values else None,
                    "sample_std": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                    "undefined_reason": None if values else "Not applicable or unavailable in every run",
                }
            )
    tables = METRICS / "tables"
    write_once(tables / "runs.json", records)
    write_once(tables / "aggregate.json", aggregate)
    write_once(
        BASE / "trained_contract_registry.json",
        {
            "version": "phase27.trained.1",
            "inference_ready": True,
            "initialized_registry_unchanged": True,
            "models": registry,
        },
    )
    plot_refs = figures(records, release)

    def summary(dataset, method, metric, split="test"):
        return next(
            r
            for r in aggregate
            if (r["dataset_id"], r["method"], r["metric"], r["split"]) == (dataset, method, metric, split)
        )

    def fmt(row, scale=1, digits=4):
        return (
            "không áp dụng"
            if row["mean"] is None
            else f"{row['mean'] / scale:.{digits}f} ± {row['sample_std'] / scale:.{digits}f}"
        )

    text = (ROOT / "report/sections/v3/ch03_cnn_theory.md").read_text(encoding="utf-8")
    text += "\n\n## 3.5. Kết quả thực nghiệm\n\n"
    text += "Toàn bộ 27 CNN và 9 baseline đã hoàn tất. Các bảng dưới dùng full TEST, mean ± sample SD trên ba seed 17/42/73. Không chọn seed tốt nhất theo TEST. Baseline lặp theo seed để cùng định dạng, có kết quả giống nhau vì không có bước học ngẫu nhiên.\n\n"
    text += "| Dataset | Cách triển khai | Macro-F1 | Accuracy | Weighted-F1 | AUROC |\n|---|---|---:|---:|---:|---:|\n"
    for dataset in DATASETS:
        for method in METHODS:
            text += (
                f"| {LABELS[dataset]} | {method} | "
                + " | ".join(
                    fmt(summary(dataset, method, metric))
                    for metric in ("macro_f1", "accuracy", "weighted_f1", "auroc")
                )
                + " |\n"
            )
    text += "\n![Hình 3.4. Macro-F1 trên full TEST, matched train, ba seed. Thanh sai số là sample SD, không phải khoảng tin cậy.](../../../artifacts/figures/phase27/quality.png)\n\n"
    for dataset in DATASETS:
        baseline = summary(dataset, "majority", "macro_f1")["mean"]
        text += (
            f"{LABELS[dataset]}: macro-F1 trung bình scratch/Keras/PyTorch lần lượt là "
            + ", ".join(f"{summary(dataset, method, 'macro_f1')['mean']:.4f}" for method in IMPLEMENTATIONS)
            + f"; majority là {baseline:.4f}. Đây là kết quả của kiến trúc nhỏ và matched train đã khóa, không phải chất lượng tối đa có thể đạt trên bộ dữ liệu.\n\n"
        )
    text += "### 3.5.1. Recall từng lớp và lỗi nhầm lẫn\n\n"
    text += "Confusion matrix dùng seed42 đã định trước để minh họa, không chọn seed bằng TEST. Hàng là nhãn thật, cột là dự đoán. Bảng recall dùng cả ba seed; giá trị nhỏ cho biết mô hình bỏ sót nhiều ảnh của lớp đó.\n\n"
    recall_rows = []
    for dataset in DATASETS:
        config = read_json(
            ROOT / next(e for e in release["runs"] if e["dataset_id"] == dataset)["config"]["path"]
        )
        text += f"#### {LABELS[dataset]}\n\n| Lớp nguồn | Scratch recall | Keras recall | PyTorch recall |\n|---|---:|---:|---:|\n"
        for class_id, name in sorted(config["class_names"].items(), key=lambda x: int(x[0])):
            formatted = []
            for method in IMPLEMENTATIONS:
                vals = [
                    r[f"recall_class_{class_id}"]
                    for r in records
                    if r["dataset_id"] == dataset and r["method"] == method and r["split"] == "test"
                ]
                valid = [v for v in vals if v is not None]
                row = {
                    "dataset_id": dataset,
                    "class_id": int(class_id),
                    "class_name": name,
                    "method": method,
                    "split": "test",
                    "n": len(valid),
                    "mean": float(np.mean(valid)) if valid else None,
                    "sample_std": float(np.std(valid, ddof=1)) if len(valid) > 1 else None,
                }
                recall_rows.append(row)
                formatted.append(fmt(row))
            text += f"| {class_id}: {name} | " + " | ".join(formatted) + " |\n"
        text += f"\n![Hình 3.{5 + list(DATASETS).index(dataset)}. Confusion matrix {LABELS[dataset]}, full TEST, seed42, matched train.](../../../artifacts/figures/phase27/{dataset}_confusion.png)\n\n"
        for method in IMPLEMENTATIONS:
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset and e["method"] == method and e["seed"] == 42
            )
            cm = np.asarray(
                read_json(BASE / "runs" / entry["run_id"] / "test_details.json")["metrics"][
                    "confusion_matrix"
                ]
            )
            errors = [
                (int(cm[i, j]), i, j)
                for i in range(len(cm))
                for j in range(len(cm))
                if i != j and cm[i, j] > 0
            ]
            errors.sort(key=lambda x: (-x[0], x[1], x[2]))
            if errors:
                count, i, j = errors[0]
                text += f"{method}, seed42: cặp nhầm nhiều nhất là {config['class_names'][str(i)]} → {config['class_names'][str(j)]}, {count} ảnh. Đây là mô tả lỗi từ prediction đã lưu, không dùng để thay dữ liệu hoặc tuning sau TEST.\n\n"
    write_once(tables / "per_class_recall.json", recall_rows)
    text += "### 3.5.2. Thời gian, bộ nhớ và checkpoint\n\n| Dataset | Triển khai / thiết bị train | Train giây | Inference p50 ms | Peak RSS MiB | Allocator VRAM MiB | Checkpoint KiB |\n|---|---|---:|---:|---:|---:|---:|\n"
    for dataset in DATASETS:
        for method in IMPLEMENTATIONS:
            text += (
                f"| {LABELS[dataset]} | {method} / {'CPU' if method == 'scratch' else 'GPU'} | "
                + " | ".join(
                    fmt(summary(dataset, method, metric, "validation"), scale=scale, digits=2)
                    for metric, scale in (
                        ("train_seconds", 1),
                        ("inference_p50_ms", 1),
                        ("peak_ram_bytes", 1024**2),
                        ("peak_vram_bytes", 1024**2),
                        ("checkpoint_bytes", 1024),
                    )
                )
                + " |\n"
            )
    text += "\nTrain bao gồm validation/checkpoint I/O, không bao gồm import framework hoặc chuẩn bị cache trước timer. Inference gồm layout/transfer; thời gian tiền xử lý được lưu riêng. RSS là high-water của process; allocator VRAM không gồm driver/ứng dụng khác. Không suy ra framework nào luôn tốt hơn từ benchmark CPU scratch so với GPU native trên một laptop.\n\n"
    text += "Lượt scratch IDRiD seed73 được resume từ epoch7 sau gián đoạn: thời gian train cộng các đoạn chạy, loại thời gian tạm dừng; timestamp metric thuộc invocation hoàn tất. Peak RSS của lượt này là process resume, không có số đo đã chốt từ process cũ để khẳng định peak gộp toàn lượt. Các số RAM trong bảng phải được đọc theo phạm vi process, không như một phép đo peak liên tục trên mọi lượt.\n\n"
    text += "| Dataset | Tiền xử lý demo p50 ms | Tiền xử lý demo p95 ms |\n|---|---:|---:|\n"
    for case in read_json(BASE / "cpu_smoke.json")["cases"]:
        timing = case["preprocessing_timing"]
        text += f"| {LABELS[case['dataset_id']]} | {timing['inference_p50_ms']:.3f} | {timing['inference_p95_ms']:.3f} |\n"
    text += "\nĐo tiền xử lý dùng PNG đã nạp base64 ở kích thước model, gồm giải mã/resize/rescale và đọc–kiểm hash metadata hợp đồng, không gồm tải ảnh qua mạng hoặc đọc file ảnh. Đây không phải chi phí giải mã ảnh IDRiD gốc 4288×2848. Cả ba trường hợp dùng 5 warmup và 30 lần đo trên CPU.\n\n"
    text += "![Hình 3.8. Train wall mean trên ba seed; trục log, CPU/GPU và graph/eager được ghi riêng.](../../../artifacts/figures/phase27/train_time.png)\n\n"
    text += "### 3.5.3. Quá trình học và minh họa độ nhạy\n\n![Hình 3.9. Train/validation loss theo epoch, seed42; đường dọc chỉ checkpoint được chọn bởi validation.](../../../artifacts/figures/phase27/learning_curves.png)\n\n"
    text += "Khi train loss giảm nhưng validation loss tăng, mô hình có dấu hiệu học quá sát train. Early stopping giữ checkpoint validation tốt nhất, không giữ epoch cuối chỉ vì train loss nhỏ hơn. Sai khác số học giữa CPU/GPU có thể tạo quỹ đạo cập nhật khác nhau sau nhiều bước; parity ban đầu không bảo đảm mọi epoch có cùng trọng số hoặc cùng nhãn dự đoán.\n\n"
    text += "![Hình 3.10. Độ nhạy logit trên ảnh TRAIN đầu tiên cố định, seed42; chuẩn hóa riêng mỗi ảnh.](../../../artifacts/figures/phase27/train_saliency.png)\n\n"
    text += "Saliency ở đây là trị tuyệt đối gradient logit của lớp dự đoán theo đầu vào, lấy cực đại qua kênh rồi chia cực đại của ảnh; ảnh có gradient bằng 0 giữ bản đồ 0. Vùng sáng chỉ cho biết độ nhạy cục bộ của mô hình ở ví dụ này, không xác nhận tổn thương, nguyên nhân hay vùng chú ý đúng. Không chọn ảnh theo kết quả TEST và không dùng heatmap để biện minh chẩn đoán.\n\n"
    text += "## 3.6. Triển khai demo và giới hạn\n\nBa checkpoint được train độc lập nhưng có thể chuyển về cùng layout canonical và nạp bằng NumPy CPU, không cần CUDA ở server. Demo nhận một ảnh RGB, kiểm schema/size/media type, resize/rescale một lần rồi đưa cùng tensor cho cả ba checkpoint. Kết quả theo API contract ghi training implementation, actual backend `numpy`, device `cpu`, hash input/checkpoint và comparison group. Vì đây là portable serving, ba nhãn scratch/Keras/PyTorch không có nghĩa server đang chạy đồng thời ba framework native.\n\n"
    text += "Chạy demo bằng `scripts.demo_phase27 --dataset ch3_idrid` trong wrapper WSL; ba notebook ở `experiments/notebooks/v3/ch03_cnn/` chỉ dùng fixed TRAIN input và đọc metric đã lưu. Chúng không train hoặc chạy lại TEST. HTTP API, tab React và kiểm tra Render được tích hợp ở Phase32–33; không tuyên bố đã có deployment live trong Phase27.\n\n"
    text += "Hạn chế chính là train IDRiD nhỏ/mất cân bằng, ảnh giảm kích thước, CNN ít kênh, matched subset ở EuroSAT/CIFAR, không augmentation ở track chính, thiếu khóa bệnh nhân/địa lý và chỉ ba seed trên một máy. Xác suất softmax không tự chứng minh được hiệu chuẩn hay an toàn y khoa. Các phần này giới hạn cách sử dụng kết quả, không được bỏ khi trình bày chất lượng mô hình.\n\n"
    text += "## 3.7. Tổng kết\n\nChương đã nối ba bài toán ảnh với cùng CNN bảy lớp, triển khai forward/backward/Adam scratch và hai backend GPU độc lập. Kiểm tra khởi tạo, batch/ID, optimizer resume, checkpoint CPU và TEST one-shot giúp phân biệt đúng đắn code với chất lượng dự đoán. Việc lựa chọn công cụ cần xét đồng thời metric, thời gian, bộ nhớ, độ dễ kiểm chứng và hạn chế dữ liệu, không chỉ accuracy cao nhất.\n\nNguồn số liệu: `artifacts/metrics/phase27/tables/`; source/split/preprocessing Phase23–25; run/selection/TEST seals và trained registry tại `artifacts/manifests/phase27/`.\n"
    path = ROOT / "report/sections/v3/ch03_cnn.md"
    path.write_text(text, encoding="utf-8", newline="\n")
    write_once(
        BASE / "report_generation.json",
        {
            "status": "PASS",
            "source": "saved validation/TEST metric and prediction artifacts; no evaluation",
            "run_rows": len(records),
            "aggregate_rows": len(aggregate),
            "per_class_recall_rows": len(recall_rows),
            "figures": plot_refs,
            "manuscript": ref(path),
            "tables": [ref(tables / (name + ".json")) for name in ("runs", "aggregate", "per_class_recall")],
        },
    )
    print(
        json.dumps(
            {"status": "PASS", "run_rows": len(records), "figures": len(plot_refs) // 2, "report": str(path)}
        )
    )


if __name__ == "__main__":
    main()
