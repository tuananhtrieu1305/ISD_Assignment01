# Biên bản revision notebook inline-v1 — 01/11/2026

Đã đưa 11 bài về **29 notebook**, mỗi cây `<bài>/notebooks/` có tối đa 4 file. Tiểu luận và Agent02 có implementation thực thi ngay trong cell, gồm các phụ thuộc xử lý dữ liệu, mô hình, loss/optimizer, vòng huấn luyện và đánh giá. Các notebook A01–A03 và Agent01 đã có code trực tiếp và đủ ít file nên giữ nguyên byte.

## Cách gộp

| Bài | Trước | Sau | Nội dung |
|---|---:|---:|---|
| A01 | 1 | 1 | Giữ nguyên |
| A02 | 1 | 1 | Giữ nguyên |
| A03 | 3 | 3 | Giữ ba bài toán |
| A04 | 17 | 3 | DNN dữ liệu bảng; MNIST; CIFAR-10 |
| A05 | 5 | 4 | Cơ bản + so sánh; ba dataset riêng |
| A06 | 9 | 4 | Cơ bản Torch/Keras; customer data + hai framework; stock data + hai framework; so sánh |
| tieuluan1 | 3 | 3 | MLP; CNN; RNN, bổ sung đầy đủ implementation |
| tieuluan2 | 12 | 4 | ML; CNN; RNN–LSTM; KG/RAG |
| tieuluan3 | 18 | 4 | ML + CNN; RNN–LSTM; KG/RAG; Multi-Agent |
| agent01 | 1 | 1 | Giữ nguyên |
| agent02 | 1 | 1 | Thêm toàn bộ implementation trước phần kết quả cũ |

“Trước” đếm entry point trong catalog REORG; notebook output và bản lưu trước revision được chuyển ra provenance. “Sau” đếm đệ quy toàn bộ thư mục notebooks, không dùng thư mục con để né giới hạn.

## Code và khả năng chạy

Notebook có các cell chứa source thật, mỗi hàm/lớp một cell hoặc một nhóm hợp lý, có tiêu đề module. Cell magic `%%inline_module` khai báo ngay trong notebook để giữ namespace, import tương đối và tên lớp serialized. Nó chỉ biên dịch/chạy phần code trong cell. Namespace riêng chặn tìm implementation qua đường dẫn `.py`; hàm sau khi khai báo có `co_filename` bắt đầu bằng `<notebook>/`.

Các import framework ở cấp module được tách theo kernel: NumPy/PyTorch trong venv Torch, NumPy/Keras trong venv Keras. Với registry driver có cả hai framework, tên class của framework không hoạt động được đặt `None`, không nhập lẫn hai runtime. Source của từng hàm/lớp gốc giữ AST nguyên vẹn; hai kernel được kiểm riêng.

Đây là revision cách trình bày và chạy notebook. Code `.py` gốc được giữ cho backend, checkpoint và bằng chứng khoa học. Sửa cell notebook không tự cập nhật serving bundle. Notebook vẫn cần dataset/config/runtime view của repository, không phải một file độc lập chứa mọi tài nguyên.

Mặc định tắt các entry point thí nghiệm lịch sử bằng `RUN_EXPERIMENTS=False`; `RUN_TRAINING` và `RUN_TEST` đều False. Không train hoặc mở scientific TEST để kiểm việc gộp. Các output cũ nằm trong phần thực hành có nhãn lịch sử. Ví dụ forward mới ở notebook neural chỉ dùng tensor synthetic và weights khởi tạo, không optimizer step và không phải kết quả dataset thật. Một thí nghiệm mới cần revision/output riêng trước khi chạy train/evaluate.

## Cập nhật liên quan

- `project.json`, README từng bài và README root trỏ đến danh sách mới.
- 18 bản tải notebook của 8 web đơn giản khớp byte với notebook hiện hành; các link task đã đổi. Sửa cả link Oxford Pets của A05 vốn trỏ vào notebook cơ bản.
- Giao diện và serving bundle ba tiểu luận giữ nguyên, không build/deploy lại cho thay đổi notebook.
- Runner ghi notebook chạy mới vào `artifacts/notebook_runs/`, tránh tăng số file ở `notebooks/`.
- Verifier hiện hành kiểm các handoff REORG cũ qua archive đúng hash và kiểm riêng revision mới. Không viết lại handoff, lock hoặc seal cũ.

## Bằng chứng nghiệm thu

- [static_check.json](static_check.json): 29 notebook hợp lệ về schema/AST; **1.317 định nghĩa hàm/lớp** khớp AST gốc; 143 file notebook/config/runner trước revision được kiểm SHA-256. Source gốc từ 147 file Python riêng được đối chiếu.
- [execution.json](execution.json): **38 lượt chạy** source inline trong process IPython mới theo đúng framework, tất cả PASS. Các lượt PASS tái sử dụng theo SHA chỉ khi notebook không đổi. A01–A03 và Agent01 giữ nguyên được kiểm tĩnh, không Run All vì chứa huấn luyện lịch sử.
- [kernel_check.json](kernel_check.json): ba lượt qua runner thật với kernel Jupyter mới: A06 customer/Keras, tiểu luận3 RNN–LSTM/Torch và Agent02/Torch, không có error output. Notebook kết quả ở artifacts/notebook_runs.
- [web_check.json](web_check.json): 18 HTTP download trả 200, đúng SHA/byte notebook canonical; link và hash trong data.js khớp bản tải.
- [verification.json](verification.json): đối chiếu 107 record handoff của ba phase REORG, source frontend/dist và serving archive/Python hiện hành; không có thay đổi source/model/raw/metric/prediction/seal/report khoa học.
- Ruff `F,E9` PASS cho các helper revision, runner và verifier. Không format source đã khóa.

Các bước kiểm chỉ khai báo code, đọc output đã lưu và forward tensor synthetic. **Số optimizer update mới = 0; scientific TEST forward mới = 0.** Không đổi môi trường, tải dataset, commit, push hoặc deploy.

Bản gốc: [backup.json](backup.json) và [presentation_backup.json](presentation_backup.json). File hiện hành: [manifest.json](manifest.json). Cách dùng và kernel: [README.md](README.md).
