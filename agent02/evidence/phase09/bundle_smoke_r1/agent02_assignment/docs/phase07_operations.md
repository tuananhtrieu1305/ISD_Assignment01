# Vận hành và bàn giao AG02 Phase 7

Chỉ ghi trong `agent02_assignment/`. Dùng runtime Ubuntu/user tuananh đã khóa,
NumPy CPU float64. Không cài dependency hoặc đổi env GPU. Các nguồn/core/protocol,
raw Gold và toàn bộ thí nghiệm Phase1–6 giữ nguyên. Không chạy lại final để lấy hình.

Từ root repo, kiểm trạng thái và audit chỉ đọc:

```powershell
.\agent02_assignment\scripts\run_agent02_phase07.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase07
```

Auditor đọc checkpoint/CSV/hash, tái tính aggregate và kỳ vọng từ mô hình đã biết.
Không train, không gọi policy trên scenario để tạo thêm final output. Đọc nhiều file
qua DrvFS có thể chậm. Không chạy writer/auditor/coverage thứ hai cùng pipeline.

## Các khóa và quá trình chạy

`docs/phase07_design.md` mô tả thiết kế trước kết quả. Train declaration pin source,
test, kernel, 15 spec, alias witness và index 60 reference. Không sửa/format các file
đã pin. Sửa sau declaration cần revision giữ bản cũ; không thay thế source âm thầm.

Mỗi run 5.000×20, fresh zeroQ, baseline learning parameters. Full state theo thứ tự
`demand, own_previous, competitor_previous, remaining_steps`; axis Q dùng
`remaining_steps-1`, shape2×2×2×20×2,320giá trị. Time1…20; terminal không có state
time0 để bootstrap. Source mới ở code/augmented.py và augmented_runs.py; core cũ
không đổi. Có 51 checkpoint/run, Q, visitation, policy160state, raw CSV và trace20.

Run DONE có complete.json/hash, chỉ đọc/reuse. Run chưa complete cần explicit
`-Task train -Resume` sau kiểm claim/checkpoint thật; không reset Q/RNG/episode.
Diskguard5GiB giữ nguyên. Controller mutable ở evidence/phase07/active_controller.json.
File flock dùng chung phase3 có thể còn sau process thoát; kiểm handle/process thực.

Sau đủ15run, eval declaration pin30job/Q/scenario trước final. Mỗi Q500episode/vai,
hai physicalrole, cùngscenario_seed2000000+seed/Tape.generate/tieRNGchannel4 như
baseline. Qcopy read-only, không learn/exploration, hash Q trước/sau và file source.
Journal riêng artifacts/evaluation/phase07/journal, exclusive claim trướcforward,
key(study,policyhash,scenariohash,role),evaluation_count1. Partial/failure consumed
claim phải giữ và chẩn đoán/revision; không reset/xóa/replay. Completedclaim chỉ
kiểm hash/reuse, không forward để dựng bảng hoặc notebook.

## Reuse reference đúng phạm vi

artifacts/manifests/phase07/reference_index.json chứa60claim đã lưu trước train:
IIDbaseline/rule từPhase5;baseline retrain/rule trênpersistent/Gold từPhase6.
Index có exactjob/result/receipt/Qpath/hash. Các policy cũ đã train trên cùngkernel
với agent mới; không dùng baselineIID làm đối chứng chính trênGold. Không đổi
registry/protocol cũ. Trường status trong spec cũ là snapshot trước train; trạng
thái thực đọc complete/controller/registry mới.

So sánh có90member(30mới+60reuse), không phải90forward mới. Gộp2vai trước rồi
mean/sample std(ddof1) qua5seed/kernel;rule n5 là5scenario panel, không5trainedagent.
Paired delta augmented−baseline/rule theo cùngseed/tape. Giữ mọi seed/kết quả, không
chọn checkpoint hoặc tune từfinal. Không coi episode/step là replicate độc lập.

## Đọc oracle, chi phí và coverage

Oracle trong code/market_oracle.py tính lùi trên simulator đã biết/fixedrule, không
phải agent model-free đã học. Train không import oracle hoặc nhận Q/action tối ưu.
Kỳ vọng γ1 chia20 có đơn vị profit/bước; kỳ vọng γ0,9 là discounted total theo target
Q, không chia hoặc gộp nhầm vào metric final. Gap phân tích có bound theo kỳ vọng;
MonteCarlo500episode vẫn có nhiễu, không ép từng score quan sát nằm dưới oracle.
Tính lại oracle không tạo scenario/claim mới và không dùng nhãn TEST.

Coverage ở cost_coverage.csv là phần ôQ cóvisit>0 so320/8ô lý thuyết. Một số fullstate
không thể đạt từreset/horizon, nên không dùng tỷ lệ này đơn độc để kết luận thiếu
khám phá. Qpayload float64 là2.560/64byte, không phải peakRAM hoặc toàn bộ memory.
CPU/wall chỉ looptrain có instrumentation, không gồm checkpointI/O hoặc report;
các lượt chạy khác thời điểm không phải benchmark hệ thống độc lập.

8CSV/4PNGgrayscale,figure_notes và bản thảo report/sections/phase07_improved_agent.md
là đầu vào Phase8. Producer pendingQA là snapshot trước xem; visual_qa.json/release
xác nhận sau đó. Không ghi đè XML/coverage/evidence đã khóa khi ghép báo cáo.

Sau nghiệm thu Phase7, đủ56market run/61learner instance toàn bài. Phase8 chỉ khi
người dùng yêu cầu:viết câu1–10/báo cáo từ artifact có sẵn,không train/evaluate lại.
Chưa build/nộp PDF hoặc DOCX ở Phase7, không mở dự án MAS/LLM/web/Render.
