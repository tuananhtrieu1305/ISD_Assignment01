# Nghiệm thu AG02 phase 2 — 24/10/2026

Đã hoàn thành môi trường/agents, cơ chế train–resume, đánh giá DEV đóng băng và
protocol trước train. Mọi đầu ra mới nằm trong `agent02_assignment/`. Bài V3,
bài DISCOVERING AI Agent, nguồn thầy và runtime hiện có được giữ nguyên.

## Những gì đã làm

- Giữ REF exact-byte; CONTROLLED tách RNG nhưng giữ luật môi trường/reward và
  Q-learning. Hai hành động được chọn trước step, không nhìn hành động hiện tại
  của đối thủ. Cả 4 joint actions ở hai mức nhu cầu đã kiểm.
- Kiểm Q câu 3 bằng 4,65; terminal bằng 4,2; lãi mỗi món 5/3 ở câu 5.
- Log episode/epsilon/reward, Q, tập action greedy, lượt thăm, trace 20 dòng,
  cấu hình/source hash và run ID. Checkpoint lưu cả RNG, không chỉ Q.
- Kiểm run chia đoạn 3+4 episode giống hệt run liên tục 7 episode; bật/tắt trace
  không đổi kết quả. Disk guard dừng ở ranh giới episode.
- DEV evaluator dùng tape độc lập, role0/1, sao Q chỉ đọc; không cập nhật Q/RNG
  train. Không có lệnh full-train/final trong CLI phase 2.
- Protocol khóa 56 market run / 61 learner instance qua các phase sau, 5 cấu
  hình chính, 5 seed, train 5.000×20 và final 500 episode **mỗi vai**. Gold chỉ
  khóa cách hiệu chỉnh và ranh giới TRAIN 08/2006, chưa ước lượng kernel.

## Kiểm thử và smoke thực tế

Nghiệm thu **103 test PASS / 0 skip** (gồm 29 regression phase 1 và 74 phase 2).
Coverage tổng **95,43%** trên sáu module mới: environment/agents, training,
frozen DEV, REF adapter, protocol và smoke runner. Đây không phải coverage code
thầy, notebook/báo cáo hay toàn project. Chi tiết line/branch nằm trong receipt.
Các module lõi riêng đạt trên 90% dòng và nhánh. Lint source mới và parser/CLI PASS.

Smoke đã chạy **100 episode REF + 100 CONTROLLED**, tổng 4.000 market step train
thử; DEV 3 episode mỗi vai, thêm 120 market step. Đây là kiểm kỹ thuật, không
đưa Q/reward smoke vào bảng kết quả báo cáo và không thay baseline seed42/11.

| Số đo smoke | Giá trị |
|---|---:|
| Thời gian train REF (100 episode) | 0,0752 giây |
| Thời gian train CONTROLLED (100 episode) | 0,2841 giây |
| Artifact trước completion receipt | 99.033 byte (~96,7 KiB) |
| Checkpoint CONTROLLED sau 100 episode | 48.483 byte |
| Ổ C trống trước/sau | khoảng 36,67 GiB |
| Biểu đồ tạo | 0 |

Thời gian trên chỉ bao quanh lời gọi train CPU, không gồm import, I/O/evaluation
và kiểm thử. Ngoại suy tuyến tính một run baseline 5.000 episode khoảng 3,76 giây
REF hoặc 14,20 giây CONTROLLED. Nếu 55 run CONTROLLED đều có chi phí như baseline,
cộng 1 REF thì khoảng **13,1 phút train thuần**; đó chỉ là dự trù từ một smoke
ngắn, chưa đo các track hai learner/trạng thái lớn, chưa phải thời gian hoàn tất
cả bài. Final evaluation, notebook, biểu đồ và audit cần ngân sách riêng.

Nếu lưu checkpoint đầy đủ chứa log tích lũy mỗi 100 episode, 50 snapshot/run có
thể khoảng 62 MB/run theo ngoại suy hiện tại; toàn ma trận có thể hơn 3 GB trước
output khác. Không coi 99 KB smoke là dung lượng của toàn nghiên cứu. Giữ guard
5 GiB, đo lại bằng run đầy đủ ở phase 3; không thay budget để ép kết quả.

## Lỗi đã bắt và phạm vi kết luận

Test-first có XML RED trước implementation. Lượt smoke CLI đầu tiên dừng trước
khi tạo claim/chạy train: đối chiếu Python tuple với list đọc từ JSON khiến
protocol tương đương bị coi là khác. Đã chuẩn hóa JSON và so canonical hash;
test hồi quy kiểm ghi/đọc lại cùng protocol và từ chối protocol thật sự thay đổi.
Không thay nội dung/cấu hình protocol đã ghi, không có thí nghiệm bị chạy lặp.
Auditor lần đầu cũng từ chối checkpoint vì so tuple/list thô sau khi đọc JSON;
đã chuyển riêng đối chiếu auditor sang canonical hash. Checkpoint/Q/RNG smoke
giữ nguyên hash; không train hay forward lại để xử lý lỗi kiểm tra này.

Smoke completion xác nhận checkpoint roundtrip chính xác, DEV giữ nguyên training
state, không gọi reference main, không final evaluation, không mở TEST V3. SHA
nguồn, 9 input phase1 và 7 asset đã chọn được đối chiếu lại. Không cài/chỉnh env,
không tải dataset, không tạo notebook server hay tiến trình train chờ nền.

Lý thuyết và bảng hàm ngắn ở `model_core_v1.md`. Mọi hình các phase sau cần phần
giải thích theo template, không chỉ chèn ảnh. Chưa có kết luận Q-learning hơn
agent luật, hội tụ tối ưu hoặc hiệu quả trên thị trường thật.

Bước tiếp theo: **`làm AG02 phase 3`**. Chi tiết chạy/khôi phục và giới hạn khóa ở
`phase02_operations.md`; bằng chứng máy đọc trong `evidence/phase02/verification.json`.
