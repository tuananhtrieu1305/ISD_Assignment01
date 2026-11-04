# Phase29 — lỗi finalization TEST của checkpoint phục hồi,20/10/2026

## Trạng thái hiện hành

Phase29 **IN_PROGRESS, chờ duyệt revision**, không COMPLETE và không USER PAUSE.
Train đã xong108/108; controller finished/PID=null, bộ chờ hậu kiểm cũ đã thoát.
Không có queue train hoặc TEST đang chạy sau lỗi. Không tự chạy lại controller TEST.

-108 native-CPU receipts PASS, audit183.159 prediction validation PASS,12 data view.
- Các khóa Phase22–28 được kiểm11.340 file và giữ nguyên hash.
- Pretest330 test/0skip, coverage88,0165289256%, lint PASS.
- Evaluator đã khóa: `d57fe9be8d8a075525a30f2d7693d77080a79cc3c7f96a50960641995c2ae32c`.
- Pretest proof SHA256:
  `1587a113a8793510139eaf4e0d526fd93555edab336eec122c24b1d753967a1b`.

## TEST đã thực hiện, không được lặp lại

| Dataset | Seal gốc | Count | Bản ghi kết quả hoàn tất |
|---|---|---:|---:|
| Gold |evaluated |1 |20/20 |
| BIS |evaluated |1 |20/20 |
| Power |failed_sealed |1 |2/20, lượt thứ3 đã có output nhưng chưa có metric/result |

Tổng42 result hoàn tất,43 claim đã consumed,17 run chưa claim. Lượt lỗi duy nhất:
`ch4_household_power_rnn_pytorch_s17_main`, checkpoint phục hồi r2 của Phase28.

Native inference đã xong, weights/optimizer không đổi và4.911 prediction cùng details
đã lưu trước khi validator từ chối metric. **Không chạy lại forward của lượt này.**
Checkpoint vẫn SHA256
`e3437f37fab6f26196f9a7d72601d4de29a1518a96f9143ed9167316bc054e82`.
Original train/RAM/VRAM vẫn null; giữ GPU→CPU FAIL lịch sử, không thay bằng số đo recovery.

## Nguyên nhân và bằng chứng

Log worker dừng tại `joint_evaluation.evaluate_member → export_r2.validate_run`:

```text
ValueError: Recovery run schema: 'validation' was expected
```

`export_r2.recovery_schema()` của Phase28 cố định `split=validation` cho đúng orphan.
Evaluator Phase29 copy metric này và đổi split thànhTEST, rồi gọi validator cũ. Vì vậy
đây là lỗi schema finalization sau inference, không phải crash train, mất weights hoặc
lỗi metric số học. Không được sửa validator/source Phase28 hay evaluator đã pin để lách lỗi.

Forensic audit chỉ đọc saved bytes đã PASS:

-4.911 row đúngID/order/float64 target/series/calendar của shared cache.
- Recompute metric từ prediction đã lưu khớp details chính xác.
-42 result hiện có và mọi metric/prediction/details/checkpoint ref giữ hash.
- Seal/manifest/claim gốc không sửa; không model construction hoặc TEST forward mới.

Evidence: `artifacts/manifests/phase29/incidents/test_recovery_schema_v1/diagnosis.json`,
SHA256 `b3b7188e48931ca161076f68425843a91fe4e048c3c9b26f7354e4da3311f3e2`.
Script `scripts/diagnose_phase29_test_schema_v1.py` được ref/pin trong evidence: không sửa/format.
File này là bằng chứng chẩn đoán, không phải authorization, metric/result mới hoặc nghiệm thu.

## Phương án đề nghị — CHƯA được duyệt/thực hiện

1. Tạo revision/schemaTEST riêng chỉ cho orphan này, giữ nguyên null telemetry, checkpoint,
   dự đoán và mọi ngưỡng. Unit test synthetic cho schema/claim/preservation trước khai báo.
   Không sửa source/evidence đã niêm phong hoặc schema/spec Phase22–28.
2. Finalize bản ghi orphan **từ4.911 prediction/details đã có**, không chạy lại model,
   không đổi quality. Original timestamp TEST chưa được lưu đủ: không bịa thời điểm inference;
   tách thời điểm phục hồi record và forward duration đã có trong details.
3. Giữ seal Power gốc `failed_sealed` cùng toàn bộ journal, tạo continuation ledger có phiên bản
   và authorization riêng, liên kết hash pretest/seal/cache/42 result/partial output.
   Không reset seal/count hoặc tạo claim mới cho43 lượt đã consumed.
4. Chỉ đánh giá17 run gốc **chưa claim**, dùng cache hiện có và checkpoint/selection đã khóa;
   không dựng lại TEST inputs, retrain, chọn lại seed hoặc tuning. Không chạy lại Gold/BIS
   hoặc các run Power đã có prediction. Audit hợp nhất từ saved outputs bằng auditor revision.
5. Khi đầy đủ mới sinh bảng/hình/bản thảo/notebook/visual QA/experiment_lock. Public record phải
   công khai sự cố schema và revision, không mô tả pipeline ban đầu thành công liền mạch.

Việc tiếp tục sau failed seal thay đổi cách vận hành journal đã khóa nên cần người dùng đồng ý
revision trước. Nếu chưa đồng ý, giữ nguyên trạng thái và bằng chứng, không tự mở lại TEST.

## Code báo cáo đã chuẩn bị nhưng chưa nghiệm thu

`summarize_phase29.py`, `write_phase29_manuscript.py`, `demo_phase29.py`, `export_phase29.py`
và `tests/report29/`:10 unit test PASS, lint PASS; RED evidence được giữ. Đây là code chuẩn bị,
chưa có full report statistics/Ch4 hợp nhất/notebook export/QA/release thực tế vì TEST chưa xong.
Không dùng các câu chữ dự kiến trong renderer làm bằng chứng rằng60 run đã hoàn tất.
Không đổi UI/API/DOCX và không tự bắt đầu Phase30.
