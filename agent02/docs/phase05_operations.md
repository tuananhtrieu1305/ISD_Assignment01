# Vận hành và bàn giao AG02 phase 5

Đã đánh giá cuối 71 claim: 50 core (25Q ×2 vai), 20 đối chứng (rule/no-discount ×5
kịch bản ×2 vai) và1 REF native. Mỗi claim500 episode ×20 bước, evaluation_count=1.
Không train/tuning, không chạy lại TEST V3. Source/Q/config của phase1–4 giữ nguyên.

Từ `C:\DATA\assign` trong PowerShell, runtime Ubuntu/tuananh đã khóa:

```powershell
.\agent02_assignment\scripts\run_agent02_phase05.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase05
```

Auditor chỉ đọc saved outputs và tái tính bảng; không gọi evaluator hoặc forward
policy. Nó kiểm các khóa cũ chứa khoảng1,2GB nên có thể chậm; không khởi động thêm
writer/auditor/producer đồng thời. Không ghi coverage/XML lên file đã khóa.

## Gate và journal

- `evidence/phase05/declaration.json`: pretest, evaluator/source hashes, input26Q,
  native checkpoint/RNG, toàn71 job và scenario đã khóa trước final forward.
- Key journal: `(study_id,policy_sha256,scenario_sha256,role)`; job_id chỉ là nhãn.
- `artifacts/evaluation/phase05/journal/<key>/claim.json` tạo exclusive trước forward.
  Có `result.json`, CSV500 dòng và `complete.json` (count1) khi thành công.
- Có claim thiếu completion thì từ chối replay, kể cả process đã thoát. Giữ partial/
  failure, chẩn đoán và revision từ saved outputs; không xóa/reset claim để chạy lại.
- Claim đã hoàn tất chỉ kiểm hash và reuse. Không forward chỉ để làm lại bảng/hình.
- `completion.json` là chỉ mục71 job; `artifacts/manifests/phase05/evaluated_registry.json`
  là handoff riêng. Registry trained phase3/4 không bị sửa counter hoặc trạng thái.
- Controller COMPLETE/PID=null; `active_controller.json` là operational mutable state
  ngoài release. Flock dùng chung phase3 để chặn writer song song; file còn không
  có nghĩa handle đang giữ.

Final pipeline đã thành công không incident, không resume claim thật. Test failure/
replay dùng fixture riêng và không tính vào71 claim khoa học. Pretest fixture dùng
seed910xxx, không final20000xx. Không dùng kết quả cuối để thay seed/alpha/epsilon.

## Cách hiểu các nhóm đánh giá

CONTROLLED dùng Tape/MarketEnv/QAgent phase2 không sửa: scenario seed2.000.000+
training_seed, episode0…499, cùng tape theo seed/role giữa cấu hình và controls.
Đổi hai vai; gộp vai mỗi seed trước rồi mean/sample std qua5 training seed, ddof1.
Q copy read-only, no learn/exploration, tie-breaking theo isclose giữ nguyên;
RNG phá đồng hạng tách RNG train. Chỉ gọi rule đối thủ theo policy cố định, không
cố định chuỗi action của rule vì nó có thể phản ứng với hành động learner trước đó.

Hai so sánh cần tách: (1) Q trừ rule **trong cùng cuộc đối đầu**, (2) reward của
policy Q trừ policy control trước cùng fixed opponent/tape. Không lấy (1) kết luận
Q tốt hơn rule-policy theo (2). Các controls không train; n5 của controls là5 kịch
bản, không phải5 trained agent. Lịch sử reset0 khiến Rule-vs-rule và no-discount
có thể cùng giữ giá suốt episode; giữ hai claim type nhưng công khai trùng hành vi.

REF native dùng `evaluate_pair` gốc với env seed500042, role0 duy nhất; policy/RNG
clone từ checkpoint REF42. Instrumentation chỉ đếm action/guard, fixture đã so
reward/action với hàm gốc. Source Q/RNG checkpoint không đổi; không gộp REF vào n5.

## Bảng, hình và kết quả dùng tiếp

Sáu CSV trong `artifacts/metrics/phase05/`: baseline_reward (6 dòng), q_policy
(104 dòng/26Q), alpha_comparison (3), exploration_comparison (3), multi_seed (25),
paired_comparison (25). Config/controls summary JSON và source manifest bổ trợ.
Raw71 CSV tổng35.500 episode rows;710.000 market step, không coi là710.000 mẫu độc lập.

4 PNG có figure_notes JSON/MD và visualQA. Mean±std rate có thể kéo whisker xuống
dưới0 khi khác biệt seed lớn; tỷ lệ thực đo từng seed vẫn0–100%, whisker không phải
khoảng xác suất/CI. Ghi rõ điều này khi ghép hình tỷ lệ action vào báo cáo cuối.
Manifest producer pendingQA là snapshot trước kiểm; QA/release xác nhận đã xem.

Đọc `docs/phase05_report.md` và `report/sections/phase05_final_evaluation.md` để ghép
báo cáo phase8. Giữ kết quả không thắng control; không chỉnh model hoặc diễn giải
thành có ý nghĩa thống kê chỉ từ whisker overlap. Phase6 chỉ khi người dùng yêu cầu:
hai learner và sửa kernel/Gold, cần gate riêng; không mở lại71 claim phase5.
