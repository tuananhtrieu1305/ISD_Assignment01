# AG02 phase 5 — đánh giá riêng và tổng hợp kết quả cuối

Ngày24/10/2026. Đã hoàn tất71/71 claim, mỗi claim đúng1 lần;35.500 dòng episode và
710.000 market step đánh giá. Không train thêm run, không thay hyperparameter,
không mở TEST bài V3. Kết quả không bị ép để Q-learning thắng rule.

## Thiết kế đã khóa trước đánh giá

Declaration `evidence/phase05/declaration.json`, SHA256
`5fd71f5c3bf70413c8bd456f79bb59ea75088a72149454cc5c3573ec871e8fa1`.
152 pretest/0skip PASS trước forward; evaluator/journal coverage97,02% đúng scope.
25 Q CONTROLLED ×2 vai =50 claim; mỗi Q500 episode/vai ×20 bước, cùng exogenous
tape theo seed giữa configs. Rule/no-discount ×5 scenario panel ×2 vai =20 claim.
REF42 native role0 theo hàm gốc =1 claim, giữ riêng khỏi n5 CONTROLLED.

Source/core cũ giữ nguyên. Q copy chỉ đọc, no learn, no exploration; phá đồng hạng
vẫn có RNG theo quy tắc đã đăng ký, không mặc định argmax luôn0. RNG train và file
checkpoint/Q không bị cập nhật; REF clone RNG policy từ checkpoint đã khóa.
Journal exclusive claim trước forward, saved result/CSV/receipt sau đó; không có
failed/partial scientific claim hoặc replay. Native wrapper đã kiểm parity trên
fixture nhỏ, không evaluate native final lần thứ hai để đối chiếu.

## Kết quả chính, trình bày ngắn và đúng ý nghĩa

Mean/sample std qua5 **training seed sau khi gộp hai vai**, đơn vị lợi nhuận giả lập/bước:

| Cấu hình | Final Q mean±std | Q−rule trong cùng trận | Q−Rule control cùng tape |
|---|---:|---:|---:|
| Baseline |34,02786±1,22178|+0,80818|−1,02449|
| Alpha0,01 |33,90382±2,60833|+0,44187|−1,14853|
| Alpha0,50 |32,06337±4,25085|+0,63457|−2,98898|
| Epsilon fixed0,05 |33,39952±2,64330|+0,84794|−1,65283|
| Epsilon fixed0,30 |32,87013±3,58062|+0,33861|−2,18222|

Đối chứng Rule-vs-rule và no-discount cùng mean35,05235/bước trên5 panel và hai vai.
Lịch sử ban đầu0 làm cả hai giữ giá mãi trong cặp đối chứng này, nên hai tên policy
không tạo hai hành vi độc lập trên trajectory đó. Không bịa rằng có hai benchmark
đối chứng khác nhau về hành vi. So Q-vs-rule trong cùng trận có thể dương vì rule
phản ứng với lịch sử giảm giá của learner; điều đó không có nghĩa Q-policy tốt hơn
rule-policy khi đặt cả hai trước cùng fixed opponent và cùng tình huống.

Baseline có mean quan sát cao nhất trong năm cấu hình, nhưng n5 nhỏ và khác biệt
seed lớn; không tuyên bố cấu hình thắng có ý nghĩa thống kê chỉ từ whisker.
Delta ghép seed so baseline: alpha0,01 −0,12404±3,39200; alpha0,50 −1,96449±5,13750;
fixed0,05 −0,62834±3,55259; fixed0,30 −1,15773±3,92963. Giữ mọi cấu hình/seed,
không chọn lại budget hoặc tune từ final. Đây vẫn chỉ là teaching simulator.

REF native seed42 riêng: Q35,12750, rule34,96850/bước, mỗi shop10.000 bước.
Nguồn RNG/environment gốc khác matched CONTROLLED, chỉ một seed/role0, không đem
làm replicate thứ sáu hoặc so chênh nhỏ này với mean n5 như một kiểm định.

## Sáu bảng và bốn hình đã giải thích

Sáu CSV ở `artifacts/metrics/phase05/`: baseline_reward6 dòng, q_policy104 state
rows của26Q, alpha_comparison3, exploration_comparison3, multi_seed25,
paired_comparison25. Q/policy giữ đủ trạng thái, kể cả state ít/không gặp khi greedy;
Q là giá trị chiết khấu ước lượng, không trực tiếp là profit/bước final.

4 PNG: final_profit, paired_and_match, train_vs_final, discount_rates. Đã xem từng
hình, font/nhãn đọc được, chữ đen và grayscale. Mỗi hình có notes theo yêu cầu
trục/đơn vị, nguồn, mean/std/n, quan sát số liệu, so sánh và giới hạn ở
`artifacts/figures/phase05/figure_notes.md`/JSON và bản thảo
`report/sections/phase05_final_evaluation.md`.

Ba điểm cần giải thích khi dùng hình:

- Hai panel paired_and_match hỏi hai câu khác nhau như bảng trên, không dùng lẫn.
- Train là cả quá trình Q đang đổi/còn epsilon; final là Q cuối cố định/tape mới.
  Reward final cao hơn train không tự chứng minh hội tụ hoặc chỉ do tắt epsilon.
- Tỷ lệ giảm giá final qua5 seed biến động lớn: baseline16,212%±22,199 điểm%;
  alpha0,01 12,876%±28,792; alpha0,50 30,186%±41,559; fixed0,05 21,160%±30,090;
  fixed0,30 19,824%±27,145. Whisker có thể xuống dưới0 do thể hiện độ phân tán,
  không phải tỷ lệ quan sát âm hoặc khoảng xác suất. Từng seed thực tế nằm0–100%.
  Tần suất action cũng không bằng epsilon vì exploration có thể chọn giữ giá,
  còn greedy có thể chủ động giảm giá. Giảm giá làm lãi/món từ5 còn3, không luôn có lợi.

## Nghiệm thu và giới hạn

157 test PASS/0skip; coverage94,32% trên `final_v1`, `journal_v1`, `aggregate_v1`,
không phải teacher, CLI/plots/auditor hay toàn project. Pretest frozen152 và final157
được lưu riêng. Test đầu có giả định sai rằng RNG luôn tiến khi greedy chọn một
action duy nhất; đã sửa fixture thành Q đồng hạng trước khi khóa evaluator. Không
thay thuật toán hoặc forward final để sửa test.

Auditor chỉ đọc saved journal, kiểm count1, đủ500 dòng/claim, Q hash, visits/action
counts, scenario/role identity, CSV↔JSON values, tái tính6 bảng và aggregate. Không
policy forward lại để làm bảng/QA. Khóa phase1–4, input teacher,7 asset tham chiếu
và Gold metadata được kiểm lại; không cài/sửa env hoặc tải dataset. Controller đã
COMPLETE/PID=null; không queue/kernel chờ nền.

Release: `evidence/phase05/experiment_lock.json`, `verification.json`; registry mới
`artifacts/manifests/phase05/evaluated_registry.json`. Registry trained3/4 giữ trạng
thái snapshot trước final; không sửa ngược lịch sử. Kết quả đã mở không được dùng
để tuning. Tiếp **`làm AG02 phase 6`** khi được yêu cầu: hai learner/robustness và Gold
theo protocol riêng, giữ nguyên bộ final phase5 này.
