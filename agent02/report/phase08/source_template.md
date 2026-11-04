# SO SÁNH TÁC TỬ HỌC TĂNG CƯỜNG VÀ TÁC TỬ THEO LUẬT TRONG MÔ PHỎNG THƯƠNG MẠI ĐIỆN TỬ

## 1. Thông tin báo cáo

Học viện Công nghệ Bưu chính Viễn thông

Môn học: Phát triển hệ thống thông minh — Intelligent System Development

Bài thí nghiệm: Agent02 — Reinforcement-Learning-Based Agents versus Rule-Based Agents

Sinh viên: Triệu Tuấn Anh

Mã sinh viên: B23DCCN053 — Lớp: D23CTPM01

Tháng 10 năm 2026

## 2. Mở đầu và mục tiêu

Trong mô phỏng hai cửa hàng, tác tử theo luật không học nhưng vẫn có thể thu lợi
nhuận tốt hơn tác tử Q-learning. Kết quả này đặt ra câu hỏi chính của bài: cần đo
thế nào để phân biệt một quyết định hợp lý về thiết kế với một chính sách thực sự
hiệu quả sau khi học? Báo cáo khảo sát câu hỏi đó bằng code và dữ liệu thực nghiệm,
thay vì mặc định phương pháp có khả năng học sẽ luôn thắng.

Bài làm thực hiện các thí nghiệm A–E của đề [S1]: tái lập baseline, theo dõi reward
khi học, đổi learning rate, đổi exploration và đánh giá policy riêng. Sau đó, bài
khảo sát hai tác tử cùng học, sửa động lực nhu cầu và kiểm chứng state có thêm trí
nhớ/thời gian. Tất cả dùng mô phỏng thương mại điện tử; không coi reward là doanh
thu của một cửa hàng thực hoặc kết quả kiểm chứng đầu tư.

### 2.1. Các khái niệm cần dùng

Một tác tử nhận thông tin về môi trường và chọn hành động để hướng đến mục tiêu.
Trong bài, thông tin gồm mức nhu cầu và lịch sử hành động; hành động là giữ giá
hoặc giảm giá; mục tiêu là tích lũy lợi nhuận. Một **policy** là cách ánh xạ thông
tin đang có sang hành động. Policy có thể được viết bằng luật hoặc hình thành
từ kinh nghiệm học. Không cần một mô hình ngôn ngữ lớn để tạo thành tác tử [S6,
trang PDF3].

**Học tăng cường (RL)** học qua tương tác: chọn hành động, nhận reward, quan sát
kết quả và điều chỉnh quyết định. Khác với học có giám sát, dữ liệu ở đây không
cung cấp sẵn nhãn “hành động đúng” cho mọi tình huống. **Q-learning** lưu giá trị
ước lượng của từng cặp state–action trong bảng Q; giá trị này cân nhắc cả reward
hiện tại và lợi ích tương lai có chiết khấu [S4, trang PDF1–7].

**Exploration** là thử hành động để có thêm kinh nghiệm; **exploitation** là chọn
hành động đang được đánh giá tốt. Epsilon điều khiển xác suất chọn ngẫu nhiên khi
train, còn alpha điều khiển mức sửa giá trị Q. Đây là hai vai trò khác nhau. Khi
đánh giá policy cuối, bài tắt exploration, nhưng vẫn phá đồng hạng gần nhau có
seed theo quy tắc của code.

Một **episode** là một lượt thị trường dài20bước, sau đó khởi tạo lại tình huống.
Một **training seed** tạo một lượt học riêng. Nhiều episode trong cùng một lượt
học không phải nhiều learner độc lập. Dùng nhiều seed giúp thấy kết quả thay đổi
ra sao khi kinh nghiệm học khác nhau, nhưng năm seed vẫn là một mẫu nhỏ.

**Hệ đa tác tử (MAS)** có nhiều tác tử tương tác qua môi trường chung, thông điệp
hoặc trạng thái dùng chung. Hai cửa hàng trong bài tác động đến kết quả của nhau
qua lựa chọn giảm giá. Đây là tương tác cạnh tranh trong simulator; không phải
một nhóm LLM phối hợp bằng trao đổi văn bản. Tài liệu [S5, trang PDF1,9] giúp phân
biệt các kiểu tương tác; bài chỉ dùng ý tưởng nền, không triển khai dự án LLM/MAS
riêng trong slide.

## 3. Môi trường và hai loại tác tử

### 3.1. Mô hình thị trường

Mỗi shop chọn một trong hai action:0giữ giá,1giảm giá. Giá gốc10, chi phí một món5,
giảm giá20%. Nhu cầu có hai mức thấp/cao, tương ứng10/20khách mô phỏng mỗi bước.
Doanh số được lấy ngẫu nhiên theo xác suất mua hàng; reward là doanh số nhân
lợi nhuận mỗi món. Các con số là giả định giảng dạy từ [S1–S3].

Xác suất mua được tính từ bốn yếu tố đơn giản: mức nền0,30; thêm0,25khi nhu cầu
cao; thêm0,15nếu shop giảm giá; trừ0,10nếu shop đối thủ giảm giá. Code chặn xác
suất vào khoảng0,05–0,95. Nói cách khác, giảm giá có thể làm tăng xác suất mua,
nhưng đồng thời làm giảm lãi trên mỗi món; reward profit mới phản ánh đánh đổi này.

Hai shop cùng chọn trước khi môi trường thực hiện một bước. Sau đó môi trường
sinh doanh số/reward, lưu hai action thành lịch sử và lấy mức nhu cầu tiếp theo.
Trong baseline, nhu cầu bước sau được lấy cân bằng0/1, không phụ thuộc action.
Doanh số hai shop được sinh riêng; không giả định một khách chỉ mua ở đúng một
shop, nên tổng sales không phải phép đo thị phần độc quyền hoặc trò chơi zero-sum.

Luồng quyết định là: **quan sát → hai shop chọn action → môi trường trả reward
và state mới → learner cập nhật Q → lặp đến hết episode**. Reward không được đưa
cho learner trước khi action hiện tại được chọn.

### 3.2. State và tác tử theo luật

State local cũ là `(demand, competitor_previous_action)`: nhu cầu hiện tại và
action trước của đối thủ. Mỗi biến có hai giá trị nên có4state; với2action, Q-table
của một learner có8giá trị. Agent không thấy action hiện tại mà đối thủ sắp chọn.
Ở đầu episode, lịch sử hai action bằng0.

Ba nhánh của rule gốc rút gọn thành: chỉ giảm giá khi nhu cầu cao **và** đối thủ
đã giảm giá ở bước trước; các trường hợp khác giữ giá. Tác tử luật không có Q-table,
không cập nhật sau reward và không có pha train. Đoạn E01 giữ đúng hành vi đó:

{{C.E01}}

Rule cố định không đồng nghĩa reward cố định. Nhu cầu, doanh số và hành động của
learner vẫn thay đổi. Vì vậy đường reward của rule vẫn dao động dù code quyết
định của nó không đổi.

### 3.3. Tác tử Q-learning và hai track thực nghiệm

Learner chọn action theo epsilon-greedy và sửa một ô Q sau mỗi bước. Reward mới
không thay thế toàn bộ bảng, mà điều chỉnh dần giá trị của cặp state–action vừa
được trải nghiệm. Bước cuối episode không dùng giá trị tương lai để bootstrap.
Ý nghĩa và phép tính cụ thể được trình bày ở câu3.

**REF** tái lập code thầy với seed42, giữ thuật toán và thứ tự RNG gốc. **CONTROLLED**
giữ luật môi trường/reward nhưng tách RNG nhu cầu, doanh số và policy để thiết kế
đánh giá ghép cặp. Hai track khác seed và cách quản lý số ngẫu nhiên; không gộp
REF thành lần lặp thứ sáu của CONTROLLED. Bản Python được sao nguyên byte từ file
thầy mang đuôi `.tex`; thay đổi phục vụ thí nghiệm nằm trong module riêng [S3,D3].

Một số câu trong đề nhắc hai RL agent, trong khi companion/code triển khai một RL
đối đầu một rule. Baseline của báo cáo theo implementation được cung cấp; thí
nghiệm hai learner cùng học được tách riêng để trả lời câu8 [S1, trang PDF6–8;
S2, trang PDF4; S3].

## 4. Thiết lập, code thiết yếu và cách đánh giá

### 4.1. Cấu hình và ma trận chạy

Mỗi run train5.000episode×20bước, bắt đầu Q bằng0. Baseline dùng α0,10, γ0,90,
epsilon bắt đầu0,20, nhân0,995sau mỗi episode và không xuống dưới0,02. Các seed
CONTROLLED là11,22,33,44,55; seed42 của REF được giữ riêng. Toàn bài chạy56lượt
thị trường và61learner instance vì5lượt two-learners có hai Q-table mỗi lượt.

| Nhóm | Kernel/cấu hình | Số market train run |
|---|---|---:|
| REF | Baseline theo code thầy, seed42 |1|
| Core CONTROLLED | Baseline, α0,01, α0,50, ε cố định0,05, ε cố định0,30; mỗi cấu hình5seed |25|
| Hai learner | Hai Q-learning cùng học, IID,5pair seed |5|
| Sửa môi trường | Persistent và Gold, mỗi kernel5seed |10|
| State memory/time | IID/persistent/Gold, mỗi kernel5seed |15|

Baseline α0,10/epsilon giảm được dùng chung cho hai sweep, không train lại để
làm hai đối chứng. Tổng56run tương ứng5.600.000market step; không đếm đôi market
step khi có hai learner. Smoke kỹ thuật và DEV được lưu riêng, không đưa vào
các bảng final. Các cấu hình, seeds và ngân sách được định trước trong protocol [D2].

Runtime là Python3.11.17 trên WSL Ubuntu, NumPy float64 CPU. Q-table nhỏ nên bài
không dùng GPU hoặc thêm mạng học sâu chỉ để làm thuật toán phức tạp hơn. Mỗi run
có raw reward theo episode, Q/policy, visitation, trace mẫu và checkpoint mỗi100
episode, gồm cả RNG để khôi phục đúng trạng thái. Tên run/config/seed và hash nằm
trong manifests kèm source.

### 4.2. Chọn action, cập nhật và tương tác

E02 cho thấy epsilon chỉ điều khiển nhánh khám phá. Nếu không khám phá, code chọn
ngẫu nhiên trong tập Q gần bằng giá trị lớn nhất; vì vậy greedy không luôn đồng
nghĩa deterministic. Quy tắc đồng hạng này cũng được giữ khi đánh giá:

{{C.E02}}

E03 là phần cập nhật Q. Nhánh `terminal` giữ target bằng reward hiện tại; không
cộng Q của một episode mới vào bước cuối episode cũ:

{{C.E03}}

E04 trích đúng một đoạn trong vòng lặp train. Hai action được lấy từ cùng snapshot
trước `env.step`; learner chỉ học sau khi nhận reward/state mới. Đoạn trích phục
vụ giải thích; module nguồn có đầy đủ reset, logging và checkpoint.

{{C.E04}}

### 4.3. Đánh giá riêng và mẫu số

Mỗi policy cuối được đo500episode×20bước **mỗi vai**. Trước tiên gộp hai vai của
cùng training seed, sau đó lấy mean và sample std qua5seed (ddof1). Rule không
được train: n5 của đối chứng là năm scenario panel, không phải năm rule learner.
Whisker/dải mean±std mô tả độ phân tán, không phải khoảng tin cậy hay kiểm định.

Scenario final dùng các seed2000011,2000022,2000033,2000044,2000055, tách khỏi seed
train và DEV. Trong cùng kernel/seed, các policy nhận cùng chuỗi nhu cầu và cùng
các số Uniform cho khách hàng/role. Sales được tính bằng số Uniform nhỏ hơn xác
suất mua, giữ phân phối Binomial nhưng tạo tình huống ghép cặp. Chỉ “cùng seed”
cho một RNG chung chưa chắc giữ cùng nhu cầu nếu số lần rút ngẫu nhiên phụ thuộc
action; vì thế bài tách các dòng ngẫu nhiên và tạo tapes riêng [D2,D5].

E05 sao Q sang bản chỉ đọc trước evaluation. E06 kiểm hash sau khi kết thúc. Các
đoạn này không thay cho toàn bộ loop; vòng lặp gốc không gọi `learn` và dùng
`explore=False` khi lấy action.

{{C.E05}}

{{C.E06}}

Mỗi final claim được ghi trước khi chạy, có kết quả/CSV và receipt count1 sau khi
hoàn tất. Bảng và hình đọc output đã lưu, không chạy lại policy để “lấy kết quả
đẹp”. Hai câu hỏi được tách: shop nào lời hơn **trong cùng trận**, và policy nào
tốt hơn **trước cùng một fixed opponent/tape**. Kết quả của hai so sánh không
nhất thiết cùng dấu.

## 5. Kết quả, bảng và giải thích hình

Các giá trị dưới đây có đơn vị lợi nhuận giả lập/bước nếu không ghi đơn vị khác.
Kết quả train đo lúc Q còn đổi và có exploration; final đo Q cuối đóng băng.
Chữ số trong bảng lấy từ artifact, có thể làm tròn khi trình bày. REF/native và
CONTROLLED luôn được ghi rõ, không gộp thành cùng một nhóm thống kê.

### 5.1. A–B: baseline, Q-table và diễn biến học

**Bảng B01. Reward và action trong hai baseline train riêng biệt.** Mỗi agent có
100.000action; các tổng reward được chia đúng100.000bước để tính mean [D3].

{{T.baseline_train}}

**Bảng B02. Q và policy cuối train, không phải profit final.** Action0giữ giá,
action1giảm giá. Tập greedy được tính trực tiếp từ hai Q-value ở mỗi state [D3].

{{T.q_policy}}

REF giảm giá ở hai state có action trước của đối thủ bằng1; CONTROLLED seed11
chọn giữ giá ở cả bốn state. Hai Q-table này khác nhau, nhưng policy có thể cho
cùng hành vi ở các state thực sự đạt tới sau reset. Điều đó không chứng minh hai
bảng tương đương trên mọi trạng thái hoặc môi trường.

**Hình F01. REF: reward thô và moving average100episode.**

{{I.F01}}

X là episode train, Y là reward cả episode chia20bước; đen liền là RL, xám đứt là
rule. Panel dưới làm mượt100episode; chỉ có một seed, không có dải sai số giữa
seed. RL tăng từ{{N.train3.REF.rl_first100_mean_per_step}} ở100episode đầu lên
{{N.train3.REF.rl_last100_mean_per_step}} ở100episode cuối. Reward vẫn dao động;
nhu cầu/doanh số ngẫu nhiên và policy đang học cùng ảnh hưởng đường vẽ. Làm mượt
không chứng minh hội tụ hoặc ưu thế ngoài mẫu. Nguồn: D3, run REF42.

**Hình F02. CONTROLLED seed11: cùng cách đọc nhưng là run khác.**

{{I.F02}}

X là episode train, Y là profit/bước; đen RL, xám đứt rule. Panel dưới là MA100;
chỉ một seed11, không có dải sai số giữa seed và không phải các learner độc lập.
RL đầu/cuối là{{N.train3.CONTROLLED.rl_first100_mean_per_step}}/
{{N.train3.CONTROLLED.rl_last100_mean_per_step}}, rule là
{{N.train3.CONTROLLED.rule_first100_mean_per_step}}/
{{N.train3.CONTROLLED.rule_last100_mean_per_step}}. Rule không học vẫn thay reward
do learner và thị trường đổi. Không lấy chênh giữa F01–F02 để xếp hạng cách quản
lý RNG vì cả seed cũng khác. Nguồn: D3, run CONTROLLED11.

**Hình F03. Tám Q-value của mỗi baseline.**

{{I.F03}}

Hàng là bốn state nhu cầu/action trước của đối thủ; cột là hai action. Ô tối hơn
có Q lớn hơn, số trong ô là Q chịu chiết khấu, không phải profit/bước. Không lấy
trung bình hai track hoặc vẽ error bar. B02 cho thấy REF chọn1ởstate(0,1)/(1,1),
trong khi CONTROLLED chọn0ởcảbốnstate. State ít hoặc không gặp trong policy greedy
có thể không ảnh hưởng score của kịch bản hiện tại. Nguồn: D3, Q/policy cuối.

**Hình F04. Action count lúc train.**

{{I.F04}}

X là từng cặp agent/action; Y là tổng số lần chọn trên100.000bước/run. Cột tối giữ
giá, cột sáng giảm giá; không có std vì mỗi track chỉ một seed. REF learner giảm
{{N.train3.REF.rl_action1}}lần, CONTROLLED giảm{{N.train3.CONTROLLED.rl_action1}}lần.
Đây là hành vi khi còn exploration, không phải tỷ lệ epsilon hoặc tần suất của
policy cuối. Giảm giá nhiều hơn không tự mang lợi nhuận cao hơn. Nguồn: D3, action_counts.

### 5.2. C–D: learning rate và exploration

**Bảng B03. Ba learning rate, các tham số khác giữ nguyên.** Các cột mean±std
đều tính qua5seed nhưng train và final đo hai giai đoạn khác nhau [D4,D5].

{{T.alpha}}

**Hình F05. Reward curves khi đổi alpha.**

{{I.F05}}

Mỗi panel ứng với α0,01/0,10/0,50; Xepisode, Yprofit/bước. Đen RL, xám đứt rule;
MA100 riêng từng seed trước rồi mean±sample std qua5seed. Cuối cửa sổ, RL lần lượt
{{N.train4.alpha_low.rl_last_window_mean}},{{N.train4.baseline.rl_last_window_mean}},
{{N.train4.alpha_high.rl_last_window_mean}}. Alpha lớn cập nhật mạnh nhưng không
tạo final mean cao hơn trong mẫu này. Vùng mờ giữa seed khác với nhiễu từng bước;
không dùng overlap của dải để làm kiểm định. Nguồn: D4, curves_mean_std.

**Bảng B04. Ba lịch exploration với alpha giữ0,10.**

{{T.exploration}}

**Hình F06. Train curves của ba lịch epsilon.**

{{I.F06}}

X là episode, Y là profit/bước; đen RL, xám đứt rule. MA100 riêng từng seed rồi
mean/std qua5seed như F05; chỉ thay lịch khám phá. RL ở cửa sổ cuối của
epsilon0,05, baseline giảm, epsilon0,30 lần lượt
{{N.train4.epsilon_low_fixed.rl_last_window_mean}},
{{N.train4.baseline.rl_last_window_mean}},
{{N.train4.epsilon_high_fixed.rl_last_window_mean}}. Khám phá cao có thể làm reward
train thấp vì tiếp tục thử action, nhưng không kết luận chỉ từ train rằng policy
cuối kém hơn. Nguồn: D4.

**Hình F07. Lịch epsilon định trước.**

{{I.F07}}

Xepisode, Yxác suất khám phá, không có đơn vị reward. Đường đen giảm0,20→0,02;
hai đường còn lại giữ0,05/0,30. Đây là cấu hình chung cho cả5seed, không phải số đo
ngẫu nhiên nên không có dải std. Epsilon chỉ là xác suất chọn action ngẫu nhiên;
tỷ lệ giảm giá còn phụ thuộc action được chọn khi khám phá và policy khi khai thác.
Nguồn: D2,D4, epsilon_schedules.

**Hình F08. Mean reward toàn giai đoạn train.**

{{I.F08}}

Hai panel tách RL và rule; Xcấu hình, Ymeanprofit/bước trên100.000bước/run. Cột là
mean5run, whisker là sample std của5mean/run. Baseline RL
{{N.train4.baseline.rl_train_mean}}±{{N.train4.baseline.rl_train_std}}; alpha0,01
{{N.train4.alpha_low.rl_train_mean}}±{{N.train4.alpha_low.rl_train_std}}. Dải của
alpha0,01 lớn hơn nhiều giữa seed; không bỏ seed bất lợi. Đó là train score, chưa
phải chất lượng cuối đo trước cùng opponent/tape. Nguồn: D4.

### 5.3. E: đánh giá policy công bằng

**Bảng B05. Final của năm cấu hình core.** Rule cùng trận có thể phản ứng với
lịch sử learner; policy rule đối chứng được đo trước cùng fixed rule/tape [D5].

{{T.core_final}}

Mean đối chứng Rule-vs-rule là{{N.rule_control_mean}}. Baseline Q lời hơn đối thủ
rule trong cùng cuộc đối đầu {{N.final5.baseline.within_match_delta_mean}}/bước,
nhưng chênh policy Q trừ policy rule đối chứng là
{{N.final5.baseline.delta_vs_rule_policy_mean}}/bước. Hai dấu này trả lời hai câu
hỏi khác nhau, không phải lỗi tính toán.

**Hình F09. Profit của Q cuối trước fixed rule.**

{{I.F09}}

Xnămcấu hình,Yprofit/bước; cột mean, whiskerstd qua5training seed sau gộp vai.
Đường đứt là mean Rule-vs-rule qua5scenario panel, không phải rule đã train. Baseline
{{N.final5.baseline.target_mean}} cao nhất trong năm mean quan sát, alpha0,50 là
{{N.final5.alpha_high.target_mean}}; không từ đó chọn lại cấu hình hoặc khẳng định
ưu thế thống kê/phổ quát. Nguồn: D5, config_summary.

**Hình F10. Chênh policy và lợi thế trong trận.**

{{I.F10}}

Hai panel cùng Xcấu hình,Ychênhprofit/bước; chấm mean, whisker sample std qua5delta
seed, đường0 là không chênh. **Panel trái** là Q cấu hình trừ Q baseline cùng seed/tape;
**panel phải** là Q trừ rule trong chính trận đó. Alpha0,50 có delta so baseline
{{N.final5.alpha_high.paired_delta_baseline_mean}}, nhưng delta trong trận
{{N.final5.alpha_high.within_match_delta_mean}}. Không dùng panel phải để tuyên bố
Q tốt hơn policy rule trước cùng opponent. Nguồn: D5, paired_comparison.

**Hình F11. Train và final không đo cùng một đại lượng.**

{{I.F11}}

Xcấu hình,Yprofit/bước; cột sáng là toàn quá trình học, cột tối là policy cuối
đóng băng trên scenario riêng, whisker đều giữa5seed. Alpha0,01 train mean
{{N.train4.alpha_low.rl_train_mean}} còn finalmean{{N.final5.alpha_low.target_mean}}.
Chênh lệch gồm cả policy thay đổi, exploration và tập tình huống; không quy toàn
bộ cho việc tắt epsilon hoặc gọi score tăng là hội tụ. Nguồn: D4,D5.

**Hình F12. Tỷ lệ giảm giá đo từ action.**

{{I.F12}}

Xcấu hình,Ytỷ lệ giảm giá(%); cột sáng train100.000bước/run, tối final20.000bước/seed
gộp hai vai. Whisker là sample std giữa5seed, đơn vị điểm%. Final baseline
{{N.final5.baseline.discount_percent}}%, alpha0,50 {{N.final5.alpha_high.discount_percent}}%.
Tỷ lệ không bằng epsilon. Whisker mean±std có thể xuống dưới0khi độ phân tán lớn;
từng tỷ lệ quan sát vẫn0–100%, whisker không phải khoảng xác suất/CI. Nguồn: D4,D5.

**Bảng B06. Từng seed baseline final và REF native riêng.** Cột steps ghi tổng
bước đã gộp vai, không phải budget của một vai. REF_NATIVE chỉ role0 [D5].

{{T.baseline_final}}

### 5.4. Hai learner và sửa động lực nhu cầu

**Bảng B07. Hai Q-learning cùng học: đo checkpoint trước fixed rule.** Hai learner
trong một pair phụ thuộc nhau; gộp hai vai, rồi hai learner trong pair, sau đó mới
lấy mean/std qua năm pair seed. Các checkpoint là các phép đo lặp của cùng quá
trình học, không phải bốn nhóm độc lập [D6].

{{T.q8}}

**Hình F13. Dữ liệu vàng và kernel dùng hiệu chỉnh kịch bản.**

{{I.F13}}

Trái: X là tháng, Y là USD/troy ounce; đường đen là {{N.gold.months}} giá tháng
trong prefix TRAIN, 01/1960–08/2006. Phải: hàng là regime hiện tại, cột là regime
tháng sau, số trong ô là xác suất sau cộng Laplace1. Regime1 là giá tăng; regime0
gồm giảm hoặc giữ nguyên. P00={{N.gold.p00}}, P11={{N.gold.p11}}, khác kernel
persistent giữ chế độ với xác suất0,9. Đây là hướng biến động **giá**, không phải
nhu cầu vàng thực đo; không diễn giải thành quan hệ nhân quả hay backtest đầu tư.
Nguồn: S7,D6, Gold TRAIN prefix/kernel.

**Bảng B08. Count chuyển regime và kernel sau hiệu chỉnh.** Chỉ dùng các tháng
liền kề; không impute hoặc nối qua tháng thiếu. Prefix này có{{N.gold.months}}giá hợp lệ,
{{N.gold.regimes}}regime và{{N.gold.transitions}}transition. Nhu cầu mô phỏng vẫn khởi tạo cân bằng0/1 [D6].

{{T.gold_kernel}}

**Hình F14. Reward khi hai learner cùng cập nhật.**

{{I.F14}}

Hai panel tách learner0/1; X là episode train, Y là profit/bước. Đường đen là mean
của MA100 riêng từng seed; dải xám là ±sample std qua năm pair seed. Hai đường
vẫn dao động; mean train của learner0/1 là{{N.pairtrain.agent0.mean}}/
{{N.pairtrain.agent1.mean}}, không tăng đều đến cuối. Đây là quá trình cả hai
policy đang đổi; vùng mờ còn chứa khác biệt kinh nghiệm giữa seed. Không từ đó
quy riêng biến động cho non-stationarity hoặc kết luận hội tụ. Nguồn: D6, pair_train_curves.

**Hình F15. Checkpoint return và policy drift.**

{{I.F15}}

Trái: X là checkpoint, Y là profit/bước khi Q đóng băng trước fixed rule; chấm
mean, whiskerstd sau gộp vai/learner trong pair, n5 pair seed. Mean ở1.000episode
là{{N.q8.e1000.target_mean}}, ở5.000 là{{N.q8.e5000.target_mean}}. Phải: X là cuối
mỗi khoảng100episode, Y là số state đổi tập greedy trên bốn state, lấy mean qua
10learner thuộc5pair. Có{{N.drift.changed}}state-change trên{{N.drift.intervals}}learner-interval; không phải
số lần đổi action trong timestep. Drift ở state ít gặp có thể không đổi return;
không chọn checkpoint1.000 làm kết quả cuối chỉ vì mean cao hơn. Nguồn: D6.

**Bảng B09. Khi chỉ thay kernel: policy IID cũ và policy train lại.** Các policy
được đo trước cùng fixed rule và tapes trong từng kernel; n5 seed/panel [D6].

{{T.variants}}

**Hình F16. Robustness dưới persistent và Gold.**

{{I.F16}}

Mỗi panel là một kernel; X gồm Q IID cũ, Q train lại, rule và no-discount; Y là
profit/bước. Cột mean, whiskerstd sau gộp hai vai. Delta train lại trừ Q IID cũ
là{{N.variant_delta.persistent.mean}}±{{N.variant_delta.persistent.std}} ởpersistent,
{{N.variant_delta.gold.mean}}±{{N.variant_delta.gold.std}} ởGold. Rule-vs-rule và
no-discount trùng hành vi giữ giá từ lịch sử reset0, nên không coi hai cột đó là
hai chuẩn hành vi độc lập. Không so raw profit xuyên kernel như cùng phân phối.
Nguồn: D6, variant_seed/variant_summary/variant_deltas.

### 5.5. State bổ sung memory/time

**Bảng B10. Ba policy trên ba kernel.** Baseline ở đây đã train trên **cùng kernel**
với agent mới. Kết quả baseline/rule được reuse từ D5/D6; chỉ30claim của augmented
là đánh giá mới. Gộp hai vai trước, rồi mean/std qua năm seed [D7].

{{T.improved}}

**Hình F17. Train curves khi thay state.**

{{I.F17}}

Ba panel là IID/persistent/Gold; X là episode, Y là profit/bước. Đen liền là state
memory/time, xám đứt là state cũ train cùng kernel; mỗi đường là mean MA100 qua
năm seed, dải là sample std tương ứng. Ở cả ba panel, đường memory/time quan sát
thấp hơn phần lớn quá trình. Train reward còn exploration và Q thay đổi; không
thay nó cho final hoặc suy ra nguyên nhân chỉ từ hình. Nguồn: D7, train_curves.

**Hình F18. Final profit: state mới chưa vượt hai đối chứng.**

{{I.F18}}

X là ba policy, Y là profit/bước; cột mean và whisker sample std, n5 sau gộp vai.
IID memory/time đạt{{N.improved.iid.augmented.profit_mean}} so với baseline
{{N.improved.iid.baseline.profit_mean}}; Gold lần lượt
{{N.improved.gold.augmented.profit_mean}}/{{N.improved.gold.baseline.profit_mean}}.
Kết quả có std nhỏ hơn không đủ để gọi robust hơn nếu mean thấp hơn. Các panel
khác phân phối nên so trong từng kernel là chính. Nguồn: D7, policy_summary.

**Bảng B11. Delta ghép cặp của memory/time.**

{{T.improved_delta}}

**Hình F19. Chênh lệch theo seed, cùng opponent/tapes.**

{{I.F19}}

X là kernel, Y là profit augmented trừ đối chứng/bước. Tròn đen trừ baseline,
vuông xám trừ rule; đường đứt0 là không chênh. Điểm là mean, whisker là sample
std của năm delta seed. Mean trừ baseline âm ở cả ba kernel: B11 ghi rõ mức chênh.
Whisker qua0 không phải kiểm định; không loại seed bất lợi hoặc tăng budget sau
khi xem score để đảo kết luận. Nguồn: D7, paired_deltas/delta_summary.

**Hình F20. Visitation và chi phí của bảng lớn hơn.**

{{I.F20}}

X là kernel. Trái: Y là phần trăm ô state–action đã được thăm trên tổng ô lý thuyết;
phải: Y là CPUgiây/100.000train market step. Cột đậm memory/time, nhạt baseline;
panel phải có whiskerstd qua5seed. Agent mới thăm{{N.coverage.iid}}%/{{N.coverage.persistent}}%/
{{N.coverage.gold}}% của320ô trênIID/persistent/Gold, baseline
thăm100% của8ô; một số fullstate không đạt được từ reset/horizon nên phần chưa
thăm không tự là lỗi. Qpayload float64 tăng64→2.560byte, không phải peakRAM. CPU
loop không gồm checkpointI/O và không phải benchmark hệ thống. Nguồn: D7, cost_coverage.

**Bảng B12. Kỳ vọng phân tích trên simulator đã biết, không phải score sampled.**
Oracle biết transition/reward và đối thủ rule; learner không nhận Q/action tối ưu
làm nhãn train. Cột γ1 có cùng đơn vị profit/bước với metric chính [D7].
Mỗi learner có kỳ vọng riêng; cột memory/time lấy mean qua5policy đã train.
Oracle là một giá trị theo mô hình cho mỗi kernel, không phải năm lần train.

{{T.oracle}}

Rule từ reset có gap kỳ vọng0 trong simulator này. Score500episode có thể hơi
cao hơn kỳ vọng oracle vì nhiễu: rule IID quan sát{{N.rule_control_mean}} so với
kỳ vọng{{N.oracle.iid.optimal_expected_profit_per_step_gamma1}}. Không sửa score
để ép nằm dưới bound. Giá trị γ0,9 trong CSV là discounted total riêng, không
trộn với profit/bước không chiết khấu hoặc gọi oracle là learner model-free.

## 6. Trả lời mười câu hỏi thí nghiệm

### 6.1. Câu 1 — Mô hình tác tử và môi trường

Hai tác tử là hai shop, dùng policy Q-learning và rule trong baseline. Môi trường
chung gồm nhu cầu, lịch sử action, cơ chế xác suất mua và reward. State local cũ
có bốn khả năng từ nhu cầu0/1 và action trước của đối thủ0/1; action giữ/giảm giá;
reward là profit. Sau action đồng thời, môi trường sinh sales, lưu action, lấy
nhu cầu mới và trả state/reward tiếp theo. E04 thể hiện đúng thứ tự này.

Theo PEAS, tiêu chí thành công là profit; môi trường là thị trường mô phỏng; bộ
chấp hành là quyết định giữ/giảm giá; thông tin quan sát là nhu cầu/lịch sử. Hai
policy cùng tác động đến xác suất mua và lịch sử của nhau nên đây là MAS qua môi
trường chung, dù không gửi thông điệp [S1, trang PDF3–7; S6, trang PDF3–5].

### 6.2. Câu 2 — Quyết định học từ kinh nghiệm và theo luật

| Khía cạnh | Rule-based | Q-learning |
|---|---|---|
| Ra quyết định | Theo nhánh điều kiện do người thiết kế viết | Theo Q đã học và epsilon khi train |
| Kinh nghiệm | Không tự sửa rule sau reward | Reward dùng sửa giá trị action |
| Thích nghi | Cần đổi rule nếu giả định thay đổi | Có thể học lại nhưng không bảo đảm tốt hơn |
| Chi phí | Không train; điều kiện đơn giản | Cần tương tác, lưu Q và kiểm tra nhiều seed |
| Giải thích | Chỉ ra nhánh luật đã dùng | Đọc state/action/Q và kết quả kiểm chứng |

Rule phù hợp khi ràng buộc rõ, cần quyết định nhất quán: ví dụ lọc nhà theo ngân
sách hoặc kiểm hồ sơ đặt lịch tư vấn tiểu đường có đủ trường thông tin. Ví dụ này
không đề xuất chẩn đoán/điều trị từ một nhãn dữ liệu. RL đáng cân nhắc khi quyết
định lặp lại có reward dài hạn và có môi trường thử nghiệm phù hợp, chẳng hạn
chính sách khuyến mãi trong simulator được kiểm chứng trước khi áp dụng.

Trong mẫu đang xét, rule control có mean{{N.rule_control_mean}}, cao hơn baseline
Q{{N.final5.baseline.target_mean}}; vì vậy khả năng học không đồng nghĩa ưu thế
mặc định. Kết quả này chỉ áp dụng simulator, budget và bộ seed hiện tại (B05,F09).

### 6.3. Câu 3 — Ý nghĩa cập nhật Q và phép tính cụ thể

Công thức cần dùng là:

**Q mới = Q cũ + α × [r + γ × max Q ở state kế − Q cũ].**

Q cũ là đánh giá đang có cho action vừa chọn. r là reward vừa nhận; maxQ ở state
kế là ước lượng tốt nhất cho bước tiếp theo; γ làm giảm trọng số lợi ích xa hơn.
Phần trong ngoặc là chênh giữa target mới và đánh giá cũ; α quyết định sửa bao
nhiêu phần của chênh đó. Ở terminal, target chỉ bằng r vì episode đã kết thúc.

Với số **giả định đề cho**, Q cũ4, α0,1, r6, γ0,9, maxQ kế5:

1. Giá trị tương lai có chiết khấu:0,9×5=4,5.
2. Target:6+4,5=10,5.
3. Chênh target so Q cũ:10,5−4=6,5.
4. Phần cập nhật:0,1×6,5=0,65.
5. Q mới:4+0,65=**4,65**.

Q tăng từ4 lên4,65 vì tín hiệu mới tốt hơn đánh giá cũ, nhưng không nhảy thẳng lên
10,5 do alpha chỉ0,1. Đây là phép tính giả định, không phải một reward hoặc Q đo
từ run. E03 và unit test kiểm đúng phép tính, đồng thời kiểm terminal. Công thức
theo [S1, trang PDF6,10] và code; survey [S4] được dùng cho phần nền RL.

### 6.4. Câu 4 — Khám phá và khai thác

Epsilon-greedy chọn action ngẫu nhiên với xác suất epsilon; ngoài nhánh đó chọn Q
lớn nhất. Khám phá giúp thử action chưa biết rõ; khai thác dùng kinh nghiệm hiện
tại để thu reward. Khám phá quá nhiều có thể tiếp tục chọn action kém; dừng quá sớm
có thể giữ một đánh giá lệch vì ít được thử lại. Đây là đánh đổi, không phải quy
tắc “epsilon càng cao càng tốt”.

B04,F06–F07 so lịch giảm với epsilon0,05 và0,30 cố định. Mean train tương ứng
{{N.train4.baseline.rl_train_mean}},{{N.train4.epsilon_low_fixed.rl_train_mean}},
{{N.train4.epsilon_high_fixed.rl_train_mean}}; final tương ứng
{{N.final5.baseline.target_mean}},{{N.final5.epsilon_low_fixed.target_mean}},
{{N.final5.epsilon_high_fixed.target_mean}}. Các số cuối đều đo với exploration
tắt, không phải vẫn giữ epsilon train. Lịch giảm có mean quan sát cao hơn trong
mẫu này, nhưng độ phân tán seed và n nhỏ hạn chế khẳng định tổng quát. E02 cho
thấy random tie vẫn khác exploration.

### 6.5. Câu 5 — Reward và mục tiêu kinh doanh

Không giảm giá: giá10−chi phí5=**5** lợi nhuận/món. Giảm20%: giá mới10×0,8=8,
lợi nhuận8−5=**3**/món. Do đó sales tăng chưa chắc profit tổng tăng. Reward trong
bài ưu tiên profit, không đơn thuần số lượng bán [S1, trang PDF4–5,10].

Nếu reward chỉ đếm sales, learner có thể thích action tăng xác suất mua dù margin
thấp. Nếu thêm tồn kho, phí khuyến mãi hoặc mục tiêu duy trì khách, hành vi tối ưu
cũng có thể khác. Đây là đề xuất thiết kế, không phải các reward đã được triển
khai trong số đo hiện tại. F04/F12 phản ánh action rate thực đo, không chứng minh
mối quan hệ nhân quả giữa giảm giá và profit ngoài mô hình.

### 6.6. Câu 6 — Tính reward trung bình và giới hạn một run

**Reward trung bình mỗi bước = tổng reward / tổng số bước.** B01 có ví dụ REF
train:3.345.548/100.000={{N.train3.REF.rl_mean_reward_per_step}} cho RL và
3.283.930/100.000={{N.train3.REF.rule_mean_reward_per_step}} cho rule. Đây là train
score, không phải kết quả policy cuối.

Với final native REF, tổng Q là{{N.baseline.s42.target_total_int}}, rule
{{N.baseline.s42.opponent_total_int}}, mỗi shop{{N.baseline.s42.steps_int}}bước;
mean tương ứng{{N.baseline.s42.target_mean}}/{{N.baseline.s42.opponent_mean}}.
Native chỉ role0 và RNG gốc, không đưa vào nhóm CONTROLLED n5 (B06).

Baseline CONTROLLED sau gộp vai có Q mean{{N.final5.baseline.target_mean}}±
{{N.final5.baseline.target_std}}, rule trong cùng trận
{{N.final5.baseline.opponent_mean}}±{{N.final5.baseline.opponent_std}}. Khi đối chứng
policy rule trước cùng fixed opponent, mean lại là{{N.rule_control_mean}}. Vì
đối thủ phản ứng với lịch sử, hai phép so sánh không được dùng thay nhau (B05,F10).

Một run chỉ quan sát một chuỗi kinh nghiệm. Nhu cầu, sales, exploration và phá
đồng hạng có thể làm Q cuối khác nhau giữa seed; B06 cho thấy các mean khác nhau
thật. Năm seed và sample std hữu ích hơn một run, nhưng không chứng minh ưu thế
ở thị trường thật hoặc coi mọi timestep là mẫu độc lập.

### 6.7. Câu 7 — Learning rate và độ ổn định

Alpha nhỏ chỉ sửa Q một phần nhỏ sau reward mới; alpha lớn phản ứng mạnh hơn với
quan sát gần nhất. Cập nhật mạnh có thể phản ứng nhanh nhưng cũng nhạy với nhiễu;
alpha nhỏ không tự bảo đảm policy tốt nếu budget hữu hạn và kinh nghiệm khác nhau.

B03,F05 đo α0,01/0,10/0,50 với các phần khác giữ nguyên. Final mean±std lần lượt
{{N.final5.alpha_low.target_mean}}±{{N.final5.alpha_low.target_std}},
{{N.final5.baseline.target_mean}}±{{N.final5.baseline.target_std}},
{{N.final5.alpha_high.target_mean}}±{{N.final5.alpha_high.target_std}}. Alpha0,50
có độ phân tán final lớn nhất trong ba nhóm, trong khi std của mean **train** của
nó không lớn như vậy. Hai đại lượng đo khác nhau, nên không dùng curve train
ổn định hơn để kết luận policy cuối ổn định hơn. Kết luận giới hạn ở cấu hình,
budget và seed đã đo; không chọn lại alpha sau final.

### 6.8. Câu 8 — Tương tác và non-stationarity

Action hiện tại của đối thủ ảnh hưởng xác suất mua của shop mình; action trước
ảnh hưởng observation và phản ứng của rule ở bước sau. Khi hai Q-learning cùng
sửa policy, learner gặp một “đối thủ đang thay đổi”: cùng local observation/action
có thể cho kết quả khác do lựa chọn của đối thủ khác, ngoài nhiễu sales vốn có.
Điều này làm việc học khó hơn so với giả định đối thủ cố định.

Một thay đổi thực nghiệm là đóng băng checkpoint rồi đo trước cùng fixed opponent
và tapes. Bài đã thực hiện năm pair seed, hai learner riêng Q/RNG và bốn mốc0/
1.000/2.500/5.000. B07,F15 có mean{{N.q8.e1000.target_mean}} ởmốc1.000 rồi
{{N.q8.e5000.target_mean}} ởmốc5.000. Không có xu hướng final return tăng đều.
Policy drift và reward dao động chưa tách được riêng tác động nhân quả của đối
thủ đang học, vì alpha, observation và nhiễu vẫn tồn tại. Không chọn mốc tốt nhất
để thay checkpoint cuối hoặc xem10learner phụ thuộc là10replicate độc lập.

### 6.9. Câu 9 — Hạn chế và sửa môi trường thật sự

Ít nhất năm hạn chế là: conversion chỉ giả định minh họa; nhu cầu IID quá đơn giản;
state cũ thiếu lịch sử của mình/thời gian còn lại; không có inventory hoặc dị biệt
khách; hai shop không chia một lượng sales độc quyền. Gold bổ trợ vẫn là proxy
từ hướng giá, không phải dữ liệu cầu đo được. Các giả định này giới hạn khả năng
suy rộng, kể cả khi mean/std đã được tính đúng.

Sửa đổi đã triển khai là dùng demand Markov: persistent giữ chế độ với xác suất0,9,
hoặc kernel hiệu chỉnh từ TRAIN Gold. Các phần giá/reward/action/rule/budget giữ
nguyên. E07 tạo các MarketConfig tương ứng; TrainSession cũ dùng đúng kernel đó,
không sửa thuật toán baseline để tạo kết quả thắng:

{{C.E07}}

Chỉ dùng{{N.gold.months}}giá tháng đến08/2006 để fit kernel (B08,F13). Trên mỗi
kernel mới, đo cả Q IID cũ đóng băng và Q train lại trước cùng fixed rule/tape.
Paired delta retrain−baseline ởpersistent là{{N.variant_delta.persistent.mean}},
ởGold{{N.variant_delta.gold.mean}} (B09,F16). Trong budget này, train lại không
cải thiện mean. Không từ đó kết luận retrain luôn kém: từng seed khác nhau, chỉ
hai kịch bản sửa môi trường và n5 nhỏ. Sửa kernel giúp kiểm độ bền trước thay đổi
nhu cầu giả lập, chưa giải quyết toàn bộ các hạn chế trên.

### 6.10. Câu 10 — Thiết kế agent đầy đủ hơn và kiểm chứng

Đề xuất thêm own_previous và remaining_steps vào state, giữ action giữ/giảm giá
và reward profit, dùng Q-learning320giá trị. Lý do là hai lịch sử cùng observation
cũ có thể làm rule hiện tại chọn khác nhau; thời gian còn lại cũng quyết định có
nên tính giá trị tương lai hay không. E08 cho thấy thời gian phải giảm đúng1 và
terminal chỉ nhận reward hiện tại:

{{C.E08}}

Để kiểm robust, train trên ba kernel với cùng5seed và5.000×20budget, sau đó đo Q
đóng băng500episode/vai trước cùng fixed rule/tapes. So với baseline **đã train
trên cùng kernel** và rule; đọc paired return, std giữa seed, action rate và cost.
Các đối chứng cũ được reuse output, không forward lại để thay điểm (B10–B12,F17–F20).

Trong thực nghiệm, augmented−baseline mean là{{N.delta.iid.delta_vs_baseline_mean}}
trênIID,{{N.delta.persistent.delta_vs_baseline_mean}} trênpersistent và
{{N.delta.gold.delta_vs_baseline_mean}} trênGold. Mean đều thấp hơn đối chứng nên
chưa đạt mục tiêu cải thiện robust. State biểu diễn đầy đủ hơn là một lý do thiết
kế, không phải bảo đảm học tốt hơn dưới budget cố định. Bảng lớn hơn/cùng số tương
tác là một giả thuyết cần khảo sát thêm, chưa được chứng minh là nguyên nhân duy nhất.

Oracle tính lùi bằng simulator đã biết chỉ dùng đối chiếu kỳ vọng (B12). Nó không
cấp action/Q tối ưu làm nhãn hoặc khởi tạo learner; không gọi là tác tử model-free
đã học. Không dùng kết quả âm để âm thầm tăng budget hoặc tune lại. Một nghiên cứu
tiếp theo có thể đăng ký trước budget/ablation mới, rồi thu bộ đánh giá mới để
kiểm giả thuyết, thay vì sử dụng lại các score cuối hiện tại.

## 7. Thảo luận, hạn chế và hướng cải tiến

Kết quả chính là sự khác nhau giữa **có khả năng học** và **đã học được policy tốt**.
Trong core, baseline có mean final cao nhất trong năm cấu hình quan sát, nhưng
vẫn thấp hơn policy rule control. Trong phần mở rộng, retrain hoặc state nhiều
thông tin hơn cũng chưa bảo đảm profit cao hơn. Những kết quả không thuận kỳ vọng
được giữ đủ, giúp kiểm giả định thay vì chỉ chọn hình đẹp.

Một nguyên nhân khiến việc diễn giải dễ nhầm là reward của rule phụ thuộc policy
learner trong cùng trận. Q có thể lời hơn shop rule bên cạnh mà vẫn kém policy
rule khi cùng được đặt trước một fixed rule. Mặt khác, hai policy có Q khác ở
state không đạt tới có thể cùng score trên kịch bản reset hiện tại. Cần đọc cả
visitation và action thực tế, không chỉ argmax toàn bảng hoặc so một mean đơn lẻ.

Các dải và whisker đang mô tả sample std qua năm seed/panel, không phải CI. Các
checkpoint của cùng learner và hai learner cùng pair còn phụ thuộc nhau. Khi
không giữ đúng mẫu số này, báo cáo dễ phóng đại độ chắc chắn bằng cách coi hàng
nghìn episode/step là hàng nghìn learner độc lập. Bài không đưa ra kiểm định ý
nghĩa thống kê hoặc kết luận kinh doanh từ mức chênh nhỏ.

Gold được ưu tiên vì phù hợp câu hỏi thay đổi động lực theo thời gian, nhưng chỉ
chuyển **hướng giá lịch sử** thành một kernel nhu cầu giả lập. Không có bằng chứng
rằng giá gây cầu, dữ liệu không phải thời gian thực và vintage có thể sửa hồi tố.
Ngược lại, bảng tiểu đường hoặc giá bán nhà lịch sử không có chuỗi action–reward
do can thiệp, nên không được gán thành môi trường RL điều trị/giao dịch chỉ để
đủ miền dữ liệu. Các ví dụ tiểu đường/nhà trong câu2 chỉ minh họa lựa chọn policy.

Hướng tiếp theo đáng kiểm là bổ sung inventory/khách hàng, kiểm các trạng thái
reachable rõ hơn, khảo sát budget học lớn hơn cho bảng state lớn và đối thủ khác.
Mỗi hướng phải thay một yếu tố có kiểm soát, giữ baseline và định trước đánh giá.
Các đề xuất này chưa có số đo trong bài. Không xem oracle tối ưu theo simulator
là chứng minh policy nào sẽ tối ưu khi các giả định thị trường không còn đúng.

Về tái lập, full source, raw reward, checkpoint/RNG, Q/policy, saved evaluation,
CSV, figure notes và manifests đi kèm. Trích code E01–E08 có vị trí và hash nguồn;
hash đầy đủ nằm trong chỉ mục code. Các bảng được dựng từ saved artifact có hash,
không chép expected results. Bản Python thầy, raw dữ liệu và kết quả các bài cũ
không được sửa hoặc chạy lại khi biên soạn báo cáo này.

## 8. Kết luận

Bài đã mô hình hóa hai shop tương tác, triển khai rule và Q-learning, chạy các
thí nghiệm A–E, lặp nhiều seed, đánh giá Q đóng băng và khảo sát hai phần mở rộng.
Kết quả thực cho thấy learner không luôn vượt rule, train reward không thay thế
final return và việc thêm state hoặc train lại không tự bảo đảm cải thiện.

Giá trị của bài nằm ở phép so sánh có thể truy ngược: giữ nguyên reward/đối chứng,
công khai seed và mẫu số, tách các nguồn ngẫu nhiên, báo đủ kết quả bất lợi và
giải thích đúng điều mỗi bảng/hình đo được. Các kết luận giới hạn trong simulator,
budget và kịch bản hiện tại; chưa chứng minh hiệu quả ở hệ thống kinh doanh thực.

## 9. Tài liệu tham khảo và nguồn số liệu

[S1] Tài liệu giảng dạy được cung cấp, *Intelligent System Development Laboratory
Experiment02: Reinforcement-Learning-Based Agents versus Rule-Based Agents*,
`assignment_Agent02_due_29.10.pdf`,13trang. Yêu cầu A–E: trang PDF8–9;10câu:10–11;
cấu trúc báo cáo/rubric:11–12. Bản gốc và hash tại sources/manifest.json.

[S2] Tài liệu giảng dạy được cung cấp, *AGENT02: Python Implementation —
Reinforcement-Learning-Based Agents and Rule-Based Agents*,
`agent02_complementary_code.pdf`,7trang, đặc biệt trang PDF4–7. Bản cung cấp là
companion hướng dẫn; code Python đầy đủ ở S3.

[S3] Mã tham chiếu thầy cung cấp, `agent02_code.tex` (nội dung Python),966dòng.
Bản byte-identical ở `code/agent02_experiment.py`; source hash trong
sources/manifest.json và evidence/phase01/input_lock.json.

[S4] Muddasar Naeem, Syed Tahir Hussain Rizvi và Antonio Coronato (2020), *A Gentle
Introduction to Reinforcement Learning and Its Application in Different Fields*,
IEEE Access. DOI:10.1109/ACCESS.2020.3038605. Bản PDF thầy cung cấp,25trang; dùng
phần nền RL. Công thức và phép tính Q trong bài đối chiếu với S1/code.

[S5] Khanh-Tung Tran, Dung Dao, Minh-Duong Nguyen, Quoc-Viet Pham, Barry O’Sullivan,
Hoang D. Nguyen (2025), *Multi-Agent Collaboration Mechanisms: A Survey of LLMs*,
arXiv:2501.06322v1, 35trang. Chỉ tham khảo khái niệm/kiểu tương tác, không triển khai
hệ LLM hoặc lấy kết quả survey làm kết quả thí nghiệm này.

[S6] Tài liệu giảng dạy được cung cấp, *Developing Multiagent Systems: A Practical
Tutorial with Python and PyTorch*, `slide_multiAgent_system_20.10.2026.pdf`,25trang.
Dùng phần agents/MAS/PEAS để đối chiếu; các bài MAS riêng trong slide không thuộc
phạm vi Agent02 đã xác nhận.

[S7] World Bank, *Commodity Price Data (The Pink Sheet), Historical Monthly Prices*.
Nguồn dataset: https://www.worldbank.org/en/research/commodity-markets . Snapshot
local `CMO-Historical-Data-Monthly.xlsx`; bài này chỉ dùng prefix TRAIN Gold
1960-01–2006-08. Provenance/cutoff/source/split/TRAIN IDs có hash trong
data/derived/gold_regime_kernel_v1.json, không tuyên bố dùng giá validation/TEST.

[D2] Protocol/code và phép tính kiểm thử Agent02, docs/protocol_v1.json,
docs/model_core_v1.md; khóa evidence/phase02/protocol_lock.json.

[D3] Baseline train/DEV/Q/policy, artifacts/runs/ref/baseline/s0042 và
artifacts/runs/controlled/iid/baseline/s0011; metrics phase03 và khóa
evidence/phase03/experiment_lock.json. DEV/smoke không gộp vào final.

[D4] Sweeps train25run, artifacts/metrics/phase04/ và artifacts/figures/phase04/;
khóa evidence/phase04/experiment_lock.json.

[D5] Final core/control/native, artifacts/evaluation/phase05/ và
artifacts/metrics/phase05/; khóa evidence/phase05/experiment_lock.json.

[D6] Two-learners/variant/Gold, artifacts/metrics/phase06/,
artifacts/evaluation/phase06/ và data/derived/gold_regime_kernel_v1.json;
khóa evidence/phase06/experiment_lock.json.

[D7] Memory/time và oracle tách biệt, artifacts/metrics/phase07/,
artifacts/evaluation/phase07/, code/market_oracle.py; khóa
evidence/phase07/experiment_lock.json. Chỉ mục reference ghi60claim được reuse,
không tính chúng thành forward mới.
