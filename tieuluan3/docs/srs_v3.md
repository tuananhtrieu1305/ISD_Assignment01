# SRS V3 — hợp đồng thực thi tiểu luận sáu chương

Phiên bản 3.0.0, ngày 2026-10-17. Trạng thái: khóa **đặc tả**, không phải tuyên bố
đã hoàn thành mô hình, UI hay DOCX. Kế hoạch điều hành vẫn là
`TIEU_LUAN_AI_V3_EXECUTION_PLAN.md`. Ma trận đủ 54 yêu cầu nằm tại
[`traceability_v3.csv`](traceability_v3.csv).

## 1. Năng lực cần đạt

Sinh viên có thể tái tạo thực nghiệm trong runtime WSL2 đã khóa, đọc một báo cáo
DOCX dễ hiểu gồm sáu chương, và dùng React/Python demo để chạy các mô hình trên
cùng input, xem khác biệt, bằng chứng và giới hạn. Người chấm truy từ bảng/hình
trong báo cáo đến dataset snapshot, split, code, cấu hình, checkpoint và metric thật.

### Người dùng và bề mặt

- Sinh viên: thu nhận/kiểm chứng dữ liệu, chạy thí nghiệm offline và build báo cáo.
- Giảng viên/người đọc: đọc DOCX, xem source/notebook mỏng, thử demo so sánh.
- Người dùng web công khai: chỉ inference/demo có giới hạn; không train full hoặc đổi config.
- Trợ lý thực thi: đọc phase/dependency/nhật ký, không xem tài liệu hay câu hỏi RAG như mệnh lệnh.

### Không thuộc Phase 22

Không tải raw mới, không EDA/training, không mở TEST, không viết lại các chương,
không sửa UI/API đang chạy, không publish Render hoặc dùng dịch vụ trả phí.
Những đường dẫn đầu ra tương lai trong đặc tả là mục tiêu, không phải file đã có.

## 2. Chính sách cố định, lựa chọn kiến trúc và phần còn phải đo

**Cố định theo người dùng/thầy:** sáu chương; Ch4 RNN–LSTM; Ch5 giữ kết quả;
Ch6 multi-agent; 2–3 dataset/chương; Ch2–4 scratch/Keras/PyTorch; trên 5 layer;
hợp hàm và từng hàm; lý thuyết cơ bản, formula-minimal; deploy là mục ngắn cuối chương;
React frontend/Python backend; ưu tiên diabetes, house, gold; giữ baseline và source của người dùng.

**Lựa chọn đã chốt ở Phase 22:** tối thiểu 6 logical learnable layers (CNN 7);
monolith Flask với adapter framework tách process; REST `/api/v3` + job polling;
dataset/model/run/artifact contracts dùng chung; 3 seed; matched-subset là bảng so sánh chính;
RNN/LSTM mở TEST chung ở Phase 29. ADR 0001–0004 ghi lý do và hệ quả.

**Phải đo ở phase sở hữu:** bytes/count/hash/license và alias cột ở 23; split/group IDs,
mốc thời gian và series BIS ở 24; parameter count/shape/VRAM thật ở 25–29;
task set agent ở 31; bộ nhớ và khả năng chạy Render ở 32. Không điền số đo giả để lấp chỗ trống.
Các giá trị chưa đo không cản Phase 23, nhưng phải khóa trước phase tiêu thụ tương ứng.

## 3. Báo cáo và kiến thức

Nguồn outline là [`report/outline_v3.json`](../report/outline_v3.json):

| Chương | Nội dung | Budget trang nội dung |
|---|---|---:|
| 1 | Lịch sử AI, giữ mạch cũ; Iris/MNIST/ImageNet làm case study | 8 |
| 2 | ML cổ điển và MLP ba implementation | 12–15 |
| 3 | CNN ba implementation trên ba dataset ảnh | 12–15 |
| 4 | RNN và LSTM, sáu implementation, so sánh trực tiếp | 18–22 |
| 5 | KB, KG, RAG và kết quả B0–B4 đã niêm phong | 12–15 |
| 6 | Hệ đa agent A0/A1/A2, ba miền và trace | 12–15 |

Mở đầu 3–4 trang; kết luận 3–4; tài liệu tham khảo/phụ lục theo nhu cầu. Budget
không phải lý do kéo dài bằng code dump. Mỗi Ch2–6 có đúng một mục triển khai ngắn
ở cuối; không có “Chương triển khai”. Ch1 không giả làm chương train.

Giữ văn phong/style tham chiếu V2/A06 (baseline chỉ đọc); chuyển builder/sections
sang V3 ở Phase 34–35. `report/sections/05_trien_khai.md` cũ là nguồn tham khảo,
không phải một chương được đưa nguyên vào outline mới. Đầu ra cuối:
`releases/v3/Tieu_luan_AI_6_chuong.docx`, không ghi đè DOCX V2.

Áp dụng [`report_style_v3.md`](report_style_v3.md): mục đích → trực giác → ví dụ →
sơ đồ → thành phần → công thức thật sự cần → code → hạn chế. Mỗi công thức có lý
do, định nghĩa ký hiệu, giải thích bằng lời và ví dụ/shape; chứng minh dài chuyển
phụ lục. Không được bỏ các cổng LSTM hoặc backward cần cho scratch chỉ vì tránh toán.

## 4. Dữ liệu và giao thức đã khóa

Nguồn máy đọc được: [`protocol_v3.json`](../experiments/configs/v3/protocol_v3.json).
18 ID = 3 dataset/benchmark/view cho mỗi chương. Số công bố trong kế hoạch không
được coi là số đo local. Data card phải có URL/license/citation, file bytes, logical
size/schema, input/output mẫu, phân bố, missing/imbalance, nhận xét và hạn chế.

- Ch1: Iris, MNIST làm case study có mẫu từ nguồn chính; ImageNet chỉ metadata/citation,
  không tải full. Không tạo điểm accuracy “mới” cho chương lịch sử.
- Ch2: UCI CDC Diabetes **nhị phân** (`Diabetes_binary`: 0 không tiểu đường,
  1 tiền tiểu đường hoặc tiểu đường), Ames Housing hồi quy giá USD, Bank Marketing
  `bank-full.csv` dự đoán đăng ký trước cuộc gọi. Không dùng `duration`, ID hoặc target làm feature.
  UCI mô tả CDC có chỗ không thống nhất về số nhóm; dùng bảng biến làm đặc tả ban đầu,
  verifier Phase 23 phải kiểm tra raw, không tự chuyển qua bản balanced/ba lớp.
- Ch3: IDRiD grading, EuroSAT RGB, CIFAR-10. Giữ official TEST khi có; resolution,
  subset và augmentation phải giống nhau giữa ba implementation trên cùng track.
- Ch4: World Bank gold theo tháng; BIS house-price index theo quý (không phải giá
  giao dịch căn nhà); household power tổng hợp theo giờ. Target/horizon/lag xem protocol.
- Ch5: MedQuAD, FinQA và Wikidata baseline. Wikidata là KG hỗ trợ có structural audit,
  **không bịa thêm một QA test set hoặc một lần mở TEST thứ ba**.
- Ch6: view nhiệm vụ diabetes/house/gold, tham chiếu snapshot cha, không chép trùng raw.

Nguồn ưu tiên phù hợp bài toán, không thay chỉ để có tên dataset “mới”. Chất lượng
thực tế phải được xác nhận bằng license/schema/EDA ở 23–24. IDRiD thiếu quyền thì
`pending_user_download`, có drop path và verifier; không dùng mirror không rõ phép.
Trước tải cần kiểm tra **host/VHD** và dung lượng giải nén dự kiến + dự phòng; không
coi dung lượng ảo WSL là dung lượng ổ C. Không tự xóa Anaconda/dữ liệu dự án khác.

### Chống leakage và chọn mô hình

1. Khóa group/duplicate identity trước split. Chỉ tuyên bố patient/client/spatial
   independence nếu thật sự có metadata; không suy đoán từ tên file.
2. Tabular 70/15/15, grouping/stratification như protocol. Official TEST được giữ,
   validation chỉ tách từ official train. Phân tầng hồi quy dùng bins theo target
   cho việc phân chia, không đưa target vào input.
3. Imputer/scaler/encoder/class weights/target transform chỉ fit TRAIN; unknown
   category được xử lý rõ. Không dùng validation hoặc TEST để tính statistics.
4. Chuỗi chia theo **thời gian target**, mọi horizon của một mẫu nằm trong cùng
   partition. Input validation/test có thể dùng lịch sử đã xảy ra trước boundary;
   không shuffle tương lai về train hoặc nội suy bằng giá trị tương lai.
5. Mốc ngày/series đủ coverage khóa ở 24 bằng rule đã định, không xem TEST metric.
   Dữ liệu World Bank/BIS là snapshot đã sửa đổi: hindcast học thuật, không khẳng định real-time.
6. Ba expanding-window validation folds chỉ trong vùng trước TEST; scaler fit lại
   theo từng fold. Không lấy kết quả TEST để chọn lookback/horizon/threshold.
7. Fixed learning rate/budget trong protocol; không HPO ngầm. Nếu cần đổi, lập
   protocol deviation trước TEST và áp dụng công bằng cả ba implementation.

## 5. Mô hình, hợp hàm và so sánh

### Định nghĩa có thể kiểm tra

**Scratch:** NumPy array operations, forward/loss/backward hoặc BPTT, optimizer và
predict tự hiện thực. Không gọi autograd/layer/model/trainer của framework. Scratch
mặc định CPU; không ghi GPU chỉ vì env có CUDA.

**Keras:** Keras 3 API, backend hiện tại **TensorFlow** đã được Phase 21 kiểm tra
GPU. PyTorch là implementation trực tiếp bằng torch. Nếu sau này phải dùng Keras
backend torch thì phải lưu probe/deviation và ghi rõ trong metric/UI; không gọi
đó là so sánh TensorFlow độc lập. Hai env Linux và lock Phase 21 không được thay bằng Python Windows.

**Trên 5 layer:** MLP = 5 Dense ẩn + Dense output; CNN = 5 Conv + 2 Dense;
RNN/LSTM = 3 recurrent layers + 3 Dense. Chỉ đếm khối có tham số học được thuộc
dense/conv/rnn/lstm. Input, activation, pooling, dropout, reshape, normalization,
container, time step và từng cổng LSTM không được dùng để đủ số lớp.
Adapter phải khai triển `num_layers=3` thành ba logical layers và đối chiếu weights,
không chỉ đếm số object Python.

**Hợp hàm:** một `model_contract.json` chứa thứ tự function IDs, mô tả luồng bằng
lời, tensor shape và số tham số từng layer. RNN/LSTM còn có unroll theo thời gian/tầng.
Mỗi function ghi signature, input/output/shape, tham số, vai trò, corner case và mapping
scratch/Keras/PyTorch; công thức chỉ khi cần, khi có phải đủ symbols/explanation/example.
Report và UI đọc cùng contract, không tự chép ba mô tả kiến trúc.

### Giao thức so sánh

- Bảng chính `matched_subset`: cùng train IDs, full validation/TEST, resolution/windows,
  preprocessing, seed, weights khởi tạo canonical, batch order, dtype và budget.
- `full_data` chỉ là bảng phụ nếu không đủ cả ba; không so metric/thời gian chéo track.
- Ba seed `{17,42,73}`, seed 42 chính. Ma trận thần kinh dự kiến **108 run**
  (4 family × 3 dataset × 3 implementation × 3 seed), chưa tính baseline và full-data.
  Run chưa hoàn thành/timeout/OOM phải giữ trạng thái thật, không bịa số hoặc giảm
  riêng dataset/layer của một implementation. Một seed không tạo ra độ lệch chuẩn.
- Canonical bias RNN/LSTM chỉ một bias học được: bias thứ hai của PyTorch phải
  zero/frozen khi đối chiếu. Gate order/layout/forget bias/Adam epsilon phải được
  adapter kiểm chứng; fixture Phase 21 không chứng minh parameter parity V3.
- Classification: macro-F1 chính, threshold nhị phân 0,5; metric phụ theo protocol.
  Ames: RMSE/MAE USD sau inverse transform. Forecast: lỗi theo từng horizon/series,
  không gộp USD, index points và kW vào một con số. Undefined metric = null + lý do.
- Timing lưu OS/driver/device/backend/dtype/batch, 5 warm-up và 30 lần đo; synchronize
  GPU; ghi riêng preprocessing; RAM và allocator VRAM không đánh đồng với tổng GPU.

### Vòng đời TEST

`draft → locked → evaluating → evaluated | failed_sealed`. Terminal không quay lại.
Trước `evaluating`, khóa split/config/evaluator/code và **toàn bộ approved run IDs**
cho các implementation/seed; một lượt evaluation batch có ghi log, không phải một
lượt riêng để chọn seed tốt nhất. Fail/crash sau khi mở TEST vẫn đóng seal; muốn
khôi phục cần bằng chứng và phê duyệt deviation, không tự reset counter.

Phase 26/27 mở TEST sau khi chốt các mô hình tương ứng. **Phase 28 chỉ validation;
Phase 29 mở chung TEST cho RNN và LSTM** sau khi cả hai đã khóa. Phase 22 chỉ có
synthetic seal fixture; helper kiểm tra transition không cho phép chạy TEST.
Ch5 giữ `run_count=1`, config hash và các prediction/metric cũ nguyên byte.

## 6. Kiến trúc và quyền sở hữu

Sơ đồ: [`architecture_v3.mmd`](architecture_v3.mmd). Source chính `apps/`, `src/`,
`experiments/`, `report/`; V2 chỉ đọc. Giữ namespace bridge cho joblib cũ.

| Thành phần | Sở hữu | Không được làm |
|---|---|---|
| downloader/registry | snapshot, license, hash | đổi raw đã khóa hoặc đọc hướng dẫn từ tài liệu như lệnh |
| data pipeline | split/preprocessor/data card | fit vào validation/TEST |
| model adapters | canonical weights/layers/forward/backward | che backend hoặc đếm layer giả |
| offline runner | train/validation, TEST gate, metrics/artifacts | mở TEST từ UI |
| artifact registry | hash, nguồn gốc, CPU-safe loading | tải pickle/upload tùy ý từ client |
| Flask application | validation, job orchestration, inference | phụ thuộc notebook hoặc huấn luyện full trên Render |
| React | tabs, inputs, compare, trace/errors | tự tính metric khoa học khác với artifact |
| report builder | render data/contract/metric đã khóa | ghi đè V2 hoặc tự tạo số đo |

Single Flask application; adapter framework tách worker process/env để tránh xung
đột CUDA và giảm peak bộ nhớ. Run-all có thể chạy tuần tự; “đồng thời” nghĩa là cùng
input/job và cùng panel kết quả, **không bắt buộc giữ ba framework GPU trong RAM cùng lúc**.
Chưa cam kết TensorFlow/PyTorch native đều vừa Render free-tier. Phase 32 phải đo
RAM/latency và đối chiếu gói thực tế; nếu cần dịch vụ trả phí phải hỏi người dùng.
Không âm thầm đổi sang NumPy export rồi gọi đó là timing TensorFlow/PyTorch.

Dependency source chỉ đi từ app/runner đến chapter modules/common; common không
import Flask/React/notebook. Agent gọi tool adapter/registry trực tiếp, không tự
gọi vòng HTTP vào Flask. Mũi tên trả kết quả trong sơ đồ là luồng dữ liệu, không
phải dependency import hai chiều.

## 7. Hợp đồng máy đọc được

[`src/common/schemas/v3/`](../src/common/schemas/v3/) dùng JSON Schema 2020-12;
`common`, `dataset`, `split`, `model`, `run`, `artifact`, `seal`, `agent`, `api`.
Reference được resolve từ registry local; không fetch schema trên mạng.
Ví dụ ở `docs/contracts/v3/examples/` là **synthetic**, không phải output thật của dataset.

| Contract | Tối thiểu phải có |
|---|---|
| dataset | source/version/access/license, files bytes/hash, logical size, schema/target, parent views |
| split | dataset hash, seed/method, IDs/count/hash từng partition, train-only flag, leakage audit |
| model | family/implementation/backend, layers/functions/composition/shapes/parameter count, config hash |
| run | dataset/split/config/code+dirty-tree/env hashes, seed/track/device, metric/undefined reason, efficiency |
| artifact | path relative allowlist, bytes/hash, producer, serialization/load policy, CPU-loadability |
| seal | config/split/evaluator hashes, approved runs, state/counter/events |
| agent | taskset hash, variant/domain, ordered DAG nodes/tool/refs/timing/outcomes, citations/limitations |
| API | bounded input, required implementation slots, async job, structured errors, actual backend/device |

Schema kiểm tra cấu trúc; semantic guards bổ sung đếm layer, tổng tham số, backend,
time overlap, completeness và TEST transition. Phase 24/25/32 bổ sung kiểm tra
byte/file/tensor thật; schema hợp lệ **không** đồng nghĩa không leakage hoặc artifact an toàn.
Publish gate bác bỏ synthetic fixture. `legacy_trusted_joblib` chỉ được load theo
manifest/hash allowlist đã bảo toàn, không làm định dạng upload công khai.

Model/run còn giữ `dataset_sha256`, preprocessor artifact ref và
`comparison_group_sha256`; run giữ thêm protocol hash. Group hash được tính từ
dataset/split/subset/preprocessing/kiến trúc/budget/seed chung, **không gồm tên
implementation**. Job và mọi slot có cùng input hash; chỉ xếp hạng khi ba model
thuộc cùng comparison group. Khác track/seed/preprocessing vẫn có thể xem dự đoán,
nhưng comparison_valid phải false và giải thích lý do.

Naming: dataset ID theo bảng đã khóa; `model_id`/`run_id` lowercase snake/kebab,
hash SHA-256 lowercase; đường dẫn POSIX relative từ repo, không `..`/absolute/drive letter.
ID khoa học phải deterministic từ canonical config/snapshot; job/request ID ngẫu nhiên
không dùng để thay split/config hash. Dirty worktree phải có source-tree hash, không
dùng riêng Git commit cũ để nhận là code tái lập. Schema version 3.0.0; thay đổi phá
hợp đồng cần version/deviation, không sửa kết quả sau khi biết TEST.

## 8. API, UI và vòng đời job

OpenAPI thiết kế: [`contracts/v3/openapi.json`](contracts/v3/openapi.json), version 3.1.1.
**Các route V3 chưa được implement trong Phase 22**; Flask V2 vẫn giữ nguyên.
Chuyển health/readiness và compatibility V2 ở Phase 32 có regression tests.

- GET chapters/datasets/models/runs/artifact metadata/model contract/agent trace.
- POST `/api/v3/comparisons` luôn nhận đủ scratch/Keras/PyTorch cho Ch2–4,
  B0–B4 cho Ch5, A0–A2 cho Ch6; POST agent-tasks là convenience cho Ch6.
- POST trả 202 + Location/Retry-After; GET jobs poll; POST cancellations hủy.
- `queued → running → succeeded | partial_failed | failed | cancelled`; job hết TTL → expired.
  Terminal không chạy lại; retry tạo job mới với provenance. Đề xuất TTL 24 giờ,
  poll 1 giây rồi backoff tối đa 5 giây, không giữ input nhạy cảm lâu dài.
- Idempotency-Key bắt buộc cho POST tạo job: cùng key/body trả cùng job trong TTL;
  cùng key khác body trả 409. Run-all dùng **một input hash**, không ba input tự xử lý riêng.
- 400 malformed JSON, 413 payload quá lớn, 415 media type, 422 schema/domain input,
  404 resource, 409 conflict, 429 rate limit, 503 model/worker không sẵn sàng;
  lỗi không lộ traceback/path nội bộ. Một model hỏng phải hiện rõ slot failed/unavailable,
  không để UI blank hoặc gọi comparison đủ ba model khi thực ra chỉ chạy một.
- Public demo read/inference-only; không API train/admin/upload checkpoint. CORS
  allowlist, 30 submit/IP/phút và một heavy job/process là giới hạn ban đầu, đo lại
  ở 32. Body JSON tối đa 7 MiB; image decoded tối đa 4 MiB/16 triệu pixel, magic
  bytes và dimensions phải kiểm tra trước decode/model; không nhận URL ảnh tùy ý.
- Tabular input đối chiếu feature whitelist/model contract; sequence ≤720 bước,
  ≤64 feature, width thống nhất và đúng as-of. Cấm NaN/Infinity.
- Job IDs ngẫu nhiên khó đoán; client không chọn path/tool/command. Logs chỉ giữ
  hash/metadata tối thiểu, không persist PII hoặc câu hỏi thô mặc định. Hash mismatch
  làm một artifact unavailable, không crash-loop toàn process; `/health` còn sống,
  `/ready` trả readiness thành phần và 503 khi mandatory component chưa dùng được.
- Không hứa durable queue qua deploy/restart khi chưa có persistence. Phase 32
  dùng SQLite local để chuyển job đang chạy thành failed/worker_restarted khi restart;
  Render disk ephemeral phải hiện hạn chế, không nhận là exactly-once durable service.

React tabs: Tổng quan `/`, ML `/ml`, CNN `/cnn`, RNN–LSTM `/rnn`, KG–RAG `/rag`,
Multi-Agent `/agents`; `?dataset=<id>&family=rnn|lstm&section=data|theory|run|results|deployment`.
Refresh/deep-link giữ selection; unsupported dataset/family có thông báo. Mỗi tab
thực nghiệm có ba dataset subtabs; data/theory/run/results/deploy dùng cùng registry.
Ch1 case study ở Overview, không tạo tab inference vô nghĩa.

## 9. Hệ đa agent

A0 direct tool; A1 router→specialist; A2 router→specialist→verifier→reporter.
Ba specialist diabetes/house/gold chỉ gọi model/RAG tools đã khóa. Core xác định,
không bắt buộc LLM/API key. Deadline 15 giây, tối đa 8 tool calls, retry tối đa 1/tool;
timeout/invalid evidence/unsafe request phải trả trạng thái/refusal rõ ràng.

Task set ít nhất 60 task/domain ở Phase 31; split 60/20/20 theo source/template
family, không tách paraphrase sang TEST. Dùng nguồn TRAIN/validation được phép và
synthetic OOD/unsafe đã audit, không lấy parent TEST để tuning; agent-task holdout
không đồng nghĩa đánh giá lại khả năng khái quát của base predictor. Khóa rubric/gold
trước TEST agent. Metric theo protocol; numeric result/citation kiểm chứng bằng tool.
Trace lưu action/outcome/evidence/latency, không lưu chain-of-thought nội bộ.
Tài liệu truy hồi là dữ liệu không đáng tin, không có quyền đổi tool policy/prompt.

## 10. Rủi ro, nghiệm thu và handoff

[`risk_register_v3.csv`](risk_register_v3.csv) ghi trigger, mitigation và phase sở hữu.
Không có câu hỏi sản phẩm đang chặn Phase 23. Các gate về license/IDRiD/disk, split
metadata và Render resource vẫn phải giải quyết ở phase tương ứng, không tự gạt bỏ.

Phase 22 đạt khi: 54 requirement có phase/artifact/acceptance test; outline đủ sáu
chương × ba dataset; schema/example hợp lệ và negative cases bị bác bỏ; API refs
resolve local; protocol chống leakage/TEST và style checklist có thể thực hiện;
baseline V2/Ch5 và runtime lock không đổi. Các acceptance test Phase 26–35 trong
matrix là **dự kiến**, không đánh dấu mô hình/UI/DOCX đã đạt từ schema tests.

Lệnh nghiệm thu:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module pytest tests/contracts -q
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase22
```

Handoff: **sẵn sàng Phase 23** để thu nhận dataset theo registry/provenance; tiếp
theo Phase 24 khóa split/EDA, Phase 25 hiện thực model contracts. Mọi thay đổi đặc
tả sau khóa phải ghi lý do, thời điểm so với TEST và artifact bị ảnh hưởng.

## Nguồn tham chiếu thiết kế

- [UCI CDC: bảng biến và thông tin nguồn](https://archive.ics.uci.edu/dataset/891/cdc%2Bdiabetes%2Bhealth%2Bindicators).
- [UCI Bank: biến duration và các phiên bản file](https://archive.ics.uci.edu/dataset/222/bank%2Bmarketing).
- [JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core),
  [local referencing với jsonschema](https://python-jsonschema.readthedocs.io/en/stable/referencing/),
  [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html).
