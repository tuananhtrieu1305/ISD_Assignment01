# AG02 phase 4 — sweeps C/D đa seed

Ngày 24/10/2026. Ma trận CONTROLLED đã đủ **25/25 cell**: 5 cấu hình × 5 seed
(11/22/33/44/55), mỗi run 5.000 episode ×20 bước. Phase4 train 24 run mới,
tái dùng nguyên baseline seed11 của phase3. REF42 vẫn riêng, không gộp thành seed thứ sáu.

## Phạm vi và kiểm soát

- Alpha: 0,01 / 0,10 / 0,50, giữ gamma0,9, lịch epsilon baseline, reward và môi trường.
- Exploration: baseline decay0,20→sàn0,02, fixed0,05 và fixed0,30; giữ alpha0,10.
- Không train trùng baseline cho hai sweep. Tổng core125.000 dòng episode,
  2.500.000 market step; phase4 mới thêm2.400.000 step. Đây là mô phỏng synthetic,
  không phải các mẫu thị trường độc lập hoặc các learner độc lập theo timestep.
- Giữ core phase2, persistence phase3 và code thầy nguyên hash. Không dùng Q smoke,
  không đổi cấu hình/seed để có hình đẹp. Không gọi lại main code thầy.
- Source/config đã khóa trước train tại `evidence/phase04/declaration.json`,
  SHA256 `cec88cd1d8300c9325c6b27f605b208c973e05297d06d3863481f9e7f7d9b92a`.
- Không có DEV mới hoặc final evaluation trong phase4; mọi final count vẫn0.

## Kết quả và phần giải thích dùng cho tiểu luận

Bản thảo C/D, bảng kết quả thật và phân tích ngắn ở
`report/sections/phase04_sweeps.md`. Dữ liệu không được lấy từ expected result
hay từ smoke. Các bảng máy đọc được nằm trong `artifacts/metrics/phase04/`:

| File | Nội dung và mẫu số |
|---|---|
| `seed_train_summary.csv` | 25 mean/run, tổng reward, action count, thời gian train; mỗi run100.000 bước |
| `config_train_summary.csv` | 5 cấu hình; mean/sample std giữa5 training seed, ddof1 |
| `curves_mean_std.csv` | 24.505 dòng: 4.901 điểm trượt100 episode ×5 cấu hình, cho cả RL/rule |
| `paired_train_deltas.json` | 4 cấu hình trừ baseline, ghép đúng seed ID; delta chỉ trong train |
| `epsilon_schedules.csv` | 15.000 dòng lịch đã đăng ký của3 exploration schedule |
| `source_index.json` | 25 CSV gốc và hash để truy ngược |
| `aggregation.json` | Đơn vị, window100, n5, ddof1 và giới hạn diễn giải |

Bốn biểu đồ gồm alpha curves, exploration curves, lịch epsilon và tổng hợp toàn
train. Mỗi hình có giải thích riêng ở `artifacts/figures/phase04/figure_notes.md`
và JSON tương ứng: mục đích, nguồn, trục/đơn vị, đường/vùng mờ, số seed, cách gộp,
so sánh định lượng và giới hạn. Tất cả được kiểm tra trực quan; chữ đen, hình xám.

Learning curve: làm mượt100 episode riêng từng seed, sau đó lấy mean ±1 sample
std qua5 seed. Vùng mờ không phải khoảng tin cậy, các cửa sổ chồng lấp không độc lập.
Bảng/cột whole-train dùng5 mean/run, khác với độ lệch chuẩn reward giữa các episode.
Ghép seed giữ thiết kế comparable nhưng chuỗi draw doanh số/policy vẫn có thể khác
khi hành động khác; không gọi đây là matched final tapes. Reward còn chứa exploration
và phản ứng của đối thủ, không dùng để xếp hạng chất lượng frozen policy cuối.

Số đo whole-train (mean ± sample std giữa 5 training seed, lợi nhuận giả lập/bước):

| Cấu hình | RL | Rule |
|---|---:|---:|
| Baseline α0,10, epsilon giảm | 33,76528 ±0,09989 | 33,22514 ±0,12848 |
| α0,01 | 30,91717 ±3,91720 | 29,64954 ±4,42718 |
| α0,50 | 31,97780 ±0,12472 | 31,11284 ±0,20670 |
| Epsilon cố định0,05 | 32,89187 ±0,18749 | 32,17176 ±0,27370 |
| Epsilon cố định0,30 | 30,92305 ±0,09846 | 30,02129 ±0,07806 |

Vùng mờ rộng của α0,01 phản ánh khác biệt lớn giữa các seed: RL seed55 chỉ25,77890
so với seed22 là34,80447/bước trên toàn train. Ở100 episode cuối, seed55 đạt28,509,
còn bốn seed khác khoảng34,66–34,81; vì vậy mean cuối33,49160 vẫn có std2,78596.
Đây không phải lỗi đồ thị hay khoảng tin cậy; không bỏ seed55 để giảm error bar.
Alpha nhỏ sửa Q ít mỗi bước, nên tiến trình thích nghi chậm là một cách giải thích
có thể có; đường reward riêng chưa tách hết vai trò visitation và lịch khám phá.

Baseline có profit train quan sát cao hơn các cấu hình còn lại trong ma trận này.
Fixed0,30 thấp hơn fixed0,05 trong train, phù hợp khả năng việc thử action ngẫu nhiên
có chi phí ngắn hạn. Tuy nhiên không suy ra policy cuối của fixed0,30 kém hơn từ
biểu đồ train; mọi Q vẫn phải qua đánh giá riêng ở phase5. Alpha0,50 có mean train
thấp hơn baseline dù std giữa mean/run nhỏ; std nhỏ không tự đồng nghĩa chất lượng tốt.
Lịch epsilon baseline chạm sàn0,02 ở episode461, còn hai lịch fixed không đổi; hình
lịch chỉ giải thích cơ chế, không phải bằng chứng reward đo được.

## Vận hành và tài nguyên đo thật

24 run mới hoàn tất một lượt, không có failed scientific run hoặc recovery thật.
Baseline reused đúng registration/declaration gốc; các fixture kiểm recovery/guards
không được tính vào số run khoa học. Controller đã COMPLETE, PID=null, một writer.

Thời gian của toàn25 run (bao gồm baseline cũ) cộng từ segment:
CPU158,136 giây, wall244,350 giây trong loop có instrumentation/disk guard.
Riêng queue phase4 khoảng564,394 giây (~9,41 phút), gồm24 run mới, checkpoint I/O,
hash verification và baseline reuse; không gồm khởi động runtime, pretrain, tạo
hình hoặc audit sau queue. Không dùng số đo này như benchmark framework/GPU.
Ổ C còn khoảng34,48GiB sau queue, trên reserve5GiB; không cài môi trường hoặc xóa dữ liệu.

## Nghiệm thu

- Pretrain r2: **132 test PASS/0 skip**; coverage100% trên hai helper mới về chọn
  run và thống kê cơ bản. Lần pretrain trước có lỗi vị trí monkeypatch trong test,
  đã sửa trước khi khai báo/chạy scientific run; XML cũ được giữ lịch sử.
- Cuối phase: **137 test PASS/0 skip**; coverage100% trên ba module `sweep_runs`,
  `sweep_analysis`, `sweep_summary` (93 statement, 36 branch). Không phải coverage
  teacher, CLI, plots, auditor hoặc toàn project.
- Auditor kiểm đủ5.000 dòng/run, 100.000 visits/run, Q8 và policy4-state, epsilon
  schedule, checkpoint hash, registration/spec và source declaration từng run.
  Tái tính bảng/curve/paired delta từ saved logs, không policy forward hoặc train lại.
- Lint và parser/CLI PASS. Bốn PNG có notes/visualQA và kiểm grayscale; manifest
  producer pendingQA là snapshot trước QA, không sửa ngược lịch sử.
- Khóa phase1–3, nguồn teacher, 7 asset tham chiếu và metadata Gold giữ nguyên hash.
  Không mở TEST V3, không chạy lại DEV phase3, không sửa env/GPU/uv.lock.

Nghiệm thu chính thức: `evidence/phase04/verification.json`, khóa artifact ở
`evidence/phase04/experiment_lock.json`. Handoff25 Q tại
`artifacts/manifests/phase04/trained_registry.json`, tách registry phase3 đã khóa.
Ma trận đăng ký trong protocol giữ nguyên; trạng thái trained được ghi riêng.

Tiếp theo **`làm AG02 phase 5`**: khóa evaluator/final gate/journal rồi đánh giá
Q đóng băng 500 episode mỗi vai theo protocol, giữ mọi cấu hình đăng ký và không tuning từ kết quả cuối.
