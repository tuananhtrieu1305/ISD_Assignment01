# Dataset card — AAPL daily prices 2015–2025

## Nhận dạng và nguồn

- Dataset ID: `ch4_aapl`.
- Chương/bài toán: Chương 4, dự đoán `Close` phiên giao dịch kế tiếp bằng many-to-one RNN.
- Trang lịch sử: <https://finance.yahoo.com/quote/AAPL/history/>; workflow dùng `yfinance` (<https://github.com/ranaroussi/yfinance>).
- Truy cập registry: 2026-10-05. Citation keys `yahoofinanceaapl`, `yfinance2026`.
- License: không xác minh được open dataset license cho market data. Apache-2.0 của yfinance chỉ áp dụng cho software, không cấp quyền cho dữ liệu Yahoo.
- Local: `A06/datasets/stock/AAPL_2015_2025.csv`; 305,816 bytes; SHA-256 `2c8eef3c6a3836e2217bf3e99faaeec37d30e60298f7319e8f3748b71e5bd2b8`.

## Kích thước và schema

- 2,766 daily rows × 7 cột: `Date, Open, High, Low, Close, Adj Close, Volume`.
- Date range: 2015-01-02 đến 2025-12-31; không missing, duplicate date hoặc giá/volume không dương theo audit A06.
- Mô hình dùng 5 feature `Open, High, Low, Close, Volume`; không dùng `Adj Close`.
- Window 30 phiên tạo 2,736 supervised sequences.

## Split và phân bố target

- Chronological split: TRAIN 1,915 (2015-02-17…2022-09-22), VAL 411 (2022-09-23…2024-05-13), TEST 410 (2024-05-14…2025-12-31).
- Target Close ranges: TRAIN 22.585–182.010 USD; VAL 125.020–198.110 USD; TEST 172.420–286.190 USD.
- Sự dịch chuyển range giữa các giai đoạn là lý do phải có naive last-Close baseline và không dùng random split.

## Mẫu input/output

- Mẫu raw đầu: 2015-01-02, Open 27.8475, High 27.8600, Low 26.8375, Close 27.3325, Volume 212,818,400.
- Sequence mẫu đầu gồm 30 phiên kết thúc 2015-02-13 với Close 31.7700; output là Close 31.9575 USD ngày 2015-02-17.
- Trong DOCX chỉ hiển thị đầu/cuối sequence và sparkline, không in đủ 30 hàng.

## Preprocessing và baseline

- Feature StandardScaler fit trên flattened TRAIN windows; target StandardScaler fit trên TRAIN y.
- Metric inverse-transform về USD: MAE, RMSE, R².
- Baseline bắt buộc: `prediction = Close` cuối input window. Kết quả A06 hiện có cho thấy baseline tốt hơn cả Keras/PyTorch RNN trên TEST; kết quả này phải được giữ nguyên và phân tích.

## Nhận xét và giới hạn

- Một mã cổ phiếu, một giai đoạn và unadjusted Close không đủ cho kết luận đầu tư hoặc khả năng khái quát thị trường.
- Price level non-stationary khiến R² âm có thể xuất hiện khi model không theo kịp regime shift, dù loss validation giảm.
- Báo cáo và deployment phải ghi “không phải khuyến nghị đầu tư”; không phân phối lại toàn bộ snapshot ngoài phạm vi được phép.

## Bằng chứng local

- Preprocessing metadata: `A06/results/metrics/preprocessing_metadata.json`.
- Processed arrays: `A06/datasets/processed/stock_{train,val,test}.npz`.
- Metrics: `A06/results/metrics/{keras,pytorch}_stock_metrics.json`; predictions CSV trong `A06/results/predictions/`.
