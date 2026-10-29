# Agent02 — bài độc lập

Kế hoạch thực hiện: [AG02_EXECUTION_PLAN.md](AG02_EXECUTION_PLAN.md).

Phạm vi đã xác nhận: chỉ báo cáo Agent02 với 10 câu hỏi; slide MAS để tham khảo.
Đề yêu cầu **PDF**, không phải chỉ DOCX. Hạn ghi trong đề: 23:30 ngày 29/10/2026.
Không áp giới hạn 6 trang của bài trước hoặc yêu cầu framework/deploy của V3.

**Đã hoàn tất phase 0–10.** Bản cuối có28trang,đủ10câu,20hình và14bảng native
(12bảng kết quả,2bảng mô tả);chữđen/ảnhgrayscale. Đã xem đủ28trang vàmởWordreadonly
thànhcông. 245test/0skip,18mục nghiệmthuPASS. Giữmọi kết quả nghiên cứu đãkhóa.

- [PDF cuối để nộp](output/agent02_D23CTPM01_TrieuTuanAnh.pdf).
- [DOCX sửa được](output/agent02_D23CTPM01_TrieuTuanAnh.docx).
- [Hướng dẫn nộp](output/AG02_HUONG_DAN_NOP.md).
- [Manifest hash sản phẩm](output/AG02_RELEASE_MANIFEST.json).

Notebook44codecell vàZIP255file đãRunAll từbản giải nén PASS. Chưa gửi bài cho
thầy;chủbài tựnộpPDF theo kênh của lớp. Không cònphase chưa thực hiện.

Trạng thái chính: `checkpoint.json`. Quy tắc cục bộ: `AGENTS.md`.
Tất cả đầu ra mới nằm trong folder này; bài trước và V3 giữ nguyên.

- `sources/manifest.json`: hash/bytes/số trang của 6 file thầy cung cấp.
- `sources/extracted/`: chữ trích từ PDF và bản text của Python mang đuôi `.tex`.
- `sources/visual/`: các trang quan trọng đã render và xem để đối chiếu.
- `evidence/planning_runtime.json`: package/GPU và hash đầu vào tái sử dụng.
- `evidence/planning_verification.json`: kiểm tra plan/checkpoint và nguyên vẹn nguồn.

Các script `inspect_sources.py`, `inspect_runtime.py` chỉ phục vụ khảo sát;
không phải implementation của thí nghiệm Agent02.

## Lưu ý trình bày đã ghi nhớ

Lý thuyết ngắn, đủ ý, dễ hiểu; chỉ giữ công thức thật cần, không bỏ phép tính bắt buộc
ở câu 3/5/6. Mọi biểu đồ phải có giải thích trục/đơn vị, đường/cột/vùng sai số, dữ liệu
và aggregation, xu hướng/so sánh định lượng, giới hạn kết luận. Xem
`docs/requirements.md` và `docs/figure_explanation_template.md`.

## Kiểm tra môi trường và reference an toàn

Từ `C:\DATA\assign` trong PowerShell:

```powershell
.\agent02_assignment\scripts\run_agent02.ps1 -Task preflight
.\agent02_assignment\scripts\run_agent02.ps1 -Task inspect-reference
```

Launcher dùng `scripts/run_experiment.ps1` đã có, chọn **Ubuntu**, user **tuananh**,
Python 3.11.17 ở `.venv-torch`. Không dùng distro mặc định Ubuntu-24.04 cũ, Windows
Python hay tạo environment mới. Package versions được đối chiếu snapshot đã kiểm.
Không có lệnh train ở phase 1; lệnh `train` bị từ chối.

`code/agent02_experiment.py` là bản sao **đúng nguyên byte** từ `sources/provided/agent02_code.tex`,
chỉ parse AST/compile ở phase 1; phase 2 import có kiểm hash và gọi hàm smoke giới hạn.
**Không chạy trực tiếp file này từ root**:
code thầy có `main()` chạy nhiều thí nghiệm và output mặc định tương đối
`agent02_results`. Runner phase 2 kiểm soát output trong folder bài này, không gọi main.

Chạy tests riêng (không train):

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module pytest -ModuleArguments @('agent02_assignment/tests','-q','-p','no:cacheprovider')
```

`evidence/phase01/runtime_probe.ipynb` đã chạy hai cell import/version/NumPy, không
phải notebook thí nghiệm RL. File kết nối Jupyter dùng thư mục tạm Linux riêng để
đáp ứng quyền 0600; không bật insecure writes hay mở notebook server công khai.

## Bàn giao phase 1

- `docs/phase01_report.md`: công việc, kiểm thử, lỗi probe và phạm vi còn lại.
- `evidence/phase01/source_receipt.json`: sáu bản nguồn và reference exact-byte.
- `evidence/phase01/reference_inspection.json`: 4 class, 12 function, defaults từ AST.
- `evidence/phase01/preparation.json`: runtime/probe/bảo toàn đầu vào trước và sau.
- `evidence/phase01/final_tests_r2.xml`, `final_coverage_r2.json`: nghiệm thu 29 test.
- `evidence/phase01/input_lock.json`, `verification.json`: khóa đầu vào và biên bản cuối.

Coverage 99,12% là cho `workspace.py`, không phải toàn pipeline/teacher model.
Mã reference không được format để giữ hash. Các mô hình, dataset và TEST cũ không chạy lại.

## Bàn giao phase 2

- [Biên bản](docs/phase02_report.md): core, 103 test/0 skip, smoke và ngân sách ước tính.
- [Giải thích mô hình/hàm](docs/model_core_v1.md): ngắn, có ví dụ Q=4,65 và margin5/3.
- [Protocol v1](docs/protocol_v1.json): 56 run đã đăng ký cho các phase sau, chưa thực hiện.
- [Vận hành](docs/phase02_operations.md): guard/resume, track REF/CONTROLLED và ranh giới final.
- `evidence/phase02/protocol_lock.json`, `verification.json`: khóa48 file và audit PASS.

Coverage 95,43% là sáu module phase2, không bao gồm code thầy/auditor/toàn project.
Không sửa file trong khóa; phase sau thêm runner riêng. Kiểm chỉ đọc:

```powershell
.\agent02_assignment\scripts\run_agent02_phase02.ps1 -Task status
.\agent02_assignment\scripts\run_agent02_phase02.ps1 -Task verify-smoke
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase02
```

Không chạy lại coverage vào file phase2 đã khóa. Dùng output mới theo phase khi cần test thêm.

## Bàn giao phase 3

- [Biên bản kết quả](docs/phase03_report.md): hai baseline, DEV, cách hiểu kết quả và giới hạn.
- [Diễn giải bốn hình](artifacts/figures/phase03/figure_notes.md): raw/MA100, Q và action count.
- [Bản thảo A–B](report/sections/phase03_baseline.md): nguồn để ghép báo cáo các phase sau.
- [Vận hành](docs/phase03_operations.md): registry, recovery và baseline11 cần reuse ở phase4.
- `artifacts/manifests/phase03/trained_registry.json`: hai checkpoint đã train, final count0.
- `evidence/phase03/experiment_lock.json`, `verification.json`: khóa268 file và audit PASS.

122 test/0skip, coverage94,94% trên ba module mới; không phải toàn repo/teacher/CLI/plots.
Kiểm chỉ đọc, không train/DEV/final lại:

```powershell
.\agent02_assignment\scripts\run_agent02_phase03.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase03
```

Phase4 dùng lại CONTROLLED baseline11 đúng checkpoint/hash/declaration, chỉ train24
core run còn lại. Không sửa protocol bất biến hay registry phase3 để cập nhật trạng thái.

## Bàn giao phase 4

- [Biên bản kết quả](docs/phase04_report.md): đầy đủ25/25 và cách đọc mean/std, khác biệt seed.
- [Diễn giải bốn hình](artifacts/figures/phase04/figure_notes.md): alpha/exploration curves, lịch epsilon, summary train.
- [Bản thảo C/D](report/sections/phase04_sweeps.md): bảng thật/notes để ghép báo cáo.
- [Vận hành](docs/phase04_operations.md): recovery, registry25 Q và handoff sang phase5.
- `artifacts/manifests/phase04/trained_registry.json`: 25 Q-table trained, final count0.
- `evidence/phase04/experiment_lock.json`, `verification.json`: khóa2.792 file, audit PASS.

137 test/0skip. Coverage100% là **ba helper mới** về chọn run và tổng hợp số liệu,
không phải toàn project/teacher/CLI/plots/auditor. Giữ mọi seed, kể cả α0,01 seed55
có profit thấp; không điều chỉnh cấu hình theo train score. Kiểm chỉ đọc:

```powershell
.\agent02_assignment\scripts\run_agent02_phase04.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase04
```

Auditor đọc khoảng1,2GB run artifacts để kiểm hash/tái tính bảng, có thể chậm trên
DrvFS; không khởi động writer thứ hai khi audit/producer đang chạy. Phase5 chỉ bắt
đầu theo yêu cầu, khóa evaluator/gate/journal trước500 episode/vai; không train lại25 Q.

## Bàn giao phase 5

- [Biên bản kết quả](docs/phase05_report.md): đánh giá cuối, kết quả thật và giới hạn.
- [Diễn giải bốn hình](artifacts/figures/phase05/figure_notes.md): profit, paired delta,
  train/final và tỷ lệ giảm giá; có trục/đơn vị, n, mean/std và số liệu nhận xét.
- [Bản thảo E](report/sections/phase05_final_evaluation.md): sáu bảng và phân tích.
- [Vận hành](docs/phase05_operations.md): journal/count1, nguồn Q và handoff phase6.
- `artifacts/manifests/phase05/evaluated_registry.json`:71 claim đã hoàn tất.
- `evidence/phase05/experiment_lock.json`, `verification.json`:khóa329 file,audit PASS.

157 test/0skip; coverage94,32% chỉ evaluator/journal/aggregate mới. Hai vai được gộp
trước khi tính mean/sample std qua5 training seed; controls có5 kịch bản, REF native
riêng. Không dùng chênh lợi nhuận giữa hai shop trong cùng trận để kết luận Q thắng
policy rule trước cùng đối thủ. Giữ cả kết quả thấp hơn đối chứng, không tuning từ final.

Kiểm chỉ đọc, không train/evaluate lại:

```powershell
.\agent02_assignment\scripts\run_agent02_phase05.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase05
```

Không chạy lại71 claim hoặc ghi đè XML/coverage/source đã khóa. Registry trained ở
phase3/4 giữ nguyên snapshot trước final. Phase6 chỉ bắt đầu khi người dùng yêu cầu.

## Bàn giao phase 6

- [Biên bản kết quả](docs/phase06_report.md): câu8/9,GoldTRAIN,so sánh thật và giới hạn.
- [Thiết kế trước thí nghiệm](docs/phase06_design.md):15run và160claim được định trước.
- [Giải thích bốn hình](artifacts/figures/phase06/figure_notes.md):giá/kernel vàng,
  trainhai learner,checkpoint drift và robustness.
- [Bản thảo câu8–9](report/sections/phase06_robustness.md),[vận hành](docs/phase06_operations.md).
- `data/derived/gold_regime_kernel_v1.json`:prefix560giáTRAIN và kernel/cutoff/hash.
- `artifacts/manifests/phase06/trained_evaluated_registry.json`:15run/20learner đã train.
- `evidence/phase06/experiment_lock.json`,`verification.json`:khóa2.343file,audit PASS.

186test/0skip;coverage97,19% chỉbốn module mới.160claim,count1,80.000episode rows;
9CSV/4PNGđã xem/giải thích.Không tune từ kết quả hoặc chạy lại để lấy hình.
Kiểm chỉ đọc từ root repo:

```powershell
.\agent02_assignment\scripts\run_agent02_phase06.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase06
```

Train lại có mean thấp hơn baseline cũ trên cảpersistent/Gold trong thí nghiệm này;
giữ đủ seed/kết quả,không coi đó là khẳng định mọi retrain đều kém. Không chọn lại
checkpoint Q8từfinal. Phase7 chỉ theo yêu cầu;không train/eval lạiPhase5/6.

## Bàn giao phase 7

- [Biên bản kết quả](docs/phase07_report.md): thiết kế câu10, so sánh thật và giới hạn.
- [Thiết kế trước train](docs/phase07_design.md), [vận hành](docs/phase07_operations.md).
- [Giải thích bốn hình](artifacts/figures/phase07/figure_notes.md): train, profit cuối,
  paired delta và visitation/chi phí.
- [Bản thảo câu10](report/sections/phase07_improved_agent.md).
- `artifacts/manifests/phase07/reference_index.json`:60claim cũ được reuse,chưa từng forward lại ởPhase7.
- `artifacts/manifests/phase07/trained_evaluated_registry.json`:15agent mới đã train/đánh giá.
- `evidence/phase07/experiment_lock.json`,`verification.json`:khóa1.822file,audit PASS.

221test/0skip;coverage96,40% chỉ6module mới,không toànproject. Oracle là tính kỳ vọng
trên mô hình đã biết/fixedrule,không phải learner được train;không dùng nhãn tối ưu
để dạy Q. Kiểm chỉ đọc:

```powershell
.\agent02_assignment\scripts\run_agent02_phase07.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase07
```

Giữ kết quả model mới thấp hơn baseline/rule ởcả3kernel;không tune hoặc mở lại
final để sửa kết luận. Phase8 viết và ghép10câu từ output đã khóa khi được yêu cầu.

## Bàn giao phase 8

- [Bản thảo đầy đủ](report/phase08/manuscript.md).
- [Đối chiếu 10 câu và bằng chứng — bản hiện hành](report/question_evidence_matrix_r2.md).
- [Biên bản](docs/phase08_report.md), [vận hành](docs/phase08_operations.md),
  [sửa liên kết trình bày r2](docs/phase08_presentation_r2.md).
- `report/active_report.json`: chọn manuscript v1 và matrix r2.
- `evidence/phase08/verification.json`: audit 101 phép tính,70 input,7.501 file cũ;
  khóa31file. Coverage96,72% chỉ helper report_assets,không phải văn xuôi/toàn project.
- `evidence/phase08_presentation_r2/verification.json`: sửa đúng1link,21link PASS;
  bản gốc giữ nguyên. Không đổi bản thảo,code thí nghiệm hoặc kết quả.

Kiểm chỉ đọc (không dùng `--seal`):

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase08
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase08_presentation_r2
```

Phase9 làm notebook đọc saved output và dựng DOCX/PDF ứng viên. Phase10 kiểm mọi
trang và phát hành; metadata cá nhân/nhóm và tên file cuối cần xác nhận trước đó.
Không train/đánh giá cuối lại để tạo báo cáo hoặc tự nộp bài.

## Bàn giao phase 9

- [DOCX ứng viên 28 trang](report/build/candidate-r3/agent02_D23CTPM01_TrieuTuanAnh.docx).
- [PDF ứng viên](report/build/candidate-r3/agent02_D23CTPM01_TrieuTuanAnh.pdf).
- [Notebook có output thật](notebooks/AG02_Code_and_Results.ipynb).
- [Source và notebook ZIP](output/AG02_Source_and_Notebook_r1.zip).
- [Hướng dẫn chạy và dựng lại](docs/phase09_reproduction.md),
  [biên bản](docs/phase09_report.md),[bàn giao Phase10](docs/phase09_operations.md).

Metadata đãđược chủbài xácnhận:nộpcánhân,TriệuTuấnAnh/B23DCCN053/D23CTPM01,
filename nhưứngviên. Không cầnxácnhận lại nếu khôngđổi. Candidate đãđượcxemđủ28trang;
245test/0skip,coverage98,89%chỉpublicationhelper,không phải toànpipeline.
ZIP255file đủRunAllnotebook;không phải fullrawtrajectoryarchive. Fullaudit cần
workspacegốc. Khóa63file vàreceiptPASS ở `evidence/phase09/`;navigationmutable
`report/active_candidate.json` trỏ r3. Kiểm chỉđọc,không dùng --seal:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase09
```

Tiếp `làm AG02 phase 10` để kiểm rubric/chốt bản nộp cuối. Không tự nộp LMS/email,
train/final lại hoặc sửa file đã khóa để biên soạn.

## Bàn giao cuối Phase 10

`report/active_release.json` chọn sản phẩm cuối,thay cho các candidate khi lấy
file đểnộp. Khóa16file/receiptPASS tại `evidence/phase10/`;63filePhase9 và
7.501file khoa học cũ giữhash. NativeWord16.0readonly nhận28trang/14bảng,khôngsave.
Coverage98,89% chỉhelperpublication,khôngtoànpipeline. BảnPDF/DOCX cuối bằngbyte
candidate-r3 đãxemđủ28trang;khôngphát sinhtrain/finalclaim hoặc thay source.
Giữcandidate/QA làm lịch sử. Sửa bản nộp sau này cầnrevisionmới vàrender/QA lại.

Kiểmchỉđọc:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase10
```

Không dùng`--seal`,khôngghiđè XML/coverage hoặcfile trongkhóa. Không tựsubmit,
commit/push/deploy,chạy lạiScientificTEST hoặc thay môi trường hiện có.
