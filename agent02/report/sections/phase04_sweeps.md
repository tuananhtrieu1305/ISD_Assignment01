# C–D: learning rate và exploration

Ma trận 5 cấu hình × 5 training seed, mỗi run 5.000 episode × 20 bước. CONTROLLED baseline seed11 tái dùng từ phase3. REF42 không thuộc nhóm n=5. Lý thuyết đủ dùng: α quyết định mức sửa Q sau reward mới; ε quyết định xác suất thử action ngẫu nhiên. Alpha sweep giữ lịch ε baseline; exploration sweep giữ α=0,10.

| Cấu hình | RL mean ± std/bước train | Rule mean ± std/bước train |
|---|---:|---:|
| Baseline: α=0,10; ε giảm | 33.76528 ± 0.09989 | 33.22514 ± 0.12848 |
| α=0,01; ε giảm | 30.91717 ± 3.91720 | 29.64954 ± 4.42718 |
| α=0,50; ε giảm | 31.97780 ± 0.12472 | 31.11284 ± 0.20670 |
| ε cố định 0,05; α=0,10 | 32.89187 ± 0.18749 | 32.17176 ± 0.27370 |
| ε cố định 0,30; α=0,10 | 30.92305 ± 0.09846 | 30.02129 ± 0.07806 |

Mẫu số: 100.000 market step/run, n=5 training seed, sample std ddof=1. Không gọi 125.000 episode là 125.000 learner độc lập. Ghép seed trong train giúp giữ comparable khởi tạo RNG/nhu cầu; sales/policy draw vẫn có thể khác khi hành động khác, không thay cho matched exogenous tapes ở final evaluation.


## Hình alpha_curves

Mỗi panel là một cấu hình. Trục x: episode 100–5.000; trục y: lợi nhuận giả lập/bước. Đường đen liền là RL, xám đứt là rule; mỗi seed được làm mượt bằng 100 episode trước, rồi lấy mean qua 5 seed (11/22/33/44/55). Vùng mờ là ±1 sample std giữa 5 đường đã làm mượt (ddof=1), không phải CI, không phải biến động từng timestep. α=0,01; ε giảm: RL cửa sổ đầu 30.0084, cuối 33.4916 ± 2.7860; Baseline: α=0,10; ε giảm: RL cửa sổ đầu 31.1301, cuối 34.2875 ± 0.2179; α=0,50; ε giảm: RL cửa sổ đầu 29.9442, cuối 31.8786 ± 0.7006. So sánh giữ cùng ngân sách 5.000×20, gamma, reward, kernel và bộ seed; chỉ đổi yếu tố đã nêu. Các cửa sổ kế tiếp chồng lấp nên không độc lập. Reward còn chịu exploration, đối thủ và nhiễu thị trường; không suy ra hội tụ/tối ưu hoặc thứ hạng final policy từ đường train. Rule không học vẫn đổi reward vì learner và tình huống đổi; phase5 mới đánh giá Q đóng băng.

Hình: `artifacts/figures/phase04/alpha_curves.png`.


## Hình exploration_curves

Mỗi panel là một cấu hình. Trục x: episode 100–5.000; trục y: lợi nhuận giả lập/bước. Đường đen liền là RL, xám đứt là rule; mỗi seed được làm mượt bằng 100 episode trước, rồi lấy mean qua 5 seed (11/22/33/44/55). Vùng mờ là ±1 sample std giữa 5 đường đã làm mượt (ddof=1), không phải CI, không phải biến động từng timestep. ε cố định 0,05; α=0,10: RL cửa sổ đầu 30.2900, cuối 32.5748 ± 0.5543; Baseline: α=0,10; ε giảm: RL cửa sổ đầu 31.1301, cuối 34.2875 ± 0.2179; ε cố định 0,30; α=0,10: RL cửa sổ đầu 30.8379, cuối 31.1551 ± 0.3991. So sánh giữ cùng ngân sách 5.000×20, gamma, reward, kernel và bộ seed; chỉ đổi yếu tố đã nêu. Các cửa sổ kế tiếp chồng lấp nên không độc lập. Reward còn chịu exploration, đối thủ và nhiễu thị trường; không suy ra hội tụ/tối ưu hoặc thứ hạng final policy từ đường train. Rule không học vẫn đổi reward vì learner và tình huống đổi; phase5 mới đánh giá Q đóng băng.

Hình: `artifacts/figures/phase04/exploration_curves.png`.


## Hình epsilon_schedules

Trục x là episode 1–5.000, trục y là xác suất khám phá ε (không đơn vị). Baseline đen liền từ 0,20 xuống sàn 0,02 lần đầu ở episode 461; xám đứt giữ 0,05, xám chấm giữ 0,30. Đây là lịch định trước, trùng ở cả 5 seed; không có vùng sai số, không phải đường reward đo được. Ngẫu nhiên do exploration khác ngẫu nhiên phá đồng hạng Q; ε=0 vẫn có thể phá đồng hạng ngẫu nhiên. Khám phá nhiều giúp thử action nhưng có thể giảm profit khi train; không mặc định lịch nào tốt nhất.

Hình: `artifacts/figures/phase04/epsilon_schedules.png`.


## Hình train_summary

Hai panel tách RL và rule. Trục ngang là 5 cấu hình; trục dọc là lợi nhuận giả lập/bước trung bình trên toàn 100.000 bước/run. Chiều cao cột là mean của 5 mean/run; whisker là sample std (ddof=1) của 5 mean/run, không phải std episode và không phải CI. Baseline: α=0,10; ε giảm: RL 33.76528 ± 0.09989, rule 33.22514 ± 0.12848; α=0,01; ε giảm: RL 30.91717 ± 3.91720, rule 29.64954 ± 4.42718; α=0,50; ε giảm: RL 31.97780 ± 0.12472, rule 31.11284 ± 0.20670; ε cố định 0,05; α=0,10: RL 32.89187 ± 0.18749, rule 32.17176 ± 0.27370; ε cố định 0,30; α=0,10: RL 30.92305 ± 0.09846, rule 30.02129 ± 0.07806. Baseline được tái dùng trong hai sweep; tổng là 25 run, không phải 30. Đây là lợi nhuận trong lúc học, có exploration và opponent phản ứng, chưa so sánh final policy trước cùng opponent/tape. Không chọn lại cấu hình/seed từ biểu đồ này, không coi overlap whisker là kiểm định.

Hình: `artifacts/figures/phase04/train_summary.png`.


## Chênh lệch train ghép seed so với baseline

| Cấu hình | Mean delta RL/bước ± std giữa 5 cặp seed |
|---|---:|
| α=0,01; ε giảm | -2.84811 ± 3.87689 |
| α=0,50; ε giảm | -1.78748 ± 0.20454 |
| ε cố định 0,05; α=0,10 | -0.87341 ± 0.14111 |
| ε cố định 0,30; α=0,10 | -2.84224 ± 0.07202 |

Delta là mean reward lúc học của cấu hình trừ baseline cùng seed, không phải chênh lệch final policy. Đã báo đủ mọi cấu hình đăng ký, không tuning lại. Nhu cầu/doanh số là mô phỏng, số seed nhỏ; không khẳng định cấu hình tốt nhất ở thị trường thật. Phase5 mới chạy đánh giá riêng đóng băng Q, 500 episode/vai và mean/std qua 5 seed.
