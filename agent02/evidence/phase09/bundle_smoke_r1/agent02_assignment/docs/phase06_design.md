# Phase 6 — thiết kế trước thí nghiệm

Ngày24/10/2026. Phạm vi câu8/9, theo protocol_v1 đã khóa ở phase2. Kết quả phase5
đã mở nhưng không dùng thay tham số, seed, kernel, số episode hoặc chọn policy.

15 market train runs đăng ký trước:5 two_learners(IID) và10 retrain(persistent/Gold).
Mỗi run5.000×20, fresh zeroQ, learning baselineα0,1/γ0,9/epsilon0,2 decay0,995 min0,02.
Hai learner có policyRNG channel3/4, environment demand/sales channel0/1/2 như core.
Cả hai chọn action từ snapshot cũ trước step; cập nhật sau nhận reward, terminal không bootstrap.
Checkpoint cả Q/RNG/log/visits mỗi100episode; chỉ explicit resume run chưa complete.

Gold: đọc XLSX snapshot đúng hash, chỉ lấy giá trước/đến cutoffTRAIN2006-08 từ split
contract đã khóa; prefix bao gồm lịch sử1960 dùng làm input trước targetTRAIN1962.
Đọc nhãn tháng trước giá, dừng ngay nhãn đầu sau cutoff. Không fit giá validation/TEST.
Regime1 nếu giá tăng so tháng liền trước, còn lại0; missing/gap không điền hoặc nối.
Transition chỉ giữa hai regime ở hai tháng liền nhau, Laplace+1 mỗi ô như protocol2.
Kernel hiệu chỉnh nhu cầu giả lập, không phải cầu vàng thực đo; vintage có thể được
chỉnh sửa hồi tố, không tuyên bố backtest giao dịch hoặc nhân quả giá→nhu cầu.
Persistent giữ chế độ0,9; cả hai kernel reset nhu cầu Bernoulli0,5 như baseline.
Chỉ đổi kernel, giữ giá/reward/conversion/rule/action/state/budget.

Đánh giá mới160 claim,500episode/claim×20step, Q đóng băng, no exploration, random tie:

- Q8:5 pair run×2 learner×4checkpoint(0,1000,2500,5000)×2physicalrole=80claim.
  Fixed opponent luôn là rule gốc, cùng IID tape2000000+seed; không đánh giá hai
  learner cùng chạy để gọi đó là môi trường cố định. Checkpoint là repeated measures,
  2learner trong cùng pair phụ thuộc nhau. Gộp role, rồi gộp learner trong pair trước
  mean/sample std qua5pair seed. Lưu riêng từng learner để thấy bất đối xứng.
  Policy changes/Qdistance giữa checkpoint và fixed-opponent return chỉ mô tả drift;
  không tự chứng minh nguyên nhân non-stationarity hoặc hội tụ.
- Q9:2kernel×5seed×4policy(baselineIIDfrozen,retrained,rule,no_discount)×2role=80claim.
  Same tape2000000+seed trong mỗi kernel, kernel khác tạo demand khác. IIDfinal đã
  có ở phase5 chỉ đọc để tham chiếu, không chạy lại. Đối chứng n5 là5scenario panel.
  Gộp role trước, paired delta retrain−baseline theo seed rồi mean/sample std(ddof1).
  Không chọn checkpoint hoặc tune từ score. Không CI/bootstrap mới.

Train declaration pin source/test/protocol/Goldkernel trước train. Eval declaration
pin chính source train và160job/Qfile/checkpoint/scenario trước final. JournalPhase6
riêng, exclusive claim trước forward,count1, failed/partial giữ nguyên không replay.
Reuse frozen evaluator Phase5 có sẵn hỗ trợ MarketConfig.kernel, không sửa evaluator.
Auditor/bảng/hình sau đó chỉ saved outputs. Không chạy TEST V3 hoặc làm phase7.

Hình dự kiến:giá/transitionGold, train2learnerMA100, checkpoint drift/return,
robustnesspairedreturn. Mỗi hình có trục/đơn vị,n,nguồn/aggregate,số đo và giới hạn.
≥3 hạn chế cần nêu:conversion giả định,demandproxy/statealiasing,không tồn kho/
dị biệt khách hàng,doanh số hai shop không độc quyền,horizon thiếu time trong state.
