# Vận hành AG02 phase 4

Phạm vi: đủ 25 CONTROLLED run = 5 cấu hình × 5 training seed. Baseline seed11 tái
dùng từ phase3, chỉ train 24 run mới. REF42 giữ riêng. Không có DEV mới hoặc final
evaluation trong phase4; không chọn lại config/seed từ biểu đồ train.

Từ `C:\DATA\assign`, PowerShell, runtime Ubuntu/tuananh đã khóa:

```powershell
.\agent02_assignment\scripts\run_agent02_phase04.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase04
```

Khi phase đã COMPLETE, ưu tiên audit chỉ đọc. Không ghi coverage/test XML lên bằng
chứng đã khóa. Không sửa source trong declaration/release, kể cả helper import từ
phase trước; thay đổi cần revision có lý do và giữ bản cũ.

## Đường dẫn cần dùng tiếp

- `docs/protocol_v1.json`: cấu hình/seed/budget bất biến của phase2.
- `evidence/phase04/declaration.json`: đăng ký source trước 24 run mới; pin khóa
  phase3, baseline completion/hash/declaration gốc và hai module thống kê/chọn run.
- `artifacts/runs/controlled/iid/<config>/sNNNN/`: CSV5.000 dòng, Q/policy/visits,
  trace20, checkpoint0 và100…5000, segment timing, manifest/claim/completion.
- `artifacts/manifests/phase04/train_completion.json`: chỉ mục đủ25 cell; baseline
  reused có source declaration phase3, 24 run mới trỏ declaration phase4.
- `artifacts/manifests/phase04/trained_registry.json`: handoff25 Q cho phase5;
  final count vẫn0. Không sửa registry phase3 hoặc protocol để đổi trạng thái.
- `artifacts/metrics/phase04/`: summary theo seed/cấu hình, 24.505 dòng mean/std
  curve (100…5000 ×5 config), paired train delta và bảng lịch epsilon.
- `artifacts/figures/phase04/`: 4 PNG/notes; status producer pendingQA là snapshot
  trước visualQA. `evidence/phase04/visual_qa.json` và release chốt việc đã xem hình.
- `report/sections/phase04_sweeps.md`: bản thảo C/D để dùng ở phase8.

## Queue và recovery

CLI phase4 dùng chung flock với phase3 để chặn writer đồng thời. Trạng thái động
ở `evidence/phase04/active_controller.json`: RUNNING có PID thật, khi thoát PID=null.
Đây là trạng thái vận hành mutable, không thuộc release; đừng suy queue sống chỉ
vì file lock còn. Kiểm process/lock thực trước khi resume.

Run DONE chỉ kiểm hash và tái dùng. Claim chưa complete cần `-Resume` tường minh,
khôi phục đúng checkpoint/Q/RNG/episode và declaration cũ; không xóa/reset claim.
Mỗi episode có guard5GiB. RuntimeError giữ checkpoint ranh giới/segmentPAUSED;
lỗi dữ liệu/serialization khác cần chẩn đoán trước, không tự sửa artifact.
Baseline11 chỉ verify registration theo declaration phase3, không gửi cho train.

Các XML RED/attempt1 là lịch sử phát triển, không cộng vào test nghiệm thu. Test
summary dùng fixture số học riêng, không phải run/reward thực hoặc forward final.
Một helper tổng hợp được bổ sung sau khai báo train; nó chỉ đọc log, không đổi
model/config/budget, và được khóa trong release trước dùng vào báo cáo cuối.

## Ý nghĩa thống kê

Curves: làm mượt100 episode **riêng từng seed**, rồi mean ±1 sample std qua5 seed,
ddof=1. Vùng mờ không phải CI; các cửa sổ chồng lấp không độc lập. Bảng whole-train
lấy mean/std của5 mean/run, khác với độ dao động reward qua episode trong một run.
Paired delta ghép seed ID, không dựa thứ tự dòng. Không coi 125.000 episode là
125.000 learner độc lập, không gọi lợi nhuận train là chất lượng final policy.

## Bước tiếp theo

Chỉ bắt đầu **AG02 phase5** khi người dùng yêu cầu. Đọc registry25 Q/hash/source
declaration, khóa evaluator/final gate/journal trước forward, dùng500 episode/vai
và seed/tape final riêng của protocol. Giữ tie-breaking, reward/môi trường và Q;
không dùng kết quả cuối để tuning. Bài V3, TEST cũ và source teacher vẫn chỉ đọc.
