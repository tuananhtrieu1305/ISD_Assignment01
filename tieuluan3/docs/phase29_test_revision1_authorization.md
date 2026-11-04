# Phase29 — đồng ý revision TEST schema r1,20/10/2026

Người dùng trả lời **“có”** cho phương án đã trình bày ngay trước đó:
khôi phục bản ghi từ4.911 prediction đã lưu, giữ nguyên seal lỗi và chỉ chạy17 lượt
chưa thực hiện. Đây là authorization cho revision có phiên bản, không phải yêu cầu
train lại, tuning hoặc mở một TEST batch mới.

Phạm vi được duyệt:

- Schema TEST riêng chỉ cho `ch4_household_power_rnn_pytorch_s17_main`.
- Finalize từ prediction/details đã lưu; không forward lại orphan, không thay null
  train/RAM/VRAM bằng0 hoặc số recovery, không đổi checkpoint/metric quality.
- Giữ nguyên original failed seal,43 claim và42 result; continuation ledger mới chỉ cho
  đúng17 run chưa claim trong original approved IDs, giữ count1 theo batch gốc.
- Không dựng lại cache TEST hoặc chạy lại Gold/BIS/các run đã consumed; mọi worker dùng
  frozen evaluator/model/checkpoint/scaler/budget. Pin revision source/tests/proof trước chạy.
- Công khai original timestamp TEST không được lưu đủ; timestamp phục hồi chỉ mô tả
  thời điểm tạo record, không giả làm thời điểm inference.
- Audit hợp nhất từ saved outputs, rồi tiếp tục report/notebook/visual QA/release Phase29.
  Không tự bắt đầu Phase30 hoặc thay UI/API/DOCX.

Incident snapshot được bảo toàn:
`artifacts/manifests/phase29/incidents/test_recovery_schema_v1/diagnosis.json`, SHA256
`b3b7188e48931ca161076f68425843a91fe4e048c3c9b26f7354e4da3311f3e2`.
Pretest cũ SHA256
`1587a113a8793510139eaf4e0d526fd93555edab336eec122c24b1d753967a1b`;
evaluator cũ `d57fe9be8d8a075525a30f2d7693d77080a79cc3c7f96a50960641995c2ae32c`.
Không sửa file này sau khi revision declaration ref/hash nó.
