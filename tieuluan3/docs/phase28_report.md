# Biên bản nghiệm thu Phase28 — RNN validation-only

Nghiệm thu: **PASS**, ngày 18/10/2026. Trạng thái phát hành và SHA-256 cuối xem
`artifacts/manifests/phase28/checkpoint.json` và `experiment_lock.json`.
Phase28 chỉ hoàn thiện RNN; LSTM và TEST chung vẫn thuộc Phase29. Chưa tích hợp DOCX/UI/API live.

## Kết quả và phạm vi

- Đủ **132 selection**: 27 RNN main, 81 RNN rolling (3 fold), 24 baseline causal.
  Ba dataset Gold/BIS/Household Power, ba implementation scratch/Keras/PyTorch, seed17/42/73.
  Baseline last-value/seasonal-naive chỉ một lượt mỗi view, không tạo SD giả.
- Mỗi RNN có3 recurrent32 + Dense16/8/3, tức6 learnable layers. Số tham số:
  Gold6.035, BIS7.539, Power6.355. Trạng thái reset mỗi window; Torch bias_hh=0/frozen.
- Main matched train531/2.504/12.000, validation115/588/5.033. Lookback24/12/168;
  horizon1/3/6 tháng,1/2/4 quý,1/6/24 giờ. Giữ các scaler/split/canonical feature order đã khóa.
  Không materialize hoặc predict TEST windows; nhãn metric lấy giá trị float64 gốc.
- Scratch là NumPy CPU/manual BPTT; Keras là TensorFlow GPU graph/XLA; PyTorch GPU eager.
  Cùng initialization/batch schedule, batch32, tối đa40 epoch/patience6/min_delta1e-5,
  Adam canonical lr0,001/epsilon1e-7/global clip1. Không tuning sau khai báo.
- Auditor đã đọc **223.861 dòng prediction**, kiểm12 data view và1.334 artifact reference.
  Metric/horizon/series được tính lại từ file đã lưu, không forward model trên validation/TEST.
- **108/108 strict native-CPU receipts PASS**, cùng rtol1e-4/atol1e-5. Scratch là kiểm round-trip
  manual engine, không được gọi là một framework độc lập thứ tư.

## Kết quả chính trên main VALIDATION

Số RNN là mean3 seed; baseline xác định n=1. Không so độ lớn sai số giữa các đơn vị.

| Dataset / metric chính | Scratch | Keras | PyTorch | Last-value | Seasonal-naive |
|---|---:|---:|---:|---:|---:|
| Gold / RMSE USD/troy ounce |670,155 |670,155 |683,270 |103,054 |217,229 |
| BIS / macro-series RMSE, điểm chỉ số2010=100 |16,388 |16,407 |16,392 |8,929 |11,798 |
| Power / RMSE kW |0,673660 |0,674599 |0,677081 |1,026273 |0,953825 |

RNN chưa vượt last-value ở Gold/BIS nhưng thấp hơn cả hai baseline ở Power trong cấu hình này.
Kết quả âm được giữ nguyên. Ba seed/rolling folds chồng lịch không chứng minh ưu thế thống kê,
khả năng đầu tư hoặc tổng quát hóa mọi hộ gia đình. Bảng đầy đủ có sample SD, horizon và từng
chuỗi ở manuscript/JSON; không chọn lại cấu hình từ các kết quả này.

## Kiểm thử và bằng chứng

**309 test duy nhất PASS,0 skip/error/failure** trong6 XML nghiệm thu:

| XML | Số test |
|---|---:|
| rnn-tests.xml |39 |
| keras-final-tests.xml |1 |
| regression-tests.xml |263 |
| preservation-tests.xml |1 |
| report-tests.xml |3 |
| powershell-entrypoint-green-tests.xml |2 |

Không cộng trùng XML pretrain, test focused, RED hoặc các lần chạy lịch sử.
Coverage module RNN (dòng+nhánh) **90,2216%**, statement92,9674%, branch81,5217%;
nguồn `final_coverage.json`. Ruff PASS. Có tiny numerical BPTT, canonical Adam W/U moments,
optimizer resume, causal windows, synthetic crash-finalization E2E, CPU input guards,
metric round-trip và notebook execution.

Giữ/công khai4 warning sklearn của trusted bundle V2 (1.9.1 so với env1.9.0), cùng warning
TensorFlow sm_120/PTX/XLA Assert. Các host finite/shape/loss/gradient checks vẫn hoạt động.
CPU receipt process cố ý ẩn GPU; thông báo CUDA_ERROR_NO_DEVICE tại process đó không phải
thất bại GPU train hoặc fallback backend.

## Sai lệch và lỗi đã xử lý có bằng chứng

1. Trước khai báo: index main không chứa một số origin hợp lệ ở rolling fold2/3. WindowData
   phase28.1 dựng lại đúng frozen ID/calendar, thêm Gold5/BIS98/Power23 ID mỗi fold.
   Không sửa split/index/scaler gốc; test đối chiếu primitive và calendar/causality PASS.
2. Trước khai báo: Keras XLA qua probe/parity/resume, giữ probe graph cũ và
   `performance_revision_xla.json`. Không đổi kiến trúc/loss/Adam/backend để tăng tốc.
3. Sau90 selection: Power/PyTorch seed17 đã train11 epoch nhưng GPU/cuDNN→NumPy CPU lệch
   tối đa2,5168e-5 ở4 TRAIN window, vượt ngưỡng tại1/12 đầu ra. Native CPU khớp NumPy,
   GPU unfused cũng khớp. Người dùng đồng ý **r2** kiểm export với native CPU, giữ ngưỡng gốc
   và cả FAIL GPU/CPU. Khôi phục từ đúng best epoch5, không thêm optimizer update hoặc
   chọn lại epoch. Checkpoint SHA-256 vẫn
   `e3437f37fab6f26196f9a7d72601d4de29a1518a96f9143ed9167316bc054e82`.
4. Process lỗi mất số đo train wall/RAM/VRAM cuối. Ba field đó là **null** trong recovery
   schema riêng của duy nhất lượt này; loại khỏi aggregate chi phí (Power/PyTorch main n=2).
   Không thay bằng0, snapshot elapsed35,789 giây hoặc peak của process recovery.
   Quality vẫn n=3; inference seed17 được đo ở process recovery và được ghi rõ.
5. Sau132 selection, bộ chờ tự động dừng bởi lỗi PowerShell Split-Path trong finish/check.
   Đã sửa root resolution và có2 test RED→GREEN, không thay source train/r2 đã pin.
6. Auditor chưa khóa ban đầu so list metric theo thứ tự JSON1/24/6 với bản gốc1/6/24.
   Auditor `phase28.metric-order-roundtrip.2` đối chiếu chính xác full row theo name/horizon,
   từ chối trùng/thiếu/thừa và sai value dù1e-12. Giữ byte-identical auditor cũ trong
   `attempts/auditor_metric_order_v1.py`; không sửa metric/prediction hoặc thêm tolerance.
7. Trước seal, đưa legend của rolling/forecast ra ngoài vùng vẽ để không che dữ liệu.
   Đã xem đủ7 PNG và xem lại2 bản chỉnh; không đổi dữ liệu của hình.

Chi tiết: `phase28_export_incident_v1.md`, `phase28_r2_authorization.md`,
`phase28_audit_roundtrip_note.md` và sidecar/log trong manifest Phase28.

## Đầu ra bàn giao

- Bản thảo: `report/sections/v3/ch04_rnn.md`; lý thuyết cơ bản, hợp hàm theo tầng/thời gian,
  shape/tham số, code ba loại, giải thích hàm, data cards, kết quả và deploy ngắn.
- JSON:132 run row,660 aggregate row,396 horizon row,540 horizon aggregate,
  2.244 per-series row tại `artifacts/metrics/phase28/tables/`.
-7 PNG300dpi +7 SVG, đã visual QA và seal; `report_generation.json` pin manuscript/tables/figures.
-3 notebook tại `experiments/notebooks/v3/ch04_rnn/` chạy fixed TRAIN input,
  đọc metric validation, không import torch/tensorflow/keras khi serving.
-9 model seed42 chạy demo/contract CPU NumPy, thực sự nạp checkpoint train độc lập.
  Registry trained-validation riêng, không sửa initialized registry Phase25.
- Handoff33 main checkpoint:27 RNN +6 baseline cho Phase29. Rolling checkpoints chỉ
  development, không thay model main để chấm TEST.

## Bảo toàn và bước tiếp theo

Release gốc SHA-256 `7947b266ef5eeafb2c72506e012b41c2b37194506e7b2a8d8b501ad46f9b75e6`;
training fingerprint52 file `c7aaafbe11688e15bbc33da23c0bc5558a42ed3662504a5ae018b4d4eb556c70`.
R2 declaration SHA-256 `11c7251f5dd092ba7c109f4ea512d3062de3cc6dd1514f683dd7aa06bbc771b7`.

Kiểm lại3.954 file của các khóa Phase22/24/25/26/27: PASS. Preservation giữ11.357 raw file,
DOCX V2,7 config/23 metric/10 prediction TEST Ch5, Ch5 run_count=1. Không sửa env/uv.lock,
UI/API/DOCX, không cleanup dữ liệu người dùng, commit/reset hoặc viết lại Git history.

Lệnh kiểm chỉ-đọc sau phát hành: `scripts/check_phase28.ps1`.
**Tiếp theo: làm Phase29 — LSTM**, giữ cùng dữ liệu/windows/scalers/budget. Chỉ mở một
batch TEST chung sau khi cả RNN/LSTM và evaluator/approved run IDs đã khóa; không tự bắt đầu
Phase29 trong lượt này. HTTP/React/Render thuộc32–33, DOCX tích hợp/render thuộc34–35.
