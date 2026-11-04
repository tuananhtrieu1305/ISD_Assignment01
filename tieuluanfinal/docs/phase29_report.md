# Biên bản nghiệm thu Phase 29 — RNN–LSTM

Ngày bàn giao: 20/10/2026. Phạm vi là Chương 4B và bản thảo Chương 4 RNN–LSTM hợp nhất;
không phải toàn bộ tiểu luận DOCX, API/React hay bản deploy Render.
Trạng thái phát hành chính thức nằm trong `artifacts/manifests/phase29/experiment_lock.json`:
chỉ COMPLETE khi khóa đã tạo và `scripts/check_phase29.ps1` kiểm hash PASS.

## 1. Kết quả thực hiện

- Hoàn tất 108 LSTM selection: 27 main và 81 rolling-validation trên Gold Pink Sheet,
  BIS Residential Property Prices và Household Power. Không train lại RNN Phase28.
- Scratch NumPy, Keras/TensorFlow và PyTorch dùng cùng cửa sổ, scaler, thứ tự feature,
  split, seed17/42/73, budget và kiến trúc 3 LSTM32 + Dense16/8/3: sáu tầng học được.
  Gates hoặc số timestep không được tính thêm thành layer.
- 108 checkpoint LSTM có strict native-CPU receipt; 183.159 prediction validation được audit.
  TEST chung gồm 27 RNN +27 LSTM +6 baseline: đủ60 member,111.900 dòng dự đoán,
  mỗi dòng ba horizon; không chọn seed hoặc rolling checkpoint bằng TEST.
- Registry trained/evaluated60 model nằm riêng tại `trained_registry.json`; không sửa
  initialized registry Phase25. Seed demo mặc định42 được cố định, không chọn bằng TEST.

## 2. Sự cố schema và phạm vi khôi phục được duyệt

Gold và BIS giữ seal gốc evaluated/evaluation_count1. Power giữ nguyên
failed_sealed/evaluation_count1,43 claim gốc và42 result đã hoàn tất toàn đợt.
Lượt `ch4_household_power_rnn_pytorch_s17_main` đã lưu4.911 dự đoán trước khi lỗi
schema phục hồi vốn chỉ cho validation. Không chạy forward lại lượt này.

Sau khi người dùng đồng ý, revision `test_schema_r1` khóa schema/finalizer/journal mới,
finalize metric từ đúng saved outputs và tiếp tục đúng17 lượt chưa claim. Cả17 đã xong,
controller finished/PID=null. Ledger revision evaluated ghi riêng; completion hiệu lực của
Power là completed_with_authorized_continuation, **không** sửa lịch sử seal lỗi và
**không** mở thêm batch TEST. Unified auditor chỉ đọc output đã lưu.

Evaluator revision SHA-256:
`8a0c613037ef5360c683c865fd348ec69b113cfc9a106bdf577529313f981145`.
Declaration/authorization, FAIL gốc, output/hash và nguồn đã pin được bảo toàn.
Timestamp finalize orphan là thời điểm hoàn tất bản ghi, không giả thành timestamp
inference cũ. Train/RAM/VRAM bị mất của orphan vẫn null: quality n3 nhưng cost n2.

## 3. Kiểm chứng

Sáu XML nghiệm thu cuối gồm65 Torch +1 Keras +263 regression +1 preservation
+15 report +21 revision: **366 test duy nhất,0 lỗi/0 skip**. XML RED hoặc lượt chạy lịch sử
không được cộng thêm. Preservation test cuối kiểm nguồn raw, V2 và TEST Ch5 không đổi.

| Phạm vi coverage cuối | Coverage line/branch hợp nhất |
|---|---:|
| Core Phase29 | 90,3581% |
| Schema/journal revision r1 | 93,4959% |
| Report/demo/export | 89,8574% |

Pretest gốc88,0165% giữ nguyên, không ghi đè bằng coverage hậu kiểm.
Ruff kiểm năm module summary/manuscript/demo/export/release và `tests/report29` PASS;
PowerShell parser của wrapper check PASS. Không cấu hình static type checker trong repo;
không tự gọi đó là type-check PASS. Kiểm shape/schema/checkpoint thực hiện bằng tests,
CPU receipts và notebook smoke. Cảnh báo module chưa import ở một process coverage riêng
không thay thế tổng coverage đã hợp nhất tuần tự ở trên.

Rà soát source mới: không thêm API công khai, credential, tải mạng, shell command hoặc
unsafe pickle. Demo whitelist dataset/family/seed, kiểm schema/finiteness/canonical order
và checkpoint hashes; notebook smoke chạy code do exporter tạo bằng runpy, không chạy
notebook do bên ngoài gửi lên. Không tự nhận đây là kiểm thử Jupyter UI/kernel picker.
Đợt release kiểm sâu11.340 file thuộc sáu khóa Phase22–28 và toàn bộ file trong khóa mới.

## 4. Nội dung báo cáo và demo

- Bản thảo hợp nhất: `report/sections/v3/ch04_rnn_lstm.md`; bản RNN Phase28 không đổi byte.
  Trình bày cơ bản, ví dụ/shape trước, công thức tối thiểu, hợp các hàm và giải thích từng
  hàm/gate; có code scratch/Keras/PyTorch, dataset card/link/mẫu/phân bố và giới hạn.
- Bảy bảng CSV và chín hình khoa học PNG300dpi/SVG: main/horizon/rolling,
  training cost, gate, gradient, learning curves, saved forecasts và lỗi49 quốc gia BIS.
  Cả chín PNG đã xem trực tiếp; visual QA PASS, chỉ áp dụng hình khoa học, không DOCX.
- Ba notebook CPU tại `experiments/notebooks/v3/ch04_rnn_lstm/`; smoke nạp đủ18 slot
  checkpoint train độc lập, dùng cùng TRAIN input cho hai họ và ba implementation.
  Serving thực tế là NumPy CPU portable, không phải ba framework GPU chạy trong web.
- Deploy chỉ là mục ngắn cuối chương. API/UI thuộc32–33; ghép/build/render DOCX thuộc34–35.

## 5. Kết quả và giới hạn cần giữ trong tiểu luận

Gold: mean RMSE RNN khoảng1.698–1.712 nghìn USD/troy oz, LSTM khoảng1.821 nghìn;
last-value khoảng255,16. BIS: macro-series RMSE RNN34,58–34,69, LSTM42,12–42,26;
last-value8,56. Hai họ đều kém baseline trên Gold/BIS; không che kết quả xấu hoặc tuning
lại bằng TEST. LSTM kém RNN khoảng6,38–7,24% trên Gold và21,68–21,96% trên BIS.

Power: mean RMSE RNN khoảng0,590–0,593 kW, LSTM0,583–0,590; last-value0,809,
seasonal0,763. Hai họ tốt hơn baseline. LSTM cải thiện khoảng1,80% scratch và1,28% Keras,
nhưng PyTorch kém RNN khoảng0,08%; không kết luận LSTM luôn tốt hơn hay có ý nghĩa
thống kê chỉ từ ba seed. Số chính xác/horizon nằm trong CSV, không dùng số làm tròn để audit.

LSTM nhiều tham số hơn RNN khoảng3,66–3,73 lần; đây là matched topology/budget,
không phải matched parameter count. Scratch CPU, Torch GPU, RNN Keras XLA và LSTM Keras
graph không XLA được khai báo trước train. Runtime được khôi phục giữa đợt, có unit test nhẹ
cùng queue; timing không phải benchmark máy cô lập hoặc HTTP latency.
Gate/gradient diagnostics là mô tả trên TRAIN, không chứng minh quan hệ nhân quả.

Gold/BIS là dữ liệu lịch sử đã sửa đổi, không bảo đảm vintage/publication-calendar thực tế;
Power chỉ một hộ và chưa xác minh DST. Đây là thực nghiệm học thuật hồi cứu, không phải
khuyến nghị đầu tư, dự báo vận hành đã triển khai hoặc cam kết khả năng tổng quát.

## 6. Bàn giao

Chạy kiểm chỉ-đọc sau phát hành:

```powershell
.\scripts\check_phase29.ps1 -Distribution Ubuntu
```

Runtime recovery r1 dùng Ubuntu/user tuananh, dependency đúng uv.lock; không gọi doctor/
bootstrap cũ ghi đè metadata. Không train, TEST forward, tuning hoặc ghi đè XML/coverage/
report đã khóa. Xem `docs/phase29_operations_r1.md` để demo và vận hành; thay đổi sau phát
hành cần revision mới giữ bằng chứng cũ. Chỉ làm Phase30 khi người dùng yêu cầu.
