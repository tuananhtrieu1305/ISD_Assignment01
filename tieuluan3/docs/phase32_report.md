# Biên bản nghiệm thu Phase32 — Python API V3

Ngày thực hiện20–21/10/2026. Các gate kiểm thử và bảo toàn bên dưới đã PASS.
Hiệu lực phát hành/COMPLETE được xác nhận riêng bằng `verification.json`, checkpoint
và hash-only check PASS; biên bản này được đưa vào khóa phát hành, không tự chứa hash của nó.
Không train, tuning hoặc mở lại TEST Ch2–6; chưa làm React33 hay DOCX34–35.

## Kết quả triển khai

Backend mới `apps/api/v3/` cung cấp catalog6chương/18dataset,36neural seed42,
15pipeline KG–RAG và9agent slot,480descriptor run lịch sử. Registry v3 gồm766asset,
86.079.357byte; trained checkpoints riêng registry initialized Phase25.
Data overview, hợp hàm/từng hàm, contract, bảng kết quả và artifact nội dung được
serve từ nguồn đã khóa, không tạo metric mới qua TEST evaluator.

Live comparison nhận cùng một input, chạy tuần tự3implementation neural hoặc
5KG/3agent pipeline; async job/poll/details/trace. CPU là portable NumPy cho các
weights train độc lập. Native local GPU dùng TensorFlow/Keras và PyTorch/CUDA
qua2env WSL riêng; scratch CPU. Backend/device/timing thực nằm trong response.
Một driver single-threaded cho job, không fork trong threaded HTTP handler.

Job có capability ownership/idempotency, TTL/capacity và storage/output budget;
strict JSON/schema/shape/finite/MIME, CORS exact allowlist, rate limit, sanitizeerror,
path/hash/size allowlist và CPU-safe load. Không request URL/pickle/path/shell,
không endpoint train/TEST/admin. Artifact hỏng làm slot unavailable/readiness503,
liveness vẫn bind; worker chết không để job queued vô hạn. Timeout/cancel/memory
kết thúc process group, không tự retry inference hoàn tất.

Wikidata là browser10entity,5QA slot unavailable đúng thiết kế, không QA benchmark
thứ ba. Ch5 demo free-question khác historical candidate-per-split benchmark.
Ch6 deterministic ID-bound, không LLM; node duration0 chưa instrument không là
0ms đã đo. Classical/causal baselines chỉ có kết quả lịch sử, không live3neural.

## Kiểm chứng

| Bằng chứng | Kết quả |
|---|---|
| Acceptance unit/integration/security |91PASS,0skip — acceptance-tests-v1.xml |
| Auditor unit |5PASS,0skip — release-unit-final.xml |
| Regression API/contracts/data/environment/scratch |263PASS,0skip — regression-tests.xml |
| Tổng testcase duy nhất |359, không cộng XML TDD/development hoặc chạy trùng |
| Coverage backend dòng+nhánh |88,6989%; statement90,6533%; branch83,1429% |
| HTTP Gunicorn CPU packagev2 |18case;55slot thành công,5WikidataQA unavailable đúng kỳ vọng |
| HTTP native local GPU packagev2 |12case/36slot PASS;24CUDA+12scratchCPU,36parity PASS, không fallback |
| Bảo toàn dependency |30.713unique file/9khóa22/24–31 PASS trước và sau |
| AST/Ruff/entrypoint/schema |PASS; OpenAPI refs self-contained, PS/Bash parser PASS |
| Secret pattern scan |0pattern trong new Python source; không scan Git history/CVE database |

4warning sklearn preprocessor V2 còn nguyên, không nâng dependency/re-serialize.
Static type checker chưa cấu hình; dùng AST/runtime/schema, không gọi đó là typecheck.
Unit integration có fixture và harnessbudget2GiB do pytest import loader lịch sử;
chỉ live Gunicorn probe riêng dùng budget CPU448MiB, không nhập nhằng hai bằng chứng.

CPU live FinQA peak sampled web+job PSS401,04MiB; medical288,72MiB; neural183,99–191,59MiB.
Monitor0,1s, không gồm Gunicorn master/OS/CUDA VRAM và có thể bỏ peak giữa mẫu.
HTTP coldwall batch1 khoảng3,11–7,15s trong lần CPU này, không p95/SLA hoặc benchmark
5warmup/30repeat. Đây là local proxy, không chứng minh free-tier Render luôn đủ RAM.
Không cài fresh CPU-only env trong phase này; compact project chạy với env WSL đã khóa.

Ngưỡng parity nativeGPU↔portable của từng checkpoint được khai báo trước smoke:
rtol1e-4/atol1e-5. Không so3weights train độc lập như thể cùng mô hình; không nới ngưỡng,
tuning hoặc đổi checkpoint. Đây là TRAIN smoke, không accuracy hoặc TEST mới.
GPU live peak sampled web+job PSS cao nhất1.757,98MiB, dưới budget4GiB;
không phải allocator VRAM. HTTP coldwall khoảng21,75–29,61s, không latency kernel
thuần. Driver không import native framework; mỗi implementation native chạy
trong process riêng rồi thoát. Receipt CPU/GPU đều ghi cloud_deployed=false.

## Các vấn đề đã xử lý, vẫn giữ lịch sử

- TDD RED/import/SQL/manifest-wrapper/contract errors giữ XML riêng; chỉ acceptance
  cuối tính359test. Không sửa XML cũ để biến FAIL thành PASS.
- FinQA dev1 vượt memory guard khi loader decode toàn corpus/nạp2miền; dev2 chỉ
  stream theo miền vẫn456,85MiB. Bản cuối giữ full index/ranking/corpus hash nhưng
  chỉ cache union top-k text<=50, exact evidence/graph/prediction parity PASS.
  Không rebuild corpus/index/weights hoặc tăng guard448MiB.
- GPUv2 bị ngắt trước khi có final receipt; không còn process, log startup gốc giữ
  riêng với SHA trong `phase32_gpu_probe_interruption.md`. Chạy lại TRAIN smoke
  nguyên bộ, không ghép lượt dở hoặc lặp TEST lịch sử.
- Registry v3 thêm recovered TEST metric Power/RNN/PyTorch/seed17 từ output đã
  finalize ở29, không forward. Train/RAM/VRAM vẫn null, qualityn3/costn2; original
  failed_sealed/count1/claims cũ không bị sửa thành evaluated.

## Bàn giao deploy và phase tiếp

Package activev2:808file,87.996.158byte expanded,74.864.102byte ZIP;
archive SHA256 `1f38247bf5b2a4a1b1a8036d234e8e1bcfb34931a59d4c41655e6d5da319db54`.
26dependency CPU subset exact uv.lock, không Torch/TF/Keras; Blueprint riêng
`deploy/v3/render.yaml`, build kiểm hash bundle. Không dùng root blueprint V2.
`active_package.json`/`openapi.json` là entrypoint bàn giao cho Phase33.

Gói local không phải service Render live. Chưa tạo service, push repo, dùng tài khoản,
thay plan trả phí hoặc cam kết cloud SLA. Owner xem `deploy/v3/README.md` khi deploy.
Hướng dẫn CPU/GPU/polling/ownership/giới hạn tại `docs/phase32_operations.md`;
khác biệt schema tại `docs/phase32_contract_extension.md`.
Skill API/security/TDD/verification đã chi phối guards, cấu trúc lỗi, các ca kiểm thử
và hash audit trước phát hành; không thay cho audit bảo mật production độc lập.

Sau release chỉ dùng `scripts/check_phase32.ps1 -Distribution Ubuntu` để kiểm hash.
Không ghi đè source/evidence đã khóa; thay đổi cần revision mới. Runtime Ubuntu/user
tuananh, không doctor/bootstrap cũ. Không commit/reset/cleanup dữ liệu người dùng.
Phase tiếp theo là **33 — React UI nhiều tab**, chỉ khi người dùng yêu cầu.
