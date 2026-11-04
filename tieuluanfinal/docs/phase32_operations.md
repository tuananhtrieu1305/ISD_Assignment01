# Phase32 — hướng dẫn vận hành backend V3

Backend mới nằm ở `apps/api/v3/`, không thay API V2 `apps/api/app.py`.
React V3 thuộc Phase33; DOCX thuộc Phase34–35. Chưa triển khai lên tài khoản Render.
Nghiệm thu cuối phải đọc `artifacts/manifests/phase32/verification.json` và checkpoint,
không coi log development hoặc tài liệu này thay cho release lock.

## Chạy local

Mở PowerShell tại `C:\DATA\assign`:

```powershell
.\scripts\run_api_v3.ps1 -Mode cpu -Port 5000 -Distribution Ubuntu
```

Hoặc kiểm tra native GPU bằng hai môi trường WSL đã khóa:

```powershell
.\scripts\run_api_v3.ps1 -Mode local_gpu -Port 5000 -Distribution Ubuntu
```

Mở `http://localhost:5000/health`, `/ready` hoặc `/api/v3/openapi.json`.
Đây là API JSON, không phải trang React. Dừng server bằng Ctrl+C.
Wrapper bind127.0.0.1; `-CorsOrigins` nhận danh sách origin chính xác, mặc định
localhost/127.0.0.1:5173. Không dùng wildcard hoặc slash cuối origin.
Runtime hiện hành là distro **Ubuntu**, user tuananh. Không dùng Python Windows,
distro Ubuntu-24.04 cũ hoặc bootstrap/doctor ghi đè evidence môi trường đã khóa.

CPU phục vụ ba bộ weights train độc lập bằng NumPy portable; tên implementation
scratch/Keras/PyTorch chỉ nguồn huấn luyện. Kết quả có actual_backend/device riêng.
Local GPU dispatch TensorFlow/Keras và PyTorch/CUDA vào hai venv riêng tuần tự;
scratch vẫn NumPy CPU. Không fallback âm thầm. Không dùng timing portable để kết
luận tốc độ native framework. HTTP driver không import TensorFlow/PyTorch.

## Registry và hợp đồng cho frontend

`active_package.json` chọn packagev2; `registry_v3.json` có60slot/766asset,
86.079.357byte,480descriptor run lịch sử. SHA256 registry:
`6e4233331107779adcff20b6461223f2de6d2e52794bc95fb73443887411398f`.
36 neural checkpoint seed42,15 KG–RAG slot và9 agent slot dùng lại3checkpoint.
Không nhầm registry initialized Phase25 với checkpoint đã train.

- GET `/api/v3/chapters`, `/datasets`, `/models`, `/runs` và detail tương ứng.
- GET `/api/v3/datasets/{id}/overview`: card/EDA/sample; `/results`: bảng đã lưu.
- GET `/api/v3/models/{id}/contract`: hợp hàm/từng hàm/mapping framework.
- GET `/api/v3/artifacts/{id}` và `/content`: metadata hoặc nội dung allowlisted.
- POST `/api/v3/comparisons`: chạy các implementation cùng input.
- POST `/api/v3/agent-tasks`: request tác tử; GET `/jobs/{id}` để poll,
  `/jobs/{id}/details` để đọc evidence/telemetry và `/agent-traces/{id}` để đọc trace.
- POST `/api/v3/jobs/{id}/cancellations` để hủy, body theo OpenAPI và cùng token owner.
- OpenAPI self-contained tại `artifacts/manifests/phase32/openapi.json` hoặc HTTP.
  JSON body3.0.0, serving extension3.1.0; schemas Phase22 không bị sửa.

Client tạo token mật mã ít nhất128bit, ví dụ24byte random thành48ký tự hex,
gửi header `X-Client-Token` cho tạo/đọc/hủy job và trace. Server chỉ lưu SHA256.
`Idempotency-Key` bắt buộc8–128ASCII, scope theo owner; cùng key khác payload409.
Poll đúng `poll_url` và giữ cùng token. Không đặt token/input vào URL hoặc log.
Phase33 nên giữ token trong sessionStorage; đây là capability, không hệ tài khoản.

Run URL thêm suffix split để validation/TEST không trùng ID; metric JSON gốc
không sửa. Orphan Power/RNN/PyTorch/seed17 TEST dùng metric phục hồi riêng đã khóa,
ba chi phí train/RAM/VRAM vẫn null; không chuyển Power failed seal gốc thành PASS.
Baseline classical/causal nằm trong bảng lịch sử; live neural comparison là3implementation.
Wikidata chỉ structural browser,5 QA slot unavailable là đúng, không QA benchmark thứ ba.
Ch5 compact free-question demo khác benchmark lịch sử. Ch6 deterministic ID-bound,
không LLM; node duration0 chưa instrument không có nghĩa đo được0ms.

## Giới hạn và xử lý lỗi

SQLite single host, tối đa32job còn giữ, TTL30phút, storage64MiB, output2MiB.
DB mặc định `/tmp/ai-paper-v3/jobs.db`, ephemeral; redeploy không durable queue.
Folder0700/db0600, secure_delete không phải bảo đảm forensic purge. Restart đánh
dấu lượt đang chạy failed, không tự lặp inference. Một Gunicorn worker/2HTTPthreads,
một supervisor exclusive flock, một job process group tuần tự. Không tăng workers
hoặc scale replica khi chưa thiết kế lại queue/ownership.

CPU deadline60s, budget448MiB; GPU300s/4GiB. Monitor mỗi0,1s cộng PSS web worker
và job group, RSS fallback có cờ; không gồm Gunicorn master/OS/CUDA VRAM, có thể bỏ
peak giữa mẫu. Timeout/cancel/memory kích TERM/KILL và reaping, không crash loop.
`/health` vẫn bind khi registry hỏng; `/ready` báo degraded/503, hash cache30s;
asset hỏng chỉ làm slot liên quan unavailable, inference kiểm hash lại khi load.

JSON6,4MB, một input/batch, ảnh RGB PNG/JPEG tối đa4Mpixel/4,5MiBdecoded;
shape/feature/finite/schema kiểm nghiêm. Không request path/URL/pickle/shell,
không train/TEST/admin hoặc fault injection HTTP. CORS exact allowlist/no credentials;
rate240request/phút/IP với1024bucket; không tin X-Forwarded-For, nên proxy có thể
trở thành giới hạn chung. Không gửi bệnh án/secret; không chẩn đoán hoặc tư vấn đầu tư.
Sai input trả structurederror; thiếu/corrupt artifact không tạo fake prediction.

## Gói Render

Gói active `dist/phase32/api-bundle-v2.zip`:808file,87.996.158byte expanded,
74.864.102byte ZIP. SHA256:
`1f38247bf5b2a4a1b1a8036d234e8e1bcfb34931a59d4c41655e6d5da319db54`.
Chỉ runtime closure và asset allowlisted, không raw train/cache/TEST predictions/
notebook/full repository. CPU26dependency đúng version/hash subset uv.lock,
không cài Torch/TensorFlow/Keras trên Render. Bundle checker kiểm từng member.

Giải nén thành repo compact riêng, giữ đường dẫn; làm theo `deploy/v3/README.md`.
Blueprint `deploy/v3/render.yaml`, không root render.yaml V2. Owner cần tự chọn repo,
xem plan/region, đặt AI_CORS_ORIGINS đúng frontend và kiểm health/readiness.
Không tự tạo service, push repo, đổi account hoặc nâng gói trả phí.
HTTP local trên compact project không chứng minh đã cài fresh CPU env hoặc deploy
Render thành công; thư viện dùng trong probe đến từ WSL env khóa có sẵn.

## Kiểm chứng và giới hạn bằng chứng

Sau release, chỉ đọc hash bằng:

```powershell
.\scripts\check_phase32.ps1 -Distribution Ubuntu
```

Không ghi đè XML/coverage/probe/package đã khóa; không chạy train/TEST cũ.
Coverage acceptance88,6989% combined (statement90,6533%, branch83,1429%).
359test duy nhất/0skip (91acceptance+5auditor+263regression); native GPU12case/
36slot parity PASS với24CUDA và12scratchCPU. CPU18case/60slot gồm5WikidataQA
unavailable đúng thiết kế, không phải55model mới train.
Unit/integration có fixture và budget harness2GiB vì pytest còn import loader cũ;
không dùng harness làm bằng chứng448MiB. Live Gunicorn CPU18case riêng giữ đúng
budget448MiB: FinQA peak sampled401,04MiB, medical288,72MiB. Đây là proxy local,
không cloud SLA/free-tier guarantee. Timing batch1 gồm cold load/process/poll,
không benchmark5warmup/30repeat hay p95.

Lịch sử TDD/development FAIL giữ riêng, không cộng trùng vào acceptance. Hai lần
FinQA vượt guard dẫn đến streaming top-k text allocation, không đổi index/corpus/
ranking/answer; exact parity đã kiểm. Log GPU bị gián đoạn được giữ nguyên riêng;
xem `phase32_gpu_probe_interruption.md`. Trạng thái final trong verification.json.
Preservation kiểm30.713 file/9khóa; giữ raw/V2/Ch5/Power failed seal/null telemetry.

Nguồn tham khảo triển khai: [Render Flask](https://render.com/docs/deploy-flask),
[Blueprint](https://render.com/docs/blueprint-spec),
[Flask security](https://flask.palletsprojects.com/en/stable/web-security/).
Context7 không khả dụng, dùng tài liệu chính thức. Skill API/security/TDD/verification
đã chi phối request guards, test RED→GREEN và kiểm chứng trước release; không là
chứng nhận audit bảo mật toàn hệ thống hay quét CVE/history.
