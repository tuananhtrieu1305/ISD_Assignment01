# A06 — Report Build Summary

**Build date:** 2026-09-29  
**Status:** PASSED  
**Output:** `report/A06_Assignment_Report.docx`

## Build basis

The report was built only from the audited A06 artifacts. No model was retrained, no dataset was resplit, and no stored metric or prediction was changed for presentation purposes. The gate document was `report/A06_AUDIT_REPORT.md`, whose final status is **PASSED**.

The previous A05 report was inspected only as an academic-format reference. No A05 technical content was reused.

## Source notebooks

- `notebooks/01_RNN_Fundamentals.ipynb`
- `notebooks/02_Customer_Behavior_Data.ipynb`
- `notebooks/03_Stock_Data.ipynb`
- `notebooks/04_PyTorch_Customer_RNN.ipynb`
- `notebooks/05_PyTorch_Stock_RNN.ipynb`
- `notebooks/06_Keras_Customer_RNN.ipynb`
- `notebooks/07_Keras_Stock_RNN.ipynb`
- `notebooks/08_Framework_Comparison.ipynb`

All eight notebooks were previously clean-executed during the technical audit. The report consumes their current saved artifacts; it does not execute training.

## Metadata and metrics used

- `results/metrics/preprocessing_metadata.json`
- `results/metrics/pytorch_customer_metrics.json`
- `results/metrics/keras_customer_metrics.json`
- `results/metrics/pytorch_stock_metrics.json`
- `results/metrics/keras_stock_metrics.json`
- `results/metrics/framework_comparison.json`

Metric snapshot reproduced in the report:

| Experiment | Main TEST results |
|---|---|
| PyTorch Customer RNN | Accuracy 0.7582; Precision 0.1587; Recall 0.5722; F1 0.2485; ROC-AUC 0.7009 |
| Keras Customer SimpleRNN | Accuracy 0.7600; Precision 0.1594; Recall 0.5697; F1 0.2491; ROC-AUC 0.7005 |
| PyTorch Stock RNN | MAE 20.3393 USD; RMSE 23.5788 USD; R² -0.0269 |
| Keras Stock SimpleRNN | MAE 23.1947 USD; RMSE 27.8703 USD; R² -0.4347 |
| Naive last-Close baseline | MAE 2.6177 USD; RMSE 3.8789 USD; R² 0.9722 |

## Actual saved figures used

Customer EDA:

- `results/figures/customer_eda/monthly_activity.png`
- `results/figures/customer_eda/customer_distributions.png`
- `results/figures/customer_eda/inactive_week_example.png`
- `results/figures/customer_eda/prototype_label_balance.png`

Stock EDA:

- `results/figures/stock_eda/close_volume_history.png`
- `results/figures/stock_eda/close_moving_averages.png`
- `results/figures/stock_eda/daily_return_distribution.png`

PyTorch experiments:

- `results/figures/pytorch_customer/training_validation_loss.png`
- `results/figures/pytorch_customer/test_confusion_matrix.png`
- `results/figures/pytorch_customer/test_roc_curve.png`
- `results/figures/pytorch_stock/training_validation_loss.png`
- `results/figures/pytorch_stock/test_actual_vs_predicted.png`
- `results/figures/pytorch_stock/rnn_vs_naive_metrics.png`

Keras experiments:

- `results/figures/keras_customer/training_validation_loss.png`
- `results/figures/keras_customer/test_confusion_matrix.png`
- `results/figures/keras_customer/test_roc_curve.png`
- `results/figures/keras_stock/training_validation_loss.png`
- `results/figures/keras_stock/test_actual_vs_predicted.png`
- `results/figures/keras_stock/rnn_vs_naive_metrics.png`

Framework comparison:

- `results/figures/comparison/customer_metrics_comparison.png`
- `results/figures/comparison/customer_confusion_matrices.png`
- `results/figures/comparison/customer_roc_comparison.png`
- `results/figures/comparison/stock_metrics_comparison.png`
- `results/figures/comparison/stock_actual_vs_predicted.png`

The document also contains two report-native explanatory diagrams: RNN unrolling and chronological splitting. These are not experimental-result figures.

## Report sections

- Bìa
- Mục lục
- Danh mục hình
- Danh mục bảng
- I. Tổng quan
- II. Cơ sở lý thuyết về RNN
- III. Phân tích dữ liệu
- IV. Tiền xử lý và thiết kế thí nghiệm
- V. Thực nghiệm PyTorch
- VI. Thực nghiệm Keras
- VII. So sánh hai framework
- VIII. Hạn chế và hướng phát triển
- IX. Kết luận
- Tài liệu tham khảo

## Build and validation notes

- Build script: `report/build_a06_report.py`
- Final length: 33 A4 pages.
- Embedded images: 46 inline objects, comprising 24 saved result figures, 2 explanatory diagrams, and 20 readable report-table renderings.
- Headings: 10 level-1, 23 level-2, and 9 level-3 headings.
- The DOCX was reopened programmatically and its ZIP package was validated.
- Required sections, captions, tables, figures, and current metric values were validated by the build script.
- The final DOCX was rendered with `artifact-tool`; all 33 rendered pages were inspected visually.
- Accessibility audit: 0 high, 0 medium, 0 low findings.
- No placeholder text remains and no stale notebook screenshot was used where an original plot existed.

Final deliverable: `C:\DATA\assign\A06\report\A06_Assignment_Report.docx`
