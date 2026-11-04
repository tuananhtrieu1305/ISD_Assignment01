# CHƯƠNG 4B. LONG SHORT-TERM MEMORY — PHẦN LSTM

Đây là phần lý thuyết bổ sung cho bản thảo RNN đã khóa ở Phase28. Kết quả train/validation
và TEST phải lấy từ artifact Phase29, không dùng số khởi tạo hoặc probe làm chất lượng mô hình.
Thứ tự mục cuối cùng sẽ được hợp nhất trong Chương4 RNN–LSTM khi tích hợp báo cáo.

## Vì sao bổ sung LSTM?

Với cửa sổ điện năng168 giờ, quan sát mới nhất và nhịp dùng điện của những ngày trước đều có
thể hữu ích. RNN liên tục cập nhật một trạng thái tóm tắt; khi truyền ngược qua nhiều bước,
tín hiệu học có thể suy giảm hoặc tăng mạnh. Điều này làm việc học quan hệ xa khó hơn,
nhưng không có nghĩa mọi bài toán đều cần mô hình phức tạp hơn.

Long Short-Term Memory (LSTM) bổ sung một đường bộ nhớ và các cổng điều khiển thông tin.
Có thể hình dung một cuốn sổ: cổng quên quyết định giữ phần nào, cổng nhận quyết định ghi thêm
bao nhiêu, còn cổng xuất chọn phần dùng cho trạng thái đưa sang bước tiếp theo. Các cổng
là vector số học được, không phải quy tắc “giữ đúng xu hướng vàng” do người lập trình đặt sẵn.

LSTM có nhiều tham số hơn RNN cùng hidden width. Nó có thể cần thêm thời gian, dữ liệu và
cũng có thể dự đoán kém baseline đơn giản. Vì vậy, thực nghiệm so cả hai với last-value và
seasonal-naive trên cùng dữ liệu, không mặc định LSTM thắng chỉ vì có bộ nhớ riêng.

## Dữ liệu đầu vào và đầu ra

Phần LSTM dùng lại đúng ba dataset và data card Phase24: vàng World Bank Pink Sheet,
chỉ số nhà BIS và điện năng UCI Household Power. Link nguồn, kích cỡ, mẫu thật, phân bố và
giới hạn nằm tại `report/references/dataset_cards/v3_eda/ch4_*.md` và phần dữ liệu RNN.
Không tải snapshot mới hoặc đổi split giữa hai họ mô hình.

| Bài toán | Một batch đầu vào | Đầu ra trực tiếp | Đơn vị sau inverse-transform |
|---|---|---|---|
| Vàng |`[B,24,4]` |`[B,3]`, sau1/3/6 tháng |USD/troy ounce |
| Giá nhà BIS |`[B,12,51]` |`[B,3]`, sau1/2/4 quý |Điểm chỉ số danh nghĩa2010=100 |
| Điện năng |`[B,168,14]` |`[B,3]`, sau1/6/24 giờ |kW trung bình giờ |

B là số window trong batch, T là chiều thời gian và D là số feature mỗi quan sát.
Mỗi window chỉ nhận lịch sử tới origin; cả ba target phải nằm sau origin và cùng partition.
Scaler và imputer chỉ dùng thống kê train đã khóa; rolling fold dùng prefix riêng.
Nhãn thiếu không được điền để tính metric. Dự đoán ba horizon thực hiện trong một lần,
không lấy dự đoán gần làm đầu vào để sinh dự đoán xa.

## Một bước LSTM: giữ, ghi và xuất

Tại bước t của một tầng, đầu vào gồm quan sát `x_t`, trạng thái ẩn cũ `h_trước` và bộ nhớ cũ
`c_trước`. Cả h và c có32 thành phần ở mô hình chính. Chúng bắt đầu bằng0 cho từng window,
không mang trạng thái của window trước sang window sau.

Để đối chiếu code scratch, chỉ cần các phép cập nhật sau:

```text
z = x_t W + h_trước U + b
(z_i, z_f, z_g, z_o) = tách z thành bốn phần
i = sigmoid(z_i); f = sigmoid(z_f); g = tanh(z_g); o = sigmoid(z_o)
c_mới = f * c_trước + i * g
h_mới = o * tanh(c_mới)
```

W là trọng số đầu vào, shape`[D,128]`; U là trọng số hồi quy`[32,128]`;
b là bias`[128]`. Vì có bốn phần32 chiều nên128=4×32. i/f/g/o lần lượt là cổng nhận,
cổng quên, ứng viên bộ nhớ và cổng xuất. Sigmoid đưa từng thành phần về0–1; tanh đưa về−1–1.
Dấu`*` là nhân từng phần tử, còn hai phép nhân với W/U là nhân ma trận.
Các phép tính này giải thích đúng code forward; đạo hàm chi tiết dành cho kiểm thử/phụ lục.

Ví dụ **synthetic một thành phần**, không phải dự đoán giá: nếu bộ nhớ cũ=2, f=0,8,
i=0,25 và g=0,4 thì bộ nhớ mới=0,8×2+0,25×0,4=1,7. Nếu o=0,5 thì trạng thái xuất
là0,5×tanh(1,7), xấp xỉ0,468. Cổng quên0,8 nghĩa là giữ80% thành phần bộ nhớ cũ tại
bước đó; không có nghĩa “mô hình nhớ đúng80% dữ liệu”.

| Hàm/thành phần | Vai trò | Input → output và lưu ý |
|---|---|---|
| `affine(x,h,W,U,b)` |Kết hợp quan sát với trạng thái cũ |`[B,D]`, `[B,32]` →`[B,128]`; cùng W/U/b dùng lại qua T bước |
| `split(z,4)` |Tách bốn nhánh theo i/f/g/o |`[B,128]` →4 tensor`[B,32]`; thứ tự phải giống ba framework |
| `sigmoid(z_i)` |Cổng nhận: mức ghi thông tin mới |`[B,32]` →`[B,32]` trong0–1 |
| `sigmoid(z_f)` |Cổng quên: mức giữ bộ nhớ cũ |Cùng shape; forget bias ban đầu=1, vẫn được học |
| `tanh(z_g)` |Ứng viên nội dung bổ sung |Cùng shape, trong−1–1; không phải một cổng sigmoid |
| `sigmoid(z_o)` |Cổng xuất: mức đưa bộ nhớ ra trạng thái h |Cùng shape, trong0–1 |
| `carry(f,c,i,g)` |Cộng phần giữ và phần ghi |Bốn tensor`[B,32]` →`c_mới[B,32]` |
| `hidden(o,c)` |Tạo trạng thái cung cấp cho tầng trên |`o*tanh(c)` →`h_mới[B,32]` |

Đây là các bước tính bên trong một tầng LSTM, không phải tám layer riêng.
Chiều thời gian dùng lại tham số; chiều tầng dùng ba bộ tham số khác nhau.

## Sáu lớp học được và hợp các hàm

Luồng bằng lời: **window chuẩn hóa → LSTM1 trả chuỗi → LSTM2 trả chuỗi → LSTM3 lấy bước cuối
→ Dense16/ReLU → Dense8/ReLU → Dense3 tuyến tính → đổi về đơn vị gốc**.

Hợp hàm của riêng mạng, đọc từ phải sang trái:

`F = dense_8 ∘ activation_7 ∘ dense_6 ∘ activation_5 ∘ dense_4 ∘ lstm_3 ∘ lstm_2 ∘ lstm_1`.

Dấu hợp hàm chỉ có nghĩa đầu ra bước trước trở thành đầu vào bước sau. Hai activation là ReLU:
giữ phần dương, đưa phần âm về0; chúng không có tham số. Dense nhân trọng số và cộng bias.
Dense cuối không có ReLU để không ép dự đoán chuẩn hóa thành số dương.

| Bước với Gold | Shape vào → ra | Tham số học được |
|---|---|---:|
| LSTM1 |`[B,24,4]` →`[B,24,32]` |4.736 |
| LSTM2 |`[B,24,32]` →`[B,24,32]` |8.320 |
| LSTM3 |`[B,24,32]` →`[B,32]` |8.320 |
| Dense16 |`[B,32]` →`[B,16]` |528 |
| Dense8 |`[B,16]` →`[B,8]` |136 |
| Dense3 |`[B,8]` →`[B,3]` |27 |

Tổng Gold22.067 tham số, BIS28.083 và Power23.347; mỗi mô hình có6 learnable layers.
Số liệu lấy theo computational plan và canonical parameter shapes Phase25.
Khác biệt giữa dataset nằm ở D đầu vào của LSTM1, không đổi hidden width hoặc độ sâu.
PyTorch có bias hồi quy thứ hai nhưng được giữ0/frozen, không đếm là tham số học được.

## Ba implementation và các hàm huấn luyện

Cả ba dùng `build_plan("lstm", input_shape,3)` và `canonical_weights(plan,seed)`.
Đây là cùng kiến trúc/điểm khởi tạo, nhưng forward, backward và update thực hiện bằng ba
đường độc lập: NumPy thủ công, Keras/TensorFlow và PyTorch. Không gọi một checkpoint là
ba mô hình chỉ bằng cách nạp nó qua ba tên framework.

```python
# Scratch: forward và BPTT viết bằng NumPy, không autograd.
trainer = ScratchTrainer(plan, weights)
trainer.step(x, y, "mse", np.ones(len(y), "float32"))
```

```python
# Keras: native keras.layers.LSTM trong KerasBackend; TensorFlow GPU.
trainer = LstmKerasTrainer(plan, weights, "gpu")
trainer.step(x, y, "mse", np.ones(len(y), "float32"))
```

```python
# PyTorch: native torch.nn.LSTM trong TorchBackend; GPU.
trainer = LstmTorchTrainer(plan, weights, "gpu")
trainer.step(x, y, "mse", np.ones(len(y), "float32"))
```

Các đoạn trích tập trung vào khác biệt implementation; source đầy đủ ở `src/common/numpy_engine.py`,
`src/common/backend_models.py`, `src/ch04_rnn_lstm/training.py` và thư mục
`src/ch04_rnn_lstm/phase29/`. Bảng hàm/shape ba implementation mỗi dataset được sinh từ model contract,
không chép một mô tả khác với mạng thực tế.

| Hàm | Giải thích ngắn và điều kiện quan trọng |
|---|---|
| `WindowData.batch(ids)` |Gom đúng lịch sử theo ID, trả x`[B,T,D]`, y`[B,3]`; development từ chối TEST |
| `NumpyNetwork.forward(x)` |Lặp thời gian và tầng; lưu cache cổng/trạng thái cho backward |
| `NumpyNetwork.backward(dy)` |BPTT: truyền gradient ngược cả h và c, cộng đóng góp vào W/U/b dùng chung |
| `loss_and_gradient(output,y,"mse")` |Sai số bình phương trung bình trên target chuẩn hóa và đạo hàm output |
| `clip_gradients(grads,1)` |Giới hạn global norm, không clip riêng từng phần tử; không bảo đảm chữa được mọi suy giảm gradient |
| `NativeAdam` / scratch `Adam` |Adam cùng quy ước sqrt(v_hat)+epsilon; không dùng stock Keras Adam thay thế |
| `fit_windows(...)` |Cùng batch order, đánh giá full validation mỗi epoch, chọn minimum thật; min_delta chỉ điều khiển patience |
| `export_state()` / `restore_state()` |Giữ weights, m/v và iteration để resume không quay lại điểm khởi tạo |
| `gate_diagnostics(...)` |Đo giá trị cổng, kiểm phương trình bộ nhớ và input gradient trên4 TRAIN windows cố định |
| `ArtifactStore.save_checkpoint/load_checkpoint` |NPZ không pickle, kiểm hash/provenance/shape/finite/budget trước nạp |

Keras chạy graph `tf.function` không XLA trong track LSTM; lựa chọn này được probe trước train
và không thay đổi backend TensorFlow. Cách dispatch LSTM có thể phụ thuộc runtime;
tham chiếu [Keras LSTM](https://keras.io/api/layers/recurrent_layers/lstm/) và
[PyTorch LSTM](https://docs.pytorch.org/docs/2.14/generated/torch.nn.LSTM.html).

## Đánh giá và phạm vi triển khai

So sánh dùng main và ba rolling fold, cùng windows/scalers/seeds/ngân sách RNN đã khóa.
RMSE/MAE/sMAPE tính sau inverse-transform; BIS ưu tiên macro-series RMSE để xem mức sai số
bình quân giữa49 chuỗi. Báo riêng horizon, từng series và chi phí train/inference/RAM/VRAM,
không gộp USD, chỉ số và kW thành một trung bình chung. Gate/input-gradient plots chỉ mô tả
độ nhạy tại mẫu đã chọn, không chứng minh nguyên nhân hoặc bảo đảm nhớ xa.

TEST chung chỉ dùng main checkpoint của cả RNN và LSTM sau khi khóa lựa chọn, evaluator và
approved IDs; không dùng rolling checkpoint thay main. Sau TEST chỉ phân tích dự đoán đã lưu.
Gold/BIS có giới hạn revised snapshot/lịch công bố, Power chỉ một hộ, nên không suy rộng
thành khuyến nghị đầu tư hoặc khả năng dùng cho mọi hộ gia đình.

Checkpoint demo phục vụ bằng NumPy CPU sau kiểm native-CPU round-trip ở ngưỡng đã khai báo;
đường train native GPU và đường serving CPU được ghi riêng. Tích hợp HTTP/React thuộc Phase32–33,
không coi notebook/CLI là Render live. Deployment sẽ là mục ngắn cuối Chương4, không thêm chương riêng.
