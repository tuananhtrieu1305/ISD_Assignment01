# E — đánh giá riêng, Q đóng băng

Mỗi final claim có 500 episode×20 bước, mỗi Q chạy hai vai. Lấy mean hai vai trước, sau đó mean/sample std ddof=1 giữa 5 training seed. Không gộp 10 vai hoặc 5.000 episode thành learner độc lập. Không có CI/kiểm định ý nghĩa từ whisker; đây là mô phỏng, chỉ 5 seed. 

71 claim: 50 core +20 đối chứng +1 REF native riêng, mỗi claim chạy đúng1 lần. Không train/tuning, Q hash trước/sau giữ nguyên, seed final tách khỏi train/DEV. Đối chứng rule-vs-rule và no-discount đều bắt đầu lịch sử0; trong mô hình này hai cách có thể giữ giá mãi trên reachable states, nên không coi chúng là hai policy độc lập về hành vi.

| Cấu hình | Final Q profit/bước ±std | Q−rule trong trận | Q−Rule control (cùng tape) |
|---|---:|---:|---:|
| Baseline | 34.02786 ± 1.22178 | 0.80818 | -1.02449 |
| α=0,01 | 33.90382 ± 2.60833 | 0.44187 | -1.14853 |
| α=0,50 | 32.06337 ± 4.25085 | 0.63457 | -2.98898 |
| ε=0,05 | 33.39952 ± 2.64330 | 0.84794 | -1.65283 |
| ε=0,30 | 32.87013 ± 3.58062 | 0.33861 | -2.18222 |

REF native seed42, role0,500 episode: RL 35.12750, rule 34.96850/bước. Đây là hàm evaluate_pair gốc với env seed500042 và RNG policy clone từ checkpoint; không gộp vào CONTROLLED n5 hoặc gọi là paired role-swap.


## Hình final_profit

Trục x: 5 cấu hình; y: profit giả lập/bước trước fixed-rule opponent. Cột xám là Q đóng băng, whisker là std giữa training seed; đường đứt là mean Rule-vs-rule qua5 kịch bản, không phải đối chứng đã train. Mỗi final claim có 500 episode×20 bước, mỗi Q chạy hai vai. Lấy mean hai vai trước, sau đó mean/sample std ddof=1 giữa 5 training seed. Không gộp 10 vai hoặc 5.000 episode thành learner độc lập. Không có CI/kiểm định ý nghĩa từ whisker; đây là mô phỏng, chỉ 5 seed. Baseline: 34.02786 ± 1.22178; α=0,01: 33.90382 ± 2.60833; α=0,50: 32.06337 ± 4.25085; ε=0,05: 33.39952 ± 2.64330; ε=0,30: 32.87013 ± 3.58062. Mean đối chứng 35.05235. Reward giữa các config được đo trên cùng tape theo seed và role. Không dùng final để tuning/chọn lại seed. Nếu hai policy cho cùng score, chỉ kết luận trên các trajectory này, không chứng minh tương đương mọi state.

Hình: `artifacts/figures/phase05/final_profit.png`.


## Hình paired_and_match

Hai panel cùng trục x cấu hình, trục y chênh profit/bước; mốc đứt0 là bằng nhau. Trái ghép Q cấu hình trừ Q baseline cùng training seed, tape và fixed opponent; phải so chất lượng policy theo panel này. Panel phải là Q trừ reward của rule trong chính cuộc đối đầu, có thể chịu phản ứng của rule với learner. Chấm là mean, whisker sample std giữa5 delta seed, không phải CI. Mỗi final claim có 500 episode×20 bước, mỗi Q chạy hai vai. Lấy mean hai vai trước, sau đó mean/sample std ddof=1 giữa 5 training seed. Không gộp 10 vai hoặc 5.000 episode thành learner độc lập. Không có CI/kiểm định ý nghĩa từ whisker; đây là mô phỏng, chỉ 5 seed. Delta so baseline: Baseline: 0.00000 ± 0.00000; α=0,01: -0.12404 ± 3.39200; α=0,50: -1.96449 ± 5.13750; ε=0,05: -0.62834 ± 3.55259; ε=0,30: -1.15773 ± 3.92963. Không đánh đồng lợi thế trong trận với hơn một policy khác trước cùng opponent.

Hình: `artifacts/figures/phase05/paired_and_match.png`.


## Hình train_vs_final

Trục x cấu hình, y profit/bước. Cột sáng lấy reward toàn giai đoạn học (còn exploration và Q đang đổi), cột tối lấy policy cuối đóng băng, tắt exploration và dùng final scenarios riêng. Hai loại whisker đều giữa5 seed, nhưng đo hai đại lượng khác nhau; không coi reward train thấp là final policy kém. Mỗi final claim có 500 episode×20 bước, mỗi Q chạy hai vai. Lấy mean hai vai trước, sau đó mean/sample std ddof=1 giữa 5 training seed. Không gộp 10 vai hoặc 5.000 episode thành learner độc lập. Không có CI/kiểm định ý nghĩa từ whisker; đây là mô phỏng, chỉ 5 seed. Final: Baseline: 34.02786 ± 1.22178; α=0,01: 33.90382 ± 2.60833; α=0,50: 32.06337 ± 4.25085; ε=0,05: 33.39952 ± 2.64330; ε=0,30: 32.87013 ± 3.58062. Chênh train/final có cả thay đổi policy, exploration và tập scenario, không quy toàn bộ tác dụng cho riêng việc tắt epsilon. Không gọi score tăng là chứng minh hội tụ.

Hình: `artifacts/figures/phase05/train_vs_final.png`.


## Hình discount_rates

Trục x cấu hình; y tỷ lệ action giảm giá (%), không phải epsilon hay xác suất chuyển đổi mua hàng. Cột sáng toàn100.000 bước train/run, cột tối20.000 bước final/seed (hai vai); whisker sample std giữa5 seed, đơn vị điểm %. Final: Baseline: 16.212% ± 22.199 điểm %; α=0,01: 12.876% ± 28.792 điểm %; α=0,50: 30.186% ± 41.559 điểm %; ε=0,05: 21.160% ± 30.090 điểm %; ε=0,30: 19.824% ± 27.145 điểm %. Mỗi final claim có 500 episode×20 bước, mỗi Q chạy hai vai. Lấy mean hai vai trước, sau đó mean/sample std ddof=1 giữa 5 training seed. Không gộp 10 vai hoặc 5.000 episode thành learner độc lập. Không có CI/kiểm định ý nghĩa từ whisker; đây là mô phỏng, chỉ 5 seed. Giảm giá làm lãi mỗi món từ5 còn3; giảm giá nhiều không tự chứng minh profit tốt. Policy có thể khác ở state không đạt tới sau reset0. Tần suất là hành vi thực đo, không chỉ đọc argmax toàn bảng Q.

Hình: `artifacts/figures/phase05/discount_rates.png`.


Sáu bảng CSV baseline_reward, q_policy, alpha_comparison, exploration_comparison, multi_seed, paired_comparison nằm trong artifacts/metrics/phase05/. Q/policy có đủ104 state rows của26 checkpoint; không dùng giá trị Q như trực tiếp profit final. Phân tích mới chỉ đọc output đã lưu. Giữ cả kết quả không thắng rule, không đổi hyperparameter/seed sau final.
