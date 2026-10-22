# Dataset card — Synthetic E-Commerce Customer Behavior

## Nhận dạng và nguồn

- Dataset ID: `ch2_ecommerce_behavior`.
- Chương/bài toán: Chương 2, binary customer churn classification.
- Nguồn: <https://www.kaggle.com/datasets/lorenzoscaturchio/ecommerce-behavior>.
- Truy cập: 2026-10-05. Citation key: `scaturchio2026ecommerce`.
- License: GPL-3.0 theo README đi kèm bản local; metadata license trên Kaggle chưa được xác nhận độc lập ở Phase 1.
- Local: `datasets/customer_behavior/`; 17,139,547 bytes cho 5 CSV chính + README; folder-manifest SHA-256 `d56173efbb0927fd1a0fa07b228d184673aba17d60c6b52dd01586669495b8bf`.

## Kích thước và quan hệ

| Bảng | Rows × columns | Kích thước bytes |
|---|---:|---:|
| `customers.csv` | 10,000 × 10 | 509,464 |
| `products.csv` | 1,000 × 11 | 76,794 |
| `transactions.csv` | 120,000 × 11 | 9,837,285 |
| `sessions.csv` | 80,000 × 10 | 5,013,659 |
| `reviews.csv` | 25,000 × 8 | 1,695,777 |

- Khóa nối chính: `customer_id`, `product_id`. Target `is_churned` nằm trong bảng customer.
- Dataset là dữ liệu tổng hợp có seed/rule-based generation, không chứa người thật.

## Phân bố và mẫu

- Target trên 10,000 customers: class 0 = 8,306 (83.06%); class 1 = 1,694 (16.94%).
- Mẫu input đã ẩn định danh: khách hàng `C*****`, tuổi 28, giới tính M, country BR, segment Premium, lifetime value 1,595.27, chưa opt-in email, chưa có app.
- Output của hàng mẫu nguồn: `is_churned=0`.
- Mô hình ghép thêm aggregate giao dịch/session/review trước prediction cutoff; schema sau preprocessing hiện có 368 transformed features.

## Chênh lệch README và dữ liệu thực tế

- Phần mô tả đầu README nói đúng quy mô 10K customers, 120K transactions, 80K sessions và 25K reviews.
- Tuy nhiên từng bảng trong README lại ghi `Rows: 5,000` cho customers/reviews/sessions/transactions. Kiểm đếm CSV thực tế cho kết quả lần lượt 10,000/25,000/80,000/120,000; các con số thực đo được dùng trong báo cáo.
- README mô tả 8 categories ở đoạn đầu nhưng bảng products cho thấy 15 giá trị category. Báo cáo sẽ dùng thống kê trực tiếp từ CSV.

## Tiền xử lý và split khóa

- Chỉ tổng hợp hành vi trước `2024-10-01 23:59:05` để giảm future leakage.
- Numeric median + scaling; categorical `Unknown` + one-hot; review text TF-IDF; fit TRAIN only.
- Outer split stratified 80/20, seed 42; development tách tiếp validation.

## Nhận xét và giới hạn

- Dữ liệu tổng hợp hữu ích cho reproducibility và không có PII thật, nhưng quan hệ feature–target có thể phản ánh rule của generator hơn là hành vi thị trường.
- Dataset có nhãn churn nhưng không có churn date chính xác; cutoff làm giảm chứ không loại bỏ hoàn toàn ambiguity của outcome window.
- Cần ưu tiên F1/recall/ROC-AUC thay vì chỉ accuracy do tỷ lệ churn 16.94%.

## Bằng chứng local

- Notebook: `pipeline/customer_behavior_pipeline.ipynb`.
- Metadata/model: `pipeline/customer_behavior/metadata.json`, `model.npz`, `preprocessor.joblib`.
