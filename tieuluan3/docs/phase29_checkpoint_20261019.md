# Checkpoint Phase29 — USER PAUSE ngày19/10/2026

Người dùng đã chọn **“Lưu checkpoint, tôi tiếp tục sau”**. Dừng thực thi tại đây;
không tự resume kể cả khi dung lượng hồi phục. Phase29 chưa COMPLETE, chưa mở TEST.

## Kết quả đã lưu

- Kiểm nguyên hash11.340 file trong6 khóa Phase22/24/25/26r2/27/28; Phase28 vẫn nguyên vẹn.
- 28 test pretrain PASS/0skip:27 torch-env,1 TensorFlow GPU; coverage dòng+nhánh86,4583%,
  lint PASS. Có RED trước triển khai core, policy và joint gate. Evidence không được ghi đè.
- 9 probe thực trên TRAIN:3 dataset ×3 framework, forward/BPTT parity PASS ở ngưỡng gốc;
  Keras TensorFlow GPU graph không XLA, không fallback. Peak allocator probe cao nhất105.791.488 byte,
  không phải peak của toàn training. Canonical Adam, h/c reset,6 learnable layers.
- Khai báo108 LSTM (27 main+81 rolling), không train lại24 baseline/RNN Phase28.
  `artifacts/manifests/phase29/release.json` SHA-256
  `e25c29bfa7bc957829a7001892eda89a253b5268e5dbdc5381bb81f7ad0ea528`.
  Source69 file fingerprint `09340206e85ab9885292b48debce490f1d5fed9fa68f6826de2dc84109081c2a`.
  Không sửa/format bất kỳ source/config/contract/evidence đã pin; cần thay đổi thì tạo revision.
- Hoàn tất3 run `ch4_gold_pink_sheet_lstm_{scratch,keras,pytorch}_s17_main`.
  Cả ba train23 epoch, best epoch17 khi đếm từ1; history/config/checkpoint/validation prediction
  và strict native-CPU export đã lưu. RMSE validation lần lượt716,338290 /716,337379 /716,332354
  USD/troy ounce; chưa phải tổng hợp3 seed hoặc kết quả TEST, không tuyên bố thắng RNN/baseline.
- Một số test synthetic nhẹ chuẩn bị cổng TEST chạy trong lúc queue phát triển còn tồn tại;
  không tuyên bố benchmark trong điều kiện máy hoàn toàn cô lập hoặc idle.
- Cổng one-shot joint TEST có12 test synthetic PASS, đã nằm trong28 test pretrain.
  Reader mới `holdout_data.py` có8 test synthetic bổ sung PASS, không mở dữ liệu TEST thật.
  Reader và test reader chưa nằm trong69 source declaration train; cần pin riêng cùng evaluator
  trước TEST. Coverage86,4583% là snapshot pretrain trước khi thêm reader, không phải coverage cuối.
- Bản thảo lý thuyết riêng `report/sections/v3/ch04_lstm_theory.md`: ví dụ cơ bản, cổng,
  hợp hàm,6 layer, giải thích từng hàm và code3 loại. Không ghi đè bản RNN/không ghép DOCX.

## Nguyên nhân dừng và trạng thái process

Trước run thứ4, `ch4_gold_pink_sheet_lstm_scratch_s42_main`, guard phát hiện host C dưới5GiB.
Run này **chưa có optimizer update/progress**, nên không phải resume từ một epoch đã train.
Log/traceback giữ trong manifest; không sửa source để bỏ guard.

Controller WSL PID4684/tool session8476 đã thoát exit1; `active_controller.json` PID=null,
status=failed. Không có queue train hoặc acceptance writer còn sống từ lượt này.
`checkpoint.json` mutable được cập nhật3/108, còn105, status=PAUSED_USER_REQUEST.

Dung lượng khi lỗi khoảng3,04GiB; sau khi process GPU thoát hồi lên khoảng11,79GiB.
Chưa chẩn đoán nguyên nhân Windows/WSL/pagefile nên không khẳng định đây là file dataset/model
phình ra. Dung lượng có thể giảm mạnh khi workload GPU hoạt động: ưu tiên15–20GiB headroom,
vẫn giữ reserve5GiB. Không xóa env/cache/raw/user data, không shutdown WSL tự động.

## Khi người dùng yêu cầu “làm tiếp phase29”

1. Đọc toàn bộ plan/AGENTS/checkpoint; kiểm host disk thực bằng .NET DriveInfo, không free ảoWSL.
   Xác nhận không có controller/coverage writer mới của người dùng. Không dùng PID lịch sử làm bằng chứng live.
2. Kiểm69 source cùng release/config/contract/hash của3 selection đã lưu, giữ Phase22–28 vàCh5.
   Không rerun prepare/preflight/proof để thay bằng chứng pretrain hoặc ghi đè file đã pin.
3. Nếu đủ headroom, resume **controller Phase29 hiện hành**:

   ```powershell
   .\scripts\run_experiment.ps1 -Framework torch -Module scripts.phase29_controller -ModuleArguments @('--stage','train')
   ```

   Controller bỏ qua3 selection đã xong, tiếp tục Gold/scratch/seed42/main. Chỉ một queue.
   Trước resume cập nhật checkpoint mutable vềIN_PROGRESS; không đổi active failed lịch sử bằng dữ liệu giả.
   `--stage status` chỉ đọc; không gọi command train nếu chưa được người dùng cho tiếp tục.
4. Chờ đủ108 selection, kiểm native CPU receipts và saved validation prediction/history/budget,
   gates/gradient/serialization, khôi phục registry trained riêng. Rolling chỉ development.
5. Hoàn thiện **evaluator/lock controller TEST còn chưa được triển khai**; test synthetic đầy đủ,
   kiểm cả27 RNN main+27 LSTM main+6 baseline main, bảo toàn orphan RNN Power/PyTorch17/null telemetry.
   Khóa evaluator/source/approved IDs/checkpoint/pretest proof trước claim; không gọi reader thật trước đó.
6. Test hai env tuần tự, regression/preservation/coverage cuối>=80%; pin bằng chứng pretest.
   Sau đó mới mở một batch TEST chung/mỗi dataset một seal; crash tiêu thụ claim, không retry/tuning.
7. Audit chỉ đọc prediction đã lưu; bảng RNN–LSTM/horizon/series/chi phí/seed, notebook/demo CPU,
   manuscript Ch4, xem hình rồi seal và release lock thật mới COMPLETE. Không tự nhảyPhase30.

HTTP/React vẫn32–33, DOCX34–35. Không mở lại TEST Ch2/Ch3/Ch5.
