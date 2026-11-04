"""Derive family-matched tables/figures from saved outputs; no model forward."""

import argparse
import csv
import gzip
import json
from collections import defaultdict

import numpy as np

from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, IMPLEMENTATIONS, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json

FIGURES = ROOT / "artifacts/figures/phase29"
LABELS = dict(zip(DATASETS, ("Gold", "BIS house index", "Household power"), strict=True))
UNITS = dict(zip(DATASETS, ("USD/troy ounce", "index 2010=100", "kW"), strict=True))
FIELDS = (
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
COLORS = dict(zip(IMPLEMENTATIONS, ("#236C9C", "#C1792C", "#7656A0"), strict=True))


def aggregate_rows(records, fields=FIELDS, extra_keys=()):
    groups = defaultdict(list)
    keys = ("dataset_id", "family", "method", "fold", "split", *extra_keys)
    for row in records:
        groups[tuple(row[k] for k in keys)].append(row)
    output = []
    for key, rows in groups.items():
        seeds = [r["seed"] for r in rows]
        expected = {42} if key[1] == "classical" else {17, 42, 73}
        if len(seeds) != len(set(seeds)) or set(seeds) != expected:
            raise ValueError("Missing/duplicate seed in family/split/fold group")
        for field in fields:
            values = [r[field] for r in rows if r.get(field) is not None]
            if not np.isfinite(values).all():
                raise ValueError("Nonfinite summary value")
            output.append(
                {
                    **dict(zip(keys, key, strict=True)),
                    "metric": field,
                    "n": len(values),
                    "mean": float(np.mean(values)) if values else None,
                    "sample_std": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                }
            )
    return output


def paired_deltas(records):
    groups = defaultdict(dict)
    for row in records:
        if row["family"] in {"rnn", "lstm"}:
            key = tuple(row[k] for k in ("dataset_id", "method", "fold", "split"))
            identity = (row["family"], row["seed"])
            if identity in groups[key]:
                raise ValueError("Duplicate paired member")
            groups[key][identity] = row
    output = []
    for key, group in groups.items():
        metric = "macro_series_rmse" if key[0] == "ch4_bis_house_prices" else "rmse"
        if set(group) != {(f, s) for f in ("rnn", "lstm") for s in (17, 42, 73)}:
            raise ValueError("Incomplete RNN/LSTM paired group")
        rnn = np.asarray([group["rnn", s][metric] for s in (17, 42, 73)])
        lstm = np.asarray([group["lstm", s][metric] for s in (17, 42, 73)])
        delta = rnn - lstm
        output.append(
            {
                **dict(zip(("dataset_id", "method", "fold", "split"), key, strict=True)),
                "metric": metric,
                "n": 3,
                "rnn_minus_lstm_mean": float(delta.mean()),
                "sample_std": float(delta.std(ddof=1)),
                "relative_improvement_percent": float(100 * delta.mean() / rnn.mean())
                if rnn.mean() != 0
                else None,
            }
        )
    return output


def test_result(dataset, run):
    audit = read_json(BASE / "test_verification.json")
    result = read_json(checked(audit["result_refs"][run]))
    if result["run_id"] != run or read_json(checked(result["metrics"]))["dataset_id"] != dataset:
        raise ValueError("Unified result identity mismatch")
    return result


def collect():
    records, horizons, series, selections = [], [], [], {}
    for phase in (28, 29):
        owner = ROOT / f"artifacts/manifests/phase{phase}"
        for entry in read_json(owner / "release.json")["runs"]:
            selected = read_json(owner / "runs" / entry["run_id"] / "selection.json")
            family = ("rnn" if phase == 28 else "lstm") if entry["method"] in IMPLEMENTATIONS else "classical"
            contract = read_json(checked(entry["model_contract"]))
            selections[entry["run_id"]] = (entry, selected, owner)
            sources = [("validation", selected["validation_metrics"], selected["details"])]
            if entry["fold"] is None:
                result = test_result(entry["dataset_id"], entry["run_id"])
                sources.append(("test", result["metrics"], result["details"]))
            for split, metric_ref, details_ref in sources:
                metric, details = read_json(checked(metric_ref)), read_json(checked(details_ref))
                base = {
                    **{k: entry[k] for k in ("run_id", "dataset_id", "method", "seed", "fold")},
                    "family": family,
                    "split": split,
                }
                records.append(
                    {
                        **base,
                        **{
                            k: v["value"]
                            for k, v in details["metrics"].items()
                            if isinstance(v, dict) and "value" in v
                        },
                        **metric["efficiency"],
                        "parameter_count": contract.get("parameter_count"),
                        "best_epoch_1based": selected["best_epoch"] + 1
                        if selected["best_epoch"] is not None
                        else None,
                        "metric_path": metric_ref["path"],
                        "metric_sha256": metric_ref["sha256"],
                    }
                )
                for name, values in details["metrics"]["by_horizon"].items():
                    horizons.append(
                        {
                            **base,
                            "horizon": int(name),
                            **{k: values[k]["value"] for k in ("rmse", "mae", "smape")},
                        }
                    )
                for name, values in details["metrics"]["by_series"].items():
                    series.append(
                        {**base, "series": name, **{k: values[k]["value"] for k in ("rmse", "mae", "smape")}}
                    )
    if len(records) != 300:
        raise ValueError("Expected240 validation +60 joint TEST records")
    return records, horizons, series, selections


def csv_once(name, rows):
    path = BASE / "tables" / (name + ".csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return ref(path)


def diagnostics_rows(selections):
    rows = []
    for run, (entry, _, owner) in selections.items():
        if entry["method"] not in IMPLEMENTATIONS:
            continue
        diagnostic = read_json(owner / "runs" / run / "gradient_diagnostics.json")
        if diagnostic["input_split"] != "train":
            raise ValueError("Gradient diagnostics must be TRAIN-only")
        history = read_json(owner / "runs" / run / "history.json")
        rows.append(
            {
                **{k: entry[k] for k in ("run_id", "dataset_id", "method", "seed", "fold")},
                "family": "lstm" if "_lstm_" in run else "rnn",
                "input_split": "train",
                "oldest_to_newest_ratio": diagnostic["oldest_to_newest_ratio"],
                "epoch_mean_clip_fraction": float(np.mean([r["gradient_clip_fraction"] for r in history])),
                "max_unclipped_gradient_norm": max(r["gradient_norm_max"] for r in history),
            }
        )
    if len(rows) != 216:
        raise ValueError("Expected216 neural TRAIN gradient diagnostics")
    return rows


def figures(records, aggregate, horizon_summary, series, selections):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.hashsalt": "phase29_rnn_lstm_1",
        }
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    outputs = []

    def save(fig, name, bottom=0.08):
        fig.tight_layout(rect=(0, bottom, 1, 1))
        for ext in ("png", "svg"):
            path = FIGURES / f"{name}.{ext}"
            if path.exists():
                raise ValueError("Do not overwrite a report figure without revision")
            fig.savefig(
                path, dpi=300, metadata={"Date": None} if ext == "svg" else {"Software": "AI V3 Phase29"}
            )
            outputs.append(ref(path))
        plt.close(fig)

    def find(rows, dataset, family, method, metric, split="test", fold=None, **extra):
        return next(
            r
            for r in rows
            if r["dataset_id"] == dataset
            and r["family"] == family
            and r["method"] == method
            and r["metric"] == metric
            and r["split"] == split
            and r["fold"] == fold
            and all(r[k] == v for k, v in extra.items())
        )

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.8))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        metric = "macro_series_rmse" if dataset == DATASETS[1] else "rmse"
        labels = []
        for i, (family, method) in enumerate((f, m) for f in ("rnn", "lstm") for m in IMPLEMENTATIONS):
            row = find(aggregate, dataset, family, method, metric)
            ax.errorbar(
                i,
                row["mean"],
                yerr=row["sample_std"],
                fmt="o" if family == "rnn" else "s",
                color=COLORS[method],
                capsize=4,
            )
            labels.append(f"{family.upper()}\n{method}")
        for method, style in (("last_value", "--"), ("seasonal_naive", ":")):
            ax.axhline(
                find(aggregate, dataset, "classical", method, metric)["mean"],
                color="#555F66",
                linestyle=style,
                label=method,
            )
        ax.set(
            title=LABELS[dataset] + " — joint TEST",
            xticks=range(6),
            xticklabels=labels,
            ylabel=metric + " (log)\n" + UNITS[dataset],
            yscale="log",
        )
        ax.legend(fontsize=7)
    save(fig, "main_test_comparison", bottom=0.01)

    for name, rows, rolling in (
        ("horizon_test", horizon_summary, False),
        ("rolling_validation", aggregate, True),
    ):
        fig, axes = plt.subplots(3, 1, figsize=(7.2, 9.2))
        for ax, dataset in zip(axes, DATASETS, strict=True):
            metric = "macro_series_rmse" if rolling and dataset == DATASETS[1] else "rmse"
            xs = [1, 2, 3] if rolling else sorted({r["horizon"] for r in rows if r["dataset_id"] == dataset})
            for family in ("rnn", "lstm", "classical"):
                for method in IMPLEMENTATIONS if family != "classical" else ("last_value", "seasonal_naive"):
                    ys = [
                        find(
                            rows,
                            dataset,
                            family,
                            method,
                            metric,
                            split="validation" if rolling else "test",
                            fold=x if rolling else None,
                            **({} if rolling else {"horizon": x}),
                        )
                        for x in xs
                    ]
                    ax.errorbar(
                        range(3),
                        [r["mean"] for r in ys],
                        yerr=[r["sample_std"] or 0 for r in ys],
                        color=COLORS.get(method, "#555F66" if method == "last_value" else "#33816D"),
                        marker="s" if family == "lstm" else "o",
                        capsize=2,
                        linestyle="-" if family == "lstm" else "--" if family == "rnn" else ":",
                        label=f"{family.upper()} {method}" if family != "classical" else method,
                    )
            ax.set(
                title=LABELS[dataset] + (" — rolling VALIDATION" if rolling else " — TEST by horizon"),
                xticks=range(3),
                xticklabels=xs,
                xlabel="Expanding fold" if rolling else "Horizon (source periods)",
                ylabel=metric + " (log)\n" + UNITS[dataset],
                yscale="log",
            )
        fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=4, fontsize=7)
        save(fig, name)

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.5))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        labels = []
        for i, (family, method) in enumerate((f, m) for f in ("rnn", "lstm") for m in IMPLEMENTATIONS):
            row = find(aggregate, dataset, family, method, "train_seconds", split="validation")
            ax.errorbar(i, row["mean"], yerr=row["sample_std"], fmt="o", color=COLORS[method], capsize=3)
            labels.append(f"{family.upper()}\n{method}\nn={row['n']}")
        ax.set(
            title=LABELS[dataset] + " — main training, not TEST timing",
            ylabel="Train wall seconds (log)",
            xticks=range(6),
            xticklabels=labels,
            yscale="log",
        )
    save(fig, "training_cost", bottom=0.01)

    fig, axes = plt.subplots(3, 3, figsize=(8.2, 8.0))
    for row_axes, dataset in zip(axes, DATASETS, strict=True):
        run = next(
            k
            for k, (e, _, _) in selections.items()
            if e["dataset_id"] == dataset
            and e["fold"] is None
            and e["method"] == "scratch"
            and e["seed"] == 42
            and "_lstm_" in k
        )
        diagnostic = read_json(BASE / "runs" / run / "gradient_diagnostics.json")
        for i, ax in enumerate(row_axes):
            for gate, color in (("input", "#236C9C"), ("forget", "#C1792C"), ("output", "#7656A0")):
                y = diagnostic["layers"][i]["gates"][gate]["mean_by_time"]
                ax.plot(range(len(y)), y, label=gate, color=color)
            ax.set(
                title=f"{LABELS[dataset]} / layer{i + 1}",
                ylim=(0, 1),
                xlabel="Step in TRAIN window",
                ylabel="Mean gate value",
            )
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center", ncol=3)
    save(fig, "lstm_gate_profiles", bottom=0.06)

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.5))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        for family in ("rnn", "lstm"):
            run = next(
                k
                for k, (e, _, _) in selections.items()
                if e["dataset_id"] == dataset
                and e["fold"] is None
                and e["method"] == "scratch"
                and e["seed"] == 42
                and ("_lstm_" in k) == (family == "lstm")
            )
            _, _, owner = selections[run]
            diagnostic = read_json(owner / "runs" / run / "gradient_diagnostics.json")
            values = diagnostic["input_gradient_rms_by_time_oldest_to_newest"]
            ax.plot(
                range(len(values)),
                np.maximum(values, 1e-30),
                label=family.upper(),
                linestyle="--" if family == "rnn" else "-",
            )
        ax.set(
            title=LABELS[dataset] + " — first4 TRAIN windows / scratch seed42",
            xlabel="Time step, oldest to newest",
            ylabel="Input gradient RMS (log)",
            yscale="log",
        )
        ax.legend()
    save(fig, "train_gradient_profiles", bottom=0.01)

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.5))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        for family in ("rnn", "lstm"):
            for method in IMPLEMENTATIONS:
                run = next(
                    k
                    for k, (e, _, _) in selections.items()
                    if e["dataset_id"] == dataset
                    and e["fold"] is None
                    and e["method"] == method
                    and e["seed"] == 42
                    and ("_lstm_" in k) == (family == "lstm")
                )
                _, selected, _ = selections[run]
                history = read_json(checked(selected["history"]))
                ax.plot(
                    range(1, len(history) + 1),
                    [r["validation_loss"] for r in history],
                    color=COLORS[method],
                    linestyle="-" if family == "lstm" else "--",
                    label=f"{family.upper()} {method}",
                )
        ax.set(
            title=LABELS[dataset] + " — main seed42",
            xlabel="Epoch",
            ylabel="Normalized validation MSE (log)",
            yscale="log",
        )
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=8)
    save(fig, "learning_curves")

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.5))
    for ax, dataset in zip(axes, DATASETS, strict=True):
        for family in ("rnn", "lstm"):
            run = next(
                k
                for k, (e, _, _) in selections.items()
                if e["dataset_id"] == dataset
                and e["fold"] is None
                and e["method"] == "scratch"
                and e["seed"] == 42
                and ("_lstm_" in k) == (family == "lstm")
            )
            result = test_result(dataset, run)
            with gzip.open(checked(result["predictions"]), "rt", encoding="utf-8") as stream:
                rows = [json.loads(line) for line in stream]
            chosen = rows[0]["series"]
            rows = [r for r in rows if r["series"] == chosen]
            stride = max(1, len(rows) // 500)
            indexes = np.arange(0, len(rows), stride)
            if family == "rnn":
                ax.plot(indexes, [rows[i]["target"][0] for i in indexes], color="#333333", label="Observed")
            ax.plot(
                indexes,
                [rows[i]["prediction"][0] for i in indexes],
                linestyle="--" if family == "rnn" else "-",
                label=family.upper(),
                alpha=0.8,
            )
        ax.set(
            title=f"{LABELS[dataset]} / {chosen} / nearest horizon / scratch seed42",
            xlabel="Chronological TEST window index (display subsampled if >500)",
            ylabel=UNITS[dataset],
        )
        ax.legend(ncol=3, fontsize=8)
    save(fig, "saved_test_forecasts", bottom=0.01)

    # By-country quality uses all saved BIS TEST output, never an extra forward.
    summary = aggregate_rows(
        [r for r in series if r["dataset_id"] == DATASETS[1] and r["split"] == "test"],
        fields=("rmse",),
        extra_keys=("series",),
    )
    countries = sorted({r["series"] for r in summary})
    pairs = [(f, m) for f in ("rnn", "lstm") for m in IMPLEMENTATIONS]
    values = np.asarray(
        [
            [
                next(r["mean"] for r in summary if r["series"] == c and r["family"] == f and r["method"] == m)
                for f, m in pairs
            ]
            for c in countries
        ]
    )
    fig, ax = plt.subplots(figsize=(7.2, 11.5))
    image = ax.imshow(np.log10(np.maximum(values, 1e-12)), aspect="auto", cmap="viridis")
    ax.set(
        yticks=range(len(countries)),
        yticklabels=countries,
        xticks=range(6),
        xticklabels=[f"{f.upper()}\n{m}" for f, m in pairs],
        title="BIS TEST — country RMSE, mean across3 seeds",
    )
    ax.tick_params(axis="y", labelsize=6)
    fig.colorbar(image, ax=ax, label="log10(RMSE in index points)", pad=0.02)
    save(fig, "bis_country_errors", bottom=0.01)
    return outputs


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    path = BASE / "report_statistics.json"
    if path.exists():
        result = read_json(path)
        for record in result["tables"] + result["figures"]:
            checked(record)
        print({"status": "PASS", "mode": "reused_verified"})
        return
    if read_json(BASE / "test_verification.json")["status"] != "PASS":
        raise ValueError("Saved TEST audit required before final statistics")
    records, horizons, series, selections = collect()
    aggregate = aggregate_rows(records)
    horizon_summary = aggregate_rows(horizons, fields=("rmse", "mae", "smape"), extra_keys=("horizon",))
    delta = paired_deltas(records)
    diagnostics = diagnostics_rows(selections)
    tables = [
        csv_once(name, rows)
        for name, rows in (
            ("runs", records),
            ("aggregate", aggregate),
            ("horizons", horizons),
            ("horizon_aggregate", horizon_summary),
            ("series", series),
            ("paired_deltas", delta),
            ("train_diagnostics", diagnostics),
        )
    ]
    outputs = figures(records, aggregate, horizon_summary, series, selections)
    result = {
        "phase": 29,
        "status": "PASS",
        "run_rows": len(records),
        "aggregate_rows": len(aggregate),
        "horizon_rows": len(horizons),
        "horizon_aggregate_rows": len(horizon_summary),
        "series_rows": len(series),
        "paired_groups": len(delta),
        "tables": tables,
        "figures": outputs,
        "new_test_forward_executed": False,
        "cost_scope": "main/rolling validation training cost; TEST copies are not additional costs",
    }
    write_once(path, result)
    print(json.dumps({k: v for k, v in result.items() if k not in {"tables", "figures"}}, indent=2))


if __name__ == "__main__":
    main()
