# ch4_household_power_lstm_scratch

đầu vào → Giữ/quên thông tin bằng bộ nhớ và cổng [168, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [168, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

`F = dense_8 ∘ activation_7 ∘ dense_6 ∘ activation_5 ∘ dense_4 ∘ lstm_3 ∘ lstm_2 ∘ lstm_1`

Ở mỗi tầng l=1..3, lặp t=1..T theo thứ tự; khởi tạo h (và c) bằng 0 cho mỗi window. Tầng 1–2 trả toàn chuỗi, tầng 3 trả bước cuối → 3 Dense.

| Hàm | Vai trò | Input → Output | Tham số |
|---|---|---|---:|
| lstm_1 | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 168, 14] → ['batch', 168, 32] | 6016 |
| lstm_2 | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 168, 32] → ['batch', 168, 32] | 8320 |
| lstm_3 | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 168, 32] → ['batch', 32] | 8320 |
| dense_4 | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 |
| activation_5 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 |
| dense_6 | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 |
| activation_7 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 |
| dense_8 | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 |

## lstm_1

`lstm(x, weights) -> y` — Giữ/quên thông tin bằng bộ nhớ và cổng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[lstm]', 'keras': 'keras.layers.LSTM', 'pytorch': 'torch.nn.LSTM'}

Chọn thông tin cần giữ, bổ sung và xuất qua các cổng.

`(i,f,g,o) = (sigmoid,sigmoid,tanh,sigmoid)(x_t W + h_previous U + b); c_t = f*c_previous + i*g; h_t = o*tanh(c_t)`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; h_t: trạng thái ở bước t; h_previous: trạng thái bước trước, bắt đầu bằng 0; U: trọng số trạng thái; t: chỉ số bước thời gian; i,f,o: cổng nhận, quên, xuất trong 0..1; g: ứng viên bộ nhớ; c_t: bộ nhớ mới; c_previous: bộ nhớ bước trước, bắt đầu bằng 0; sigmoid: hàm ép vào khoảng 0 đến 1; tanh: hàm ép vào khoảng -1 đến 1; *: nhân từng phần tử.

Shape [168, 14] → [168, 32] cho một mẫu; batch được giữ nguyên.

## lstm_2

`lstm(x, weights) -> y` — Giữ/quên thông tin bằng bộ nhớ và cổng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[lstm]', 'keras': 'keras.layers.LSTM', 'pytorch': 'torch.nn.LSTM'}

Chọn thông tin cần giữ, bổ sung và xuất qua các cổng.

`(i,f,g,o) = (sigmoid,sigmoid,tanh,sigmoid)(x_t W + h_previous U + b); c_t = f*c_previous + i*g; h_t = o*tanh(c_t)`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; h_t: trạng thái ở bước t; h_previous: trạng thái bước trước, bắt đầu bằng 0; U: trọng số trạng thái; t: chỉ số bước thời gian; i,f,o: cổng nhận, quên, xuất trong 0..1; g: ứng viên bộ nhớ; c_t: bộ nhớ mới; c_previous: bộ nhớ bước trước, bắt đầu bằng 0; sigmoid: hàm ép vào khoảng 0 đến 1; tanh: hàm ép vào khoảng -1 đến 1; *: nhân từng phần tử.

Shape [168, 32] → [168, 32] cho một mẫu; batch được giữ nguyên.

## lstm_3

`lstm(x, weights) -> y` — Giữ/quên thông tin bằng bộ nhớ và cổng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[lstm]', 'keras': 'keras.layers.LSTM', 'pytorch': 'torch.nn.LSTM'}

Chọn thông tin cần giữ, bổ sung và xuất qua các cổng.

`(i,f,g,o) = (sigmoid,sigmoid,tanh,sigmoid)(x_t W + h_previous U + b); c_t = f*c_previous + i*g; h_t = o*tanh(c_t)`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; h_t: trạng thái ở bước t; h_previous: trạng thái bước trước, bắt đầu bằng 0; U: trọng số trạng thái; t: chỉ số bước thời gian; i,f,o: cổng nhận, quên, xuất trong 0..1; g: ứng viên bộ nhớ; c_t: bộ nhớ mới; c_previous: bộ nhớ bước trước, bắt đầu bằng 0; sigmoid: hàm ép vào khoảng 0 đến 1; tanh: hàm ép vào khoảng -1 đến 1; *: nhân từng phần tử.

Shape [168, 32] → [32] cho một mẫu; batch được giữ nguyên.

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
