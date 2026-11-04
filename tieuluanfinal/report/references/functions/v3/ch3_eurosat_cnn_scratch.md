# ch3_eurosat_cnn_scratch

đầu vào → Tìm đặc trưng trong vùng ảnh [32, 32, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32, 32, 8] → Tìm đặc trưng trong vùng ảnh [32, 32, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32, 32, 8] → Rút gọn vùng ảnh [16, 16, 8] → Tìm đặc trưng trong vùng ảnh [16, 16, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16, 16, 16] → Tìm đặc trưng trong vùng ảnh [16, 16, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16, 16, 16] → Rút gọn vùng ảnh [8, 8, 16] → Tìm đặc trưng trong vùng ảnh [8, 8, 32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8, 8, 32] → Rút gọn vùng ảnh [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [10] → đầu ra (logit/giá trị chuẩn hóa)

`F = dense_16 ∘ activation_15 ∘ dense_14 ∘ pooling_13 ∘ activation_12 ∘ conv2d_11 ∘ pooling_10 ∘ activation_9 ∘ conv2d_8 ∘ activation_7 ∘ conv2d_6 ∘ pooling_5 ∘ activation_4 ∘ conv2d_3 ∘ activation_2 ∘ conv2d_1`



| Hàm | Vai trò | Input → Output | Tham số |
|---|---|---|---:|
| conv2d_1 | Tìm đặc trưng trong vùng ảnh | ['batch', 32, 32, 3] → ['batch', 32, 32, 8] | 224 |
| activation_2 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 0 |
| conv2d_3 | Tìm đặc trưng trong vùng ảnh | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 584 |
| activation_4 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 0 |
| pooling_5 | Rút gọn vùng ảnh | ['batch', 32, 32, 8] → ['batch', 16, 16, 8] | 0 |
| conv2d_6 | Tìm đặc trưng trong vùng ảnh | ['batch', 16, 16, 8] → ['batch', 16, 16, 16] | 1168 |
| activation_7 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 0 |
| conv2d_8 | Tìm đặc trưng trong vùng ảnh | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 2320 |
| activation_9 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 0 |
| pooling_10 | Rút gọn vùng ảnh | ['batch', 16, 16, 16] → ['batch', 8, 8, 16] | 0 |
| conv2d_11 | Tìm đặc trưng trong vùng ảnh | ['batch', 8, 8, 16] → ['batch', 8, 8, 32] | 4640 |
| activation_12 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8, 8, 32] → ['batch', 8, 8, 32] | 0 |
| pooling_13 | Rút gọn vùng ảnh | ['batch', 8, 8, 32] → ['batch', 32] | 0 |
| dense_14 | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 |
| activation_15 | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 |
| dense_16 | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 10] | 330 |

## conv2d_1

`conv2d(x, weights) -> y` — Tìm đặc trưng trong vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[conv2d]', 'keras': 'keras.layers.Conv2D', 'pytorch': 'torch.nn.Conv2d'}

Tìm đặc trưng cục bộ bằng bộ lọc trượt trên ảnh.

`y = conv_same(x, W) + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; conv_same: trượt bộ lọc 3×3, đệm 0 để giữ kích thước ảnh.

Shape [32, 32, 3] → [32, 32, 8] cho một mẫu; batch được giữ nguyên.

## activation_2

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## conv2d_3

`conv2d(x, weights) -> y` — Tìm đặc trưng trong vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[conv2d]', 'keras': 'keras.layers.Conv2D', 'pytorch': 'torch.nn.Conv2d'}

Tìm đặc trưng cục bộ bằng bộ lọc trượt trên ảnh.

`y = conv_same(x, W) + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; conv_same: trượt bộ lọc 3×3, đệm 0 để giữ kích thước ảnh.

Shape [32, 32, 8] → [32, 32, 8] cho một mẫu; batch được giữ nguyên.

## activation_4

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## pooling_5

`pooling(x, weights) -> y` — Rút gọn vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[pooling]', 'keras': 'keras.layers.MaxPooling2D/GlobalAveragePooling2D', 'pytorch': 'torch.nn.MaxPool2d/AdaptiveAvgPool2d'}

## conv2d_6

`conv2d(x, weights) -> y` — Tìm đặc trưng trong vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[conv2d]', 'keras': 'keras.layers.Conv2D', 'pytorch': 'torch.nn.Conv2d'}

Tìm đặc trưng cục bộ bằng bộ lọc trượt trên ảnh.

`y = conv_same(x, W) + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; conv_same: trượt bộ lọc 3×3, đệm 0 để giữ kích thước ảnh.

Shape [16, 16, 8] → [16, 16, 16] cho một mẫu; batch được giữ nguyên.

## activation_7

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## conv2d_8

`conv2d(x, weights) -> y` — Tìm đặc trưng trong vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[conv2d]', 'keras': 'keras.layers.Conv2D', 'pytorch': 'torch.nn.Conv2d'}

Tìm đặc trưng cục bộ bằng bộ lọc trượt trên ảnh.

`y = conv_same(x, W) + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; conv_same: trượt bộ lọc 3×3, đệm 0 để giữ kích thước ảnh.

Shape [16, 16, 16] → [16, 16, 16] cho một mẫu; batch được giữ nguyên.

## activation_9

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## pooling_10

`pooling(x, weights) -> y` — Rút gọn vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[pooling]', 'keras': 'keras.layers.MaxPooling2D/GlobalAveragePooling2D', 'pytorch': 'torch.nn.MaxPool2d/AdaptiveAvgPool2d'}

## conv2d_11

`conv2d(x, weights) -> y` — Tìm đặc trưng trong vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[conv2d]', 'keras': 'keras.layers.Conv2D', 'pytorch': 'torch.nn.Conv2d'}

Tìm đặc trưng cục bộ bằng bộ lọc trượt trên ảnh.

`y = conv_same(x, W) + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được; conv_same: trượt bộ lọc 3×3, đệm 0 để giữ kích thước ảnh.

Shape [8, 8, 16] → [8, 8, 32] cho một mẫu; batch được giữ nguyên.

## activation_12

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## pooling_13

`pooling(x, weights) -> y` — Rút gọn vùng ảnh.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[pooling]', 'keras': 'keras.layers.MaxPooling2D/GlobalAveragePooling2D', 'pytorch': 'torch.nn.MaxPool2d/AdaptiveAvgPool2d'}

## dense_14

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [32] → [32] cho một mẫu; batch được giữ nguyên.

## activation_15

`activation(x, weights) -> y` — Giữ tín hiệu dương, tạo khả năng học phi tuyến.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[activation]', 'keras': 'keras.layers.ReLU', 'pytorch': 'torch.nn.ReLU'}

## dense_16

`dense(x, weights) -> y` — Kết hợp các đặc trưng.

Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối.

Mapping: {'scratch': 'src.common.numpy_engine.NumpyNetwork.forward[dense]', 'keras': 'keras.layers.Dense', 'pytorch': 'torch.nn.Linear'}

Kết hợp các giá trị đầu vào bằng trọng số rồi cộng bias.

`y = xW + b`

x: tensor đầu vào (x_t: tại bước t); y: tensor đầu ra; W: trọng số đầu vào; b: bias học được.

Shape [32] → [10] cho một mẫu; batch được giữ nguyên.
