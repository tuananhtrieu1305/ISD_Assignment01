# Mô hình Agent02 và các hàm chính — phase 2

## Bài toán rất ngắn

Hai cửa hàng chọn cùng lúc: giữ giá (0) hoặc giảm 20% (1). Agent học dùng trạng thái
`(nhu cầu hiện tại, hành động trước của đối thủ)`. Có 4 trạng thái và 2 hành động,
nên Q chỉ có 8 giá trị. Agent theo luật chỉ giảm giá khi nhu cầu cao và đối thủ
đã giảm ở bước trước; ba trạng thái còn lại giữ giá. Agent luật không học.

Một episode có 20 bước, bắt đầu với nhu cầu xác suất 0,5 và lịch sử hành động bằng 0.
Nhu cầu thấp/cao tương ứng 10/20 khách. Xác suất mua tăng theo nhu cầu và việc tự
giảm giá, giảm khi đối thủ giảm giá; dùng đúng hệ số trong code thầy. Hai cửa hàng
lấy mẫu doanh số riêng, không chia một tổng khách mua cố định. Vì vậy đây không
phải trò chơi tổng bằng không, tổng doanh số không được gọi là thị phần độc quyền.

Lãi mỗi món khi giữ giá là `10 − 5 = 5`; khi giảm giá là `10 × 0,8 − 5 = 3`.
Reward là số món bán được nhân lãi mỗi món, đơn vị tiền giả lập. Bán nhiều hơn
không tự động đồng nghĩa có lợi nhuận cao hơn.

## Q-learning, chỉ giữ phép tính cần thiết

Q lưu ước lượng lợi ích khi chọn một hành động trong một trạng thái. Sau mỗi bước,
agent dịch Q cũ một phần alpha về phía reward hiện tại cộng giá trị tương lai đã
chiết khấu gamma. Ở bước cuối episode không còn giá trị tương lai.

Câu 3 của đề cho số giả định: Q cũ 4, reward 6, Q tốt nhất kế tiếp 5, alpha 0,1,
gamma 0,9. Mục tiêu `6 + 0,9 × 5 = 10,5`; sai lệch `10,5 − 4 = 6,5`;
Q mới `4 + 0,1 × 6,5 = 4,65`. Nếu đó là bước cuối, Q mới chỉ là
`4 + 0,1 × (6 − 4) = 4,2`. Đây là phép kiểm, không phải kết quả train đo được.

Epsilon là xác suất thử hành động ngẫu nhiên khi học. Baseline bắt đầu 0,2,
giảm theo episode với hệ số 0,995, không dưới 0,02. Khi các Q gần bằng nhau,
agent bốc thăm có seed trong tập hành động đồng hạng; không mặc định luôn chọn 0.
Khi đánh giá, tắt exploration nhưng vẫn giữ cách xử lý đồng hạng đã khai báo.

## Các hàm làm gì

| Thành phần | Vai trò và đầu ra |
|---|---|
| `MarketConfig`, `LearningConfig` | Kiểm tra cấu hình, số bước, giá, discount, kernel và tham số học; từ chối giá trị sai/NaN. |
| `conversion(demand, own, other)` | Tính xác suất mua theo luật thầy, chặn trong 0,05–0,95. Với đầu vào nhị phân hợp lệ mặc định, xác suất đã nằm trong giới hạn. |
| `margin(config, action)` | Tính lãi mỗi món 5 hoặc 3 ở baseline; không phải reward cả bước. |
| `MarketEnv.reset()` | Bắt đầu episode, đặt lại lịch sử; trả cùng nhu cầu cho hai agent. |
| `MarketEnv.step(actions)` | Nhận cả hai hành động đã chọn, tính xác suất/doanh số/reward, cập nhật lịch sử và nhu cầu; trả trạng thái mới, reward và cờ kết thúc. |
| `RuleAgent.act(state)` | Áp đúng 3 nhánh luật của thầy, rút gọn tương đương thành chỉ giảm ở `(1,1)`. |
| `QAgent.act(...)` | Chọn epsilon-greedy hoặc greedy có bốc thăm đồng hạng; RNG chính sách riêng. |
| `QAgent.learn(...)` | Chỉ cập nhật đúng một ô Q; không bootstrap ở terminal. |
| `TrainSession.run_chunk(...)` | Chạy số episode giới hạn, chọn cả hai hành động trước step; ghi reward, epsilon, đếm hành động và lượt thăm trạng thái–hành động. |
| `checkpoint()` / `from_checkpoint()` | Lưu/khôi phục Q, cấu hình, episode, log, lượt thăm và toàn bộ RNG; kiểm hash và số đếm. |
| `Tape.generate(...)` | Tạo nhu cầu và số ngẫu nhiên khách hàng theo từng episode, không phụ thuộc hành động của policy. |
| `evaluate_dev(...)` | Sao chép Q chỉ đọc, chạy DEV với tape ghép cặp, đổi vai bằng `role`; không gọi learn, không nhận partition final. |
| `load_reference()` / `reference_smoke()` | Chỉ import bản code thầy đúng đường dẫn/hash; gọi hàm train giới hạn tối đa 100 episode cho kiểm tra. Không gọi main. |

`controlled.py` chứa môi trường/agents; `training.py` quản lý tiến trình;
`evaluation/frozen.py` tách đánh giá; `phase02.py` chỉ điều phối smoke và log.
Notebook/báo cáo các phase sau sẽ gọi các hàm này thay vì chép thuật toán khác.

## REF và CONTROLLED

REF giữ nguyên 25.001 byte code thầy và thứ tự gọi RNG. CONTROLLED giữ luật mô
phỏng, reward, budget và thuật toán nhưng tách RNG nhu cầu, doanh số từng shop,
chính sách. Do đó không yêu cầu trajectory/Q của hai track phải giống nhau với
cùng một seed; không cộng hai track thành các replicate của cùng thí nghiệm.
Fixture REF 3 episode đã đối chiếu wrapper với lời gọi trực tiếp hàm gốc.

Khi DEV đánh giá, mỗi khách có một số ngẫu nhiên U; mua khi U nhỏ hơn xác suất mua.
Cách đếm này có cùng phân phối Binomial với code gốc. Dùng lại tape giữa các cấu
hình giảm khác biệt do tình huống ngẫu nhiên. Chạy cả vai 0 và 1 để không thiên
vị vị trí cửa hàng. Q và RNG train phải giữ nguyên trước/sau đánh giá.

## Giới hạn cần nói rõ trong tiểu luận

Quan sát hai biến không chứa lịch sử hành động của chính agent hoặc số bước còn
lại. Chính sách đối thủ phụ thuộc lịch sử nên quan sát này có thể gộp những tình
huống khác nhau; không khẳng định bài toán quan sát cục bộ luôn là MDP đầy đủ hay
Q chắc chắn hội tụ tối ưu. Phase 7 mới kiểm thiết kế trạng thái bổ sung đã đăng ký.

Gold chỉ được dùng để hiệu chỉnh một kernel nhu cầu giả lập ở phase 6, từ prefix
TRAIN đã khóa đến 08/2006. Phase 2 chỉ đọc metadata ranh giới, chưa đọc giá để fit
kernel. CDC/Ames không biến thành môi trường điều trị/mua bán chỉ từ nhãn tĩnh.

Phase 2 không có biểu đồ và không kết luận agent nào tốt hơn. Mọi hình từ phase
3 trở đi cần giải thích theo `figure_explanation_template.md`: trục, đơn vị,
nguồn, cách gộp, số mẫu, xu hướng, chênh lệch và giới hạn. Giữ lý thuyết ngắn,
dùng ví dụ trên; không thêm công thức nặng nếu không giúp trả lời câu hỏi.
