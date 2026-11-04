# CHƯƠNG 4. RNN–LSTM VÀ DỰ ĐOÁN CHUỖI THỜI GIAN

Chương này xét cùng ba bài toán vàng, chỉ số nhà và điện năng bằng RNN, LSTM và hai baseline nhân quả. Mỗi họ mạng có ba bản scratch, Keras/TensorFlow và PyTorch, cùng sáu lớp học được. Phần thực nghiệm phân biệt rõ validation dùng chọn checkpoint với TEST chung chỉ đánh giá một lần.

## 4.1. Bài toán dữ liệu tuần tự

Để dự đoán giá vàng tháng tới, chỉ biết giá của một tháng thường chưa đủ. Ta còn muốn biết
những tháng trước giá đang tăng, giảm hay dao động. Tương tự, chỉ số nhà theo quý có xu hướng
chậm, còn điện năng theo giờ thay đổi theo nhịp sinh hoạt. Thứ tự quan sát là một phần của dữ liệu.

Mạng hồi quy (Recurrent Neural Network, RNN) đọc lần lượt các quan sát và cập nhật một vector
tóm tắt lịch sử, gọi là trạng thái ẩn. Có thể hình dung mỗi bước mạng đọc thêm một dòng rồi sửa
bản ghi nhớ của mình. Khi đã đọc hết cửa sổ, trạng thái cuối được dùng để dự đoán các mốc tương lai.
Vector này không phải một bản sao đầy đủ của mọi quan sát; mạng có thể làm mất thông tin cũ.

Ở bài toán vàng, đầu vào có 24 tháng và 4 đặc trưng mỗi tháng. Đầu ra gồm 3 giá trị: giá sau 1,
3 và 6 tháng. Mạng dự đoán trực tiếp cả 3 mốc trong một lần, không lấy dự đoán tháng 1 làm dữ liệu
đầu vào để dự đoán tháng 3. Với điện năng, đầu vào dài 168 giờ; đầu ra ở 1,6 và 24 giờ tiếp theo.

Một **window** hay cửa sổ là đoạn lịch sử kết thúc tại một origin. Origin chỉ là mốc cuối của
lịch sử đã quan sát. Mọi nhãn dự đoán phải nằm sau mốc đó. Hai cửa sổ liên tiếp có thể chồng nhau;
điều này không cho phép đưa quan sát tương lai vào đầu vào hoặc chia ngẫu nhiên các cửa sổ.

Luồng chính: **lịch sử đã quan sát → tạo cửa sổ → chuẩn hóa theo train → RNN nhiều tầng →
Dense → dự đoán chuẩn hóa → đổi về đơn vị gốc → so với nhãn thật**.

## 4.2. Ba dataset và cách chia theo thời gian

### 4.2.1. Nguồn, kích cỡ và ý nghĩa đầu ra

Bảng 4.1. Nguồn, kích cỡ và ý nghĩa đầu ra

| Dataset | Snapshot local và kích cỡ | Phần dùng trong mô hình | Đầu ra / đơn vị |
|---|---|---|---|
| World Bank Pink Sheet | XLSX 586.099 byte,801 tháng từ 1960-01 đến 2026-09 | Một chuỗi;24 tháng ×4 feature | Gold sau 1/3/6 tháng, USD/troy ounce |
| BIS WS_SPP | ZIP 135.216 byte;35.780 quan sát không thiếu trong toàn bulk | Panel 49 nền kinh tế,4.689 dòng, từ 2002;12 quý ×51 feature | Chỉ số nhà sau 1/2/4 quý, danh nghĩa 2010=100 |
| UCI Household Power | ZIP 20.640.916 byte;2.075.259 dòng phút | Tổng hợp 34.589 giờ;168 giờ ×14 feature | Công suất tác dụng trung bình sau 1/6/24 giờ, kW |

Các file nguồn và thẻ dữ liệu đã khóa ở Phase 23–24. Nguồn tải:
[World Bank Pink Sheet October 2026](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx),
[BIS WS_SPP](https://data.bis.org/static/bulk/WS_SPP_csv_col.zip) và
[UCI Household Power](https://archive.ics.uci.edu/dataset/235/individual%2Bhousehold%2Belectric%2Bpower%2Bconsumption).
World Bank/UCI có ghi nhận CC BY 4.0 trong receipt. BIS dùng điều khoản thống kê riêng,
không tự gán giấy phép CC BY và không phát lại raw trong repository.

Giá vàng dùng thêm silver, platinum và dầu thô trễ một tháng; gold tại origin là quan sát đã có
trong cách đánh giá hồi cứu này. BIS chỉ giữ Q/N/628: chuỗi quý, chỉ số danh nghĩa,2010=100;
không trộn chỉ số thực hoặc phần trăm tăng trưởng.51 feature gồm chỉ số, thay đổi so với quý
trước và 49 cột định danh quốc gia. **Đây không phải giá bán căn nhà bằng USD như Ames**.

Điện năng cần ít nhất 45 phút có quan sát để nhận giá trị trung bình giờ. Có 438 giờ thiếu nhãn;
không điền các nhãn này để chấm điểm. Chỉ đặc trưng đầu vào được forward-fill tối đa 6 giờ,
sau đó dùng imputer đã fit train và các cờ thiếu. kW là công suất trung bình, không phải kWh.

### 4.2.2. Mẫu input/output thật và phân bố

Những mẫu sau thuộc TRAIN, đầu ra là nhãn nguồn đã biết, **không phải dự đoán của model**.

Bảng 4.2. Mẫu input/output thật và phân bố

| Dataset / origin | Một phần đầu vào tại mốc cuối | Nhãn ở ba horizon |
|---|---|---|
| GOLD/1961-12 |24 tháng; gold 35, silver_lag 1=0,9, platinum_lag 1=84, crude_oil_lag 1=1,6 |35 /35 /35 USD/troy ounce |
| Q.AT.N.628/2004-10 |12 quý; house_index 80,8486; index_change 1,7286; country_AT=1 |81,1628 /81,9485 /83,9914 điểm chỉ số |
| HOUSEHOLD/2006-12-23 T 20:00 |168 giờ; Global_active_power 4,1814 kW; cờ thiếu 0 |3,288433 /2,303033 /0,4741 kW |

Ba mẫu đầy đủ mỗi dataset, toàn bộ feature/schema và provenance nằm trong
`report/references/dataset_cards/v3_eda/ch4_*.md`. Thống kê dưới đây là mô tả snapshot EDA đã
khóa, không được dùng để fit scaler hoặc lựa chọn mô hình dựa trên TEST.

Bảng 4.3. Mẫu input/output thật và phân bố

| Dataset | Trung vị / khoảng 25%–75% của target quan sát | Min–max | Nhận xét |
|---|---|---|---|
| Gold |379 /159–1.095 USD/troy ounce |35–5.020 |Mức giá đổi mạnh qua thời gian; giai đoạn sau có thể vượt xa miền train |
| BIS |107,6851 /92,7579–151,6941 điểm |16,4856–416,5466 |Khác biệt giữa nền kinh tế; cần xem sai số riêng từng chuỗi |
| Power |0,8027 /0,3419–1,5793 kW |0,124–6,5605 |Lệch phải, có giờ dùng điện cao và nhãn thiếu; chỉ một hộ gia đình |

### 4.2.3. Causal windows, scaler và rolling validation

Bảng 4.4. Causal windows, scaler và rolling validation

| Dataset | Full train / matched train | Full validation | TEST giữ kín đến chốt mô hình | Lookback → horizons |
|---|---:|---:|---:|---|
| Gold |531 /531 |115 |116 |24 tháng →1/3/6 tháng |
| BIS |2.504 /2.504 |588 |568 |12 quý →1/2/4 quý |
| Power |23.797 /12.000 |5.033 |4.911 |168 giờ →1/6/24 giờ |

Tập chính được chia theo lịch của **target**, không theo thứ tự ngẫu nhiên của window.
Mọi horizon trong một window phải thuộc cùng partition; các window cắt ngang ranh giới bị loại.
Context của validation được phép bắt đầu trước ranh giới train, vì đó là quá khứ đã quan sát.
Khi origin dịch chuyển trong validation, mô hình được nhận lịch sử thực tế tới origin mới:
đây là đánh giá rolling-origin, không phải dự đoán toàn giai đoạn bằng một mốc ban đầu duy nhất.

Scaler của tập chính fit trên prefix train đã khóa; mỗi rolling fold dùng scaler của prefix
riêng. Không fit lại trên validation. TensorAdapter áp dụng đúng canonical feature order,
không suy thứ tự từ dictionary JSON. Nhãn để tính metric lấy float 64 từ nguồn; dự đoán được
inverse-transform về đơn vị gốc, không dùng nhãn float 32 đã đổi ngược làm ground truth.

Ba rolling fold mở rộng vùng train bên trong phần pre-TEST, giúp xem kết quả có phụ thuộc
giai đoạn hay không. Các fold dùng lại nhiều quan sát, không phải các phép thử thống kê độc lập.
Khi fold 2/3 chứa origin bị loại tại ranh giới main cũ, adapter Phase 28 dựng lại index theo đúng
ID/calendar đã khóa; không đổi ID/split/scaler. Gold có 5, BIS 98 và power 23 ID bổ sung mỗi fold.

Gold và BIS là snapshot đã chỉnh sửa hồi tố; không có vintage và lịch công bố để khẳng định
dự đoán khả dụng trong giao dịch thật. Với BIS, “quá khứ đã quan sát” không bảo đảm được công bố
đúng ngày origin. Calendar key +00:00 chỉ chuẩn hóa tọa độ thời gian; riêng power không có bằng
chứng timezone/DST đầy đủ. Không suy ra khả năng đầu tư hoặc tổng quát hóa cho mọi hộ gia đình.

## 4.3. RNN sáu lớp và hợp các hàm

### 4.3.1. Một bước nhớ, hai chiều lặp

Ở mỗi tầng, bước thời gian mới kết hợp dữ liệu hiện tại với trạng thái trước rồi đi qua tanh:

`h_t^(l) = tanh(x_t^(l) W_l + h_(t-1)^(l) U_l + b_l)`.

Ở đây t là vị trí trong window, l là tầng RNN. x là vector đầu vào của tầng: tầng 1 dùng các
feature của quan sát, tầng 2–3 dùng output cùng thời điểm của tầng dưới. h là trạng thái 32 chiều.
W có shape `[D,32]`, U là `[32,32]`, b là `[32]`; D của tầng 1 lần lượt 4/51/14, tầng 2–3 là 32.
Với batch B, x có shape `[B,D]`, nên hai tích ma trận đều cho `[B,32]`. tanh giữ từng thành phần
trong khoảng−1 đến 1. Trạng thái trước bước đầu là 0, không mang sang window khác.

Ví dụ shape: một batch 32 cửa sổ vàng đi vào tầng 1 là `[32,24,4]`; output từng thời điểm của
tầng 1 là `[32,24,32]`. Có hai chiều cần phân biệt: **theo thời gian**, cùng một tầng dùng lại
W/U/b qua 24 bước; **theo tầng**, ba bộ W/U/b khác nhau xử lý lần lượt.24 bước thời gian không
được tính thành 24 layer học được.

### 4.3.2. Luồng tổng thể và bảng shape

Luồng model là **RNN 32 trả chuỗi → RNN 32 trả chuỗi → RNN 32 lấy bước cuối → Dense 16 → ReLU →
Dense 8 → ReLU → Dense 3**. Có 3 recurrent và 3 Dense, tức 6 lớp có tham số; activation và bước
lấy phần tử cuối không được dùng để tăng số đếm. Đầu ra cuối là tuyến tính để dự đoán giá trị số.

Viết gọn theo yêu cầu hợp hàm: `F = f_L ∘ ... ∘ f_1`. Cụ thể, dữ liệu đi qua chuẩn hóa,
ba phép lặp RNN, ba Dense xen ReLU rồi đổi ngược target. Dấu hợp hàm chỉ có nghĩa “đầu ra của
bước trước trở thành đầu vào của bước sau”, không thay thế cho sơ đồ thời gian đã giải thích.

Bảng 4.5. Luồng tổng thể và bảng shape

| Bước | Gold input → output | Tham số học được |
|---|---|---:|
| RNN 1, trả toàn chuỗi |`[B,24,4] → [B,24,32]` |1.184 |
| RNN 2, trả toàn chuỗi |`[B,24,32] → [B,24,32]` |2.080 |
| RNN 3, lấy bước cuối |`[B,24,32] → [B,32]` |2.080 |
| Dense 16 + ReLU |`[B,32] → [B,16]` |528 |
| Dense 8 + ReLU |`[B,16] → [B,8]` |136 |
| Dense 3 tuyến tính |`[B,8] → [B,3]` |27 |

Tổng Gold 6.035 tham số; BIS 7.539; Power 6.355. Khác biệt nằm ở số feature đầu vào của RNN 1,
không phải thay số tầng hoặc kích thước hidden. Model contracts và shape trace được sinh từ
cùng computational plan Phase 25 cho cả ba implementation, không viết ba mô tả độc lập.

### 4.3.3. Các hàm cốt lõi và mapping sang code

Bảng 4.6. Các hàm cốt lõi và mapping sang code

| Hàm / signature | Vai trò và input → output | Corner case / mapping |
|---|---|---|
| `WindowData.batch(ids)` |ID → x`[B,T,D]`, y`[B,3]`; gather theo cửa sổ |Từ chối ID TEST/không biết/trùng; dùng cùng reader cho 3 implementation |
| `TensorAdapter.transform(frame)` |Feature gốc → float 32 chuẩn hóa |Dùng stats train và thứ tự cột đã khóa; không refit |
| Bước RNN |x`[B,D]`, h cũ`[B,32]` → h mới`[B,32]` |NumPyNetwork tự matmul/tanh; Keras `SimpleRNN`; Torch `nn.RNN` |
| Lấy trạng thái cuối |Chuỗi`[B,T,32]` → `[B,32]` |Chỉ tầng RNN 3; hai tầng đầu phải trả toàn chuỗi |
| Dense / ReLU |Vector → vector kích thước mới / giữ shape |Dense có W/b; ReLU không có tham số, zero là điểm gấp |
| `loss_and_gradient(pred,y,"mse")` |`[B,3]` → scalar loss và gradient |MSE là trung bình bình phương sai số trên batch và 3 đầu ra chuẩn hóa |
| `NumpyNetwork.backward(dy)` |Gradient output → gradient weights/input |Tự BPTT từ cuối về đầu và từ tầng trên xuống; không gọi autograd |
| `clip_gradients(grads,1)` |Gradient → gradient cùng hướng, norm≤1 |Chặn global norm, không clip riêng từng phần tử; gradient không hữu hạn là lỗi |
| `Adam.step(weights,grads)` |Weights + gradient → weights mới |Lưu m/v/step; giữ quy ước `sqrt(v_hat)+epsilon` như Chương 2 |
| `EarlyStopping.observe(loss,epoch)` |Validation MSE → lưu best/dừng |Lưu minimum thật; min_delta chỉ điều khiển patience |
| `inverse_target(values)` |Dự đoán chuẩn hóa → USD/index/kW |Không làm tròn về số nguyên, không impute nhãn |
| `regression_metrics(y,p,horizons,series)` |Giá trị gốc → RMSE/MAE/sMAPE |Có breakdown horizon/series; không trộn đơn vị giữa dataset |

BPTT, tức lan truyền ngược theo thời gian, áp dụng chuỗi đạo hàm qua các bước mà forward đã
dùng. Scratch lưu trạng thái trung gian để dùng khi quay ngược. Qua nhiều bước tanh, ảnh hưởng
của quan sát cũ có thể suy giảm hoặc gradient có thể lớn bất thường. Gradient clipping giúp
hạn chế update quá lớn, nhưng không tự khắc phục việc mất thông tin dài hạn. LSTM trong phần tiếp theo
được so sánh trên cùng windows, không mặc định tốt hơn chỉ vì có thêm cổng.

Gradient diagnostics dùng 4 window TRAIN cố định và weights được chọn bằng validation.
Biểu đồ ghi độ lớn gradient theo từng vị trí đầu vào bằng RMS (căn của trung bình bình phương),
giúp quan sát loss còn nhạy đến mức nào với từng đoạn lịch sử. Các chuẩn gradient và ma trận
chi tiết được giữ trong `gradient_diagnostics.json` để đối chiếu kỹ thuật.
Giá trị nhỏ ở một vị trí chỉ là độ nhạy cục bộ của loss/ví dụ đó; không chứng minh mô hình luôn
quên quá khứ hoặc feature đó không quan trọng. Biểu đồ này không phải giải thích nhân quả.

### 4.3.4. Scratch, Keras và PyTorch

Ba cách triển khai nhận cùng NTF tensor, cùng weights khởi tạo và batch order theo seed.
Scratch thực hiện forward, MSE, BPTT, clipping và Adam bằng NumPy CPU. Keras dùng 3 SimpleRNN
và 3 Dense của TensorFlow GPU; PyTorch dùng 3 nn.RNN và 3 Linear trên GPU. Trong Torch,
bias recurrent thứ hai được đặt 0 và frozen để không tăng tham số so với canonical W/U/b.

Đoạn khởi tạo ngắn, code đầy đủ nằm trong source và function contracts:

```python
plan = build_plan("rnn", [24, 4], outputs=3)
weights = canonical_weights(plan, seed=42)
scratch_trainer = ScratchTrainer(plan, weights)       # NumPy CPU, tự BPTT
keras_trainer = RnnKerasTrainer(plan, weights, "gpu") # TensorFlow GPU + XLA
torch_trainer = RnnTorchTrainer(plan, weights, "gpu") # PyTorch GPU eager
```

Để thấy rõ thao tác của từng cách viết, dưới đây là các đoạn cốt lõi tối giản. Chúng minh họa
forward/kiến trúc, không thay runner đã khóa; code train thật gán canonical weights và dùng
loss/BPTT/Adam, kiểm tra và checkpoint trong `src/common/` và `src/ch04_rnn_lstm/`.

Scratch tự tính một tầng theo thời gian, không gọi lớp RNN hay autograd:

```python
def simple_rnn(x, W, U, b, return_sequences=True):
    h = np.zeros((len(x), U.shape[0]), dtype=x.dtype)
    sequence = []
    for t in range(x.shape[1]):
        h = np.tanh(x[:, t] @ W + h @ U + b)
        sequence.append(h)
    return np.stack(sequence, axis=1) if return_sequences else h
```

Hai lần đầu trả cả chuỗi, lần thứ ba chỉ trả h cuối. Dense và ReLU xử lý vector đó; backward
trong `NumpyNetwork` quay ngược những trạng thái đã lưu để tính gradient W/U/b bằng phép toán mảng.

Keras thể hiện rõ sáu lớp có tham số trên ví dụ Gold:

```python
import keras
model = keras.Sequential([
    keras.Input(shape=(24, 4)),
    keras.layers.SimpleRNN(32, return_sequences=True),
    keras.layers.SimpleRNN(32, return_sequences=True),
    keras.layers.SimpleRNN(32),
    keras.layers.Dense(16, activation="relu"),
    keras.layers.Dense(8, activation="relu"),
    keras.layers.Dense(3),
])
```

PyTorch trả tuple từ mỗi RNN nên cần lấy chuỗi output trước khi chuyển sang tầng kế tiếp:

```python
import torch
from torch import nn
class RNN6(nn.Module):
    def __init__(self, features=4):
        super().__init__()
        self.rnns = nn.ModuleList([
            nn.RNN(d, 32, batch_first=True) for d in (features, 32, 32)
        ])
        self.head = nn.Sequential(nn.Linear(32, 16), nn.ReLU(),
                                  nn.Linear(16, 8), nn.ReLU(), nn.Linear(8, 3))
        for layer in self.rnns:
            with torch.no_grad():
                layer.bias_hh_l0.zero_()
            layer.bias_hh_l0.requires_grad_(False)
    def forward(self, x):
        for layer in self.rnns:
            x, _ = layer(x)
        return self.head(x[:, -1])
```

Mỗi native framework chạy trong process/env riêng; đoạn trên chỉ minh họa cách gọi, không phải
hướng dẫn import hai engine CUDA vào chung một process. Hai tầng recurrent đầu bật
`return_sequences`, tầng cuối lấy trạng thái cuối; các API đối chiếu tại
[Keras SimpleRNN](https://keras.io/api/layers/recurrent_layers/simple_rnn/) và
[PyTorch RNN 2.14](https://docs.pytorch.org/docs/2.14/generated/torch.nn.RNN.html).

Keras dùng graph/XLA sau probe trước khai báo, giữ nguyên loss/optimizer/architecture. XLA có thể
bỏ TF Assert nên wrapper kiểm finite/shape ở host và kiểm loss/gradient trả về. Chi phí compile
được tính trong train wall nếu xảy ra trong timer; graph không đồng nghĩa luôn nhanh hơn eager.
Xem [TensorFlow tf.function](https://www.tensorflow.org/guide/function) về graph tracing/thực thi.

Huấn luyện dùng batch 32, tối đa 40 epoch, patience 6, min_delta 0,00001 và Adam learning_rate 0,001,
epsilon 0,0000001, clip global norm 1. Seed 17/42/73 không đổi split. Mỗi epoch được lưu weights,
m/v/iteration, best/history/early stopping để resume đúng lịch batch; Torch chuyển cả W và U
moments về canonical layout. NaN/OOM/timeout ghi lỗi, không tự giảm dữ liệu riêng cho một engine.


## 4.4. LSTM: đường bộ nhớ và các cổng

### 4.4.1. Vì sao bổ sung LSTM?

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

### 4.4.2. Dữ liệu đầu vào và đầu ra

Phần LSTM dùng lại đúng ba dataset và data card Phase24: vàng World Bank Pink Sheet,
chỉ số nhà BIS và điện năng UCI Household Power. Link nguồn, kích cỡ, mẫu thật, phân bố và
giới hạn nằm tại `report/references/dataset_cards/v3_eda/ch4_*.md` và phần dữ liệu RNN.
Không tải snapshot mới hoặc đổi split giữa hai họ mô hình.

Bảng 4.7. Dữ liệu đầu vào và đầu ra

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

### 4.4.3. Một bước LSTM: giữ, ghi và xuất

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

Bảng 4.8. Một bước LSTM: giữ, ghi và xuất

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

### 4.4.4. Sáu lớp học được và hợp các hàm

Luồng bằng lời: **window chuẩn hóa → LSTM1 trả chuỗi → LSTM2 trả chuỗi → LSTM3 lấy bước cuối
→ Dense16/ReLU → Dense8/ReLU → Dense3 tuyến tính → đổi về đơn vị gốc**.

Hợp hàm của riêng mạng, đọc từ phải sang trái:

`F = dense_8 ∘ activation_7 ∘ dense_6 ∘ activation_5 ∘ dense_4 ∘ lstm_3 ∘ lstm_2 ∘ lstm_1`.

Dấu hợp hàm chỉ có nghĩa đầu ra bước trước trở thành đầu vào bước sau. Hai activation là ReLU:
giữ phần dương, đưa phần âm về0; chúng không có tham số. Dense nhân trọng số và cộng bias.
Dense cuối không có ReLU để không ép dự đoán chuẩn hóa thành số dương.

Bảng 4.9. Sáu lớp học được và hợp các hàm

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

### 4.4.5. Ba implementation và các hàm huấn luyện

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

Bảng 4.10. Ba implementation và các hàm huấn luyện

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


### 4.4.6. Code cốt lõi ở ba cách viết

Đoạn scratch dưới đây minh họa forward của một tầng. Hai lần đầu trả cả chuỗi,
lần thứ ba lấy trạng thái cuối, rồi nối Dense16/ReLU → Dense8/ReLU → Dense3.
Backward/BPTT của cả h và c, cache các bước và Adam nằm trong source đã kiểm gradient;
không thay chúng bằng autograd trong bản scratch.

```python
def lstm_layer(x, W, U, b, return_sequences=True):
    h = np.zeros((len(x), U.shape[0]), dtype=x.dtype)
    c = np.zeros_like(h)
    sequence = []
    for t in range(x.shape[1]):
        zi, zf, zg, zo = np.split(x[:, t] @ W + h @ U + b, 4, axis=1)
        i, f, o = sigmoid(zi), sigmoid(zf), sigmoid(zo)
        g = np.tanh(zg)
        c = f * c + i * g
        h = o * np.tanh(c)
        sequence.append(h)
    return np.stack(sequence, axis=1) if return_sequences else h
```

Keras biểu diễn sáu lớp có tham số trên ví dụ vàng như sau. Code train thật gán
canonical weights, forget bias và dùng NativeAdam đã chuẩn hóa, không gọi stock
Keras Adam để thay quy ước update.

```python
model = keras.Sequential([
    keras.Input(shape=(24, 4)),
    keras.layers.LSTM(32, return_sequences=True),
    keras.layers.LSTM(32, return_sequences=True),
    keras.layers.LSTM(32),
    keras.layers.Dense(16, activation="relu"),
    keras.layers.Dense(8, activation="relu"),
    keras.layers.Dense(3),
])
```

PyTorch cũng dùng ba LSTM riêng và ba Linear; tuple trạng thái (h,c) không được
truyền sang window khác. Bias recurrent thứ hai giữ0/frozen để khớp số tham số.

```python
class LSTM6(nn.Module):
    def __init__(self, features=4):
        super().__init__()
        self.layers = nn.ModuleList([
            nn.LSTM(d, 32, batch_first=True) for d in (features, 32, 32)
        ])
        self.head = nn.Sequential(nn.Linear(32, 16), nn.ReLU(),
                                  nn.Linear(16, 8), nn.ReLU(), nn.Linear(8, 3))
        for layer in self.layers:
            with torch.no_grad():
                layer.bias_hh_l0.zero_()
            layer.bias_hh_l0.requires_grad_(False)
    def forward(self, x):
        for layer in self.layers:
            x, _ = layer(x)
        return self.head(x[:, -1])
```

Các đoạn trên tập trung vào phép tính/shape, không phải runner thay thế hoặc một
lượt train mới. Runner dùng LstmKerasTrainer/LstmTorchTrainer và gán đúng canonical
initial weights trước update. Mỗi native engine chạy process/venv riêng.


## 4.5. Giao thức so sánh và ý nghĩa số đo

RNN và LSTM dùng cùng split, windows, scaler, seed17/42/73 và ngân sách đã nêu. Mỗi họ có27 lượt main và81 lượt rolling, tổng216 lượt mạng;24 baseline validation ở Phase28 được dùng lại, không train lại. Hai họ dùng cùng hidden width nhưng LSTM có nhiều tham số hơn, vì vậy đây không phải so sánh cùng parameter budget.

Sau khi đủ108 lựa chọn LSTM,108 native-CPU receipts và audit183.159 dòng validation PASS, 330 test/0skip cùng coverage88,02% được khóa trước TEST. Cả hai họ,60 approved main run IDs và evaluator được niêm phong; rolling checkpoint không vào TEST. Mỗi dataset đánh giá9 RNN+9 LSTM+2 baseline, mỗi window đúng một lần cho mỗi model, không update optimizer hoặc chạy timing lặp trên TEST. Gold/BIS có seal evaluated/count1. Power giữ nguyên seal failed_sealed/count1 vì lỗi schema phục hồi chỉ cho validation; revision được người dùng duyệt hoàn tất bản ghi orphan từ4.911 output đã có rồi chạy đúng17 run chưa claim. Không lặp43 claim hoặc dựng lại cache; continuation journal riêng công khai sự cố thay vì reset seal. Revision có21 test và coverage93,50% phần schema/journal PASS trước khi chạy tiếp. Audit hợp nhất111.900 dòng prediction, mỗi dòng có ba horizon, chỉ đọc output đã lưu. Timestamp tạo metric orphan là thời điểm phục hồi record, không giả làm thời điểm inference đã mất.

RMSE là căn của trung bình bình phương sai số, nên phạt sai số lớn; MAE là sai số tuyệt đối trung bình. Hai số cùng đơn vị với target và càng thấp càng tốt. sMAPE thể hiện sai số tương đối đối xứng theo phần trăm; giá trị gần0 có thể làm tỷ lệ nhạy hơn. BIS dùng macro-series RMSE làm metric chính: tính RMSE từng nền kinh tế rồi lấy trung bình ngang49 chuỗi. Không cộng USD, điểm chỉ số và kW thành một điểm chung.

Bảng mạng ghi mean ± sample SD qua ba seed, không phải khoảng tin cậy hoặc bằng chứng hơn hẳn. Baseline là quy tắc cố định với n=1, không dựng SD=0 để giả độ ổn định. Delta ghép theo dataset/method/seed, không chọn seed tốt nhất theo TEST. Các rolling fold chồng lịch nên không coi là mẫu độc lập.

Bảng 4.11. Giao thức so sánh và ý nghĩa số đo

| Dataset | RNN /6 lớp | LSTM /6 lớp | Tỷ số tham số LSTM/RNN |
|---|---|---|---|
| Gold | 6035 | 22067 | 3.66 |
| BIS house index | 7539 | 28083 | 3.73 |
| Household power | 6355 | 23347 | 3.67 |

## 4.6. Kết quả: LSTM không mặc định tốt hơn RNN

### 4.6.1. Chất lượng trên TEST chung

Metric chính là macro-series RMSE cho BIS và RMSE cho hai dataset còn lại. MAE có cùng đơn vị target; sMAPE tính theo%. Bảng dùng full TEST116/568/4.911 windows, không cắt TEST theo matched train.

Bảng 4.12. Chất lượng trên TEST chung

| Dataset | Họ | Cách viết/quy tắc | Metric chính | MAE | sMAPE% |
|---|---|---|---|---|---|
| Gold | RNN | scratch | 1698,490 ± 14,311 | 1435,388 ± 13,413 | 100,780 ± 1,515 |
| Gold | RNN | keras | 1698,490 ± 14,311 | 1435,388 ± 13,413 | 100,780 ± 1,515 |
| Gold | RNN | pytorch | 1712,112 ± 40,745 | 1451,417 ± 45,286 | 102,794 ± 5,505 |
| Gold | LSTM | scratch | 1821,403 ± 72,754 | 1571,944 ± 84,688 | 118,379 ± 11,675 |
| Gold | LSTM | keras | 1821,403 ± 72,754 | 1571,944 ± 84,688 | 118,379 ± 11,675 |
| Gold | LSTM | pytorch | 1821,323 ± 72,616 | 1571,752 ± 84,371 | 118,344 ± 11,616 |
| Gold | CLASSICAL | last_value | 255,158 (n=1) | 146,520 (n=1) | 6,259 (n=1) |
| Gold | CLASSICAL | seasonal_naive | 564,109 (n=1) | 343,945 (n=1) | 14,649 (n=1) |
| BIS house index | RNN | scratch | 34,575 ± 15,171 | 32,853 ± 15,268 | 15,837 ± 8,426 |
| BIS house index | RNN | keras | 34,617 ± 15,136 | 32,914 ± 15,217 | 15,858 ± 8,409 |
| BIS house index | RNN | pytorch | 34,692 ± 15,451 | 32,984 ± 15,537 | 15,875 ± 8,589 |
| BIS house index | LSTM | scratch | 42,167 ± 5,528 | 40,677 ± 5,551 | 20,532 ± 3,183 |
| BIS house index | LSTM | keras | 42,120 ± 5,572 | 40,659 ± 5,569 | 20,569 ± 3,144 |
| BIS house index | LSTM | pytorch | 42,260 ± 5,452 | 40,772 ± 5,475 | 20,589 ± 3,139 |
| BIS house index | CLASSICAL | last_value | 8,564 (n=1) | 6,919 (n=1) | 3,423 (n=1) |
| BIS house index | CLASSICAL | seasonal_naive | 12,340 (n=1) | 11,135 (n=1) | 5,581 (n=1) |
| Household power | RNN | scratch | 0,593 ± 0,008 | 0,426 ± 0,012 | 44,992 ± 1,205 |
| Household power | RNN | keras | 0,590 ± 0,005 | 0,430 ± 0,003 | 45,931 ± 0,189 |
| Household power | RNN | pytorch | 0,590 ± 0,005 | 0,426 ± 0,013 | 45,289 ± 1,474 |
| Household power | LSTM | scratch | 0,583 ± 0,014 | 0,424 ± 0,016 | 45,350 ± 1,346 |
| Household power | LSTM | keras | 0,583 ± 0,019 | 0,422 ± 0,020 | 44,863 ± 1,956 |
| Household power | LSTM | pytorch | 0,590 ± 0,012 | 0,427 ± 0,012 | 45,234 ± 0,760 |
| Household power | CLASSICAL | last_value | 0,809 (n=1) | 0,556 (n=1) | 53,887 (n=1) |
| Household power | CLASSICAL | seasonal_naive | 0,763 (n=1) | 0,512 (n=1) | 49,182 (n=1) |

![Hình 4.1. TEST chung, sai số chính theo từng dataset; trục log, đơn vị riêng. Error bar là sample SD ba seed, đường baseline n=1.](../../../artifacts/figures/phase29/main_test_comparison.png)

Dấu dương ở cột cải thiện nghĩa là LSTM có sai số trung bình thấp hơn RNN; dấu âm nghĩa là kém hơn. Tỷ lệ được tính bằng100×(mean RNN−mean LSTM)/mean RNN trên cùng nhóm, không phải lợi nhuận.

Bảng 4.13. Chất lượng trên TEST chung

| Dataset | Cách viết | RNN−LSTM (đơn vị target) | Cải thiện tương đối% |
|---|---|---|---|
| Gold | scratch | -122,914 ± 78,098 | -7.24 |
| Gold | keras | -122,913 ± 78,098 | -7.24 |
| Gold | pytorch | -109,211 ± 87,697 | -6.38 |
| BIS house index | scratch | -7,591 ± 18,810 | -21.96 |
| BIS house index | keras | -7,503 ± 18,870 | -21.68 |
| BIS house index | pytorch | -7,568 ± 19,130 | -21.81 |
| Household power | scratch | 0,011 ± 0,018 | 1.80 |
| Household power | keras | 0,008 ± 0,023 | 1.28 |
| Household power | pytorch | -0,000 ± 0,010 | -0.08 |

**Gold:** LSTM giảm metric chính ở0/3 implementation trên TEST. Kết quả này mô tả đúng kiến trúc và ngân sách đã khóa, không chứng minh ưu thế của mọi LSTM/RNN.

Last-value có metric chính 255,158 (n=1) USD/troy ounce; RNN thấp hơn baseline này ở0/3 cách viết, LSTM ở0/3. Đây là so sánh với quy tắc đã khai báo, không chọn lại mô hình triển khai bằng TEST.

**BIS house index:** LSTM giảm metric chính ở0/3 implementation trên TEST. Kết quả này mô tả đúng kiến trúc và ngân sách đã khóa, không chứng minh ưu thế của mọi LSTM/RNN.

Last-value có metric chính 8,564 (n=1) index 2010=100; RNN thấp hơn baseline này ở0/3 cách viết, LSTM ở0/3. Đây là so sánh với quy tắc đã khai báo, không chọn lại mô hình triển khai bằng TEST.

**Household power:** LSTM giảm metric chính ở2/3 implementation trên TEST. Kết quả này mô tả đúng kiến trúc và ngân sách đã khóa, không chứng minh ưu thế của mọi LSTM/RNN.

Last-value có metric chính 0,809 (n=1) kW; RNN thấp hơn baseline này ở3/3 cách viết, LSTM ở3/3. Đây là so sánh với quy tắc đã khai báo, không chọn lại mô hình triển khai bằng TEST.

### 4.6.2. Horizon dài và biến động giai đoạn

Bảng sau xét horizon xa nhất bằng RMSE theo toàn window. Riêng BIS, bảng này là pooled RMSE, khác metric chính macro-series RMSE ở bảng trước; không đổi tên hai cách tính cho nhau.

Bảng 4.14. Horizon dài và biến động giai đoạn

| Dataset | Horizon xa | Cách viết | RNN RMSE | LSTM RMSE |
|---|---|---|---|---|
| Gold | 6 | scratch | 1803,309 ± 22,961 | 1912,018 ± 75,841 |
| Gold | 6 | keras | 1803,309 ± 22,961 | 1912,018 ± 75,842 |
| Gold | 6 | pytorch | 1812,833 ± 38,592 | 1913,807 ± 78,229 |
| BIS house index | 4 | scratch | 53,896 ± 20,364 | 61,479 ± 8,145 |
| BIS house index | 4 | keras | 54,048 ± 20,238 | 61,727 ± 7,939 |
| BIS house index | 4 | pytorch | 54,054 ± 20,891 | 61,519 ± 8,112 |
| Household power | 24 | scratch | 0,623 ± 0,004 | 0,612 ± 0,005 |
| Household power | 24 | keras | 0,621 ± 0,002 | 0,615 ± 0,013 |
| Household power | 24 | pytorch | 0,620 ± 0,003 | 0,617 ± 0,006 |

![Hình 4.2. TEST theo cả ba horizon, mean ± sample SD; tháng/quý/giờ theo dataset, không đồng nhất về thời lượng.](../../../artifacts/figures/phase29/horizon_test.png)

![Hình 4.3. Ba expanding rolling VALIDATION; scaler riêng từng prefix. Đây là development, không phải ba lượt TEST hoặc ba mẫu độc lập.](../../../artifacts/figures/phase29/rolling_validation.png)

### 4.6.3. Ví dụ dự đoán và khác biệt giữa nền kinh tế

Ví dụ forecast dùng scratch seed42 đã định trước, horizon gần nhất và chuỗi đầu theo ID. Power hiển thị thưa nếu quá500 điểm để đọc hình; metric vẫn tính trên mọi window. Đường sát nhau không đồng nghĩa có giá trị giao dịch hay mô hình nhận ra đúng cơ chế kinh tế.

![Hình 4.4. Nhãn thật và dự đoán TEST đã lưu, một chuỗi/dataset; không phát sinh inference TEST để vẽ.](../../../artifacts/figures/phase29/saved_test_forecasts.png)

![Hình 4.5. BIS TEST: RMSE từng nền kinh tế, trung bình ba seed, màu log10 cùng thang cho sáu cách triển khai.](../../../artifacts/figures/phase29/bis_country_errors.png)

## 4.7. Quá trình học, cổng và gradient

Đường loss dùng seed42 main của cả hai họ và cả ba framework, không lấy seed có đường đẹp nhất. Early stopping chọn minimum validation thật, không chọn theo TEST. Sai khác giữa các framework có thể tích lũy qua update và làm epoch dừng khác nhau, dù khởi tạo và quy ước Adam giống nhau.

![Hình 4.6. Validation MSE chuẩn hóa theo epoch, seed42 main; không so giá trị loss giữa dataset như cùng đơn vị vật lý.](../../../artifacts/figures/phase29/learning_curves.png)

Cổng sigmoid có giá trị0–1: gần1 cho phép giữ/ghi/xuất nhiều hơn tại thành phần đó. Hình lấy trung bình trên4 TRAIN windows và hidden dimensions của scratch seed42, không phải tỷ lệ dự đoán đúng. Cổng quên cao không tự chứng minh rằng mô hình đã học được quan hệ dài hạn hữu ích.

![Hình 4.7. Input/forget/output gates theo bước thời gian, ba tầng LSTM, chỉ dùng TRAIN.](../../../artifacts/figures/phase29/lstm_gate_profiles.png)

![Hình 4.8. Input-gradient RMS của4 TRAIN windows cố định; floor1e−30 chỉ để hiển thị log nếu bằng0, không dùng cho metric/parity.](../../../artifacts/figures/phase29/train_gradient_profiles.png)

Độ lớn gradient mô tả độ nhạy cục bộ của loss tại checkpoint và mẫu đã chọn, không phải causal importance. Không kết luận LSTM khắc phục mọi vanishing/exploding gradient chỉ từ một đường cong. Các tỷ lệ oldest/newest và clipping của toàn216 lượt mạng nằm trong `train_diagnostics.csv`.

Bảng 4.15. Quá trình học, cổng và gradient

| Dataset | Họ /scratch seed42 | Gradient oldest/newest | Tỷ lệ batch bị clip, TB epoch |
|---|---|---|---|
| Gold | RNN | 0.01261 | 0.0709 |
| BIS house index | RNN | 0.119 | 0.0842 |
| Household power | RNN | 1.049e-09 | 0.8945 |
| Gold | LSTM | 0.3204 | 0.1255 |
| BIS house index | LSTM | 1.76 | 0.0952 |
| Household power | LSTM | 0.000138 | 0.6707 |

## 4.8. Chi phí, sai lệch đo và giới hạn

Scratch chạy NumPy CPU; Keras và PyTorch train GPU trong hai venv độc lập. RNN Keras dùng XLA, LSTM Keras graph không XLA; PyTorch eager. Vì vậy thời gian phản ánh cả engine, dispatch/compile và implementation, không đo riêng độ phức tạp lý thuyết. Các unit test nhẹ đã chạy khi queue hoạt động nên không gọi đây là benchmark máy cô lập.

Trong Phase29, distro/runtime cũ không còn nên được khôi phục đúng lock ở Ubuntu/user mới. Bốn process torch/TF ×GPU/CPU và shared-package parity đã PASS; năm selection cũ được giữ nguyên. Không mô tả RNN và LSTM là hai lượt đo liên tiếp trong một phiên runtime không gián đoạn.

Train wall là thời gian đoạn fit, có thể bao gồm validation/compile trong timer; RSS là high-water process, VRAM là peak allocator, không phải bộ nhớ toàn máy/GPU. Timing p50/p95 lưu từ5warmup+30repeat trên một TRAIN input, không phải end-to-end HTTP hoặc đo lại TEST. TEST metric giữ bản sao chi phí train gốc; không cộng thành chi phí train thứ hai.

RNN Power/PyTorch seed17 có original train/RAM/VRAM bị mất khi export lỗi. Giữ null, giữ FAIL GPU→CPU gốc và bản phục hồi không thêm update; quality dùng3 seed nhưng nhóm chi phí dùng2. Không thay bằng0 hoặc peak của process recovery.

Bảng 4.16. Chi phí, sai lệch đo và giới hạn

| Dataset | Họ | Cách viết | Train giây | Peak RSS MiB | Peak allocator VRAM MiB |
|---|---|---|---|---|---|
| Gold | RNN | scratch | 8,518 ± 0,698 (n=3) | 227,3 ± 0,3 | 0,0 ± 0,0 |
| Gold | RNN | keras | 25,116 ± 1,018 (n=3) | 1516,0 ± 2,2 | 2,0 ± 0,0 |
| Gold | RNN | pytorch | 10,640 ± 3,491 (n=3) | 1739,1 ± 2,1 | 74,4 ± 0,0 |
| Gold | LSTM | scratch | 8,006 ± 1,061 (n=3) | 228,8 ± 0,9 | 0,0 ± 0,0 |
| Gold | LSTM | keras | 14,975 ± 2,820 (n=3) | 1524,2 ± 89,0 | 18,4 ± 0,0 |
| Gold | LSTM | pytorch | 8,406 ± 2,122 (n=3) | 1741,7 ± 2,4 | 76,4 ± 0,0 |
| BIS house index | RNN | scratch | 10,095 ± 2,473 (n=3) | 237,3 ± 0,4 | 0,0 ± 0,0 |
| BIS house index | RNN | keras | 37,904 ± 9,290 (n=3) | 1522,7 ± 1,5 | 1,9 ± 0,0 |
| BIS house index | RNN | pytorch | 24,752 ± 7,211 (n=3) | 1749,7 ± 0,4 | 73,4 ± 0,0 |
| BIS house index | LSTM | scratch | 15,011 ± 1,484 (n=3) | 238,0 ± 0,7 | 0,0 ± 0,0 |
| BIS house index | LSTM | keras | 35,949 ± 6,259 (n=3) | 1502,8 ± 1,2 | 18,0 ± 0,0 |
| BIS house index | LSTM | pytorch | 18,193 ± 1,729 (n=3) | 1752,7 ± 0,1 | 74,5 ± 0,0 |
| Household power | RNN | scratch | 108,922 ± 24,083 (n=3) | 325,9 ± 1,2 | 0,0 ± 0,0 |
| Household power | RNN | keras | 558,896 ± 149,511 (n=3) | 1597,2 ± 0,5 | 16,4 ± 0,0 |
| Household power | RNN | pytorch | 68,641 ± 0,552 (n=2) | 1827,0 ± 0,7 | 88,2 ± 0,0 |
| Household power | LSTM | scratch | 441,879 ± 6,008 (n=3) | 328,3 ± 0,6 | 0,0 ± 0,0 |
| Household power | LSTM | keras | 245,851 ± 20,212 (n=3) | 1589,7 ± 3,9 | 26,5 ± 0,1 |
| Household power | LSTM | pytorch | 44,718 ± 5,326 (n=3) | 1831,6 ± 0,1 | 100,9 ± 0,0 |

![Hình 4.9. Train wall chính, mean ± sample SD trên số seed có telemetry; n=2 được ghi riêng, không phải latency TEST.](../../../artifacts/figures/phase29/training_cost.png)

Snapshot vàng/BIS có thể đã được chỉnh sửa hồi tố; không có vintage và lịch công bố đầy đủ. Power chỉ một hộ và timezone/DST chưa xác minh. Các mô hình sâu có thể kém baseline khi dữ liệu ít, trend đổi hoặc target vượt vùng train. Không tuning lại sau TEST để che các kết quả âm; không suy rộng thành hệ dự báo giá hay điện thương mại.



## 4.9. Mẫu dữ liệu và đường dẫn hồ sơ

### ch4_gold_pink_sheet

Mẫu window thuộc matched train; known_output là giá trị tương lai đã có trong nguồn train, không phải dự đoán. Target thiếu không bao giờ được điền.

Bảng 4.17. ch4_gold_pink_sheet

| Mã mẫu | Input minh họa | Output nguồn |
|---|---|---|
| GOLD/1961-12-01T00:00:00 | {"context_end": "1961-12-01T00:00:00", "context_start": "1960-01-01T00:00:00", "last_values": {"crude_oil_lag1": 1.6, "gold": 35.0, "platinum_lag1": 84.0, "silver_lag1": 0.9}} | {"horizons": [1, 3, 6], "target_times": ["1962-01-01T00:00:00", "1962-03-01T00:00:00", "1962-06-01T00:00:00"], "values": [35, 35, 35]} |
| GOLD/1962-01-01T00:00:00 | {"context_end": "1962-01-01T00:00:00", "context_start": "1960-02-01T00:00:00", "last_values": {"crude_oil_lag1": 1.6, "gold": 35.0, "platinum_lag1": 84.0, "silver_lag1": 1.0}} | {"horizons": [1, 3, 6], "target_times": ["1962-02-01T00:00:00", "1962-04-01T00:00:00", "1962-07-01T00:00:00"], "values": [35, 35, 35]} |
| GOLD/1962-02-01T00:00:00 | {"context_end": "1962-02-01T00:00:00", "context_start": "1960-03-01T00:00:00", "last_values": {"crude_oil_lag1": 1.5, "gold": 35.0, "platinum_lag1": 84.0, "silver_lag1": 1.0}} | {"horizons": [1, 3, 6], "target_times": ["1962-03-01T00:00:00", "1962-05-01T00:00:00", "1962-08-01T00:00:00"], "values": [35, 35, 35]} |

Nguồn đầy đủ: `report/references/dataset_cards/v3_eda/ch4_gold_pink_sheet.md`; mọi đoạn rút gọn được ghi là trích.

Hồ sơ nguồn, dung lượng, schema, phân bố và giới hạn đầy đủ ở Phụ lục A, mục `ch4_gold_pink_sheet`.

### ch4_bis_house_prices

Mẫu window thuộc matched train; known_output là giá trị tương lai đã có trong nguồn train, không phải dự đoán. Target thiếu không bao giờ được điền.

Bảng 4.18. ch4_bis_house_prices

| Mã mẫu | Input minh họa | Output nguồn |
|---|---|---|
| Q.AT.N.628/2004-10-01T00:00:00 | {"context_end": "2004-10-01T00:00:00", "context_start": "2002-01-01T00:00:00", "last_values": {"country_AT": 1.0, "country_AU": 0.0, "house_index": 80.8486, "index_change": 1.7286000000000001}} | {"horizons": [1, 2, 4], "target_times": ["2005-01-01T00:00:00", "2005-04-01T00:00:00", "2005-10-01T00:00:00"], "values": [81.1628, 81.9485, 83.9914]} |
| Q.AT.N.628/2005-01-01T00:00:00 | {"context_end": "2005-01-01T00:00:00", "context_start": "2002-04-01T00:00:00", "last_values": {"country_AT": 1.0, "country_AU": 0.0, "house_index": 81.1628, "index_change": 0.3141999999999996}} | {"horizons": [1, 2, 4], "target_times": ["2005-04-01T00:00:00", "2005-07-01T00:00:00", "2006-01-01T00:00:00"], "values": [81.9485, 82.0271, 84.9342]} |
| Q.AT.N.628/2005-04-01T00:00:00 | {"context_end": "2005-04-01T00:00:00", "context_start": "2002-07-01T00:00:00", "last_values": {"country_AT": 1.0, "country_AU": 0.0, "house_index": 81.9485, "index_change": 0.7856999999999914}} | {"horizons": [1, 2, 4], "target_times": ["2005-07-01T00:00:00", "2005-10-01T00:00:00", "2006-04-01T00:00:00"], "values": [82.0271, 83.9914, 85.6413]} |

Nguồn đầy đủ: `report/references/dataset_cards/v3_eda/ch4_bis_house_prices.md`; mọi đoạn rút gọn được ghi là trích.

Hồ sơ nguồn, dung lượng, schema, phân bố và giới hạn đầy đủ ở Phụ lục A, mục `ch4_bis_house_prices`.

### ch4_household_power

Mẫu window thuộc matched train; known_output là giá trị tương lai đã có trong nguồn train, không phải dự đoán. Target thiếu không bao giờ được điền.

Bảng 4.19. ch4_household_power

| Mã mẫu | Input minh họa | Output nguồn |
|---|---|---|
| HOUSEHOLD/2006-12-23T20:00:00 | {"context_end": "2006-12-23T20:00:00", "context_start": "2006-12-16T21:00:00", "last_values": {"Global_active_power": 4.1814, "Global_active_power_missing": 0.0, "Global_reactive_power": 0.12476666666666666, "Global_reactive_power_missing": 0.0}} | {"horizons": [1, 6, 24], "target_times": ["2006-12-23T21:00:00", "2006-12-24T02:00:00", "2006-12-24T20:00:00"], "values": [3.2884333333333333, 2.303033333333333, 0.4741]} |
| HOUSEHOLD/2006-12-23T23:00:00 | {"context_end": "2006-12-23T23:00:00", "context_start": "2006-12-17T00:00:00", "last_values": {"Global_active_power": 5.5624666666666664, "Global_active_power_missing": 0.0, "Global_reactive_power": 0.12806666666666666, "Global_reactive_power_missing": 0.0}} | {"horizons": [1, 6, 24], "target_times": ["2006-12-24T00:00:00", "2006-12-24T05:00:00", "2006-12-24T23:00:00"], "values": [4.0280000000000005, 1.6319000000000001, 0.48633333333333334]} |
| HOUSEHOLD/2006-12-24T00:00:00 | {"context_end": "2006-12-24T00:00:00", "context_start": "2006-12-17T01:00:00", "last_values": {"Global_active_power": 4.0280000000000005, "Global_active_power_missing": 0.0, "Global_reactive_power": 0.09066666666666667, "Global_reactive_power_missing": 0.0}} | {"horizons": [1, 6, 24], "target_times": ["2006-12-24T01:00:00", "2006-12-24T06:00:00", "2006-12-25T00:00:00"], "values": [3.2757, 1.8952, 0.9995666666666667]} |

Nguồn đầy đủ: `report/references/dataset_cards/v3_eda/ch4_household_power.md`; mọi đoạn rút gọn được ghi là trích.

Hồ sơ nguồn, dung lượng, schema, phân bố và giới hạn đầy đủ ở Phụ lục A, mục `ch4_household_power`.

## 4.10. Triển khai ngắn

Tab RNN–LSTM giữ ba dataset và cho đổi family trước khi chạy ba implementation trên một cửa sổ. API giữ scaler, feature order, lookback và horizon từ contract, không trộn lịch giữa hai quốc gia BIS hoặc thêm quan sát tương lai. Đầu ra đổi ngược sang USD/troy ounce, chỉ số nhà hoặc kW theo dataset. Chế độ CPU dùng NumPy portable; local_gpu dùng framework native, không đổi weights hay cập nhật model bằng câu hỏi.

Đường dẫn minh họa: `/rnn?dataset=ch4_gold_pink_sheet&family=lstm&section=run`. Selector seed trong kết quả lịch sử chỉ lọc bảng; serving vẫn seed42 đã chọn trước, không chọn checkpoint tốt nhất theo TEST. Sai số TEST, chi phí train và thời gian job demo là ba loại số khác nhau. Các notebook mỏng vẫn ở `experiments/notebooks/v3/ch04_rnn_lstm/`; chúng không làm phát sinh một lượt TEST mới.

Python API và React UI đã được kiểm thử local; không có endpoint train/TEST. Job có kiểm schema/hash/quyền đọc, timeout và giới hạn tài nguyên. Demo không là chẩn đoán, định giá hiện tại hay khuyến nghị đầu tư. Blueprint CPU dành Render và Static Site đã chuẩn bị, nhưng chưa cloud deploy; cần API HTTPS và CORS chính xác khi build. Hướng dẫn dài ở Phụ lục C.
