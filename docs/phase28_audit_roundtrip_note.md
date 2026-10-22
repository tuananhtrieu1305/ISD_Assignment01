# Phase28 — sửa đối chiếu metric sau JSON round-trip

Ngày18/10/2026. Không sửa source train, evaluator tạo prediction, metric, checkpoint,
spec/core/data lock hoặc r2 native-CPU export gate.

Hậu kiểm đầu tiên dừng với `Run metric/schema mismatch` ở Power. Lượt đại diện
`ch4_household_power_rnn_scratch_s17_main` lưu metric theo horizon1/6/24, nhưng
`validation_details.json` có các khóa chuỗi đã sort thành1/24/6. Dựng lại list từ
dictionary rồi so sánh thứ tự list tạo false mismatch, dù metric có cùng ý nghĩa.

Auditor cũ chưa thuộc52 source train hoặc revision r2 đã khóa. Bản byte-identical
được giữ ở `artifacts/manifests/phase28/attempts/auditor_metric_order_v1.py`, SHA-256
`35f40f70b78cd27154c8b73e9a241941b0e8cd9f8cd7e46016ecf01c924c5b9f`.

Auditor hiện hành ghi revision `phase28.metric-order-roundtrip.2`. Nó đối chiếu từng
row đầy đủ theo khóa `(name,horizon)`, không phụ thuộc thứ tự serialize dictionary;
từ chối row trùng, thiếu/thừa hoặc thay đổi value/unit/direction/undefined_reason.
Giá trị vẫn khớp chính xác qua canonical JSON, không thêm epsilon hoặc nới tolerance.
Metric gốc không được sắp lại hay ghi đè. Thêm kiểm run_id/dataset_id của metric.

Giữ `metric-order-red-tests.xml` và test mới trong final RNN suite để chứng minh
thay đổi thứ tự được chấp nhận nhưng sai số1e-12 vẫn bị từ chối. Không chạy model
validation/TEST để sửa lỗi audit này; chỉ đọc prediction đã lưu và fixed TRAIN demo.

Lỗi PowerShell `Split-Path $PSScriptRoot '..'` của finish/check cũng đã được sửa
thành resolve đường dẫn cha bằng Join-Path/Resolve-Path. Hai kiểm thử root-expression
được chạy RED rồi GREEN, không thực thi pipeline/model trong test; XML riêng được
đếm một lần trong nghiệm thu. Chúng không sửa runtime hoặc source train đã pin.
