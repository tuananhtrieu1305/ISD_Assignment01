# ch2_bank_marketing_mlp_pytorch

đầu vào → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [1] → đầu ra (logit/giá trị chuẩn hóa)

`F = dense_11 ∘ activation_10 ∘ dense_9 ∘ activation_8 ∘ dense_7 ∘ activation_6 ∘ dense_5 ∘ activation_4 ∘ dense_3 ∘ activation_2 ∘ dense_1`



| Hàm | Vai trò | Input → Output | Tham số |
|---|---|---|---:|
| dense_1 | Kết hợp các đặc trưng | ['batch', 50] → ['batch', 64] | 3264 |
| activation_2 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 |
| dense_3 | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 64] | 4160 |
| activation_4 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 |
| dense_5 | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 32] | 2080 |
| activation_6 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 |
| dense_7 | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 |
| activation_8 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 |
| dense_9 | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 |
| activation_10 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 |
| dense_11 | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 1] | 17 |

## dense_1

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [50] → [64] cho một mẫu; batch được giữ nguyên.

## activation_2

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_3

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [64] → [64] cho một mẫu; batch được giữ nguyên.

## activation_4

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_5

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [64] → [32] cho một mẫu; batch được giữ nguyên.

## activation_6

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_7

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [32] → [32] cho một mẫu; batch được giữ nguyên.

## activation_8

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_9

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [32] → [16] cho một mẫu; batch được giữ nguyên.

## activation_10

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_11

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [16] → [1] cho một mẫu; batch được giữ nguyên.
