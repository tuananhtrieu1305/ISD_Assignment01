# Vận hành và bàn giao AG02 phase 2

Chỉ dùng runtime WSL **Ubuntu**, user **tuananh**, Python 3.11.17 đã khóa.
Tất cả lệnh dưới chạy từ `C:\DATA\assign` trong PowerShell. Không cài package,
bootstrap/doctor, đổi môi trường GPU hoặc chạy main của code thầy.

```powershell
.\agent02_assignment\scripts\run_agent02_phase02.ps1 -Task status
.\agent02_assignment\scripts\run_agent02_phase02.ps1 -Task verify-smoke
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase02
```

`write-protocol` đã chạy trước smoke; chỉ tái dùng nội dung tương đương JSON.
`smoke` đã COMPLETE: gọi lại chỉ kiểm hash và đọc kết quả đã lưu, không train lại.
Giữ `claim.json` kể cả khi hỏng/đứt quãng. Nếu có claim nhưng thiếu completion,
runner từ chối chạy lại; chẩn đoán từ checkpoint và lập attempt/revision riêng.
REF không có resume tự động trong smoke. CONTROLLED có checkpoint/RNG ở ranh giới
episode, đã kiểm split run so với run liên tục chính xác từng byte JSON payload.

## Bằng chứng được giữ

- Protocol: `docs/protocol_v1.json` (cấu hình/seed/budget và phương pháp).
- Source/tests/docs/evidence của phase này: `evidence/phase02/protocol_lock.json`.
- Nghiệm thu: `evidence/phase02/verification.json`, `final_tests.xml`, `final_coverage.json`.
- Smoke: `evidence/phase02/smoke/complete.json`, hai thư mục `reference/`, `controlled/`.
- `checkpoint_e000100.json`: Q + RNG + rows + trace + visits; chỉ là **checkpoint smoke**.
- `policy.json`: tập hành động greedy ở từng state, giữ đồng hạng thay vì bốc thêm RNG.
- `development.json`: hai vai, mỗi vai 3 episode; không phải final evaluation.
- Các XML RED/development/candidate là lịch sử, không cộng vào 103 test nghiệm thu.

Khóa phase 2 gồm source điều phối smoke và core; không sửa/format file trong lock.
Phase sau dùng module/runner mới và các hàm đã khóa. Nếu phát hiện lỗi, tạo revision
có lý do và giữ bằng chứng cũ; không sửa kết quả để qua test. Plan/checkpoint/README/
AGENTS là điều hướng có thể cập nhật, không thuộc khóa dữ liệu thí nghiệm.

## Ranh giới thực thi tiếp theo

Phase 3 chỉ khi người dùng yêu cầu **`làm AG02 phase 3`**: REF baseline seed42 và
CONTROLLED baseline seed11, mỗi run 5.000×20, vẽ learning curve/policy theo plan.
Tạo runner full-train riêng, manifest/run ID rõ ràng; dùng protocol v1 và Q-learning
core đã khóa, không lấy seed hay Q smoke làm điểm bắt đầu. Source thầy chỉ gọi các
hàm cần thiết, không gọi main. Phase 4 mới chạy các seed/config còn lại.

Giữ tối thiểu 5 GiB trống, một writer. CONTROLLED kiểm guard trước từng episode;
nếu guard dừng, lưu checkpoint ở ranh giới đã hoàn tất. Với REF đầy đủ, phase 3 cần
wrapper giám sát dung lượng và thiết kế recovery riêng, không sửa RNG/thuật toán gốc.

Final evaluation thuộc phase 5 (variant 6/improved 7) sau gate, Q đóng băng,
seed/tape namespace riêng, đổi vai và journal claim. Evaluator phase 2 cố ý giới
hạn 100 episode DEV; phase sau thêm entry point final có gate/version riêng,
không nới ngầm giới hạn của module này. Không mở bất kỳ TEST V3 nào.

56 run là đăng ký cho nhiều phase; chưa phải 56 run đã thực hiện. Hai learner
và trạng thái cải tiến ở phase 6–7 cần module bổ sung; phase 2 chưa triển khai
chúng. Gold chưa có kernel đo được; không tự điền giá trị vào protocol đã khóa.
