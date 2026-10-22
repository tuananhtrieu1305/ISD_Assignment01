# Làm rõ scope demo — không đổi dữ liệu/kết quả

Ma trận UI18case gồm12neural TRAIN,3agent parent_train và3KG–RAG
**demo_not_benchmark**. Marker input_split lấy nguyên từ smoke Phase32, không
đổi query hoặc tự gán QA query vào TRAIN/TEST. Wikidata chỉ browser structural.
Không đánh giá accuracy mới, không mở lại benchmark/TEST seal.

Tên test/field scope mô tả chung “live TRAIN comparison”/“TRAIN-only UI serving
smoke” là nhãn template ở harness; không dùng nhãn đó để đổi nghĩa marker thật
của3KGcase. input_split trong từng receipt và văn bản này là scope cụ thể.
Giữ receipt/header/source frontend nguyên byte, không “sửa” saved output để
qua audit. Auditor r2 kiểm marker đúng theo miền thay vì ép mọi QA thành TRAIN.

Python review đầu tiên và7fixture tests cũ giữ riêng; snapshot5source
trước sửa auditor ở python_review_r1_source.zip, SHA256
53b6b335de1bc2556ace838b2492a89e6037a6938e378de997d23f2833145bb1.
Review r2 và XML auditor-final-r4.xml thêm test scope riêng (8test), không cộng
XML cũ vào tổng nghiệm thu. Đây là sửa kiểm tra/ghi rõ scope trước release UI,
không sửa evaluator/model/data/metric của22–32 hoặc ngưỡng so sánh.
