# Source V3

`common/` và các package `ch02_ml/`, `ch03_cnn/`, `ch04_rnn_lstm/`,
`ch05_knowledge_rag/`, `ch06_multi_agent/` là vị trí triển khai mới theo Phase 25–31.

`term_paper/` chứa code V2 cần tái sử dụng. Namespace này được giữ tạm thời để load
bundle joblib Ch5 có tên lớp đã khóa. Khi chuyển code, giữ một bản triển khai duy nhất
và cung cấp import alias nếu checkpoint còn cần namespace cũ.

`legacy_a06/` là code tham chiếu, không phải runner V3.
