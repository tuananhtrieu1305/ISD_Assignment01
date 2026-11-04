# ch4_gold_pink_sheet_rnn_scratch

đầu vào → Nhớ thông tin theo thời gian [24, 32] → Nhớ thông tin theo thời gian [24, 32] → Nhớ thông tin theo thời gian [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

`F = dense_8 ∘ activation_7 ∘ dense_6 ∘ activation_5 ∘ dense_4 ∘ rnn_3 ∘ rnn_2 ∘ rnn_1`

Ở mỗi tầng l=1..3, lặp t=1..T theo thứ tự; khởi tạo h (và c) bằng 0 cho mỗi window. Tầng 1–2 trả toàn chuỗi, tầng 3 trả bước cuối → 3 Dense.

| Hàm | Vai trò | Input → Output | Tham số |
|---|---|---|---:|
| rnn_1 | Nhớ thông tin theo thời gian | ['batch', 24, 4] → ['batch', 24, 32] | 1184 |
| rnn_2 | Nhớ thông tin theo thời gian | ['batch', 24, 32] → ['batch', 24, 32] | 2080 |
| rnn_3 | Nhớ thông tin theo thời gian | ['batch', 24, 32] → ['batch', 32] | 2080 |
| dense_4 | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 |
| activation_5 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 |
| dense_6 | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 |
| activation_7 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 |
| dense_8 | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 |

## rnn_1

`rnn(x, weights) -> y` — Nhớ thông tin theo thời gian.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[rnn]', 'keras': 'keras.layers.SimpleRNN', 'pytorch': 'torch.nn.RNN'}

Kết hợp dữ liệu hiện tại và thông tin nhớ từ bước trước.

`h_t = tanh(x_t W + h_previous U + b)`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; h_t: trạng thái ở bước t; h_previous: trạng thái bước trước, bắt đầu bằng 0; U: trọng số trạng thái; t: chỉ số bước thời gian; tanh: hàm ép giá trị vào khoảng -1 đến 1.

Shape [24, 4] → [24, 32] cho một mẫu; batch được giữ nguyên.

## rnn_2

`rnn(x, weights) -> y` — Nhớ thông tin theo thời gian.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[rnn]', 'keras': 'keras.layers.SimpleRNN', 'pytorch': 'torch.nn.RNN'}

Kết hợp dữ liệu hiện tại và thông tin nhớ từ bước trước.

`h_t = tanh(x_t W + h_previous U + b)`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; h_t: trạng thái ở bước t; h_previous: trạng thái bước trước, bắt đầu bằng 0; U: trọng số trạng thái; t: chỉ số bước thời gian; tanh: hàm ép giá trị vào khoảng -1 đến 1.

Shape [24, 32] → [24, 32] cho một mẫu; batch được giữ nguyên.

## rnn_3

`rnn(x, weights) -> y` — Nhớ thông tin theo thời gian.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[rnn]', 'keras': 'keras.layers.SimpleRNN', 'pytorch': 'torch.nn.RNN'}

Kết hợp dữ liệu hiện tại và thông tin nhớ từ bước trước.

`h_t = tanh(x_t W + h_previous U + b)`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; h_t: trạng thái ở bước t; h_previous: trạng thái bước trước, bắt đầu bằng 0; U: trọng số trạng thái; t: chỉ số bước thời gian; tanh: hàm ép giá trị vào khoảng -1 đến 1.

Shape [24, 32] → [32] cho một mẫu; batch được giữ nguyên.

## dense_4

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [32] → [16] cho một mẫu; batch được giữ nguyên.

## activation_5

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_6

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [16] → [8] cho một mẫu; batch được giữ nguyên.

## activation_7

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_8

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [8] → [3] cho một mẫu; batch được giữ nguyên.
