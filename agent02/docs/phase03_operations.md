# Bàn giao vận hành AG02 phase 3

Đã COMPLETE 2 baseline, chưa final evaluation. Đọc plan và checkpoint hiện hành
trước khi làm tiếp. Không sửa source/tests/evidence trong declaration hoặc release
lock của phase3; cũng không sửa bất kỳ file đã khóa phase1–2.

Từ `C:\DATA\assign`, PowerShell, runtime đã khóa Ubuntu/tuananh:

```powershell
.\agent02_assignment\scripts\run_agent02_phase03.ps1 -Task status
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase03
```

Auditor chỉ đọc output đã lưu, không train/DEV/final lại. `train` khi cả hai DONE
chỉ kiểm hash rồi reuse. `development` khi COMPLETE cũng chỉ kiểm output cũ.
Không gọi trực tiếp main của `code/agent02_experiment.py`.

## Hai run và dữ liệu dùng lại

- REF: `artifacts/runs/ref/baseline/s0042/`.
- CONTROLLED: `artifacts/runs/controlled/iid/baseline/s0011/`.
- Mỗi run có manifest/claim/completion, 5.000 dòng CSV, Q/policy/visits, trace20,
  checkpoint0 và các checkpoint100…5000; RNG nằm trong checkpoint.
- `segment_*.json` đo CPU/wall từng chunk; không nhầm với wall toàn command.
- `artifacts/metrics/phase03_dev/`: DEV riêng, 100 episode/vai, scenario1000011.
- `artifacts/metrics/phase03_*`: các bảng/analysis đọc từ log, không thêm training run.
- `artifacts/figures/phase03/`: 4 hình, notes và manifest producer. Status producer
  `GENERATED_PENDING_VISUAL_QA` là snapshot trước QA; `evidence/phase03/visual_qa.json`
  và release verification xác nhận QA PASS sau đó. Không sửa ngược snapshot producer.
- Bản thảo: `report/sections/phase03_baseline.md`; PDF/DOCX thuộc phase9–10.

Registry trained có 2 entry, không đổi registry hay protocol bất biến thành trạng
thái mới. Phase4 tạo registry/manifest của phase4, trỏ baseline11 vào đúng checkpoint/
Q/hash/declaration phase3. Không gọi lại helper với declaration mới cho runID cũ:
helper sẽ từ chối registration khác. Chỉ chạy 24 run CONTROLLED chưa có, không
train lại baseline11, không gộp REF42 vào mean/std của 5 seed CONTROLLED.

## Recovery nếu phase sau dùng lại runner persistence

`execute_run` có claim, checkpoint hash và yêu cầu `resume=True` tường minh khi
claim chưa complete. Giữ claim cũ, không xóa hay replay. Kiểm source/spec/config/
declaration hash đúng; lấy checkpoint gần nhất, khôi phục RNG và episode toàn cục,
chỉ chạy phần chưa hoàn tất. Một run DONE phải reuse, kể cả gọi lại với `--resume`.
Không dùng checkpoint smoke. Run mới dùng zero-Q và seed đăng ký.

Mỗi episode kiểm trống ít nhất5GiB trước khi chạy. Khi guard RuntimeError, snapshot
ở episode đã xong và segmentPAUSED được giữ. REF adapter dùng class gốc và loop
giữ đúng thứ tự RNG; kiểm resume/parity đã có trước train. Lỗi khác hoặc checkpoint
partial phải chẩn đoán/revision, không tự sửa/hash lại Q. Chưa có recovery thật của
hai run nghiệm thu; không mô tả fixture như incident thực.

Một writer được thực thi bằng Linux flock ở `evidence/phase03/.writer.lock`.
File có thể còn nhưng handle đã thả khi process thoát; kiểm PID/process và lock
thật, không coi file tồn tại là queue đang sống. Không cài env, sửa pagefile/WSL,
khởi động GPU hoặc dọn raw/cache của bài cũ.

Final evaluation vẫn đóng. Phase5 mới khóa evaluator và journal cho 25 Q; dùng
seed/tape final riêng, 500 episode/vai, giữ nguyên Q và cách xử lý đồng hạng.
DEV phase3 không dùng để chọn alpha/epsilon hoặc chọn lại seed.
