# Baseline A–B — bản thảo từ số đo phase 3

Mỗi track có một training seed, 5.000 episode × 20 bước. REF dùng các class gốc của thầy với loop instrument đã kiểm parity; CONTROLLED dùng core phase2 tách RNG. Không gộp hai run thành n=2.

| Track | RL profit/bước train | Rule profit/bước train | Chênh lệch trong đối đầu |
|---|---:|---:|---:|
| REF | 33.45548 | 32.83930 | 0.61618 |
| CONTROLLED | 33.74759 | 33.28637 | 0.46122 |

Mean là tổng reward chia 100.000 market step cho từng shop. Chênh lệch train mô tả cùng cuộc đối đầu, chưa là so sánh frozen policy trước cùng opponent.


## Hình ref_learning_curve

REF seed 42: mỗi điểm ở phần trên là reward cả episode chia 20 bước; trục ngang là episode 1–5.000, trục dọc là lợi nhuận giả lập/bước. Đen liền là RL, xám đứt là rule. Phần dưới gộp cửa sổ 100 episode liên tiếp (2.000 bước), điểm đầu ở episode100; không đệm 0, không dùng dữ liệu tương lai. Mỗi track chỉ một seed, không có error band. RL: 100 episode đầu 31.9210, cuối 33.5690; rule: 30.4315 → 33.4115. Độ lệch chuẩn reward trung bình/bước giữa 5.000 episode: RL 5.2756, rule 5.6354 (ddof1, không phải std giữa training seed). Đường trượt RL vẫn dao động trong [31.0690, 35.7060]. Nhu cầu và doanh số ngẫu nhiên tạo nhiễu; epsilon giảm cũng làm đổi hành vi train. Rule cố định vẫn có reward đổi vì đối thủ RL và tình huống thị trường đổi. Làm mượt giúp đọc xu hướng, không chứng minh hội tụ/tối ưu hay hơn ngoài mẫu.

Nguồn hình: `artifacts/figures/phase03/ref_learning_curve.png`; số liệu ở `artifacts/metrics/phase03_*`.


## Hình controlled_learning_curve

CONTROLLED seed 11: mỗi điểm ở phần trên là reward cả episode chia 20 bước; trục ngang là episode 1–5.000, trục dọc là lợi nhuận giả lập/bước. Đen liền là RL, xám đứt là rule. Phần dưới gộp cửa sổ 100 episode liên tiếp (2.000 bước), điểm đầu ở episode100; không đệm 0, không dùng dữ liệu tương lai. Mỗi track chỉ một seed, không có error band. RL: 100 episode đầu 30.2715, cuối 34.3120; rule: 29.0340 → 33.3620. Độ lệch chuẩn reward trung bình/bước giữa 5.000 episode: RL 5.3246, rule 5.6387 (ddof1, không phải std giữa training seed). Đường trượt RL vẫn dao động trong [30.2590, 35.6420]. Nhu cầu và doanh số ngẫu nhiên tạo nhiễu; epsilon giảm cũng làm đổi hành vi train. Rule cố định vẫn có reward đổi vì đối thủ RL và tình huống thị trường đổi. Làm mượt giúp đọc xu hướng, không chứng minh hội tụ/tối ưu hay hơn ngoài mẫu.

Nguồn hình: `artifacts/figures/phase03/controlled_learning_curve.png`; số liệu ở `artifacts/metrics/phase03_*`.


## Hình q_tables

Hai ô hình là Q cuối train của hai run, mỗi run một seed, không lấy trung bình. Trục dọc có 4 state (nhu cầu/hành động trước của đối thủ), trục ngang 2 action. Thang xám chung: tối hơn là Q lớn hơn; số trong ô là Q, không phải profit/bước DEV. REF: (0, 0)→[0], (0, 1)→[1], (1, 0)→[0], (1, 1)→[1]; CONTROLLED: (0, 0)→[0], (0, 1)→[0], (1, 0)→[0], (1, 1)→[0]. Hai track khác RNG và seed nên không dùng chênh Q để xếp hạng phương pháp. Q là ước lượng chịu chiết khấu, nhiễu và cập nhật terminal; bảng cuối không chứng minh policy tối ưu. Tập greedy giữ toàn bộ action đồng hạng theo isclose; Q và policy đầy đủ được lưu riêng.

Nguồn hình: `artifacts/figures/phase03/q_tables.png`; số liệu ở `artifacts/metrics/phase03_*`.


## Hình action_counts

Trục ngang là 4 cặp agent/action; trục dọc là tổng lượt chọn trên 5.000×20 bước. Cột tối giữ giá, cột sáng giảm giá, số trên cột là count; mỗi cặp 0+1 của một agent bằng100.000. REF: RL giảm 17,524/100.000 (17.524%), rule giảm 8,323/100.000 (8.323%); CONTROLLED: RL giảm 14,474/100.000 (14.474%), rule giảm 6,784/100.000 (6.784%). Không gộp hai track thành n2, không có error bar. Đây là hành động lúc train còn exploration, không phải tần suất policy greedy DEV. Giảm giá nhiều hơn không tự chứng minh tốt hơn: lãi mỗi món từ5 còn3. Không thể quy khác biệt cho framework khi seed/RNG đã khác.

Nguồn hình: `artifacts/figures/phase03/action_counts.png`; số liệu ở `artifacts/metrics/phase03_*`.


## DEV riêng, chưa là kết quả cuối

| Track | Vai learner | RL profit/bước | Rule profit/bước |
|---|---:|---:|---:|
| REF | 0 | 35.65250 | 35.21000 |
| REF | 1 | 35.21000 | 35.65250 |
| CONTROLLED | 0 | 35.65250 | 35.21000 |
| CONTROLLED | 1 | 35.21000 | 35.65250 |

DEV dùng100 episode mỗi vai, scenario seed1000011/tape chung cho cả hai Q, Q đóng băng và exploration tắt; không dùng để chỉnh cấu hình. Mỗi vai2.000 bước, không gọi200 episode là200 training seed. Hai Q có thể khác ở state không gặp trong trajectory greedy: khi cả hai bắt đầu giữ giá và learner tiếp tục giữ giá ở observation đối thủ0, rule luôn giữ giá và observation đối thủ1 không xuất hiện. Nếu DEV trùng, đó là cùng hành vi đạt tới trên kịch bản này, không phải Q bằng nhau hoặc chứng minh mọi môi trường tương đương. Final500 episode/vai và đa seed thuộc phase5.
