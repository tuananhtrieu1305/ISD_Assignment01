# Vận hành Phase 6 — Agent02

Runtime đã khóa Ubuntu/user tuananh, NumPy CPU float64. Mọi output chỉ trong bài này.
Core/thầy/protocol/Phase1–5 không sửa; đánh giá cuối Phase5 không mở lại.

Lệnh từ root repo, dùng từng bước theo trạng thái; không khởi động hai writer:

```powershell
.\agent02_assignment\scripts\run_agent02_phase06.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase06
```

Lệnh auditor chỉ đọc saved scientific outputs/hash, không gọi train hoặc policyforward.
Đọc nhiều checkpoint/log qua DrvFS nên có thể chậm. Không chạy coverage vào evidence đã khóa.

## Thiết kế và gate

`docs/phase06_design.md` là thiết kế đã chốt trước kết quả; `train_declaration.json`
pin source/protocol/test/Goldprefix/kernel trước15train. Mỗi learner có8Qvalue,
mỗi pair có16Qvalue;10variant mỗi run8Qvalue. Tổng20learner instance.
Pair policyRNG SeedSequence([seed,3/4]); demand/sales giữ channel0/1/2.
Action hai learner chọn đồng thời từ state cũ; cập nhật sau cùng reward/terminal.
Không đổi alpha/gamma/epsilon để sửa kết quả bất lợi.

Run hoàn tất có complete.json/hash, raw5000episode,51checkpoint,visits,trace20,policy.
Trường status=declared_not_started kế thừa bên trong spec là snapshot protocol trước
train; trạng thái thực ở complete.json/controller/registry mới, không sửa ngược spec.
Không train lại run DONE. Run chưa complete cần đọc claim/checkpoint thật và explicit
`-Task train -Resume`; resume đúng Q/RNG/log, không reset sốepisode. Diskguard5GiB
giữ nguyên. Controller mutable trong evidence/phase06/active_controller.json.

`eval_declaration.json` pin160job và Qfile/checkpoint trước forward cuối, gồm:

-80Q8 claim:5pair×2learner×4checkpoint(0/1000/2500/5000)×2physicalrole.
-80variant claim:2kernel×5seed×4policy(IIDbaseline,retrained,rule,no_discount)×2role.

Mỗi claim500episode×20step;scenario_seed2000000+seed, cùngtape trong mỗi kernel,
đối thủ luôn fixed rule. Baseline cũ chỉ được đo trên hai kernel mới; IIDfinal đã có
ở Phase5 dùng saved reference. Không gọi lại Phase5 evaluator queue.
Module frozen final_v1 hỗ trợ MarketConfig.kernel, được reuse giữ nguyên sourcehash.
Journal riêng artifacts/evaluation/phase06/journal, key(study,policyhash,scenariohash,role).
Q8study tách checkpoint/learner để nhận diện repeated measures đã đăng ký.
Claim exclusive trướcforward,count1. Partial/failed phải giữ, chẩn đoán và revision;
không xóa/reset/replay claim consumed. Completedclaim chỉ kiểm/reuseoutput.

## Tổng hợp và giới hạn

Q8:gộp hai vai của từnglearner, rồi hai learner trongpair, cuối cùng mean/sample std
qua5pair seed. Không xem10learner là10replicate độc lập. Bốncheckpoint phụ thuộc,
không chọn checkpoint tốt nhất từfinal;policy drift ởstate ítgặp có thể không đổi reward.
Q9:gộp hai vai rồipaired delta retrain−baseline theo cùngseed/kernel. Controls khôngtrain;
n5 là5scenariopanel. Không so profit giữa hai kernel như một thử nghiệm cùng phân phối.
Rule/no_discount có thể cùnghànhvi từhistoryreset0;không bịa hai chuẩn hànhvi độc lập.

GoldTRAIN560tháng1960-01…2006-08, gồm lịch sử input trước targetTRAIN1962. Source/split/
trainIDhash lưu trong data/derived/gold_regime_kernel_v1.json. Không đọc giá muộn hơn cutoff
đểfit;không missing/impute/bridge. Regime0 gồm giảm/giữ,1làtăng,558transition cóLaplace+1.
Kernel đo hướnggiá vintage sửa hồi tố,không đo cầu vàng, không chứng minh nhân quả/đầu tư.

Các bảng/hình từ saved outputs:9CSV và4PNGgrayscale, figure_notes và bảnthảo
report/sections/phase06_robustness.md. Producer pendingQA là snapshot trước xem;
visual_qa.json/release xác nhận sau đó. Timing train chỉloopchunk, không checkpointI/O;
không dùng CPU/wall như benchmark hệ thống độc lập.

HandoffPhase7:giữcả5IIDbaseline Q từ3/4 và10variantQ từ6, cùngkernel/budget/tapes.
Không sửa registry cũ hoặc gọi lại160claim đểghép bảng. Phase7 chỉ khi được yêu cầu.
