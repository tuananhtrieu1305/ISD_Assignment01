# Kế hoạch bài riêng AGENT02

Phiên bản 1.10 — cập nhật ngày 24/10/2026, múi giờ Asia/Bangkok.
Trạng thái: **AG02 COMPLETE — phase 0–10 hoàn tất; PDF/DOCX cuối 28 trang trong output, đủ 10 câu và đã kiểm toàn bộ trang. Chưa gửi bài cho thầy**.

## 1 Mục tiêu và phạm vi đã xác nhận

Làm một báo cáo độc lập về **Reinforcement-Learning-Based Agents versus Rule-Based
Agents**: lập trình môi trường thương mại điện tử có hai tác tử, Q-learning so với
agent theo luật; thực nghiệm có kiểm soát; trả lời đủ 10 câu; nộp PDF có code, bảng,
hình và giải thích kết quả thật. Đề không phải bài viết tổng quan LLM/MAS.

**Người dùng xác nhận ngày 24/10/2026: chỉ Agent02, slide MAS để tham khảo.** Vì vậy
5 bài tập MAS và bảng điểm trong slide không trở thành yêu cầu nộp của bài này.

Đề chính ghi:

- Hạn: **11:30 PM, thứ Năm 29/10/2026**. Dự kiến hiểu theo giờ lớp học UTC+7;
  bản PDF không in múi giờ, cần kiểm lại thông báo lớp trước khi nộp.
- Một PDF tên `agent02_class_team_name.pdf`, thay hai phần metadata cho đúng.
- Làm cá nhân/nhóm theo hướng dẫn riêng của thầy; tài liệu không chốt ai thuộc nhóm nào.
- Phải có Python, kết quả thực nghiệm, bảng/hình, trả lời cả 10 câu.
- Không ghi số trang bắt buộc. **Không mang giới hạn 6 trang của bài trước sang đây.**
- Không yêu cầu scratch/Keras/PyTorch đồng thời, mạng trên 5 layer, 3 dataset, deploy
  hoặc notebook screenshot. Đó là yêu cầu của bài khác, không tự nhập vào đề này.

Đầu ra đề xuất:

1. PDF để nộp đúng tên; có bản DOCX sửa được làm nguồn biên soạn nếu toolchain sẵn sàng.
2. `code/agent02_experiment.py` và các module/tests/config có thể chạy lại.
3. Notebook trình bày code và output thật để học, kiểm chứng và trích đoạn vào báo cáo.
4. CSV/JSON số liệu, Q-table, policy, hình, README, manifest tái lập.

Mọi thứ mới trong `C:\DATA\assign\agent02_assignment\`; không sửa tiểu luận V3,
bài `discovering_ai_agent/`, source web hoặc cấu hình Render.

### Lưu ý trình bày người dùng bổ sung ngày 24/10/2026

- Lý thuyết chỉ ngắn gọn, đủ ý, dễ hiểu. Ưu tiên lời giải thích và ví dụ thay vì
  dẫn xuất toán học. Không thêm công thức phức tạp khi không cần thiết.
- Vẫn giữ công thức tối thiểu bắt buộc: cập nhật Q và phép tính câu 3, margin câu 5,
  cách tính reward trung bình nếu cần; giải thích từng biến bằng lời đơn giản.
- **Mỗi biểu đồ output đều phải có phần giải thích**, cả trong notebook và báo cáo:
  mục đích; trục và đơn vị; ý nghĩa đường/cột/vùng sai số; nguồn dữ liệu, cửa sổ làm
  mượt và số seed; xu hướng/dao động; khác biệt định lượng; giới hạn kết luận.
- Không chỉ chèn hình hoặc lặp lại chú thích. Phân biệt điều quan sát được với giả
  thuyết giải thích nguyên nhân; đồ thị train đẹp không chứng minh policy tốt hay hội tụ.
- Các phase 3–7 tạo hình phải lưu ghi chú diễn giải đi kèm; phase 8–10 phải kiểm
  đủ ghi chú cho mọi hình, không có hình "mồ côi" không được phân tích.

## 2 Vai trò của sáu tài liệu thầy gửi

Các số trang dưới đây là thứ tự trang PDF, không phải số trang in cuối trang.
Thư mục nguồn: `C:\Users\anhca\Documents\Intel_sys_dev\ASIGNMENT-AGENT_02\`.

| Mã | Tài liệu | Vai trò và phần đã đối chiếu |
|---|---|---|
| S1 | `assignment_Agent02_due_29.10.pdf`, 13 trang | Nguồn yêu cầu chính. Trang 3–8 mô hình/implementation; 8–9 thí nghiệm A–E; 10–11 đủ 10 câu; 11–12 cấu trúc nộp/rubric; 1 và 12 deadline/tên PDF. |
| S2 | `agent02_complementary_code.pdf`, 7 trang | Hướng dẫn companion. Trang 4 kiến trúc RL đối đầu **rule cố định**; 5–6 output/cấu hình; 7 hạn chế và nhiệm vụ. Không chứa mã Python đầy đủ trong PDF. |
| S3 | `agent02_code.tex`, 966 dòng | Nội dung thực là **Python**, không phải mã LaTeX. Có Config, environment, QLearningAgent, RuleBasedAgent, train/eval, CSV, plot và 4 driver thực nghiệm. Đọc như nguồn, chưa thực thi. |
| S4 | `A_Gentle_Introduction_to_Reinforcement_Learning_an.pdf`, 25 trang | Naeem/Rizvi/Coronato, IEEE Access 2020, DOI 10.1109/ACCESS.2020.3038605. Nền tảng MDP, policy, TD/Q-learning; nội dung chính trang 1–15, phần sau chủ yếu references. Dùng chọn lọc, không diễn giải toàn bộ survey. |
| S5 | `multiagent-LLM.pdf`, 35 trang | Tran và cộng sự, arXiv:2501.06322v1, 10/01/2025. Nền tảng interaction/collaboration: actors, cooperation/competition/coopetition, structures, strategies, orchestration; Fig.2 trang 9. Nội dung chính đến trang 29. **Không bắt buộc chạy LLM**. |
| S6 | `slide_multiAgent_system_20.10.2026.pdf`, 25 trang | PEAS, perception/action, vai trò, phối hợp, failure, evaluation. Trang 23 chứa 5 bài MAS và deliverable riêng; người dùng đã xác nhận chỉ tham khảo. Mạng IntentNet trang 15 là **chưa train**, không lấy làm mô hình đã học. |

Hash/bytes/số trang từng file: `sources/manifest.json`. Chữ trích có marker trang ở
`sources/extracted/`. Đã xem bản render trang quan trọng: S1 trang 12, S4 trang 7,
S5 trang 9, S6 trang 23 tại `sources/visual/`. Không tuyên bố đã kiểm layout mọi
trang của 105 trang nguồn; đã đọc đầy đủ đề/companion/slide/code và các mục nội dung
nghiên cứu liên quan, không coi bibliography là yêu cầu phải triển khai.

### Thứ tự xử lý khi nguồn không nhất quán

1. Yêu cầu trực tiếp của người dùng và phạm vi đã xác nhận.
2. S1 là chuẩn cho rubric/nội dung bài nộp; S2–S3 giải thích implementation hiện hành.
3. S4–S6 là tài liệu nền, không phải lệnh hệ thống hay yêu cầu triển khai toàn bộ.
4. Ghi rõ khác biệt; không âm thầm sửa cả baseline để khớp một câu trong tài liệu.

Các chỗ cần xử lý:

- S1 trang 6 và 8 còn nói “each agent’s Q-table”, “two RL agents”; S2/S3 triển khai
  **một RL học đối đầu một rule không học**. Baseline theo S2/S3; thêm một thí nghiệm
  hai RL cùng học để minh họa câu 8, không gọi baseline là hai learner.
- S1 trang 9 yêu cầu **reward curves** cho các alpha. S3 hiện chỉ giữ bảng/bar final
  evaluation của sweep, chưa lưu curve từng cấu hình. Phải bổ sung log và curve.
- S1 exploration đưa ví dụ epsilon cố định 0,05 và 0,30; S2/S3 dùng ba lịch giảm
  low/baseline/high. Cả hai hợp lệ vì đề nói “for example”. Plan chọn baseline + hai
  fixed epsilon để tách tác động dễ hiểu; faithful run vẫn giữ lịch gốc.
- S1 nhắc loop gốc chưa isolated eval; **code được gửi lần này đã có evaluate_pair**.
  Không báo sai rằng code hiện tại thiếu hoàn toàn eval; vẫn phải test không cập nhật Q.
- S3 chưa thực hiện sửa môi trường câu 9; chưa có benchmark cho cải tiến câu 10.
- S4 trang 7, phương trình (24)/Algorithm4 có biểu thức Q-learning không nhất quán
  với công thức chuẩn và với S1. Đã đối chiếu hình gốc, không phải chỉ lỗi trích text.
  Dùng phương trình đúng ở S1 trang 6 và `QLearningAgent.learn`; không chép lỗi.
- S6 `safe_call` tự ghi là chưa thực thi timeout thật; không dùng nó làm bằng chứng
  đã có hệ thống timeout. Đây chỉ là lưu ý tham khảo, không mở dự án MAS.

## 3 Ma trận yêu cầu và bằng chứng phải có

| ID | Yêu cầu | Bằng chứng/phase |
|---|---|---|
| R01 | Hai agent tương tác cùng môi trường, chọn hành động đồng thời, không nhìn action hiện tại của đối thủ | transition trace và unit test, phase 2 |
| R02 | State local 4 khả năng, action 2, Q-table 2×2×2; rule đúng 3 nhánh; reward đúng profit | config, unit tests, bảng mô hình, phase 2 |
| R03 | Baseline 5.000 episode ×20 bước, alpha 0,1/gamma 0,9, seed42 và lịch epsilon gốc | faithful manifest/CSV/Q, phase 3 |
| R04 | A: total/mean reward, số hai action, Q-value và greedy policy | CSV, policy table, phase 3/5 |
| R05 | B: reward theo episode/window, phân tích biến động thay vì khẳng định hội tụ | raw logs + plot, phase 3 |
| R06 | C: alpha 0,01/0,10/0,50, giữ phần khác; curves và final eval | ma trận cấu hình, train/eval CSV/hình, phase 4/5 |
| R07 | D: >=3 cấu hình exploration, cả train và eval | baseline decay/fixed0,05/fixed0,30, phase 4/5 |
| R08 | E: separate evaluation, frozen Q, exploration tắt, demand comparable | hash Q trước/sau, independent RNG và paired scenarios, phase 5 |
| R09 | Lặp nhiều seed để tránh kết luận từ một run; mean và sample std | 5 seed/cấu hình, n và ddof=1, phase 5 |
| R10 | Q1–Q10 có câu trả lời và dẫn chứng truy ngược | `report/question_evidence_matrix.md`, phase 8 |
| R11 | Q3 tính cụ thể Q mới; Q5 margin 5 và 3 | calculation tests + diễn giải, phase 2/8 |
| R12 | Q8 giải thích non-stationarity và đề nghị thay đổi thí nghiệm | thêm hai RL cùng học/frozen opponents, phase 6 |
| R13 | Q9 >=3 hạn chế và **implement ít nhất một modification** | Markov demand / gold-calibrated variant, phase 6 |
| R14 | Q10 đề xuất agent tốt hơn: state/action/reward/method/evaluation | augmented-state design và kiểm chứng bổ sung, phase 7 |
| R15 | Cấu trúc nộp đủ 9 mục, code thiết yếu, seed/param/episodes/protocol | report + reproducibility appendix, phase 8–10 |
| R16 | PDF mở được, đúng tên/metadata/deadline | all-page QA + release manifest, phase 10 |
| U01 | Lý thuyết ngắn, đủ ý, dễ hiểu; chỉ công thức cần thiết | checklist nội dung, phase 8–10 |
| U02 | Mọi biểu đồ output được giải thích rõ, dựa số đo thật | figure notes + nguồn CSV/aggregation, phase 3–10 |

Rubric S1: hiểu mô hình 15%, implementation/tái lập 20%, thiết kế đo 20%, trả lời 10 câu 30%,
thảo luận/cải tiến 10%, trình bày 5%. Ưu tiên phần đo và lập luận, không dồn công vào UI.

## 4 Tận dụng gì và không tận dụng gì

### 4.1 Runtime đã kiểm ngày 24/10/2026

`evidence/planning_runtime.json` ghi kết quả import/device inventory thực:

- WSL **Ubuntu**, user **tuananh**, Python **3.11.17**.
- `.venv-torch` ở `/home/tuananh/.local/share/ai-term-paper-v3/`.
- NumPy 2.4.6, Matplotlib 3.11.2, pandas 3.0.6, sklearn 1.9.0, PyTorch 2.14.1+cu130,
  nbformat 5.11.1, nbclient 0.11.0, python-docx 1.2.0, pypdf 6.21.0, pytest 9.1.1.
- GPU nhìn thấy: **NVIDIA GeForce RTX 5050 Laptop GPU**, 8.546.484.224 byte
  (~7,96 GiB). Đây là probe nhìn thấy thiết bị, không phải số đo training mới.
- Ổ C khoảng 35,3 GiB trống lúc kiểm kê; chỉ snapshot, phải đo lại trước mỗi phase chạy.
- Venv do uv quản lý không có `pip` module; **không phải lỗi cần cài lại**. Không chạy
  lệnh `pip install` trong tài liệu khi dependencies đã sẵn.

Lệnh dùng runtime, từ root repo:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module <module_AG02>
```

Phải ghi evidence mới trong folder bài này, không chạy doctor/bootstrap cũ ghi đè evidence V3.
Q-learning bảng chỉ 8 số, **chạy NumPy CPU**, không cần Keras/GPU/DQN. GPU không làm
bài đúng hơn. Không cài thêm mô hình LLM hay framework agent.

Toolchain tài liệu Phase 35 và renderer có sẵn: có thể tái sử dụng wrapper chỉ đọc để
build/render tài liệu mới trong folder này. Khi đến phase 9 phải đọc skill tài liệu/PDF
hiện hành và kiểm quyền/runtime; không coi phê duyệt của bài cũ là quyền cài môi trường mới.

### 4.2 Mã và kinh nghiệm cũ

- Tận dụng patterns seeding, kiểm terminal, frozen-Q eval, plot và kiểm thử từ notebook
  bài trước; **không dùng đường mê cung/kết quả 24 bước làm kết quả Agent02**.
- Tham khảo cách log/reproducibility của V3 và phân biệt rule/learned/LLM. Không gọi lại
  producer/evaluator hoặc sử dụng kết quả Phase31 làm kết quả mới của Agent02.
- Không dùng web/API/Render vì không phục vụ rubric bài này.
- Giữ nguyên raw, checkpoint, metric, TEST seals và mọi khóa Phase22–35.

### 4.3 Dataset và ba miền thầy thích

**Dataset chính của Agent02 là trajectory do simulator sinh**, không phải CSV bệnh nhân
hay bảng giá. Phải ghi đó là synthetic simulation, có state/action/reward/next_state.

| Nguồn sẵn có | Quy mô snapshot đã có | Dùng phù hợp trong bài này | Không được suy diễn |
|---|---:|---|---|
| Mô phỏng e-commerce của thầy | Mỗi train run 100.000 market step, 2 agent | Toàn bộ thí nghiệm chính, profit/discount và Q-learning | Không phải dữ liệu thị trường thật |
| World Bank Pink Sheet Gold | 801 tháng, 1960-01–2026-09; file 586.099 byte | **Ưu tiên phần mở rộng câu 9**: hiệu chỉnh ma trận chuyển chế độ từ hướng biến động quá khứ; so với IID/Markov cố định | Không coi biến động giá là nhu cầu vàng đã đo; không daily trading/real-time/đầu tư |
| CDC Diabetes | 253.680 dòng/21 feature; file 13.494.568 byte | Ví dụ Q2/Q10: hỗ trợ thống kê/giáo dục cần rule an toàn; nhắc ML score không phải policy RL | Không có action/reward/treatment trajectory; không làm RL chọn thuốc/insulin từ nhãn bệnh |
| Ames Housing | 2.930 nhà/82 cột nguồn; file 960.807 byte | Ví dụ Q2/Q10: lọc nhà theo ngân sách, phối hợp rule và estimator | Giá bán lịch sử không phải listing/availability hiện tại; không có chuỗi phản ứng với action agent |
| MedQuAD | Snapshot 47.441 QA pair, 16.407 answer không rỗng theo audit local | Chỉ tham khảo giáo dục nếu cần ví dụ tiểu đường | Không phải hồ sơ bệnh nhân hoặc benchmark treatment RL; không mở TEST QA cũ |

Nguồn kiểm lại ngày 24/10:

- UCI: https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators
- Ames tác giả gói: https://github.com/topepo/AmesHousing
- World Bank: https://www.worldbank.org/en/research/commodity-markets
- MedQuAD tác giả: https://github.com/abachaa/MedQuAD

Số đo local lấy từ receipt/docs Phase 23–24, không đánh đồng headline website với
snapshot (đặc biệt MedQuAD). CDC nhãn local là `Diabetes_binary`, không tự đổi thành 3 lớp.
Không tải dataset mới chỉ vì muốn nhiều dataset. Chỉ tải khi nguồn sẵn thiếu thứ thật
sự cần, có bản quyền/provenance rõ, được ghi revision và không ảnh hưởng deadline.

Chính sách Gold: chỉ đọc **prefix thuộc TRAIN V3**, được chọn theo calendar/ID đã khóa;
không dùng validation/TEST V3 hoặc toàn bộ 801 tháng để chỉnh variant. Dùng dấu thay đổi
giá đã quan sát, không dùng tương lai. Ước lượng transition 2×2 có Laplace smoothing
đã định trước; sinh nhu cầu giả lập từ kernel này. **Đây là proxy thiết kế mô phỏng**, không
chứng minh giá gây ra nhu cầu. Ghi tháng dùng, đơn vị, missing, count chuyển trạng thái,
kernel, hash và giả định; không gán episode synthetic thành số khách hàng/tháng độc lập thật.

## 5 Thiết kế thực nghiệm dự kiến

Thiết kế đã khóa ở `docs/protocol_v1.json` trong phase 2. Trạng thái thực nghiệm
đọc từ checkpoint/registry; không sửa protocol bất biến để cập nhật trạng thái run.

### 5.1 Track tham chiếu và track so sánh

**REF** giữ nguyên code/param của thầy về thuật toán và RNG để có run faithful seed 42.
Copy Python từ S3 sang đúng đuôi `.py`, AST/compile trước, không “biên dịch tex”.
Nếu cần thêm log dùng wrapper không đổi thứ tự gọi RNG. Nếu thấy lỗi phải giữ REF và
ghi revision, không âm thầm đổi rồi gọi byte-identical.

**CONTROLLED** bổ sung instrumentation/evaluation riêng, có version. Giữ cùng environment
law, reward và budget; thay seed plumbing/evaluation tapes khi cần kiểm soát công bằng.
Không trộn raw kết quả REF với CONTROLLED thành cùng một replicate.

Baseline:

- 2 agent: một Q-learning, một rule cố định; action 0/1, cùng chọn trước `step`.
- Local state `(demand, competitor_previous_action)`; Q shape 2×2×2.
- 5.000 episode, 20 step/episode; alpha 0,1; gamma 0,9.
- Epsilon `max(0.02,0.20*0.995**episode)`; price 10/cost 5/discount 20%; customers 10/20.
- Conversion `clip(0.30+0.25*d+0.15*a_self-0.10*a_other,0.05,0.95)`.
- Sales Binomial(N,p), reward sales×margin. Mô hình không bảo đảm khách chỉ mua ở một
  shop; không gọi tổng sales hai shop là thị phần độc quyền hay game zero-sum.

### 5.2 Ma trận core

Seeds train chính: **11,22,33,44,55** (theo list đa seed trong code thầy).
REF baseline: 42 riêng. Giữ train-RNG, action-RNG, eval-RNG tách/ghi đầy đủ.

| Nhóm | Cấu hình | Runs train dự kiến |
|---|---|---:|
| REF | Baseline 42 faithful | 1 |
| Alpha/exploration CONTROLLED | Baseline; alpha 0,01; alpha 0,50; fixed epsilon 0,05; fixed epsilon 0,30 × 5 seed | 25 |
| Q8 two-learners diagnostic | Hai Q cùng học, baseline param × 5 seed | 5 pair runs, 10 Q-table |
| Q9 retrain variants | Demand persistent 0,9 và kernel Gold × 5 seed | 10 |
| Q10 improved-agent check | Augmented-state learner × 3 kernel (IID/persistent/Gold) × 5 seed | 15 |
| Tổng dự kiến | 56 run môi trường; Q8 có 2 learner/run | 56 |

Không chạy trùng baseline alpha 0,10/epsilon baseline trong sweeps. Mỗi train run
100.000 market step ⇒ khoảng 5,6 triệu market step, không phải 5,6 triệu mẫu độc lập.
Trước chốt budget đo smoke throughput, giới hạn storage; không hứa thời gian khi chưa đo.

Mỗi frozen policy được eval **500 episode × 20 step** trên tập scenario mới, không learn,
explore=False; metadata ghi tie-breaking. S3 chọn ngẫu nhiên khi các Q gần bằng qua
`np.isclose`, dù epsilon 0; cần ghi/test chứ không gọi deterministic tuyệt đối.

### 5.3 Fair evaluation và bất định

- Hai nhóm kết luận khác nhau: (a) ai thu lợi thế nào **trong cùng cuộc đối đầu**,
  (b) policy nào tốt hơn **khi đối mặt cùng một fixed opponent**. Không đánh đồng.
- Dùng held-out seeds/tapes như nhau cho các configuration, có role-swap để phát hiện
  lợi thế vị trí. Rule-vs-rule/no-discount là đối chứng nhỏ, không học.
- Tách demand random stream khỏi sales/action stream. Cùng seed chung cho cả env chưa
  bảo đảm cùng demand khi RNG draw phụ thuộc action/binomial. Với matched tapes: demand
  và Uniform[0,1] theo episode/step/customer/role sinh trước; sales là count(U<p), giữ
  đúng marginal Binomial. Tạo/tải từng episode để tiết kiệm RAM. Ghi đây là revision
  kiểm soát số ngẫu nhiên, không khẳng định trace giống REF.
- Hash Q trước/sau eval bằng nhau. Không update scaler/config/hyperparameter từ eval cuối.
- Train logging không dùng chung RNG hoặc làm đổi dynamics. Không sửa reward cho RL thắng.
- Log per-episode cho tất cả run, transition trace chi tiết cho fixture/run mẫu có hạn mức;
  không dump triệu dòng không cần thiết. Q-value, state visitation/action count đầy đủ.
- Mean/std **giữa 5 training seed**, sample std với ddof=1; mỗi run ghi variation episode
  riêng. Nếu dùng CI bootstrap, resample seed/pair, không giả mỗi timestep độc lập.
- Kết quả so sánh dùng paired delta reward/step theo seed và cùng opponent/tape.
- Chọn threshold/cấu hình chỉ bằng development seeds tách trước. Final eval được
  khóa và chạy sau source/config/test PASS; lỗi cần giữ failed attempt/revision.
- Nếu RL thua/không khác, vẫn nộp kết quả thật và giải thích. Rising reward không tự
  chứng minh hội tụ, nhân quả hoặc tổng quát hóa.

### 5.4 Vấn đề mô hình cần giải thích

Agent thấy action **trước** của đối thủ, không thấy action hiện tại. Đối thủ rule ở
bước hiện tại lại có thể phụ thuộc action **trước của chính learner**. Vì vậy local
state 2 biến chưa chắc đủ Markov: cần dựng hai history cùng observation nhưng khác
own_previous_action để kiểm tra. Baseline giữ nguyên để tái lập, hạn chế được công khai.
Horizon 20 nhưng observation không có thời gian còn lại cũng là một xấp xỉ.

Q10 đề xuất **memory/time-augmented tabular Q**:
`(demand, own_previous_action, competitor_previous_action, remaining_steps)`;
20 giá trị remaining × 2 × 2 × 2 × 2 action = 320 Q-value, vẫn nhẹ. Không bảo đảm tối ưu
khi đối thủ cũng học. So sánh baseline/rule trên cùng kernel và budget; exact finite-
horizon dynamic programming với fixed rule dùng như oracle kiểm tra tùy khả năng,
tách khỏi dữ liệu dạy Q và không gọi oracle model-free learner.

## 6 Cấu trúc thư mục

```text
agent02_assignment/
  AGENTS.md
  AG02_EXECUTION_PLAN.md
  checkpoint.json
  sources/manifest.json, extracted/, visual/, provided/   # provided tạo phase1
  docs/requirements.md, protocol_v1.json, deviations.md
  code/agent02_experiment.py, agents/, environments/, evaluation/
  configs/                                               # versioned, không ghi root
  notebooks/
  data/derived/                                          # không clone raw cũ
  artifacts/runs/<track>/<config>/<seed>/
  artifacts/metrics/, figures/, manifests/
  tests/
  evidence/<phase>/
  report/sections/, question_evidence_matrix.md
  report/build/, qa/
  output/                                                # chỉ bản đã nghiệm thu
  README.md
```

Không sửa AGENTS/plan V3 ở root. Đường dẫn output/checkpoint của code thầy phải được
override vào bài mới, không tạo `agent02_results/` lẫn ở root.

## 7 Quy tắc thực thi phase

- Lệnh: **`làm AG02 phase N`**. “Làm tiếp Agent02” đọc checkpoint rồi tiếp đúng run
  chưa xong. Không dùng phase 20–35 cho bài này vì đã thuộc V3.
- Nếu người dùng chỉ gõ “làm phase N” mà ngữ cảnh không rõ bài, hỏi một câu chọn bài;
  không đoán và ghi đè plan khác. Trong mạch AG02 rõ ràng, dùng plan này.
- Mỗi lượt: đọc toàn bộ plan + checkpoint + log phase + process thực; xác minh dependency;
  thực hiện đúng phạm vi; kiểm thử; ghi receipt/hashes; cập nhật trạng thái và next_phase.
- Không có “phase hoàn tất ngầm”: phải có đầu ra và acceptance PASS.
- Người dùng yêu cầu phase có dependency chưa xong: báo thiếu gì, không tự chạy dài
  qua nhiều phase trừ khi người dùng yêu cầu làm liên tục.
- Khi dừng: ghi runID/config/seed/episode/Q/RNG và process thật; chỉ một writer.
  Resume không lặp run DONE. Đánh giá cuối hỏng không reset journal để che attempt.
- Đây là kế hoạch hiện tại; trạng thái mới nhất ở mục 11 và checkpoint. Không tự nộp/commit/push.

## 8 Các phase thực hiện

### Phase 0 — Đọc đề và kiểm kê phạm vi

**Trạng thái: COMPLETE (khảo sát, không phải implementation).**

Đã đọc/đối chiếu 6 file, trích nội dung, hash/số trang; xem trang nguồn quan trọng;
kiểm runtime/package/GPU và asset; hỏi người dùng phạm vi slide; lập ma trận yêu cầu,
plan và checkpoint riêng. Không chạy code thầy, train hay TEST V3.

Bằng chứng: `sources/manifest.json`, `sources/extracted/`, `sources/visual/`,
`evidence/planning_runtime.json`, plan và câu trả lời người dùng ngày 24/10.

### Phase 1 — Khởi tạo bài và khóa đầu vào

Dependency: 0. Mục tiêu: có workspace riêng và đường chạy tái lập trước code thực nghiệm.

**COMPLETE ngày 24/10/2026.** Sáu nguồn copy đúng hash; reference Python exact-byte,
chỉ AST/compile. Notebook probe 2 cell PASS; 29 test/0 skip; coverage guard workspace
99,1150%, Ruff và launcher PowerShell PASS. Khóa 9 đầu vào tại
`evidence/phase01/input_lock.json`, SHA-256
`4ef77dcf11e5470c328d33e71e12c8e9f96b3f2d512dbb82276bb8702f9bde34`.
Biên bản `docs/phase01_report.md`, proof `evidence/phase01/verification.json`.
Không thực thi reference/train/eval. Lỗi probe DrvFS được giữ riêng, đã phục hồi bằng
temp Linux bảo mật; không cài/sửa env. Các bước bên dưới là checklist đã thực hiện.

1. Đọc AGENTS/plan/checkpoint; xác minh hash nguồn và metadata lớp/tên/nhóm đang biết.
2. Copy byte-identical 6 file vào `sources/provided/` nếu cần portable (~5 MB), kiểm hash;
   nguồn Documents không đổi. Không coi extracted text là bản source gốc.
3. Parse AST/compile S3 mà không chạy; chuyển bản sao thành `.py`, giữ nguyên bản thầy.
4. Kiểm runtime bằng wrapper Ubuntu, import NumPy/Matplotlib/Jupyter; không cài package.
5. Ghi baseline fingerprint, package versions, disk trước phase và cấu trúc folder.
6. Khởi tạo runner từ root nhưng output luôn ở bài này; README lệnh cụ thể.

Đầu ra: `docs/requirements.md`, provenance, original code snapshot, runtime receipt,
README và journal. Nghiệm thu: AST PASS, đủ 6 hash, không ghi ngoài folder, chưa train đầy đủ.

### Phase 2 — Environment, agents, protocol và test trước train

**Trạng thái: COMPLETE ngày 24/10/2026.** Bằng chứng `docs/phase02_report.md`,
`evidence/phase02/verification.json`; khóa 48 file ở `evidence/phase02/protocol_lock.json`.
103 test/0 skip, coverage dòng 96,77%, nhánh 90,35% (sáu module phase2; không phải toàn repo).
Smoke 100 episode/track; không dùng làm baseline kết quả. Core và protocol đã khóa,
phase sau thêm runner/module riêng; sửa file khóa cần revision giữ bằng chứng cũ.

Dependency: 1. Mục tiêu: mô hình đúng đề, test bắt được lỗi trước khi có kết quả.

1. Tách REF/CONTROLLED rõ ràng; giữ 3 nhánh rule, reward, hành động đồng thời và reset.
2. Ghi log theo episode, Q snapshot, policy, visitation, run ID và hash cấu hình/source.
3. Viết test trước implementation: 4 state × 2 action; cả joint actions; demand thấp/cao;
   price/margin/probability clipping; action sai; terminal không bootstrap; epsilon;
   tie-breaking có seed; rule không học; hai agent nhìn cùng snapshot trước step.
4. Kiểm câu 3: target = 6 + 0,9 × 5 = 10,5; delta = 10,5 − 4 = 6,5;
   Q mới = 4 + 0,1 × 6,5 = **4,65**. Đây là số giả định đề cho, không phải số đo train.
5. Kiểm câu 5: margin không giảm = 10 − 5 = **5**; giảm 20% = 8 − 5 = **3**.
6. Chuẩn bị evaluator đóng băng Q và các RNG riêng. Fixture kiểm demand/uniform tapes,
   đổi vai và phân phối Binomial; chưa chạy đánh giá cuối.
7. Smoke 100 episode để đo tốc độ và kích thước log, ước tính ngân sách 56 run.
   Giữ tối thiểu 5 GiB trống và cơ chế dừng/resume; không trộn smoke vào kết quả.
8. Khóa `docs/protocol_v1.json`: cấu hình, seeds, train/dev/final evaluation,
   budget 5.000×20/500×20, aggregate ghép cặp, các kernel, state cải tiến dự kiến,
   filenames, test plan và hash source. Thay đổi cần revision có lý do.

Nghiệm thu: test lõi PASS; coverage mục tiêu ≥90% dòng/nhánh, tối thiểu 80%; không
skip trọng yếu; fixture tái lập; eval không update Q; không mở TEST của V3.

### Phase 3 — Baseline A và diễn biến học B

**COMPLETE ngày 24/10/2026.** REF42 và CONTROLLED11, mỗi run5.000×20;
10.000 dòng train, Q/policy/count/visits, 51 checkpoint/run. DEV100 episode/vai,
hai vai/tape chung; final chưa mở. Bốn hình đã xem và có lời giải thích.
122 test/0skip, coverage94,9367% trên ba module mới. Nghiệm thu
`docs/phase03_report.md`, `evidence/phase03/verification.json`;
khóa268 file SHA256 `25b050a28691073aab61064b3d3bf3d32ae1aac2388c2c6ccc681a099118a00a`.
CONTROLLED seed11 được tái dùng nguyên checkpoint/hash ở phase4–5, không train lại.

Dependency: 2. Mục tiêu: chạy reference seed 42 và có đủ bằng chứng A–B.

1. Chạy REF 5.000×20, seed 42, giữ thứ tự RNG; lưu config/versions.
2. Chạy CONTROLLED baseline seed 11 để mở đầu ma trận chính. Tái dùng run này ở
   phase 4/5, không train lại.
3. Lưu Q-table, policy cho 4 state, train curve, total/mean reward hai agent,
   số action giảm/không giảm giá, epsilon và visitation; đo thời gian CPU.
4. Vẽ raw reward và moving average 100 episode cho cả RL và rule, đúng trục/đơn vị.
5. Đánh giá development riêng để kiểm pipeline, ghi nhãn DEV; final evaluation thuộc phase 5.
6. Nhận xét giai đoạn đầu/cuối và biến động từ CSV; không tự kết luận “hội tụ”.
7. Ghi chú giải thích từng hình theo mục 1: trục/đơn vị, hai đường RL/rule, cửa sổ
   100 episode, xu hướng, dao động và điều không thể kết luận từ train curve.

Nghiệm thu: đủ 5.000 dòng/run và 100.000 step; hình truy ngược được từ CSV;
Q shape/count action/hash đúng; không gộp REF và CONTROLLED làm cùng một replicate.

### Phase 4 — Sweeps C và D, đủ ma trận đa seed

**COMPLETE ngày 24/10/2026.** Đủ25/25 CONTROLLED:24 mới +baseline11 giữ nguyên
hash/declaration phase3. Core125.000 dòng train/2.500.000 market step, không DEV
mới/final. 4 hình đã xem và có giải thích mean±sample std giữa5 seed, window100;
24.505 dòng curve aggregate. 137 test/0skip, coverage100% chỉ ba helper mới.
Biên bản `docs/phase04_report.md`, vận hành `docs/phase04_operations.md`,
registry `artifacts/manifests/phase04/trained_registry.json` (25Q, final count0).
Khóa2.792 file `evidence/phase04/experiment_lock.json`, SHA256
`3ff17f6682ae26c5303a5d07450f6c0ce44df6304223838e63eb8da0371d7f38`.
Không train lại25 run hoặc chỉnh tham số theo train curve; phase5 chỉ sau yêu cầu.

Dependency: 3. Mục tiêu: đủ 3 alpha, 3 exploration và 5 seed mỗi cấu hình.

1. Hoàn tất 25 run CONTROLLED trong bảng 5.2, bỏ qua run DONE ở phase 3.
2. Sweep alpha chỉ đổi alpha; sweep exploration chỉ đổi lịch epsilon. Ghép cặp
   seeds/scenarios; không vừa đổi alpha vừa đổi demand trong cùng so sánh.
3. Lưu **toàn bộ train curve mỗi cấu hình**, không chỉ biểu đồ cột reward cuối.
4. Vẽ mean/variation qua các seed và biểu đồ lịch epsilon.
5. Ghi thời gian, failed/resumed runs; không chỉnh tham số chỉ để có hình đẹp.
6. Mỗi hình có ghi chú giải thích mean/variation giữa seed khác với moving average
   trong một run; nêu cấu hình nào khác, chênh lệch thật và giới hạn so sánh.

Nghiệm thu: ma trận 25/25; config chỉ khác đúng yếu tố đang khảo sát; đủ Q/logs;
không đánh giá cuối sớm hoặc train lại chỉ vì thiếu hình (hình đọc log đã lưu).

### Phase 5 — Fair evaluation E và aggregate

**COMPLETE ngày 24/10/2026.** 71 claim, mỗi claim500 episode ×20 bước, count1:
50 core (25Q ×2 vai),20 đối chứng và1 REF native riêng. Tổng35.500 dòng episode/
710.000 market step; không train thêm, không tuning. Q/source/config giữ nguyên.
Gộp hai vai trước, rồi mean/sample std qua5 training seed; controls là5 scenario
panel, REF không gộp vào n5. Sáu CSV và4 hình grayscale đã xem/giải thích đầy đủ.
157 test/0skip, coverage94,3182% chỉ final_v1/journal_v1/aggregate_v1.
Biên bản `docs/phase05_report.md`, vận hành `docs/phase05_operations.md`,
registry `artifacts/manifests/phase05/evaluated_registry.json`, audit PASS tại
`evidence/phase05/verification.json`. Khóa329 file ở `evidence/phase05/experiment_lock.json`,
SHA256 `8aa5969bacbeb6e069bf357453c4679600f5a9fcd6e58064eea4dbf192c2865c`.
Không chạy lại71 claim hoặc sửa file đã khóa; số đo mới chỉ đọc saved outputs.

Dependency: 4 và khóa evaluator/source/config PASS. Mục tiêu: so sánh RL với rule công bằng.

1. Khóa Q/config/evaluator/run IDs; tách development/final tapes trước khi chạy.
2. Đánh giá policy đóng băng trên 500 episode × 20 step với scenario độc lập;
   không update Q, không khám phá; ghi cơ chế random tie. Dùng cùng tapes và đổi vai.
3. Đánh giá mỗi policy trước cùng một fixed rule opponent; thêm đối chứng
   rule-vs-rule/no-discount. Ghi nhãn riêng cho bảng đối đầu và bảng chất lượng policy.
4. Hash Q trước/sau; lưu reward/action counts theo episode. Aggregate mean/std 5 seed,
   paired delta và n; CI nếu có phải resample seed pairs. Không gọi 500×5 episode là
   2.500 learner độc lập; không dùng final evaluation để chọn hyperparameter.
5. Lập 6 bảng: baseline reward, Q/policy, alpha, exploration, multi-seed, paired comparison.
   Tái tính từ saved results, không chạy model lại chỉ để làm bảng.

Nghiệm thu: hash Q không đổi; đủ 500 dòng/run và seed groups; mẫu số rõ;
kết quả nhất quán, không bắt buộc RL thắng. Không ghi đè journal để che lần chạy lỗi.

### Phase 6 — Tương tác hai learner và robustness, ưu tiên Gold

**COMPLETE ngày 24/10/2026.** 5pair run hai learner +10variant run(persistent/Gold),
đều5.000×20,fresh zeroQ;75.000 train rows/1.500.000 market step/20learner instance.
Gold TRAIN560tháng1960-01…2006-08,558transition cóLaplace+1;source/split/TRAIN IDs
giữ hash,không fit giá validation/TEST. Kernel và prefix ở `data/derived/`.
160 final claim/count1:80Q8 checkpoint +80variant,500episode/vai;80.000 saved rows/
1.600.000 market step. Đã gộp role,hai learner trongpair rồi5pair seed cho Q8;
variant paired delta theo5seed/kernel. Giữ kết quả retrain thấp hơn baseline.
9CSV/4PNG đã xem/giải thích;186test/0skip,coverage97,1875% trên4module mới.
Biên bản `docs/phase06_report.md`,vận hành `docs/phase06_operations.md`,bản thảo
`report/sections/phase06_robustness.md`;auditor PASS,bảo toàn3.336file cũ/7parentasset.
Khóa2.343file `evidence/phase06/experiment_lock.json`,SHA256
`9637d62f6c2061f173d0147d77d368bf2d85e21b5049d60320a7edca0d5d68d3`.
Registry trained/evaluated riêng;không sửa protocol hoặc registry cũ. Không train/
eval lại15run/160claim;không tự thực hiện phase7 hoặc dựng PDF/DOCX.

Dependency: 5. Mục tiêu: bằng chứng câu 8 và sửa môi trường thực sự ở câu 9.

1. Q8: chạy 5 cặp seed, mỗi cặp có hai Q-learning cùng học; RNG riêng từng learner,
   action chọn đồng thời. Lưu policy checkpoints, reward volatility và visitation.
   Đánh giá checkpoint đóng băng trước cùng opponent/tapes để phân biệt policy drift
   với nhiễu sales. Đây là kiểm tra thêm; Q8 tối thiểu chỉ yêu cầu đề xuất thay đổi.
2. Q9 chính: đổi IID demand sang Markov với xác suất giữ chế độ 0,9, khởi tạo cân bằng;
   giữ nguyên reward/action/price. Test transition kernel trước khi chạy.
3. Gold companion: đọc Pink Sheet và cutoff TRAIN cũ chỉ đọc; parse gold series;
   kiểm tháng/đơn vị/missing. Mô tả mẫu/phân bố và ước lượng transition 2×2 theo mục 4.3.
   Lưu `data/derived/gold_regime_kernel_v1.json`, hash nguồn và cutoff.
4. Không gán gold regime là demand thật. Dùng như **kịch bản nhu cầu giả lập được
   hiệu chỉnh từ chuỗi lịch sử**; công khai giả định và giữ teaching conversion/reward.
5. Mỗi variant train 5 seed. Đánh giá cả baseline policy đóng băng và policy train lại
   trên variant, dùng cùng scenario. Chỉ đổi kernel, không sửa rule cho thua;
   khóa protocol trước đánh giá cuối của nhóm variant.
6. Giải thích ≥3 hạn chế: conversion minh họa, demand đơn giản, state aliasing,
   không inventory/customer heterogeneity, không bảo đảm thị phần, horizon hữu hạn.

Nghiệm thu: 5 pair run hai learner và 10 run variant hoàn tất; truy ngược Gold kernel;
có code sửa đổi, bảng trước/sau và giả định. Không đọc/tuning TEST V3.
Nếu parse/provenance Gold thất bại, lưu receipt và báo; kernel persistent vẫn đáp ứng
câu 9. Không bịa dữ liệu, tự đổi nguồn hoặc trì hoãn bản core để tải tập lớn.

### Phase 7 — Agent cải tiến và kiểm tra câu 10

**COMPLETE ngày 24/10/2026.** Đủ15 memory/time-augmented run trên3kernel×5seed,
Q320giá trị,5.000×20/run,fresh zeroQ.75.000train episode/1.500.000market step;
fixture aliasing,terminal/time và resume đúng Q/RNG PASS. Không dùng oracle labels.
30final claim mới/count1,500episode/vai;reuse60claim baseline/rule cùngkernel từ5/6,
không forward lại. So sánh90member,45.000saved episode rows;30claim mới chỉ15.000row.
Oracle là kỳ vọng phân tích known-model/fixedrule,không train/model-free hoặc sampledTEST.
8CSV/4PNG đã xem/giải thích;221test/0skip,coverage96,3964% trên6module mới.
Thiết kế sửa state có lý do nhưng meanprofit thấp hơn baseline/rule trên cả3kernel
trong budget đã khóa;giữ kết quả,không tăngbudget hoặc tuning từfinal.
Biên bản `docs/phase07_report.md`,vận hành `docs/phase07_operations.md`,bản thảo
`report/sections/phase07_improved_agent.md`;auditor PASS,bảo toàn5.679file cũ/7asset.
Khóa1.822file `evidence/phase07/experiment_lock.json`,SHA256
`06d4046f04abc456ba703819a4fe4c8bdee5f2757830d1409902ef4764e9f607`.
Toàn bộ56registered market run/61learner instance COMPLETE. Phase8 chỉ viết từ
artifact đã khóa;không train/evaluate lại hoặc tự bắt đầu8–10 khi chưa được yêu cầu.

Dependency: 6. Mục tiêu: cải tiến có lý do, không thêm deep RL khi không cần.

1. Dùng fixture chứng minh local observation cũ có thể che own_previous_action;
   ghi đây là phân tích mô hình, không đổi baseline đã chạy.
2. Implement memory/time-augmented Q ở mục 5.4; test 320 entries, remaining time,
   reset/terminal. Giữ action/reward/budget; viết test trước train.
3. Train 15 run (3 kernel × 5 seed), đánh giá đóng băng theo protocol đã khóa.
   So sánh với baseline/rule cùng scenario, ghi cả reward và chi phí.
4. Nếu làm exact finite-horizon oracle, chỉ dùng simulator đã biết và fixed rule để
   kiểm value/gap; không cấp optimal actions vào Q training. Phân biệt oracle model-based
   với learner model-free. Không kết luận agent mới luôn thắng.
5. Viết đủ state/action/reward/method/evaluation và tiêu chí “robust hơn”:
   paired return/gap qua 3 kernel, biến động seed và chi phí; kết luận theo số đo.

Nghiệm thu: test state mới PASS, 15 run đủ, so sánh 3 phương án và nêu giới hạn.
Câu 10 chỉ bắt buộc đề xuất framework và thiết kế kiểm chứng; train agent mới là
phần tăng bằng chứng. Nếu thiếu thời gian, giảm bonus bằng deviation công khai,
không bịa rằng đã train. Thiết kế mới phải được chốt trước kết quả đánh giá của nó.

### Phase 8 — Viết đủ mười câu và báo cáo

**COMPLETE ngày 24/10/2026.** Bản thảo `report/phase08/manuscript.md` có đủ 9 phần,
10 câu trả lời, 12 bảng từ artifact, 20 hình đã có giải thích và 8 đoạn code nguyên
source/range/hash. Lý thuyết cơ bản, chỉ công thức cần thiết; giữ kết quả bất lợi,
phân biệt REF/native, CONTROLLED n5, within-match/policy-quality, Gold proxy và oracle.
234 test/0 skip, coverage 96,7213% chỉ helper report_assets; 101 phép đối chiếu số
học PASS, 7.501 file khóa Phase1–7 và 7 parent asset giữ hash. Không train/forward mới.
Khóa nội dung 31 file `evidence/phase08/experiment_lock.json`, SHA256
`5399801278e64aaed9b6535ac4d9684e31434311a4623e33c5bd153445f8bbc6`.
Bản matrix Markdown hiện hành `report/question_evidence_matrix_r2.md` sửa đúng một
link điều hướng bị thêm khoảng trắng; matrix gốc/bản thảo/số liệu giữ nguyên.
Revision chỉ trình bày, kiểm đủ 21 link và 31 file gốc PASS; khóa 4 file tại
`evidence/phase08_presentation_r2/experiment_lock.json`, SHA256
`ae374a5358940f1c5dd97b4be9bd4a596e5dcb07f74a3ef31aca6b61af80027c`.
Chọn qua `report/active_report.json`. Đọc `docs/phase08_report.md`,
`phase08_operations.md` và `phase08_presentation_r2.md` trước Phase9.
Chưa build notebook báo cáo/DOCX/PDF, chưa kiểm trang; các bước này thuộc 9–10.

Dependency: 5, 6, 7 hoặc deviation bonus đã ghi. Mục tiêu: bản thảo dễ hiểu, có bằng chứng.

1. Lập `report/question_evidence_matrix.md`: từng Q1–Q10 có claim/code/CSV/figure locator.
2. Viết đủ 9 mục của S1. Dự kiến 20–28 trang kể cả code/phụ lục, không phải giới hạn đề.
   Lý thuyết thuần khoảng 3–4 trang; ưu tiên kết quả và 10 câu, không chép toàn survey.
3. Q1: sơ đồ 2 agent ↔ shared market, PEAS, state/action/reward/transition.
4. Q2: bảng rule/RL, training/inference. Ví dụ hành chính tiểu đường cần rule an toàn,
   lọc nhà theo ngân sách và giảm giá shop; không đưa ra tuyên bố lâm sàng.
5. Q3: Q-update đúng, giải thích alpha/gamma/target/delta và tính 4,65 từng bước.
6. Q4 và Q7: train curves + paired evaluation; phân biệt epsilon/alpha, không mặc định
   “cao hơn tốt hơn”.
7. Q5: margin 5/3, lợi nhuận khác số bán; reward thiết kế thế nào thì hành vi theo đó.
8. Q6: mean reward từ CSV và tổng step; bảng mean/std 5 seed, kết luận có giới hạn.
9. Q8: fixed rule so với hai learner; non-stationarity/partial observation và phase 6.
10. Q9: ≥3 hạn chế, code/kernel sửa và kết quả trước/sau; Gold proxy ghi nhãn đúng.
11. Q10: state cải tiến, action/reward/method/evaluation; số đo phase 7 nếu đã có.
12. Trích code từ source hiện hành kèm hash; không cắt mất xử lý terminal.
    Notebook/code/output bổ trợ tái lập, không thay bảng kết quả và câu trả lời.
13. Liên hệ S4–S6 vừa đủ: RL khác supervised ML, MAS không nhất thiết LLM;
    mô phỏng cạnh tranh không phải hệ LLM hợp tác. Không cần API key/model download.
14. Rà U01/U02: rút gọn lý thuyết; giữ phép tính cần thiết; mọi biểu đồ có phần phân
    tích trục/đơn vị, aggregation, xu hướng, so sánh và giới hạn bằng số liệu tương ứng.

Nghiệm thu: 10/10 câu đủ locator; phép tính đúng; không placeholder/expected results;
mọi số đo trong văn/bảng tái tính từ artifact. Kiểm citation, văn phong và phạm vi kết luận.

### Phase 9 — Notebook, source bundle và dựng tài liệu

**COMPLETE ngày 24/10/2026.** Notebook `notebooks/AG02_Code_and_Results.ipynb`
108 cell/44 code cell đã chạy;20 hình output/12 bảng kết quả/8 source excerpt và
10 câu trả lời. RunAll chỉ đọc saved inputs,không train/final forward. Gói ZIP
`output/AG02_Source_and_Notebook_r1.zip` có255payloadfile,15.746.858byte;
RunAll từ bản giải nén cũng PASS,255file giữhash,không importproject ngoàiZIP.
Không gọi đây làfulltrajectoryarchive;đọc `docs/phase09_reproduction.md`.

Ứng viên hiện hành `report/build/candidate-r3/agent02_D23CTPM01_TrieuTuanAnh.docx`
và PDF cùng tên:28trang,14 bảngnative(12bảng số liệu+2bảng mô tả),20hình,
8codeexcerpt nguyêntext,chữđen/grayscale. Đã xem riêng đủ28PNG125dpi ởđộ phân
giải gốc;không clipping/overlap/missingglyph. Giữ r1/r2 làm lịch sử. Chưa claim
nativeWordpagination hoặc phát hành bài nộp cuối. Chọn qua `report/active_candidate.json`.
User đã xác nhận nộp cá nhân,Triệu Tuấn Anh/B23DCCN053/D23CTPM01 vàfilenamePDF;
sidecar `evidence/phase09/submission_metadata.json`,không hỏi lại khi không có thay đổi.

245test/0skip,coverage98,8889% chỉpublication_v1 helper;Ruff/CLI/audit PASS,
bảo toàn7.501file khóa cũ/7parentasset. Khóa63file tại
`evidence/phase09/experiment_lock.json`,SHA256
`c482f44341c0d314ffed40f1084f37d59a4c58f10f60497ea2ac4c6db5c1886d`.
Không sửa/format source/docs/notebook/candidate/QA/evidence đãkhóa;thayđổi cần
revision giữ bản cũ. Toolchain hiện có được reuse,không cài/sửa GPUenv. Lượt seal
đầu bị hệ thống review dừng vì usage limit,chưa chạy;đã tiếp tục theo yêu cầu và
seal/audit PASS. Không train/evaluate lại hoặc tự bắt đầu Phase10.
Đọc `docs/phase09_report.md`, `phase09_operations.md` khi tiếp tục.

Dependency: 8. Mục tiêu: bộ chạy lại và ứng viên PDF/DOCX.

1. Thực thi notebook thật, không cài/sửa runtime. Đọc kết quả đã khóa để vẽ/report;
   Run All không tự train 56 run hay đánh giá cuối lại. Demo nhỏ ghi nhãn DEV.
2. README có lệnh runtime/train/eval/audit/report, cây thư mục và dependency hash.
3. Build DOCX sửa được và PDF nộp trong `report/build/candidate-version`; đọc skills
   hiện hành, dùng toolchain có sẵn, không ghi đè bài khác. Nếu toolchain thiếu thì
   báo đúng phần kẹt, không bỏ PDF bắt buộc hoặc cài lại môi trường GPU.
4. Bìa dùng thông tin đã biết, nhưng cá nhân/nhóm phải xác nhận. Không tự suy tên nhóm;
   ứng viên dùng tên trung tính trước khi đủ metadata.
5. Chữ đen, bảng native, code đọc được, hình grayscale; lý thuyết cơ bản, công thức
   chỉ khi cần và có giải thích biến.

Nghiệm thu: notebook không error; đủ mục/hình/bảng/code; source chạy được trên runtime
hiện có, PDF mở được. Toàn bài chưa COMPLETE trước nghiệm thu/phát hành ở phase 10.

### Phase 10 — Nghiệm thu, phát hành và hướng dẫn nộp

**COMPLETE ngày24/10/2026.** FinalPDF/DOCX ở
`output/agent02_D23CTPM01_TrieuTuanAnh.pdf` và `.docx`;byte-identicalcandidate-r3,
không sửa nội dung hoặcsource đãkhóa. Đối chiếu18mục R01–R16/U01–U02 vàđềS1
trang8–12;10câu/12bảng dữ liệu/8đoạncode được kiểm locator vàtext thật. Có14bảng
native/20hình trên28trang. Đã mở lại vàxem riêng đủ28PNGđộ phân giải gốc;reuse
renderPhase9 vìbytekhôngđổi. NativeWord16.0 readonlyPASS,28trang/14bảng,khôngsave.
Chữđen/ảnhgrayscale;phép tính cơbản vàgiới hạn kếtluận giữ đúng nhưthínghiệm.

245test/0skip chạy lại ởPhase10,coverage98,8889%chỉpublicationhelper. Ruff,
rubric/table/source/PDF audit PASS. Kiểm lại7.501file khoa học đãkhóa/7parentasset,
uv.lock/đầu vào cũ giữhash;101phép đối chiếu sốhọc chỉđọc savedoutputs. Không
train/finalforward mới,không tuning hoặc đổi môi trường. Metadata nộpcánhân đã
xácnhận. SourceZIP255file vànotebook44codecell được giữ nguyên.

Manifest `output/AG02_RELEASE_MANIFEST.json`;hướngdẫn `output/AG02_HUONG_DAN_NOP.md`;
activepointer `report/active_release.json`. Khóa16file ở
`evidence/phase10/experiment_lock.json`,SHA256
`06cdbb14f8e2e1d2b7c7f652e287d18acaa9861b91fcad7f6a056322add6f541`;
63filePhase9giữhash. Khôngghiđè fileđãpháthành;cầnrevision mới khi sửa. Bài đã
hoàn tất vềsản phẩm;chủbài tựnộpPDF qua kênh của lớp,trước hạn đề. Chưa tựsubmit,
email,commit/push/deploy;không cóphase tiếp theo được tựđộng chạy.

Dependency: 9. Mục tiêu: PDF đúng tên/đủ yêu cầu, không lỗi layout, bảo toàn bài cũ.

1. Audit R01–R16 và U01–U02, phép tính/run tables/config/source hash; kiểm mọi hình có
   phân tích rõ ràng, mọi công thức giữ lại có mục đích và giải thích dễ hiểu.
2. Chạy unit/integration tests; audit chỉ đọc saved outputs, không train/evaluate thêm.
   Coverage phải ghi đúng scope, không báo 100% toàn repo vì chỉ test core.
3. Render và xem từng trang: chữ, công thức Q, bảng, nhãn trục, code đầy đủ;
   không cắt caption/heading, trang trắng hay reference hỏng.
4. Kiểm tên `agent02_<class>_<team_name>.pdf`. Nếu cá nhân và được phép dùng tên cá nhân,
   đặt tên sau khi chủ bài xác nhận; không giữ placeholder làm filename nộp.
5. Xuất PDF cuối và DOCX sửa được từ ứng viên đã QA; ghi hash/bytes/page count,
   release manifest và hướng dẫn bàn giao. Không tự nộp LMS/email.
6. Kiểm lại hash đầu vào cũ/uv.lock và git diff ngoài folder; không dọn cache/dữ liệu.
7. Cập nhật checkpoint COMPLETE, bàn giao PDF; kèm DOCX/source/notebook khi cần.

Nghiệm thu: PDF nộp được, đủ 10 câu và số đo thật; đã xem tất cả trang;
đầu vào cũ không đổi, không có process/writer mồ côi. Không gọi deploy/cloud PASS.

## 9 Kế hoạch theo ngày và ưu tiên

Lịch gợi ý, không phải cam kết thời gian chạy chưa đo:

| Ngày | Công việc |
|---|---|
| 24/10 | Phase 0 đã xong; phase 1–2: nguồn/runtime/protocol/tests |
| 25/10 | Phase 3–4: baseline và sweeps đa seed |
| 26/10 | Phase 5–6: đánh giá công bằng, robustness và Gold |
| 27/10 | Phase 7–8: cải tiến, trả lời 10 câu và viết báo cáo |
| 28/10 | Phase 9–10: notebook, dựng PDF, xem mọi trang, chốt bản nộp |
| 29/10 | Dự phòng sửa format/metadata, xác nhận múi giờ và nộp trước 23:30 |

Không cắt R01–R16 để đổi lấy LLM/web. Nếu gấp, giữ baseline, 3 alpha, 3 exploration,
so sánh đa seed, sửa môi trường Q9, đủ 10 câu và PDF. Gold companion và train bonus Q10
có thể giảm bằng deviation công khai; phần đề xuất Q10 và kế hoạch kiểm chứng vẫn phải có.
Không bỏ câu 9 hoặc thay bằng lời kể mà chưa implement modification.

## 10 Điểm còn cần người dùng xác nhận

- **Đã chốt ởPhase9:** nộp cá nhân,Triệu Tuấn Anh,MSSV B23DCCN053,lớp D23CTPM01;
  user chấp thuận bìa vàfilename `agent02_D23CTPM01_TrieuTuanAnh.pdf`.
  Không cần hỏi lại metadata này,trừ khi user yêu cầu đổi.
- Deadline không ghi timezone: kiểm thông báo lớp. Chưa có quyền tự submit.

**Đã chốt, không hỏi lại:** slide MAS chỉ tham khảo, không làm cả 5 exercise MAS.

## 11 Nhật ký và trạng thái

| Phase | Trạng thái | Bằng chứng |
|---|---|---|
| 0 | COMPLETE khảo sát | 6 source hash, extracted text, 4 trang render, runtime inventory, xác nhận phạm vi, plan |
| 1 | COMPLETE | 6 nguồn nguyên byte, AST/compile, 2-cell probe, 29 test, input lock và verification PASS |
| 2 | COMPLETE | Core/DEV/protocol, 103 test, smoke 100 episode mỗi track, khóa 48 file, audit PASS |
| 3 | COMPLETE | 2 baseline đầy đủ, 4 hình/diễn giải, DEV frozen, 122 test, registry2 và khóa268 file |
| 4 | COMPLETE | Ma trận25/25, 4 hình/notes/QA, 137 test, registry25 và khóa2.792 file |
| 5 | COMPLETE | 71 claim/count1,6 CSV/4 hình giải thích/QA,157 test,registry và khóa329 file,audit PASS |
| 6 | COMPLETE | 15train/160claim-count1,GoldTRAIN560 tháng,9CSV/4hình/QA,186test,khóa2.343file/audit PASS |
| 7 | COMPLETE | 15augmented train/30claim mới+60reuse,8CSV/4hình/QA,221test,oracle riêng,khóa1.822file/audit PASS |
| 8 | COMPLETE | 9 phần/10 câu,12 bảng/20 hình giải thích/8 code,234 test,101 arithmetic checks,khóa31file;matrix r2 sửa1link/21link PASS |
| 9 | COMPLETE | 44codecell/20hình/12bảng,ZIP255file RunAll PASS,DOCX/PDF28trang đãxem,245test,khóa63file |
| 10 | COMPLETE | 18mục/10câu PASS,28trang đãxem,Wordreadonly28trang,245test,finalPDF/DOCX,manifest/guide,khóa16file |

24/10/2026: tạo folder bài riêng; đối chiếu bộ nguồn 105 trang PDF (5 file) và 966 dòng
Python; đọc đầy đủ yêu cầu/companion/slide/code và các mục nghiên cứu liên quan.
Không mở TEST cũ, không cài phần mềm, không chạy code tham chiếu.
Bước kế tiếp hiện hành: **không còn phase chưa làm; chủ bài tự nộp PDF cuối theo hướng dẫn của lớp**.

24/10/2026, cập nhật v1.1: người dùng bổ sung yêu cầu lý thuyết ngắn/dễ hiểu và giải
thích rõ mọi biểu đồ; ghi U01/U02 và bắt đầu phase 1 theo yêu cầu. Không đổi mô hình
hoặc budget đã đề xuất; protocol thí nghiệm vẫn chỉ được khóa ở phase 2.

24/10/2026, nghiệm thu phase 1: `docs/phase01_report.md`; input lock 9 file và
verification PASS. Probe kernel lỗi cũ đã dừng đúng process, probe thành công đã
đóng kernel; không còn writer cần resume. Không thực hiện phase 2 khi chưa được yêu cầu.

24/10/2026, v1.2 nghiệm thu phase2 theo yêu cầu: REF giữ nguyên, CONTROLLED tách RNG;
Q câu3=4,65, margin5/3, frozen DEV/role swap và checkpoint resume exact PASS.
Protocol đăng ký 56 run/61 learner instance cho các phase sau, 5 config/5 seed;
Gold cutoff TRAIN08/2006 chỉ đọc metadata, chưa fit kernel. 103 test/0skip;
coverage combined95,4296%, core dòng97,7492%/nhánh91,6667%.
Smoke100REF+100CONTROLLED/4.000 train market step thử +120DEV step, charts0;
không gọi reference main, không fulltrain/final hay TEST V3. Source/input/env bảo toàn.
Khóa48 file SHA256 `dfc338bfce41cbb4462c2e3fe7b04168f5193ab79f154d108024b75d65ce7832`.
Lỗi so tuple/list trong CLI/auditor đã sửa trước seal bằng canonical JSON, giữ
nguyên protocol/checkpoint và không chạy lại smoke. Không có queue đang chạy.
Đọc `docs/phase02_operations.md` khi tiếp tục; phase3 chỉ chạy khi được yêu cầu.

24/10/2026, v1.3 nghiệm thu phase3: dependency phase2 PASS. Pretrain116 test/0skip,
khóa source/config/seed trước train ở `evidence/phase03/declaration.json` SHA256
`50615dbdf5dbcb3893f0039a08f134f51ab17ec8c7e810797f0d4b1deec27506`.
REF adapter dùng class thầy và loop instrument parity với3 fixture; giữ nguyênRNG,
không gọi main. Hai run fresh zero-Q hoàn tất, không recovery thật hoặc train lại.
RL/rule profit/bước train: REF33,45548/32,83930; CONTROLLED33,74759/33,28637.
DEV100/vai cùng tape cho hai Q: hành vi giữ giá giống trên state đạt tới; trung bình
hai vai RL/rule đều35,43125. Không đổi config từ DEV, không gọi đây là final/kết luận đa seed.
4 PNG grayscale có notes và visualQA PASS. Final122 test, coverage94,9367% chỉ ba
module mới; source/lock/input cũ giữ nguyên. Registry trained2 entry, final count0.
Khóa268 file SHA256 `25b050a28691073aab61064b3d3bf3d32ae1aac2388c2c6ccc681a099118a00a`.
Không có queue đang chạy. Phase4 chỉ chạy khi được yêu cầu; tái dùng baseline11,
chạy24 run CONTROLLED còn thiếu. Đọc `docs/phase03_operations.md` khi tiếp tục.

24/10/2026, v1.4 nghiệm thu phase4 theo yêu cầu: dependency phase3 PASS, pretrain132
test/0skip và source declaration SHA256
`cec88cd1d8300c9325c6b27f605b208c973e05297d06d3863481f9e7f7d9b92a` trước train.
Đã đủ25 CONTROLLED (24 mới, baseline11 reused registration gốc); REF42 giữ riêng,
tổng26 scientific run của bài. Không failed/resumed scientific run; controller COMPLETE/PID=null.
Whole-train RL mean±sample std/bước qua5 seed: baseline33,76528±0,09989;
alpha_low30,91717±3,91720; alpha_high31,97780±0,12472;
epsilon_low_fixed32,89187±0,18749; epsilon_high_fixed30,92305±0,09846.
Alpha_low seed55 vẫn giữ trong báo cáo; khác biệt seed giải thích vùng mờ rộng,
không đổi budget/config hoặc loại run. Không kết luận final policy từ train score.
4 PNG grayscale đã xem, notes đầy đủ; manuscript `report/sections/phase04_sweeps.md`.
137 test/0skip, coverage100% chỉ sweep_runs/sweep_analysis/sweep_summary (không phải
toàn project/teacher/CLI/plots/auditor). Khóa phase1–3 và asset cũ giữ hash.
Khóa2.792 file SHA256 `3ff17f6682ae26c5303a5d07450f6c0ce44df6304223838e63eb8da0371d7f38`.
Final count0, không DEV mới trong4. Tiếp phase5 khi được yêu cầu: đọc registry25 Q,
khóa evaluator/gate/journal trước forward,500 episode/vai/seed cuối riêng; không tuning.

24/10/2026, v1.5 nghiệm thu phase5 theo yêu cầu: dependency phase4 audit PASS;
152 pretest/0skip, declaration evaluator/Q/job trước forward SHA256
`5fd71f5c3bf70413c8bd456f79bb59ea75088a72149454cc5c3573ec871e8fa1`.
71/71 claim hoàn tất,count1:50core+20controls+1REF native;35.500 episode rows,
710.000 market step. Không scientific failure/partial/replay,không train/DEV mới.
CONTROLLED mean±sample std/bước sau gộp vai: baseline34,02786±1,22178;
alpha_low33,90382±2,60833;alpha_high32,06337±4,25085;
epsilon_low_fixed33,39952±2,64330;epsilon_high_fixed32,87013±3,58062.
Q−rule trong cùng trận dương không đồng nghĩa thắng policy đối chứng cùng opponent;
cả5 cấu hình có mean thấp hơn Rule control35,05235. Giữ nguyên kết quả và mọi seed.
REF nativeQ35,12750/rule34,96850 riêngrole0,n1,không gộp vào5 CONTROLLED seed.
6CSV/4PNG grayscale đã xem,notes đầy đủ,bản thảo phase05_final_evaluation.md.
157 test/0skip,coverage94,3182% chỉ3 module evaluator/journal/aggregate;lint/parser/CLI PASS.
Khóa phase1–4,source thầy,7 parent asset/Gold metadata giữ hash. Khóa329 file SHA256
`8aa5969bacbeb6e069bf357453c4679600f5a9fcd6e58064eea4dbf192c2865c`.
Controller COMPLETE/PID=null. Registry evaluated riêng,không sửa counter snapshot3/4.
Tiếp phase6 khi được yêu cầu;không tự mở robustness/improved hoặc build PDF/DOCX.

24/10/2026,v1.6 nghiệm thu phase6 theo yêu cầu: dependency5 audit PASS.181pretrain
test/0skip,source/kernel/design declaration trước train SHA256
`d95096c67d760240c1ee8ac45264d8dcdbe59d067baff97b26ce2e999f9288a8`.
Đủ15train(5two-learner pair +10variant),20learner instance,không scientific failure/
resume.Tổng41/56registered market run của bài;còn15run phase7.Không train lại core25.
Gold chỉ prefixTRAIN560 tháng,559regime/558transition,counts[[240,99],[99,120]],
kernel[[0,706745;0,293255],[0,452489;0,547511]];không missing/impute/bridge hoặc dùng
giá validation/TEST;đây là proxy demand giả lập từ giá vintage,không backtest đầu tư.
Final declaration160job trước forward SHA256
`f03206ede3ec1973e94270985c2a19f01bbdaa38007de5f382c395c030481a2d`.
160/160count1,80.000episode rows/1.600.000market step,không partial/failure/replay.
Q8fixed-rule return qua5pair seed:e0=29,55358;e1000=34,48443;e2500=34,23232;
e5000=31,58872.Không chọn checkpoint tốt nhất;drift612statechange/500learner-interval.
Persistent meanbaseline34,54252/retrain33,06165;Gold30,16204/29,35694.Paired delta
retrain−baseline:−1,48087±2,70026 và−0,80510±3,54276.Không ép retrain thắng,không
loại seed hoặc tuning.Two-learner/pair aggregation không coi10learner là10replicate.
9CSV/4PNGgrayscale đã xem,notes/manuscript đầy đủ.186test/0skip,coverage97,1875%
chỉgold_regime/pair_training/phase06_journal/phase06_analysis;lint/parser/CLI PASS.
Audit chỉ savedoutputs,bảo toàn3.336protectedfile/7parentasset/Goldprovenance.
Khóa2.343file SHA256 `9637d62f6c2061f173d0147d77d368bf2d85e21b5049d60320a7edca0d5d68d3`.
Controller COMPLETE/PID=null,không queue/acceptancewriter.Không sửa file đã khóa;
tiếp phase7 theo yêu cầu,giữ Q/kernel/budget để so augmented agent trên cùng chuẩn.

24/10/2026,v1.7 nghiệm thu phase7 theo yêu cầu: dependency6 audit PASS.216pretrain
test/0skip,train source/spec/reference declaration SHA256
`9c14187e3aca833e70389395db4b9115c6b24ba3512db29f70ca8a249fd236d9`.
Đủ15augmented run,3kernel×5seed,320Qvalue,Q0,51checkpoint/run,không scientific
failure/resume. Tổng56/56market train run và61learner instance đúng protocol.
Eval declaration trước30newclaim SHA256
`909607dff359f2ec12a90d2c5d4738c76bf54f1a98b97f1f6ef65cf943690975`.
30/30count1,15.000new episode rows/300.000newmarket step;60reference chỉreuse
saved output từ5/6. So sánh90member/45.000savedrow,không90forwardmới.
Meanprofit augmented/baseline/rule:IID30,27341/34,02786/35,05235;
persistent30,97311/33,06165/35,02665;Gold27,10489/29,35694/31,07485.
Paired augmented−baseline:−3,75445±1,52304;−2,08854±3,69446;−2,25205±2,93133.
Không đạt cải thiện robust theo tiêu chí đã đề ra;giữ mọiseed,không ép model mới thắng.
Oracle γ1 optimal expectedprofit/bước35/35/31,01586;γ0,9discountedtotal riêng,
không cấp nhãn train hoặc tính làfinalclaim. Model-policy expectations/gap táitính
bằng simulator biết trước,fixedrule,không sampledforward.Nhiễu có thể làm score
MonteCarlo hơi cao hơn expectedbound,không sửa output để che điều này.
8CSV/4PNG grayscale đã xem,notes/manuscript đầy đủ;221test/0skip,coverage96,3964%
chỉ6module mới;lint/parser/CLI PASS.Bảo toàn5.679protectedfile cũ/7parentasset.
Khóa1.822file SHA256 `06d4046f04abc456ba703819a4fe4c8bdee5f2757830d1409902ef4764e9f607`.
Controller COMPLETE/PID=null,khôngqueue/writer.TiếpPhase8theoyêucầu:viết10câu,
question-evidence matrix,báo cáo ngắn/dễ hiểu và phân tích sốđo thật;không train/
TEST lại,không tự build/nộpPDF ởPhase7.

24/10/2026, v1.8 nghiệm thu phase8 theo yêu cầu: parent7 audit PASS. Viết đầy đủ
9 phần/10 câu,12 bảng,20 hình kèm phân tích và8 source excerpt,8.047 đơn vị tách
theo khoảng trắng (không phải page count). 70 input file/hash,409 numeric source
record/88 token trong văn,101 phép đối chiếu số học PASS. 234 test/0skip,coverage
96,7213% chỉ report_assets; Ruff/CLI PASS. Giữ 7.501 file khóa cũ/7parentasset.
Khóa nội dung31file SHA256
`5399801278e64aaed9b6535ac4d9684e31434311a4623e33c5bd153445f8bbc6`.
Sau seal phát hiện duy nhất link matrix `(phase 08/manuscript.md)` sai đường dẫn;
giữ file gốc và thêm matrix r2 chỉ thay một link. Kiểm21link/31filegốc PASS,
khóa4file presentation_r2 SHA256
`ae374a5358940f1c5dd97b4be9bd4a596e5dcb07f74a3ef31aca6b61af80027c`.
Bản thảo khoa học và mọi kết quả không đổi. Bản REF cũ vốn đã đúng; nhận định
commentary nhầm đã được đính chính,không tạo sửa số liệu không có thật.
Không thêm train/final claim,không notebook execution/DOCX/PDF hoặc nộp bài.
Metadata cá nhân/nhóm/team_name còn chờ xác nhận trước filename phát hành.
Tiếp `làm AG02 phase 9`: đọc active_report.json,build notebook read-only và tài
liệu ứng viên bằng toolchain hiện có;không ghi đè nội dung đã khóa hoặc train/eval lại.

24/10/2026,v1.9 nghiệm thuPhase9 theo yêu cầu. Dependency8 chỉđọc trước/sau PASS;
7.501protectedfiles/7parentasset giữhash,101arithmeticchecks cũ khôngđổi.
Notebook108cell/44codecell thực thi,hiển thị12bảng/8excerpt/20PNGvà10câu;
khôngimport scientificrunner hoặcforward. ZIP255payloadfile/15.746.858byte,
hash `4382e8321924115e2247fd51433bfabcae8258204ed94ea827b7efb9072bbf10`;
RunAll từbản giải nén cũng44cell PASS,255file trước/saugiữhash.
DOCX/PDFứngviênr3 có28trang,14native table/20figure/8exactsourcecode;28PNG125dpi
đãmởxemriêng/QA PASS. ChữDOCX/PDFđen,mọiPNGgrayscale,10headingcâu trongPDF.
R1/r2 giữlịch sử,không dùng làmcurrent. User xácnhận nộpcánhân/bìa vàfilename
agent02_D23CTPM01_TrieuTuanAnh.pdf. Runtimecode/docslocal hiện có đượcreuse,
không cài/sửaGPUenvironment. Lầnseal banđầu chưa chạy vìusage-limitreviewfailure;
người dùng yêu cầu tiếp tục,lệnhseal tiếp theoPASS. 245test/0skip,coverage98,8889%
chỉpublicationhelper,Ruff/CLI PASS. Khóa63file SHA256
`c482f44341c0d314ffed40f1084f37d59a4c58f10f60497ea2ac4c6db5c1886d`.
Không train/finalclaim mới,khôngcommit/push/nộpbài. Tiếp **làm AG02 phase10**
chỉkhiđược yêu cầu:kiểm rubric/toàn bộtrang vàpháthànhPDF/DOCXcuối từcandidate
đãQA hoặcpresentationrevision mới;không hỏi lại metadata cá nhânđãchốt.

24/10/2026,v1.10 nghiệm thuPhase10:parent9hash PASS;đềS1trang8–12 và18mục
rubric được đối chiếuPDFthực,đủ10câu/20figurelocator. Soexact12Wordtable với
artifact và8sourceexcerpt,kểcảterminal;không thay nội dung. Đã mởxemlại28PNG
125dpi,PDF/DOCXbytekhôngđổi nênreuse latest render. Word16.0readonlyPASS,
28trang/14bảng/field0error,khôngsave/khôngđụng phiên Worduser. 245test/0skip,
coverage98,8889%chỉpublicationhelper,RuffPASS. Fullparentaudit kiểm7.501file/
7parentasset/hashuv.lock và101arithmeticchecks PASS,khôngtrain/evaluate mới.
FinalPDF SHA256c15a623023525257af0a95cc72af0ae4a4ffca887a69bd9175d22295188f518e,
3.509.427byte;DOCX SHA2567b215b3c7e865ed849305a3dafffcdf1cd7b39b5aa02db36650329546507301d,
4.505.765byte. Manifest/guide ởoutput,khóa16file SHA256
`06cdbb14f8e2e1d2b7c7f652e287d18acaa9861b91fcad7f6a056322add6f541`.
CheckpointAG02COMPLETE,completed0..10,next=null;chưa gửi bài cho thầy,không
commit/push hoặcđụngbàiV3/DiscoveringAI. Sửa sau này tạorevision,mọifilecũ giữnguyên.
