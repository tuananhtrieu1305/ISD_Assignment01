# Dàn ý khóa cho tiểu luận AI/ML/CNN/RNN

Phiên bản: 1.0 — khóa ở Phase 1, ngày 2026-10-05.  
Độ sâu: đến Heading 3. Số trang là ngân sách nội dung sau khi dựng DOCX, không phải số trang Markdown.

## Ngân sách tổng

| Phần | Trang mục tiêu | Ràng buộc |
|---|---:|---|
| Front matter | 5 | Bìa, trang tên, tóm tắt, mục lục, danh mục hình/bảng |
| Mở đầu | 4 | Yêu cầu 3–4 |
| Chương 1 | 8 | Yêu cầu 8 |
| Chương 2 | 13 | Yêu cầu 10–15 |
| Chương 3 | 13 | Yêu cầu 10–15 |
| Chương 4 | 13 | Yêu cầu 10–15 |
| Phần triển khai | 3 | Bắt buộc có deploy |
| Kết luận | 2 | Tổng hợp, hạn chế, hướng phát triển |
| Tài liệu tham khảo | 3 | 20–30 nguồn ban đầu, bổ sung khi viết |
| **Tổng trước phụ lục** | **64** | 51 trang cho Mở đầu + Chương 1–4 |
| Phụ lục | 5–10 | Chỉ code/protocol/bảng mở rộng cần thiết |

## Ngân sách hình và bảng

| Phần | Hình tối đa mục tiêu | Bảng tối đa mục tiêu | Ghi chú |
|---|---:|---:|---|
| Mở đầu | 1 | 1 | Sơ đồ phạm vi và bảng câu hỏi nghiên cứu |
| Chương 1 | 2 | 1 | Timeline hai trang hoặc một timeline + một sơ đồ; tránh gallery lịch sử |
| Chương 2 | 5 | 5 | 3 phân bố dataset; 1 workflow; 1 result plot; dataset/metric tables gộp |
| Chương 3 | 6 | 5 | Sample grids, architecture, class/result plots; confusion matrices ghép panel |
| Chương 4 | 6 | 5 | Sequence diagram, EDA, ROC/CM, time-series predictions; ghép panel khi hợp lý |
| Triển khai | 3 | 2 | Kiến trúc + tối đa 2 screenshot app; bảng test/provenance |
| Kết luận | 0–1 | 1 | Chỉ dùng nếu giúp tổng hợp xuyên chương |

Mỗi hình/bảng dự kiến chiếm trung bình 1/3–1/2 trang. Figure phụ, full confusion matrices và bảng hyperparameter dài chuyển sang phụ lục để các chương 2–4 giữ trong 10–15 trang.

## Front matter — 5 trang

### FM.1. Bìa ngoài

- Tên trường/khoa, môn học, tên đề tài, giảng viên, sinh viên, lớp/MSSV, địa điểm và năm.

### FM.2. Trang tên

- Lặp thông tin học thuật theo mẫu; bỏ yếu tố trang trí không cần thiết.

### FM.3. Tóm tắt và từ khóa

- Bài toán, 8 dataset instance, ba cách cài đặt, deployment và giới hạn chính.

### FM.4. Mục lục

- Word TOC tự động từ Heading 1–3.

### FM.5. Danh mục hình và danh mục bảng

- Word fields tự động từ caption “Hình” và “Bảng”.

## Mở đầu — 4 trang

### 0.1. Bối cảnh và lý do chọn đề tài

- Vai trò của AI, ML, CNN và RNN; nhu cầu nối lý thuyết với thực nghiệm tái lập.

### 0.2. Mục tiêu nghiên cứu

- Hệ thống hóa lịch sử; trình bày nền tảng; cài đặt scratch/Keras/PyTorch; so sánh công bằng; triển khai inference.

### 0.3. Đối tượng, phạm vi và câu hỏi nghiên cứu

- Ba họ mô hình; dữ liệu bảng, ảnh và chuỗi; không tuyên bố SOTA; không đưa khuyến nghị y khoa/tài chính.

### 0.4. Phương pháp và cấu trúc tiểu luận

- Nghiên cứu tài liệu, audit notebook, controlled experiments, artifact-first reporting; giới thiệu cấu trúc các chương.

## Chương 1. Lịch sử phát triển trí tuệ nhân tạo — 8 trang

### 1.1. Tiền đề lý thuyết trước khi AI thành ngành

#### 1.1.1. Logic hình thức, tính toán và neuron nhân tạo

#### 1.1.2. McCulloch–Pitts và mô hình hóa hoạt động thần kinh

### 1.2. Turing và câu hỏi về trí tuệ máy

#### 1.2.1. Imitation Game năm 1950

#### 1.2.2. Ý nghĩa và giới hạn của phép thử hành vi

### 1.3. Dartmouth 1955–1956 và sự hình thành tên gọi AI

#### 1.3.1. Mục tiêu trong đề xuất Dartmouth

#### 1.3.2. Kỳ vọng ban đầu và những hướng nghiên cứu chính

### 1.4. Từ AI biểu tượng đến các chu kỳ hưng thịnh–suy giảm

#### 1.4.1. Tìm kiếm, biểu diễn tri thức và hệ chuyên gia

#### 1.4.2. AI winter: giới hạn dữ liệu, tính toán và kỳ vọng

### 1.5. Sự trỗi dậy của machine learning và deep learning

#### 1.5.1. Perceptron, backpropagation và học biểu diễn

#### 1.5.2. CNN, ImageNet và bước ngoặt AlexNet

#### 1.5.3. RNN, LSTM, attention và Transformer

### 1.6. Bài học lịch sử cho thực nghiệm hiện đại

#### 1.6.1. Dữ liệu, compute, kiến trúc và protocol đánh giá

#### 1.6.2. Tính tái lập, đạo đức và giới hạn suy diễn

## Chương 2. Các kỹ thuật Machine Learning cơ bản — 13 trang

### 2.1. Bài toán học máy có giám sát

#### 2.1.1. Classification và regression

#### 2.1.2. Train/validation/test và khái quát hóa

### 2.2. Các thuật toán nền tảng

#### 2.2.1. Linear/logistic regression và hàm mất mát

#### 2.2.2. k-nearest neighbors và support vector machine

#### 2.2.3. Decision tree, random forest và boosting

#### 2.2.4. Multilayer perceptron và backpropagation

### 2.3. Quy trình dữ liệu và kiểm soát leakage

#### 2.3.1. Làm sạch, mã hóa, chuẩn hóa và fit scope

#### 2.3.2. Split, seed, threshold và baseline

### 2.4. Datasets của Chương 2

#### 2.4.1. CDC Diabetes Health Indicators — binary

#### 2.4.2. Vietnam Housing Dataset 2024

#### 2.4.3. Synthetic E-Commerce Customer Behavior

### 2.5. Ba cách cài đặt MLP

#### 2.5.1. NumPy scratch: forward, loss, backpropagation và update

#### 2.5.2. Keras Dense MLP

#### 2.5.3. PyTorch MLP

### 2.6. Kết quả thực nghiệm và so sánh

#### 2.6.1. So sánh trên diabetes classification

#### 2.6.2. So sánh trên house-price regression

#### 2.6.3. So sánh trên customer churn classification

### 2.7. Phân tích sai số và giới hạn

#### 2.7.1. Imbalance, calibration và failure cases

#### 2.7.2. Tác động của dữ liệu tổng hợp và tính đại diện

### 2.8. Tiểu kết chương

## Chương 3. Convolutional Neural Network — 13 trang

### 3.1. Động cơ và trực giác CNN

#### 3.1.1. Local connectivity và weight sharing

#### 3.1.2. Translation equivariance và receptive field

### 3.2. Thành phần toán học

#### 3.2.1. Convolution/cross-correlation, padding và stride

#### 3.2.2. Activation, pooling và classification head

#### 3.2.3. Backpropagation qua lớp convolution

### 3.3. Thiết kế thực nghiệm

#### 3.3.1. Split, chuẩn hóa ảnh/feature và class weighting

#### 3.3.2. Matched topology, benchmark subset và fairness

### 3.4. Datasets của Chương 3

#### 3.4.1. EuroSAT RGB

#### 3.4.2. Oxford-IIIT Pet

#### 3.4.3. CDC Diabetes Health Indicators — 3 lớp

### 3.5. Ba cách cài đặt CNN

#### 3.5.1. NumPy scratch CNN có backward/update

#### 3.5.2. Keras Conv2D/Conv1D

#### 3.5.3. PyTorch Conv2d/Conv1d

### 3.6. Kết quả matched comparison

#### 3.6.1. EuroSAT image classification

#### 3.6.2. CDC Diabetes Conv1D adaptation

#### 3.6.3. Oxford-IIIT Pet case study mở rộng

### 3.7. Ablation kiến trúc và phân tích failure

#### 3.7.1. Basic, AlexNet-inspired, VGG-inspired, ResNet-inspired

#### 3.7.2. Collapse, near-random result và giới hạn protocol

### 3.8. Tiểu kết chương

## Chương 4. Recurrent Neural Network — 13 trang

### 4.1. Dữ liệu tuần tự và trạng thái ẩn

#### 4.1.1. Many-to-one sequence modeling

#### 4.1.2. Quan hệ giữa thứ tự thời gian và split

### 4.2. Vanilla RNN và Backpropagation Through Time

#### 4.2.1. Phương trình forward

#### 4.2.2. BPTT, vanishing/exploding gradient và clipping

### 4.3. Từ Vanilla RNN đến LSTM/GRU và attention

#### 4.3.1. Cơ chế cổng và long-term dependency

#### 4.3.2. Giới hạn phạm vi: thực nghiệm chính dùng Vanilla RNN

### 4.4. Datasets của Chương 4

#### 4.4.1. UCI Online Retail II — customer-week classification

#### 4.4.2. AAPL 2015–2025 — next-day Close regression

### 4.5. Ba cách cài đặt Vanilla RNN

#### 4.5.1. NumPy scratch với BPTT và gradient clipping

#### 4.5.2. Keras SimpleRNN

#### 4.5.3. PyTorch nn.RNN

### 4.6. Kết quả matched comparison

#### 4.6.1. Customer next-week purchase

#### 4.6.2. AAPL next-trading-day Close

#### 4.6.3. Parameter count, thời gian và sai khác framework

### 4.7. Phân tích giới hạn

#### 4.7.1. Imbalance và trade-off precision–recall

#### 4.7.2. Distribution shift và naive last-Close baseline

### 4.8. Tiểu kết chương

## Phần 5. Triển khai mô hình — 3 trang

### 5.1. Kiến trúc ứng dụng và provenance

#### 5.1.1. Luồng input → validate → preprocess → model → response

#### 5.1.2. Model/preprocessor version và SHA-256

### 5.2. Use case ML: diabetes risk

#### 5.2.1. Form nhập liệu, output và cảnh báo y khoa

### 5.3. Use case CNN: EuroSAT

#### 5.3.1. Upload ảnh, top classes và confidence

### 5.4. Use case RNN: customer/AAPL

#### 5.4.1. Sequence input, RNN output, baseline và cảnh báo tài chính

### 5.5. Kiểm thử và tái lập

#### 5.5.1. Health check, invalid input và smoke tests

#### 5.5.2. Chạy local, Docker và trạng thái cloud

### 5.6. Hạn chế khi triển khai

## Kết luận — 2 trang

### K.1. Kết quả đạt được

### K.2. Trả lời câu hỏi nghiên cứu

### K.3. Hạn chế và hướng phát triển

## Tài liệu tham khảo — 3 trang

### TL.1. Bài báo và sách nền tảng

### TL.2. Dataset, framework và tài liệu kỹ thuật

## Phụ lục — 5–10 trang

### PL.A. Hợp đồng thực nghiệm và môi trường

### PL.B. Kiến trúc/siêu tham số chi tiết

### PL.C. Bảng metric mở rộng và kiểm tra tái lập

### PL.D. Hướng dẫn chạy code/deployment
