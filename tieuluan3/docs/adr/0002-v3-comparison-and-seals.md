# ADR 0002 — Độ sâu thật, matched-track và TEST one-shot

Trạng thái: ACCEPTED, 2026-10-17.

## Quyết định

MLP 6 Dense, CNN 5 Conv + 2 Dense, RNN/LSTM 3 recurrent + 3 Dense. Đếm logical
parameterized layers, không đếm time step, gate, pooling hoặc normalization.
Parameter count/shape/function contract là bằng chứng, không chỉ `len(model.layers)`.

Bảng chính dùng cùng matched train IDs/full validation/TEST cho cả ba implementation;
GPU full-data là bảng phụ nếu scratch không hoàn thành full. Ba seed 17/42/73,
canonical initialization/batch order, cùng optimizer convention/budget. Bias phụ
PyTorch recurrent phải zero/frozen để parameter parity; mọi khác biệt còn lại được
ghi và không nhận là “matched” khi chưa kiểm chứng. 108 neural run là mục tiêu,
không phải kết quả đã có. Timeout/failure không bị loại khỏi báo cáo.

TEST seal khóa manifest của tất cả approved run IDs trước một evaluation batch.
`failed_sealed` vẫn terminal: không sửa code theo TEST rồi reset counter. Mặc định
Phase 28 chỉ validation; Phase 29 khóa cả RNN/LSTM rồi đánh giá TEST chung. Điều
này ngăn việc xem RNN TEST để chọn LSTM. Ch5 không tạo seal mới: giữ run_count=1.

## Hệ quả

Scratch có thể chậm và chất lượng matched-subset thấp hơn full GPU; phải báo riêng,
không dùng hiệu quả hardware khác nhau để tuyên bố thuật toán tốt hơn. Giữ đủ seed
hoặc công bố rõ phần chưa đạt; không tạo mean/std giả. Mọi đổi data cap/budget chỉ
được làm trước TEST, có version và áp dụng công bằng.

## Kiểm chứng

Negative contract tests bác bỏ 5 layer, pooling-as-layer, parameter mismatch,
time overlap, thiếu implementation và reopen TEST. Phase 25–29 bổ sung numerical
gradient/weight-layout/parity kiểm tra tensor thật; Phase 22 chưa thay các test đó.
