"""Build the Vietnamese Chapter 4 evidence notebook from saved artifacts."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "term_paper" / "notebooks" / "ch4_rnn_framework_comparison.ipynb"


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
        markdown("""
# Chương 4 — Vanilla RNN: NumPy scratch, Keras và PyTorch

Notebook đọc lại artifact Phase 5, không huấn luyện lại và không dùng TEST để chọn cấu hình. Mục tiêu là kiểm tra provenance, tái tính metric, xác nhận ba framework dùng cùng sample, và trình bày failure result AAPL so với naive last-Close.
"""),
        code("""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from IPython.display import display, Image
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, average_precision_score, mean_absolute_error,
                             mean_squared_error, r2_score)

start = Path.cwd().resolve()
ROOT = next(path for path in (start, *start.parents) if (path / "term_paper").exists())
TERM = ROOT / "term_paper"
METRICS = TERM / "artifacts" / "metrics"
FIGURES = TERM / "artifacts" / "figures" / "ch4"
MANIFESTS = TERM / "artifacts" / "manifests" / "ch4"
print("Workspace:", ROOT)
"""),
        markdown("""
## 1. Protocol khóa trước thực nghiệm

- Vanilla RNN `tanh`, many-to-one, hidden size 32, 1 recurrent layer và 1 head.
- Customer: sequence 8×5, subset cố định 30.000/8.000/8.000 từ split A06; BCE có class weight.
- AAPL: sequence 30×5, toàn bộ 1.915/411/410; MSE trên training scale, metric inverse về USD.
- Adam, gradient clipping 1,0; learning rate 0,003 hoặc 0,001; chọn bằng VALIDATION.
- Seed 42, 52, 62. Threshold customer được chọn riêng trên VALIDATION; TEST chỉ đánh giá sau khi khóa.
"""),
        code("""
display(pd.read_csv(METRICS / "ch4_dataset_summary.csv"))
for dataset in ("ch4_online_retail_customer_week", "ch4_aapl_next_close"):
    metadata = json.loads((MANIFESTS / f"{dataset}_metadata.json").read_text(encoding="utf-8"))
    print(dataset, metadata["split_sizes"], metadata["date_ranges"], metadata["split_sha256"])
"""),
        markdown("## 2. Phân bố và trục thời gian"),
        code('display(Image(filename=str(FIGURES / "ch4_dataset_overview.png")))'),
        markdown("""
Customer-week mất cân bằng mạnh nên accuracy không đủ. AAPL có mức giá TEST cao hơn phần lớn TRAIN, tạo distribution shift rõ và khiến baseline bám giá gần nhất trở thành đối chứng bắt buộc.
"""),
        markdown("## 3. Tái tính metric từ prediction artifact"),
        code("""
comparison = pd.read_csv(METRICS / "ch4_framework_comparison.csv")
checks = []
for _, row in comparison.iterrows():
    frame = pd.read_csv(TERM / row["prediction_path"])
    if row.task == "binary":
        pred = (frame.score_or_prediction >= frame.threshold.iloc[0]).astype(int)
        values = {"f1": f1_score(frame.y_true, pred),
                  "roc_auc": roc_auc_score(frame.y_true, frame.score_or_prediction),
                  "pr_auc": average_precision_score(frame.y_true, frame.score_or_prediction)}
    else:
        values = {"mae": mean_absolute_error(frame.y_true, frame.score_or_prediction),
                  "rmse": mean_squared_error(frame.y_true, frame.score_or_prediction) ** 0.5,
                  "r2": r2_score(frame.y_true, frame.score_or_prediction)}
    delta = max(abs(values[name] - row[name]) for name in values)
    checks.append({"dataset": row.dataset_id, "framework": row.framework,
                   "seed": row.seed, "max_metric_delta": delta, "samples": len(frame)})
checks = pd.DataFrame(checks); display(checks)
assert checks.max_metric_delta.max() < 1e-12
print("PASS: metric của 18 run tái tính khớp prediction CSV.")
"""),
        markdown("## 4. Sample-key parity"),
        code("""
for dataset in comparison.dataset_id.unique():
    for seed in sorted(comparison.seed.unique()):
        selected = comparison[(comparison.dataset_id == dataset) & (comparison.seed == seed)]
        frames = [pd.read_csv(TERM / row.prediction_path)[["sample_key", "y_true"]].astype(str)
                  for _, row in selected.iterrows()]
        assert len(frames) == 3 and frames[0].reset_index(drop=True).equals(frames[1].reset_index(drop=True))
        assert frames[0].reset_index(drop=True).equals(frames[2].reset_index(drop=True))
print("PASS: NumPy, Keras và PyTorch dùng cùng TEST keys/dates/targets.")
"""),
        markdown("## 5. Customer next-week purchase"),
        code("""
summary = pd.read_csv(METRICS / "ch4_framework_summary.csv")
display(summary[summary.dataset_id == "ch4_online_retail_customer_week"])
display(Image(filename=str(FIGURES / "ch4_customer_metrics.png")))
display(Image(filename=str(FIGURES / "ch4_customer_roc_pr.png")))
display(Image(filename=str(FIGURES / "ch4_customer_confusion_matrices.png")))
"""),
        markdown("""
F1 và PR-AUC cho thấy khác biệt giữa ba implementation trong cùng protocol, còn confusion matrix làm rõ cái giá của recall: nhiều false positive hơn. Threshold đều được chọn trên VALIDATION, không tối ưu từ TEST.
"""),
        markdown("## 6. AAPL next-Close và baseline"),
        code("""
display(summary[summary.dataset_id == "ch4_aapl_next_close"])
stock = comparison[comparison.dataset_id == "ch4_aapl_next_close"]
display(stock[["framework", "seed", "mae", "rmse", "r2", "naive_mae", "naive_rmse", "naive_r2"]])
display(Image(filename=str(FIGURES / "ch4_stock_actual_vs_predicted.png")))
display(Image(filename=str(FIGURES / "ch4_stock_rmse_and_validation.png")))
assert (stock.rmse > stock.naive_rmse).all()
print("PASS: naive last-Close thắng mọi RNN run trong protocol này.")
"""),
        markdown("""
## 7. Đối chiếu A06 và kết luận kiểm chứng

Track matched hidden-32 không thay thế kết quả A06 hidden-64; bảng dưới giữ A06 như bằng chứng full-data/reference riêng. Không kết quả nào cho phép khuyến nghị đầu tư.
"""),
        code('display(pd.read_csv(METRICS / "ch4_a06_reference.csv"))'),
        markdown("""
1. Scratch RNN có forward nhiều bước, BPTT, clipping, Adam và save/load; gradient số được unit test.
2. Ba framework có đúng 1.249 trainable parameters và dùng cùng tensor/test key.
3. 18 prediction artifact tái tạo metric; customer có ROC/PR/confusion analysis.
4. Cả 9 RNN stock runs thua naive last-Close; đây là failure result cần giữ nguyên.
5. Phạm vi chỉ là hai dataset và Vanilla RNN; không suy rộng thành đánh giá mọi RNN/LSTM/GRU.
"""),
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
