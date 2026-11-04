# AG02 Phase 6 — tương tác hai learner và độ bền khi đổi nhu cầu

Ngày 24/10/2026. Đã chạy đủ 15 lượt train đã đăng ký và 160 lượt đánh giá đóng băng,
mỗi lượt đánh giá đúng một lần. Kết quả dưới đây lấy từ output đã lưu; không chạy lại
Phase 5, không chỉnh tham số theo điểm cuối và không mở TEST của tiểu luận V3.

## Những phần đã thực hiện

Năm lượt có hai Q-learning cùng học trong thị trường IID; mỗi tác tử có Q-table và
RNG chính sách riêng. Cả hai chọn hành động từ trạng thái cũ trước khi môi trường
trả reward, sau đó mới cập nhật Q. Mười lượt còn lại là một Q-learning trước agent
luật cố định: năm lượt nhu cầu persistent và năm lượt dùng kernel hiệu chỉnh từ vàng.
Mọi lượt đều bắt đầu từ Q bằng 0, train 5.000 episode ×20 bước, giữ nguyên learning
budget, giá, chi phí, reward và conversion của baseline. Chỉ kernel nhu cầu thay đổi
trong thí nghiệm câu 9; rule không bị sửa để tạo lợi thế cho learner.

Tổng cộng 75.000 dòng train, 1.500.000 market step và 2.000.000 lần cập nhật learner;
hai learner dùng chung một lượt thị trường nên không đếm đôi market step. Có 20
learner instance, 51 checkpoint mỗi run, visitation, policy, Q và trace 20 bước/run.
Không có scientific failure hoặc resume. Thời gian CPU/wall trong manifest chỉ đo
loop train có instrumentation, không gồm ghi checkpoint; không phải benchmark máy.

Train declaration SHA256:
`d95096c67d760240c1ee8ac45264d8dcdbe59d067baff97b26ce2e999f9288a8`.
Eval declaration SHA256:
`f03206ede3ec1973e94270985c2a19f01bbdaa38007de5f382c395c030481a2d`.
Thiết kế và nguồn được khóa trước train; 160 job/Q/checkpoint/scenario được khóa
trước đánh giá. Xem `docs/phase06_design.md` và `evidence/phase06/`.

## Dữ liệu vàng được dùng thế nào

Tận dụng snapshot World Bank Pink Sheet có sẵn, không tải lại hoặc sử dụng nhãn
validation/TEST cũ. Chỉ lấy 560 giá tháng từ 01/1960 đến cutoff TRAIN 08/2006,
bao gồm lịch sử input trước thời điểm target TRAIN 1962. Đơn vị USD/troy ounce;
560 giá hợp lệ, không có tháng thiếu trong prefix này. Giá nhỏ nhất 35, lớn nhất
675, trung bình 253,90357. Chỉ đọc giá sau khi kiểm nhãn tháng nằm trong cutoff.
Source XLSX, split contract và TRAIN IDs có hash trong artifact dẫn xuất.

Từ hai tháng liền kề: trạng thái 1 nếu giá tăng, trạng thái 0 nếu giảm hoặc không
đổi. Có 559 trạng thái (340 trạng thái 0, 219 trạng thái 1), 558 chuyển trạng thái:

| Hiện tại → tháng sau | 0 | 1 |
|---|---:|---:|
| 0 |240|99|
| 1 |99|120|

Sau khi cộng 1 vào mỗi ô theo protocol đã định trước, kernel là
`[[0,706745; 0,293255], [0,452489; 0,547511]]`. Như vậy xác suất giữ trạng thái 0
là 70,67%, giữ trạng thái 1 là 54,75%; persistent giữ cả hai trạng thái với xác suất
90%, còn IID là 50%. Các episode vẫn khởi tạo nhu cầu cân bằng 0/1 như baseline.

Đây là cách thiết kế **nhu cầu giả lập từ hướng biến động giá**, không phải đo cầu
vàng, dự báo giá hay kiểm chứng giao dịch. Giá thuộc vintage có thể đã sửa hồi tố.
Không dùng việc giá tăng để kết luận nhu cầu thực tế tăng. Artifact:
`data/derived/gold_regime_kernel_v1.json`, `gold_train_prefix_v1.csv`.

## Câu 8 — khi cả hai tác tử cùng học

Đối thủ giảm giá làm thay đổi xác suất mua ở shop của learner; hành động trước của
learner cũng ảnh hưởng hành động tiếp theo của agent luật. Khi cả hai Q-learning
cùng đổi chính sách, một lựa chọn từng có lợi có thể cho kết quả khác vì đối thủ
đã thay đổi. Learner phải thích nghi với cả nhiễu doanh số và chính sách đối thủ.

Để khảo sát, đóng băng Q ở các checkpoint 0, 1.000, 2.500 và 5.000 rồi đo từng
learner trước **cùng agent luật cố định và cùng scenario tapes**, 500 episode/vai.
Gộp hai vai trước, rồi hai learner trong một pair, sau đó tính mean/sample std qua
5 pair seed. Không coi 10 learner phụ thuộc là 10 lần lặp độc lập.

| Checkpoint | Lợi nhuận giả lập/bước, mean±std qua 5 pair seed |
|---|---:|
| 0 |29,55358±0,19596|
| 1.000 |34,48443±1,32679|
| 2.500 |34,23232±0,70593|
| 5.000 |31,58872±2,75761|

Mean tăng 4,93085 ở checkpoint 1.000 so với khởi tạo, nhưng giảm 2,89571 từ 1.000
đến 5.000. Vì vậy train lâu hơn không bảo đảm checkpoint cuối tốt hơn trong phép
đo này. Vẫn báo đủ bốn điểm đã định trước, không chọn checkpoint 1.000 làm kết quả
cuối thay thế. Ở checkpoint 0, hai Q-table đều bằng 0 và cơ chế phá đồng hạng trong
evaluation giống nhau; đó không phải hai chính sách khởi tạo độc lập khác nhau.

Qua 500 khoảng learner×100 episode, có 612 lần một state đổi tập hành động greedy.
Mỗi learner có bốn state nên một khoảng có thể có nhiều state đổi. Đây là số đếm
thay đổi chính sách, không phải số lần thay action trong từng timestep. Q-L2 giữa
checkpoint cũng được lưu. State ít gặp có thể đổi greedy mà không đổi return.
Những quan sát này chưa chứng minh riêng tác động nhân quả của đối thủ đang học:
alpha cố định, lấy mẫu, observation thiếu thông tin và các yếu tố khác vẫn tồn tại.

## Câu 9 — sửa môi trường và so sánh kết quả

Trên mỗi kernel mới, đo Q baseline IID cũ, Q train lại, rule và no-discount trước
cùng fixed rule opponent, cùng tape theo seed và hai vai. Mỗi policy 500 episode/vai.
IID final đã có ở Phase 5 không chạy lại. Mean/std dưới đây gộp vai trước; n=5 là
training seed đối với Q và scenario panel đối với hai đối chứng không train.

| Kernel | Q IID cũ | Q train lại | Rule | Giữ giá |
|---|---:|---:|---:|---:|
| Persistent |34,54252±0,71342|33,06165±2,63493|35,02665±0,25749|35,02665±0,25749|
| Gold |30,16204±1,09861|29,35694±2,78040|31,07485±0,21348|31,07485±0,21348|

Chênh ghép cặp **train lại trừ baseline cũ**: persistent −1,48087±2,70026;
Gold −0,80510±3,54276 lợi nhuận/bước. Train lại không cải thiện mean trong hai
thí nghiệm này. Gold có seed 22/33 cải thiện, nhưng seed 11/44 giảm; không loại
seed bất lợi hoặc đổi budget để làm đẹp mean. Rule và no-discount trùng hành vi
giữ giá trước fixed rule từ history reset bằng 0, nên không phải hai chuẩn hành vi
độc lập. Các whisker là độ phân tán, không phải CI hoặc kiểm định ý nghĩa thống kê.

So sánh hợp lệ là giữa các policy trong cùng kernel. Không lấy profit Gold thấp
hơn persistent để kết luận riêng chất lượng learner giảm: phân phối nhu cầu đã
khác. Với n=5 và simulator minh họa, chưa đủ kết luận một phương pháp luôn hơn.

Ít nhất năm hạn chế vẫn cần nêu: conversion chỉ là giả định; nhu cầu đơn giản và
proxy vàng không đo nhu cầu; observation cũ thiếu hành động trước của chính mình
và thời gian còn lại; không có tồn kho/dị biệt khách; doanh số hai shop được sinh
riêng, không phải thị phần độc quyền. Thay kernel đã triển khai sửa đổi thật theo
đề, nhưng chỉ kiểm tra một khía cạnh độ bền, không giải quyết mọi hạn chế.

## Hình, bảng và nghiệm thu

Có 9 CSV trong `artifacts/metrics/phase06/`: sáu bảng aggregate cùng train summary,
pair train curves và policy drift. Bốn hình grayscale đã mở xem từng hình:

- `gold_calibration.png`: trục thời gian/giá, kernel và ý nghĩa regime; không có giá
  validation/TEST sau cutoff trong đường vẽ.
- `two_learner_training.png`: MA100 riêng từng seed, đường mean và dải ±sample std
  qua 5 pair seed. Reward vẫn dao động; mean train learner0/1 là 32,99454/32,98117.
  Std reward theo episode ở 100 episode cuối trung bình 5,59195/5,66629 là đại lượng
  khác với dải std giữa seed trên hình, không dùng thay nhau.
- `checkpoint_drift.png`: bốn checkpoint đo trước fixed rule, và số state đổi tập
  greedy/4 mỗi khoảng 100 episode. Điểm nối chỉ giúp đọc các mốc đã đo.
- `variant_robustness.png`: bốn policy trong từng kernel, cột mean/whisker std;
  paired delta tính theo seed chứ không trừ tùy hai episode độc lập.

Mỗi hình có diễn giải trục/đơn vị, đường/cột/dải, nguồn, aggregation/n, số liệu và
giới hạn tại `artifacts/figures/phase06/figure_notes.md`/JSON. Bản thảo để ghép báo cáo:
`report/sections/phase06_robustness.md`. Không có hình bị cắt nhãn hoặc chữ màu khác.

186 test PASS/0skip; coverage combined 97,1875% trên bốn module mới
gold_regime/pair_training/phase06_journal/phase06_analysis; statement 97,8632%,
branch 95,3488%. Không phải coverage toàn project, CLI, plots, auditor hoặc evaluator
cũ. Pretrain 181 và final 186 lưu riêng. Hai lỗi fixture development (tính nhầm
Laplace và so tuple với list sau JSON) đã sửa trước train; giữ XML cũ, không phải
scientific failure. Ruff, PowerShell parser, CLI help/status đạt.

160 claim/count1 có 80.000 dòng episode, 1.600.000 market step. Auditor chỉ đọc
journal/raw CSV/Q/hash và tái tính bảng; không policy forward. Nguồn thầy, khóa
Phase1–5, các asset tham chiếu và provenance Gold được kiểm bảo toàn. Release và
verification ở `evidence/phase06/`; registry trained/evaluated mới ở
`artifacts/manifests/phase06/trained_evaluated_registry.json`. Controller kết thúc,
PID=null; registry/protocol cũ giữ nguyên snapshot lịch sử.

Bước tiếp theo khi được yêu cầu: **`làm AG02 phase 7`**. Handoff Q baseline/variant,
kernel/budget/tapes đã khóa để kiểm agent tăng memory/time; không mở lại final
Phase5/6, không tự build PDF/DOCX hoặc nộp bài ở Phase6.
