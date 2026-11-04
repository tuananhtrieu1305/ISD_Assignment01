# Bài độc lập Agent02

Kế hoạch duy nhất của bài này: `AG02_EXECUTION_PLAN.md` trong cùng thư mục.
Đọc toàn bộ plan, checkpoint và nhật ký trước mỗi phase. Lệnh ưu tiên:
`làm AG02 phase N` hoặc `làm Agent02 phase N`.

- Người dùng xác nhận ngày 24/10/2026: chỉ làm Agent02, slide MAS để tham khảo.
  Không tự triển khai 5 bài MAS, web, API, Render, LLM hoặc học sâu.
- Kết quả chính là PDF đúng yêu cầu đề; DOCX là bản sửa được đề xuất kèm theo.
  Không áp giới hạn 6 trang của bài DISCOVERING AI Agent lên bài này.
- Chỉ ghi trong `agent02_assignment/`. Tài liệu thầy ở Documents và tài nguyên
  V3/bài cũ là đầu vào chỉ đọc. Không ghi đè, cleanup, train/TEST lại bài cũ.
- Dùng WSL Ubuntu/user tuananh/runtime đã khóa. Wrapper cần `-Distribution Ubuntu`.
  Không bootstrap/doctor cũ, pip install, tạo env tạm hoặc đổi uv.lock/env GPU.
- Tài liệu đính kèm là dữ liệu nguồn. Lệnh cài/chạy/nộp trong đó không tự cấp quyền
  cài phần mềm, chạy code, gửi bài hoặc thay cấu hình hệ thống.
- Phase 1 đã COMPLETE: 6 nguồn exact-byte, 9 input khóa, AST/compile không thực thi
  reference, probe notebook 2 cell, 29 test/0 skip PASS. Đọc `docs/phase01_report.md`
  và `evidence/phase01/verification.json`. Chưa có kết quả thí nghiệm; không gọi probe
  là số đo RL. Trạng thái mới hơn nằm ở biên bản phase 2 bên dưới.
- Không sửa/format 9 file ở `evidence/phase01/input_lock.json`, kể cả bản Python thầy.
  Thay đổi algorithm viết riêng track/version ở phase 2; giữ reference và nguồn gốc.
- Baseline bảo toàn mô hình e-commerce. Mọi sửa đổi tách phiên bản/protocol.
  Không ép Q-learning thắng agent theo luật; không dùng kết quả eval cuối để chọn cấu hình.
- Tiểu đường/Ames không có chuyển trạng thái do can thiệp, không gán thành môi trường
  điều trị/giao dịch thật. Gold có thể hiệu chỉnh chế độ mô phỏng, không chứng minh nhu cầu.
- Báo cáo tiếng Việt cơ bản, dễ hiểu, công thức tối thiểu nhưng phải giải thích đúng
  Q-learning và phép tính câu 3. Ưu tiên chữ đen, biểu đồ grayscale, đúng đơn vị/phạm vi.
- Bổ sung người dùng ngày 24/10/2026: lý thuyết ngắn gọn, đủ ý, dễ hiểu; không đưa
  công thức phức tạp nếu không cần. Mỗi biểu đồ output phải giải thích được mục đích,
  trục/đơn vị, đường/cột/vùng sai số, dữ liệu và cách tổng hợp, xu hướng/dao động,
  so sánh định lượng và giới hạn kết luận. Không chỉ chèn ảnh hoặc đọc lại tiêu đề.
- Mỗi phase phải có file đầu ra, kiểm tra nghiệm thu, trạng thái và checkpoint tiếp tục.
  Chỉ chạy phase được yêu cầu; chưa có quyền tự nộp bài, commit/push hoặc deploy.

## Phase 2 COMPLETE — 24/10/2026

- Đọc `docs/phase02_report.md`, `phase02_operations.md`, `model_core_v1.md` và
  `docs/protocol_v1.json`. Khóa48 file ở `evidence/phase02/protocol_lock.json`, SHA256
  `dfc338bfce41cbb4462c2e3fe7b04168f5193ab79f154d108024b75d65ce7832`.
  Không sửa/format source/tests/docs/evidence trong khóa; thay đổi cần revision giữ bản cũ.
- 103 test/0skip; coverage tổng95,4296% trên sáu module mới, dòng96,7667%/nhánh90,3509%.
  Auditor/code thầy không thuộc coverage. Không ghi đè XML/JSON coverage phase2 đã khóa.
- Smoke100 episode mỗi track, 4.000 train step thử+120DEV step, không phải kết quả
  nghiên cứu. Q/checkpoint smoke không làm điểm khởi đầu cho baseline phase3.
  Không có queue/process đang chạy; `smoke` khi COMPLETE chỉ đọc kiểm hash/reuse.
  Claim chưa complete phải chẩn đoán/revision, không tự xóa claim hoặc replay.
- REF exact-byte; CONTROLLED có RNG riêng nhu cầu/doanh số/policy. DEV đóng băng Q,
  scenario tape ghép cặp và đổi vai. Giữ terminal không bootstrap và Q câu3=4,65.
  Luật3 nhánh tương đương chỉ giảm ở state(1,1); reward lợi nhuận margin5/3.
- Protocol đăng ký56 run/61 learner instance nhưng chưa train đầy đủ. Phase3 chỉ
  REF baseline42 +CONTROLLED baseline11; full runner viết module mới, dùng core khóa.
  Final evaluation phase5/variant6/improved7 cần gate/journal riêng, không nới module DEV.
- Gold chỉ đọc metadata TRAINcutoff08/2006 ở phase2, chưa fit kernel. Không đụng giá
  validation/TEST V3; không tự chạy TEST của bài cũ. CDC/Ames không gán thành treatment RL.
- Runtime Ubuntu/tuananh đã khóa, CPU NumPy; không cần GPU. Giữ5GiB trống và một writer.
  Trạng thái hiện hành mới hơn ở biên bản phase3 bên dưới; không tự train đủ56 run hoặc viết PDF.

## Phase 3 COMPLETE — 24/10/2026

- Hai baseline REF42/CONTROLLED11 đã xong, mỗi run5.000×20, fresh zeros. Không train lại.
  Source thầy và core phase2 giữ hash; wrapper REF dùng nguyên class thầy, loop instrument
  đã khớp Q/reward/RNG chính sách với hàm gốc trên3 fixture trước train. Không gọi main.
- Đọc `docs/phase03_report.md`, `phase03_operations.md`, `report/sections/phase03_baseline.md`.
  Declaration SHA256 `50615dbdf5dbcb3893f0039a08f134f51ab17ec8c7e810797f0d4b1deec27506`.
  Khóa268 file `evidence/phase03/experiment_lock.json`, SHA256
  `25b050a28691073aab61064b3d3bf3d32ae1aac2388c2c6ccc681a099118a00a`.
  Không sửa/format file trong declaration/release (source/tests/docs/metric/prediction/checkpoint/QA).
- 122 test/0skip, coverage94,9367% chỉ reference_training/baseline_runs/baseline_analysis;
  không phải teacher/CLI/plots/auditor/toàn project. Giữ XML/coverage/pretrain theo hash.
- 10.000 dòng train, Q8/4-state policy, visits100.000/run, trace20/run, 51 checkpoint/run.
  Timing CPU/wall chỉ loop chunk có instrumentation, không bao gồm checkpoint I/O/DEV/report.
- DEV100 episode/vai, hai vai/tape1000011 cho cả hai Q, tổng8.000 market step, Q hash giữ nguyên.
  Cả hai learner giữ giá trên reachable observations; DEV sau gộp vai RL/rule cùng35,43125.
  Không dùng DEV chọn cấu hình hoặc coi là final; khác Q ở state không gặp không đổi hành vi này.
- 4 PNG grayscale đã xem, có explanation notes ở artifacts/figures/phase03/.
  Manifest producer pendingQA là snapshot lịch sử; visual_qa.json/release xác nhận PASS sau đó.
- Registry trained2 ở artifacts/manifests/phase03/trained_registry.json, final count0.
  Phase4 tái dùng baseline11 từ phase3, train24 run CONTROLLED còn lại; REF42 luôn riêng,
  không đưa vào replicate n5. Không sửa registry/protocol cũ để đổi trạng thái; tạo bản phase4.
- Check chỉ đọc: module agent02_assignment.verify_phase03, wrapper -Distribution Ubuntu.
  Không còn process/writer; file .writer.lock có thể còn nhưng không phải lock đang giữ.
  Chưa final evaluation/TEST V3 hoặc PDF/DOCX ở thời điểm3; trạng thái mới hơn ở phase4 bên dưới.

## Phase 4 COMPLETE — 24/10/2026

- Đủ25/25 CONTROLLED, 24 train mới +baseline11 reused giữ nguyên hash/declaration3.
  REF42 luôn riêng, tổng26 scientific run; không train lại để lấy hình hoặc thay seed.
  Source/core/model/protocol không đổi; không có scientific failure/resume.
- Declaration `evidence/phase04/declaration.json` SHA256
  `cec88cd1d8300c9325c6b27f605b208c973e05297d06d3863481f9e7f7d9b92a`.
  Release `evidence/phase04/experiment_lock.json` khóa2.792 file, SHA256
  `3ff17f6682ae26c5303a5d07450f6c0ce44df6304223838e63eb8da0371d7f38`.
  Không sửa/format source/tests/docs/artifact/evidence đã pin; thay đổi cần revision giữ bản cũ.
- Đọc docs/phase04_report.md, phase04_operations.md và report/sections/phase04_sweeps.md.
  Core125.000 episode rows/2.500.000 market step, Q8/policy4/visits100.000 và51 checkpoint/run.
  Registry trained25 ở artifacts/manifests/phase04/trained_registry.json; không sửa registry cũ.
- 137 test/0skip; coverage100% chỉ sweep_runs/sweep_analysis/sweep_summary (93 statement,
  36 branch), không phải toànrepo/teacher/CLI/plots/auditor. Giữ pretrain r2 và final XML/coverage.
  XML pretrain attempt1 lỗi mock là lịch sử, không phải scientific failure hay test nghiệm thu.
- 4 PNG grayscale đã xem/notes PASS. Curves mean±sample std giữa5 seed (ddof1) sau rolling100
  riêng từng seed, không phảiCI;24.505 aggregate curve rows. Whole-train std là giữa5 mean/run.
  Giữ seed55 của alpha_low trong phân tích; không bỏ outlier hoặc chọn lại config từ score train.
- Final count0, phase4 không DEV mới. Controller COMPLETE/PID=null; active_controller.json
  là mutable operational state ngoài lock. Không queue/producer/acceptance writer còn sống.
  File flock phase3 có thể còn nhưng handle đã thả. Không tự chạy lại coverage vào file khóa.
- Audit module agent02_assignment.verify_phase04 chỉ saved outputs, không policy forward;
  đọc/hash khoảng1,2GB nên có thể chậm. Wrapper luôn -Distribution Ubuntu/user tuananh.
  Khóa phase1–3/nguồn teacher/7 parent asset/Gold split metadata đã kiểm giữ nguyên.
- Tiếp AG02 phase5 chỉ khi người dùng yêu cầu: registry25Q đã train, đóng băng Q/config;
  khóa evaluator/gate/journal trước final500 episode/vai, giữ matched tapes/role swap,
  source declaration baseline11 thuộc3,24 run khác thuộc4. Không train lại25 run, không tuning
  từ final score, không mở TEST V3 hoặc thực hiện phase6–10 khi chưa được yêu cầu.

## Phase 5 COMPLETE — 24/10/2026

- Đọc docs/phase05_report.md,phase05_operations.md và report/sections/phase05_final_evaluation.md.
  Declaration trước final SHA256 `5fd71f5c3bf70413c8bd456f79bb59ea75088a72149454cc5c3573ec871e8fa1`.
  Khóa329 file `evidence/phase05/experiment_lock.json`, SHA256
  `8aa5969bacbeb6e069bf357453c4679600f5a9fcd6e58064eea4dbf192c2865c`.
  Không sửa/format source/tests/docs/output/evidence đã khóa; cần revision giữ bản cũ.
- Đủ71 claim/count1:50core(25Q×2vai),20controls(rule/no-discount×5panel×2vai),1REF native.
  500episode/claim,35.500 saved rows/710.000 market step. Không train/DEV mới hoặc tuning.
  Journal không failed/partial claim thật; không reset/xóa/replay claim để lấy lại kết quả.
  Mọi bảng/hình/audit tiếp theo chỉ đọc saved outputs, không policy forward lại.
- Q/source/config cũ giữ hash; registry evaluated mới ở artifacts/manifests/phase05/.
  Registry trained3/4 counter0 là snapshot lịch sử, không sửa ngược. Tổng26 scientific
  train run vẫn giữ;30 market train run của phase6/7 chưa thực hiện.
- Gộp hai vai trước, rồi mean/sample std(ddof1) qua5 training seed. Controls n5 là5scenario
  panel, không phải5trainedagent. REF native role0 riêng, không gộp vào n5 CONTROLLED.
  Rule-vs-rule/no-discount trùng hành vi giữ giá trên trajectory reset0; công khai điều này.
  Q−rule trong cùng trận không đồng nghĩa Q thắng policycontrol cùng đối thủ/tape.
  Giữ mọi seed và kết quả dưới đối chứng; không chọn config/tuning từ final.
- 6CSV/4PNG đã xem/giải thích/QA PASS. Whisker mean±std của tỷ lệ có thể vượt0–100%,
  không phải tỷ lệ quan sát hoặc CI; từng seed thực đo nằm0–100%. Notes đầy đủ trong figures/phase05/.
  157test/0skip;coverage94,3182% chỉ final_v1/journal_v1/aggregate_v1, không toàn project.
  Không ghi đè pretest152/final157 XML hoặc coverage/evidence đã khóa.
- Auditor agent02_assignment.verify_phase05 chỉ saved outputs/hash,tái tính aggregate;
  phase1–4/teacher/7parentasset/Goldmetadata giữ nguyên. Controller COMPLETE/PID=null.
  Không resume queue lịch sử;không chạy writer/auditor song song. Runtime Ubuntu/tuananh,
  wrapper -Distribution Ubuntu. Tiếp phase6 chỉ khi được yêu cầu;không tự PDF/DOCX hoặc TEST V3.

## Phase 6 COMPLETE — 24/10/2026

- Đọc docs/phase06_report.md,phase06_operations.md,phase06_design.md và
  report/sections/phase06_robustness.md. Train declaration SHA256
  `d95096c67d760240c1ee8ac45264d8dcdbe59d067baff97b26ce2e999f9288a8`;
  eval declaration SHA256 `f03206ede3ec1973e94270985c2a19f01bbdaa38007de5f382c395c030481a2d`.
  Khóa2.343file evidence/phase06/experiment_lock.json SHA256
  `9637d62f6c2061f173d0147d77d368bf2d85e21b5049d60320a7edca0d5d68d3`.
  Không sửa/format source/tests/docs/output/evidence đã khóa;thay đổi cần revision giữ bản cũ.
- Đủ15registered trainrun:5pair two-learners +10persistent/Gold variant,20learner,
  freshzeroQ,5.000×20/run,51checkpoint/run.75.000trainrow/1,5triệumarketstep/
  2triệulearnerupdate. Không train lại15run hoặc core25/REF;không scientificfailure/resume.
  Tổng41/56market trainrun của bài;phase7còn15augmented run,không tự chạy.
- Gold kernel từ560giáTRAIN1960-01…2006-08,559regime/558transition,cóLaplace+1.
  Hashsource/split/TRAIN IDs/cutoff trong data/derived/gold_regime_kernel_v1.json.
  Chỉprefixgiá,không impute/bridge hoặcfitvalidation/TEST. Đây là proxy demand giả lập,
  không dữ liệu nhu cầu vàng hoặc backtestđầu tư;vintage có thể sửa hồi tố.
- 160claim/count1(80Q8checkpoint +80variant),80.000row/1,6triệumarketstep final.
  Journal riêng artifacts/evaluation/phase06/journal;không failed/partialclaim hoặcreplay.
  Không reset/xóa/retry consumedclaim hoặcforward đểlấy lại bảng/hình. IIDfinalPhase5
  đã giữ nguyên;Qbaseline cũ chỉ đo trênkernel mới theoPhase6declaration.
- Q8gộp role→2learner trongpair→5pair seed;không coi10learner là10replicate độc lập.
  Checkpoint0/1000/2500/5000 là repeatedmeasures;không chọn lại checkpoint tốt nhất.
  Variantpaired delta theo5seed/kernel;controlsn5là5scenariopanel. Rule/no_discount
  trùnghànhvi trêntrajectoryreset0;không bịa hai chuẩn độc lập. Giữkếtquảretrain thấp
  hơnbaseline ởcả2kernel,không tuning/loại seed. Driftdescriptive,không chứngminhnhânquả.
- 9CSV/4PNGgrayscale đãxem/giải thích/QA PASS.186test/0skip,coverage97,1875% chỉ
  gold_regime/pair_training/phase06_journal/phase06_analysis;khôngtoànrepo/frozen
  evaluator/CLI/plots/auditor. Khôngghiđè181pretrain/final186XML/coverageđãkhóa.
  Registrytrained/evaluatedmới riêng,khôngsửa protocolstatus/snapshotregistry cũ.
- Auditor agent02_assignment.verify_phase06 chỉsavedoutputs/hash/táitính,khôngforward.
  Bảo toàn3.336protectedfilePhase1–5/7parentasset/Goldprovenance. ControllerCOMPLETE/
  PID=null,khôngqueue/acceptancewriter. RuntimeUbuntu/tuananh,wrapper -Distribution Ubuntu.
  TiếpPhase7chỉkhiđượcyêucầu;không tựPDF/DOCX/LLM/MAS/Render hoặcTESTV3.

## Phase 7 COMPLETE — 24/10/2026

- Đọc `docs/phase07_report.md`, `phase07_operations.md`, `phase07_design.md` và
  `report/sections/phase07_improved_agent.md`. Train declaration SHA256
  `9c14187e3aca833e70389395db4b9115c6b24ba3512db29f70ca8a249fd236d9`;
  eval declaration SHA256 `909607dff359f2ec12a90d2c5d4738c76bf54f1a98b97f1f6ef65cf943690975`.
  Release `evidence/phase07/experiment_lock.json` khóa1.822file, SHA256
  `06d4046f04abc456ba703819a4fe4c8bdee5f2757830d1409902ef4764e9f607`.
  Không sửa/format source/tests/docs/model/output/evidence đã khóa; cần revision giữ bản cũ.
- Đủ15 augmented run:3kernel×5seed,5.000×20/run,fresh zeroQ,51checkpoint/run.
  State(demand,own_previous,competitor_previous,remaining1…20),Qshape2×2×2×20×2,
  320giá trị. Fixture aliasing,terminal/no bootstrap,time và exact resume Q/RNG PASS.
  Không scientific failure/resume; không train lại. Toàn bài đủ56market run/61learner
  instance đăng ký, không còn run train cần hoàn tất ở các phase sau.
- 30 final claim mới/count1,15.000episode rows/300.000market step. Reuse60claim cũ:
  IIDbaseline/rule từ5,persistent/Gold matched baseline/rule từ6. Index pin trước train,
  không forward lại reference. So sánh90member/45.000savedrow,không90newforward.
  Journal riêng artifacts/evaluation/phase07/journal;không reset/xóa/replay consumed
  claim hoặc forward để lấy bảng/hình/notebook. Registry cũ giữ nguyên snapshot.
- Gộp role trước rồi5seed/kernel,paired delta cùng tape/opponent. Baseline chính
  đã train trên cùng kernel,không dùng QIID cũ làm baselinechính choGold. Rule n5
  làscenario panel,không5trainedagent. Model mới có meanprofit thấp hơnbaseline/rule
  trêncả3kernel trong budgetđãkhóa;không coi std nhỏ hơn là robust hơn,không tuning/
  chọnseed/checkpoint từfinal. Đề xuất state hợp lý không đồng nghĩa đã cải thiện score.
- Oracle code/market_oracle.py chỉ kỳ vọng phân tích known-model/fixedrule,không
  model-free đã học,không dạy learner bằng Q/action tối ưu. γ1profit/bước táchγ0,9
  discountedtotal. Gap bound áp dụng kỳ vọng,không ép MonteCarlo score dưới bound.
  Auditor được táitính oracle từQ đãlưu,không sampledforward/TEST hoặc train.
- 8CSV/4PNGgrayscale đã xem/giải thích/QA PASS. 221test/0skip,coverage96,3964% chỉ
  augmented/augmented_runs/augmented_final/phase07_journal/market_oracle/phase07_analysis;
  không CLI/plots/auditor/frozenbaseline/toànrepo. Giữ pretrain216/final221 XML/coverage.
  Qpayload2.560/64byte không phảipeakRAM;visitationtheoretical320/8ô có structuralzeros.
- Auditor agent02_assignment.verify_phase07 chỉsavedoutputs/hash/aggregate/analytic
  model expectations; bảo toàn5.679filePhase1–6/7parentasset. Controller COMPLETE/PID=null,
  khôngqueue/acceptancewriter. RuntimeUbuntu/tuananh,wrapper -Distribution Ubuntu.
  TiếpPhase8 chỉ khi được yêu cầu:viết10câu/evidence matrix/báo cáo từartifactđãkhóa,
  không train/evaluate lại hoặc tựPDF/DOCX/nộpbài/LLM/MAS/Render/TESTV3.

## Phase 8 COMPLETE — 24/10/2026

- Bản thảo hiện hành `report/phase08/manuscript.md`:9 phần,10 câu,12 bảng,
  20 hình có giải thích,8 exact-source excerpt. Chọn qua `report/active_report.json`.
  Matrix hiện hành `report/question_evidence_matrix_r2.md`; JSON matrix v1 giữ nguyên.
- Khóa31file `evidence/phase08/experiment_lock.json`, SHA256
  `5399801278e64aaed9b6535ac4d9684e31434311a4623e33c5bd153445f8bbc6`.
  Không sửa/format manuscript/template/compiler/helper/tests/docs/evidence trong khóa;
  cần revision giữ bản cũ. Không ghi đè final_tests_r2.xml/final_coverage_r2.json.
- Sau seal phát hiện matrix Markdown dẫn tới `phase 08/manuscript.md` sai. Giữ
  matrix gốc, thêm r2 chỉ thay đúng1link. Revision khóa4file tại
  `evidence/phase08_presentation_r2/experiment_lock.json`, SHA256
  `ae374a5358940f1c5dd97b4be9bd4a596e5dcb07f74a3ef31aca6b61af80027c`.
  Auditor r2 kiểm31file gốc/21link; không sửa manuscript/số liệu hoặc code scientific.
- 234test/0skip,coverage96,7213% chỉreport_assets;101saved-arithmetic checks PASS,
  70input/409numeric records/88numeric tokens;7.501protected file/7parentasset giữhash.
  PixelQA20hình từ3–7 reuse;20caption review,F03/F10 mở đối chiếu. Chưa render DOCX/PDF,
  không gọi đây làall-pageQA. REFpolicy bản cũ vốn đúng;không sửa số liệu không có lỗi.
- Đọc `docs/phase08_report.md`, `phase08_operations.md`, `phase08_presentation_r2.md`.
  Hai verifier Phase8 chỉ đọc hash/saved outputs,không train/forward. Chạy không --seal.
  Cả56run/61learner và261claim đã xong,không mở lại final hoặc train đểlàm notebook.
- Tiếp Phase9 chỉ khi được yêu cầu: đọc skill hiện hành,notebook read-only/sourcebundle,
  buildDOCX/PDF ứng viên bằng runtime/toolchain cũ;20hình/bảngnative/code chữđen và
  giải thích phải giữ. Metadata cá nhân/nhóm/team_name còn cần xác nhận trước filename
  phát hành;khôngbịa. Phase10 xem mọi trang/chốt nộp. Không tự nộp/commit/deploy.

## Phase 9 COMPLETE — 24/10/2026

- Đọc `docs/phase09_report.md`, `phase09_operations.md`, `phase09_reproduction.md`;
  chọnứngviên qua `report/active_candidate.json`. DOCX/PDF r3 trong
  `report/build/candidate-r3/`,28trang/14native table/20figure/8exact-sourceexcerpt.
  Đã mởxem riêng đủ28PNG125dpi ởQAphase09/r3,khôngclipping/overlap/missingglyph;
  chữDOCX/PDFđen,mọiPNGgrayscale. KhôngclaimnativeWordpagination hoặc finalrelease.
- Notebook `notebooks/AG02_Code_and_Results.ipynb`:44codecell đãchạy,20PNGoutput/
  12bảng kết quả/8codeexcerpt/10câu. ASTguard khôngchoimport scientificmodule hoặc
  train/learn/step/evaluate. RunAll chỉđọcfile/hash/hiểnthịvàtínhQ3giảđịnh.
- ZIP `output/AG02_Source_and_Notebook_r1.zip`:255payloadfile/15.746.858byte,
  SHA256 `4382e8321924115e2247fd51433bfabcae8258204ed94ea827b7efb9072bbf10`.
  ĐãRunAll từbản giảinén độc lập:44cell PASS/255hashkhôngđổi. Đây làsource+
  compactpresentationinputs,không fulltrajectoryarchive;fullscientificaudit cần
  workspacegốc. Khôngcầndatasetdownload hoặcmodelforwardđểchạynotebook.
- User xácnhận nộpcánhân,TriệuTuấnAnh/B23DCCN053/D23CTPM01 vàfilename
  `agent02_D23CTPM01_TrieuTuanAnh.pdf`;ghi `evidence/phase09/submission_metadata.json`.
  Không hỏi lại nếu userkhôngđổi. MetadataPhase8đãkhóa giữnguyên lịch sử.
- Khóa63file `evidence/phase09/experiment_lock.json`,SHA256
  `c482f44341c0d314ffed40f1084f37d59a4c58f10f60497ea2ac4c6db5c1886d`.
  Không sửa/format source/tests/docs/notebook/candidate/QA/evidence đãpin;
  thayđổi cầnrevision mới giữbảncũ. Khôngghiđèfinal_tests_r3.xml/final_coverage_r3.json.
  Giữr1/r2 vàattempts. `verify_phase09` không--seal chỉđọc/hash,khôngforward.
- 245test/0skip,coverage98,8889% chỉpublication_v1 helper;statement98,3871%/
  branch100%,khôngphải builder/renderer/vănxuôi/toànrepo. Ruff/CLI/seal PASS;
  dependency8audit trước/sau giữ7.501file/7parentasset/hash và101phép đối chiếu.
  Không train/finalclaim mới. Runtimecode/docs cũreuse,khôngcài/sửaGPUenv.
- Lượtseal trước bịauto-reviewusage-limitfailure nênchưa chạy;userđãyêu cầu
  tiếp tục,seal sauPASS. Khôngcònqueue/writer cầnresume. TiếpPhase10 chỉkhi
  được yêu cầu:rubric/toàntrang/finalrelease/hướngdẫnnộp. Mọi sửa phải tạo
  candidate-r4/QAphase10 mới,khôngghiđèr3. Khôngtựsubmit/commit/push/deploy.

## Phase 10 COMPLETE — 24/10/2026 — AG02 hoàn tất

- Sản phẩm cuối `output/agent02_D23CTPM01_TrieuTuanAnh.pdf` và `.docx`;chọn qua
  `report/active_release.json`. Manifest `output/AG02_RELEASE_MANIFEST.json`,guide
  `output/AG02_HUONG_DAN_NOP.md`. Metadata cá nhân đãchốt,không hỏi lại. Chưasubmit.
- Final bằngbytecandidate-r3 đãQA,28trang/14native table/20hình/8sourceexcerpt.
  Phase10 đãmởxemlạiđủ28PNGđộ phân giải gốc,reuse render vìDOCX/PDF khôngđổi.
  Word16.0readonlyPASS,28trang/14bảng/field0error,khôngsave vàđónginstance riêng.
  KhôngclaimđãxemnativeWordlayout ởmọiphiênbản. PDF chínhgiữbố cục đãnghiệmthu.
- 18mục R01–R16/U01–U02,citation/10câu/12bảng số liệu/8đoạncode được đốichiếu
  vớiPDF/sourceartifact/S1trang8–12. Giữkếtquảâm,mẫusố,n/std vàphạmviGoldproxy,
  khôngtune hoặcchạy lại TEST/training. Lýthuyếtbasic,côngthức cầnthiết,hìnhcógiảithích.
- 245test/0skip chạyởPhase10,coverage98,8889% chỉpublication_v1 helper;khôngphải
  toànrepo/renderer/releaseCLI/vănxuôi. EvidencePhase10 mới,khôngghiđèPhase9.
  RuffPASS,fullparentaudit giữ7.501file/7parentasset/uv.lock và101arithmeticchecks.
- Khóa16file `evidence/phase10/experiment_lock.json`,SHA256
  `06cdbb14f8e2e1d2b7c7f652e287d18acaa9861b91fcad7f6a056322add6f541`.
  Khôngsửa/format source/docs/output/evidence đãpin. Giữ63filePhase9/khóacũ;
  thayđổi saupháthành cầnrevisionmới,khôngghiđèfinal/candidate/QA hiện tại.
  `verify_phase10` không--seal chỉđọc/hash,không scientificexecution.
- FinalPDF SHA256c15a623023525257af0a95cc72af0ae4a4ffca887a69bd9175d22295188f518e;
  DOCX SHA2567b215b3c7e865ed849305a3dafffcdf1cd7b39b5aa02db36650329546507301d.
  Notebook44cell/ZIP255file giữ nguyên. User tựnộpPDF trước hạn trongđề;
  khôngtựLMS/email/commit/push/deploy. Khôngcònqueue/writer hoặcphase chưa làm.
