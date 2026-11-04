# Báo cáo revision r7 — ba generation call

Ngày chốt offline: 03/11/2026. Phase 2 vẫn **IN_PROGRESS**; revision này chưa chạy một lượt Gemini mới để tránh tiêu hao quota.

## Kết quả chính

Mỗi lượt so sánh mới dùng đúng **3 lần gọi generation**:

1. Baseline LLM trực tiếp: 1 lần.
2. Coordinator phân tích câu hỏi/pre-retrieval: 1 lần.
3. Reporter tổng hợp câu trả lời có bằng chứng: 1 lần.

Embedding truy vấn dùng quota riêng của `gemini-embedding-001`, tối đa ba query theo cấu hình. Nó không phải generation call và được hiển thị riêng, không được che giấu trong con số ba.

## Năm agent thực sự dùng gì

| Vai trò | Công cụ | Generation call |
|---|---|---:|
| Coordinator | Gemini để chuẩn hóa ý định, thực thể và truy vấn | 1 |
| Knowledge Agent | BM25, Gemini query embedding, vector store, mini-KG và reranker local | 0 |
| Risk Agent | checkpoint NumPy CDC đã khóa; chỉ chạy khi có đủ hồ sơ | 0 |
| Reporter | Gemini để viết câu trả lời dựa trên evidence đã chọn | 1 |
| Code Verifier | Python kiểm schema, citation, provenance, source marker và số liệu | 0 |

Năm agent là năm trách nhiệm trong pipeline, không phải năm mô hình LLM. `Code Verifier` không đánh giá đúng/sai về y khoa; nó chỉ kiểm tra tính toàn vẹn có thể xác định bằng code.

## Reranker được kế thừa thế nào

Project tham khảo dùng `BaseReranker` và mặc định `BGEReranker` chạy local bằng `CrossEncoder`, không gọi API generation. Revision r7 giữ cùng kiểu giao diện nhưng dùng `LocalEvidenceReranker` nhẹ hơn để phù hợp môi trường demo/Render hiện tại, vốn không mang `sentence-transformers`, Torch và trọng số BGE lớn. Điểm xếp hạng gồm hybrid RRF 0,55, độ phủ từ khóa 0,35 và KG/source boost 0,10. Đây là adapter local lấy cảm hứng từ kiến trúc tham khảo, không được mô tả là BGE thật.

## Bỏ các request không cần thiết

- Không dùng Gemini reranker.
- Không dùng LLM Verifier.
- Không có vòng repair sinh lại câu trả lời.
- Backend từ chối tạo lượt so sánh mới khi quota generation còn dưới ba, tránh hoàn thành một nhánh rồi treo nhánh còn lại.

## Nghiệm thu offline

- 16/16 kiểm tra hợp đồng ba call PASS.
- 28/28 regression PASS.
- 10/10 kiểm tra UI PASS.
- 3 notebook/16 module export parity PASS.
- React build 18 module PASS.
- Không gọi generation hoặc embedding mới trong revision này.

UI dùng kết quả đã lưu cùng metadata r7 giả lập chỉ để kiểm tra cách trình bày; không được xem là kết quả chất lượng mô hình mới. Backend đang chạy cổng 8031 thuộc người dùng và vẫn giữ import cũ cho tới khi được restart.
