# KẾ HOẠCH THỰC THI TIỂU LUẬN AI V3

> **Trạng thái:** `ACTIVE` — nguồn sự thật duy nhất cho yêu cầu mới từ ngày 2026-10-16.
>
> Phase 0–9 trong `TIEU_LUAN_AI_EXECUTION_PLAN.md` và Phase 10–19 trong
> `CHUONG_5_KNOWLEDGE_RAG_EXECUTION_PLAN.md` là lịch sử đã hoàn thành. Đợt V3 dùng
> **Phase 20–35**. Khi người dùng gõ **`làm phase N`** với `N = 20..35`, phải đọc
> toàn bộ file này, kiểm tra dependency và nhật ký, rồi tự thực hiện đúng phase đó.

## 0. Quy tắc điều hành

Khi nhận lệnh `làm phase N`, trợ lý phải:

1. Đọc file này và mọi `AGENTS.md` áp dụng cho đường dẫn sẽ sửa.
2. Kiểm tra `git status`; không ghi đè thay đổi không liên quan của người dùng.
3. Kiểm tra dependency trong bảng trạng thái. Không tự nhảy sang phase độc lập khác.
4. Dùng dữ liệu, số đo, metric, hình, log và trích dẫn thật; không bịa kết quả.
5. Ưu tiên nguồn dữ liệu chính thức, lưu URL, thời điểm truy cập, phiên bản và SHA-256.
6. Chạy kiểm tra tương xứng rủi ro và lưu artifact có thể tái lập.
7. Cập nhật ngay trạng thái, đầu ra, lệnh kiểm tra, kết quả và sai lệch vào nhật ký cuối file.
8. Chỉ đặt `COMPLETE` khi toàn bộ tiêu chí nghiệm thu đạt. Nếu chưa đạt, giữ
   `IN_PROGRESS`; chỉ dùng `BLOCKED` khi thật sự cần quyết định/quyền truy cập từ người dùng.
9. Không chạy lại tập TEST đã niêm phong chỉ để cải thiện báo cáo. Mọi lần mở TEST phải có log.
10. Trả lời bằng kết quả, file quan trọng, kiểm tra đã chạy và phase hợp lý tiếp theo.

Các lựa chọn nhỏ đã khóa trong kế hoạch không cần hỏi lại. Phải hỏi trước khi dùng dịch vụ
trả phí, API key, gửi dữ liệu ra ngoài, thay đổi phạm vi lớn hoặc viết lại lịch sử Git.

## 1. Hợp đồng yêu cầu V3

### 1.1. Cấu trúc báo cáo bắt buộc

1. Mở đầu.
2. Chương 1 — Lịch sử phát triển trí tuệ nhân tạo.
3. Chương 2 — Các kỹ thuật Machine Learning cơ bản.
4. Chương 3 — Convolutional Neural Network (CNN).
5. Chương 4 — Recurrent Neural Network và Long Short-Term Memory (RNN–LSTM).
6. Chương 5 — Knowledge Base, Knowledge Graph và Retrieval-Augmented Generation.
7. Chương 6 — Hệ đa tác tử (Multi-Agent Systems).
8. Kết luận, tài liệu tham khảo và phụ lục cần thiết.

Chương 1–3 giữ mạch nội dung đã có nhưng được sửa số liệu, dataset, code và hình khi không còn
đạt yêu cầu. Chương 4 phải mở rộng từ RNN thành RNN–LSTM thực nghiệm đầy đủ. Chương 5 giữ nội
dung và kết quả đã khóa, chỉ chỉnh cấu trúc/tích hợp. Chương 6 là chương mới hoàn chỉnh.

**Deployment không phải chương riêng.** Cuối mỗi chương thực nghiệm 2–6 có một mục ngắn về
đóng gói, API/UI, giới hạn triển khai và đường dẫn demo tương ứng.

### 1.2. Dataset và thực nghiệm

- Mỗi chương có 2–3 dataset/corpus/benchmark phù hợp với bản chất chương.
- Mỗi dataset phải có: link, giấy phép/citation, dung lượng file, kích cỡ logic, schema,
  mẫu input/output, phân bố quan trọng, missing/imbalance, nhận xét và hạn chế.
- Chương 1 dùng 3 benchmark lịch sử làm case study, không giả vờ là chương huấn luyện.
- Chương 2–4 mỗi chương có 3 dataset và giao thức đánh giá khóa trước.
- Chương 5 giữ MedQuAD, FinQA và Wikidata đã thu nhận/đánh giá.
- Chương 6 dùng 3 bộ nhiệm vụ diabetes, house price và gold, tái sử dụng snapshot đã khóa;
  không nhân bản dữ liệu thô.
- Mọi split có manifest ID/hash. Tabular dùng stratified/group split khi phù hợp; chuỗi thời gian
  luôn split theo thời gian; không shuffle tương lai về quá khứ.
- Ba implementation trên cùng bài toán dùng cùng preprocessing, split, seed policy, metric và
  budget epoch/patience. Khác biệt bắt buộc phải được ghi rõ.

### 1.3. Ba loại code và quy tắc trên 5 layer

Yêu cầu tối thiểu được diễn giải bảo thủ để tránh tranh cãi khi chấm:

- Chương 2 có MLP `scratch`, `Keras`, `PyTorch` bên cạnh các mô hình ML cổ điển.
- Chương 3 có CNN `scratch`, `Keras`, `PyTorch` trên cả 3 dataset.
- Chương 4 có **sáu họ triển khai**: RNN scratch/Keras/PyTorch và
  LSTM scratch/Keras/PyTorch trên cả 3 dataset.
- Mỗi mạng sâu dùng **ít nhất 6 lớp/khối có tham số học được**. Input, reshape, activation,
  pooling, dropout, normalization không được dùng để đủ số đếm. Báo cáo phải có bảng đếm lớp,
  tensor shape và parameter count tự động kiểm chứng.
- ML cổ điển không bị ép dùng khái niệm layer; yêu cầu này áp dụng cho MLP/CNN/RNN/LSTM.
- Scratch nghĩa là tự hiện thực forward, loss, backward/BPTT, optimizer update và predict bằng
  phép toán mảng; không gọi layer/model/automatic differentiation của Keras hay PyTorch.

Kiến trúc tham chiếu để so sánh công bằng:

| Họ | Tối thiểu khối học được | Quy ước mặc định |
|---|---:|---|
| MLP | 6 | 5 Dense ẩn + Dense đầu ra |
| CNN | 7 | 5 Convolution + 2 Dense |
| RNN | 6 | 3 recurrent layers + 3 Dense |
| LSTM | 6 | 3 LSTM layers + 3 Dense |

Nếu scratch quá chậm, được dùng tập train stratified cố định hoặc giảm resolution đã khai báo,
nhưng không được thay test split. Báo cáo phải tách `full-data track` và `matched-subset track`,
không so thời gian/metric giữa hai track như thể cùng điều kiện.

### 1.4. Hợp các hàm và giải thích hàm

Mỗi mô hình phải có cả hai mức giải thích:

1. **Hợp hàm tổng thể:** biểu diễn dạng `F = f_L ∘ ... ∘ f_2 ∘ f_1`, kèm sơ đồ tensor
   và shape tại từng bước. Với RNN/LSTM phải thể hiện thêm phép lặp theo thời gian và theo tầng.
2. **Từng hàm riêng:** tên/signature, input, output, tham số học được, công thức, vai trò,
   shape, corner case và mapping tới hàm scratch/Keras/PyTorch.

Mỗi notebook/module phải sinh machine-readable `model_contract.json`; báo cáo và web đọc cùng
contract để tránh ba nơi mô tả ba kiến trúc khác nhau.

### 1.5. Câu hỏi nghiên cứu khóa trước

- RQ2: Với dữ liệu bảng, ba cách hiện thực MLP khác nhau thế nào về chất lượng, thời gian,
  bộ nhớ, độ ổn định và độ khó triển khai so với baseline ML cổ điển?
- RQ3: Trên ảnh y khoa/viễn thám/vật thể tự nhiên, CNN scratch, Keras và PyTorch khác nhau
  thế nào khi dùng cùng kiến trúc và split?
- RQ4.1: Vanilla RNN thay đổi ra sao trên chuỗi ngắn/dài và ba miền gold/house/power?
- RQ4.2: LSTM có cải thiện sai số dài hạn và gradient stability so với RNN không?
- RQ5: Giữ các câu hỏi B0–B4 đã khóa của Chương 5; không mở lại TEST để tuning.
- RQ6: Hệ nhiều agent có cải thiện task success, kiểm chứng và độ an toàn so với direct/single
  agent, với chi phí latency/message count nào?

### 1.6. Chính sách trình bày lý thuyết

Phần lý thuyết của tất cả các chương phải ở mức **cơ bản, dễ hiểu và vừa đủ ý**. Mục tiêu là
giúp người đọc hiểu mô hình hoạt động như thế nào và liên hệ được với phần thực nghiệm, không
biến tiểu luận thành tài liệu chứng minh toán học.

Thứ tự trình bày mặc định cho mỗi khái niệm:

1. Bài toán hoặc câu hỏi mà kỹ thuật cần giải quyết.
2. Giải thích trực giác bằng ngôn ngữ thông thường.
3. Sơ đồ luồng dữ liệu hoặc ví dụ nhỏ có input/output cụ thể.
4. Các thành phần chính và vai trò của từng thành phần.
5. Một công thức tối thiểu nếu thật sự cần để hiểu cách tính.
6. Liên hệ trực tiếp tới code, dataset và kết quả thực nghiệm.
7. Ưu điểm, hạn chế và trường hợp nên sử dụng.

Quy tắc dùng công thức:

- Không đưa công thức chỉ để làm nội dung có vẻ học thuật hơn.
- Không trình bày chứng minh dài, khai triển vi phân nhiều bước hoặc ký hiệu không được sử dụng
  trong code/thực nghiệm.
- Mỗi công thức xuất hiện phải được giải thích ngay bằng lời, định nghĩa mọi ký hiệu và có ví dụ
  số hoặc tensor shape đơn giản khi phù hợp.
- Ưu tiên sơ đồ, bảng so sánh, pseudocode ngắn và ví dụ trước công thức.
- Phần “hợp các hàm” chỉ cần biểu diễn chuỗi xử lý ở dạng dễ đọc, ví dụ
  `đầu vào → tiền xử lý → lớp 1 → ... → đầu ra`; ký hiệu
  `F = f_L ∘ ... ∘ f_1` được dùng một lần để đáp ứng yêu cầu và luôn đi cùng sơ đồ bằng lời.
- Công thức bắt buộc giới hạn ở những phần cần thiết cho việc hiểu code scratch: hàm dự đoán,
  loss, cập nhật trọng số, convolution, trạng thái RNN và các cổng LSTM. Chỉ nêu dạng cốt lõi,
  không đưa suy diễn đầy đủ nếu không phục vụ việc hiện thực.
- Chi tiết toán học mở rộng, nếu cần lưu để đối chiếu, đặt trong phụ lục hoặc tài liệu kỹ thuật,
  không làm gián đoạn mạch đọc của chương chính.

Tiêu chí đọc hiểu: một sinh viên đã học lập trình và toán đại cương phải hiểu được ý chính mà
không cần tra thêm tài liệu toán chuyên sâu. Mỗi mục lý thuyết phải trả lời được ba câu hỏi:
“dùng để làm gì?”, “dữ liệu đi qua mô hình như thế nào?” và “kết quả được đánh giá ra sao?”.

## 2. Hiện trạng và vấn đề phải xử lý trước

Snapshot kiểm kê ngày 2026-10-16:

- Git đang theo dõi khoảng 55.865 file; pack/loose object xấp xỉ 1,82 GiB.
- `A05/` khoảng 53 nghìn file/0,95 GiB; phần lớn là dataset và output sinh lại được.
- `term_paper/` khoảng 0,90 GiB; `knowledge_rag/` và output render chiếm phần lớn.
- `backend/.venv/` khoảng 0,48 GiB, là venv duy nhất; chưa có PyTorch/TensorFlow.
- `mobile/` khoảng 0,26 GiB nhưng không còn thuộc sản phẩm đích React web + Python API.
- GPU: NVIDIA GeForce RTX 5050 Laptop, 8 GiB VRAM, compute capability 12.0.
- Python hiện tại 3.12.3; web có `/ml`, `/cnn`, `/rnn`, `/rag`, chưa có Chương 6.
- CNN/RNN hiện hữu chưa đạt quy tắc trên 5 lớp; A06 chưa có huấn luyện LSTM đầy đủ.
- Bản V2 đã phát hành: `term_paper/report/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx`,
  86 trang, SHA-256 `d7286dd4867e6216f197414e42fc112a3759621c017839fa9b1491b7c5dbfa51`.

Không xóa mù quáng. Phase 20 phải tạo manifest KEEP/MIGRATE/REGENERATE/REMOVE, đối chiếu hash
và giữ bản V2 trước khi dọn. Kế hoạch này **không cho phép tự viết lại Git history**; việc dùng
Git LFS/filter-repo chỉ là bảo trì tùy chọn cần người dùng phê duyệt riêng.

## 3. Kiến trúc đích của repository

```text
assign/
├── apps/
│   ├── api/                    # Python API, job/inference/comparison
│   └── web/                    # React UI
├── src/
│   ├── common/                 # seed, schemas, metrics, device, artifact I/O
│   ├── ch02_ml/
│   ├── ch03_cnn/
│   ├── ch04_rnn_lstm/
│   ├── ch05_knowledge_rag/
│   └── ch06_multi_agent/
├── experiments/
│   ├── configs/                # immutable experiment configs
│   ├── runners/
│   └── notebooks/              # notebooks mỏng, gọi code trong src
├── data/
│   ├── registry.yaml
│   ├── raw/                    # ignored, immutable after download
│   ├── interim/                # ignored
│   ├── processed/              # ignored hoặc chỉ manifest nhỏ
│   └── splits/                 # versioned IDs/hash, không chứa dữ liệu lớn
├── artifacts/
│   ├── manifests/
│   ├── metrics/
│   ├── figures/
│   └── models/                 # checkpoints lớn ignored
├── report/
│   ├── sections/
│   ├── references/
│   ├── tools/
│   └── build/
├── releases/
│   ├── v2/                     # baseline chỉ đọc
│   └── v3/
├── scripts/                    # bootstrap, doctor, data, train, verify
├── tests/
├── docs/
└── TIEU_LUAN_AI_V3_EXECUTION_PLAN.md
```

Nguồn code nằm trong `src/`; notebook không chứa bản sao độc lập của thuật toán. Raw data,
venv, `node_modules`, checkpoint, cache và render QA không được commit. Artifact nhỏ cần cho
báo cáo được version hóa bằng manifest và hash.

## 4. Ma trận dataset đã chọn

Số dưới đây là thông tin công bố ban đầu. Phase 23 phải đo lại file local và ghi số chính xác.

| Chương | ID | Nguồn chính | Quy mô công bố | Vai trò |
|---|---|---|---:|---|
| 1 | `ch1_iris_history` | UCI Iris | 150 mẫu, 4 feature, 3 lớp | Case study lịch sử phân loại |
| 1 | `ch1_mnist_history` | MNIST/LeCun | 70.000 ảnh, 28×28, 10 lớp | Case study deep learning sớm |
| 1 | `ch1_imagenet_history` | ImageNet/ILSVRC | chỉ metadata/citation | Mốc AlexNet; không tải full dataset |
| 2 | `ch2_cdc_diabetes` | UCI CDC Diabetes Health Indicators, DOI 10.24432/C53919 | 253.680 mẫu, 21 biến | Phân loại 3 mức/nhị phân, ưu tiên tiểu đường |
| 2 | `ch2_ames_housing` | AmesHousing/project paper | 2.930 bất động sản, 82 trường | Hồi quy giá nhà |
| 2 | `ch2_bank_marketing` | UCI Bank Marketing, DOI 10.24432/C5K306 | 45.211 mẫu, 16 feature | Phân loại mất cân bằng, đối chứng miền |
| 3 | `ch3_idrid` | IDRiD Grand Challenge/IEEE DataPort | 516 ảnh fundus 4288×2848, nhãn DR 5 mức | CNN ảnh tiểu đường |
| 3 | `ch3_eurosat` | EuroSAT/Zenodo | 27.000 ảnh 64×64 RGB, 10 lớp | CNN viễn thám |
| 3 | `ch3_cifar10` | University of Toronto CIFAR-10 | 60.000 ảnh 32×32 RGB, 10 lớp | CNN benchmark vật thể |
| 4 | `ch4_gold_pink_sheet` | World Bank Commodity Markets Pink Sheet monthly | 1960–hiện tại; đo lại khi tải | Forecast giá vàng đa biến theo tháng |
| 4 | `ch4_bis_house_prices` | BIS Selected Residential Property Prices | hơn 300 series, khoảng 60 quốc gia | Forecast chỉ số giá nhà đa chuỗi theo quý |
| 4 | `ch4_household_power` | UCI Household Power, DOI 10.24432/C58K54 | 2.075.259 dòng, 9 biến, 1 phút | Forecast chuỗi dài, kiểm tra RNN/LSTM |
| 5 | `ch5_medquad_diabetes` | MedQuAD snapshot đã khóa | 47.441 QA local; lát cắt 247 query | KG–RAG y khoa/tiểu đường |
| 5 | `ch5_finqa` | FinQA snapshot đã khóa | 8.281 public QA + 919 private-test | KG–RAG tài chính có bảng/số học |
| 5 | `ch5_wikidata_subgraphs` | Wikidata snapshot đã khóa | 10 entity, 2.056 claim local | KG nền có provenance |
| 6 | `ch6_diabetes_tasks` | view từ Ch2 + Ch5 | khóa ở Phase 31 | Router/tool/critic miền tiểu đường |
| 6 | `ch6_house_tasks` | view từ Ames + BIS | khóa ở Phase 31 | Agent phân tích giá nhà |
| 6 | `ch6_gold_tasks` | view từ World Bank Pink Sheet | khóa ở Phase 31 | Agent phân tích chuỗi vàng, không tư vấn đầu tư |

Nguồn tham chiếu chính:

- CDC Diabetes: <https://archive.ics.uci.edu/dataset/891/cdc%2Bdiabetes%2Bhealth%2Bindicators>
- Ames Housing: <https://github.com/topepo/AmesHousing>
- Bank Marketing: <https://archive.ics.uci.edu/dataset/222/bank%2Bmarketing>
- IDRiD: <https://idrid.grand-challenge.org/Data/>
- CIFAR-10: <https://www.cs.toronto.edu/~kriz/cifar.html>
- World Bank Pink Sheet: <https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/>
- BIS property prices: <https://data.bis.org/bulkdownload>
- UCI Household Power: <https://archive.ics.uci.edu/dataset/235/individual%2Bhousehold%2Belectric%2Bpower%2Bconsumption>

IDRiD có thể yêu cầu chấp nhận điều khoản/tải thủ công từ IEEE DataPort. Phase 23 phải tạo đúng
drop path và verifier. Nếu quyền truy cập không được cấp, không tự thay bằng Kaggle mirror không
rõ license; ghi `PENDING_USER_DOWNLOAD` và tiếp tục các dataset khác.

## 5. Môi trường và chính sách GPU

Runtime chuẩn là **WSL2 Ubuntu 24.04 + Python 3.11 + `uv`**, dùng NVIDIA driver của Windows.
Không lấy native Windows TensorFlow GPU làm chuẩn vì TensorFlow chỉ hỗ trợ GPU native Windows
đến 2.10; bản mới dùng WSL2.

Để vừa đồng nhất thao tác vừa tránh xung đột CUDA:

- `.venv-torch`: NumPy scratch, PyTorch CUDA, EDA, API và công cụ chung.
- `.venv-keras`: Keras với TensorFlow GPU để giữ implementation độc lập thật sự.
- Hai env dùng cùng Python minor, cùng phiên bản package dữ liệu, cùng schema/split/config và
  được điều khiển bằng một bộ lệnh `scripts/bootstrap`, `scripts/doctor`, `scripts/run_experiment`.
- Pin chính xác chỉ được chốt sau probe RTX 5050/sm_120 trong Phase 21; không đoán wheel CUDA.
- Nếu TensorFlow stable chưa hỗ trợ sm_120, fallback được phép là Keras 3 backend PyTorch,
  nhưng phải ghi rõ trong report/UI và không gọi đó là TensorFlow comparison.
- Scratch ưu tiên CPU/NumPy để thể hiện thuật toán. GPU chỉ dùng nếu có backend mảng riêng được
  kiểm chứng; tuyệt đối không che giấu device.
- Tất cả bảng thời gian ghi OS, CPU/GPU, driver, framework, dtype, batch size, warm-up và số lần lặp.

Smoke test bắt buộc: nhận đúng GPU, matrix multiply, CNN forward/backward, stacked RNN
forward/backward, stacked LSTM forward/backward, Keras fit một batch, PyTorch fit một batch,
VRAM telemetry và CPU fallback.

## 6. Hệ đa agent và web đích

### 6.1. Chương 6

Không dựa vào AutoGen cũ làm lõi. Xây một orchestrator nhỏ, xác định được và không yêu cầu API key:

```text
User task
  -> RouterAgent
  -> DiabetesSpecialist | HouseSpecialist | GoldSpecialist
  -> Verifier/CriticAgent
  -> ReporterAgent
```

Ba cấu hình so sánh:

- A0: direct tool/single response, không orchestration.
- A1: router + specialist.
- A2: router + specialist + verifier + reporter.

Metric: routing accuracy, task success, numeric parity, citation/provenance correctness,
unsafe/unsupported claim rate, refusal correctness, latency, message count và peak memory.
LLM local/remote chỉ là adapter tùy chọn; đường chạy deterministic phải hoạt động không API key.

### 6.2. React UI

Thanh điều hướng cấp một:

`Tổng quan | ML | CNN | RNN–LSTM | KG–RAG | Multi-Agent`

Trong mỗi tab kiến thức:

- 3 tab con dataset theo ma trận ở Mục 4;
- Data card: link, size, sample, distribution, nhận xét;
- Theory/Functions: hợp hàm, sơ đồ shape, giải thích từng hàm;
- Run/Compare: chạy inference hoặc job demo cho tất cả implementation hợp lệ;
- Results: metric, confusion/error chart, timing, memory, parameter/layer count;
- Deployment: trạng thái API/model, limitations, artifact hash.

RNN–LSTM phải cho chọn `RNN`/`LSTM` và hiển thị 3 framework song song. UI không huấn luyện full
dataset trên Render; huấn luyện GPU diễn ra offline/local, Render chỉ inference trên checkpoint
đã khóa và các demo job nhỏ. Multi-Agent có trace graph, message timeline, evidence và verifier result.

## 7. Giao thức đánh giá chung

- Seed chuẩn: 42; phase triển khai có thể thêm 3 seed `{17, 42, 73}` cho độ ổn định.
- Validation dùng cho tuning; TEST niêm phong trước tuning và chỉ mở một lần/config release.
- Classification: accuracy, macro-F1, weighted-F1, per-class recall, confusion matrix, AUROC khi hợp lệ.
- Regression/forecast: MAE, RMSE, MAPE/sMAPE khi mẫu số hợp lệ, R² cho tabular; thêm horizon-wise error.
- Efficiency: train wall time, inference p50/p95, peak RAM/VRAM, checkpoint size, parameter count.
- Mỗi metric row chứa dataset version, split hash, code commit, config hash, seed, device và framework.
- So sánh thống kê dùng mean/std trên seed; không tuyên bố hơn hẳn chỉ từ một run.
- Nội dung y khoa chỉ mang tính học thuật, không chẩn đoán. Nội dung vàng không phải khuyến nghị đầu tư.

## 8. Bảng phase

| Phase | Tên | Dependency | Trạng thái |
|---:|---|---|---|
| 20 | Đóng băng V2, kiểm kê và dọn repository | 0–19 | `COMPLETE` |
| 21 | Chuẩn hóa WSL2/GPU và lock môi trường | 20 | `COMPLETE` |
| 22 | Khóa SRS, kiến trúc, schema và giao thức V3 | 21 | `COMPLETE` |
| 23 | Thu nhận dataset mới và registry provenance | 22 | `COMPLETE` — bổ sung IDRiD 516 ảnh/nhãn; 15 ready, 3 Ch6 declared; khóa mới giữ baseline |
| 24 | EDA, data card, split và leakage audit | 23 | `COMPLETE` — 18 card, 9 split/9 folds, 55 CSV/19 hình; 263 test PASS; khóa 294 file |
| 25 | Lõi dùng chung, model contract và hợp hàm | 24 | `COMPLETE` — 9 adapter/36 contract; 330 test, coverage 95,67%; CPU/GPU parity và khóa 219 file |
| 26 | Chương 2: ML/MLP scratch–Keras–PyTorch | 25 | `COMPLETE` — 54 run/3 TEST seal một lần; 299 test, coverage 92,12%; khóa 1.032 file |
| 27 | Chương 3: CNN scratch–Keras–PyTorch | 25 | `COMPLETE` — 27 CNN + 9 majority/3 TEST seal count1; 293 test, coverage 93,11%; khóa 2.378 file |
| 28 | Chương 4A: RNN scratch–Keras–PyTorch | 25 | `COMPLETE` — 108 RNN +24 baseline validation-only;309 test, coverage90,22%; khóa7.386 file; TEST chung Phase29 |
| 29 | Chương 4B: LSTM scratch–Keras–PyTorch | 28 | `COMPLETE` —108 LSTM/108 CPU receipt;60 joint TEST/111.900 prediction;366 test/0skip; khóa6.197 file/verify PASS; revision schema được duyệt, giữ failed seal gốc |
| 30 | Hợp nhất và regression Chương 5 KG–RAG | 25 | `COMPLETE` —341 test/0skip,coverage89,28%;3 notebook/10 QA slot+10 entity;7 hình QA/r2; khóa12.153 file/verify PASS; TEST count1 không đổi |
| 31 | Chương 6: hệ đa agent và benchmark | 26, 29, 30 | `COMPLETE` —300 task/900 result;352 test/0skip,coverage91,53%;3 notebook/9 CPU slot;5 hình active QA/r2; bảo toàn29.004file; khóa1.709file/verify PASS |
| 32 | Python API, artifact registry và deploy contract | 26–31 | `COMPLETE` —359test/0skip,coverage88,70%;HTTP CPU18/GPU12,36parity;60slot/480run; bảo toàn30.713file; khóa1.645file/verify PASS; chưa cloud deploy |
| 33 | React UI nhiều tab và so sánh đồng thời | 32 | `COMPLETE` |
| 34 | Viết và tích hợp báo cáo 6 chương | 24–33 | `COMPLETE` |
| 35 | Build DOCX, render QA, release và bàn giao | 34 | `COMPLETE` — DOCX202trang, QA202/202, Word16/82test/23E2E PASS; khóa391file và verify PASS. Smoke local, chưa cloud deploy |

## 9. Chi tiết từng phase

### Phase 20 — Đóng băng V2, kiểm kê và dọn repository

**Mục tiêu:** có repository gọn, phục hồi được và chỉ còn một đường phát triển V3.

**Công việc:**

1. Hash và sao lưu logic bản DOCX V2 cùng source/manifests tối thiểu vào `releases/v2/`.
2. Sinh inventory theo file/size/tracked/ignored/hash và phân loại:
   `KEEP`, `MIGRATE`, `REGENERATE`, `REMOVE`, `MANUAL_REVIEW`.
3. Khóa whitelist source/notebook/model/report cần giữ từ `pipeline/`, `A05/`, `A06/`,
   `term_paper/`, `backend/`, `web/`; ghi lý do cho từng nhóm.
4. Tạo cấu trúc đích Mục 3; migrate source cần dùng, không copy output nặng.
5. Xóa đúng target đã xác minh: `.venv`, `node_modules`, cache, nested `.git`, render page tạm,
   duplicate raw data/checkpoint/metric, mobile app không còn dùng và output có thể sinh lại.
6. Cập nhật `.gitignore`, README và `docs/repository_manifest.md`.
7. Không rewrite history; báo riêng kích thước working tree và `.git` còn lại.

**Đầu ra:** manifest CSV/JSON, deletion log, keep-list, V2 release hash, cấu trúc V3 sạch.

**Nghiệm thu:** không mất DOCX V2; mọi file xóa có lý do và recovery source; không còn venv,
`node_modules`, cache hay duplicate dataset/model trong cây làm việc; tests nguồn được giữ còn import được.

### Phase 21 — Chuẩn hóa WSL2/GPU và lock môi trường

**Mục tiêu:** một lệnh bootstrap và một lệnh doctor tái tạo được hai env GPU nhất quán.

**Công việc:** kiểm tra WSL/NVIDIA; chốt wheel chính thức hỗ trợ sm_120; tạo lockfiles; cài hai env;
viết PowerShell wrapper và Bash scripts; chạy toàn bộ smoke test GPU/CPU; ghi device manifest.

**Đầu ra:** `pyproject.toml`, lockfiles theo backend, `scripts/bootstrap*`, `scripts/doctor*`,
`artifacts/manifests/environment.json`, hướng dẫn VS Code/Jupyter.

**Nghiệm thu:** fresh bootstrap thành công; PyTorch và Keras train được một batch trên GPU hoặc
fallback Keras được công khai; test CNN/RNN/LSTM backward không lỗi; peak VRAM dưới 8 GiB.

### Phase 22 — Khóa SRS, kiến trúc, schema và giao thức V3

**Mục tiêu:** loại bỏ mơ hồ trước khi tải dữ liệu/huấn luyện.

**Công việc:** tạo requirement traceability matrix; khóa outline 6 chương; API/artifact schemas;
quy tắc layer count; model/data/run contracts; naming; metric; split; TEST seal; page budget dự kiến;
risk register; mapping report–code–web; khóa style guide lý thuyết theo nguyên tắc dễ hiểu,
formula-minimal và quy tắc chuyển phần toán mở rộng xuống phụ lục.

**Đầu ra:** `docs/srs_v3.md`, `docs/traceability_v3.csv`, JSON Schemas, ADRs và architecture diagram.

**Nghiệm thu:** mọi câu yêu cầu của giảng viên/người dùng map tới ít nhất một phase, artifact và test;
không còn thuật ngữ “Keras”/“scratch”/“trên 5 layer” chưa định nghĩa; có checklist kiểm tra mọi
công thức đều cần thiết, được định nghĩa ký hiệu và giải thích bằng lời.

### Phase 23 — Thu nhận dataset mới và registry provenance

**Mục tiêu:** tải snapshot thật, hợp pháp và kiểm chứng được cho toàn bộ ma trận.

**Công việc:** viết downloader idempotent; tải nguồn chính; ghi license/citation/access time/version;
hash từng file; validate schema; lưu manifest; xử lý IDRiD manual drop nếu cần; không tải ImageNet full;
không nhân bản Ch5/Ch6 raw data.

**Đầu ra:** `data/registry.yaml`, raw manifests, dataset cards bản nguồn, download/verify scripts.

**Nghiệm thu:** mỗi dataset có URL, license status, byte size, logical size, SHA-256 và verifier;
mọi file lớn ignored; rerun không tải lại file đúng hash.

### Phase 24 — EDA, data card, split và leakage audit

**Mục tiêu:** tạo phần dữ liệu hoàn chỉnh trước khi mô hình hóa.

**Công việc:** EDA tự động + kiểm tra mẫu; target/class/time distribution; missing/outlier/duplicate;
sample input/output; stratified/group/time split; fit preprocessing chỉ trên train; leakage audit;
ước lượng RAM/VRAM; tạo hình publication-ready.

**Đầu ra:** 2–3 data card/chương, split manifests, preprocessing contracts, EDA tables/figures.

**Nghiệm thu:** mỗi card đủ link/size/sample/distribution/comment/limitations; split hash cố định;
không có ID/time/group leakage; hình và số trong card tái sinh từ script.

### Phase 25 — Lõi dùng chung, model contract và hợp hàm

**Mục tiêu:** ba framework dùng cùng hợp đồng thay vì notebook rời rạc.

**Công việc:** xây seed/device/data/metric/artifact core; model registry; layer/parameter counter;
tensor-shape tracer; schema `model_contract.json`; renderer hợp hàm; trainer hooks; checkpoint metadata;
unit tests gradient/shape/parity trên synthetic tiny data. Renderer phải sinh cả phiên bản kỹ thuật
và phiên bản dễ đọc dạng `input → các bước xử lý → output`, để report/UI không buộc người đọc
phải hiểu ký hiệu toán trước.

**Đầu ra:** `src/common/`, config schemas, equation/function table generator và test suite.

**Nghiệm thu:** contract phát hiện mô hình dưới 6 lớp; output shapes/parameter counts đối chiếu được;
scratch numerical gradient check đạt tolerance; artifact không thiếu provenance.

**Bàn giao bắt buộc từ Phase24:** đọc `data/catalog_v3.json`, `docs/phase24_report.md` và lock
`artifacts/manifests/phase24/data_lock.json`. Các module dữ liệu đã khóa không được format/refactor
ngầm. Tạo adapter tensor mới: ordered `output_feature_names`, categorical/label mapping, HWC/NCHW
và test serialize/load roundtrip, cùng input cho ba framework. Named statistics của Phase24 hợp lệ,
nhưng không suy thứ tự feature từ dictionary JSON: writer sort keys, helper transform EDA duyệt
insertion order, nên output trong RAM/đọc JSON có thể khác thứ tự nếu dùng trực tiếp. Phase24 chưa
lưu dense model tensor/chưa train; chốt canonical order ở Phase25 trước mô hình. Giữ scaler/vocab
đã fit train, không refit validation/TEST; đo peak GPU thật thay vì dùng input-byte estimate làm peak.

### Phase 26 — Chương 2: ML/MLP scratch–Keras–PyTorch

**Mục tiêu:** hoàn thiện ba bài toán tabular và phần code Chương 2.

**Công việc:** baseline ML phù hợp; MLP 6 lớp scratch/Keras/PyTorch; cùng split/preprocessing;
train diabetes, Ames, Bank; tuning chỉ validation; calibration/error/fairness proxy hợp lý;
TEST one-shot; sinh bảng/hình/hợp hàm/giải thích hàm và checkpoint demo.

**Nghiệm thu:** 3 dataset × 3 MLP implementation có metric thật; baseline ML riêng; layer count ≥6;
không leakage; bảng so sánh quality/time/RAM-VRAM/size; test inference parity trên sample cố định.

### Phase 27 — Chương 3: CNN scratch–Keras–PyTorch

**Mục tiêu:** CNN đủ sâu trên IDRiD, EuroSAT và CIFAR-10.

**Công việc:** chuẩn hóa image pipeline; augmentation train-only; 5 Conv + 2 Dense; scratch conv,
pool, loss, backward; Keras/PyTorch matched architecture; class weighting cho IDRiD; GPU training;
saliency chỉ dùng như minh họa, không tuyên bố giải thích lâm sàng; TEST one-shot.

**Nghiệm thu:** 3×3 run hợp lệ hoặc scratch matched-subset được dán nhãn rõ; ≥7 learnable layers;
confusion/per-class metrics; layer/shape/function docs; checkpoint inference chạy qua API contract.

**Ghi nhận khi thực thi:** preprocessing matched Phase24 đã khóa `augmentation=none`;
track Phase27 giữ nguyên cho cả ba implementation, không tự thêm augmentation như dự kiến ban đầu.
Đủ 3 seed mỗi implementation, full validation/TEST và class weights train-only cho IDRiD.
Kết quả/khóa và revision trình bày r2 ở biên bản cuối file; không chạy lại TEST để tuning.

### Phase 28 — Chương 4A: RNN scratch–Keras–PyTorch

**Mục tiêu:** Vanilla RNN đầy đủ trên vàng, giá nhà và điện năng.

**Công việc:** tạo causal windows; scaler fit train-only; naive/seasonal baseline; 3 recurrent + 3 Dense;
scratch BPTT và gradient clipping; Keras/PyTorch; multi-horizon evaluation; gradient diagnostics;
khóa config trước TEST.

**Nghiệm thu:** 3 dataset × 3 implementation; ≥6 learnable layers; không future leakage;
metric theo horizon; biểu diễn hợp hàm theo thời gian/tầng; numerical gradient tests trên tiny sequence.

**Khóa Phase 22:** Phase 28 chỉ đánh giá validation; TEST RNN và LSTM được mở chung ở Phase 29,
sau khi đã khóa toàn bộ cấu hình/seed/approved run IDs của cả hai họ.

### Phase 29 — Chương 4B: LSTM scratch–Keras–PyTorch

**Mục tiêu:** bổ sung LSTM thật và so trực tiếp với RNN.

**Công việc:** scratch input/forget/output/candidate gates + BPTT; 3 LSTM + 3 Dense;
Keras/PyTorch matched; cùng windows/splits/budget Phase 28; gate/gradient diagnostics;
so RNN–LSTM theo dataset/horizon/efficiency; TEST one-shot.

**Nghiệm thu:** 3 dataset × 3 LSTM implementation; ≥6 learnable layers; gate equations và từng hàm
được giải thích; bảng RNN vs LSTM; kiểm tra gradient/parity/serialization đạt.

### Phase 30 — Hợp nhất và regression Chương 5 KG–RAG

**Mục tiêu:** đưa Chương 5 cũ vào cấu trúc V3 mà không phá vỡ kết quả đã khóa.

**Công việc:** migrate source/artifacts tối thiểu; giữ hash dataset/config/result Phase 11–19;
chạy regression tests không mở lại public TEST; chuẩn hóa data/model contracts; tạo 3 dataset tabs;
chuyển phần Agent cũ thành cầu nối ngắn sang Chương 6; cập nhật deploy mục cuối chương.

**Nghiệm thu:** metric/citation cũ không đổi; public TEST run count không tăng; local retrieval/demo
và API contract hoạt động; Ch5 không còn trình bày Agent như nội dung thay cho Ch6.

### Phase 31 — Chương 6: hệ đa agent và benchmark

**Mục tiêu:** xây và đánh giá A0/A1/A2 trên ba miền ưu tiên.

**Công việc:** task schema; deterministic router; 3 specialist dùng model/RAG tools đã khóa;
critic/verifier; reporter; timeout/retry/error propagation; trace/provenance; bộ câu hỏi fixed;
safety cases; optional local-LLM adapter; benchmark A0/A1/A2 trên cùng task set.

**Nghiệm thu:** chạy không API key; 3 domain mỗi domain có task train/dev/test hoặc fixed eval rõ;
metric task/routing/citation/safety/latency/message; không đưa dự đoán y khoa/tài chính như lời khuyên;
mọi answer truy ngược tới tool call, artifact version và evidence.

### Phase 32 — Python API, artifact registry và deploy contract

**Mục tiêu:** một backend Python ổn định phục vụ toàn bộ UI và Render.

**Công việc:** endpoints chapter/dataset/model/run/compare/job/agent-trace; request validation;
async job/polling cho demo dài; artifact hash verification; CPU-safe loading; health/readiness;
CORS/env config; size/memory budget; Render blueprint; unit/integration/security tests.

**Nghiệm thu:** OpenAPI/schema khớp frontend; invalid input trả lỗi có cấu trúc; artifact hash mismatch
không làm process crash lặp; local GPU mode và Render CPU inference đều chạy; không chứa secret.

### Phase 33 — React UI nhiều tab và so sánh đồng thời

**Mục tiêu:** thay UI hiện tại bằng giao diện học thuật, rõ và có thể demo.

**Công việc:** top-level tabs và 3 dataset subtabs; reusable DataCard/FunctionComposition/
ModelRunner/Comparison/Deployment components; chạy ba implementation cùng input; RNN/LSTM toggle;
agent trace; responsive/accessibility/loading/error/empty states; chart không gây hiểu sai;
Playwright E2E và production build.

**Nghiệm thu:** mỗi tab đủ data/theory/run/results/deploy; CNN và RNN/LSTM hiển thị đúng 3 dataset;
run-all cho kết quả truy nguồn; URL deep-link; refresh không mất route; API error không làm blank page;
build và E2E đạt.

### Phase 34 — Viết và tích hợp báo cáo 6 chương

**Mục tiêu:** hoàn thiện nội dung học thuật từ artifact thật.

**Công việc:** giữ giọng/style mẫu DOCX; cập nhật Ch1–3; viết lại Ch4 RNN–LSTM; regression Ch5;
viết Ch6; chèn data cards, hợp hàm, từng hàm, layer/parameter tables, metrics, error analysis,
limitations; mục deploy ngắn cuối từng chương; cập nhật mục lục/hình/bảng/tài liệu tham khảo.
Mỗi phần lý thuyết phải đi từ trực giác và ví dụ đến sơ đồ, chỉ sau đó mới dùng công thức tối thiểu;
loại bỏ công thức trang trí, chứng minh dài và ký hiệu không được dùng trong code hoặc phân tích.

**Page budget dự kiến:** Mở đầu 3–4; Ch1 khoảng 8; Ch2 12–15; Ch3 12–15;
Ch4 18–22 do gồm RNN và LSTM; Ch5 12–15; Ch6 12–15; kết luận 3–4. Đây là budget trình bày,
không được kéo dài bằng code dump; code đầy đủ nằm trong repo/phụ lục chọn lọc.

**Nghiệm thu:** mọi số liệu truy tới artifact; mỗi yêu cầu trong traceability matrix có bằng chứng;
không còn chương deploy riêng; heading/caption/cross-reference/citation liên tục; không có placeholder;
mọi công thức đều có giải thích bằng lời và định nghĩa ký hiệu; mỗi mục lý thuyết trả lời rõ “dùng để
làm gì?”, “dữ liệu đi qua mô hình như thế nào?” và “đánh giá ra sao?”.

### Phase 35 — Build DOCX, render QA, release và bàn giao

**Mục tiêu:** phát hành một DOCX V3 đã kiểm tra từng trang và source tái lập được.

**Công việc:** build DOCX mới không ghi đè V2; render PDF/PNG; kiểm tra cover/TOC/page break,
overflow, bảng/hình/caption/font, orphan heading, code readability; spell/style/link/citation audit;
chạy tests cuối; smoke deploy; sinh release manifest/hash và hướng dẫn demo.

**Đầu ra chính:** `releases/v3/Tieu_luan_AI_6_chuong.docx`, PDF kiểm tra, release manifest,
demo guide, environment/data/model hashes và test report.

**Nghiệm thu:** render toàn bộ trang không lỗi; navigation target/caption/reference hợp lệ;
DOCX mở được trên Word; web/API production build đạt; V2 nguyên vẹn; hash release được ghi lại.

## 10. Rủi ro và quyết định mặc định

| Rủi ro | Xử lý mặc định |
|---|---|
| RTX 5050/sm_120 chưa được wheel hỗ trợ | Probe official matrix ở Phase 21; không tự compile; CPU fallback có nhãn |
| TensorFlow/Keras và PyTorch xung đột CUDA | Hai venv khóa riêng trong cùng WSL/runtime contract |
| IDRiD cần thao tác tài khoản | Manual drop path + verifier; không dùng mirror không rõ license |
| Scratch CNN/RNN/LSTM quá chậm | Matched-subset cố định; full TEST giữ nguyên; không so chéo track |
| Mô hình >5 lớp overfit dataset nhỏ | Regularization/early stopping trên validation; vẫn báo limitation, không che metric |
| Gold/house series ít điểm | Dùng multivariate/multi-series windows, rolling-origin validation; không random split |
| Render không đủ GPU/RAM | Train local GPU; deploy CPU inference/demo subset; lazy-load và budget artifact |
| Ch5 TEST bị chạy lại | Regression từ artifact/hash, không rerun evaluator TEST |
| Git vẫn lớn sau cleanup | Báo `.git` riêng; history rewrite/LFS cần phê duyệt riêng |
| Multi-agent phụ thuộc LLM/API | Deterministic core bắt buộc; LLM adapter chỉ optional |

## 11. Definition of Done toàn dự án

- Repository gọn, không chứa môi trường/cache/dataset/model/output lớn bị trùng.
- WSL2 GPU chạy được PyTorch và Keras hoặc fallback được công khai, có lockfile và doctor report.
- Tất cả dataset có nguồn, license, hash, size, sample, distribution, comment và limitation.
- Ch2 có MLP scratch/Keras/PyTorch; Ch3 có CNN scratch/Keras/PyTorch; Ch4 có RNN và LSTM,
  mỗi loại scratch/Keras/PyTorch; mọi mạng sâu có ít nhất 6 learnable layers.
- Hợp các hàm và giải thích từng hàm tồn tại trong code contract, report và UI từ cùng một nguồn.
- Lý thuyết được trình bày cơ bản, dễ hiểu, đủ ý; ưu tiên trực giác, sơ đồ và ví dụ; chỉ giữ công
  thức thật sự cần thiết và mọi ký hiệu đều được giải thích.
- Ba implementation được đánh giá công bằng trên 3 dataset/chương, có metric và efficiency thật.
- Ch5 giữ nguyên tính tái lập; Ch6 có multi-agent benchmark thực và chạy không API key.
- React UI có tab chính/tab dataset, run-all, comparison và trace; Python API ổn định trên Render.
- Deployment chỉ là mục ngắn cuối chương, không phải chương riêng.
- DOCX V3 được render/kiểm tra từng trang, V2 còn nguyên, release có SHA-256 và test report.

## 12. Nhật ký thực thi V3

Chỉ thêm dòng khi phase được thực hiện.

| Ngày | Phase | Trạng thái | Tóm tắt | Artifact/kiểm tra |
|---|---:|---|---|---|
| 2026-10-16 | Plan | `COMPLETE` | Lập kế hoạch V3 Phase 20–35 theo yêu cầu mới | `TIEU_LUAN_AI_V3_EXECUTION_PLAN.md` |
| 2026-10-16 | Plan update | `COMPLETE` | Khóa chính sách lý thuyết dễ hiểu, formula-minimal và nghiệm thu khả năng đọc hiểu | Mục 1.6; Phase 22, 25, 34; Definition of Done |
| 2026-10-16 | 20 | `COMPLETE` | Đóng băng V2; kiểm kê 105.995 file; di chuyển source về apps/src/data/report/experiments; dọn dataset/output/cache/venv cũ | `docs/phase20_report.md`; `artifacts/manifests/phase20/`; `releases/v2/` |
| 2026-10-17 | 21 | `COMPLETE` | Hai env WSL2/Python 3.11.17 đã khóa; PyTorch CUDA 13 và Keras/TensorFlow GPU độc lập; bootstrap/doctor/runner và Jupyter kernels đạt | `docs/phase21_report.md`; `docs/environment_v3.md`; `uv.lock`; `artifacts/manifests/environment.json`; 46 test đạt |
| 2026-10-17 | 22 | `COMPLETE` | Khóa SRS, 54 yêu cầu, outline 6 chương/18 dataset, protocol, 9 schemas, OpenAPI, 4 ADR và style formula-minimal; 31 file có content-hash lock | `docs/phase22_report.md`; `docs/srs_v3.md`; `artifacts/manifests/phase22/`; 121 test đạt, contract coverage 90,27% |
| 2026-10-17 | 23 | `IN_PROGRESS` — user pause | Đã tải 10 snapshot nguồn; tạo 17 manifest/thẻ nguồn; kiểm hash 11.345 raw Ch5; IDRiD tải sau theo lựa chọn người dùng; CIFAR tự dừng khi ổ C xuống dưới reserve 5 GiB. Người dùng yêu cầu lưu checkpoint rồi tiếp tục sau | `docs/phase23_report.md`; `artifacts/manifests/phase23/checkpoint.json`; 59 data test đạt/1 skip + 121 regression test đạt |
| 2026-10-17 | 23 resume | `IN_PROGRESS` | Tiếp tục theo yêu cầu người dùng; ổ C còn khoảng 11,3 GiB; kiểm đúng partial cũ 24 MiB theo hash rồi dọn; tải lại CIFAR chính thức; Phase22 verifier PASS, 121 regression test PASS; đang chờ chuỗi nghiệm thu nguồn đầy đủ | `artifacts/manifests/phase23/`; IDRiD vẫn pending theo lựa chọn cũ |
| 2026-10-17 | 23 acceptance | `COMPLETE` — IDRiD deferred | Tải đủ 11 snapshot tự động/313.065.095 byte; registry V3 đủ 18 ID, 18 thẻ nguồn; deep verifier PASS, khóa 58 file provenance; 77 data + 121 regression test đạt; không đổi V2/Ch5/TEST/môi trường | `docs/phase23_report.md`; `data/registry.yaml`; `artifacts/manifests/phase23/verification.json`; `dataset_lock.json`; IDRiD pending, Ch6 task view declared |
| 2026-10-17 | 23 IDRiD update | `COMPLETE` — IDRiD ready | Nhập ZIP người dùng tải: 516 ảnh RGB/nhãn, official 413 train+103 test, CC BY 4.0; registry 15 ready+3 declared; 97 data+121 regression PASS; deep PASS; khóa mới 62 file, giữ khóa cũ và snapshot 58 metadata; không train/TEST | `docs/phase23_report.md`; `docs/datasets/idrid_manual.md`; `artifacts/manifests/phase23/updates/idrid_20261017_8a9f4752b35d/`; `verification.json` |
| 2026-10-17 | 24 start | `IN_PROGRESS` | Đọc lại toàn bộ plan/spec và kiểm Phase22–23 PASS; tạo EDA/18 card, 9 split, 3×3 rolling folds; 35 unit policy/verifier test PASS; phát hiện CDC trùng feature/nhãn mâu thuẫn và IDRiD 1 ảnh train trùng TEST cần quarantine; đang kiểm độc lập/visual QA/reproducibility trước khóa | `artifacts/manifests/phase24/checkpoint.json`; `report/references/dataset_cards/v3_eda/`; `data/splits/v3/`; chưa train/TEST |
| 2026-10-17 | 24 acceptance | `COMPLETE` | 18 card, 9 split, 9 rolling folds, 55 CSV/19 hình; verifier PASS 38.163 window; 81 quyết định dữ liệu giữ hash qua QA; 142 data+121 regression PASS, coverage 97,58%; khóa 294 file, producer/exporter rerun PASS; không train/TEST/đổi baseline | `docs/phase24_report.md`; `data/catalog_v3.json`; `artifacts/manifests/phase24/data_lock.json`; `verification.json`; `data-tests.xml`; `regression-tests.xml` |
| 2026-10-17 | 25 start | `IN_PROGRESS` | Đọc toàn bộ kế hoạch, kiểm dependency; TDD cho adapter thứ tự feature/label/layout, model contract, scratch primitives, parity và checkpoint; không sửa nguồn dữ liệu/spec đã khóa | `artifacts/manifests/phase25/checkpoint.json` |
| 2026-10-17 | 25 acceptance | `COMPLETE` | 11 core module, 9 adapter, 12 kiến trúc/36 contract/hợp hàm; 330 test PASS, coverage 95,67%; 16 parity case và 24 probe GPU PASS; khóa 219 file; không train data thật/TEST, không sửa UI/DOCX/env | `docs/phase25_report.md`; `docs/model_core_v3.md`; `artifacts/manifests/phase25/core_lock.json`; `verification.json` |
| 2026-10-17 | 26 start | `IN_PROGRESS` | Đọc toàn bộ plan và kiểm Phase25 PASS; triển khai trainer/resume, baseline, diagnostic và one-shot TEST gate bằng TDD; giữ nguyên core đã khóa | `artifacts/manifests/phase26/checkpoint.json` |
| 2026-10-17 | 26 resume / r2 | `IN_PROGRESS` | 29 test CPU/GPU PASS; v1 dừng trước update vì object cache, giữ khai báo/log và snapshot 33 source; r2 dùng Unicode và cache riêng, khóa 54 run rồi bắt đầu train thật. Chưa mở TEST | `docs/phase26_report.md`; `artifacts/manifests/phase26/revision_r2.json`; `revisions/r2/release.json` |
| 2026-10-17 | 26 acceptance | `COMPLETE` | 54 run, 3 TEST seal count=1; 299 test/0 skip; coverage cuối 92,12%; 5 hình/5 CSV, 3 notebook và CPU parity; khóa 1.032 file, giữ V2/Ch5/env | `docs/phase26_report.md`; `revisions/r2/experiment_lock.json`; `report/sections/v3/ch02_ml.md` |
| 2026-10-17 | 27 start | `IN_PROGRESS` | Đọc toàn bộ plan/handoff; triển khai bằng TDD cache uint8 có budget, pixel/ID parity và CNN trainer. Giữ augmentation=none theo preprocessing Phase24 đã khóa; chưa train hoặc mở TEST | `artifacts/manifests/phase27/checkpoint.json` |
| 2026-10-17 | 27 declaration/train | `IN_PROGRESS` | 16 test Torch + 1 Keras GPU PASS; 3 cache uint8 kiểm toàn bộ model pixel hash; 9 probe shape/device PASS, gradient max ~6,4e-6; khóa 27 CNN + 9 majority trước update, bắt đầu controller train tuần tự. 3 test CPU/API/saliency fixture PASS. TEST vẫn kín | `artifacts/manifests/phase27/release.json`; `docs/phase27_operations.md`; `report/sections/v3/ch03_cnn_theory.md` |
| 2026-10-18 | 27 resume | `IN_PROGRESS` | Controller cũ PID2242 đã dừng, có 8/36 selection. Tiếp tục scratch IDRiD seed73 từ immutable epoch007, không train lại run đã chọn. Giữ source fingerprint, TEST chưa mở | `artifacts/manifests/phase27/checkpoint.json`; `active_controller.json`; log train riêng từng lượt |
| 2026-10-18 | 27 training milestone | `IN_PROGRESS` | Hoàn tất 12 lượt IDRiD, 12 EuroSAT và 3 CNN CIFAR seed17; các checkpoint đã có CPU parity. Bổ sung synthetic E2E evaluator/cache/seal PASS và real TRAIN-only API demo IDRiD PASS; metadata máy được xác minh lại. Tiếp tục CIFAR seed42/73, chưa mở TEST thật | `docs/phase27_report.md`; `hardware_snapshot.json`; `resume_measurement_note.json`; `synthetic_evaluator_tests.xml` |
| 2026-10-18 | 27 validation complete | `IN_PROGRESS` | Đủ 36 selection: 27 CNN + 9 majority; CPU checkpoint parity đạt, source42 giữ hash, Ruff PASS. Bắt đầu unit hai env tuần tự, regression/preservation/coverage và pretest audit; chỉ mở CNN TEST sau các gate này. Chưa nghiệm thu phase | `artifacts/manifests/phase27/runs/`; `lint.json`; `scripts/finish_phase27.ps1` |
| 2026-10-18 | 27 acceptance | `COMPLETE` | 27 CNN + 9 majority, 3 TEST seal count1; 293 test, coverage93,11%; khóa2.378 file và audit sau phát hành PASS; r2 chỉ sửa trình bày | `docs/phase27_report.md`; `artifacts/manifests/phase27/experiment_lock.json` |
| 2026-10-18 | 28 start | `IN_PROGRESS` | Đọc toàn bộ plan/handoff; chuẩn bị causal batch reader, trainer RNN/resume, naive/seasonal và rolling validation bằng TDD; giữ core/spec/data và TEST đã khóa | `artifacts/manifests/phase28/checkpoint.json` |
| 2026-10-18 | 28 declaration/train | `IN_PROGRESS` | 26 CPU +1 Keras GPU test PASS, coverage pretrain89%; 12 data view/pixel-free causal cache và 9 shape/backend probe PASS. Bổ sung riêng index gap rolling fold2/3; Keras XLA qua parity/resume, giữ probe cũ. Khóa132 run (108 RNN +24 baseline) trước train, bắt đầu controller tuần tự; không TEST | `artifacts/manifests/phase28/release.json`; `docs/phase28_operations.md`; source fingerprint c7aaafbe11688e15bbc33da23c0bc5558a42ed3662504a5ae018b4d4eb556c70 |
| 2026-10-18 | 28 export incident / decision | `IN_PROGRESS` | 90/132 selection hoàn tất; controller dừng exit1/PID=null. Power PyTorch seed17 train11 epoch/best5 nhưng GPU fused→CPU gate fail1/12. Probe cùng TRAIN/weights: native CPU và GPU unfused khớp NumPy ngưỡng gốc; giữ FAIL gốc. Kiểm854 ref PASS; không TEST. R2 native-CPU export reference mới là đề xuất cần đồng ý; không tự resume/train lại/nới tolerance; telemetry cuối process lỗi còn thiếu | `docs/phase28_export_incident_v1.md`; `artifacts/manifests/phase28/checkpoint.json`; `attempts/export_numeric_probe_v2.json` |
| 2026-10-18 | 28 r2 approved / recovery | `IN_PROGRESS` | Người dùng đồng ý r2;11 test và Ruff PASS trước khai báo. Khôi phục Power PyTorch seed17 từ best checkpoint không thêm update, giữ FAIL GPU/CPU và null telemetry train gốc/schema riêng. Đạt91/132, queue r2 chạy tiếp; không đổi52 source/config/spec/env và không TEST. Nghiệm thu còn cần108 strict native-CPU receipts, audit/test/report/visual QA/release | `docs/phase28_r2_authorization.md`; `revisions/r2/revision.json` SHA11c7251f5dd092ba7c109f4ea512d3062de3cc6dd1514f683dd7aa06bbc771b7; `scripts/finish_phase28.ps1` |
| 2026-10-18 | 28 r2 automatic handoff | `IN_PROGRESS` | Queue đạt92/132 lúc ghi nhận; test aggregate null/n=2 PASS. Bộ chờ đợi132/process exit rồi chạy finish tuần tự, có exclusive lock chống trùng writer; không tự TEST/seal/release. Kiểm153 ref bảo toàn90 selection/source/checkpoint PASS. Chưa có nghiệm thu cuối; đọc process thực/checkpoint, không khởi động queue/coverage thứ hai | `scripts/finish_phase28_after_queue.ps1`; `docs/phase28_operations.md`; queue session8342/waiter session55253 |
| 2026-10-18 | 28 final acceptance checks | `IN_PROGRESS` | Đủ132 selection/controller exit0; sửa finish/check root bằng2 test RED→GREEN.108 native-CPU receipts PASS; auditor metric-order round-trip giữ số đo nguyên vẹn, đối chiếu223.861 prediction/3.954 protected file PASS.309 test/0skip, coverage90,2216%;3 notebook/9 CPU model;7 hình đã xem và seal. Đang tạo release lock, chưa bắt đầu29/TEST | `docs/phase28_report.md`; `docs/phase28_audit_roundtrip_note.md`; `verification.json`; `report_generation.json`; `visual_qa.json` |
| 2026-10-18 | 28 acceptance | `COMPLETE` | 132 selection/223.861 prediction validation;108 CPU receipts,309 test/0skip, coverage90,2216%;7 hình/3 notebook/9 CPU model; khóa7.386 file và verify-lock PASS. Giữ FAIL GPU/CPU gốc và null telemetry Power/PyTorch seed17, không train lại/tuning/TEST. Phần RNN sẵn sàng ghép LSTM ở29, DOCX34–35 | `artifacts/manifests/phase28/experiment_lock.json` SHAafd93a2a8c8c7336670c17c8d30132f5bcc663448f7658f5a3b35d6ae1d6c27e; `docs/phase28_report.md`; `report/sections/v3/ch04_rnn.md` |
| 2026-10-19 | 29 declaration / user pause | `IN_PROGRESS` — user pause | Đọc toàn bộ plan; bảo toàn11.340 file trong6 khóa;28 test pretrain/coverage86,46% và9 real-shape probe PASS. Khai báo108 LSTM trước train;3 Gold seed17 scratch/Keras/PyTorch hoàn tất, strict CPU export PASS. Run thứ4 chưa update vì host dưới5GiB; controller thoát/PID=null. Người dùng chọn lưu checkpoint/tiếp tục sau; không mở TEST. Thêm8 synthetic reader test PASS, bản lý thuyết LSTM riêng; chưa nghiệm thu toàn phase | `docs/phase29_checkpoint_20261019.md`; `artifacts/manifests/phase29/release.json` SHAe25c29bfa7bc957829a7001892eda89a253b5268e5dbdc5381bb81f7ad0ea528; `checkpoint.json`; `report/sections/v3/ch04_lstm_theory.md` |
| 2026-10-19 | 29 resume1 / user pause | `IN_PROGRESS` — user pause | Resume theo yêu cầu từ11,84GiB;312 ref trước/114 ref sau giữ hash. Thêm2 Gold seed42 scratch/Keras PASS, đạt5/108; PyTorch seed42 chưa update vì guard5GiB. Snapshot GPU2,387GiB, pagefile allocated19.307→23.099 MB; sau thoát11,46GiB. Giữ lỗi/source, không hạ reserve/đổi env/xóa dữ liệu/TEST. Người dùng chọn lưu checkpoint, controller exit1/PID=null | `docs/phase29_checkpoint_resume1_20261019.md`; `disk_diagnostic_resume1.json`; `checkpoint.json` PAUSED_USER_REQUEST |
| 2026-10-20 | 29 pretest / TEST schema incident | `IN_PROGRESS` — chờ duyệt revision |108/108 LSTM hoàn tất;108 CPU receipts/183.159 validation audit PASS,330 pretest/0skip/coverage88,02%. Khóa evaluator/60main rồi TEST: Gold/BIS đủ20+20, Power2 result+1 partial; schema phục hồi orphan chỉ cho validation nên finalization TEST lỗi sau khi lưu4.911 prediction. Forensic audit khớp output, không chạy lại TEST;43 claim consumed,17 chưa claim. Giữ failed seal/source/proof/hash/null telemetry. Đề nghị revision finalize saved outputs và continuation17 unclaimed, chưa được duyệt.10 report unit/lint PASS, report pipeline/release còn thiếu | `docs/phase29_test_schema_incident_20261020.md`; `incidents/test_recovery_schema_v1/diagnosis.json`; `checkpoint.json` |

### Biên bản Phase 20

- Giữ DOCX V2/PDF, DOCX A03/A05/A06 tham chiếu, 998 thành viên source snapshot và metrics V2.
  SHA-256 DOCX V2 vẫn `d7286dd4867e6216f197414e42fc112a3759621c017839fa9b1491b7c5dbfa51`.
- Source API → `apps/api/`; React → `apps/web/`; code tái sử dụng → `src/term_paper/`;
  notebook → `experiments/notebooks/legacy/`; manuscript/bibliography → `report/`.
- Giữ một cầu nối `term_paper/__init__.py` để joblib Ch5 tiếp tục load đúng tên lớp cũ.
  Đây là điều chỉnh migration nhằm bảo toàn artifact. Các runner/report builder lịch sử được
  chuyển contract V3 ở Phase 25/30/34, trước khi chạy lại.
- 11.345 file raw Ch5 khớp hash trước dọn; 10 prediction TEST khớp hash; `run_count=1`.
  14 cache upstream FinQA đã được khôi phục đúng commit/hash sau khi verifier phát hiện bị dọn;
  raw snapshot hiện được loại trừ khỏi mọi cleanup cache.
- Đã đạt: 31 test API; 3 smoke scratch forward/backward/save/load; 10 test React; TypeScript;
  Vite production build trước di chuyển; 2 truy vấn KG–RAG thực tế; verifier preservation và deploy.
- Test legacy đầy đủ chưa phải acceptance V3: còn import TensorFlow/PyTorch chưa có trong env cũ.
  Dùng smoke NumPy riêng và không cài framework trong Phase 20.
- Đã gỡ venv cũ sau kiểm tra, dừng helper Black formatter của VS Code đang giữ venv mở.
  Không tạo môi trường mới hoặc tải dataset mới trong phase này.
- Working tree giảm từ khoảng 3,64 GB xuống khoảng 0,33 GB (ngoài `.git`), tiết kiệm khoảng
  3,31 GB. `.git` còn khoảng 1,82 GiB; không commit hoặc viết lại lịch sử.
- Rủi ro chuyển tiếp: index Ch5 lưu bằng sklearn 1.9.0, env cũ là 1.9.1. Demo đạt nhưng cần
  khóa phiên bản artifact hoặc rebuild bundle tương thích ở Phase 21/30 mà không chạy lại TEST.
- Phase tiếp theo: **21 — Chuẩn hóa WSL2/GPU và lock môi trường**.

### Checkpoint Phase 21 — PAUSED ngày 2026-10-16

- Tạm dừng theo yêu cầu người dùng; chờ người dùng giải phóng dung lượng rồi yêu cầu tiếp tục.
- Đã xác minh WSL 2.6.3, distro `Ubuntu-24.04`, Ubuntu 24.04.4 LTS, kernel WSL2 6.6.87.2.
- GPU nhìn thấy từ WSL: RTX 5050 Laptop, 8151 MiB VRAM, driver 591.74, compute capability 12.0.
- Distro lưu trên ổ C. Dung lượng trống trên host từng xuống 0 byte, chưa đủ để cài bộ GPU.
  Khi tiếp tục phải kiểm tra lại dung lượng host, không dựa vào dung lượng ảo 925 GB mà `df /` báo.
- Chưa cài Python 3.11/Linux uv/PyTorch/TensorFlow; chưa tạo env, lockfiles hoặc chạy GPU smoke test.
  Có script đọc metadata PyPI tại `scripts/phase21_package_metadata.ps1`, chưa chạy tải metadata.
- Bước tiếp tục: xác nhận ổ C còn ít nhất khoảng 20 GB hoặc chọn nơi lưu khác; resolve/pin package
  chính thức; tạo bootstrap/doctor và hai env; chạy toàn bộ smoke tests trước khi đánh dấu COMPLETE.
- Anaconda Windows có env `tf312` và `rnn312`; không thuộc runtime V3 đã chọn. Nếu gỡ, người dùng
  cần giữ cấu hình env cho các dự án khác trước. Không tự gỡ Anaconda trong Phase 21.

### Biên bản Phase 21 — COMPLETE ngày 2026-10-17

- Tiếp tục theo yêu cầu người dùng sau khi ổ C đã được giải phóng lên khoảng 22 GiB.
  Tạo hai venv Linux mới và cache hardlink tại `~/.local/share/ai-term-paper-v3/`, tổng khoảng 13 GiB.
- Khóa uv 0.13.1, Python 3.11.17, PyTorch 2.14.1+cu130, Keras 3.15.1, TensorFlow 2.21.0;
  các thư viện dữ liệu/checkpoint dùng cùng version, có `uv.lock` và 3 export requirements có hash.
- TensorFlow ban đầu lỗi library discovery; sửa theo hướng dẫn chính thức và thêm library paths
  riêng cho process/kernel. GPU probe đạt qua PTX JIT; **backend cuối là TensorFlow, không fallback**.
- `scripts/bootstrap.ps1`, `scripts/doctor.ps1` chạy thành công; `run_experiment.ps1` chạy test thành công.
  CNN 7 lớp, RNN/LSTM 6 lớp synthetic đều forward/backward/update được trên cả GPU và CPU.
  Peak allocator GPU: PyTorch khoảng 88,3 MiB, TensorFlow khoảng 64,5 MiB, đều dưới 8 GiB.
- 46 test đạt (31 API, 12 environment, 3 NumPy scratch compatibility); coverage riêng module
  environment 100%; 2 KG–RAG demo query đạt. Không xem đây là training/architecture acceptance V3.
- V2/raw Ch5/prediction TEST giữ hash; `run_count=1`. Không tải dataset mới, không chạy TEST,
  không commit/reset Git, không gỡ Anaconda. Còn 4 cảnh báo sklearn ở preprocessor V2 (1.9.1 vs 1.9.0);
  xử lý migration riêng Phase 30/32 mà không thay artifact niêm phong.
- Hướng dẫn VS Code WSL/Jupyter tại `docs/environment_v3.md`; evidence tại
  `artifacts/manifests/environment.json` và `artifacts/manifests/phase21/`.
- Ổ C còn ít dung lượng dự phòng sau cài; kiểm tra/giải phóng thêm trước Phase 23 tải data lớn.
- Phase tiếp theo: **22 — Khóa SRS, kiến trúc, schema và giao thức V3**.

### Biên bản Phase 22 — COMPLETE ngày 2026-10-17

- SRS + traceability 54 yêu cầu; outline sáu chương/18 dataset; giao thức target/split/metric/
  kiến trúc/budget/seed/TEST; quy tắc lý thuyết cơ bản và checklist công thức; 4 ADR, sơ đồ kiến trúc,
  risk register 16 mục. Tham chiếu `docs/phase22_report.md` để thực hiện các phase sau.
- Chốt scratch NumPy không autograd; Keras backend TensorFlow độc lập hiện tại; MLP/RNN/LSTM
  tối thiểu 6 logical learnable layers, CNN 7; không đếm pooling/normalization/time step/gate.
- Giao thức chính matched-subset, ba seed 17/42/73, 108 neural run dự kiến; không gộp full-data.
  Model/run có preprocessing/dataset/config hashes; job chỉ xếp hạng cùng input/comparison group.
- Chốt CDC binary và Bank bỏ duration cho bài toán trước cuộc gọi. License/raw/schema/số đo/split
  cụ thể vẫn phải kiểm ở Phase 23/24, không xem số công bố hoặc ví dụ schema là kết quả local.
- RNN Phase 28 chỉ validation; TEST RNN/LSTM mở chung ở Phase 29. Ch5 giữ nguyên seal/run_count=1.
- 9 JSON Schemas + 9 synthetic examples, OpenAPI 3.1.1 (16 path thiết kế), guards và offline
  audit PASS. 31 file đặc tả được khóa SHA-256; verifier không ghi đè khóa khi spec đổi.
- 121 test PASS; coverage riêng module contracts (statement+branch) 90,27%; lint/format/AST đạt.
  Bốn cảnh báo sklearn preprocessor V2 vẫn được công khai, không sửa artifact niêm phong.
- So hash trực tiếp 7 config + 23 metric Ch5 khớp inventory trước dọn; preservation verifier giữ
  V2/raw/TEST; environment lock Phase 21 không đổi. Không tải dataset/train/chạy TEST, không sửa
  UI/API live, không build DOCX, không cài env/package mới hoặc commit/reset Git.
- Phase tiếp theo: **23 — Thu nhận dataset mới và registry provenance**; kiểm host/VHD disk và
  license/access trước tải, IDRiD manual drop nếu cần, không sao chép trùng raw Ch5/Ch6.

### Checkpoint Phase 23 — USER PAUSE ngày 2026-10-17

- Người dùng chọn **“Lưu checkpoint, tôi sẽ tiếp tục Phase 23 sau”** sau cảnh báo dung lượng.
  Dừng tải và thực thi phase tại đây; không tự chuyển sang Phase 24, train hay build DOCX.
  Trạng thái nghiệm thu vẫn `IN_PROGRESS`, không phải `COMPLETE`.
- 10 snapshot tải thành công, tổng **143.012.924 byte**: Iris, MNIST, trang metadata ILSVRC2012,
  CDC diabetes, Ames original 2.930 dòng, Bank original, EuroSAT RGB, World Bank Pink Sheet
  October 2026, BIS WS_SPP và household power. Receipts có SHA-256 tại
  `artifacts/manifests/phase23/receipts/`; raw được ignore, chưa giải nén bản trùng.
- Số đo đã xác minh: CDC 253.680 dòng/21 biến (ID không dùng làm feature); Bank 45.211 dòng
  và bỏ duration trước cuộc gọi; EuroSAT 27.000 ảnh RGB; vàng 801 tháng; BIS 35.780 quan sát
  quý không thiếu trên toàn bulk (CHƯA phải panel danh nghĩa chọn cho train); power 2.075.259
  dòng phút (CHƯA tổng hợp giờ). Ch1 MNIST chỉ phục vụ lịch sử; ImageNet chỉ một trang metadata.
- 11.345 raw Ch5 khớp hash inventory Phase 20; toàn corpus MedQuAD có 47.441 QAPair,
  16.407 answer không rỗng, không nhầm với 247 query diabetes đã khóa ở Phase 12.
  FinQA 9.200 record gồm private_test; Wikidata 10 snapshot entity. Không chạy lại TEST.
- Đã tạo **17 manifest và 17 thẻ nguồn** tại `artifacts/manifests/datasets/` và
  `report/references/dataset_cards/v3/`. Ba task view Ch6 là `declared`, không sinh task/raw trùng.
  `data/registry.yaml` hiện **vẫn là registry bảo toàn Phase 20**, builder cố ý chưa thay bằng
  registry V3 khi còn thiếu CIFAR. `registry_build.json` đang FAIL đúng vì thiếu receipt CIFAR.
- IDRiD: người dùng chọn tải sau. Giữ `pending_user_download`, records=null, không thay dataset.
  Hướng dẫn `docs/datasets/idrid_manual.md`; chỉ cần B. Disease Grading. Verifier phải kiểm
  413/103 split, 516 ảnh/nhãn khớp, grade 0–4 và ghi nhận điều khoản trước khi được ready.
- CIFAR: tải chính thức binary TAR, không pickle. Full GET chậm; Range đã kiểm Content-Range
  và MD5 cuối file, nhưng tự dừng khi dung lượng C giảm. SHA/receipt toàn file CHƯA có,
  không nhận 60.000 ảnh local là kết quả đã đo. File tạm Range đã được finally xóa.
  Còn một partial cũ 25.165.824 byte, ignored, KHÔNG phải dataset hợp lệ:
  `data/raw/ch3/cifar10/.cifar-10-binary.tar.gz.fe1b9a4da87b4164a2659ffb5258871f.part`;
  SHA-256 `486a64fcea36e049df29356de72f972e337b37f31be93a1b796bc7a00cbcec2e`.
- Dung lượng host C từng còn 9,8 GiB rồi giảm còn khoảng **2,4 GiB**. PowerShell `Get-PSDrive`
  trả Free=null trong phiên này; phải dùng `.NET DriveInfo.AvailableFreeSpace` và
  `shutil.disk_usage('/mnt/c/DATA/assign')`, không coi null là 0 hay dùng free ảo của WSL root.
- Test đã chạy: **59 data test PASS + 1 CIFAR integration SKIP**, coverage hai module dữ liệu
  khoảng **92%**; **121 regression test PASS**, 4 cảnh báo sklearn V2 đã biết. Lint/format
  đã chạy, nhưng vài chỉnh sửa nhỏ cuối ở source aliases/provenance lock cần lint/test lại khi
  tiếp tục. Chưa có `verification.json` PASS cuối hoặc `dataset_lock.json` Phase 23.
- Không đổi env/uv.lock, không sửa đặc tả Phase 22, raw/config/metric/TEST Ch5 hay V2;
  không commit/reset, không xóa dữ liệu ngoài scope, không sửa UI/API live.

**Khi nhận “làm tiếp phase 23” / “làm phase 23”:**

1. Đọc lại kế hoạch và checkpoint; kiểm tra không còn tiến trình tải Phase 23 cũ.
   Chỉ xem process của đúng module/PID; KHÔNG dump toàn bộ command line hệ thống vì có thể lộ secret.
2. Kiểm `.NET DriveInfo('C:\\').AvailableFreeSpace`; cần ít nhất **6 GiB**, khuyến nghị **10 GiB**
   và ổn định khi tải. Nếu chưa đủ, hỏi người dùng, không hạ reserve 5 GiB hay tự dọn ổ/môi trường.
3. Dọn riêng partial do lần chạy này tạo sau khi kiểm exact path/hash/không còn writer;
   không đụng file người dùng hoặc raw Ch5. Tải lại CIFAR qua
   `scripts.acquire_datasets --dataset ch3_cifar10`; yêu cầu MD5
   `c32a1d4ab5d03f1284b67883e8d87530` khớp và ghi receipt SHA-256 đầy đủ.
4. Chạy `scripts.acquire_datasets --all --offline` để chứng minh 11 snapshot đã đúng hash
   không gọi network; chạy lại `scripts.build_phase23_registry` để sinh đủ registry V3/18 contract.
   Nếu IDRiD chưa được cung cấp, vẫn giữ trạng thái pending theo lựa chọn người dùng.
5. Chạy lại lint/format, data tests trên snapshot thật (không còn CIFAR skip), regression;
   `scripts.verify_phase22`; `scripts.verify_phase23 --deep --lock` (chỉ tạo khóa lần đầu).
   Kiểm protected config/metric và TEST seal, lưu evidence cuối; không đánh giá lại TEST.
6. Đọc kết quả thật rồi cập nhật `docs/phase23_report.md`, README, bảng trạng thái/nhật ký;
   chỉ đánh dấu COMPLETE khi nghiệm thu đạt cho phạm vi tự động và ghi riêng IDRiD deferred.
   Phase 24 có thể làm các dataset khác; IDRiD vẫn là gate trước nghiệm thu ma trận CNN Phase 27.

### Biên bản Phase 23 — COMPLETE phạm vi tự động ngày 2026-10-17

Checkpoint tạm dừng và các bước resume phía trên là **lịch sử đã xử lý**, không phải việc còn chờ.
Người dùng yêu cầu tiếp tục sau khi giải phóng ổ C lên khoảng 11,3 GiB. Không tự chạy Phase 24.

- CIFAR binary đã tải xong 170.052.171 byte, MD5 chính thức
  `c32a1d4ab5d03f1284b67883e8d87530`; SHA-256
  `c4a38c50a1bc5f3a1c5537f2155ab9d68f9f25eb1ed8d9ddda3db29a59bca1dd`.
  Đo đủ 60.000 ảnh (50.000 train/10.000 test); không nạp pickle. Đã dọn đúng partial cũ
  24 MiB sau kiểm path/hash và không còn writer; không xóa dữ liệu khác.
- 11 snapshot tự động tổng 313.065.095 byte, 11/11 rerun `--all --offline` đều `reused`.
  Không tải ImageNet full, không giải nén bản trùng, không nhân bản raw Ch5/Ch6.
- `data/registry.yaml` V3 đã phát hành đủ **18 ID**: 14 `ready`, 1 `pending_user_download`
  (IDRiD) và 3 `declared` (task view Ch6 sẽ tạo ở Phase 31). Có 18 manifest và 18 thẻ nguồn.
  Đây là nghiệm thu thu nhận nguồn, chưa phải EDA/split/preprocessing/training.
- Deep verifier PASS: 11.356 file raw/476.033.475 byte, 8 inventory archive với 27.061 thành viên;
  tất cả raw ignored; 58 file provenance được khóa tại `artifacts/manifests/phase23/dataset_lock.json`.
  Không ghi đè khóa khi có sai lệch; IDRiD nhập sau cần cập nhật có phiên bản, giữ khóa hiện tại.
- 11.345 raw Ch5 vẫn khớp baseline Phase 20. 31 file đặc tả Phase 22, 7 config + 23 metric Ch5,
  10 prediction TEST và V2 giữ hash; `run_count=1`, `uv.lock` không đổi. Không chạy evaluator TEST.
- **77 data test PASS, không skip**, **121 regression test PASS** (tổng 198). Coverage ba module
  dữ liệu/import khoảng **94%**; từng module đều trên 80%. Lint/format 13 file Python đạt.
  Thêm guard trạng thái nguồn, khóa không ghi đè, cap CSV IDRiD và test EOL Git;
  YAML/JSONL được giữ LF để không vỡ hash sau checkout Windows. Bốn warning sklearn V2 vẫn công khai.
- IDRiD tiếp tục chờ tải thủ công theo quyết định người dùng: records=null, license pending,
  không thay dataset và không bịa kết quả. Hướng dẫn `docs/datasets/idrid_manual.md`.
  Đây là ngoại lệ được chấp nhận cho thu nhận tự động, **không** phải nghiệm thu IDRiD/CNN đủ ba tập.
- Không đổi UI/API live, không train, không build DOCX, không cài env/package hay commit/reset Git.
  Tài liệu vận hành và mapping archive/alias: `docs/datasets/README.md`.
- Phase tiếp theo: **24 — EDA, data card, split và leakage audit**. Làm các nguồn đã ready;
  giữ IDRiD là gate riêng trước EDA của chính nó và nghiệm thu đầy đủ CNN ở Phase 27.

### Bổ sung Phase 23 — IDRiD READY ngày 2026-10-17

Biên bản này cập nhật trạng thái hiện hành; các mục IDRiD pending/deferred phía trên là lịch sử.
Người dùng đã cung cấp ZIP B. Disease Grading và yêu cầu cập nhật Phase 23.

- Đủ **516 ảnh RGB 4288×2848**, **413 train + 103 test**, CSV nhãn DR grade 0–4 khớp toàn bộ ảnh.
  ZIP đã kèm CSV và license, không cần tải CSV riêng hay gói A/C. Chưa EDA/split validation/train.
- File hiện hành: `data/raw/ch3/idrid/manual/B_Disease_Grading.zip`, **212.405.123 byte**,
  SHA-256 `8a9f4752b35d74cc35ff48b21ad44f295a6f800110ec218fc2d1c264803e4d8c`.
  Chỉ chuẩn hóa tên ZIP ngoài cho schema đã khóa; không sửa byte hoặc tên file bên trong.
  Không giải nén bản trùng. License **CC BY 4.0** được xác lập từ declaration và toàn văn trong ZIP.
- Dùng ID `official_split/image_stem` vì train và test trùng basename; loader Phase24/27 phải
  theo `image_index.json`, không gộp basename. Official TEST giữ riêng, không tuning.
- Registry **18 ID: 15 ready, 3 Ch6 declared**. Ch6 task benchmark vẫn thuộc Phase31.
  Khóa mới: `artifacts/manifests/phase23/updates/idrid_20261017_8a9f4752b35d/dataset_lock.json`
  gồm **62 file**; khóa gốc giữ nguyên SHA-256
  `afc01c76d35ac4c2b34134632a33fd367e1d8dea931bdf650d4471b435adc4c1`.
  Snapshot 58 metadata cũ tại `artifacts/manifests/phase23/snapshots/pre_idrid_v1/` được kiểm hash.
  Không nhân bản raw; 17 registry entry khác và evidence không thuộc IDRiD giữ nguyên.
- Deep verifier PASS: **11.357 raw file / 688.438.598 byte**, **9 archive / 27.581 thành viên**,
  raw ignored; 31 file spec Phase22, môi trường, V2, Ch5 raw và 10 prediction TEST không đổi,
  `run_count=1`; Phase22 verifier cũng PASS 7 config/23 metric Ch5. Không chạy TEST evaluator.
- **97 data test + 121 regression test PASS** (218 tổng, không skip; 4 warning sklearn V2 đã biết).
  Coverage bốn module dữ liệu/import khoảng **96%**, từng module trên 80%; lint/format 9 file đạt.
  Đã kiểm chạy lại import/builder không ghi đè khóa hoặc trả IDRiD về pending.
- Evidence: `verification.json`, `idrid_manual.json`, `idrid-data-tests.xml`,
  `idrid-regression-tests.xml`, `idrid_data_coverage.json`, `checkpoint.json` trong manifest Phase23;
  receipt gốc/chuẩn hóa, image index và import result trong thư mục update.
- **Bước tiếp theo: “làm phase 24”** — EDA/data card/split/leakage audit gồm cả IDRiD.
  Không tự chạy Phase24, không đổi spec đã khóa, UI/API/DOCX hay commit Git ở lần cập nhật này.

### Biên bản Phase24 — COMPLETE ngày 2026-10-17

- Tạo 18 card mới ở `report/references/dataset_cards/v3_eda/`, không ghi đè source card Phase23.
  Catalog `data/catalog_v3.json` nối source/EDA/card/split/preprocessing cho report/code/web.
- Ch2–4 có 9 split contracts, 9 preprocessing states và 3×3 expanding rolling folds (mỗi fold
  train/validation/matched IDs và scaler riêng). Toàn bộ official TEST và full validation giữ nguyên.
  55 bảng CSV sinh từ EDA, 19 hình PNG300dpi/SVG đã xem lại bằng bốn contact sheets.
- CDC 25.772 dòng trùng feature/1.566 nhóm nhãn mâu thuẫn được gom trước split, không sửa nhãn.
  IDRiD 6 dòng pixel trùng/3 nhóm nhãn mâu thuẫn, quarantine đúng 1 ảnh train trùng TEST;
  model train/validation/test là 348/64/103, cộng quarantine đủ 516. Không có patient/spatial key
  xác minh nên không tuyên bố độc lập bệnh nhân/địa lý. Bank bỏ duration và gom 16 duplicate.
- Gold 801 tháng, giải thích lag1; BIS 49 chuỗi Q/N/628, history chung 2002Q1 theo coverage,
  4.689 dòng canonical; power 34.589 giờ, 438 nhãn thiếu không điền. Dùng causal windows;
  38.163 window hợp lệ được verifier đối chiếu source/index/target-time. Calendar-key UTC normalization
  không có nghĩa nguồn power được xác minh timezone/DST. Revision/vintage limitations vẫn công khai.
- Ch1 chỉ lịch sử; ImageNet metadata-only/0 ảnh. Ch5 read-only, không mở QA TEST/private_test;
  ví dụ MedQuAD là retrieval evidence corpus, không gán split khi bundle không có metadata.
  Ch6 chỉ parent views; task/gold/split/benchmark vẫn Phase31, không bịa dữ liệu agent.
- 142 data + 121 regression test PASS (263 tổng, 0 skip); coverage unit+pipeline thật 97,58%,
  từng module >=95%; lint/format 14 Python file PASS. Bốn warning sklearn V2 được giữ/công khai.
  Scan pattern secret giới hạn 9 source không thấy pattern phổ biến, không phải audit toàn history.
- Tái sinh giữ nguyên hash 81 artifact ID/subset/fitted state/cache. Khóa 294 artifact/code/test
  file ở `artifacts/manifests/phase24/data_lock.json`, SHA-256
  `5ae1091892262b0b2e52a570e19963005da6724a736447bd11b4e9be3b60e37e`.
  Gọi lại producer/exporter sau khóa PASS, không ghi đè. CSV và JSON/MD/Python có LF, gzip mtime0.
- Source Phase23/parent snapshot58 và spec31 Phase22 giữ hash; môi trường/V2/raw Ch5/config/
  metric/10 prediction TEST không đổi, Ch5 run_count=1. Không train, model TEST eval, UI/API,
  DOCX, package/env thay đổi, commit/reset hay dọn dữ liệu người dùng trong Phase24.
- Handoff Phase25: dùng named stats đã khóa nhưng xây adapter tensor có canonical feature order
  và test JSON serialization roundtrip, không tin dictionary insertion order của helper EDA.
  Chưa có model tensor/train bị ảnh hưởng. Ghi `output_feature_names` rõ ràng và đo peak GPU thật.
- Evidence tại `artifacts/manifests/phase24/`: `verification.json`, `data-tests.xml`,
  `regression-tests.xml`, `data_coverage.json`, `reproducibility.json`, `visual_qa.json`,
  `memory_plan.json`, `data_lock.json`, `checkpoint.json`. Đọc `docs/phase24_report.md`.
- **Tiếp theo: “làm phase 25”** — không tự triển khai trong lượt Phase24 này.

### Biên bản Phase25 — COMPLETE ngày 2026-10-17

- 11 module core mới, không sửa module dữ liệu Phase24/spec Phase22 đã khóa. Chốt canonical
  feature order qua output_feature_names và JSON roundtrip trên 9 dataset; numeric/categorical,
  target inverse transform, label/class-weight mapping, NHWC/NCHW và 9 rolling-fold adapter có test.
- 12 computational plans/configs và 36 model contracts; 36 bộ bảng hàm JSON/CSV và Markdown.
  MLP/RNN/LSTM 6 lớp, CNN 7 lớp; shape trace và số tham số đối chiếu NumPy/Keras/PyTorch.
  Registry là initialized_only/inference_ready=false, không phải kết quả huấn luyện/deploy.
- Scratch NumPy forward/backward/BPTT/Adam và numerical gradients trên tiny data; native GPU
  update cùng quy ước Adam sqrt(v_hat)+epsilon; recurrent bias thứ hai Torch zero/frozen.
  Keras giữ backend TensorFlow độc lập; backward/update cũng tuân device context.
- Hợp hàm có bản kỹ thuật và luồng bằng lời, signature, vai trò, input/output, tham số,
  công thức cần thiết được giải thích, ví dụ, corner case và mapping ba framework.
- 330 test PASS/0 skip (61 core + 6 Keras + 263 regression), coverage 95,67%, mọi core module
  >=89,9%; lint/format 28 file Python PASS. TDD RED evidence được lưu; bốn warning sklearn V2
  và warning TensorFlow sm_120/PTX JIT được công khai. Không thay backend/dependency.
- 16 parity case CPU/GPU và 24 probe kích thước GPU PASS; ngưỡng gradient symmetric relative
  L2 từng tensor 1e-3, lưu max absolute error. Giữ log lần thử elementwise gần zero thất bại.
  Peak allocator tối đa Torch 125.947.904 byte, TF 134.422.272 byte; chỉ synthetic workload,
  không phải peak toàn training hoặc tổng VRAM. RSS là high-water cả đời process.
- Safe NPZ weights checkpoint có CPU load, hash/dtype/shape/finite/budget và 9 provenance
  hashes; E2E synthetic kiểm update/save/load/parity/explain. Không xem là full optimizer resume.
- Khóa 219 artifact/code/test file, SHA-256 core_lock.json
  `596e500edf30f4ab6440eb050f3ff2c274c30a9e02e062831a338ad83fa647d1`.
  Đọc `docs/phase25_report.md`, `docs/model_core_v3.md`; kiểm bằng `scripts/check_phase25.ps1`.
- Giữ 31 file spec Phase22, 294 file Phase24, môi trường, V2/raw/config/metric/TEST Ch5;
  run_count=1. Không train dữ liệu thật, model TEST evaluation, UI/API/DOCX, commit/reset hay cleanup.
- Bàn giao Phase26: dùng core/adapter/weights đã khóa; tạo run ledger, TEST evaluator/seal,
  checkpoint/metric mới và nhóm so sánh theo seed/run ID; không ghi đè registry initialized.
  Ch2 input widths 21/313/50. Ch4 feature widths 4/51/14, context 24/12/168.
  Phase27 thêm batch/cache uint8 cho CIFAR TAR.GZ trước train, giữ pixel/ID parity và budget.
  Phase28 chỉ validation, Phase29 TEST RNN/LSTM chung; Ch5 không mở lại TEST.
- **Tiếp theo: “làm phase 26”** — không tự huấn luyện trong lượt Phase25 này.

### Biên bản Phase26 — COMPLETE ngày 2026-10-17

- 54 run hoàn tất: 27 MLP scratch/Keras/Torch và 27 baseline; 3 dataset CDC/Ames/Bank, 3 seed 17/42/73, cùng matched train và full validation/TEST.
- MLP có 6 learnable layers; parameter counts 9.249/27.937/11.105. Giữ core Phase25, spec Phase22, adapter và preprocessing Phase24 nguyên hash.
- TEST 3 dataset đều evaluated/evaluation_count=1, 18 run mỗi seal; không mở lại TEST Ch5. Audit sau TEST chỉ đọc prediction đã lưu.
- 299 test PASS/0 skip: 33 Phase26, 263 regression, 1 preservation, 2 report/notebook. Coverage trước TEST 87,64%, sau pipeline 92,12%; Ruff PASS. Giữ/công khai 4 warning sklearn V2 và TF sm_120/PTX.
- 108 run-summary row, 564 aggregate row, 5 CSV, 5 PNG300dpi/SVG đã xem; bản thảo Ch2 dễ hiểu, có code/mapping/hợp hàm, data cards, metric, error/group/calibration và deploy ngắn.
- 54 checkpoint CPU parity; demo seed42 nạp 18 model, 3 notebook CPU chạy được không import GPU framework. Registry trained riêng, không ghi đè registry initialized Phase25.
- V1 preflight dừng trước update vì object cache được giữ cùng snapshot33 source. r2 dùng Unicode/cache riêng. Auditor dtype round-trip có phiên bản, giữ tolerance1e-10; không sửa source train/evaluator hoặc metric/checkpoint đã khai báo. Đọc docs/phase26_report.md.
- Khóa 1032 file: artifacts/manifests/phase26/revisions/r2/experiment_lock.json, SHA-256 dcf18106ea7ccdd75843cd44f2061ccab492b9e274eaea9e63900a6125198d1c. Đã đọc lại toàn bộ hash PASS; public wrapper scripts/check_phase26.ps1 chỉ audit sau khóa.
- Raw 11.357 file, DOCX V2, 7 config/23 metric/10 prediction Ch5 giữ hash, run_count=1; không đổi env/UI/API/DOCX, không commit/reset/cleanup.
- Đầu ra chính: report/sections/v3/ch02_ml.md; docs/phase26_report.md; docs/phase26_operations.md; artifacts/manifests/phase26/revisions/r2/.
- **Tiếp theo: “làm phase 27” — CNN**, không tự bắt đầu trong lượt Phase26. Tích hợp DOCX vẫn Phase34–35.

### Biên bản Phase27 — COMPLETE ngày 2026-10-18

- Đủ 27 CNN train độc lập scratch/Keras/PyTorch + 9 majority trên IDRiD/EuroSAT/CIFAR-10,
  seed17/42/73. 5 Conv + 2 Dense, 7 learnable layers; 10.157/10.322/10.322 tham số.
  Matched train348/3.000/5.000, full validation64/4.050/5.000; preprocessing Phase24 giữ
  augmentation=none, class weights IDRiD train-only; không sửa 42 source đã khai báo.
- Cache uint8/batch reader có budget256MiB/reserve host5GiB, đối chiếu mọi pixel/ID Phase24;
  CIFAR TAR binary một stream, không pickle. TEST cache chỉ dựng sau consumed claim.
- Scratch NumPy CPU; Keras TensorFlow GPU graph và PyTorch GPU eager độc lập, canonical Adam.
  Resume scratch IDRiD seed73 từ epoch7, không train lại selection đã hoàn tất; giữ optimizer/
  lịch batch/history. Train time cộng các đoạn; peak RSS chỉ process resume, không ước lượng
  peak process bị ngắt. Giữ metadata máy i7-13620H/RTX5050 và môi trường khóa Phase21.
- Pretest proof khóa evaluator/auditor/tests/coverage trước TEST. Cả 3 seal evaluated/count1,
  12 run mỗi dataset, full TEST103/4.050/10.000; **169.836 prediction row** được audit từ file
  đã lưu. Không TEST forward trong auditor; không mở TEST Ch2/Ch5 hay tuning sau TEST.
- **293 test duy nhất PASS/0 skip**: 26 CNN (25 Torch-env + 1 Keras GPU), 263 regression,
  1 preservation, 3 report/notebook; không cộng trùng 4 demo test hoặc các XML lịch sử.
  Coverage dòng+nhánh93,1083%, statement96,0894%; Ruff PASS. Giữ 4 warning sklearn V2 và
  TF sm_120/PTX; không fallback backend hay đổi dependency. TDD RED evidence được giữ.
- 72 run-summary/288 aggregate/75 per-class-recall row; mean ± sample SD ba seed; confusion,
  learning curves, hiệu năng và saliency TRAIN. IDRiD macro-F1 scratch/Keras/Torch lần lượt
  0,1804/0,1579/0,1454; EuroSAT0,6738/0,6902/0,6983; CIFAR0,5199/0,5086/0,5201.
  IDRiD quality thấp/nhiều lớp recall0; không chẩn đoán hoặc kết luận hơn hẳn theo ba seed.
- 36 checkpoint CPU parity, registry trained riêng; 9 model seed42 chạy demo/API contract,
  3 notebook CPU không import framework GPU, 9 saliency fixed TRAIN. Serving NumPy/CPU
  được ghi rõ khác training implementation; chưa phải HTTP/React/Render live.
- Visual QA sửa chồng số confusion grid10 lớp bằng **revision trình bày r2**: 3 hình mới,
  thang màu count chung và chú thích; r1/manuscript/hình/table giữ nguyên hash, không đổi kết quả.
  7 PNG300dpi/SVG hiện hành đã xem. Pointer `artifacts/manifests/phase27/active_report.json`;
  bản thảo chính **`report/sections/v3/ch03_cnn_r2.md`**, biên bản `docs/phase27_report.md`.
  Lý thuyết cơ bản, giải thích từng hàm/hợp hàm/shape, dataset và deploy ngắn cuối chương.
- Khóa **2.378 file** tại `artifacts/manifests/phase27/experiment_lock.json`, SHA-256
  **`f66f1b5b3793bce8f3a79c0603a2882a7f4173ac11bb51e21c8c3e9c5856522b`**.
  Kiểm chỉ-đọc bằng `scripts/check_phase27.ps1`. Spec31/data294/core219/Phase26r2 1.032 file
  giữ nguyên hash; preservation PASS 11.357 raw file/V2/config/metric/10 TEST prediction Ch5,
  Ch5 run_count=1. Không đổi môi trường/UI/API/DOCX, không commit/reset/cleanup.
- **Tiếp theo: “làm phase 28” — RNN validation-only**; khóa cả RNN/LSTM rồi TEST chung ở
  Phase29. Không tự bắt đầu phase mới. DOCX tích hợp/render cuối vẫn Phase34–35.

### Biên bản Phase28 — COMPLETE ngày 2026-10-18

- 132 selection:27 main RNN +81 rolling RNN +24 baseline causal trên Gold/BIS/Household Power,
  seed17/42/73. Scratch/Keras TensorFlow/PyTorch train độc lập,6 learnable layers; h reset/window.
  Giữ cùng matched windows/scalers/Adam/clip/budget; không tuning sau khai báo.
- 223.861 prediction validation được audit bằng file đã lưu,12 data view,1.334 artifact refs;
  108 strict native-CPU receipts PASS. Không forward validation/TEST trong auditor.
- R2 đã được người dùng đồng ý: khôi phục Power/PyTorch seed17 từ best checkpoint không
  thêm update; giữ GPU/cuDNN→CPU FAIL, dùng native CPU export reference và giữ tolerance.
  Original train/RAM/VRAM null theo recovery schema riêng; cost group n=2, quality n=3.
- Sửa PowerShell root ở finish/check và đối chiếu thứ tự metric sau JSON round-trip bằng TDD.
  Auditor cũ giữ nguyên byte; bản mới so exact row theo name/horizon, không nới tolerance.
  Source52/r2/data/core/spec/weights/metric/prediction đã khóa không bị sửa.
- 309 test duy nhất PASS/0 skip:39 Torch-env +1 Keras GPU +263 regression +1 preservation
  +3 report/notebook +2 PowerShell entrypoint. Coverage90,2216%, statement92,9674%, branch81,5217%.
  Ruff PASS; giữ4 warning sklearn V2 và warning TF sm_120/XLA/CPU-only CUDA discovery.
- 132 run/660 aggregate/396 horizon/540 horizon aggregate/2.244 series row;7 PNG300dpi/SVG
  đã xem, legend rolling/forecast ngoài axes trước seal.3 notebook/9 seed42 CPU model PASS.
  Bản thảo `report/sections/v3/ch04_rnn.md` dễ hiểu, có data/hợp hàm/giải thích từng hàm,
  code3 loại, quality/cost/gradient/limitations và deploy ngắn; chưa phải Chương4 RNN–LSTM đầy đủ.
- Main validation: RNN kém last-value ở Gold/BIS, tốt hơn hai baseline ở Power; giữ kết quả âm,
  không chọn lại hyperparameter. Handoff33 main checkpoint (27 RNN +6 baseline) riêng với rolling.
- Khóa7.386 file tại `artifacts/manifests/phase28/experiment_lock.json`, SHA-256
  `afd93a2a8c8c7336670c17c8d30132f5bcc663448f7658f5a3b35d6ae1d6c27e`; verify-lock PASS.
  `checkpoint.json` COMPLETE; kiểm chỉ-đọc bằng `scripts/check_phase28.ps1`.
- Spec31/data294/core219/Phase26r2 1.032/Phase27 2.378 file giữ hash; preservation giữ11.357
  raw file/V2/7 config/23 metric/10 TEST prediction Ch5, run_count=1. TEST Phase28 count=0.
  Không đổi env/UI/API/DOCX, commit/reset/history hoặc dọn dữ liệu người dùng.
- **Tiếp theo: “làm phase29” — LSTM**; chỉ mở TEST chung sau khi cả hai họ và evaluator/approved
  run IDs khóa. Không tự bắt đầu29; tích hợp HTTP/React32–33 và DOCX/render34–35.

### Nhật ký Phase29 — RESUME2 đang thực hiện,19/10/2026

- Người dùng đã yêu cầu tiếp tục, hủy USER PAUSE trước đó. Runtime Ubuntu-24.04 cũ không
  còn đăng ký; recovery r1 trong Ubuntu/user tuananh đã PASS4 probe GPU/CPU và package parity.
  Giữ uv.lock/metadata cũ/69 source train; dùng wrapper `-Distribution Ubuntu`, không chạy lại
  bootstrap/doctor cũ. Chi tiết declaration/probe/source pin ở Phase29/runtime_recovery/r1/.
- Snapshot73/108 selection: vàng/BIS đủ72, Power scratchs17 main xong. Queue3767/session29693
  đang chạy; trạng thái hiện hành phải đọc checkpoint/active_controller. Không train lại5
  selection có sẵn hoặc mở thêm queue/coverage writer. C còn32,55GiB ở lần đo bàn giao.
- Evaluator/cache/CPU receipt/validation audit/pretest proof/saved-TEST audit mới có38 synthetic
  test PASS +lint16 file PASS; chưa phải nghiệm thu toàn phase, chưa có TEST thật.
- Bộ chờ Windows22436/session42613 đang giữ exclusive handle, đợi108/controller thoát rồi
  hậu kiểm tuần tự; tuyệt đối không tự lock-test/test/release. Không sửa EVAL_SOURCE_FILES hoặc
  chạy thêm acceptance writer khi bộ chờ đang hoạt động. Sau proof đổi code cần revision.
- Chỉ mở TEST chung sau108/CPU receipts/tests/coverage/audit/proof PASS và evaluator/approved60
  khóa. Sau đó audit saved outputs, lập bảng/hình/bản thảo RNN–LSTM/notebook/demo/QA/khóa release.
  Không mở TEST Ch2/Ch3/Ch5, không đổi null telemetry orphan RNN, không gọi CLI là HTTP live.
- Bàn giao đầy đủ: `docs/phase29_checkpoint_resume2_20261019.md`. Phase29 vẫn IN_PROGRESS;
  không tự chuyển30. Tích hợp UI/API32–33, DOCX34–35 chưa làm trong phase này.

### Biên bản Phase29 — COMPLETE,20/10/2026

- Người dùng đã đồng ý revision TEST schema r1. Finalize orphan Power/RNN/PyTorch/s17 từ
  đúng4.911 prediction đã lưu, không forward lại; chỉ tiếp tục17 run chưa claim, đủ17/17.
  Giữ nguyên43 claim/42 result gốc, Power failed_sealed/count1 và null train/RAM/VRAM;
  effective completion ghi ở ledger revision riêng, không mở thêm batch TEST.
- Đủ108 LSTM selection/108 native-CPU receipts; audit183.159 validation prediction.
  TEST chung60 unique main member/111.900 prediction row ×3horizon:27RNN+27LSTM+6baseline.
  Controller finished/PID=null; không có queue train/TEST cần resume. Không train hoặc TEST lại.
- Nghiệm thu366 test duy nhất/0skip; coverage core90,3581%, revision93,4959%, report89,8574%.
  Ruff và PowerShell parser PASS; bảo toàn11.340 file thuộc sáu khóa Phase22–28, raw/V2/Ch5.
  Pretest proof/coverage/evaluator cũ không bị ghi đè; FAIL gốc giữ nguyên.
- Bản thảo Ch4 hợp nhất `report/sections/v3/ch04_rnn_lstm.md`; pointer
  `artifacts/manifests/phase29/active_report.json`.7 CSV/9 PNG+SVG đã visual QA PASS;
  3 notebook CPU/18 checkpoint slot PASS; registry trained/evaluated60 model riêng Phase25.
  Vàng/BIS kém baseline được báo cáo trung thực; Power tốt hơn baseline. Không tuning TEST.
- Khóa6.197 file ở `artifacts/manifests/phase29/experiment_lock.json`, SHA-256
  `1dbed9e911025069644e4cf74638ff427e6d79b0686d710d86581efed1b58143`;
  verify-lock PASS, checkpoint COMPLETE. Source/evidence/report đã khóa không sửa/format;
  đổi sau phát hành cần revision mới. Kiểm chỉ-đọc bằng `scripts/check_phase29.ps1 -Distribution Ubuntu`.
- Runtime Ubuntu/user tuananh và recovery r1 giữ nguyên; không doctor/bootstrap cũ. Bàn giao
  `docs/phase29_report.md`, `docs/phase29_operations_r1.md`. CLI/notebook NumPy CPU chưa phải
  HTTP/React/Render live; API/UI32–33, DOCX34–35. **Tiếp theo “làm phase30”**, không tự bắt đầu.

### Nhật ký Phase30 — nghiệm thu cuối đang thực hiện,20/10/2026

- Đọc toàn bộ plan/manifest và kiểm dependency25; source adapter mới chỉ ở
  `src/ch05_knowledge_rag/`, giữ pure functions/index/namespace `term_paper` cũ.
  Snapshot11.490 asset PASS, gồm11.345 raw Ch5/7config/23metric/10prediction TEST;
  TEST run_count1 không đổi, đối chiếu6.045 saved prediction không inference.
- Ba dataset-tab descriptor,15 non-neural contract slot (10QA available/5structural
  unavailable),3 notebook CPU (10QA slot+10Wikidata entity) PASS. Không bịa QA TEST thứ ba;
  demo compact/free-question/toàn corpus khác evaluator/candidate-per-split lịch sử.
- 78 Phase30 +263 regression=341 unique test/0skip. Coverage89,2791% dòng+nhánh,
  statement92,1376%, branch80,5970%; Ruff/PowerShell parser PASS. Giữ4 warning sklearnV2.
  Không nâng env/dependency, fit/re-serialize index, sửa source hay TEST đã khóa.
- Visual QA phát hiện font/label cũ và prose trộn TEST+challenge. Presentation r2 riêng
  giữ r1/metric/prediction: entity-linking TEST0/1.053 +challenge8/8 khớp aggregate8/1.061.
  Đã xem đủ7 PNG hiện hành; manuscript `report/sections/v3/ch05_knowledge_rag_r2.md`;
  giữ citation keys; Agent thành cầu nối ngắn và deploy là mục cuối chương.
- Verifier final `scripts.verify_phase30 --lock` đang chạy; tool session27364 chỉ snapshot,
  kiểm process/trạng thái thật trước khi resume. Chưa gọi COMPLETE khi chưa có lock+verify.
  Không mở audit/release writer thứ hai hoặc sửa source/evidence đang được khóa.
- Bàn giao `docs/phase30_report.md`, `docs/phase30_operations.md`, contract extension và
  presentation r2 note. HTTP/React32–33 và DOCX34–35 chưa làm; không tự bắt đầu31.

### Biên bản Phase30 — COMPLETE ngày20/10/2026

- Nghiệm thu341 unique test/0skip; coverage89,2791% combined, statement92,1376%,
  branch80,5970%. XML hiện hành `final-tests-r2.xml`78 test và `regression-tests.xml`263;
  giữ RED/development/lượt65 test trước làm lịch sử, không cộng trùng. Ruff/CLI help/
  PowerShell wrapper parser PASS;4 warning sklearn V2 được công khai, không đổi env.
- Khóa12.153 file `artifacts/manifests/phase30/experiment_lock.json`, SHA-256
  `d04a28e060105dda17c8bf1212068e051dcea5780a25ccb4defc16cf316655ca`;
  đọc lại toàn bộ file verify-lock PASS, checkpoint COMPLETE. Không còn train/TEST/release
  writer cần resume. Check chỉ-đọc: `scripts/check_phase30.ps1 -Distribution Ubuntu`.
- Snapshot11.490 asset giữ hash, raw/config/metric/citation/10TEST prediction Ch5 và
  TEST run_count1 không đổi;6.045 saved row được kiểm không inference. Spec/data/core
  dependency544 file PASS, V2/namespace/env/uv.lock và Phase29 lock giữ nguyên.
- Source tối thiểu KG–RAG ở `src/ch05_knowledge_rag/`;3 dataset-tab descriptor,
 15 extension contract slot (10 QA available,5 Wikidata unavailable cho QA),3 notebook
  CPU/10 QA slot +10 entity PASS. Không fit/rebuild/re-serialize artifact cũ, không
  thay initialized registry Phase25, không gọi Wikidata là QA benchmark thứ ba.
- Bản thảo active `report/sections/v3/ch05_knowledge_rag_r2.md`, chọn qua active_report;
 7 hình PNG300dpi/SVG đã xem/QA PASS. Lý thuyết gọn, hợp hàm/bảng từng hàm; Agent chỉ
  cầu nối sang Ch6; deploy là mục ngắn. R1/baseline vẫn nguyên byte. R2 chỉ sửa font/
  layout/cạnh schema và prose TEST/challenge; metric không thay đổi.
- Mọi source/tests/docs/evidence/report được khóa: không sửa/format/ghi đè XML hoặc
  coverage sau release; đổi cần revision mới. Runtime vẫn Ubuntu/user tuananh, wrapper
  phải override distro; không doctor/bootstrap cũ. Xem docs/phase30_report.md và operations.
- Tiếp theo **“làm phase31”** theo plan, không tự bắt đầu. API contract local/demo không
  phải HTTP/React/Render V3 live; API/UI32–33, tích hợp/build/render DOCX34–35 vẫn chưa làm.

### Biên bản Phase31 — COMPLETE ngày20/10/2026

- Core nhiều vai trò xác định A0 direct/A1 router-specialist/A2 thêm verifier-reporter,
  3 miền diabetes/house/gold; không LLM/key/network. Dùng3 scratch checkpoint seed42
  đã khóa (MLP CDC/Ames,LSTM Gold), serving NumPy CPU; evidence MedQuAD exact lookup,
  BIS/Gold TRAIN-origin. Không gọi lookup ID-bound là hỏi đáp tự do hoặc hệ tự chủ tổng quát.
- Task view mới300 câu (100/miền), template/source split60/20/20. Mỗi miền5category×20task;
  input numeric/evidence từ parent thật, câu hỏi/OOD/unsafe/fault injection ghi rõ synthetic.
  Không clone raw; Gold window có thể chồng context, parent TRAIN không là predictor holdout.
- Active taskset_v2/input_views_v2/results_v2; giữ v1/results làm development history.
  Khóa source/rubric/gold trước TEST: declaration SHA
  `b05d6003eabe626caa75bccc269805ac1e3c6ede94f70e8b86863cfe8271619a`.
  Đủ720 TRAIN/dev+180 TEST tác tử=900 unique result, agent TEST count1; không lặp TEST.
  Audit chỉ đọc saved outputs, đối chiếu schema/DAG/message hash và tái tính metric.
- TEST mỗi miền: A0/A1 18/20,A2 20/20; benign8/8 như nhau. Lợi ích A2 chỉ ở containment
  2 ca numeric/citation tamper đã khai báo; answer completion11/20 so9/20 vì A2 từ chối
  output hỏng. Không coi tool parity là predictive accuracy hay chứng nhận an toàn.
- 352 unique test/0skip (80core,263regression,6report,3packaging), coverage core91,5294%
  dòng+nhánh/94,0199%statement/85,4839%branch. Ruff/AST/wrapper parser PASS; giữ4warning
  sklearn V2, không đổi env.3 notebook/9variant slot CPU TRAIN-only PASS; chưa Jupyter UI QA.
- Bản thảo hiện hành `report/sections/v3/ch06_multi_agent_r2.md`, chọn qua
  `artifacts/manifests/phase31/active_report_r2.json`; rootactive_report/report_generation
  giữ r1 lịch sử.5PNG300dpi/SVG active đã xem; r2 chỉ giải thích node timing0 chưa instrument
  và kết quả containment, không sửa metric/trace.3data card/5mẫu mỗi miền,9function contract,
 2CSV, bibliography mới riêng. Lý thuyết cơ bản, một hợp hàm tối thiểu có giải thích.
- Final hash audit PASS29.004 protected file trong8khóa22/24–30; V2/raw/config/metric/
  prediction/seal cũ giữ nguyên, Ch5 count1 và Power failed seal/null telemetry Phase29
  không đổi. Không train/tuning/TEST lại Ch2–5, commit/reset/cleanup hoặc đổi runtime.
- Khóa1.709 file `artifacts/manifests/phase31/experiment_lock.json`, SHA-256
  `10f0196e8fb340e398146654896d845f65c4230231143c739ce5acb328e455b3`;
  verify-lock PASS, checkpoint COMPLETE, packager thoát0/PID lịch sử không resume.
  Check chỉ-đọc `scripts/check_phase31.ps1 -Distribution Ubuntu`. Source/evidence/report
  đã khóa không sửa/format/ghi đè XML/coverage; thay đổi cần revision giữ bản cũ.
- Bàn giao `docs/phase31_report.md`, `docs/phase31_operations.md`. Local contract chưa là
  HTTP/React/Render live; API32/UI33, tích hợp/build/render DOCX34–35 chưa làm.
  **Tiếp theo “làm phase32”**, chỉ khi người dùng yêu cầu.

### Biên bản Phase32 — COMPLETE ngày21/10/2026

- Backend mới `apps/api/v3/`, không thay API V2. Catalog6chương/18dataset,
  registry_v3 có60slot (36neural seed42,15KG,9agent),766asset/86.079.357byte,
  480descriptor run lịch sử. Dataset overview/results, contract/hợp hàm/từng hàm,
  artifact nội dung, comparison/job/poll/details/cancel/agent-trace và OpenAPI đầy đủ.
  Không đổi schema Phase22; extension3.1.0/body3.0.0 khai báo riêng.
- HTTP CPU packagev2:18case/60slot,55thành công và5WikidataQA unavailable đúng thiết
  kế, browser vẫn có dữ liệu thật. Local GPU12case/36slot:24TensorFlow/PyTorchCUDA
  và12scratchCPU,36parity rtol1e-4/atol1e-5 PASS. Chỉ TRAIN/parentTRAIN, không
  train/tuning/TEST cũ. CPU là NumPy portable của3weights train độc lập, không
  native framework timing. Ch5 free-question khác historical benchmark; Ch6 ID-bound.
- 359unique test/0skip:91acceptance,5auditor,263regression; không cộng XML RED/
  development. Coverage88,6989%combined/90,6533%statement/83,1429%branch.
  AST/Ruff/entrypoint/schema/secret-pattern scope PASS; static type checker chưa
  cấu hình.4warning sklearn V2 giữ nguyên. Không thay uv.lock/env/index/model.
- Async single-host SQLite capability ownership/idempotency,32retained job/TTL30phút;
  một Gunicorn worker/2HTTPthreads, một supervisor flock, job subprocess tuần tự.
  Strict input/CORS/rate/hash/path/budget; không uploaded pickle/path/URL/shell,
  train/TEST/admin API. Artifact hỏng không crash loop; worker chết báo503.
  Deadline/cancel/memory terminate+reap process group, không retry inference đã xong.
- CPU guard448MiB, deadline60s; local GPU4GiB/300s. FinQA peak sampled PSS401,04MiB,
  medical288,72MiB; native GPU cao nhất1.757,98MiB, không VRAM. Monitor0,1s không
  gồm master/OS hoặc peak giữa mẫu. Unit harness2GiB không phải bằng chứng Render;
  live probe dùng guard thật. Không suy cloud fit/SLA/p95 từ một lượt cold batch1.
  Streaming top-k text giữ full immutable index/ranking/corpus/evidence, exact parity;
  các FAIL development/log GPU gián đoạn được giữ, không biến thành PASS lịch sử.
- Compact packagev2:808file/87.996.158byte expanded/74.864.102byte ZIP, SHA256
  `1f38247bf5b2a4a1b1a8036d234e8e1bcfb34931a59d4c41655e6d5da319db54`.
  26CPUdependency exact subset uv.lock; không Torch/TF/Keras trên Render. Blueprint
  riêng `deploy/v3/render.yaml`, active_package/openapi bàn giao cho33. Không cài
  fresh CPU env, tạo cloud service/push repo/tính phí hoặc gọi Render live.
- Bảo toàn30.713unique file/9khóa22/24–31 trước/sau PASS; raw/V2/Ch5 count1,
  original Power failed seal/count1/43claim và null training telemetry giữ hash.
  Recovered metric phục vụ read-only từ revision29, không forward lại.
- Khóa1.645file `artifacts/manifests/phase32/experiment_lock.json`, SHA256
  `6491a5dce969f2fc4028bfcbf29ae261ca193670304676625c98f9e66a8a8eee`;
  verify-lock PASS, checkpoint COMPLETE. Không sửa/format source/docs/test/XML/
  coverage/package/evidence đã khóa; đổi sau release cần revision giữ bản cũ.
  Kiểm chỉ-đọc `scripts/check_phase32.ps1 -Distribution Ubuntu`.
- Hướng dẫn local `scripts/run_api_v3.ps1 -Mode cpu|local_gpu -Distribution Ubuntu`;
  runtime Ubuntu/user tuananh, không doctor/bootstrap cũ. Bàn giao
  `docs/phase32_report.md`, `docs/phase32_operations.md`, contract extension và
  `deploy/v3/README.md`. Chưa React V3 hoặc DOCX; không commit/reset/cleanup.
  **Tiếp theo “làm phase33”**, chỉ khi người dùng yêu cầu; DOCX34–35.

### Biên bản Phase33 — COMPLETE ngày21/10/2026

- React UI hiện hành `apps/web/src/v3/`: sáu tab chương, ba dataset mỗi chương,
  RNN/LSTM toggle; data/theory/run/results/deploy, cùng input so sánh neural/B0–B4/
  A0–A2, agent trace/citation, deep-link/refresh, responsive và accessibility.
  Ch1 chỉ lịch sử/data/theory, không giả train. UI cũ giữ tham chiếu và snapshot ZIP.
- 101 unique test PASS/0skip:60Vitest+10legacy+23Playwright+8Python auditor.
  Coverage UI V3 statements97,06%,branches88,72%,functions95,51%,lines97,52%.
  Lint/type/build/AST/Ruff/5PS entrypoint/YAML PASS; npm audit snapshot0finding.
  Không cộng RED/development/candidate v1/v2 vào nghiệm thu, không claim full-repo coverage.
- Browser Chromium headless23/23, retries0/0flaky;18demo gồm12neural TRAIN,
  3agent parent_train,3KG demo_not_benchmark.60slot:55success+5WikidataQA unavailable
  đúng contract. Neural checkpoint/prediction parity Phase32; không accuracy/TEST mới.
  Marker input_split là scope thật, không nhãn TRAIN-only template cũ; xem scope clarification.
- Bảy PNG desktop/mobile cuối đã xem và seal; Axe/keyboard/width checks PASS.
  Build HTTP thực khớp hash HTML/JS/CSS; source fingerprint
  `622536a29e86a67dd5f149d1c1f252f7b236e98cb625a7dfd2d3eeb2fda3fb50`.
  CPU NumPy portable không native framework timing; KG compact không benchmark equivalence,
  agent deterministic ID-bound không LLM. Null cost/failed seal lịch sử giữ nguyên.
- Audit trước/sau31.641protected file/10parent locks PASS; không train hoặc mở TEST Ch2–6.
  Token sessionStorage/owner scope, input/upload/URL guard, React escape; không raw HTML,
  uploaded pickle/path/URL/secret log. Không đổi Python/env/uv.lock/backend frozen.
- Khóa140file `artifacts/manifests/phase33/experiment_lock.json`, SHA256
  `526c4248bf14175336bdc529c0bb8decc2fde98e19593d305a20c766798d3252`;
  release và public check hash PASS, checkpoint COMPLETE. Không sửa/format source/docs/tests/
  evidence đã khóa; thay đổi cần revision giữ bằng chứng cũ. Không ghi đè XML/coverage.
  Check chỉ-đọc `scripts/check_phase33.ps1 -Distribution Ubuntu`.
- Snapshot preview ZIP `dist/phase33/web-preview-acceptance-v3.zip`, SHA256
  `ed820c8dc1c7d3b47cee9fe320a23e4b1706e3ab95d32cd5d579a1a92f4c652c`.
  Bản này trỏ API local, không public production build. Render blueprint riêng deploy/web-v3/;
  deploy cần API HTTPS/CORS/build URL đúng. Chưa cloud deploy/push/tạo service hoặc DOCX.
- Bàn giao `docs/phase33_report.md`, `docs/phase33_operations.md`. Node22.23.4 portable,
  backend Ubuntu/user tuananh; wrapper run_web_v3 và run_api_v3. API QA PID2942/session64348
  đã TERM đúng identity và thoát0, không queue train/TEST hoặc UI QA cần resume.
  Không commit/reset/cleanup. **Tiếp theo “làm phase34”**, chỉ khi người dùng yêu cầu.

### Biên bản Phase34 — COMPLETE ngày22/10/2026

- Nội dung tích hợp mới `report/phase34/manuscript.md`, chọn qua
  `report/active_manuscript_v3.json`; front matter, mục lục nội dung/hình/bảng,
  Mở đầu, sáu chương, Kết luận,43references và bốn phụ lục. Publication_order
  trong manifest chỉ rõ thứ tự ghép, không ghép cả manuscript và sections gây trùng.
- Ch1 giữ mạch lịch sử, cập nhật CNN/RNN–LSTM và ba benchmark; ImageNet metadata-only,
  không ảnh/thống kê huấn luyện giả. Ch2–6 dùng đúng source active r2/combined/r2/r2;
 43bảng gốc giữ nguyên giá trị. Không sửa bản thảo/model/metric/checkpoint đã khóa.
- 18hồ sơ dữ liệu,36contract/12kiến trúc; hợp hàm/từng hàm/shape/parameter/mapping,
  mẫu input/output, kết quả/chi phí/error/limitations. Triển khai cập nhật API32/UI33
  local, là mục cuối Ch2–6; không chương deploy riêng. CPU portable khác nativeGPU/cloud.
- 58mục cấp hai,143bảng captioned (67thân chương+76phụ lục),37hình nguyên nguồn,
 43citation/55relative target PASS. Outline extension phase34.integration.1 map mục
  dự kiến tới heading thực tế; spec/outline22 giữ hash. Tóm tắt/từ viết tắt riêng.
- 38test r3 PASS/0skip, coverage editor/assembler/auditor92,7512%, mọi module>80%;
  AST/Ruff/format8Python và parserPowerShell PASS, static type checker chưa cấu hình.
  Integration r3 chỉ ghi TemporaryDirectory do test sở hữu, không ghi publication.
  R1/r2/XML/coverage/source ZIP giữ riêng; r2 bổ sung bằng chứng thực thi20–23,
  r3 cô lập test. Không cộng trùng test hoặc biến proof cũ thành source mới.
- Ma trận54yêu cầu có locator/bằng chứng thực thi, ghi rõ DOCX/render deferred35 và
  cloud chưa deploy. Lý thuyết theo ví dụ/trực giác/flow trước công thức cốt lõi;
  không thêm suy diễn dài. Phụ lục D trích5method exact line/hash, không code model mới.
- A06 trích style/text/section XML read-only; hash vẫn
  `9eecf073897b609d9e2d0024bd56594dc6fec99823508e57ed79dff8d4780348`.
  Đây không full render/distillation; style definitions chưa thay thế kiểm direct
  formatting/theme/visual. Handoff `report/phase34/artifact.md`; chưa author DOCX.
- Bảo toàn31.772file/11parent locks trước/sau PASS; nativeWindows cross-check độc lập
  cũng PASS. Không train/tuning/forward validation/TEST hoặc đổi env/uv.lock/V2/rawCh5,
  failed Power seal và null telemetry. Không API/UI cloud mới hoặc commit/reset/cleanup.
- Khóa226file `artifacts/manifests/phase34/experiment_lock.json`, SHA256
  `e4ba90714b4cd42a46eca8702f3c6b3dc2e0ddf1a11141e1df3944c56af8ebbc`;
  release và public verify PASS/checkpoint COMPLETE/PIDnull. Manuscript SHA256
  `dcb895acfd76f1ad616baecd7fdc7fa099becbc0cc508a80b3c0432eabef2b19`.
  Không sửa/format source/docs/inputs/manuscript/manifest/test/proof đã khóa;
  thay đổi cần revision riêng. Chỉ đọc `scripts/check_phase34.ps1 -Distribution Ubuntu`.
- Bàn giao `docs/phase34_report.md`, `phase34_operations.md`, acceptance_revisions,
  outline_extension và requirements_matrix. Runtime Ubuntu/user tuananh, không
  bootstrap/doctor cũ. **Tiếp theo “làm phase35”** chỉ khi người dùng yêu cầu: resolve
  documents runtime/renderer hợp lệ, dựng DOCX mới không ghi đèV2, TOC/SEQ/REF/PAGE,
  render và xem từng trang trước giao. Page count/budget thực tế chưa được nghiệm thu.

### Checkpoint Phase35 — preflight ngày22/10/2026

- Bắt đầu theo yêu cầu người dùng; đã đọc toàn bộ kế hoạch/AGENTS và handoff34.
  Public check34 PASS226file/read_only_no_inference; manuscript/A06/uv.lock/environment
  giữ hash. Không chạy lại unit test34 hoặc model TEST để tạo bằng chứng mới.
- Documents yêu cầu workspace dependency runtime/bundled renderer trước authoring.
  Tool/resource hiện tại không có loader đó; plugin search không tìm đường dựng phù hợp,
  Word document-control không có phiên kết nối. Không dùng desktop Office/LibreOffice
  hoặc env repo thay thế rồi giả PASS. Chưa author DOCX/chạy marker/render mẫu.
- Lưu việc còn lại và điều kiện tiếp tục ở docs/phase35_checkpoint_20261022.md;
  receipt/checkpoint tại artifacts/manifests/phase35/. Phase35 chưa COMPLETE, chưa có
  release Word/PDF hoặc page QA. Cần runtime hợp lệ hoặc quyết định rõ của người dùng
  về phương án dựng local có khóa phiên bản; không thay môi trường GPU đã khóa.
- Không train/tuning/TEST lại, cloud deploy/push/commit/reset/cleanup. Khi tiếp tục
  không resume session/PID lịch sử; dựng output35 mới và kiểm mọi trang trước phát hành.
- Native PowerShell preserve PASS31.848file/12khóa, exit0. Lượt WSL hash trùng bị
  dừng đúng process do agent tạo, không phải hash failure và không cộng là PASS.
  Hai auditor đã thoát; preservation_20261022.json ghi rõ phạm vi hash-only.

### Phase35 — tiếp tục sau phê duyệt runtime/bìa,22/10/2026

- Người dùng đồng ý toolchain local có khóa riêng và giữ thông tin bìa. Runtime tài liệu
  đã PASS reference render32trang; không thay GPU/uv.lock. Ubuntu LO fail giữ r1;
  active TDF26.2.6.3 giữ r2; runtime_ready.json ghi version/hash.
- Full distillation report/phase35/artifact.md; marker DOCX đã chạy1lần. Có ứng viên mới,
  không ghi đè V2/A06/Phase34; native144bảng/37hình/180caption. Development46test PASS;
  Word16 mở r2 chỉ đọc PASS203trang/file giữ hash. R3 đang QA, chưa là bản phát hành.
- Final page-map/render mọi trang/tests/smoke/hash còn lại. Checkpoint35 là hiện hành;
  runtime gate đã giải quyết, không hỏi lại quyền/bìa. Phase35 vẫn IN_PROGRESS.

### Phase35 COMPLETE — phát hành ngày22/10/2026

- File nộp `releases/v3/Tieu_luan_AI_6_chuong.docx`,202trang/11.508.758byte,
  SHA-256 `5daf2aa5b5f587be5f61ecf7a2c6d32dc131c9ae2efe5df8630b4a23387060a5`.
  PDF QA cùng thư mục; release_manifest.json PASS. Giữ thông tin bìa A06 theo xác nhận.
- Native144table(143captioned),37figure+logo,180caption,549bookmark,12OMML;
 256page-cache target đúng. Word16 mở read-only/cập nhật trường trong bộ nhớ PASS202trang,
  error index0, không save/hash không đổi. Rà đủ202trang; carry chỉ khi PNG byte-identical.
-82test/0skip PASS, coverage84,8925%combined/80,4270%branch;23E2E/0retry PASS trên React
  production và compact CPU bundle Linux ext4. Đây local smoke với env hiện có, không
  fresh CPU-only install, Render/cloud/SLA. R1lỗi và các ứng viên cũ giữ lịch sử.
- Bảo toàn31.848file/12khóa cha PASS; không train/tuning/TEST, không đổi GPU/uv.lock,
  raw/V2/checkpoint/metric cũ. Khóa391file `artifacts/manifests/phase35/release_lock.json`,
  SHA-256 `3d66f57de0d5bd48f19b15eaf75c92619519ab9c29a1beb11b469512ea47adab`;
  `scripts/check_phase35.ps1 -Distribution Ubuntu` verify PASS/read-only/no-inference.
- Bàn giao `docs/phase35_report.md`, `docs/phase35_operations.md`, `docs/demo_v3.md`.
  Không resume session/installer/producer/test lịch sử. Đổi bản phát hành cần revision mới.
  Hai probe Word đầu có thể để UpdateLinksAtOpen=False; đã công khai, không tự đoán
  giá trị cũ để đổi ngược. Không còn Word automation hay server demo5000/5173 do task chạy.
- Mục triển khai cloud trong DoD toàn dự án vẫn chưa được nghiệm thu; không biến local
  PASS thành tuyên bố Render live. Không tự deploy tài khoản, commit/reset/cleanup.

