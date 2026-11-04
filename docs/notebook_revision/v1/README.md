# Notebook hiện hành — bản gộp ngày 01/11/2026

Mỗi bài có tối đa **4 notebook trong toàn bộ cây `notebooks/`**. Tổng cộng 29 notebook cho 11 bài. Đây là revision sau REORG; biên bản ba phase REORG vẫn giữ nguyên làm lịch sử.

| Bài | Số file | Cách chia |
|---|---:|---|
| A01 | 1 | Giữ notebook bài A01 |
| A02 | 1 | Giữ notebook bài A02 |
| A03 | 3 | Customer behavior, tiểu đường, giá nhà |
| A04 | 3 | DNN ba dataset dạng bảng; MNIST; CIFAR-10 |
| A05 | 4 | CNN cơ bản + so sánh; EuroSAT; Oxford Pets; CDC Diabetes |
| A06 | 4 | RNN cơ bản cả hai framework; customer behavior; stock; so sánh |
| tieuluan1 | 3 | MLP; CNN; RNN — mỗi file đủ dữ liệu, ba implementation và train/evaluate |
| tieuluan2 | 4 | ML; CNN; RNN–LSTM; Knowledge–RAG |
| tieuluan3 | 4 | ML + CNN; RNN–LSTM; Knowledge–RAG; Multi-Agent |
| agent01 | 1 | Q-learning mê cung |
| agent02 | 1 | Toàn bộ code môi trường, agent, huấn luyện và phân tích kết quả |

Các tiểu luận và Agent02 có **implementation thật ngay trong code cell**: lớp mô hình, forward/backward, loss, optimizer, vòng train, đọc/chia dữ liệu, đánh giá và các hàm phụ thuộc của chúng. Notebook không dùng `%run`, `exec(read_text(...))` hoặc chỉ `display(Code(...))` để thay cho phần implementation này. Bạn không cần mở file `.py` để xem các thuật toán. Source `.py` gốc vẫn cần cho backend/web, load checkpoint và bằng chứng thí nghiệm đã khóa nên được giữ lại nguyên trạng.

## Đọc và sửa code

Chạy cell khởi tạo trước, rồi đọc từ trên xuống: mỗi module có tiêu đề, sau đó là imports/hằng số và từng hàm/lớp trong cell riêng. `%%inline_module` ở đầu cell là cell magic nhỏ được khai báo ngay trong notebook. Nó chạy **nội dung cell đó** trong namespace riêng, giúp các lớp trùng tên giữa ba framework và các import tương đối hoạt động đúng. Nó không đọc implementation từ `.py`. Các hàm đã nạp được kiểm tra có nguồn `<notebook>/...`.

Khi sửa một hàm/lớp, chạy lại cell đó và các cell sử dụng nó. Nếu module khác đã `from ... import ...`, hãy chạy lại cell import đó, hoặc Restart Kernel và chạy từ đầu. Mỗi bài dùng kernel mới, tránh trộn các package tên `src` của hai bài.

Các nhóm framework dùng chung dữ liệu và notebook, nhưng chạy trong **hai kernel riêng**. Trong kernel Torch, cell NumPy/PyTorch hoạt động và cell Keras được bỏ qua; trong kernel Keras thì ngược lại. Bạn vẫn đọc được toàn bộ code của cả ba implementation trong cùng file. Không cài TensorFlow và Torch trộn vào một môi trường để chạy các cell này.

## Kernel và lệnh chạy

Mở VS Code qua WSL **Ubuntu**, user `tuananh`, chọn:

- NumPy/PyTorch: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
- Keras/TensorFlow: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`.

A05 dùng kernel Keras; Agent02 dùng Torch/NumPy. A04, A06 và các notebook neural của ba tiểu luận hỗ trợ hai kernel. KG/RAG/Multi-Agent dùng Torch/NumPy làm kernel mặc định, không cần mở TensorFlow để đọc bài.

Từ root `C:\DATA\assign` trong PowerShell:

```powershell
./scripts/run_assignment.ps1 -Project A06 -Inspect
./scripts/run_assignment.ps1 -Project A06 -Notebook notebooks/02_Customer_Behavior.ipynb -Framework torch -Cpu
./scripts/run_assignment.ps1 -Project A06 -Notebook notebooks/02_Customer_Behavior.ipynb -Framework keras -Cpu
./scripts/run_assignment.ps1 -Project tieuluan3 -Notebook notebooks/02_RNN_LSTM.ipynb -Framework torch -Cpu
```

Runner dùng các môi trường đã có, không cài dependency. Nó ghi notebook đã chạy vào `<bài>/artifacts/notebook_runs/`, không tạo thêm file trong `notebooks/`. Notebook vẫn cần dataset/config/runtime view của repository; file tải riêng từ web không chứa toàn bộ dataset và checkpoint.

## Kết quả cũ và lượt chạy mới

Các notebook vừa gộp mặc định có `RUN_EXPERIMENTS=False`, `RUN_TRAINING=False`, `RUN_TEST=False`. Phần code thí nghiệm lịch sử được đặt sau cờ để bạn đọc đầy đủ mà không ghi đè split, metric, checkpoint hoặc mở lại TEST. Output giữ từ notebook cũ được đánh dấu là output lịch sử; nó không phải output của lần kiểm tra revision này. Một số notebook neural có ví dụ forward tensor synthetic nhỏ để chạy trực tiếp code inline; đây không phải kết quả trên dataset thật.

Không bật các cờ lịch sử để chạy lại thí nghiệm đã khóa. Nếu cần huấn luyện mới, tạo revision thí nghiệm mới với output riêng và protocol phù hợp. Thay notebook không tự đổi serving bundle của web.

Bản trước khi gộp, kể cả các notebook output cũ, được giữ nguyên tại `<bài>/provenance/notebooks_before_inline_v1/notebooks/`; manifest SHA-256 ở [backup.json](backup.json). Các bản notebook tải web trước revision được giữ riêng trong `presentation_before/`, ghi nhận ở [presentation_backup.json](presentation_backup.json).

Danh sách file mới: [manifest.json](manifest.json). Kiểm chứng source/schema: [static_check.json](static_check.json). Kết quả chạy cell: [execution.json](execution.json). Trạng thái bàn giao: [checkpoint.json](checkpoint.json).
