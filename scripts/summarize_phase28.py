"""Derive validation tables, scientific figures and RNN manuscript; never evaluate TEST."""

import argparse
import gzip
import json
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.ch04_rnn_lstm.protocol import (
    BASE,
    DATASETS,
    IMPLEMENTATIONS,
    METRICS,
    ROOT,
    check_sources,
    checked,
    ref,
)
from src.common.artifact_core import write_once
from src.common.contracts import read_json

FIGURES = ROOT / "artifacts/figures/phase28"
LABELS = {
    "ch4_gold_pink_sheet": "Gold",
    "ch4_bis_house_prices": "BIS house index",
    "ch4_household_power": "Household power",
}
METHODS = (*IMPLEMENTATIONS, "last_value", "seasonal_naive")
COLORS = {
    "scratch": "#236C9C",
    "keras": "#C1792C",
    "pytorch": "#7656A0",
    "last_value": "#555F66",
    "seasonal_naive": "#33816D",
}
UNITS = {
    "ch4_gold_pink_sheet": "USD/troy ounce",
    "ch4_bis_house_prices": "index 2010=100",
    "ch4_household_power": "kW",
}


def collect(release):
    records, registry, horizons, series = [], [], [], []
    for entry in release["runs"]:
        selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
        details = read_json(checked(selected["details"]))
        metric = read_json(checked(selected["validation_metrics"]))
        contract = read_json(checked(entry["model_contract"]))
        base = {key: entry[key] for key in ("run_id", "dataset_id", "method", "seed", "fold")}
        records.append(
            {
                **base,
                "split": "validation",
                **{
                    key: value["value"]
                    for key, value in details["metrics"].items()
                    if isinstance(value, dict) and "value" in value
                },
                **metric["efficiency"],
                "parameter_count": contract.get("parameter_count"),
                "best_epoch_1based": selected["best_epoch"] + 1
                if selected["best_epoch"] is not None
                else None,
                "epochs": len(read_json(checked(selected["history"]))),
                "metrics": selected["validation_metrics"],
                "original_training_telemetry_available": metric["efficiency"]["train_seconds"] is not None,
            }
        )
        for horizon, values in details["metrics"]["by_horizon"].items():
            horizons.append(
                {
                    **base,
                    "horizon": int(horizon),
                    **{key: values[key]["value"] for key in ("rmse", "mae", "smape")},
                }
            )
        for name, values in details["metrics"]["by_series"].items():
            series.append(
                {**base, "series": name, **{key: values[key]["value"] for key in ("rmse", "mae", "smape")}}
            )
        registry.append(
            {
                "model_id": entry["run_id"],
                "dataset_id": entry["dataset_id"],
                "fold": entry["fold"],
                "seed": entry["seed"],
                "training_implementation": entry["method"],
                "serving_backend": "numpy_cpu_portable"
                if entry["method"] in IMPLEMENTATIONS
                else "causal_history_baseline",
                "family": "rnn" if entry["method"] in IMPLEMENTATIONS else "classical",
                "lifecycle": "trained_validation_selected"
                if entry["method"] in IMPLEMENTATIONS
                else "fixed_causal_baseline_validated",
                "inference_ready": True,
                "checkpoint": selected["checkpoint"],
                "checkpoint_metadata": selected["checkpoint_metadata"],
                "model_contract": entry["model_contract"],
                "config": entry["config"],
                "validation_metrics": selected["validation_metrics"],
                "comparison_group_sha256": entry["comparison_group_sha256"],
                "test_evaluation_executed": False,
            }
        )
    if len(records) != 132:
        raise ValueError("Incomplete validation experiment matrix")
    return records, registry, horizons, series


def aggregate_rows(records, extra_keys=()):
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["dataset_id"], row["method"], row["fold"], *[row[k] for k in extra_keys])].append(row)
    output = []
    for keys, rows in grouped.items():
        expected = {17, 42, 73} if keys[1] in IMPLEMENTATIONS else {42}
        if {r["seed"] for r in rows} != expected:
            raise ValueError("Missing seed in validation aggregation")
        fields = (
            ("rmse", "mae", "smape")
            if extra_keys
            else (
                "rmse",
                "macro_series_rmse",
                "mae",
                "smape",
                "train_seconds",
                "inference_p50_ms",
                "inference_p95_ms",
                "peak_ram_bytes",
                "peak_vram_bytes",
                "checkpoint_bytes",
                "parameter_count",
            )
        )
        for field in fields:
            values = [row[field] for row in rows if row.get(field) is not None]
            output.append(
                {
                    "dataset_id": keys[0],
                    "method": keys[1],
                    "fold": keys[2],
                    **dict(zip(extra_keys, keys[3:], strict=True)),
                    "metric": field,
                    "n": len(values),
                    "mean": float(np.mean(values)) if values else None,
                    "sample_std": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                    "undefined_reason": None if values else "Not applicable to a parameter-free baseline",
                }
            )
    return output


def figures(release, records, aggregate, horizon_summary, series):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.hashsalt": "rnn_phase28_v1",
        }
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    outputs = []

    def save(fig, name, rect=None):
        fig.tight_layout(rect=rect)
        for extension in ("png", "svg"):
            path = FIGURES / f"{name}.{extension}"
            fig.savefig(
                path,
                dpi=300,
                metadata={"Date": None} if extension == "svg" else {"Software": "AI V3 Phase28"},
            )
            outputs.append(ref(path))
        plt.close(fig)

    def value(dataset, method, metric, fold=None):
        return next(
            row
            for row in aggregate
            if row["dataset_id"] == dataset
            and row["method"] == method
            and row["fold"] == fold
            and row["metric"] == metric
        )

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 8.6))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        hs = sorted({row["horizon"] for row in horizon_summary if row["dataset_id"] == dataset})
        for method in METHODS:
            values = [
                next(
                    row
                    for row in horizon_summary
                    if row["dataset_id"] == dataset
                    and row["method"] == method
                    and row["fold"] is None
                    and row["horizon"] == h
                    and row["metric"] == "rmse"
                )
                for h in hs
            ]
            ax.errorbar(
                range(3),
                [r["mean"] for r in values],
                yerr=[r["sample_std"] or 0 for r in values],
                label=method,
                color=COLORS[method],
                marker="o",
                linestyle="--" if method not in IMPLEMENTATIONS else "-",
                capsize=3,
            )
        ax.set(
            title=LABELS[dataset] + " — main VALIDATION",
            xticks=range(3),
            xticklabels=[str(h) for h in hs],
            xlabel="Horizon (source periods)",
            ylabel="RMSE, log (" + UNITS[dataset] + ")",
            yscale="log",
        )
        ax.legend(fontsize=7, ncol=3)
    save(fig, "horizon_errors")

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 8.2))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        metric = "macro_series_rmse" if dataset == "ch4_bis_house_prices" else "rmse"
        for method in METHODS:
            rows = [value(dataset, method, metric, fold) for fold in (1, 2, 3)]
            ax.errorbar(
                [1, 2, 3],
                [r["mean"] for r in rows],
                yerr=[r["sample_std"] or 0 for r in rows],
                color=COLORS[method],
                marker="o",
                label=method,
                capsize=3,
                linestyle="--" if method not in IMPLEMENTATIONS else "-",
            )
        ax.set(
            title=LABELS[dataset] + " — rolling VALIDATION",
            xlabel="Expanding fold",
            xticks=[1, 2, 3],
            ylabel=metric + " (log)\n" + UNITS[dataset],
            yscale="log",
        )
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    save(fig, "rolling_validation", rect=(0, 0.065, 1, 1))

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 8.4))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        for method in METHODS:
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset
                and e["fold"] is None
                and e["method"] == method
                and e["seed"] == 42
            )
            selected = read_json(BASE / "runs" / entry["run_id"] / "selection.json")
            with gzip.open(checked(selected["validation_predictions"]), "rt", encoding="utf-8") as stream:
                saved = [json.loads(line) for line in stream]
            first_series = saved[0]["series"]
            saved = [r for r in saved if r["series"] == first_series][:120]
            times = np.asarray([r["target_times"][-1] for r in saved], dtype="datetime64[s]")
            if method == "scratch":
                ax.plot(
                    times, [r["target"][-1] for r in saved], color="#162C38", label="observed", linewidth=2
                )
            ax.plot(
                times,
                [r["prediction"][-1] for r in saved],
                color=COLORS[method],
                label=method,
                linestyle="--" if method not in IMPLEMENTATIONS else "-",
                alpha=0.8,
            )
        ax.set(title=LABELS[dataset] + " — largest horizon, seed42", ylabel=UNITS[dataset])
        ax.tick_params(axis="x", labelrotation=20, labelsize=7)
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    save(fig, "forecast_examples", rect=(0, 0.065, 1, 1))

    fig, axes = plt.subplots(3, 3, figsize=(12.6, 9.6))
    gradient_fig, gradient_axes = plt.subplots(3, 3, figsize=(12.6, 9.6))
    for row, dataset in enumerate(DATASETS):
        for col, method in enumerate(IMPLEMENTATIONS):
            entry = next(
                e
                for e in release["runs"]
                if e["dataset_id"] == dataset
                and e["fold"] is None
                and e["method"] == method
                and e["seed"] == 42
            )
            folder = BASE / "runs" / entry["run_id"]
            history = read_json(folder / "history.json")
            selected = read_json(folder / "selection.json")
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
            ax.axvline(selected["best_epoch"] + 1, color="#72777A", linestyle=":")
            ax.set(
                title=LABELS[dataset] + "/" + method,
                xlabel="Epoch",
                ylabel="Normalized MSE (log)",
                yscale="log",
            )
            ax.legend(fontsize=12)
            gradient = np.asarray(
                read_json(folder / "gradient_diagnostics.json")["input_gradient_rms_by_time_oldest_to_newest"]
            )
            ga = gradient_axes[row, col]
            if np.any(gradient > 0):
                ga.plot(
                    np.arange(1, len(gradient) + 1),
                    np.where(gradient > 0, gradient, np.nan),
                    color=COLORS[method],
                )
                ga.set_yscale("log")
            else:
                ga.text(0.5, 0.5, "All input gradients = 0", transform=ga.transAxes, ha="center")
            ga.set(
                title=LABELS[dataset] + "/" + method,
                xlabel="Time: oldest to newest",
                ylabel="Input gradient RMS (log)",
            )
            for panel in (ax, ga):
                panel.tick_params(labelsize=13)
                panel.title.set_size(15)
                panel.xaxis.label.set_size(14)
                panel.yaxis.label.set_size(14)
    save(fig, "learning_curves")
    save(gradient_fig, "train_gradient_by_time")

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 8.1))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        values = [value(dataset, method, "train_seconds") for method in IMPLEMENTATIONS]
        ax.bar(
            ["scratch\nCPU", "Keras/XLA\nGPU", "PyTorch/eager\nGPU"],
            [r["mean"] for r in values],
            color=[COLORS[m] for m in IMPLEMENTATIONS],
        )
        for i, row in enumerate(values):
            ax.text(i, row["mean"] * 1.05, f"{row['mean']:.1f}\nn={row['n']}", ha="center", fontsize=9)
        ax.set(title=LABELS[dataset] + " — main training", ylabel="Seconds (log)", yscale="log")
        ax.margins(y=0.25)
    save(fig, "train_time")

    rows = [
        r
        for r in series
        if r["dataset_id"] == "ch4_bis_house_prices"
        and r["fold"] is None
        and r["seed"] == 42
        and r["method"] in IMPLEMENTATIONS
    ]
    names = sorted({r["series"] for r in rows})
    matrix = [
        [
            next(r["rmse"] for r in rows if r["series"] == name and r["method"] == method)
            for method in IMPLEMENTATIONS
        ]
        for name in names
    ]
    fig, ax = plt.subplots(figsize=(6.4, 8.5))
    im = ax.imshow(matrix, aspect="auto", cmap="Blues", vmin=0)
    ax.set(
        yticks=range(len(names)),
        yticklabels=[name.split(".")[1] for name in names],
        xticks=range(3),
        xticklabels=IMPLEMENTATIONS,
        title="BIS per-economy VALIDATION RMSE — seed42",
        ylabel="Economy code (frozen alphabetical order)",
    )
    ax.tick_params(axis="y", labelsize=7)
    fig.colorbar(im, ax=ax, label="RMSE, index points")
    save(fig, "bis_per_series")
    return outputs


def manuscript(records, summary, horizon_summary, series):
    text = (ROOT / "report/sections/v3/ch04_rnn_theory.md").read_text(encoding="utf-8")
    text += (
        "\n\n**Ghi chú kiểm chứng export r2.** Model được train bằng framework đã khai báo; "
        "bản NumPy CPU được kiểm riêng với native CPU ở cùng ngưỡng rtol=1e-4, atol=1e-5. "
        "Đối chiếu GPU/cuDNN với CPU của Power/PyTorch seed17 vượt ngưỡng ở một đầu ra; "
        "lỗi gốc vẫn được lưu, không gọi là PASS. Lượt này được khôi phục từ đúng best checkpoint, "
        "không thêm optimizer update hoặc chọn lại epoch. Chi tiết nằm trong hồ sơ revision r2.\n\n"
        "Riêng lượt Power/PyTorch seed17 đã mất số đo cuối của process train trước khi lưu: "
        "train wall, peak RSS và VRAM gốc được để null và loại khỏi aggregate chi phí tương ứng. "
        "Các ô chi phí Power/PyTorch main dùng n=2; metric chất lượng vẫn đủ ba seed. "
        "Inference của lượt này được đo ở process khôi phục, không thay cho thời gian train.\n"
    )

    def value(dataset, method, metric, fold=None):
        return next(
            row
            for row in summary
            if row["dataset_id"] == dataset
            and row["method"] == method
            and row["fold"] == fold
            and row["metric"] == metric
        )

    def fmt(row, scale=1, digits=3):
        base = f"{row['mean'] / scale:.{digits}f}"
        result = base + (
            f" ± {row['sample_std'] / scale:.{digits}f}" if row["sample_std"] is not None else ""
        )
        return result + (f" (n={row['n']})" if row["n"] != 3 else "")

    text += (
        "\nKết quả chính cần lưu ý: trên Gold và BIS, cả ba cách hiện thực RNN đều có sai số "
        "main validation cao hơn last-value. Với Household Power, cả ba RNN có RMSE thấp hơn "
        "hai baseline. Do đó, mạng sâu hơn chưa đủ để bảo đảm dự báo tốt hơn một quy tắc đơn giản; "
        "kết luận phải gắn với từng miền và cấu hình đã khóa. Đây vẫn là validation, không phải "
        "bằng chứng TEST hay cơ sở để chọn lại hyperparameter sau thực nghiệm.\n"
    )

    text += "\n\n### 4.4.1. Kết quả tập validation chính\n\nCác số dưới là VALIDATION, chưa phải TEST. Ba seed17/42/73 của RNN dùng mean ± sample SD. Hai baseline xác định chỉ có một lượt mỗi view, không tạo SD giả.\n\n| Dataset | Triển khai | RMSE | MAE | sMAPE % | Macro-series RMSE |\n|---|---|---:|---:|---:|---:|\n"
    for dataset in DATASETS:
        for method in METHODS:
            text += f"| {LABELS[dataset]} | {method} | {fmt(value(dataset, method, 'rmse'))} | {fmt(value(dataset, method, 'mae'))} | {fmt(value(dataset, method, 'smape'))} | {fmt(value(dataset, method, 'macro_series_rmse'))} |\n"
    text += "\nĐơn vị RMSE/MAE lần lượt là USD/troy ounce, điểm chỉ số2010=100 và kW; không so độ lớn giữa dataset. Với Gold/Power chỉ một chuỗi, macro-series RMSE trùng RMSE. BIS dùng macro-series làm metric chính.\n\n"
    for dataset in DATASETS:
        primary = "macro_series_rmse" if dataset == "ch4_bis_house_prices" else "rmse"
        baseline_best = min(value(dataset, method, primary)["mean"] for method in METHODS[-2:])
        text += (
            f"{LABELS[dataset]}: metric chính trung bình scratch/Keras/PyTorch là "
            + ", ".join(f"{value(dataset, method, primary)['mean']:.3f}" for method in IMPLEMENTATIONS)
            + f"; baseline tốt hơn trong hai baseline có giá trị {baseline_best:.3f}. Đây là mô tả các cấu hình đã khóa, không dùng để chọn lại hyperparameter sau hàng đợi.\n\n"
        )
    text += "Mạng nhỏ không được bảo đảm vượt baseline. Train loss thấp cùng validation error lớn có thể phản ánh overfit hoặc dịch chuyển mức/đặc trưng theo thời gian. Với vàng, prefix train và validation thuộc những chế độ mức giá khác nhau; không được gọi khả năng bám một đoạn train là khả năng giao dịch tương lai.\n\n"
    text += "### 4.4.2. Sai số theo horizon và rolling fold\n\n| Dataset | Triển khai | Horizon | RMSE | MAE | sMAPE % |\n|---|---|---:|---:|---:|---:|\n"
    for dataset in DATASETS:
        for method in METHODS:
            hs = sorted({r["horizon"] for r in horizon_summary if r["dataset_id"] == dataset})
            for h in hs:

                def hv(metric, dataset=dataset, method=method, horizon=h):
                    return next(
                        r
                        for r in horizon_summary
                        if r["dataset_id"] == dataset
                        and r["method"] == method
                        and r["fold"] is None
                        and r["horizon"] == horizon
                        and r["metric"] == metric
                    )

                text += f"| {LABELS[dataset]} | {method} | {h} | {fmt(hv('rmse'))} | {fmt(hv('mae'))} | {fmt(hv('smape'))} |\n"
    text += "\n![Hình 4A.1. Main validation RMSE theo horizon; trục log và đơn vị riêng từng dataset. Error bar là sample SD ba seed, baseline một lượt không có SD.](../../../artifacts/figures/phase28/horizon_errors.png)\n\n"
    text += "| Dataset | Triển khai | Fold1 metric chính | Fold2 | Fold3 |\n|---|---|---:|---:|---:|\n"
    for dataset in DATASETS:
        primary = "macro_series_rmse" if dataset == "ch4_bis_house_prices" else "rmse"
        for method in METHODS:
            text += (
                f"| {LABELS[dataset]} | {method} | "
                + " | ".join(fmt(value(dataset, method, primary, fold)) for fold in (1, 2, 3))
                + " |\n"
            )
    text += "\n![Hình 4A.2. Rolling validation tách khỏi main; mỗi fold có scaler/prefix riêng. Không coi các fold chồng lịch là ba phép thử độc lập.](../../../artifacts/figures/phase28/rolling_validation.png)\n\n"
    text += "### 4.4.3. Ví dụ dự đoán và khác biệt giữa chuỗi\n\n![Hình 4A.3. Seed42, horizon lớn nhất, chuỗi đầu theo thứ tự ID và tối đa120 window validation đầu; chọn bằng quy tắc cố định, không chọn đoạn đẹp nhất.](../../../artifacts/figures/phase28/forecast_examples.png)\n\nĐường dự đoán đọc trực tiếp từ JSONL.GZ đã lưu, không forward model lần nữa. Các điểm là dự đoán từ nhiều origin liên tiếp, không phải một dự báo dài phát ra ở một ngày. BIS minh họa chuỗi đầu theo ID; bảng đầy đủ49 chuỗi nằm trong `tables/series.json`.\n\n![Hình 4A.4. BIS RMSE từng nền kinh tế, seed42, main validation; cùng thang màu cho ba implementation, thứ tự mã quốc gia cố định.](../../../artifacts/figures/phase28/bis_per_series.png)\n\n"
    text += "### 4.4.4. Quá trình học và gradient\n\n![Hình 4A.5. Train/validation MSE đã chuẩn hóa, trục log, seed42 main; vạch dọc là epoch được chọn bằng validation.](../../../artifacts/figures/phase28/learning_curves.png)\n\n![Hình 4A.6. Gradient RMS theo vị trí đầu vào của bốn TRAIN window cố định, seed42; trục log, giá trị0 không được vẽ thành epsilon giả.](../../../artifacts/figures/phase28/train_gradient_by_time.png)\n\nGradient và loss được mô tả theo phạm vi ví dụ đã đo. Không suy ra quan hệ nhân quả, không dùng tỷ số hai vị trí để chứng minh ưu thế LSTM khi chưa chạy Phase29. Lịch sử còn lưu norm trước clip và tỷ lệ batch bị clip từng epoch.\n\n"
    text += "### 4.4.5. Thời gian và bộ nhớ\n\n| Dataset | Triển khai / thiết bị | Train giây | Inference p50 ms | Peak RSS MiB | Allocator VRAM MiB | Checkpoint KiB |\n|---|---|---:|---:|---:|---:|---:|\n"
    for dataset in DATASETS:
        for method in IMPLEMENTATIONS:
            text += f"| {LABELS[dataset]} | {method} / {'CPU' if method == 'scratch' else 'GPU'} | {fmt(value(dataset, method, 'train_seconds'))} | {fmt(value(dataset, method, 'inference_p50_ms'))} | {fmt(value(dataset, method, 'peak_ram_bytes'), 1024**2, 1)} | {fmt(value(dataset, method, 'peak_vram_bytes'), 1024**2, 1)} | {fmt(value(dataset, method, 'checkpoint_bytes'), 1024, 2)} |\n"
    text += "\n![Hình 4A.7. Main train wall, mean ba seed; CPU/GPU và Keras XLA khác PyTorch eager. Không kết luận một framework luôn nhanh hơn.](../../../artifacts/figures/phase28/train_time.png)\n\nTrain wall gồm batch gather, validation và progress I/O, cả graph compile nếu nằm trong timer; không gồm import framework hoặc xây data view trước timer. Inference batch1 dùng5 warmup/30 lần, có transfer/layout và đồng bộ GPU, tách preprocessing. RSS là peak cả process, không phải phần tăng thêm của model; VRAM là framework allocator, không phải tổng VRAM máy. Baseline không có fitting tham số nên không xếp hạng bằng timer tạo một mảng đánh dấu.\n\n"
    text += "Máy: Intel i7-13620H (10 core/16 luồng host), RTX 5050 Laptop, driver 591.74, VRAM driver báo 8.151 MiB; WSL2 Python 3.11.17, PyTorch 2.14.1+cu130 và Keras 3.15.1/TensorFlow 2.21.0 trong hai env độc lập. Dtype float32, chính sách hai luồng tính toán CPU, source/environment/data hashes được pin. Metadata tại `artifacts/manifests/phase28/hardware_snapshot.json`. Timing trên một laptop và số epoch dừng sớm khác nhau không tách được mọi nguyên nhân chênh lệch.\n\n"
    text += "## 4.5. Triển khai RNN ngắn và bàn giao LSTM\n\nBa model seed42 của mỗi dataset được chuyển về canonical NPZ và chạy bằng NumPy CPU. Demo nhận ma trận feature gốc đã được tạo nhân quả, theo thứ tự cột và lookback cố định; chuẩn hóa một lần rồi đưa cùng tensor cho ba checkpoint. Job có prediction/horizon/unit, input/checkpoint/comparison hash, training implementation và actual backend/device. Việc nạp checkpoint train bằng Keras hoặc PyTorch không có nghĩa server đang chạy native engine đó.\n\nBa notebook tại `experiments/notebooks/v3/ch04_rnn/` dùng fixed TRAIN input và đọc metric validation đã lưu; không train hoặc mở TEST. Demo `scripts.demo_phase28 --dataset ch4_gold_pink_sheet` chạy qua wrapper WSL. API HTTP/tab React/Render thuộc Phase32–33; đây chưa phải deployment live.\n\nGiới hạn chính gồm snapshot revised, thiếu lịch công bố thật, dữ liệu ít/khác chế độ ở vàng, country encoding chỉ dùng được các nền kinh tế đã khai báo, power chỉ một hộ, matched train12.000 và không có calibration khoảng dự đoán. Không dùng đầu ra để đưa lời khuyên đầu tư hay khẳng định tổng quát hóa dân số.\n\nPhase28 khóa config, weights được chọn bằng validation và toàn bộ bằng chứng. Phase29 phải giữ cùng windows/scaler/budget để triển khai LSTM rồi mới mở một batch TEST chung cho cả hai họ. Không tự chạy lại TEST Ch2/Ch3/Ch5.\n\nNguồn kết quả: `artifacts/metrics/phase28/tables/`, `artifacts/manifests/phase28/`; provenance dữ liệu Phase23–25.\n"
    path = ROOT / "report/sections/v3/ch04_rnn.md"
    text = text.replace(
        "Main train wall, mean ba seed;",
        "Main train wall, mean trên số seed có số đo (3; riêng Power/PyTorch n=2);",
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seal", action="store_true", help="Pin existing derived output only after visual QA; never rerender"
    )
    args = parser.parse_args()
    if (BASE / "experiment_lock.json").exists():
        raise ValueError("Phase28 locked; do not regenerate report outputs")
    generation_path = BASE / "report_generation.json"
    if generation_path.exists():
        generation = read_json(generation_path)
        for record in [generation["manuscript"], *generation["figures"], *generation["tables"]]:
            checked(record)
        print(json.dumps({"status": "PASS", "mode": "sealed_read_only"}))
        return
    release = check_sources()
    records, registry, horizons, series = collect(release)
    summary, horizon_summary = aggregate_rows(records), aggregate_rows(horizons, ("horizon",))
    table_root = METRICS / "tables"
    table_refs = []
    for name, values in (
        ("runs", records),
        ("aggregate", summary),
        ("horizons", horizons),
        ("horizon_aggregate", horizon_summary),
        ("series", series),
    ):
        path = table_root / f"{name}.json"
        write_once(path, values)
        table_refs.append(ref(path))
    write_once(
        BASE / "trained_validation_registry.json",
        {
            "status": "trained_validation_only",
            "models": registry,
            "initialized_registry_unchanged": "artifacts/manifests/phase25/initialized_contract_registry.json",
            "test_evaluation_executed": False,
        },
    )
    main_entries = [e for e in release["runs"] if e["fold"] is None]
    write_once(
        BASE / "holdout_handoff.json",
        {
            "phase": 28,
            "next_phase": 29,
            "status": "RNN_validation_locked_pending_LSTM",
            "rnn_run_ids": [e["run_id"] for e in main_entries if e["method"] in IMPLEMENTATIONS],
            "baseline_run_ids": [e["run_id"] for e in main_entries if e["method"] not in IMPLEMENTATIONS],
            "selection_refs": [ref(BASE / "runs" / e["run_id"] / "selection.json") for e in main_entries],
            "test_evaluation_executed": False,
            "rule": "Joint RNN/LSTM TEST only after both families and evaluator/approved IDs locked; rolling checkpoints are development only",
        },
    )
    if args.seal:
        qa = read_json(BASE / "visual_qa.json")
        if qa["status"] != "PASS" or len(qa["figures"]) != 7:
            raise ValueError("Inspect all seven figures first")
        for record in qa["figures"]:
            checked({key: record[key] for key in ("path", "sha256")})
        plot_refs = [
            ref(FIGURES / f"{name}.{ext}")
            for name in (
                "horizon_errors",
                "rolling_validation",
                "forecast_examples",
                "learning_curves",
                "train_gradient_by_time",
                "train_time",
                "bis_per_series",
            )
            for ext in ("png", "svg")
        ]
        manuscript_path = ROOT / "report/sections/v3/ch04_rnn.md"
        if {r["path"] for r in qa["figures"]} != {r["path"] for r in plot_refs if r["path"].endswith(".png")}:
            raise ValueError("Visual QA figure set differs")
        write_once(
            generation_path,
            {
                "status": "PASS",
                "run_rows": len(records),
                "aggregate_rows": len(summary),
                "horizon_rows": len(horizons),
                "horizon_aggregate_rows": len(horizon_summary),
                "series_rows": len(series),
                "figures": plot_refs,
                "tables": table_refs,
                "manuscript": ref(manuscript_path),
                "source": "Saved validation metrics/predictions only; zero TEST evaluation",
                "test_evaluation_executed": False,
            },
        )
    else:
        plot_refs = figures(release, records, summary, horizon_summary, series)
        manuscript_path = manuscript(records, summary, horizon_summary, series)
        print(
            json.dumps(
                {
                    "status": "DRAFT_RENDERED",
                    "run_rows": len(records),
                    "figures": len(plot_refs) // 2,
                    "manuscript": str(manuscript_path),
                    "next": "Inspect figures; write visual_qa; then --seal",
                }
            )
        )


if __name__ == "__main__":
    main()
