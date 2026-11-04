# Lượt smoke GPU bị gián đoạn — 21/10/2026

Khi tiếp tục Phase32, tool session5065 không còn tồn tại. Kiểm tra đúng module
`scripts.smoke_phase32` và `apps.api.v3` trong WSL Ubuntu không thấy tiến trình.
Không có `http_gpu_v2.json` hoặc `http_gpu_v2_failure.json`; log chỉ có startup
Gunicorn ngày20/10, không có biên bản hoàn tất. Không suy đoán số case đã chạy.

Giữ log gốc tại
`artifacts/manifests/phase32/interruptions/http_gpu_v2_interrupted_20261020.gunicorn.log`,
SHA256 `3a6b19e85f0defd74da91564b37b932c05e837edbc827181a5c536b8991ec6dd`.
Bundle verification đã PASS được giữ nguyên. Không sửa source đã preflight,
weights, packagev2 hoặc evidence CPU.

Chạy lại smoke TRAIN/parent TRAIN cố định trên cùng package/checkpoint, giữ
rtol1e-4/atol1e-5. Đây là kiểm chứng serving, không phải train/tuning hay mở lại
TEST lịch sử. Biên bản `http_gpu_v2.json` chỉ được tạo khi toàn bộ12case PASS;
không ghép kết quả dở dang hoặc coi lượt gián đoạn là PASS.
