# AG02 phase 3 — baseline A và diễn biến học B

Ngày 24/10/2026. Hoàn thành hai baseline đúng protocol v1: mỗi run 5.000 episode,
20 bước/episode, Q khởi tạo bằng 0; không dùng checkpoint smoke. Mọi output mới
nằm trong folder Agent02; final evaluation và TEST của bài V3 chưa được mở.

## Kết quả train thật

Đơn vị reward là tiền giả lập. Mean/bước bằng tổng reward của shop chia 100.000
market step; cả hai shop cùng tham gia một cuộc đối đầu. Mỗi track chỉ có một seed.

| Đại lượng | REF seed42 | CONTROLLED seed11 |
|---|---:|---:|
| Episode / market step | 5.000 / 100.000 | 5.000 / 100.000 |
| Tổng reward RL | 3.345.548 | 3.374.759 |
| Tổng reward rule | 3.283.930 | 3.328.637 |
| Mean RL / bước | 33,45548 | 33,74759 |
| Mean rule / bước | 32,83930 | 33,28637 |
| Chênh RL − rule / bước trong train | 0,61618 | 0,46122 |
| RL giảm giá / 100.000 action | 17.524 | 14.474 |
| Rule giảm giá / 100.000 action | 8.323 | 6.784 |
| CPU trong loop có instrumentation | 4,713 giây | 6,851 giây |
| Wall trong loop có instrumentation | 7,518 giây | 10,438 giây |

Thời gian cộng qua 50 chunk, bao gồm log trong RAM và disk guard; không bao gồm
serialize checkpoint/CSV, import, DEV, dựng hình hay audit. Không dùng hai track
để benchmark tốc độ thuật toán vì RNG, implementation và seed khác nhau.
Hai thư mục run chứa tổng khoảng 93,18 MB (88,86 MiB), gồm 51 checkpoint/run tính
cả episode0 và snapshot đầy đủ mỗi 100 episode. Ổ C còn khoảng 36,35 GiB lúc hậu kiểm.

REF dùng nguyên các class môi trường, Q-learning và luật của thầy, giữ seed+10.000
cho RNG chính sách và thứ tự gọi RNG. Wrapper bổ sung loop chia đoạn và log, không
gọi `main()` hoặc sửa file gốc. Ba fixture seed42/11/55 so Q, reward rows và RNG
chính sách với `train_rl_against_rule` gốc đều khớp chính xác; kiểm split/resume
cũng khớp. Đây là bằng chứng parity trên fixture, không khẳng định đã train gốc
5.000 episode lần thứ hai để đối chiếu. CONTROLLED dùng `TrainSession` phase2 nguyên
hash với RNG nhu cầu/doanh số/policy riêng. Hai run không phải hai replicate đồng nhất.

## Diễn biến và giải thích hình

Đã xem trực quan đủ **4 PNG**: REF learning curve, CONTROLLED learning curve,
Q-table và số lần chọn hành động. Nhãn tiếng Việt đọc được, không bị cắt; hình
chỉ có grayscale, chữ đen. Mỗi hình có lời giải thích mục đích, nguồn, trục/đơn vị,
legend, cách gộp, số seed, so sánh định lượng và giới hạn ở:

- `artifacts/figures/phase03/figure_notes.md` và `figure_notes.json`.
- Bản thảo sử dụng lại: `report/sections/phase03_baseline.md`.
- Số đo gốc: `artifacts/metrics/phase03_curve_analysis.json` và các CSV cùng prefix.

Learning curve có phần raw (reward episode chia 20 bước) và phần trung bình trượt
100 episode, điểm đầu ở episode100, không đệm 0 hay dùng cửa sổ nhìn tương lai.
RL từ 31,921 lên 33,569 ở REF khi so cửa sổ đầu/cuối; CONTROLLED từ 30,2715 lên
34,312. Tuy vậy đường trượt vẫn dao động; không kết luận hội tụ hoặc tối ưu.
Độ lệch chuẩn qua episode trong một run không thay cho độ lệch chuẩn qua training seed.
Agent luật không học vẫn đổi reward do đối thủ RL và thị trường thay đổi.

Q và greedy policy đều lưu đủ 4 state/8 giá trị. REF chọn giữ giá khi observation
đối thủ0, giảm giá khi đối thủ1; CONTROLLED chọn giữ giá cả 4 state ở snapshot cuối.
Q là lợi ích chiết khấu ước lượng, không trực tiếp là lợi nhuận/bước khi đánh giá.
Tần suất action train còn chịu exploration; không đồng nhất với policy greedy cuối.

## DEV đóng băng — tách khỏi kết quả cuối

Mỗi Q được DEV 100 episode/vai trên cùng scenario seed1000011, tổng 8.000 market
step cho 2 policy × 2 vai × 100 × 20. Không cập nhật Q, không exploration; hash
Q trước/sau bằng nhau. Tie-breaking giữ theo protocol. Không dùng DEV để đổi config.

| Track | Vai learner | RL profit/bước | Rule profit/bước |
|---|---:|---:|---:|
| REF | 0 | 35,6525 | 35,2100 |
| REF | 1 | 35,2100 | 35,6525 |
| CONTROLLED | 0 | 35,6525 | 35,2100 |
| CONTROLLED | 1 | 35,2100 | 35,6525 |

Cả hai learner chọn giữ giá toàn bộ 2.000 action/vai. Bắt đầu với lịch sử0, learner
giữ giá ở observation đối thủ0, nên rule cũng giữ giá và observation đối thủ1
không xuất hiện. Do đó khác biệt Q ở các state còn lại chưa ảnh hưởng trajectory
greedy này. Sau lấy trung bình hai vai, RL và rule cùng 35,43125/bước ở cả hai track.
Chênh lệch ở một vai là nhiễu doanh số theo vị trí tape; không gọi đó là lợi thế policy.
Đây là DEV n=1 training seed/track, chưa phải final500 episode/vai hay kết luận đa seed.

## Nghiệm thu và bàn giao

- Pretrain: **116 test PASS/0 skip**, coverage hai wrapper mới 94,79%; nguồn và
  cấu hình được khai báo trước train trong `evidence/phase03/declaration.json`.
- Cuối phase: **122 test PASS/0 skip**, coverage tổng **94,94%** trên ba module
  `reference_training`, `baseline_runs`, `baseline_analysis`. Không gồm teacher,
  CLI/plot/auditor hoặc toàn project. Không ghi đè XML/coverage phase1–2 hay pretrain.
- Auditor tái tính từ CSV/checkpoint/DEV đã lưu, kiểm Q/policy, action count,
  visitation100.000/run, schedule epsilon, 5.000 dòng/run và hash mọi output.
  Không train hoặc forward/evaluate policy lại khi audit/làm hình.
- Source mới được lint, launcher PowerShell parse/CLI PASS; bốn hình có QA riêng.
  Nguồn cũ, khóa phase2, 7 asset tham chiếu và metadata Gold giữ nguyên hash.
- Hai run hoàn tất không có resume thật; kiểm recovery dùng fixture nhỏ riêng.
  Không có failed scientific run, background queue, cài dependency hoặc tải dataset.

Khóa phát hành/receipt ở `evidence/phase03/experiment_lock.json`, `verification.json`.
Registry trained riêng ở `artifacts/manifests/phase03/trained_registry.json`;
final evaluation count vẫn0. Không sửa protocol để đổi `declared_not_started` thành
completed: đó là đăng ký bất biến, trạng thái thật được ghi riêng trong registry.

Tiếp theo **`làm AG02 phase 4`**: hoàn thành 24 run còn lại của ma trận CONTROLLED25,
tái dùng baseline seed11 này. Giữ REF42 riêng; chưa tự chạy final evaluation ở phase4.
