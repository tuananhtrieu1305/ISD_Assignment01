# PHỤ LỤC B. HỢP ĐỒNG HÀM VÀ MÃ NGUỒN

Contract cấu trúc bên dưới lấy từ lõi dùng chung, không coi initialized registry là checkpoint đã train. Checkpoint/kết quả dùng registry thực nghiệm của từng chương. Các hàm chung chỉ giải thích một lần ở thân chương; tại đây giữ shape/parameter cụ thể cho từng dataset. Các mapping chỉ tên API, không ngụ ý ba framework được import trong cùng process.

## B.1. ch2_cdc_diabetes / mlp

đầu vào → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [1] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.1. B.1. ch2_cdc_diabetes / mlp

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| dense_1 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 21] → ['batch', 64] | 1408 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_2 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_3 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 64] | 4160 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_4 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_5 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_6 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_7 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_8 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_9 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_10 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_11 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 1] | 17 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.2. B.1. ch2_cdc_diabetes / mlp

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| dense_1 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_2 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_3 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_4 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_5 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_6 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_7 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_8 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_9 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_10 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_11 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.2. ch2_ames_housing / mlp

đầu vào → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [1] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.3. B.2. ch2_ames_housing / mlp

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| dense_1 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 313] → ['batch', 64] | 20096 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_2 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_3 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 64] | 4160 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_4 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_5 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_6 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_7 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_8 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_9 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_10 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_11 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 1] | 17 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.4. B.2. ch2_ames_housing / mlp

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| dense_1 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_2 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_3 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_4 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_5 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_6 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_7 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_8 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_9 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_10 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_11 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.3. ch2_bank_marketing / mlp

đầu vào → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [64] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [1] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.5. B.3. ch2_bank_marketing / mlp

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| dense_1 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 50] → ['batch', 64] | 3264 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_2 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_3 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 64] | 4160 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_4 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64] → ['batch', 64] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_5 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 64] → ['batch', 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_6 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_7 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_8 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_9 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_10 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_11 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 1] | 17 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.6. B.3. ch2_bank_marketing / mlp

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| dense_1 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_2 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_3 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_4 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_5 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_6 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_7 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_8 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_9 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_10 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_11 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.4. ch3_idrid / cnn

đầu vào → Tìm đặc trưng trong vùng ảnh [128, 128, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [128, 128, 8] → Tìm đặc trưng trong vùng ảnh [128, 128, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [128, 128, 8] → Rút gọn vùng ảnh [64, 64, 8] → Tìm đặc trưng trong vùng ảnh [64, 64, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64, 64, 16] → Tìm đặc trưng trong vùng ảnh [64, 64, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [64, 64, 16] → Rút gọn vùng ảnh [32, 32, 16] → Tìm đặc trưng trong vùng ảnh [32, 32, 32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32, 32, 32] → Rút gọn vùng ảnh [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [5] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.7. B.4. ch3_idrid / cnn

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| conv2d_1 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 128, 128, 3] → ['batch', 128, 128, 8] | 224 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_2 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 128, 128, 8] → ['batch', 128, 128, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_3 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 128, 128, 8] → ['batch', 128, 128, 8] | 584 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_4 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 128, 128, 8] → ['batch', 128, 128, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_5 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 128, 128, 8] → ['batch', 64, 64, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_6 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 64, 64, 8] → ['batch', 64, 64, 16] | 1168 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64, 64, 16] → ['batch', 64, 64, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_8 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 64, 64, 16] → ['batch', 64, 64, 16] | 2320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_9 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 64, 64, 16] → ['batch', 64, 64, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_10 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 64, 64, 16] → ['batch', 32, 32, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_11 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 32, 32, 16] → ['batch', 32, 32, 32] | 4640 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_12 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32, 32, 32] → ['batch', 32, 32, 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_13 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 32, 32, 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_14 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_15 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_16 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 5] | 165 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.8. B.4. ch3_idrid / cnn

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| conv2d_1 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_2 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| conv2d_3 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_4 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_5 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| conv2d_6 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| conv2d_8 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_9 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_10 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| conv2d_11 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_12 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_13 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| dense_14 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_15 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_16 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.5. ch3_eurosat / cnn

đầu vào → Tìm đặc trưng trong vùng ảnh [32, 32, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32, 32, 8] → Tìm đặc trưng trong vùng ảnh [32, 32, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32, 32, 8] → Rút gọn vùng ảnh [16, 16, 8] → Tìm đặc trưng trong vùng ảnh [16, 16, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16, 16, 16] → Tìm đặc trưng trong vùng ảnh [16, 16, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16, 16, 16] → Rút gọn vùng ảnh [8, 8, 16] → Tìm đặc trưng trong vùng ảnh [8, 8, 32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8, 8, 32] → Rút gọn vùng ảnh [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [10] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.9. B.5. ch3_eurosat / cnn

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| conv2d_1 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 32, 32, 3] → ['batch', 32, 32, 8] | 224 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_2 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_3 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 584 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_4 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_5 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 32, 32, 8] → ['batch', 16, 16, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_6 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 16, 16, 8] → ['batch', 16, 16, 16] | 1168 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_8 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 2320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_9 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_10 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 16, 16, 16] → ['batch', 8, 8, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_11 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 8, 8, 16] → ['batch', 8, 8, 32] | 4640 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_12 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8, 8, 32] → ['batch', 8, 8, 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_13 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 8, 8, 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_14 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_15 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_16 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 10] | 330 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.10. B.5. ch3_eurosat / cnn

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| conv2d_1 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_2 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| conv2d_3 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_4 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_5 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| conv2d_6 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| conv2d_8 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_9 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_10 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| conv2d_11 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_12 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_13 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| dense_14 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_15 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_16 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.6. ch3_cifar10 / cnn

đầu vào → Tìm đặc trưng trong vùng ảnh [32, 32, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32, 32, 8] → Tìm đặc trưng trong vùng ảnh [32, 32, 8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32, 32, 8] → Rút gọn vùng ảnh [16, 16, 8] → Tìm đặc trưng trong vùng ảnh [16, 16, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16, 16, 16] → Tìm đặc trưng trong vùng ảnh [16, 16, 16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16, 16, 16] → Rút gọn vùng ảnh [8, 8, 16] → Tìm đặc trưng trong vùng ảnh [8, 8, 32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8, 8, 32] → Rút gọn vùng ảnh [32] → Kết hợp các đặc trưng [32] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [32] → Kết hợp các đặc trưng [10] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.11. B.6. ch3_cifar10 / cnn

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| conv2d_1 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 32, 32, 3] → ['batch', 32, 32, 8] | 224 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_2 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_3 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 584 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_4 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32, 32, 8] → ['batch', 32, 32, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_5 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 32, 32, 8] → ['batch', 16, 16, 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_6 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 16, 16, 8] → ['batch', 16, 16, 16] | 1168 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_8 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 2320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_9 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16, 16, 16] → ['batch', 16, 16, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_10 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 16, 16, 16] → ['batch', 8, 8, 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| conv2d_11 / conv2d(x, weights) -> y | Tìm đặc trưng trong vùng ảnh | ['batch', 8, 8, 16] → ['batch', 8, 8, 32] | 4640 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_12 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8, 8, 32] → ['batch', 8, 8, 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| pooling_13 / pooling(x, weights) -> y | Rút gọn vùng ảnh | ['batch', 8, 8, 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_14 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 32] | 1056 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_15 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 32] → ['batch', 32] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_16 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 10] | 330 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.12. B.6. ch3_cifar10 / cnn

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| conv2d_1 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_2 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| conv2d_3 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_4 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_5 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| conv2d_6 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| conv2d_8 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_9 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_10 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| conv2d_11 | src.common.numpy_engine.NumpyNetwork.forward[conv2d] | keras.layers.Conv2D | torch.nn.Conv2d |
| activation_12 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| pooling_13 | src.common.numpy_engine.NumpyNetwork.forward[pooling] | keras.layers.MaxPooling2D/GlobalAveragePooling2D | torch.nn.MaxPool2d/AdaptiveAvgPool2d |
| dense_14 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_15 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_16 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.7. ch4_gold_pink_sheet / rnn

đầu vào → Nhớ thông tin theo thời gian [24, 32] → Nhớ thông tin theo thời gian [24, 32] → Nhớ thông tin theo thời gian [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.13. B.7. ch4_gold_pink_sheet / rnn

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| rnn_1 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 24, 4] → ['batch', 24, 32] | 1184 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| rnn_2 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 24, 32] → ['batch', 24, 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| rnn_3 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 24, 32] → ['batch', 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_4 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_5 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_6 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_8 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.14. B.7. ch4_gold_pink_sheet / rnn

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| rnn_1 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| rnn_2 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| rnn_3 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| dense_4 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_5 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_6 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_8 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.8. ch4_gold_pink_sheet / lstm

đầu vào → Giữ/quên thông tin bằng bộ nhớ và cổng [24, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [24, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.15. B.8. ch4_gold_pink_sheet / lstm

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| lstm_1 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 24, 4] → ['batch', 24, 32] | 4736 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| lstm_2 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 24, 32] → ['batch', 24, 32] | 8320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| lstm_3 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 24, 32] → ['batch', 32] | 8320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_4 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_5 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_6 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_8 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.16. B.8. ch4_gold_pink_sheet / lstm

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| lstm_1 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| lstm_2 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| lstm_3 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| dense_4 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_5 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_6 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_8 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.9. ch4_bis_house_prices / rnn

đầu vào → Nhớ thông tin theo thời gian [12, 32] → Nhớ thông tin theo thời gian [12, 32] → Nhớ thông tin theo thời gian [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.17. B.9. ch4_bis_house_prices / rnn

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| rnn_1 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 12, 51] → ['batch', 12, 32] | 2688 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| rnn_2 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 12, 32] → ['batch', 12, 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| rnn_3 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 12, 32] → ['batch', 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_4 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_5 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_6 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_8 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.18. B.9. ch4_bis_house_prices / rnn

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| rnn_1 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| rnn_2 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| rnn_3 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| dense_4 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_5 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_6 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_8 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.10. ch4_bis_house_prices / lstm

đầu vào → Giữ/quên thông tin bằng bộ nhớ và cổng [12, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [12, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.19. B.10. ch4_bis_house_prices / lstm

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| lstm_1 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 12, 51] → ['batch', 12, 32] | 10752 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| lstm_2 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 12, 32] → ['batch', 12, 32] | 8320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| lstm_3 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 12, 32] → ['batch', 32] | 8320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_4 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_5 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_6 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_8 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.20. B.10. ch4_bis_house_prices / lstm

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| lstm_1 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| lstm_2 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| lstm_3 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| dense_4 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_5 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_6 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_8 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.11. ch4_household_power / rnn

đầu vào → Nhớ thông tin theo thời gian [168, 32] → Nhớ thông tin theo thời gian [168, 32] → Nhớ thông tin theo thời gian [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.21. B.11. ch4_household_power / rnn

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| rnn_1 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 168, 14] → ['batch', 168, 32] | 1504 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| rnn_2 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 168, 32] → ['batch', 168, 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| rnn_3 / rnn(x, weights) -> y | Nhớ thông tin theo thời gian | ['batch', 168, 32] → ['batch', 32] | 2080 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_4 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_5 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_6 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_8 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.22. B.11. ch4_household_power / rnn

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| rnn_1 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| rnn_2 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| rnn_3 | src.common.numpy_engine.NumpyNetwork.forward[rnn] | keras.layers.SimpleRNN | torch.nn.RNN |
| dense_4 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_5 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_6 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_8 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.12. ch4_household_power / lstm

đầu vào → Giữ/quên thông tin bằng bộ nhớ và cổng [168, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [168, 32] → Giữ/quên thông tin bằng bộ nhớ và cổng [32] → Kết hợp các đặc trưng [16] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [16] → Kết hợp các đặc trưng [8] → Giữ tín hiệu dương, tạo khả năng học phi tuyến [8] → Kết hợp các đặc trưng [3] → đầu ra (logit/giá trị chuẩn hóa)

Bảng B.23. B.12. ch4_household_power / lstm

| Hàm/signature | Vai trò | Input → output | Tham số | Trường hợp biên |
|---|---|---|---|---|
| lstm_1 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 168, 14] → ['batch', 168, 32] | 6016 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| lstm_2 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 168, 32] → ['batch', 168, 32] | 8320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| lstm_3 / lstm(x, weights) -> y | Giữ/quên thông tin bằng bộ nhớ và cổng | ['batch', 168, 32] → ['batch', 32] | 8320 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_4 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 32] → ['batch', 16] | 528 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_5 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 16] → ['batch', 16] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_6 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 16] → ['batch', 8] | 136 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| activation_7 / activation(x, weights) -> y | Giữ tín hiệu dương, tạo khả năng học phi tuyến | ['batch', 8] → ['batch', 8] | 0 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |
| dense_8 / dense(x, weights) -> y | Kết hợp các đặc trưng | ['batch', 8] → ['batch', 3] | 27 | Sai rank/shape bị từ chối; trạng thái RNN/LSTM reset giữa các window; không bỏ batch cuối. |

Bảng B.24. B.12. ch4_household_power / lstm

| Function ID | Scratch | Keras | PyTorch |
|---|---|---|---|
| lstm_1 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| lstm_2 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| lstm_3 | src.common.numpy_engine.NumpyNetwork.forward[lstm] | keras.layers.LSTM | torch.nn.LSTM |
| dense_4 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_5 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_6 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |
| activation_7 | src.common.numpy_engine.NumpyNetwork.forward[activation] | keras.layers.ReLU | torch.nn.ReLU |
| dense_8 | src.common.numpy_engine.NumpyNetwork.forward[dense] | keras.layers.Dense | torch.nn.Linear |

## B.13. Đối chiếu tất cả implementation

Bảng B.25. B.13. Đối chiếu tất cả implementation

| Model ID | Lớp học được | Tham số | Implementation |
|---|---|---|---|
| ch2_cdc_diabetes_mlp_scratch | 6 | 9249 | scratch |
| ch2_cdc_diabetes_mlp_keras | 6 | 9249 | keras |
| ch2_cdc_diabetes_mlp_pytorch | 6 | 9249 | pytorch |
| ch2_ames_housing_mlp_scratch | 6 | 27937 | scratch |
| ch2_ames_housing_mlp_keras | 6 | 27937 | keras |
| ch2_ames_housing_mlp_pytorch | 6 | 27937 | pytorch |
| ch2_bank_marketing_mlp_scratch | 6 | 11105 | scratch |
| ch2_bank_marketing_mlp_keras | 6 | 11105 | keras |
| ch2_bank_marketing_mlp_pytorch | 6 | 11105 | pytorch |
| ch3_idrid_cnn_scratch | 7 | 10157 | scratch |
| ch3_idrid_cnn_keras | 7 | 10157 | keras |
| ch3_idrid_cnn_pytorch | 7 | 10157 | pytorch |
| ch3_eurosat_cnn_scratch | 7 | 10322 | scratch |
| ch3_eurosat_cnn_keras | 7 | 10322 | keras |
| ch3_eurosat_cnn_pytorch | 7 | 10322 | pytorch |
| ch3_cifar10_cnn_scratch | 7 | 10322 | scratch |
| ch3_cifar10_cnn_keras | 7 | 10322 | keras |
| ch3_cifar10_cnn_pytorch | 7 | 10322 | pytorch |
| ch4_gold_pink_sheet_rnn_scratch | 6 | 6035 | scratch |
| ch4_gold_pink_sheet_rnn_keras | 6 | 6035 | keras |
| ch4_gold_pink_sheet_rnn_pytorch | 6 | 6035 | pytorch |
| ch4_gold_pink_sheet_lstm_scratch | 6 | 22067 | scratch |
| ch4_gold_pink_sheet_lstm_keras | 6 | 22067 | keras |
| ch4_gold_pink_sheet_lstm_pytorch | 6 | 22067 | pytorch |
| ch4_bis_house_prices_rnn_scratch | 6 | 7539 | scratch |
| ch4_bis_house_prices_rnn_keras | 6 | 7539 | keras |
| ch4_bis_house_prices_rnn_pytorch | 6 | 7539 | pytorch |
| ch4_bis_house_prices_lstm_scratch | 6 | 28083 | scratch |
| ch4_bis_house_prices_lstm_keras | 6 | 28083 | keras |
| ch4_bis_house_prices_lstm_pytorch | 6 | 28083 | pytorch |
| ch4_household_power_rnn_scratch | 6 | 6355 | scratch |
| ch4_household_power_rnn_keras | 6 | 6355 | keras |
| ch4_household_power_rnn_pytorch | 6 | 6355 | pytorch |
| ch4_household_power_lstm_scratch | 6 | 23347 | scratch |
| ch4_household_power_lstm_keras | 6 | 23347 | keras |
| ch4_household_power_lstm_pytorch | 6 | 23347 | pytorch |

KB–KG–RAG và tác tử không có số lớp/tham số neural để đếm. Bảng từng hàm và luồng nhánh/từ chối của chúng nằm ở mục5.6 và6.4, lấy đúng contract của API/UI.
