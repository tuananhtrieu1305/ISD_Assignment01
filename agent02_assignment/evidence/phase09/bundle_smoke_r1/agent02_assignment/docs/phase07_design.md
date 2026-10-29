# Phase 7 — thiết kế trước train cho câu 10

Ngày 24/10/2026. Chỉ Phase7; không chỉnh tham số theo kết quả Phase5/6 hoặc mở lại
đánh giá cũ. State tăng memory/time đã được định trước trong protocol Phase2.

## Mục tiêu và mô hình

Một Q-learning trước fixed rule như baseline. State mới là (demand, own_previous,
competitor_previous, remaining_steps). Bốn thành phần lần lượt cho biết nhu cầu,
hành động trước của mình, hành động trước của đối thủ, số bước còn lại (1…20).
Hai action giữ giá/giảm giá, reward profit không đổi. Q có2×2×2×20×2=320giá trị,
thứ tự axis(demand,own_previous,competitor_previous,remaining_minus1,action).

Fixture: demand1/competitor_previous0 giống nhau, nhưng own_previous0/1 làm rule
hiện tại chọn0/1; giữ giá có reward kỳ vọng55/45. State cũ không phân biệt hai lịch
sử đó. Đây là phép phân tích simulator, không phải số đo final hoặc sửa baseline.
State mới thêm thông tin nhưng cần học nhiều giá trị hơn; không mặc định sẽ tốt hơn.

## Ma trận train và tiêu chí đo

15run đã đăng ký:IID/persistent/Gold ×5seed11/22/33/44/55. Fresh zeroQ,5.000episode
×20step,α0,1/γ0,9/epsilon0,2 decay0,995 min0,02. Kernel Gold reuse đúng artifact TRAIN
Phase6, không fit lại. Mọi phần môi trường, đối thủ, budget và stream RNG giữ nguyên.
PolicyRNG SeedSequence([seed,3]), như baseline; demand/sales riêngchannel0/1/2.
Checkpoint mỗi100episode gồm Q,visits,log,RNG,51checkpoint/run. Explicit resume đúng
checkpoint cho run chưa xong, không train lại DONE;guard tối thiểu5GiB,một writer.

Đánh giá mới chỉ30claim:15Q×2physicalrole,500episode×20step/vai,no learn/exploration,
phá đồng hạng bằng np.isclose(rtol1e-5,atol1e-8) vàRNGchannel4 như Phase5/6.
Scenario_seed2000000+train_seed,Tape.generate gốc,initialdemandBernoulli0,5/history0.
FrozenQ copyread-only/hash trước/sau. JournalPhase7 riêng,claim exclusive trướcforward,
count1,không reset/replay consumedclaim. Eval declaration pin toàn30job/Q sau train,
source/evaluator/test/design đã khóa từ trước train;không chọn checkpoint theo final.

So ba phương án:augmented,baseline cùngkernel vàrule. Reuse60claim đã lưu:
IIDbaseline/rule từPhase5;baseline retrain/rule trênpersistent/Gold từPhase6.
Không forward lại reference;trỏ exactjob/Q/result/receipt/hash. Pin index trướctrain.
So policy cũ train trên cùngkernel, cùngbudget, thay đổi chính làstate. Không dùng
QIID cũ làm baselinechính trênGold vì đồng thời đổi phân phối train sẽ gây nhầm.
Kiểm actualmarket/kernel/seed/episode/tieRNG tương thích dù tênschema scenario khác.

Gộp2vai trước,rồi mean/sample std(ddof1) qua5seed/kernel. Paired delta augmented−baseline
vàaugmented−rule cùngseed/tape;không giảepisode/timestep độc lập,không CI/tuning mới.
Tiêu chí robust:delta qua3kernel,độ phân tán seed,discount rate,visited cells vàchi phí.
Báo CPU/wall loop train vàQpayloadfloat64(320vs8) riêng,không gọi làpeakRAM hoặc
benchmarkmáy;CSV/checkpointI/O không nằm trongtrainloop timing. Không buộc agentmới thắng.

## Oracle bổ trợ, tách khỏi learner

Tính lùi hữu hạn trên simulator đã biết/fixedrule để kiểm kỳ vọng. Oracle quan sát
fullmemory/time và biết transition/reward;không phải agent học model-free. Không
chuyển action/Q tối ưu thành nhãn/initialization/curriculum cho learner.
Hai mục tiêu phải phân biệt:γ0,9 phù hợp targetQ;γ1 làtổng reward không chiết khấu,
chia20 mới cùng đơn vị profit/bước. Gap tính từkỳ vọng phân tích của policy,
không ép scoreMonteCarlo mỗi run nằm dưới bound vìcòn nhiễu sampling.
Oracle không dùng dữ liệuTEST hoặcRNG,không tính làfinalclaim thứ31.

## Đầu ra dự kiến

Q/policy160state,visits320cell,rawlogs/checkpoints,traincost. Bảng3kernel/3policy,
paired deltas,exact model-value/gap vàcoverage. Hìnhgrayscale:trainMA100,finalprofit,
paired delta,coverage/cost;mọi hình cótrục/đơn vị,n,mean/std,source,số liệu vàgiới hạn.
Viết đủstate/action/reward/method/evaluation,giải thích đơn giản;không thêmcôngthức
phức tạp hoặc tuyên bố áp dụng kinh doanh/điều trị thật. Không thực hiện Phase8–10.
