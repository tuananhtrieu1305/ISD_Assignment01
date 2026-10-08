# Dataset card — UCI Online Retail II

## Nhận dạng và nguồn

- Dataset ID: `ch4_online_retail_ii`.
- Chương/bài toán: Chương 4, dự đoán khách hàng có mua ở tuần kế tiếp bằng many-to-one RNN.
- Nguồn: <https://archive.ics.uci.edu/dataset/502/online+retail+ii>, DOI `10.24432/C5CG6D`.
- Truy cập: 2026-10-05. Citation key: `chen2012onlineretailii`.
- License: CC BY 4.0 theo record UCI.
- Local: `A06/datasets/customer/online_retail_II.xlsx`; 45,622,278 bytes; SHA-256 `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.

## Kích thước raw và làm sạch

- 1,067,371 transaction lines, 8 cột, 2 sheets: 525,461 hàng (2009–2010) và 541,910 hàng (2010–2011).
- Sau chuẩn hóa/cleaning: 779,425 hàng, 36,969 invoices, 5,878 customers; date range 2009-12-01 đến 2011-12-09.
- Audit loại 34,335 exact duplicates; 243,007 dòng thiếu/invalid CustomerID; cancellations, quantity/price không dương theo rule đã khóa.

## Biểu diễn sequence và phân bố

- Mỗi customer-week có 5 feature: `total_spent`, `total_quantity`, `order_count`, `unique_products`, `active_flag`.
- Input gồm 8 tuần; output là `active_flag` tuần liền sau.
- 350,864 sequence samples: TRAIN 247,458; VAL 50,354; TEST 53,052.
- Positive rate: TRAIN 6.568% (16,252); VAL 4.887% (2,461); TEST 6.987% (3,707). Dữ liệu mất cân bằng mạnh.

## Mẫu input/output

- Mẫu biểu diễn: ma trận `8×5` của một customer đã ẩn ID; các tuần không hoạt động được điền vector 0 trước scaling.
- Mẫu key/output thực tế trong TEST: `CustomerID=*****`, `target_week=2011-09-26`, `true_label=0`.
- Prediction artifact PyTorch hiện có cho mẫu đầu: probability 0.3066, predicted label 0 ở threshold 0.5; đây là output mô hình, không phải nhãn nguồn.

## Split và leakage control

- Split theo `target_week`, không random; TRAIN kết thúc 2011-07-11, VAL 2011-07-18…2011-09-19, TEST 2011-09-26…2011-11-28.
- Validation/TEST input chỉ dùng history có sẵn trước target week.
- StandardScaler fit flattened TRAIN X; class weight chỉ tính từ TRAIN y.

## Nhận xét và giới hạn

- Dữ liệu giao dịch thực tế có missing CustomerID và cancellations đáng kể; cleaning thay đổi population được mô hình hóa.
- Một khách hàng sinh nhiều windows, nên samples không độc lập; split thời gian giúp kiểm soát leakage nhưng không biến đây thành cohort study.
- Precision/recall/PR-AUC quan trọng hơn accuracy; cần giải thích false positive do class weighting.

## Bằng chứng local

- Preprocessing metadata: `A06/results/metrics/preprocessing_metadata.json`.
- Processed arrays: `A06/datasets/processed/customer_{train,val,test}.npz`.
- Framework artifacts: `A06/results/metrics/{keras,pytorch}_customer_metrics.json` và prediction CSV tương ứng.
