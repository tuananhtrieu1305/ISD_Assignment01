# Quy ước thuật ngữ cho bản thảo

Tệp này là hợp đồng biên tập dùng ở Phase 7–19, không phải một phần của nội dung nộp.

| Khái niệm | Cách viết thống nhất | Quy tắc |
|---|---|---|
| Artificial Intelligence | trí tuệ nhân tạo (Artificial Intelligence — AI) | Viết đầy đủ ở lần xuất hiện đầu; sau đó dùng AI. |
| Machine Learning | học máy (Machine Learning — ML) | Viết đầy đủ ở lần xuất hiện đầu; sau đó dùng ML. |
| Convolutional Neural Network | Convolutional Neural Network (CNN) | Giữ tên tiếng Anh để nhất quán với notebook và mã nguồn. |
| Recurrent Neural Network | Recurrent Neural Network (RNN) | Không dịch là “mạng hồi quy” vì dễ nhầm với regression. |
| Knowledge Base | kho tri thức (Knowledge Base — KB) | KB là khái niệm rộng; không đồng nhất mọi KB với Knowledge Graph. |
| Knowledge Graph | đồ thị tri thức (Knowledge Graph — KG) | Dùng KG sau lần xuất hiện đầu; luôn nêu schema và provenance. |
| Retrieval-Augmented Generation | sinh có tăng cường truy hồi (Retrieval-Augmented Generation — RAG) | Dùng RAG sau lần đầu; tách retrieval quality khỏi answer correctness. |
| Graph-guided RAG | KG-RAG hoặc graph-guided RAG | Dùng cho pipeline B4 của đề tài; không gọi là full GraphRAG community-summary. |
| Agent | Agent bị giới hạn công cụ | Không gọi là tác nhân tự trị; nêu allow-list, citation và refusal. |
| Dataset | dataset | Giữ từ `dataset` vì đây là thuật ngữ trong yêu cầu giảng viên; không trộn với “bộ dữ liệu” trong cùng một nhãn. |
| Data split | TRAIN / VALIDATION / TEST | Viết hoa khi chỉ đúng split đã khóa; không dùng “test set” xen kẽ trong bảng kết quả. |
| Implementation | implementation NumPy/scratch, Keras, PyTorch | `scratch` chỉ cách tự cài đặt toán học; NumPy là runtime của scratch. |
| Framework comparison | matched comparison | Chỉ dùng khi topology, split, search space và budget đã được khóa chung. |
| Baseline | baseline | Giữ tiếng Anh; luôn nêu baseline cụ thể và cùng split đánh giá. |
| Random seed | seed | Ghi rõ 42/52/62 ở bảng matched hoặc chú thích nguồn. |
| Artifact | artifact | Chỉ tệp dữ liệu, metric, prediction, model hoặc manifest có thể kiểm tra lại. |
| Metric | metric | Giữ tên chuẩn; Ch5 dùng Recall@k, MRR@10, exact match, token F1, citation validity và latency. |

Quy ước số liệu: dùng dấu phẩy cho số thập phân trong phần văn xuôi và bảng tiếng Việt; tên tệp, mã nguồn và giá trị máy đọc được giữ nguyên định dạng gốc. Không suy rộng kết quả của benchmark subset thành kết quả trên toàn bộ quần thể.
