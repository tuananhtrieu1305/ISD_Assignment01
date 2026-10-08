# Quy ước thuật ngữ cho bản thảo

Tệp này là hợp đồng biên tập dùng ở Phase 7–9, không phải một phần của nội dung nộp.

| Khái niệm | Cách viết thống nhất | Quy tắc |
|---|---|---|
| Artificial Intelligence | trí tuệ nhân tạo (Artificial Intelligence — AI) | Viết đầy đủ ở lần xuất hiện đầu; sau đó dùng AI. |
| Machine Learning | học máy (Machine Learning — ML) | Viết đầy đủ ở lần xuất hiện đầu; sau đó dùng ML. |
| Convolutional Neural Network | Convolutional Neural Network (CNN) | Giữ tên tiếng Anh để nhất quán với notebook và mã nguồn. |
| Recurrent Neural Network | Recurrent Neural Network (RNN) | Không dịch là “mạng hồi quy” vì dễ nhầm với regression. |
| Dataset | dataset | Giữ từ `dataset` vì đây là thuật ngữ trong yêu cầu giảng viên; không trộn với “bộ dữ liệu” trong cùng một nhãn. |
| Data split | TRAIN / VALIDATION / TEST | Viết hoa khi chỉ đúng split đã khóa; không dùng “test set” xen kẽ trong bảng kết quả. |
| Implementation | implementation NumPy/scratch, Keras, PyTorch | `scratch` chỉ cách tự cài đặt toán học; NumPy là runtime của scratch. |
| Framework comparison | matched comparison | Chỉ dùng khi topology, split, search space và budget đã được khóa chung. |
| Baseline | baseline | Giữ tiếng Anh; luôn nêu baseline cụ thể và cùng split đánh giá. |
| Random seed | seed | Ghi rõ 42/52/62 ở bảng matched hoặc chú thích nguồn. |
| Artifact | artifact | Chỉ tệp dữ liệu, metric, prediction, model hoặc manifest có thể kiểm tra lại. |
| Metric | metric | Tên metric giữ chuẩn: accuracy, macro-F1, MAE, RMSE, R², ROC-AUC, PR-AUC. |

Quy ước số liệu: dùng dấu phẩy cho số thập phân trong phần văn xuôi và bảng tiếng Việt; tên tệp, mã nguồn và giá trị máy đọc được giữ nguyên định dạng gốc. Không suy rộng kết quả của benchmark subset thành kết quả trên toàn bộ quần thể.
