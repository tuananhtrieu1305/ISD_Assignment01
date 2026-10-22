# Contract KG–RAG Phase30.1

Phase22 giữ nguyên byte/hash. `model.schema.json` và validator model hiện chỉ diễn tả mạng
neural: backend scratch/Keras/PyTorch, ít nhất6 layer và parameter_count>0. Không ép BM25,
LSA hoặc snapshot Wikidata thành mạng sáu lớp để qua schema.

Extension có phiên bản `phase30.retrieval_pipeline.1`, schema local tại
`src/ch05_knowledge_rag/pipeline_contract.schema.json`, chuẩn hóa function/composition,
config/source refs và trạng thái demo. Số layer/parameter neural là null (không áp dụng),
không đổi common schema hoặc registry initialized Phase25. Request/job/chapter/citation
vẫn kiểm bằng schema API V3 gốc. Đây là extension non-neural, không thay giao thức TEST.

MedQuAD và FinQA có5 slot B0–B4, dùng index/bundle đã fit từ trước; không fit lại.
B2 giữ sparse0,75; B4 giữ0,6/0,1/0,3 và RRF60. Nhánh graph demo khớp nhãn compact/free
question; graph lịch sử dùng query-ID và full adjacency. Không tuyên bố demo tái hiện
rankings/latency TEST. Các số TEST trong báo cáo chỉ đọc artifact Phase15.

Tab Wikidata duyệt10 entity/revision/claim/hash và không có metric QA. Nếu gửi compare QA,
job V3 trả đủ5 slot unavailable/not_run với lý do structural_dataset_only. Công cụ riêng
`inspect_entity` hoạt động local, không gắn nhãn nó là B3 đã đánh giá trên QA TEST thứ ba.
Catalog cung cấp3 dataset-tab descriptor, React thật triển khai ở Phase33.

Citation demo giữ chunk/document ID cũ trong evidence. Citation V3 dùng ID hash chuẩn hóa,
locator tới `kg_chunks.jsonl.gz#chunk;document=...`, SHA-256 chính container local và URL
upstream dataset. Bundle compact không còn URL/locator raw từng chunk; không bịa lại.
Hash ở đây xác minh container local được locator nêu, không phải bytes tải từ URL landing
page. Manifest nối container với snapshot nguồn; citation hợp lệ không có nghĩa answer đúng.

Nạp joblib chỉ cho4 index local nằm trong manifest SHA cứng đã khóa, sau khi kiểm cả6 file,
role/path/size/hash/budget; không nhận file upload hay đường dẫn từ request. Giữ namespace
`term_paper` để serialized class load được. Không nâng dependency hoặc sửa pickle.

Timing demo cộng các thành phần dùng chung và answer, loại cold load/serialize. Nó không
phải5 process benchmark độc lập hoặc HTTP latency; không trộn với p95 TEST lịch sử.
Guardrail hữu hạn không thay thế kiểm chứng an toàn y khoa/tài chính thực tế.
