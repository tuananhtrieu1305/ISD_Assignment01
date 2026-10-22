# Quy tắc làm việc cho tiểu luận V3

Kế hoạch đang hoạt động là `TIEU_LUAN_AI_V3_EXECUTION_PLAN.md`.

- Khi người dùng gõ `làm phase N` với N từ 20 đến 35, đọc toàn bộ kế hoạch này,
  kiểm tra trạng thái/dependency/nhật ký và thực hiện đúng phase; cập nhật bằng chứng nghiệm thu.
- Phase 0–19 là lịch sử. Không dùng outline hay đường dẫn của kế hoạch cũ để ghi đè yêu cầu V3.
- Source chính nằm trong `apps/`, `src/`, `experiments/` và `report/`.
  Xem `docs/repository_manifest.md` để hiểu đường dẫn đã chuyển ở Phase 20.
- `releases/v2/` là baseline chỉ đọc. Snapshot ZIP giữ cả source chưa commit trước khi dọn.
- `data/raw/ch5/`, cấu hình Ch5, metric và dự đoán TEST Phase 15 được giữ nguyên byte/hash.
  Không chạy lại TEST để tuning. Cache có sẵn trong raw snapshot cũng được bảo toàn.
- `term_paper/__init__.py` chỉ là cầu nối namespace cho serialized artifact; implementation
  nằm ở `src/term_paper/`. Giữ khả năng load các checkpoint cũ khi refactor namespace.
- `tests/legacy_v2/` và notebook `legacy/` là tài liệu tham chiếu; không mặc định chạy toàn bộ
  vì chúng còn yêu cầu framework/dataset/đường dẫn V2. Test API hiện tại nằm ở `tests/api/`.
- Phase 20 đã gỡ venv cũ. Phase 21 đã hoàn tất runtime WSL2/GPU: Python 3.11.17,
  PyTorch 2.14.1+cu130 và Keras 3.15.1/TensorFlow 2.21.0 trong hai venv Linux riêng.
  Xem `docs/environment_v3.md`; dùng bootstrap/doctor/run_experiment wrappers.
  Không dùng Python Windows, `backend/.venv` hoặc tự tạo env tạm không khóa dependency.
  TensorFlow cần wheel-local CUDA library paths; kernel/runner/doctor đã cấu hình sẵn.
  Không đổi Keras sang PyTorch nếu chưa có probe thất bại và ghi rõ fallback.
- Lý thuyết phải cơ bản, dễ hiểu, đủ ý; ưu tiên ví dụ và sơ đồ, công thức chỉ dùng khi cần.
- Phase 22 đã khóa `docs/srs_v3.md`, `experiments/configs/v3/protocol_v3.json`,
  `report/outline_v3.json` và schemas `src/common/schemas/v3/`. Kiểm tra bằng
  `scripts/run_experiment.ps1 -Framework torch -Module scripts.verify_phase22`.
  Không ghi đè `artifacts/manifests/phase22/spec_lock.json`; đổi spec cần deviation/version.
  Số đo thu nhận/EDA ghi vào artifact mới, không điền ngược vào protocol đã khóa.
  Ví dụ schema là synthetic, không dùng làm data/model/result thật.
  Phase 28 chỉ validation; TEST RNN/LSTM mở chung ở Phase 29 sau khi cả hai đã khóa.
- Phase25 đã hoàn tất: `docs/model_core_v3.md`, `docs/phase25_report.md`, registry
  `artifacts/manifests/phase25/initialized_contract_registry.json` và `core_lock.json` (219 file).
  Dùng `DatasetView`/`TensorAdapter`, canonical feature order và weights chung; không dùng helper
  transform EDA trực tiếp để train. Core/contract đã khóa, đổi cần revision có phiên bản.
  Registry chỉ initialized_only/inference_ready=false, không được coi là checkpoint đã train.
  Keras native Adam đã chuẩn hóa sqrt(v_hat)+epsilon; không thay bằng stock Keras Adam.
  Runner kiểm chứng `scripts/check_phase25.ps1`; coverage hai env phải ghi tuần tự.
  Phase27 cần batch reader/cache uint8 có budget cho CIFAR trước train; loader tham chiếu còn chậm.
- Phase26 COMPLETE: active manifest/registry/experiment_lock ở `artifacts/manifests/phase26/revisions/r2/`.
  54 run đã train/đánh giá; 3 TEST seal evaluated, count=1; không chạy lại TEST hoặc tuning.
  Checkpoint/source/config/core đã khóa; audit bằng `scripts/check_phase26.ps1` hoặc
  `scripts.verify_phase26_roundtrip_v1` (auditor gốc được giữ lịch sử, không dùng tiếp).
  Mọi phân tích mới đọc prediction đã lưu. Không đổi registry initialized Phase25 thành trained.
  Đọc `docs/phase26_operations.md`, `docs/phase26_report.md`; Ch2 draft ở report/sections/v3/.
  V1 preflight/snapshot33 và audit dtype revision giữ nguyên; đổi file khóa cần revision.
  Chưa đổi UI/API/DOCX; tiếp theo Phase27 theo yêu cầu người dùng.
- Giữ các thay đổi có sẵn của người dùng. Cleanup Phase 20 tạo nhiều tracked deletion và
  untracked migration; không reset, commit hoặc viết lại Git history nếu người dùng chưa yêu cầu.

## Phase27 COMPLETE — ngày 18/10/2026

- Đã khai báo 27 CNN + 9 majority tại `artifacts/manifests/phase27/release.json`.
  Source fingerprint `01e3a9025202e8e5f047f10f0d0cb9add4a482642c39db3d4fbb5b96688fc2d6`.
  Không sửa/format `src/ch03_cnn/`, prepare/controller/worker hoặc coverage INI đã khai báo.
  Thay đổi cần revision mới, giữ bằng chứng cũ. Các helper Ch2 import lại chỉ đọc.
- Matched preprocessing Phase24 khóa **augmentation=none**. Giữ nguyên cho cả ba framework;
  không tự thêm augmentation vào track đã khai báo. IDRiD dùng class weights train đã khóa.
- Cache development uint8 tại `data/processed/v3/phase27/`, pixel/ID parity đã kiểm toàn bộ;
  CIFAR đọc TAR binary theo một stream, không pickle. Không dựng TEST cache trước claim.
- Đủ 27 CNN + 9 majority, 3 seal TEST evaluated/evaluation_count=1; 169.836 prediction đã lưu.
  Controller finished/pid=null. Không chạy lại train hoặc TEST; Ch2/Ch5 TEST cũng không mở lại.
  Audit chỉ đọc prediction đã lưu, không TEST forward.
- Pretest Phase27 đã PASS ngày 18/10/2026, coverage 93,1083%. Giữ nguyên
  `artifacts/manifests/phase27/pretest_verification.json` và mọi evidence được ref trong đó.
  Auditor `scripts/verify_phase27.py` đã khóa SHA-256
  `8929cace0580aff718606e93a3388ffdcaf5f2c3a09529a69e01d6cc0751c4ea`.
  Không sửa/format auditor hoặc ghi đè unit XML/pretest coverage sau thời điểm này.
  Nếu phát hiện lỗi audit cần revision riêng, không đổi training/evaluator/TEST output.
- Khóa `artifacts/manifests/phase27/experiment_lock.json` gồm 2.378 file, SHA-256
  `f66f1b5b3793bce8f3a79c0603a2882a7f4173ac11bb51e21c8c3e9c5856522b`.
  293 test PASS/0 skip, coverage 93,1083%; kiểm bằng `scripts/check_phase27.ps1` (audit-only).
- `docs/phase27_operations.md` và `docs/phase27_report.md` mô tả bàn giao.
  Manuscript hiện hành `report/sections/v3/ch03_cnn_r2.md`, chọn qua `active_report.json`.
  r2 chỉ sửa trình bày confusion grids; r1/metric/checkpoint/prediction giữ nguyên byte/hash.
  Không sửa các file đã khóa kể cả docs/auditor; cần revision mới khi thay đổi.
- Scratch IDRiD seed73 resume epoch7: train time cộng đoạn chạy, RSS chỉ peak process resume;
  không khẳng định peak liên tục của toàn lượt. IDRiD quality thấp, không dùng chẩn đoán.
- Chưa tích hợp DOCX/UI/API live; các bước đó thuộc Phase32–35. Tiếp theo Phase28 chỉ
  validation RNN; TEST RNN/LSTM mở chung Phase29 sau khi khóa cả hai họ. Không tự chạy Phase28.

## Phase28 — lịch sử trước nghiệm thu (trạng thái hiện hành ở biên bản cuối)

- Khai báo trước train `artifacts/manifests/phase28/release.json`, SHA-256
  `7947b266ef5eeafb2c72506e012b41c2b37194506e7b2a8d8b501ad46f9b75e6`.
  Source fingerprint `c7aaafbe11688e15bbc33da23c0bc5558a42ed3662504a5ae018b4d4eb556c70`.
  Không sửa/format source đã pin trong release, gồm `src/ch04_rnn_lstm/`, prepare/worker/
  controller/preflight Phase28 và coverage INI; thay đổi cần revision giữ bằng chứng cũ.
- Ma trận132 selection: 27 RNN chính +81 RNN rolling (3 fold) +24 baseline causal.
  Cùng architecture3RNN32 +Dense16/8/3, seed17/42/73, batch32 và budget Phase22.
- WindowData revision phase28.1 bổ sung index gap của fold2/3 theo ID/calendar đã khóa;
  không sửa dữ liệu/split/scaler Phase24–25. Gold5/BIS98/power23 ID mỗi fold; xem operations.
- Keras vẫn TensorFlow GPU độc lập, dùng XLA sau probe/parity/resume PASS; giữ probe graph
  ban đầu ở `preflight_keras.json`, active `preflight_keras_xla_v1.json`. Host kiểm input/loss/
  gradient finite vì XLA có thể bỏ TF Assert. Không đổi model hyperparameter/backend.
- Controller/PID và checkpoint hiện hành trong manifest Phase28; chỉ một queue/coverage writer.
  **Checkpoint r2:** người dùng đã đồng ý; revision SHA-256
  `11c7251f5dd092ba7c109f4ea512d3062de3cc6dd1514f683dd7aa06bbc771b7`.
  Power PyTorch seed17 đã khôi phục từ best checkpoint, không thêm update, FAIL GPU/CPU gốc
  vẫn giữ. Đã đạt91/132 lúc ghi nhận; queue r2 chạy tiếp. Đọc trạng thái thực từ manifest.
  Không resume controller gốc; runner hiện hành `scripts.phase28_r2 --stage train`.
  Source r2 `export_r2.py`, `scripts/phase28_r2.py`, hai test và authorization đã pin, không
  sửa/format; thay đổi tiếp cần revision. Kiểm export bằng native CPU, giữ ngưỡng gốc cho108
  receipt; không nới tolerance. Telemetry train wall/RAM/VRAM gốc của duy nhất lượt orphan
  để null trong recovery schema, loại khỏi aggregate chi phí (n=2); không tạo số thay thế.
- Bộ chờ hậu kiểm r2 đã khởi động: Windows PID23296/tool session55253; queue WSL PID3707/
  session8342, chỉ là snapshot nhận diện. Kiểm trạng thái thực trước khi chạy lệnh mới.
  `scripts/finish_phase28_after_queue.ps1` đợi đủ132 và process controller thoát rồi mới
  chạy finish tuần tự; không tự TEST/seal/release. Không chạy thêm coverage/finish/receipt
  writer khi bộ chờ hoặc pipeline còn sống. Exclusive `.acceptance_*` file handles chặn
  trùng pipeline; xem operations. Sau pipeline phải audit/XML/coverage, xem7 hình, seal và
  release thật mới COMPLETE. Không tự nhảy Phase29.
- Không có lệnh TEST trong Phase28. TEST RNN/LSTM chỉ mở chung Phase29 sau khi cả hai khóa;
  TEST Ch2/Ch3/Ch5 tuyệt đối không chạy lại. HTTP/UI/DOCX vẫn thuộc các phase tích hợp sau.
- `docs/phase28_operations.md` mô tả vận hành. Chưa nghiệm thu toàn phase, không gọi initialized
  registry Phase25 là checkpoint đã train; registry trained-validation phải tách riêng.

## Phase28 COMPLETE — ngày18/10/2026

- 132 selection hoàn tất:108 RNN (27 main,81 rolling) +24 baseline causal; không train lại.
  Controller đã finished/PID=null, không còn queue chờ hoặc coverage writer nghiệm thu.
- Khóa7.386 file `artifacts/manifests/phase28/experiment_lock.json`, SHA-256
  `afd93a2a8c8c7336670c17c8d30132f5bcc663448f7658f5a3b35d6ae1d6c27e`.
  Không sửa/format source52, source r2, auditor/tests/docs/report/checkpoint/metric/prediction
  đã pin trong khóa. Sửa sau phát hành cần revision mới giữ bằng chứng cũ.
- 223.861 prediction validation được audit;108 strict native-CPU receipts PASS ở ngưỡng gốc.
  Giữ GPU/cuDNN→CPU FAIL của Power/PyTorch seed17, best checkpoint không đổi, không thêm update.
  Original train/RAM/VRAM của lượt orphan là null theo recovery schema; không thay bằng0 hoặc
  recovery peak. Cost aggregate nhóm này n=2, quality n=3. R2 declaration/authorization giữ nguyên.
- Auditor hiện hành `scripts/verify_phase28.py` SHA-256
  `0379f1e1b0d8a6694cb56f25e433f127e7981005464956dbb9b2871fb7bc8494`;
  so exact full metric row theo name/horizon, không list order. Bản cũ byte-identical ở attempts.
  Đọc `docs/phase28_audit_roundtrip_note.md`; không sửa metric hoặc nới tolerance để qua audit.
- 309 test/0 skip, coverage90,2216%;7 hình đã xem và seal,3 notebook/9 model CPU PASS.
  Không ghi đè XML/coverage/evidence sau khóa. Check chỉ-đọc bằng `scripts/check_phase28.ps1`;
  auditor chỉ có thể cập nhật `verification.json` mutable, không TEST forward hoặc training.
- Manuscript `report/sections/v3/ch04_rnn.md`, biên bản/vận hành ở docs/phase28*.md.
  Registry trained-validation riêng Phase25 initialized. Handoff27 main RNN +6 baseline cho29;
  rolling checkpoint chỉ development. Không gọi demo NumPy CLI là HTTP/React/Render live.
- Phase28 TEST evaluation_count=0. Phase29 phải triển khai LSTM trên cùng windows/scalers/budget,
  khóa cả hai họ/evaluator/approved IDs rồi mới TEST chung một lần; không mở lại TEST Ch2/Ch3/Ch5.
  Tiếp theo29 chỉ khi người dùng yêu cầu. DOCX vẫn thuộc34–35, API/UI32–33.

## Phase29 — lịch sử USER PAUSE ngày19/10/2026

- Người dùng chọn lưu checkpoint/tiếp tục sau. Không tự resume train khi chưa có yêu cầu mới.
  Đọc `docs/phase29_checkpoint_20261019.md`, checkpoint/active controller và toàn bộ plan khi tiếp tục.
- Đã khai báo108 LSTM, hoàn tất3 Gold seed17 main (scratch/Keras/PyTorch), còn105.
  Release SHAe25c29bfa7bc957829a7001892eda89a253b5268e5dbdc5381bb81f7ad0ea528;
  source69 fingerprint09340206e85ab9885292b48debce490f1d5fed9fa68f6826de2dc84109081c2a.
  Không sửa/format source/config/contracts/evidence đã pin, kể cả docs/phase29_operations.md.
- Controller4684/session8476 là lịch sử đã thoát exit1/PID=null. Run Gold/scratch/seed42/main
  chưa update vì host dưới5GiB. Checkpoint PAUSED_USER_REQUEST; không có queue hoặc writer còn sống.
  Disk lỗi3,04GiB, sau process GPU thoát hồi11,79GiB; cần kiểm headroom15–20GiB trước resume,
  không hạ reserve5GiB hoặc tự xóa env/dữ liệu/shutdown WSL.
- 28 test pretrain PASS/coverage86,4583%,9 real-shape probe PASS; Keras TF GPU graph khôngXLA.
  CPU export native-CPU ngưỡng gốc khai báo trước train, GPU comparison giữ diagnostic.
  8 reader synthetic test bổ sung PASS, reader chưa pin trong train release; evaluator TEST chưa xong.
  Không ghi đè XML/coverage/probe/proof đã ref trong declaration để tạo bằng chứng mới.
- TEST vẫn chưa mở. Sau108 selection phải audit/tests/pin evaluator/approved IDs/cả hai họ rồi mới
  TEST chung một lần. Không chạy lại TEST Ch2/Ch3/Ch5 hoặc3 selection đã hoàn tất. DOCX/UI chưa tích hợp.

## Phase29 — RESUME được yêu cầu ngày19/10/2026

- Người dùng đã yêu cầu tiếp tục sau khi thấy C còn gần12GB; yêu cầu này hủy pause ở trên.
  Host đo11,84GiB;312 ref/source/config/contract/3 selection giữ hash. Giữ reserve5GiB,
  không thay source69 đã pin hoặc train lại3 selection; theo dõi disk động khi GPU hoạt động.
- Trạng thái thực/process đọc từ manifest hiện hành, không suy ra từ PID/session lịch sử.
  TEST chưa được phép chạy trước khi đủ108 selection và các gate nghiệm thu tương ứng.

## Phase29 — trạng thái hiện hành: USER PAUSE sau resume1,19/10/2026

- Người dùng lại chọn lưu checkpoint/tiếp tục sau. Đọc
  `docs/phase29_checkpoint_resume1_20261019.md`; không tự resume theo mục RESUME lịch sử ở trên.
- Đủ5/108 LSTM: Gold seed17 ba implementation +seed42 scratch/Keras. Còn103; lượt tiếp theo
  Gold/PyTorch/seed42/main chưa update/progress. Không train lại5 selection đã xong.
- Controller2531/session99310 đã thoát exit1/PID=null; checkpoint PAUSED_USER_REQUEST.
  Source69/release/config giữ nguyên;312 ref trước và114 source/selection ref sau resume PASS.
- Host11,84GiB lúc nghỉ→2,387GiB khi GPU→11,46GiB sau thoát. WMI pagefile allocated
 19.307→23.099MB chỉ giải thích một phần sụt disk; snapshot ở `disk_diagnostic_resume1.json`.
  Gần12GiB idle đã hai lần không đủ; cần headroom khoảng20GiB, giữ reserve5GiB. Không tự
  đổi pagefile/WSL, xóa env/cache/raw/user data hoặc sửa training source đã pin để vượt guard.
- TEST chưa mở; evaluator TEST vẫn chưa hoàn thiện. Không ghi đè pretrain XML/coverage/probe/proof;
  chuẩn bị phần còn lại theo checkpoint khi người dùng yêu cầu tiếp tục. DOCX/UI chưa tích hợp.

## Phase29 — RESUME2 được yêu cầu ngày19/10/2026

- Yêu cầu tiếp tục mới đã hủy pause. Host56,21GiB;330 ref/source/config/5 selection PASS.
  Tiếp tục controller hiện hành từ Gold/PyTorch/seed42/main, không train lại5 selection đã xong.
  Giữ source69/config/guard5GiB; chỉ một queue/coverage writer. TEST vẫn sau gate nghiệm thu.

## Phase29 — runtime recovery r1 trong RESUME2

- Distro Ubuntu-24.04 không còn đăng ký; Ubuntu24.04.4 hiện tại dùng user tuananh, không có
  runtime cũ. GPU/driver vẫn nhận đúng. Không sửa runner/source69 hoặc metadata môi trường cũ.
- Recovery khai báo ở `artifacts/manifests/phase29/runtime_recovery/r1/declaration.json`;
  cài đúng uv.lock vào `/home/tuananh/.local/share/ai-term-paper-v3/` bằng nguồn versioned.
  Không gọi bootstrap/doctor cũ vì chúng ghi đè evidence Phase21/environment.json đã khóa.
  Không nâng dependency, không Keras fallback; probe mới chỉ ghi Phase29/runtime_recovery/r1/.
- Trước train phải recovery PASS/GPU–CPU smoke/package parity và kiểm hash declaration/source.
  Dùng wrapper `-Distribution Ubuntu` khi runtime được xác nhận; chưa có lượt train mới trong
  RESUME2 ở thời điểm khai báo. Theo dõi session cài47316 trước khi chạy thêm installer/queue.

## Phase29 — runtime recovery r1 PASS

- Cài47316 đã hoàn tất exit0. Probe4 process (torch/tensorflow ×GPU/CPU) PASS CNN/RNN/LSTM,
  exact Python3.11.17 và shared-package parity; không fallback. Receipt/source/log pin ở
  `artifacts/manifests/phase29/runtime_recovery/r1/`; không sửa các source recovery đã khai báo.
- Runtime mới `/home/tuananh/.local/share/ai-term-paper-v3/`; wrapper bắt buộc thêm
  `-Distribution Ubuntu`. Không dùng default Ubuntu-24.04 hoặc đường dẫn user anhca cũ.
  Old environment.json/uv.lock/release giữ hash; không chạy doctor/bootstrap cũ ghi đè evidence.
- Host còn33,44GiB sau khôi phục. Resume controller từ5/108; đọc PID/session/checkpoint thực,
  không mở thêm queue hoặc coverage writer. Cache/evaluator mới đang có11 synthetic test PASS,
  chưa phải evaluator TEST hoàn chỉnh/đã khóa, chưa được mở TEST thật.

## Phase29 — RESUME2 đang train và có bộ chờ hậu kiểm

- Đọc `docs/phase29_checkpoint_resume2_20261019.md`. Snapshot73/108, vàng/BIS đủ72,
  Power scratchs17 main xong; controller WSL3767/session29693 vẫn chạy. Không USER PAUSE.
- Runtime recovery r1 PASS, wrapper phải `-Distribution Ubuntu`, user tuananh/runtime mới;
  không bootstrap/doctor cũ, không dùng distro/home cũ. Giữ69 source train và3 recovery source.
- Bộ chờ hậu kiểm Windows22436/session42613 giữ exclusive `.development_pipeline.lock`,
  đợi108/controller thoát rồi tests/CPU receipts/audit/coverage/pretest proof tuần tự.
  Không chạy thêm queue/coverage/acceptance writer hoặc bộ chờ khi nó còn sống.
  Kiểm trạng thái thật, không suy từ PID snapshot/file lock tồn tại.
- Evaluator/cache/receipt/auditor mới có38 synthetic test PASS +lint16 file PASS; chưa phải
  nghiệm thu toàn phase. Không sửa EVAL_SOURCE_FILES khi pipeline đang chờ/chạy: audit/proof
  sắp pin fingerprint và CPU receipt pin writer. Sau proof thay đổi cần revision giữ evidence.
- Chưa TEST thật. Bộ chờ KHÔNG lock-test/test/release. Chỉ sau108 và pretest PASS mới mở3 seal
  chung RNN/LSTM/60main một lần. Post-TEST auditor mới chỉ đọc saved outputs, không forward.
  Report/figures/notebooks/demo/visual QA/experiment_lock còn chưa làm xong. Không gọi COMPLETE.

## Phase29 — trạng thái hiện hành ngày20/10/2026: TEST schema failure, chờ duyệt revision

-108/108 LSTM train xong/controller finished/PID=null; bộ chờ22436 không còn sống.
 108 CPU receipts/audit183.159 validation PASS;330 test/0skip/coverage88,0165% pretest PASS.
  Pretest proof1587a113a8793510139eaf4e0d526fd93555edab336eec122c24b1d753967a1b;
  evaluator d57fe9be8d8a075525a30f2d7693d77080a79cc3c7f96a50960641995c2ae32c đã khóa.
  Không sửa/format EVAL_SOURCE_FILES, XML/proof/coverage đã ref hoặc CPU receipt writer.
- TEST thật đã mở: Gold/BIS evaluated/count1 đủ20+20; Power failed_sealed/count1 sau2 result
  và1 partial. Tổng42 result,43 consumed claim,17 chưa claim. Controller TEST session18374
  đã thoát exit1; không có queue TEST/train đang chạy, không tự gọi lại --stage test.
- Orphan Power/RNN/Torch/s17 đã forward đúng1 lần và lưu4.911 prediction/details, nhưng
  validator Phase28 recovery schema chỉ cho validation nên từ chối metricTEST. Không forward
  lại lượt này, không sửa source Phase28/evaluator hoặc reset seal/claim để chạy tiếp.
- Forensic saved-output audit PASS, không model construction/TEST forward/đổi seal. Đọc
  `docs/phase29_test_schema_incident_20261020.md` và incidents/test_recovery_schema_v1/diagnosis.json.
  Diagnosis SHA b3b7188e48931ca161076f68425843a91fe4e048c3c9b26f7354e4da3311f3e2;
  script diagnose_phase29_test_schema_v1.py đã được ref/pin, không sửa/format.
- **Cần người dùng đồng ý revision**: schemaTEST riêng orphan +finalize từ output đã lưu,
  giữ seal failed gốc và continuation journal versioned chỉ cho17 lượt chưa claim. Đây mới
  là đề nghị, chưa authorization/code recovery. Không rerun43 claim, cache build, train/tuning;
  original orphan train/RAM/VRAM null và GPU→CPU FAIL giữ nguyên.
- Code report/demo mới ngoài EVAL đã chuẩn bị,10 unit/lint PASS, chưa chạy full pipeline vì
  TEST thiếu. Chưa có manuscript Ch4 hợp nhất/notebook/QA/release. Phase29 vẫn IN_PROGRESS,
  chờ duyệt, không COMPLETE/Phase30. Snapshot RESUME2/"chưa TEST" phía trên là lịch sử.

## Phase29 — revision TEST schema r1 được duyệt ngày20/10/2026

- Người dùng trả lời “có”, đồng ý phương án trong incident. Authorization riêng tại
  `docs/phase29_test_revision1_authorization.md`. Được finalize orphan từ4.911 output cũ,
  giữ failed seal gốc và continuation ledger mới chỉ cho17 run chưa claim. Không lặp43 claim.
- Source/schema/core/gate mới ở `src/ch04_rnn_lstm/phase29_revision/`, runner
  `scripts/phase29_test_r1.py`, auditor `scripts/verify_phase29_test_r1.py`; khai báo/evidence
  ở `artifacts/manifests/phase29/revisions/test_schema_r1/`. Sau declaration không sửa/format
  các FILES đã pin. Không đổi EVAL_SOURCE_FILES cũ, Phase28/recovery source hoặc proof cũ.
- Revision dùng cache cũ, không materialize; orphan schema chỉ chấp nhận đúngrun/method/device
  và3 null cost field. Timestamp phục hồi tách inference gốc. Source model/evaluator forward
  vẫn là hàm frozen; code revision chỉ journal/schema. Chờ đọc trạng thái thật sau declaration.

## Phase29 — revision r1 đã khai báo và đang continuation

- Declaration ở revisions/test_schema_r1/declaration.json; evaluator revision
  `8a0c613037ef5360c683c865fd348ec69b113cfc9a106bdf577529313f981145`.
 21 test/0skip và coverage93,4959% schema/journal PASS trước declaration.8 FILES đã pin,
  không sửa/format runner/auditor/recovery/tests/INI/authorization trong declaration.
- Orphan đã finalize từ saved4911 output, không model construction hoặc forward thêm.
  Original failed seal/43 claim/42 result và null telemetry giữ hash.
- Controller continuation tool session95003 đang chạy, snapshot10/17 result. Trạng thái thực
  đọc revisions/test_schema_r1/active_controller.json và gate/state.json; không khởi động
  controller, coverage writer hoặc postpipeline thứ hai khi queue còn sống. Không tự retry
  nếu failed/consumed partial claim. Root checkpoint counts42/43/17 là snapshot incident.
- Khi17 xong/controller thoát: auditor scripts.verify_phase29_test_r1 chỉ saved outputs,
  rồi report scripts mới resolve result_refs từ unified audit. Không dùng auditor cũ cho
  final aggregate vì original Power seal được giữ failed. Report/QA/release vẫn chưa xong.

## Phase29 COMPLETE — ngày20/10/2026

- Revision test_schema_r1 được người dùng duyệt và hoàn tất: orphan finalize từ4.911 output
  cũ, không forward lại;17/17 run chưa claim đã xong. Hai controller finished/PID=null,
  không resume bất kỳ queue train/TEST/waiter lịch sử nào. Không train hoặc TEST lại.
- 108 LSTM selection/108 strict native-CPU receipts,183.159 validation prediction PASS.
  TEST chung60 unique member/111.900 prediction row ×3horizon,3 batch gốc/count1.
  Gold/BIS giữ evaluated; **Power seal gốc vẫn failed_sealed/count1**,43 claim/42 result gốc
  giữ hash. Ledger revision evaluated ghi completion hiệu lực riêng,0 additional batch.
  Không sửa failed seal thành evaluated hoặc chạy lại orphan/claim đã consumed.
- Orphan original train/RAM/VRAM vẫn null, qualityn3/costn2; GPU→CPU FAIL Phase28 còn nguyên.
  Timestamp schema-finalization khác inference cũ. Evaluator revision8a0c613037ef5360c683c865fd348ec69b113cfc9a106bdf577529313f981145;
  8 FILES trong declaration và69 source train/EVAL cũ giữ nguyên, không sửa/format.
- 366 test duy nhất/0skip; coverage core90,3581%, revision93,4959%, report89,8574%.
  11.340 protected file trong6 khóa Phase22–28 và raw/V2/Ch5 preservation PASS.
  Không ghi đè XML/coverage/proof đã khóa. Unified auditor chỉ đọc saved predictions;
  auditor TEST cũ giữ lịch sử, không dùng cho aggregate revision.
- Khóa6.197 file `artifacts/manifests/phase29/experiment_lock.json`, SHA-256
  `1dbed9e911025069644e4cf74638ff427e6d79b0686d710d86581efed1b58143`, verify-lock PASS.
  Bao gồm source/tests/docs/report/model/metric/prediction/evidence đã ref; đổi cần revision
  mới giữ bản cũ. Checkpoint root COMPLETE. Check chỉ-đọc `scripts/check_phase29.ps1 -Distribution Ubuntu`.
- Manuscript hiện hành `report/sections/v3/ch04_rnn_lstm.md`, chọn qua active_report.json;
  RNN Phase28 không đổi.7 CSV/9 PNG+SVG đã xem/QA PASS;3 notebook/18 checkpoint slot CPU PASS.
  Registry trained/evaluated60 member riêng initialized Phase25, default seed42 cố định.
  Demo thực tế NumPy CPU, không gọi là native framework GPU/HTTP/React/Render live.
- Bàn giao `docs/phase29_report.md`, `docs/phase29_operations_r1.md`. Runtime vẫn Ubuntu/
  user tuananh; wrapper bắt buộc -Distribution Ubuntu, không doctor/bootstrap cũ.
  Phase30 chỉ khi được yêu cầu; API/UI32–33, tích hợp/build/render DOCX34–35 chưa thực hiện.

## Phase30 — đang nghiệm thu cuối ngày20/10/2026

- Source adapter mới `src/ch05_knowledge_rag/`; không sửa source/artifact đã khóa.
  Snapshot11.490 asset PASS, raw Ch5/7config/23metric/10TEST prediction giữ hash,
  run_count1.6.045 saved predictions được audit không model/TEST forward.
- 3 dataset-tab descriptor/15 pipeline contract slot;10 QA available và5 Wikidata
  unavailable cho QA. Wikidata chỉ structural browser10entity/2.056claim, không tạo
  benchmark QA thứ ba. Index cũ load qua namespace term_paper, không fit/re-serialize.
- 341 unique test/0skip, coverage89,2791% combined (statement92,1376%, branch80,5970%);
 3 notebook/10 QA slot+10 entity CPU PASS. Giữ4 warning sklearn preprocessorV2.
- Manuscript active `report/sections/v3/ch05_knowledge_rag_r2.md`,7 PNG đã xem/QA PASS.
  Presentation r2 giữ r1/metric/prediction; sửa font/label và scope TEST vs challenge:
  entity-linking TEST0/1.053 +challenge8/8, aggregate gốc8/1.061 không đổi.
- Final verifier `scripts.verify_phase30 --lock` đang chạy, tool session27364 chỉ snapshot.
  Đọc checkpoint/process thật trước khi chạy tiếp, không chạy writer thứ hai hoặc sửa
  source/evidence đang được khóa. Chưa COMPLETE trước lock+verify PASS.
- Wrapper bắt buộc -Distribution Ubuntu/user tuananh; không bootstrap/doctor cũ.
  API contract local không đồng nghĩa HTTP/React/Render live. API/UI32–33, DOCX34–35.
  Không tự bắt đầu31; bàn giao docs/phase30_report.md và phase30_operations.md.

## Phase30 COMPLETE — ngày20/10/2026

- Khóa12.153 file `artifacts/manifests/phase30/experiment_lock.json`, SHA-256
  `d04a28e060105dda17c8bf1212068e051dcea5780a25ccb4defc16cf316655ca`, verify-lock PASS;
  checkpoint COMPLETE. Không resume verifier/release writer/session27364 lịch sử.
  Check chỉ-đọc `scripts/check_phase30.ps1 -Distribution Ubuntu`; không chạy coverage/
  producer vào file đã khóa. Source/tests/docs/report/evidence đổi cần revision mới.
- 341 unique test/0skip (78Phase30 +263regression), coverage89,2791% combined;
  statement92,1376%,branch80,5970%. XML cuối final-tests-r2.xml/regression-tests.xml,
  coverage final_coverage_r2.json; không ghi đè, không cộng XML RED/development lịch sử.
  Ruff/CLI help/PowerShell parser PASS,4 warning sklearn preprocessorV2 còn nguyên.
- Snapshot11.490 asset SHA481071f65b2c01b8d132532bdaccaa08ff760b153b908bbf1906e72d2f1c310a
  giữ raw Ch5/7config/23metric/10TEST prediction/citation/source cũ; run_count1,6.045 saved
  row audit không model/TEST forward. Spec/data/core544 file, V2/env/uv.lock/Phase29 lock
  bảo toàn. Không tuning/rebuild corpus hoặc chạy lại TEST Ch2/Ch3/Ch4/Ch5.
- Source V3 KG–RAG `src/ch05_knowledge_rag/` và scripts/test Phase30 đã khóa.3 dataset-tab
  descriptor/15 non-neural pipeline contract slot (10QA available/5Wikidata unavailable).
  Wikidata chỉ structural browser10entity/2.056claim; không bịa QA benchmark thứ ba.
  Registry reused riêng, không thay Phase25 initialized hoặc gọi index cũ là model vừa train.
- 3 notebook generator-owned code chạy runpy PASS:10 QA slot và10entity. Actual NumPy CPU/
  JSON browser; không framework GPU hoặc Jupyter UI test. Class joblib cũ load qua bridge
  term_paper, không fit/re-serialize. Loader chỉ4 local index theo manifest pin cứng,
  kiểm6file/role/path/hash/size/budget; không nhận uploaded pickle hoặc path từ request.
- Demo full compact corpus/free-question khác benchmark candidate-per-split/query-ID cũ;
  không gán demo là TEST tương đương. Citation source_sha256 là local chunk container và
  locator chunk/document, URL cấp dataset; không bịa raw locator từng chunk bị lược bỏ.
- Manuscript active `report/sections/v3/ch05_knowledge_rag_r2.md`, chọn active_report.json.
 7 PNG300dpi/SVG đã xem/QA PASS; r1/baseline giữ nguyên. R2 chỉ trình bày/scope:
  entity-linking TEST0/1.053 +challenge8/8 khớp aggregate cũ8/1.061. Không sửa metric/prediction.
- Bàn giao docs/phase30_report.md, phase30_operations.md, contract_extension và
  presentation_revision_r2. Runtime Ubuntu/user tuananh; -Distribution Ubuntu bắt buộc,
  không doctor/bootstrap cũ. Tiếp31 chỉ khi được yêu cầu; HTTP/React32–33, DOCX34–35 chưa làm.

## Phase31 — lịch sử trước nghiệm thu,20/10/2026

- Active taskset_v2/input_views_v2/results_v2;300 task/3 miền,720 TRAIN-dev và180 TEST
  tác tử đã xong/count1. Không gọi lại --stage test, train/tuning/TEST Ch2–5.
  Declaration b05d6003eabe626caa75bccc269805ac1e3c6ede94f70e8b86863cfe8271619a pin16source;
  không sửa/format source/evaluator/auditor/tests/XML/coverage trong declaration.
- 352 test/0skip, coverage core91,5294%;9 demo slot/3 notebook CPU TRAIN-only;900 saved
  outputs được audit. V1/results là lịch sử development, không cộng vào900 nghiệm thu.
  Raw/V2/Ch5/8dependency locks giữ hash trước phát triển, final phải kiểm lại29.004file.
- Active presentation_r2 dùng active_report_r2.json, manuscript ch06_multi_agent_r2.md.
  Root active_report.json/report_generation.json/r1 giữ lịch sử và hash. R2 chỉ ghi rõ
  router/reporter node duration0 chưa instrument (không phải số đo0ms) và kết quả containment;
  metric/trace/task/rubric không đổi.5PNG active đã xem/QA PASS,1trace figure mới/4 reuse.
- Final packager scripts.release_phase31 bổ sung closure report/bibliography, giữ frozen
  scripts.verify_phase31.py nguyên byte. Chỉ COMPLETE sau experiment_lock+verify thật.
  Không chạy acceptance/coverage/release writer thứ hai trong lúc packager còn sống.
  Snapshot kiểm đúng module: WSL PID1360/tool session79611, đang hash5.000/29.004;
  đọc process thực khi tiếp tục; không suy từ PID/session lịch sử hoặc mở writer thứ hai.
- Local deterministic NumPy CPU/record-bound, không LLM/key/HTTP/React/Render live.
  A0/A1 benign8/8 nhưA2; lợi ích A2 chỉ containment numeric/citation tamper được khai báo.
  Không xem tool parity là predictive accuracy. API32/UI33/DOCX34–35 chưa làm.

## Phase31 COMPLETE — ngày20/10/2026

- 300 task/3miền, mỗi miền100/60-20-20 group split;720 development+180 TEST=900result.
  Agent TEST count1/180approvedpair đã hoàn tất. Không gọi lại stage test/reset claim,
  không train/tuning/TEST Ch2–5. Source16/evaluator/auditor/tests/protocol/inputs/XML/
  coverage đã pin trong declarationb05d6003eabe626caa75bccc269805ac1e3c6ede94f70e8b86863cfe8271619a;
  không sửa/format, kể cả scripts.verify_phase31.py. Thay đổi cần revision giữ evidence.
- Khóa1.709file ở artifacts/manifests/phase31/experiment_lock.json, SHA-256
  10f0196e8fb340e398146654896d845f65c4230231143c739ce5acb328e455b3;
  verify-lock PASS/checkpoint COMPLETE, packager exit0. Không resume PID1360/session79611
  lịch sử. Kiểm chỉ-đọc scripts/check_phase31.ps1 -Distribution Ubuntu; không ghi XML/
  coverage hoặc chạy producer vào artifact đã khóa.
- 352unique test/0skip, core coverage91,5294%combined/94,0199%statement/85,4839%branch;
 3notebook/9CPU TRAIN-only slot PASS,5PNG active QA PASS. Giữ4warning sklearnV2.
 29.004 protected files/8parent locks PASS; V2/raw/Ch5 count1 và Power failed seal/
  null telemetry Phase29 giữ hash. Không thay env/dependency hoặc commit/reset/cleanup.
- Active manuscript report/sections/v3/ch06_multi_agent_r2.md qua active_report_r2.json.
  Root active_report.json/report_generation.json giữ r1 lịch sử, không dùng làm active khi
  tích hợp Ch6. R2 chỉ node timing0 chưa đo riêng/containment prose; metric/trace nguyên vẹn.
 9 non-neural function contract (layers/parameters null),3dataset card/2CSV/bibliography mới.
- Core là deterministic local role-orchestration, không LLM/key/hệ tự chủ tổng quát.
  Models3 scratch seed42 đã khóa, actual serving NumPy CPU. MedQuAD exact chunk lookup,
  không QA/RAG TEST mới; Gold/BIS observation TRAIN-origin, không dữ liệu thị trường live.
  A0/A1 benign100%nhưA2; A2 chỉ chặn tamper challenge đã khai báo. Không tuyên bố cải thiện
  predictive accuracy. Router/reporter node duration0 mặc định chưa instrument; wall latency
  tổng đo riêng. Child RSS không PSS và không cộng parent+child thành peak đồng thời.
- Catalog/agent_task/trace contract local, chưa HTTP/React/Render live. API32 cần pin
  catalog/registry, worker riêng (không fork từ threaded handler), giữ deadline/rate/budget;
  UI33 dùng3dataset/A0-A2 trace. DOCX34–35 chưa tích hợp. Tiếp32 chỉ khi được yêu cầu.
  Đọc docs/phase31_report.md và docs/phase31_operations.md khi bàn giao.

## Phase32 COMPLETE — ngày21/10/2026

- Backend mới apps/api/v3/, không sửa API V2. Active registry_v3.json SHA256
  6e4233331107779adcff20b6461223f2de6d2e52794bc95fb73443887411398f;
  766asset/60slot (36neural seed42,15KG,9agent),480run descriptor. Không thay
  initialized registry25; metric/history không phải kết quả mới train.
- Khóa1.645file artifacts/manifests/phase32/experiment_lock.json, SHA256
  6491a5dce969f2fc4028bfcbf29ae261ca193670304676625c98f9e66a8a8eee;
  verify-lock PASS/checkpoint COMPLETE. Không sửa/format source/scripts/tests/docs/
  XML/coverage/probe/package đã khóa; thay đổi cần revision, giữ bằng chứng cũ.
  Chỉ đọc scripts/check_phase32.ps1 -Distribution Ubuntu, không rerun producer.
- 359unique test/0skip (91acceptance+5auditor+263regression), coverage88,6989%
  combined/90,6533%statement/83,1429%branch. AST/Ruff/schema/PS+Bash PASS;
  static type checker chưa cấu hình, secret scan chỉ new Python source.
  Giữ4warning sklearnV2.30.713protected file/9parent locks PASS trước/sau.
  Không train/tuning/TEST Ch2–6 hoặc thay env/uv.lock/namespace cũ.
- HTTP CPU18case/60slot:55success+5WikidataQA unavailable đúng thiết kế, browser
  structural có dữ liệu. Native localGPU12case/36slot:24CUDA+12scratchCPU,
  36parity rtol1e-4/atol1e-5 PASS trên TRAIN/parentTRAIN. Không fallback hoặc
  gọi CPU portable là native TensorFlow/PyTorch timing; không accuracy/TEST mới.
  GPUv2 startup log gián đoạn giữ riêng trong interruptions theo docs, không PASS
  hoặc lặp TEST. Source/package không đổi trong lượt smoke chạy lại.
- CPU budget448MiB/60s, GPU4GiB/300s; FinQA peak sampled PSS401,04MiB, nativeGPU
  1.757,98MiB không VRAM. Excludes master/OS/peak giữa0,1s; không cloud SLA.
  Unit harness2GiB không là Render fit proof. Streaming text<=50 giữ full index/
  ranking/corpus và exact parity, không rebuild/index fit. Ch5 free-question khác
  historical benchmark, Wikidata không QA benchmark thứ ba; Ch6 ID-bound không LLM.
- Package activev2 (active_package.json):808file/87.996.158expanded/74.864.102ZIP,
  archive SHA256 1f38247bf5b2a4a1b1a8036d234e8e1bcfb34931a59d4c41655e6d5da319db54.
  26CPUdependency subset uv.lock; chưa fresh CPU env/cloud deploy. Blueprint
  deploy/v3/render.yaml dành compact repo, không root render.yaml V2. Không tự push,
  tạo service, đổi tài khoản/gói trả phí. NumPy CPU inference, không GPU trên Render.
- Job capability X-Client-Token crypto random>=128bit (24byte→48hex khuyến nghị),
  required Idempotency-Key, owner-scoped polling/details/cancel/trace. Phase33 giữ
  token sessionStorage, không URL/log; đọc OpenAPI active thay vì legacy contract.
  SQLite32retained/TTL30min ephemeral, một Gunicorn worker2threads/supervisor flock,
  một job process group tuần tự; không tăng worker/replica mà chưa revision queue.
  Artifact mismatch không crash loop; strict input/CORS/rate/hash/path/budget;
  không endpoint train/TEST/admin/uploaded pickle hoặc client shell/URL/path.
- Historical recovered Power/RNN/Torch/s17 metric có3nullcost nguyên vẹn;
  qualityn3/costn2, failed seal/count1/43claim cũ không đổi. UI phải tách live
  serving telemetry khỏi chi phí train và historical metric/benchmark scope.
- Runtime vẫn Ubuntu/user tuananh, -Distribution Ubuntu bắt buộc; không doctor/
  bootstrap cũ. Local scripts/run_api_v3.ps1 -Mode cpu|local_gpu -Port 5000;
  docs/phase32_operations.md, phase32_report.md và contract_extension bàn giao.
  React33 và DOCX34–35 chưa làm; tiếp33 chỉ khi người dùng yêu cầu. Không resume
  session/PID smoke/release lịch sử hoặc tự train/TEST/commit/reset/cleanup.

## Phase33 COMPLETE — ngày21/10/2026

- Active React UI apps/web/src/v3/, entrypoint src/App.tsx; legacy UI còn làm tham chiếu,
  snapshot artifacts/manifests/phase33/web_before.zip. Không xóa hoặc dùng legacy entrypoint
  để ghi đè UI V3. Sáu tab chương/ba dataset, RNN/LSTM toggle, run-all cùng input, trace,
  data/function/history/deploy. Ch1 chỉ case study lịch sử, không train.
- Khóa140file artifacts/manifests/phase33/experiment_lock.json, SHA256
  526c4248bf14175336bdc529c0bb8decc2fde98e19593d305a20c766798d3252;
  release/check hash PASS, checkpoint COMPLETE. Không sửa/format source/scripts/docs/tests/
  XML/coverage/evidence đã khóa; đổi cần revision, giữ bản cũ. Check chỉ-đọc
  scripts/check_phase33.ps1 -Distribution Ubuntu. Không chạy producer vào acceptance cũ.
- 101unique test/0skip:60unit+10legacy+23E2E+8auditor; UI V3 coverage97,06%statement,
  88,72%branch,95,51%function,97,52%line. Lint/type/build/Ruff/AST/5PS/YAML PASS,
  npm audit snapshot0vulnerability. Bảy final PNG đã xem/seal; Chromium headless desktop/
  mobile emulation, không mọi browser/device hoặc full WCAG certification.
- Active acceptance-v3/e2e-v3 source fingerprint
  622536a29e86a67dd5f149d1c1f252f7b236e98cb625a7dfd2d3eeb2fda3fb50.
  18live case=12neural TRAIN+3agent parent_train+3KG demo_not_benchmark, không gọi tất cả
  là TRAIN. input_split authoritative, scope template cũ được giải thích ở scope_clarification.
  60slot=55success+5WikidataQA unavailable; neural parity với Phase32 CPU, không TEST mới.
- Bảo toàn31.641file/10parent locks trước/sau PASS; không train/tuning/TEST Ch2–6.
  CPU serving là NumPy portable của weights scratch/Keras/Torch, không native timing.
  KG demo khác benchmark; agent ID-bound deterministic, không LLM. Null cost/Power failed
  seal giữ hash, không thay0. Node duration0 chưa instrument không phải số đo0ms.
- Preview ZIP dist/phase33/web-preview-acceptance-v3.zip SHA256
  ed820c8dc1c7d3b47cee9fe320a23e4b1706e3ab95d32cd5d579a1a92f4c652c,
  build local API127.0.0.1:5000. Deploy Render cần build APIHTTPS/CORS đúng; blueprint mới
  deploy/web-v3/, không rootV2. Chưa cloud deploy/push/tạo service/upgrade trả phí/DOCX.
- Runtime Node22.23.4 portable .local; run_web_v3.ps1 -Action dev; backend
  run_api_v3.ps1 -Mode cpu|local_gpu -Distribution Ubuntu. Không doctor/bootstrap Python cũ.
  API QA2942/session64348 đã dừng đúng identity/exit0; không resume PID/session QA lịch sử.
  Token sessionStorage, không URL/log/localStorage; không lưu private input hoặc uploaded
  pickle/path. Refresh GET-only không re-POST. TTL30phút/ephemeral, không hệ tài khoản.
- Bàn giao docs/phase33_report.md, phase33_operations.md. Tiếp34 chỉ khi người dùng yêu cầu,
  tích hợp/build/render DOCX34–35 chưa làm. Không commit/reset/cleanup hoặc chạy lại TEST.

## Phase34 COMPLETE — ngày22/10/2026

- Active nội dung ở report/phase34/manuscript.md qua report/active_manuscript_v3.json.
  Dùng publication_order trong artifacts/manifests/phase34/manuscript_manifest.json
  khi ghép Word; không ghép cả manuscript và sections. Ch3 active r2, Ch4 combined,
  Ch5 r2, Ch6 active_report_r2; bản gốc vẫn frozen. Ch1 history cập nhật đúngV3,
  ImageNet chỉ metadata/không ảnh local. Mở đầu/Kết luận mới,18card/36contract.
- Khóa226file artifacts/manifests/phase34/experiment_lock.json SHA256
  e4ba90714b4cd42a46eca8702f3c6b3dc2e0ddf1a11141e1df3944c56af8ebbc;
  release/public verify PASS/checkpoint COMPLETE/PIDnull. Manuscript SHA256
  dcb895acfd76f1ad616baecd7fdc7fa099becbc0cc508a80b3c0432eabef2b19.
  Không sửa/format source/docs/input/report/test/XML/coverage/evidence/active pointer
  đã khóa; đổi cần revision giữ bản cũ. Check chỉ đọc scripts/check_phase34.ps1
  -Distribution Ubuntu; không chạy producer vào acceptance đã phát hành.
- 38test r3 PASS/0skip, coverage92,7512% ba module editor/assembler/auditor, mỗi module
  >80%; AST/Ruff/format8filePython/PSparser PASS, static type checker chưa cấu hình.
  Active acceptance-tests-r3.xml/acceptance_coverage_r3.json/lint-r3.json. R1/r2 và
  source_review_r1/r2.zip giữ lịch sử. R2 bổ sung bằng chứng20–23; r3 integration ghi
  fixture TemporaryDirectory riêng đã xác minh phạm vi, không overwrite publication.
- 6chương/58mục,143bảng captioned (67main+76appendix),37hình,43citation,55localtargets
  audit PASS;43bảng gốc giữ nguyên. 54requirement có locator/proof, không gọi DOCX/
  cloud end-to-end PASS. Outline extension34.integration.1 không sửa outline/spec22.
  Phụ lục D trích5method frozen line/hash; không framework/model/TEST execution.
-31.772protected file/11parent locks trước/sau PASS; nativeWindows independent
  hash cross-check cũng PASS. Không train/tuning/forward validation/TEST Ch2–6,
  không đổi raw/V2/Ch5 count1/env/uv.lock/namespace/Power failed seal/null cost.
  Ch4 giữ qualityn3/costn2; CPU NumPy khác nativeTensorFlow/Torch timing; KG compact
  khác benchmark; agent ID-bound deterministic, không LLM; node0 uninstrumented.
- Mục triển khai cuối Ch2–6 cập nhật API32/UI33 đã kiểm local; chưa clouddeploy,
  không chương deploy riêng. Chưa có DOCX/pagecount/render/Word QA. Front matter,
  contents/figures_and_tables/references và4appendix sẵn cho35; không gán pagebudget
  thành số trang thật. Đọc docs/phase34_report.md, phase34_operations.md và README.
- A06 reference SHA9eecf073897b609d9e2d0024bd56594dc6fec99823508e57ed79dff8d4780348
  giữ nguyên. report/phase34/artifact.md chỉ structural typography/geometry/text,
  không full template distillation đã render; direct formatting/theme còn cần QA.
  Phase35 đọc documents skill hiện hành, resolve workspace dependencies/bundled renderer;
  loader/renderer chưa có trong tool34. Không dùng desktop Office hoặc env tạm để giả
  PASS render. Dựng file mới releases/v3/, không ghi đèV2/A06; xem mọi trang trước giao.
- Không có queue train/TEST/API/UI của34 cần resume; audit/native/tests/release đều
  đã thoát. Không resume tool session/PID lịch sử. Runtime vẫn Ubuntu/user tuananh,
  -Distribution Ubuntu bắt buộc, không doctor/bootstrap cũ. Tiếp35 chỉ khi người dùng
  yêu cầu; không tự commit/reset/cleanup hoặc triển khai cloud trả phí.

## Phase35 IN_PROGRESS — preflight ngày22/10/2026

- Đọc docs/phase35_checkpoint_20261022.md và artifacts/manifests/phase35/checkpoint.json
  trước khi tiếp tục. Public check34 PASS226file, manuscript/A06 giữ hash; chưa tạo DOCX,
  PDF, ảnh trang hoặc release. Không gọi COMPLETE/Word-open/render PASS.
- Documents skill hiện hành yêu cầu workspace dependency runtime/bundled renderer.
  Phiên preflight không có loader/runtime tool/resource, Word control không có phiên
  kết nối; plugin search không cung cấp đường thay thế phù hợp. Không tự dùng env repo,
  Python Windows/desktop Office/LibreOffice để vượt gate. Cần runtime hợp lệ hoặc người
  dùng đồng ý rõ deviation dựng local có khóa phiên bản trước khi cấu hình phương án đó.
- Marker DOCX chưa chạy vì chưa authoring. Khi runtime có, render toàn bộ A06 rồi distill,
  working-copy template, publication_order34, fields/navigation, render/xem từng trang,
  tests/smoke/release/hash. Không sửa file khóa34 trở về trước hoặc ghi đè V2/A06.
- Không có queue train/TEST/render/authoring để resume. Chỉ có audit hash đọc file trong
  preflight; trạng thái kết thúc ghi receipt. Không dùng session/PID lịch sử để chạy lại.
- Preserve native Windows PASS31.848file/12khóa, exit0, receipt preservation_20261022.json.
  Auditor WSL trùng được agent dừng đúng process/SIGTERM, không hash mismatch/không PASS;
  cả hai đã thoát. Không resume tool session/PID audit. Chưa có authoring/render process.

## Phase35 — runtime được duyệt, đang dựng Word ngày22/10/2026

- Preflight phía trên là lịch sử. Người dùng đồng ý toolchain tài liệu local riêng và
  giữ thông tin bìa A06. Xem docs/phase35_local_toolchain_authorization.md.
  Dùng scripts/run_docs_v3.ps1, Ubuntu/user tuananh; không sửa env GPU/uv.lock.
  Docvenv riêng /home/tuananh/.local/share/ai-term-paper-docs-v1/.venv.
- Rootless Ubuntu LO thất bại, giữ metadata r1. Active TDF26.2.6.3 official/hash-pinned
  ở local_toolchain_r2/probe.json; Poppler24.02.0; runtime_ready.json.
  Không chạy lại installer/relocate hoặc ghi đè receipt chỉ vì log fail lịch sử.
- A06 render32trang đã xem từng trang; template_inventory.json và report/phase35/artifact.md
  là full distillation. Theme thực Calibri; bảng/công thức mẫu là ảnh. Bản mới dùng native
  tables/OMML và sửa trang trống/mục lục/số trang, giữ các pattern còn lại.
- Marker đã chạy thành công đúng1lần: artifact_operation_started.json; không chạy lại.
  Builder scripts/phase35_docx.py; candidate-r1/r2/r3 dưới report/build/phase35/ chỉ là
  ứng viên. R1 thiếu32caption alt được test bắt; r2 đủ180caption/144table/37image;
  r3 sửa bookmark span/REF và đang render. Không giao ứng viên như release.
- Development46test PASS, còn nghiệm thu cuối. Word16 mở r2 read-only PASS203trang,
  file giữ hash; chưa phải final Word QA. Lỗi COM Quit thiếu by-ref để lại phiên rỗng
  đã xác minh và đóng riêng; không kill/đóng Word người dùng. Script đã sửa.
- Đọc checkpoint/process thật khi resume, không dựa PID/session lịch sử. Còn page-map,
  final build/render/xem mọi trang, tests/coverage/audits, smoke localAPI/UI, preservation
 31.848file/12lock và release/hash/hướng dẫn. Không train/tuning/TEST/cloud.

## Phase35 COMPLETE —22/10/2026, trạng thái hiện hành

- Đã phát hành `releases/v3/Tieu_luan_AI_6_chuong.docx`,202trang, SHA-256
  `5daf2aa5b5f587be5f61ecf7a2c6d32dc131c9ae2efe5df8630b4a23387060a5`.
  PDF QA/release_manifest cùng thư mục. Candidate-r12 là nguồn copy đã nghiệm thu;
  r1–r11 và thông báo IN_PROGRESS/runtime block phía trên chỉ còn lịch sử.
- QA đủ202/202trang, Word16 read-only PASS202trang/field-error-index0/hash unchanged;
  native144bảng/37hình+logo/180caption/549bookmark/12OMML,256pagecache đúng.
 82test/0skip PASS, coverage84,8925%combined/80,4270%branch;23E2E/0retry PASS local
  Reactproduction+compactAPI Linuxext4. Không cloud/fresh CPU-only/SLA hoặc TEST replay.
- Khóa391file `artifacts/manifests/phase35/release_lock.json`, SHA-256
  `3d66f57de0d5bd48f19b15eaf75c92619519ab9c29a1beb11b469512ea47adab`;
  verify PASS. Không sửa/format source/tests/docs/QA/evidence/release đã khóa. Dùng
  `scripts/check_phase35.ps1 -Distribution Ubuntu` hash-only; sửa cần revision mới.
  Không ghi đè final_tests_r2.xml/final_coverage_r2.json; r1thất bại giữ lịch sử.
- Bảo toàn31.848file/12khóa cha PASS; GPU/uv.lock/V2/raw/checkpoint/TEST giữ nguyên.
  Không resume bất kỳ queue/Word/server/installer/session lịch sử; task không còn
  process Word ẩn hoặc server5000/5173. Không train/tuning/TEST/commit/reset/cleanup.
- Đọc `docs/phase35_report.md`, `phase35_operations.md`, `demo_v3.md`. Toolchaindoc riêng
  đã được duyệt, không reinstall hay chạy marker lần hai. TOC materialized REF/PAGEREF,
  không tự thêm heading; thay nội dung phải render/QA lại revision. Không save đè release.
- Probe Word đầu có thể để Options.UpdateLinksAtOpen=False mà thiếu before snapshot;
  đã công khai ở bàn giao. Không tự đoán giá trị cũ để đảo lại. Script cuối không đổi
  tùy chọn này, mọi probe đóng không lưu file. Cloud V3 vẫn chưa deploy/nghiệm thu.

## Render monorepo revision r1 — local verification PASS,22/10/2026

- Người dùng yêu cầu sửa source để deploy cùng repo lên hai service Render Free hiện có.
  Root `render.yaml` đã chuyển V3, bản trước ở `deploy/render-v3-r1/render-v2-before.yaml`.
  Không sửa source/artifact/khóa Phase22–35. Không commit/push hoặc sửa account Settings.
- `deploy/render-v3-r1/api-bundle.zip` là bản sao byte-identical gói CPU Phase32/package_v2,
  SHA-256 `1f38247bf5b2a4a1b1a8036d234e8e1bcfb34931a59d4c41655e6d5da319db54`,74864102byte.
  Git theo dõi ZIP trực tiếp, không force-add model/raw hoặc dùng LFS pointer.11JSON Wikidata
  trong data/raw là runtime browser allowlist, không tải lại raw dataset.
- `scripts/render_v3.py build|start|check` staging riêng `.render-v3/` ignored; kiểm ZIP/member/
  manifest/hash và source Python trong checkout. Backend frozen đổi cần revision/gói mới,
  không âm thầm phục vụ ZIP cũ; React vẫn build từ apps/web trong commit hiện hành.
  Không chạy `build` trong GPU env: nó cài CPU lock. Render dùng Python3.11.17/NumPy CPU.
- 46unit/integration PASS, coverage96,3134%combined;8E2E/20live slot PASS trên CPU-only QA
  venv riêng26dependency hash-locked;4neural TRAIN+FinQA demo+Gold agent parent-TRAIN.
  Không scientific TEST/train/nativeGPU hoặc cloud/SLA.31848protected file/12lock và
  Phase35 release391file vẫn PASS. Receipt artifacts/manifests/render_v3_r1/verification.json.
- Handoff `deploy/render-v3-r1/README.md`, docs/render_v3_r1_operations.md. Hai service thủ công
  cần owner đổi Build/Start/Environment một lần; root YAML không tự sửa Dashboard. Không tự
  tạo service, nâng plan hoặc resume server/installer QA theo PID lịch sử. QA tmp riêng giữ
  trong /tmp/ai-paper-render-v3-r1-*; không thay runtime GPU Ubuntu/user tuananh.
