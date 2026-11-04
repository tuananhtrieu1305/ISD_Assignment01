# AG02 Phase 7 — kiểm chứng agent có thêm trí nhớ và thời gian

Ngày 24/10/2026. Đã train đủ 15 agent theo thiết kế định trước và hoàn tất 30 lượt
đánh giá mới, mỗi lượt đúng một lần. Kết quả cho thấy **thiết kế state đầy đủ hơn
chưa giúp policy tốt hơn với ngân sách 5.000 episode** trong thí nghiệm này. Giữ
nguyên mọi seed và kết quả; không train thêm hoặc sửa tham số theo final score.

## Thiết kế trả lời câu 10

Đề xuất giữ Q-learning bảng, bổ sung hai thông tin vào state: hành động trước của
chính mình và số bước còn lại. Như vậy learner thấy nhu cầu, hành động trước của
mình, hành động trước của đối thủ và thời gian còn lại. Các thông tin đều có thể
biết ở thời điểm quyết định; không nhìn hành động hiện tại chưa chọn của đối thủ.

| Thành phần | Cách thực hiện |
|---|---|
| State | `(demand, own_previous, competitor_previous, remaining_steps)`; ba biến nhị phân, thời gian 1…20 |
| Action | 0 giữ giá, 1 giảm giá; giống baseline |
| Reward | Lợi nhuận bằng doanh số nhân margin; không đổi để ưu ái agent mới |
| Method | Q-learning bảng, 320 giá trị; α0,1, γ0,9, epsilon0,2 giảm0,995 đến0,02 |
| Budget | Mỗi kernel5seed, mỗi run5.000episode×20step, Q khởi tạo0 |
| Evaluation | Q đóng băng, không khám phá, 500episode/vai, cùng đối thủ luật và scenario tapes |
| Tiêu chí robust | Paired profit qua3kernel, độ phân tán seed, action rate và chi phí; không chỉ nhìn curve train |

Fixture chỉ ra lý do sửa state: ở nhu cầu cao và đối thủ trước đó giữ giá, nếu chính
mình trước đó giữ giá thì rule hiện tại giữ giá; nếu mình trước đó giảm giá thì rule
hiện tại giảm giá. Hai trường hợp có cùng observation cũ, nhưng reward kỳ vọng khi
learner giữ giá là55 và45. Q cũ gộp hai lịch sử này; state mới phân biệt được. Đây là
phân tích simulator, không phải hai mẫu final hoặc phép sửa baseline sau kết quả.

Thêm thời gian còn lại giúp phân biệt bước gần cuối với bước còn xa. Bước cuối
chỉ học từ reward hiện tại, không bootstrap sang time0. Full state có160 khả năng,
hai action nên320giá trị Q, so với8giá trị của baseline. Thông tin nhiều hơn cũng
làm dữ liệu bị chia cho nhiều ô hơn; không bảo đảm cùng ngân sách sẽ học tốt hơn.
Với đối thủ cũng thay đổi chính sách, việc bổ sung state này chưa giải quyết toàn
bộ khó khăn tương tác; thí nghiệm câu10 ở đây dùng fixed rule.

Các hàm chính được hiểu đơn giản:

| Hàm | Vai trò |
|---|---|
| `observe` / `state_index` | Lấy thông tin hiện tại, đổi thời gian1…20 thành vị trí0…19 trong bảng |
| `act` | Epsilon-greedy khi train; khi đánh giá chỉ chọn Q lớn nhất, phá đồng hạng có seed |
| `learn` | Cập nhật một ô Q từ reward và state kế; xử lý bước cuối riêng |
| `run_chunk` | Chạy một nhóm episode, ghi reward, action, visitation và trace |
| `checkpoint` / `from_checkpoint` | Lưu và khôi phục Q, log cùng toàn bộ RNG, không bắt đầu lại run |
| `evaluate_augmented` | Đo policy cuối trên tapes mới, Q chỉ đọc và hash không đổi |
| `solve` / `policy_value` | Tính kỳ vọng từ mô hình đã biết để đối chiếu; không dạy Q bằng nhãn oracle |

## Những lượt chạy và đối chứng đã dùng

15run mới:IID/persistent/Gold×5seed11/22/33/44/55. Kernel Gold dùng nguyên artifact
TRAIN Phase6, không fit lại hoặc đọc giá validation/TEST để chỉnh mô phỏng. Môi
trường, conversion, margin, action, đối thủ và ngân sách giữ như baseline. Policy
RNG độc lập demand/sales và cùng quy tắc seed như core.

Train có75.000episode rows,1.500.000market step,51checkpoint/run, Q/policy160state,
visits320ô và trace20bước. Không có scientific failure/resume; cả15run bắt đầu Q0,
không nhận action hoặc Q tối ưu từ oracle. Toàn bài hiện đủ56market run/61learner
instance đã đăng ký trong protocol, chưa cần thêm lượt ngoài ma trận.

Train declaration SHA256:
`9c14187e3aca833e70389395db4b9115c6b24ba3512db29f70ca8a249fd236d9`.
Eval declaration SHA256:
`909607dff359f2ec12a90d2c5d4738c76bf54f1a98b97f1f6ef65cf943690975`.

30claim mới là15Q×2vai, có15.000dòng episode/300.000market step. Reuse60claim:
IIDbaseline/rule từPhase5 và baseline đã train lại/rule trênpersistent/Gold từPhase6.
Không forward lại các đối chứng. So sánh dùng90member/45.000saved episode rows;
đó không phải90lượt đánh giá mới. Index trước train lưu job/result/receipt/hash.

Baseline chính được train trên cùng kernel với agent mới. Nhờ vậy không gộp tác
động của thay state với tác động đổi phân phối train. Gộp hai physicalrole trước,
sau đó tính mean/sample std qua5training seed/kernel. Rule không train: n5 là năm
scenario panel. Không xem500episode là500learner độc lập hoặc gọi whisker là CI.

## Kết quả cuối và mức độ robust

Đơn vị lợi nhuận giả lập/bước, mean±sample std sau gộp vai:

| Kernel | Memory/time | Baseline cùng kernel | Rule |
|---|---:|---:|---:|
| IID |30,27341±0,60242|34,02786±1,22178|35,05235±0,22585|
| Persistent |30,97311±1,69375|33,06165±2,63493|35,02665±0,25749|
| Gold |27,10489±0,28315|29,35694±2,78040|31,07485±0,21348|

Paired delta tính từng seed cùng tapes, rồi tổng hợp qua5seed:

| Kernel | Memory/time − baseline | Memory/time − rule |
|---|---:|---:|
| IID |−3,75445±1,52304|−4,77894±0,53768|
| Persistent |−2,08854±3,69446|−4,05354±1,74828|
| Gold |−2,25205±2,93133|−3,96996±0,40610|

Mean của thiết kế mới thấp hơn cả hai đối chứng trên cả ba kernel. Độ lệch giữa seed
nhỏ hơn baseline trong bảng profit không đủ để gọi robust hơn khi mức lợi nhuận
thấp hơn. Persistent seed44 vàGold seed11 có delta so baseline dương, nhưng mean
nhóm vẫn âm; không chọn riêng các seed tốt. Không có kiểm định ý nghĩa thống kê
hoặc kết luận rằng mọi agent có memory/time luôn kém hơn.

Tỷ lệ giảm giá final trung bình của agent mới là43,998%/37,480%/43,834% trên
IID/persistent/Gold. Đây là hành động của policy greedy sau train, không phải epsilon
đánh giá: epsilon final bằng0. Hành động giảm giá làm margin từ5 còn3 như core;
không thể dùng số lần giảm giá hoặc doanh số cao để thay thước đo lợi nhuận.

State mới phân biệt được lịch sử và bước còn lại theo fixture, nhưng kết quả hữu
hạn không đạt tiêu chí cải thiện robust đã đề ra. Bảng lớn hơn, cùng budget, mức
thăm ô không đều và lịch khám phá có thể liên quan đến khó học; đây là giả thuyết
cần thí nghiệm khác được đăng ký trước, không phải nguyên nhân đã được chứng minh.
Không tăng budget hoặc chọn lại checkpoint từ các final score vừa mở.

## Đối chứng tính toán từ mô hình đã biết

Oracle dùng simulator đã biết và fixed rule, tính lùi từ bước cuối để tìm kỳ vọng
tốt nhất. Nó biết transition/reward; Q-learning vẫn học từ tương tác với Q0. Không
gọi oracle là agent model-free vừa được train. Cùng policy greedy cũng được tính
kỳ vọng bằng mô hình, với phân phối đều giữa các action đồng hạng gần nhất.

| Kernel | Oracle: kỳ vọng profit/bước, γ1 | Memory/time: kỳ vọng profit/bước trung bình | Gap kỳ vọng |
|---|---:|---:|---:|
| IID |35,00000|30,21586|4,78414|
| Persistent |35,00000|30,96036|4,03964|
| Gold |31,01586|27,04324|3,97262|

Rule từ trạng thái reset có gap kỳ vọng0 trong cả ba mô hình này. Đây là tính chất
của simulator/fixed rule đang xét, không có nghĩa rule luôn tối ưu trong kinh doanh.
Score MonteCarlo500episode có thể hơi cao hơn kỳ vọng oracle do nhiễu: ví dụ rule
IID quan sát35,05235 so với kỳ vọng35. Không sửa score để ép nó nằm dưới bound.

CSV còn lưu kỳ vọng total chiết khấu γ0,9 và gap tương ứng để đối chiếu target Q.
Giá trị tối ưu γ0,9 củaIID/persistent là307,44817 vàGold275,47308; đơn vị này khác
profit/bước không chiết khấu. Không trộn hai cột khi kết luận. Tính lại kỳ vọng không
dùng RNG/scenario, không tạo claim mới hoặc mở TEST của bài cũ.

## Chi phí, hình và cách giải thích

Payload Q float64 tăng64→2.560byte,40lần nhưng vẫn nhỏ tuyệt đối; đó không phải
peakRAM hay toàn bộ bộ nhớ chương trình. Phần ô state-action được thăm trung bình
trên tổng bảng lý thuyết khoảng83,6%/78,4%/81,8% cho ba kernel; baseline là100% của
8ô. Một số fullstate không thể đạt từ reset/horizon, nên không coi phần chưa thăm
là bằng chứng trực tiếp của lỗi hoặc thiếu khám phá.

CPU loop train trung bình(agent mới/baseline), giây mỗi100.000market step:
IID7,3186/6,5035;persistent7,1533/6,9060;Gold7,2149/6,5628. Số đo có instrumentation,
không gồm checkpointI/O/report; các lượt chạy khác thời điểm không phải benchmark
hệ thống độc lập. Không gán Qpayload thành RAM hoặc dùng walltime để tuyên bố GPU.

Bốn hình grayscale đã được mở xem và kiểm nhãn:

- `augmented_training.png`: ba panelkernel, Xepisode,Yprofit/bước. Làm MA100 từng
  seed rồi vẽ mean và dải±sample std qua5seed. Memory/time có MA100 cuối29,94750/
  30,39230/26,94880, thấp hơn baseline34,28750/33,28630/29,85110. Curve train vẫn
  khác phép đo final Q cố định; đường phẳng không tự chứng minh hội tụ.
- `augmented_final_profit.png`: mỗi kernel so ba policy; cột mean, whiskerstd.
  Các panel khác phân phối nhu cầu; so policy trong cùng kernel là so sánh chính.
- `augmented_paired_delta.png`: tròn đen trừ baseline, vuông xám trừ rule, mốc0 là
  không chênh. Tính delta theo seed sau gộp vai. Whisker qua0 không phải một kiểm
  định và không làm mean âm trở thành kết quả cải thiện.
- `augmented_coverage_cost.png`: bên trái phần ôQ đã thăm, bên phải CPUlooptrain.
  Hai trục có đơn vị khác nhau; không so trực tiếp độ cao cột giữa hai panel.

Mỗi hình có source/trục/đơn vị,n,aggregation,quan sát định lượng và giới hạn tại
`artifacts/figures/phase07/figure_notes.md`/JSON. Có8CSV:seed comparison,policy summary,
paired deltas,delta summary,train curves,cost coverage,model expectations,oracle summary.
Bản thảo để ghép báo cáo: `report/sections/phase07_improved_agent.md`.

## Nghiệm thu và phần tiếp theo

221test PASS/0skip; coverage combined96,3964% trên6module mới:augmented,
augmented_runs,augmented_final,phase07_journal,market_oracle,phase07_analysis.
Statement97,2892%,branch93,75%; không phải CLI/plots/auditor/baseline cũ/toàn project.
Pretrain216 và final221 lưu riêng. Fixture development từng so số thực45,00000000000001
bằng45 tuyệt đối; đã sửa kiểm xấp xỉ trước declaration, không đổi reward/thuật toán.
Ruff,PowerShell parser và CLIhelp/status đạt.

Auditor chỉ đọc saved checkpoints/claims/reference/hash, tái tính bảng và kỳ vọng
phân tích; không train hoặc sampled forward. Giữ khóa Phase1–6,source thầy,Gold và
7asset tham chiếu. Khóa/verification ở evidence/phase07/,registry trained/evaluated
mới ở artifacts/manifests/phase07/. Controller kết thúc/PID=null; không queue nền.

Tiếp theo khi được yêu cầu: **`làm AG02 phase 8`**, viết đủ10câu và báo cáo từ kết
quả thật. Không tự build PDF/DOCX, nộp bài hoặc mở lại train/final ở Phase7.
