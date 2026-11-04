# Contract V3 — cách sử dụng và giới hạn

Phiên bản 3.0.0. Đây là đặc tả Phase 22; API V3 được implement ở Phase 32.

Schema gốc ở `src/common/schemas/v3/*.schema.json`. Chín file: common, dataset,
split, model, run, artifact, seal, agent, api. OpenAPI ở thư mục này tham chiếu
schema bằng đường dẫn relative local; các schema tham chiếu nhau bằng URN trong
registry offline. Không tạo HTTP request để tìm schema.

Ví dụ ở `examples/` là **synthetic contract fixtures**: hash `aaaa...`, đường dẫn
fixture và metric minh họa không phải dữ liệu/model/result thật. Không được đưa
vào registry live, UI production hoặc bảng kết quả báo cáo. Artifact/data/run/model
đều có `evidence_kind`; publish gate bác bỏ `synthetic_fixture`. API examples chỉ
là wire-format fixtures, không phải file để tự động seed production jobs.

```python
from src.common.contracts import validate_document

validate_document("model", model_contract)
validate_document("run", run_manifest, publish=True)
validate_document("api", comparison_request)
validate_document("api#job", job_response)
```

JSON Schema bác bỏ missing/extra fields, version sai, hash/path sai, input quá
lớn, công thức thiếu giải thích, v.v. Semantic guard bác bỏ layer count giả,
parameter total sai, backend/dataset/family sai, temporal target overlap, incomplete
job được nhận thành công, thiếu error, invalid probability sum, trace sai thứ tự
hoặc vai trò, checkpoint thiếu CPU-safe loader. NaN/Infinity bị cấm trước validate.

`check_seal_transition` chỉ kiểm tra đề nghị chuyển trạng thái; không ghi file,
không tự tăng counter và **không có quyền mở TEST**. Executor/locking/atomic event
log phải được implement ở Phase 25. Ch5 dùng seal cũ nguyên byte, không convert
đè bằng schema mới. `historical_baseline` adapter phải trỏ hash bản gốc.

## Trách nhiệm chưa thể thay thế bằng schema

- Phase 23: tải đúng nguồn, kiểm tra license và hash/bytes thật, chống ZIP traversal.
- Phase 24: kiểm tra ID/group/duplicate/window thật; schema thời gian không tự biết
  liệu feature có dùng tương lai hay scaler đã fit vào TEST.
- Phase 25: đối chiếu tensor shape/parameter/bias/gate layout/gradient thật và
  triển khai TEST gate atomic. Model contract không tự chứng minh code có đủ layer.
- Phase 26–31: chạy thực nghiệm thật, không biến fixture thành kết quả.
- Phase 32: feature whitelist/shape/units registry, image magic bytes/dimensions,
  safe serialization/hash allowlist, job resource/ownership/TTL/idempotency,
  schema response thực tế và OpenAPI integration tests.
- Phase 33–35: frontend/report đọc đúng artifact, review khả năng đọc hiểu và QA.

`jsonschema` và `referencing` hiện có sẵn và đã khóa transitively trong uv lock
Phase 21; không cài thêm dependency hoặc thay lock trong Phase 22. Khi nâng lõi
runtime ở Phase 25, khai báo direct dependencies nếu đưa guards vào production.

## Khóa và thay đổi

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase22 --lock
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase22
```

`--lock` chỉ tạo khóa lần đầu. Nếu file đã khóa thay đổi, verifier báo lỗi và
không ghi đè lock. Sửa đặc tả phải có biên bản deviation/version mới, ghi rõ đã
hay chưa xem TEST và ảnh hưởng dữ liệu/model/report/UI. Không nới schema theo
kết quả TEST cho vừa mô hình. File lock không tự cho phép trả lời mới hoặc mở TEST.
