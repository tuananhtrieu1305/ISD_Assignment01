# Hợp đồng serving Phase32 — revision3.1.0

Không chỉnh `docs/contracts/v3/openapi.json` hoặc schemas Phase22. Hàm
`apps.api.v3.openapi.specification()` tạo bản self-contained OpenAPI3.1.1,
info.version3.1.0; JSON body tiếp tục schema_version3.0.0.

## Những khác biệt được khai báo

| Thành phần | Quy tắc triển khai |
|---|---|
| Catalog/chapter/dataset/model | Envelope/pagination theo Phase22; dataset trả chính contract bên trong source manifest, không trả wrapper thu nhận |
| Dataset Ch6 | Catalog overlay riêng phản ánh100task/miền đã tạo ở31; manifest declared cũ giữ nguyên |
| Contract mô hình | Neural dùng model schema cũ; KG/Agent dùng non-neural contract version Phase30/31, layers/parameters null |
| Job ownership | Header X-Client-Token32–128ký tự, tạo crypto random>=128bit ở client; server chỉ lưu SHA256; mọi job/details/cancel/trace phải cùng owner |
| Idempotency | Header bắt buộc8–128ASCII ký tự; scope theo owner; khác payload409; key không phải quyền đọc job |
| Run ID | URL `<original_run_id>_<split>` duy nhất; list trả descriptor, GET trả metric JSON nguyên nội dung/nullable recovery gốc; không đổi metric.run_id |
| Artifact | GET metadata data-only descriptor; `/content` attachment chỉ JSON/CSV/MD/PNG allowlisted; không weights/pickle/path động |
| Overview | `/datasets/{id}/overview` trả card/EDA/sample cùng derived overlay; Ch1 metadata-only có thể không có sample chạy |
| Results | `/datasets/{id}/results` trả schema_version `phase32.result_index.1` tới bảng JSON/CSV đã khóa, kèm dataset/domain filter hint; không chạy evaluator để tạo số mới |
| Job details | `/jobs/{id}/details` trả evidence/graph/agent action messages/serving telemetry; không chain-of-thought |
| OpenAPI | `/api/v3/openapi.json` trả đúng spec runtime; localrefs đã bundle, không fetch schema online |

Catalog công khai; job có capability riêng, không hệ tài khoản/đăng nhập. HTTP public
demo không nhận bệnh án/secret, không cung cấp chẩn đoán/khuyến nghị đầu tư. Không
có API train/TEST/admin/network/tool command từ câu hỏi. Token không đặt querystring,
không ghi payload/header vào log. Không cookie/credential CORS nên không có phiên
cookie cần CSRF; Origin lạ bị403, response content JSON/attachment và nosniff.

Request errors dùng api#error3.0.0:400malformed/key/token/query,403origin,404unknown/
not-owned,409idempotency,413body,415MIME,422schema/shape,429rate,500sanitized,
503registry/asset/queuebudget. Liveness/metadata vẫn bind được khi registry hỏng;
missing slot báo unavailable, không fake prediction. Ready hash cache30s, inference
kiểm hash lại khi nạp. Chưa có bảo đảm cloud SLA hoặc persistence qua redeploy.

Model summary.backend là **serving backend**; contract.backend mô tả implementation
huấn luyện. CPU deploy NumPy portable cho3bộ weights train độc lập, không timing native.
Local_gpu dispatch riêng Keras TensorFlow/PyTorch/CUDA; scratch luôn CPU. Default42
không được chọn lại theo TEST; rolling checkpoints không dùng live. Baseline classical/
causal hiện ở metric lịch sử, primary live comparison là3neural implementation.

Ch5 free-question demo khác evaluator lịch sử; structural-only không fakeQA. Streaming
loader mới giữ exact index/corpus/algorithm và citation cũ, chỉ đổi allocation. Ch6 vẫn
deterministic ID-bound, không LLM hoặc suy luận tự do. Action message là input/output
công cụ, không chain-of-thought. Node duration0 có thể chưa instrument, không0ms đo.

## Blueprint và quyền deploy

`deploy/v3/render.yaml` dành cho compact project do package_phase32 tạo. RegionSingapore,
CPU/free,1gunicorn worker+2HTTPthreads; job exec riêng. Health `/health`, diagnostic
`/ready`. Python/dependency subset hash-lock từ uv.lock; không Torch/TF/Keras trên Render.
Không tự thay root render.yaml cũ, không tự tạo service/tính phí/push repo/account.
Frontend Phase33 đặt URL API/CORS đúngorigin, đọc cùng spec và headerownership.

## Registry v3 và kết quả lịch sử

Active registry_v3.json có480descriptor run,60model/pipeline slot và766asset.
Run ID URL chứa split chỉ là alias; không sửa metric gốc. Bổ sung metric TEST
phục hồi orphan Power/RNN/PyTorch/seed17 từ revision được duyệt Phase29, không
forward lại. Ba chi phí train/RAM/VRAM null giữ nguyên; failed seal gốc vẫn failed.
Danh sách bảng kết quả là artifact lịch sử, không live model accuracy.
Wikidata results chỉ graph statistics; không gán QA scorecard của2miền khác.
Ch5 có cờ `live_demo_equivalent_to_historical_benchmark:false`; frontend cần hiển thị
khác biệt scope này thay vì coi free-question demo là lần TEST tương đương.
