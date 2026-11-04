# A06 — Báo cáo kiểm toán toàn bộ dự án

**Ngày kiểm toán:** 2026-09-27  
**Phạm vi:** `PROJECT_SPEC.md`, `CURRENT_STATE.md`, 8 notebooks, toàn bộ `src/`, `tests/`, processed artifacts, preprocessing metadata, metrics, predictions, saved models và figures.  
**Mục tiêu:** kiểm tra correctness, data leakage, fairness, coverage, chất lượng notebook, khả năng thực thi và tính nhất quán artifact; không thiết kế lại thí nghiệm.

## 1. Tóm tắt kết quả

- Không phát hiện data leakage.
- Không phát hiện khác biệt dữ liệu đầu vào giữa PyTorch và Keras.
- Cả 8 notebooks chạy lại thành công theo thứ tự từ output trống, mỗi notebook dùng một kernel mới.
- `pytest`: **50 passed, 0 failed**.
- Bốn saved models tải lại thành công và tái tạo prediction hiện hành trong sai số floating-point/serialization dự kiến; nhãn phân loại tại threshold 0.5 khớp tuyệt đối.
- Metrics tái tính trực tiếp từ prediction CSV khớp metrics JSON.
- Tất cả 27 PNG được đọc lại, kiểm tra không rỗng và kiểm tra trực quan.
- Không cần thay đổi protocol, pipeline, kiến trúc Vanilla RNN hoặc dữ liệu.
- Metrics dự báo sau lần chạy sạch không đổi. Chỉ thời gian huấn luyện thay đổi theo runtime của lần audit và đã được ghi lại trong artifact mới.

## 2. Environment verified

Environment verifier được chạy lại bằng interpreter khóa:

- Conda environment: `rnn312`
- Interpreter: `C:\Users\anhca\anaconda3\envs\rnn312\python.exe`
- Python: `3.12.14`
- PyTorch: `2.14.0`, CPU; CUDA không khả dụng
- TensorFlow: `2.21.0`, CPU
- Keras: `3.15.1`
- Tất cả direct package imports: PASS
- `python -m compileall -q src tests`: PASS
- `python -m pip check`: `No broken requirements found`

TensorFlow phát cảnh báo runtime về CPU/native Windows và một thuộc tính `tf.data` không được binary hiện tại nhận biết. TensorFlow nói rõ thuộc tính đó được bỏ qua; các notebook Keras vẫn hoàn tất, lưu model, tải lại model và tái tạo predictions. Đây không phải lỗi correctness.

## 3. Datasets verified

### Customer — UCI Online Retail II

- Raw file: `datasets/customer/online_retail_II.xlsx`
- SHA-256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- Hai sheets: `Year 2009-2010` và `Year 2010-2011`
- Tổng raw rows: `1,067,371`
- Workbook vẫn giữ nguyên; normalization chỉ diễn ra trong DataFrame.
- Modeling cleaning còn `779,425` transaction lines, `5,878` customers và `36,969` invoices.

### Stock — locked AAPL snapshot

- Raw file: `datasets/stock/AAPL_2015_2025.csv`
- SHA-256: `2c8eef3c6a3836e2217bf3e99faaeec37d30e60298f7319e8f3748b71e5bd2b8`
- Rows: `2,766`
- Actual trading range: `2015-01-02` đến `2025-12-31`
- Không missing value, duplicate date hoặc sai thứ tự thời gian.
- Không notebook nào redownload dữ liệu.

Các raw hashes vẫn khớp contract sau toàn bộ lần chạy audit.

## 4. Notebook execution status

Trước khi chạy, output của cả 8 notebooks được xóa. Sau đó notebooks được thực thi tuần tự bằng `nbconvert --execute --inplace`, timeout 1,800 giây cho mỗi notebook và kernel mới cho mỗi lần gọi.

| Notebook | Code cells | Kết quả | Error outputs |
|---|---:|---|---:|
| `01_RNN_Fundamentals.ipynb` | 10/10 | PASS | 0 |
| `02_Customer_Behavior_Data.ipynb` | 14/14 | PASS | 0 |
| `03_Stock_Data.ipynb` | 9/9 | PASS | 0 |
| `04_PyTorch_Customer_RNN.ipynb` | 11/11 | PASS | 0 |
| `05_PyTorch_Stock_RNN.ipynb` | 13/13 | PASS | 0 |
| `06_Keras_Customer_RNN.ipynb` | 11/11 | PASS | 0 |
| `07_Keras_Stock_RNN.ipynb` | 12/12 | PASS | 0 |
| `08_Framework_Comparison.ipynb` | 11/11 | PASS | 0 |

Tổng cộng: **91/91 code cells** có execution count liên tục trong từng notebook; không có stale error output.

## 5. Pytest status

Lệnh cuối cùng sau khi tái sinh toàn bộ artifact:

```text
..................................................                       [100%]
50 passed in 16.28s
```

Không có test bị bỏ qua hoặc lỗi bị che giấu.

## 6. Leakage audit

Kiểm toán không chỉ đọc metadata. Customer windows được inverse-transform rồi đối chiếu exhaustive với weekly aggregates dựng lại từ raw workbook; stock windows được đối chiếu với từng dòng raw CSV theo target date. Sai số feature inverse-transform duy nhất là round-off do lưu `float32`; label/target timestamp alignment khớp.

| Yêu cầu | Bằng chứng kiểm toán | Kết quả |
|---|---|---|
| Customer dùng đúng 8 tuần trước | Tất cả `350,864` samples được đối chiếu với tuần `t-8 ... t-1`; mỗi bước cách 7 ngày | PASS |
| Customer `y` là tuần kế tiếp | `y` được đối chiếu với `active_flag` của đúng customer tại target week `t` | PASS |
| Stock dùng đúng 30 trading days trước | Tất cả `2,736` samples được đối chiếu với raw rows `[target_position-30:target_position]` | PASS |
| Stock `y` là trading day kế tiếp | `y` khớp raw `Close` tại target position; naive khớp `Close` tại position trước đó | PASS |
| Target timestamps chronological | Customer non-decreasing theo target week; stock strictly increasing theo target date | PASS |
| Split ranges không overlap | Các boundary bên dưới thỏa `TRAIN max < VAL min < TEST min` | PASS |
| Feature scaler TRAIN-only | Customer scaler thấy `247,458 × 8 = 1,979,664` rows; stock scaler thấy `1,915 × 30 = 57,450` rows; mean/scale tái tính từ raw TRAIN windows khớp | PASS |
| Target scaler TRAIN-only | Stock target scaler thấy đúng `1,915` TRAIN targets; mean/scale tái tính từ raw TRAIN `y` khớp | PASS |
| Class weight TRAIN-only | `231,206 / 16,252 = 14.226310607925178`; khớp metadata và cả hai notebooks | PASS |
| TEST không dùng cho early stopping | PyTorch nhận riêng validation loader; Keras callbacks monitor `val_loss`; TEST chỉ được dự đoán sau model selection | PASS |
| Model selection dùng validation | PyTorch checkpoint và Keras `EarlyStopping`/`ModelCheckpoint` đều chọn theo validation loss | PASS |
| Không có future-derived aggregate | Mỗi customer feature row khớp aggregate của đúng tuần lịch sử; target-week aggregate không xuất hiện trong input | PASS |

### Chronological target ranges

| Task | TRAIN | Validation | TEST |
|---|---|---|---|
| Customer | 2010-02-01 — 2011-07-11 | 2011-07-18 — 2011-09-19 | 2011-09-26 — 2011-11-28 |
| Stock | 2015-02-17 — 2022-09-22 | 2022-09-23 — 2024-05-13 | 2024-05-14 — 2025-12-31 |

Validation/TEST sequences được phép dùng lịch sử đã biết trước target boundary; split assignment vẫn dựa hoàn toàn trên target timestamp, phù hợp `PROJECT_SPEC.md`.

## 7. PyTorch/Keras fairness audit

### Customer

- Cả hai frameworks đọc cùng ba artifacts `customer_train.npz`, `customer_val.npz`, `customer_test.npz` và kiểm tra cùng SHA-256 từ preprocessing metadata.
- Vì là cùng binary artifacts nên `X`, `y`, sample ordering, `customer_id` và `target_week` là đồng nhất.
- Hai prediction CSV có cùng `53,052` TEST rows; `CustomerID`, `target_week`, `true_label` khớp từng dòng.
- `CustomerID` chỉ là metadata, không nằm trong năm model features.
- Cả hai dùng threshold `0.5` và cùng TRAIN-derived class ratio.

### Stock

- Cả hai frameworks đọc cùng ba stock NPZ artifacts và cùng TRAIN-only target scaler.
- `X`, raw/scaled `y`, sample ordering và `target_date` là đồng nhất.
- Hai prediction CSV có cùng `410` TEST dates, `actual_close` và `naive_close` khớp từng dòng.
- Naive metrics giống tuyệt đối giữa hai frameworks: MAE `2.6177071920`, RMSE `3.8789281161`, R² `0.9722086869`.

Fairness conclusion: **PASS**.

## 8. Assignment coverage

| Requirement | Coverage |
|---|---|
| RNN concepts, equations và executable code | Notebook 01: sequence data, hidden state equations, manual NumPy pass, sharing/unrolling, PyTorch/Keras shape demos, BPTT, gradients, LSTM/GRU motivation |
| Customer temporal data understanding | Notebook 02: workbook validation, integrity/cancellation/cleaning audit, EDA, weekly aggregation, inactive weeks, label preview và leakage discussion |
| Stock data understanding | Notebook 03: integrity, OHLC/volume/returns/moving averages, window concept, chronological split, scaling, baseline và metrics |
| PyTorch customer | Notebook 04: Vanilla `nn.RNN`, validation early stopping, predictions, metrics, confusion matrix và ROC |
| PyTorch stock | Notebook 05: Vanilla `nn.RNN`, scaled MSE training, inverse scaling, naive comparison và chronological plots |
| Keras customer | Notebook 06: `SimpleRNN`, sigmoid/BCE, TRAIN-only weights, callbacks, predictions và plots |
| Keras stock | Notebook 07: `SimpleRNN`, linear Dense/MSE, inverse scaling, naive comparison và plots |
| Cross-framework interpretation | Notebook 08: artifact-only comparison, fairness checks, metric/confusion/ROC/probability analysis và conclusions |

Coverage conclusion: **PASS**.

## 9. Notebook quality audit

- Markdown chủ yếu bằng tiếng Việt; standard English technical terms được dùng đúng ngữ cảnh.
- Theory/prose nằm trong Markdown cells; executable logic nằm trong code cells.
- Không tìm thấy `TODO`, `FIXME`, placeholder, `Lorem ipsum` hoặc “your code here”.
- Không có output dạng dump lớn không cần thiết; stream output lớn nhất chỉ 8 dòng trong một cell.
- Tables dùng summary/head/targeted displays thay vì in toàn bộ dataset.
- Các plot đã lưu có title, trục và legend phù hợp với số series; 27/27 PNG có kích thước đọc được và không blank.
- Hình minh họa gradient trong Notebook 01 được kiểm tra riêng và coherent với phần vanishing/exploding gradient.
- Không có fabricated result: model metrics được tái tính từ prediction CSV và predictions được tái tạo từ saved models.
- Sau clean execution, code, output, metrics và figures không mâu thuẫn.

Quality conclusion: **PASS**.

## 10. Artifact consistency

- `preprocessing_metadata.json` khớp shapes, timestamp ranges, scaler statistics và artifact hashes.
- Sáu processed NPZ files và ba preprocessing scalers vẫn khớp metadata; notebooks 01–08 không tự ý tạo split mới.
- Bốn saved models tải lại thành công:
  - `models/pytorch/pytorch_customer_rnn_best.pt`
  - `models/pytorch/pytorch_stock_rnn_best.pt`
  - `models/keras/keras_customer_rnn_best.keras`
  - `models/keras/keras_stock_rnn_best.keras`
- Saved models tái tạo current prediction files. Những sai khác số học quan sát được chỉ ở mức round-off CPU/`float32`; threshold labels và reported metrics khớp.
- Bốn metrics JSON khớp current predictions.
- `framework_comparison.json` được Notebook 08 tái sinh sau các notebook model và lưu hashes của current metric/prediction sources.
- Comparison figures phản ánh current metrics; stock comparison tiếp tục cho thấy cả hai RNN không vượt naive baseline.
- `PROJECT_SPEC.md` và implementation không mâu thuẫn; không có protocol change.

## 11. Current model results sau clean execution

### Customer TEST

| Framework | Accuracy | Precision | Recall | F1 | ROC-AUC | Epochs | Best epoch | Duration (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PyTorch RNN | 0.7582 | 0.1587 | 0.5722 | 0.2485 | 0.7009 | 11 | 9 | 151.06 |
| Keras SimpleRNN | 0.7600 | 0.1594 | 0.5697 | 0.2491 | 0.7005 | 18 | 16 | 86.01 |

### Stock TEST

| Model | MAE (USD) | RMSE (USD) | R² | Epochs | Best epoch | Duration (s) |
|---|---:|---:|---:|---:|---:|---:|
| PyTorch RNN | 20.3393 | 23.5788 | -0.0269 | 14 | 9 | 5.61 |
| Keras SimpleRNN | 23.1947 | 27.8703 | -0.4347 | 30 | 30 | 21.47 |
| Naive last Close | 2.6177 | 3.8789 | 0.9722 | — | — | — |

Training duration là số đo mô tả của lần chạy CPU này, chịu ảnh hưởng bởi framework/runtime/kernel và không phải universal benchmark.

## 12. Issues discovered và exact fixes applied

### Correctness issues

- Không phát hiện leakage, split error, fairness error, model-selection error, stale metric hoặc fabricated result.
- Không có source code, data pipeline, protocol hay architecture fix nào cần áp dụng.

### Documentation/artifact refresh

- Tất cả notebook outputs được xóa rồi chạy lại để loại trừ stale state.
- Models, predictions, metrics và figures của Notebooks 04–08 được tái sinh bởi current code.
- `environment_verification.json/.md` được chạy lại ngày 2026-09-27.
- `CURRENT_STATE.md` được cập nhật với clean-run durations, audit evidence và đường dẫn báo cáo này.

## 13. Documented experimental limitations

- Môi trường hiện tại chỉ có CPU; duration không đại diện cho mọi máy.
- Mỗi baseline dùng một chronological split và một seed; kết quả không chứng minh khả năng tổng quát ở mọi giai đoạn.
- Customer target mất cân bằng mạnh, nên accuracy không đủ để đánh giá một mình.
- Stock price level non-stationary; hai Vanilla RNN hiện tại kém hơn persistence baseline trên TEST.
- Vanilla RNN có giới hạn long-term memory và vanishing-gradient; LSTM/GRU chỉ là hướng mở rộng, không được huấn luyện trong A06.

## Final artifact status

Raw data, processed data, preprocessing scalers, four trained models, four prediction CSVs, model metrics, comparison summary, 27 saved figures, eight executed notebooks và project documentation đều hiện hữu, đọc được và nhất quán với current code.

**PASSED**
