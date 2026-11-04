# Giải thích hình Phase6

## gold_calibration

**purpose**: Mô tả dữ liệu thực dùng tạo kịch bản, không phải đo demand.

**axes_and_units**: Trái:X tháng,Y USD/troy ounce;phải:hàng regime hiện tại,cột regime kế;ô xác suất0–1.

**legend**: Đường đen:giá tháng;ô xám/xác suất:kernel.

**aggregation_and_n**: 560giá tháng,559regime,558transition;không smoothing giá.

**observations**: 01/1960–08/2006;min35.00,max675.00;counts[[240, 99], [99, 120]];P00=0.7067,P11=0.5475;persistent giữ0,9,còn IID0,5.

**quantitative_comparison**: 01/1960–08/2006;min35.00,max675.00;counts[[240, 99], [99, 120]];P00=0.7067,P11=0.5475;persistent giữ0,9,còn IID0,5.

**limitations**: Regime1 là giá tăng,0 gồm giảm/không đổi;giá không đo demand. Vintage sửa hồi tố;không backtest đầu tư.

**data_source**: data/derived/gold_regime_kernel_v1.json và gold_train_prefix_v1.csv

## two_learner_training

**purpose**: Quan sát reward và độ biến động khi đối thủ cũng thay đổi.

**axes_and_units**: X:episode train;Y:lợi nhuận giả lập/bước.

**legend**: Mỗi panel một learner;đen meanMA100,xám±std.

**aggregation_and_n**: Làm mượt riêng mỗi trajectory100episode rồi mean/std ddof1 qua5pair seed;không phảiCI.

**observations**: learner0:mean train=32.99454,std100episode cuối trung bình=5.59195;learner1:mean train=32.98117,std100episode cuối trung bình=5.66629

**quantitative_comparison**: learner0:mean train=32.99454,std100episode cuối trung bình=5.59195;learner1:mean train=32.98117,std100episode cuối trung bình=5.66629

**limitations**: Hai learner trong một pair phụ thuộc;vùng mờ chứa cả khác biệt seed và quá trình học. Không chứng minh hội tụ/nhân quả.

**data_source**: artifacts/metrics/phase06/pair_train_curves.csv và train_summary.csv

## checkpoint_drift

**purpose**: Tách đo policy cố định khỏi reward khi cùng học.

**axes_and_units**: Trái:X checkpoint,Y profit/bước;phải:X cuối100episode,Y số state đổi tập greedy/4.

**legend**: Đen mean;whisker trái±std;đường phải mean sốstate đổi.

**aggregation_and_n**: Trái:gộp2vai,rồi2learner trong pair,rồi5pair seed;500episode/vai. Phải:mean10learner thuộc5pair,khôngCI.

**observations**: e0:29.55358±0.19596;e1000:34.48443±1.32679;e2500:34.23232±0.70593;e5000:31.58872±2.75761;tổng612state-change trên500learner-interval;Q-L2 cũng lưuCSV.

**quantitative_comparison**: e0:29.55358±0.19596;e1000:34.48443±1.32679;e2500:34.23232±0.70593;e5000:31.58872±2.75761;tổng612state-change trên500learner-interval;Q-L2 cũng lưuCSV.

**limitations**: Bốn điểm repeated measures,không chọn checkpoint tốt nhất;drift ở state không gặp có thể không đổi return. Không chứng minh nguyên nhân từ opponent.

**data_source**: artifacts/metrics/phase06/q8_summary.csv và policy_drift.csv

## variant_robustness

**purpose**: So policy cũ với retrain khi chỉ đổi kernel nhu cầu.

**axes_and_units**: X:4policy,Y:lợi nhuận giả lập/bước;hai panel kernel khác.

**legend**: Cột xám mean;whisker±sample std qua5seed/panel.

**aggregation_and_n**: 500episode/vai,gộp vai trước;5trainingseed choQ,5scenario panel cho controls;paired delta cùngseed/tape.

**observations**: persistent:retrain−baseline=-1.48087±2.70026;gold:retrain−baseline=-0.80510±3.54276

**quantitative_comparison**: persistent:retrain−baseline=-1.48087±2.70026;gold:retrain−baseline=-0.80510±3.54276

**limitations**: Không so rawreturn giữa kernel như cùng phân phối;controls có thể trùng hành vi. Không bảo đảm retrain thắng;n5 nhỏ,khôngCI/kiểm định.

**data_source**: artifacts/metrics/phase06/variant_seed.csv,variant_summary.csv,variant_deltas.csv
