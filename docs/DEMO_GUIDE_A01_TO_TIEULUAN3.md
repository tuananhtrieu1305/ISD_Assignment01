# Hướng dẫn chạy demo A01–A06 và tiểu luận 1–3

Tài liệu này hướng dẫn chạy lần lượt chín web demo trong repository hiện tại. Các lệnh chính được viết cho **Git Bash** và chạy từ thư mục gốc `C:\DATA\assign`.

## 1. Chuẩn bị chung

Yêu cầu hiện có của project:

- Windows đã bật WSL và có distro `Ubuntu`.
- User Linux là `tuananh`.
- Runtime Torch/NumPy đã có tại `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
- Ba frontend tiểu luận đã có sẵn `dist/`; không cần build lại nếu chỉ chạy demo.
- Không dùng Python Windows hoặc Anaconda.
- Git Bash không đọc được cú pháp `.ps1`; dùng wrapper `scripts/run_web_gitbash.sh` được cung cấp bên dưới.

Mở Git Bash và chuyển về root:

```bash
cd /c/DATA/assign
```

Kiểm tra nhanh một bài trước khi chạy:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PWD/scripts/run_assignment.ps1")" -Project A01 -Inspect
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PWD/scripts/run_assignment.ps1")" -Project A01 -ListDatasets
```

Quy tắc vận hành:

1. Mỗi terminal chạy một web và giữ terminal đó mở.
2. Nhấn `Ctrl+C` trong terminal để dừng web trước khi chuyển bài.
3. Nếu cổng mặc định đang bận, thêm số cổng vào cuối lệnh, ví dụ `./scripts/run_web_gitbash.sh A01 9000` và mở `http://127.0.0.1:9000`.
4. Có thể kiểm tra backend bằng `curl http://127.0.0.1:<port>/health`.
5. A01–A03 có inference CPU. A04–A06 là replay kết quả đã lưu, không được giới thiệu là vừa huấn luyện hoặc dự đoán live.
6. Không bật lại cờ training/TEST trong notebook chỉ để trình diễn web.
7. Wrapper Git Bash chỉ chuyển đúng tham số sang runner PowerShell hiện có; backend thực tế vẫn chạy trong WSL Ubuntu.

## 2. Bảng lệnh nhanh

| Bài | Lệnh Git Bash | URL mặc định | Chế độ |
|---|---|---|---|
| A01 | `./scripts/run_web_gitbash.sh A01` | http://127.0.0.1:8011 | Form nhập → 5 mô hình |
| A02 | `./scripts/run_web_gitbash.sh A02` | http://127.0.0.1:8012 | Form nhập → 5/6 mô hình |
| A03 | `./scripts/run_web_gitbash.sh A03` | http://127.0.0.1:8013 | Form nhập → Improved DNN |
| A04 | `./scripts/run_web_gitbash.sh A04` | http://127.0.0.1:8014 | Replay so sánh đã lưu |
| A05 | `./scripts/run_web_gitbash.sh A05` | http://127.0.0.1:8015 | Replay CNN đã lưu |
| A06 | `./scripts/run_web_gitbash.sh A06` | http://127.0.0.1:8016 | Replay RNN/LSTM đã lưu |
| tieuluan1 | `./scripts/run_web_gitbash.sh tieuluan1` | http://127.0.0.1:8017 | React/Python, Chương 1–4 |
| tieuluan2 | `./scripts/run_web_gitbash.sh tieuluan2` | http://127.0.0.1:8018 | React/Python, Chương 1–5 |
| tieuluan3 | `./scripts/run_web_gitbash.sh tieuluan3` | http://127.0.0.1:8019 | React/Python, Chương 1–6 |

## 3. Demo A01

Chạy:

```bash
./scripts/run_web_gitbash.sh A01
```

Mở http://127.0.0.1:8011.

Luồng trình diễn đề xuất:

1. Chọn **Pima · Tiểu đường**.
2. Nhập đường huyết, BMI, tuổi, số lần mang thai, huyết áp và chỉ số di truyền trong sáu ô nhập.
3. Bấm **Kiểm tra và so sánh**.
4. Xem năm thẻ kết quả Logistic Regression, KNN, Decision Tree, Random Forest và SVM cùng mức đồng thuận. Thay đường huyết/BMI rồi kiểm tra lại để thấy kết quả thay đổi.
5. Chuyển sang **Giá nhà Việt Nam**, nhập diện tích/số tầng/số phòng và so sánh năm mô hình hồi quy.
6. Mở liên kết notebook nếu cần chỉ ra code nguồn.

Điểm cần nói: A01 minh họa các mô hình ML cơ bản cho một bài toán phân loại và một bài toán hồi quy.

## 4. Demo A02

Chạy:

```bash
./scripts/run_web_gitbash.sh A02
```

Mở http://127.0.0.1:8012.

Luồng trình diễn đề xuất:

1. Xem lại hai bài toán **Pima · Tiểu đường** và **Giá nhà Việt Nam**.
2. Chuyển sang **Hành vi khách hàng**.
3. Giới thiệu nhóm đặc trưng hồ sơ, giao dịch, phiên truy cập và đánh giá sản phẩm.
4. Thay các ô tuổi, giao dịch, chi tiêu hoặc mức tương tác rồi bấm **Kiểm tra và so sánh** để xem sáu mô hình.
5. Form khách hàng giữ các trường kỹ thuật ít dùng ở giá trị mẫu; số trường này được ghi dưới form. Hai tab tiểu đường/giá nhà vẫn so sánh năm mô hình.

Điểm cần nói: A02 mở rộng từ dữ liệu y tế/giá nhà sang dữ liệu hành vi nhiều nhóm đặc trưng.

## 5. Demo A03

Chạy:

```bash
./scripts/run_web_gitbash.sh A03
```

Mở http://127.0.0.1:8013.

Luồng trình diễn đề xuất:

1. Chọn **Hành vi khách hàng**, nhập tuổi, giao dịch, chi tiêu và tương tác; bấm **Kiểm tra**.
2. Chọn **CDC · Tiểu đường**, thay các yếu tố sức khỏe. Tuổi là nhóm CDC 1–13, thu nhập là nhóm 1–8.
3. Chọn **Giá nhà**, nhập diện tích, mặt tiền, đường vào, số tầng, phòng ngủ, phòng tắm và địa điểm.
4. Bấm **Kiểm tra** để xem dự đoán Improved DNN trên input mới.
5. Backend A03 hiện chỉ phục vụ một Improved DNN mỗi bài toán; giao diện không giả lập thêm các mô hình từ bảng metric cũ.

Điểm cần nói: A03 chuyển từ mô hình cổ điển sang DNN và cho thấy mô hình sâu không tự động tốt hơn ở mọi metric.

## 6. Demo A04

Chạy:

```bash
./scripts/run_web_gitbash.sh A04
```

Mở http://127.0.0.1:8014.

Luồng trình diễn đề xuất:

1. Chọn bài toán, chọn chỉ số cần đối chiếu rồi bấm **Xem kết quả**.
2. Xem các thẻ mô hình được sắp theo chỉ số đã chọn.
3. A04 hiện chỉ có bảng kết quả tổng hợp phục vụ web, chưa có form dự đoán từ input mới. Không giới thiệu thao tác này là chạy model trên một mẫu mới.

Lưu ý: A04 là **replay comparison đã lưu**, không có endpoint inference live.

## 7. Demo A05

Chạy:

```bash
./scripts/run_web_gitbash.sh A05
```

Mở http://127.0.0.1:8015.

Luồng trình diễn đề xuất:

1. Chọn **EuroSAT · Vệ tinh**, giới thiệu bài toán phân loại ảnh viễn thám.
2. Chọn **Oxford-IIIT Pet**, giới thiệu phân loại giống chó/mèo.
3. Chọn **CDC · Ba lớp**, giải thích cách CNN được áp dụng lên biểu diễn dữ liệu tiểu đường ba lớp trong assignment.
4. Chọn một mẫu rồi bấm **Xem kết quả**: giao diện hiện nhãn thật và dự đoán đã lưu của bốn kiến trúc CNN.
5. Dùng liên kết notebook để chỉ ra phần code CNN và hàm train/evaluate.

Lưu ý: A05 là replay kết quả CNN đã lưu; không train ảnh trong lúc demo.

## 8. Demo A06

Chạy:

```bash
./scripts/run_web_gitbash.sh A06
```

Mở http://127.0.0.1:8016.

Luồng trình diễn đề xuất:

1. Chọn **Online Retail II · Khách hàng** để xem dự đoán hành vi từ chuỗi thời gian.
2. Chọn khách hàng rồi bấm **Xem kết quả**, đối chiếu dự đoán nguy cơ rời bỏ của Keras và PyTorch.
3. Chọn **AAPL · Giá đóng cửa** để xem dự báo chuỗi giá cổ phiếu.
4. Chọn ngày rồi bấm **Xem kết quả**, đối chiếu dự báo Keras/PyTorch với giá thực tế và baseline dùng giá gần nhất.
5. Mở notebook **So sánh framework** để chỉ ra sự khác nhau giữa scratch, Keras và PyTorch.

Lưu ý: A06 hiển thị dự đoán/kết quả đã lưu; không mô tả nó là dữ liệu thị trường thời gian thực.

## 9. Demo tiểu luận 1

Chạy:

```bash
./scripts/run_web_gitbash.sh tieuluan1
```

Mở http://127.0.0.1:8017.

Luồng trình diễn đề xuất:

1. **Trang chủ**: giới thiệu lịch sử AI và cấu trúc bốn chương.
2. **ML** (`/ml`): chạy bài toán tiểu đường, xem dự đoán và so sánh mô hình.
3. **CNN** (`/cnn`): chạy/xem demo EuroSAT và giải thích đầu vào ảnh–đầu ra lớp.
4. **RNN** (`/rnn`): chọn use case chuỗi, xem kết quả RNN và baseline.
5. Kết thúc bằng việc nhấn mạnh đây là bản tiểu luận 1 gồm Chương 1–4, chưa có KG–RAG hay multi-agent.

Mẫu demo của tiểu luận 1 có thể dùng TRAIN sample hoặc fixture. Không giới thiệu fixture là hàng TEST mới.

## 10. Demo tiểu luận 2

Chạy:

```bash
./scripts/run_web_gitbash.sh tieuluan2
```

Mở http://127.0.0.1:8018.

Luồng trình diễn đề xuất:

1. **Chương 1 – Tổng quan**: Iris, MNIST và ImageNet minh họa các giai đoạn phát triển AI.
2. **Chương 2 – ML**: CDC Diabetes, Ames Housing và Bank Marketing.
3. **Chương 3 – CNN**: IDRiD, EuroSAT và CIFAR-10; so sánh scratch, Keras, PyTorch.
4. **Chương 4 – RNN–LSTM**: giá vàng World Bank, giá nhà BIS và điện năng hộ gia đình.
5. **Chương 5 – KG–RAG**: MedQuAD Diabetes, FinQA và Wikidata subgraphs; trình bày B0–B4, nguồn dẫn và graph path.
6. Nhấn mạnh bản này chỉ có Chương 1–5, không có Chương 6 multi-agent.

## 11. Demo tiểu luận 3

Chạy:

```bash
./scripts/run_web_gitbash.sh tieuluan3
```

Mở http://127.0.0.1:8019.

Luồng trình diễn đề xuất:

1. Đi nhanh qua **Tổng quan**, **ML**, **CNN** và **RNN–LSTM**, dùng cùng ba dataset mỗi chương.
2. Ở **KG–RAG**, chọn câu hỏi y khoa hoặc tài chính, xem evidence, citation và đường đi trên graph.
3. Ở **Multi-Agent**, chọn tác vụ tiểu đường, giá nhà hoặc giá vàng.
4. So sánh A0 trực tiếp, A1 có router và A2 có verifier/reporter trên cùng request ID.
5. Mở agent trace để giải thích định tuyến, specialist, kiểm chứng và báo cáo.
6. Kết thúc bằng phần triển khai: web chỉ phục vụ inference/replay, không huấn luyện lại mô hình khi người dùng bấm chạy.

Lưu ý quan trọng: Chương 6 hiện có trong `tieuluan3` là demo multi-agent đã khóa của tiểu luận. Nó **khác** với `project01` RAG + Gemini v2 đang được phát triển riêng ở cổng 8031.

## 12. Xem notebook và dataset

Liệt kê notebook, runtime và dataset của từng bài:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PWD/scripts/run_assignment.ps1")" -Project A05 -Inspect
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PWD/scripts/run_assignment.ps1")" -Project A05 -ListDatasets
```

Thay `A05` bằng tên bài cần xem. Notebook hiện hành nằm trong `<bài>\notebooks\`, dataset catalog nằm tại `<bài>\datasets\catalog.json`.

Khi trình bày code:

- Mở notebook bằng VS Code trong WSL Ubuntu.
- Chọn kernel Torch hoặc Keras đúng theo `<bài>\project.json`/README.
- Giữ `RUN_EXPERIMENTS=False`, `RUN_TRAINING=False` và `RUN_TEST=False` nếu notebook có các cờ này.
- Không chạy toàn bộ notebook huấn luyện chỉ để kiểm tra UI.

## 13. Build lại ba web tiểu luận khi cần

Chỉ build lại khi đã sửa frontend hoặc `dist/` bị thiếu:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PWD/scripts/build_web.ps1")" -Project tieuluan3
```

Nếu máy chưa có dependency Node tương ứng:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PWD/scripts/build_web.ps1")" -Project tieuluan3 -Install
```

Thay `tieuluan3` bằng `tieuluan1` hoặc `tieuluan2`. Không cần build cho A01–A06 vì chúng là HTML/CSS/JS static.

## 14. Lỗi thường gặp

### Xuất hiện lỗi `[CmdletBinding()]` trong Git Bash

Nguyên nhân: Bash đang đọc cú pháp PowerShell như `[CmdletBinding()]`.

Cách xử lý: không chạy trực tiếp file `.ps1`. Dùng `./scripts/run_web_gitbash.sh A01`.

### Cổng đã được sử dụng

```bash
./scripts/run_web_gitbash.sh A01 9000
```

Sau đó mở http://127.0.0.1:9000.

### Web mở nhưng API không phản hồi

Kiểm tra terminal runner còn hoạt động và chạy:

```bash
curl http://127.0.0.1:8011/health
```

Nếu vừa sửa source backend, dừng bằng `Ctrl+C`, chạy lại runner và refresh trình duyệt bằng `Ctrl+F5`.

### Tiểu luận báo thiếu `dist/index.html`

Chạy lại `build_web.ps1` theo mục 13 rồi khởi động web lần nữa.

### Dataset/model lớn không có sau khi clone Git

Đọc `<bài>\datasets\catalog.json` và README của bài. Raw dataset/checkpoint bị ignore không tự có trong clean checkout; không thay file khác cùng tên nếu chưa kiểm hash.
