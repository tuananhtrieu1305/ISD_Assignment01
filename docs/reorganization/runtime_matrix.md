# Runtime cho11 bài — kiểm kê Phase1

Môi trường được giữ nguyên. Các JSON `runtime_torch_metadata.json` và
`runtime_keras_metadata.json` là số đo package hiện có, đọc metadata mà không import framework.
Đây chưa phải kiểm chứng rằng mọi notebook/checkpoint lịch sử chạy đúng trên package mới.

## Môi trường hiện hành

- WSL distro `Ubuntu`, user `tuananh`, Python3.11.17.
- NumPy/PyTorch: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
- Keras/TensorFlow: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`.
- Runtime tài liệu riêng đã có chỉ dùng khi cần về sau; không dựng lại DOCX trong Phase1.
- Không dùng default distro cũ `Ubuntu-24.04`, Windows Python hoặc Anaconda ghi trong notebook cũ.
  Giữ các chỉ dẫn đó trong baseline như lịch sử; thay bằng revision có ghi diff ở Phase2.
- Không chạy bootstrap/doctor cũ vì chúng có thể ghi đè evidence đã khóa. Không pip install,
  nâng package hoặc nhập hai môi trường thành một trong lần kiểm kê này.

| Bài | Nhu cầu code | Cách chạy cần làm ở Phase2 |
|---|---|---|
| A01/A02 | NumPy/pandas/sklearn/joblib, ML truyền thống | Torch env cho xử lý CPU; probe sklearn serialization và feature order trước inference |
| A03 | NumPy scratch + sklearn, custom preprocessor | Torch env; giữ class namespace/source khi load joblib; không chạy fit từ notebook gốc |
| A04 | Cùng notebook có TensorFlow lẫn Torch + NumPy | Kiểm metadata2 env; dùng driver/các cell wrapper tách subprocess theo framework nếu một env không đủ; không tự cài cả hai vào chung env |
| A05 | Keras3/TensorFlow2.21;12 model tự viết, sklearn | Keras env; sửa guard Anaconda trong migration revision, kiểm custom object và shape; không đổi sang pretrained hoặc PyTorch |
| A06 | PyTorch và Keras, openpyxl/joblib/scalers | Tách notebook theo framework hiện có; fundamentals có thể import cả hai nên cần adapter; nguyên processed arrays và scaler |
| tieuluan1 | NumPy CPU serving; notebook đọc metrics; source train cả3 framework | Kế thừa đúng phiên bản; không cài lại requirements cũ vào GPU env; probe model namespace và CRLF artifact hash |
| tieuluan2 | V3 Ch1–5 | Dùng chung runtime/bộ artifact hợp lệ của V3; serving tách catalog Ch6 |
| tieuluan3 | Runtime V3 hiện tại, CPU serving riêng Render | Giữ GPU env cho notebook; không chạy Render build installer trong GPU env; migration cần source/bundle parity |
| agent01 | NumPy Q-learning + Matplotlib | Torch env CPU; notebook này thật sự train5000episode nên không Run All trong migration |
| agent02 | NumPy/pandas/Matplotlib đọc kết quả và source; code simulation riêng | Torch env CPU; notebook44cell chỉ đọc, chỉ Run All ở Phase2 sau path/namespace audit |

## Các khác biệt phải kiểm chứng

README A05 cũ yêu cầu Python3.12/Anaconda, NumPy2.5.3/pandas3.0.5/sklearn1.9.1;
runtime hiện tại NumPy2.4.6/pandas3.0.6/sklearn1.9.0. Phiên bản TensorFlow2.21.0 và
Keras3.15.1 trùng metadata lịch sử. Vì vậy không được coi package có mặt là đã tương thích
serialization hoặc cho kết quả giống hệt. Phase2 cần native-load trên TRAIN/demo input,
so output đã lưu với tolerance khai báo trước; không train lại để thay model lỗi load.

Các notebook A01–A06 có cell fit/train/evaluate và ghi file. Chỉ static-parse chúng trong
Phase1. Notebook results-only cũng có thể có guard đường dẫn hoặc ghi ảnh, nên phải đọc
trước Run All. File nguyên bản vẫn giữ; smoke migration ghi vào thư mục revision riêng.

## Công cụ phục hồi đã dùng

Python WSL đã khóa dùng Git object survey/JSON/AST. Ghi hàng chục nghìn file nhỏ qua WSL
chậm nên chuyển sang Git Windows `archive` + .NET ZIP/SHA streams. Đây không phải tạo runtime
Python Windows. Mỗi payload đối chiếu Git blob SHA1 và SHA256. Git archive phải dùng
`-c core.autocrlf=false -c core.eol=lf` để giữ đúng byte blob; không đổi Git config toàn cục.
Archive thử sai CRLF không được dùng làm baseline; file nguồn đang hoạt động không đổi.
