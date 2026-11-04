# Dataset card — MedQuAD diabetes v2

Ngày lấy 02/11/2026, revision Phase1. Đầu vào công khai cho hỏi đáp kiến thức, không phải hồ sơ bệnh nhân và không phải dữ liệu huấn luyện lại mô hình CDC.

| Nguồn / sản phẩm | Kích cỡ và vai trò |
|---|---|
| [MedQuAD](https://github.com/abachaa/MedQuAD), commit `577bd37b96c02d1833b2c9eed2de9f96964e96cb` | Archive7.291.319 byte; quét11.274 XML; chọn sơ bộ72 tài liệu/287 QA có diabetes trong focus/title |
| Corpus chính |45 tài liệu,210 QA nguyên ngữ cảnh,316 chunk text duy nhất,409 liên kết nguồn; tổng348.397 ký tự ở chunks |
| Mini-KG r2 |35 concept,35 assertion,20 chunk nguồn/17 tài liệu; curation trợ lý, chưa chạy extractor LLM |
| Evaluation v1 tự soạn |20 development+40 held-out; không là QA benchmark chính thức của MedQuAD |
| CDC hiện có |Giữ dataset/checkpoint cũ253.680 dòng/21 field, không tải lại/train/TEST trong Phase1; chỉ là công cụ risk bổ sung ở Phase2 |

`source_catalog.json` liệt kê đủ45 title, URL gốc phục hồi từ XML, snapshot locator và document ID. Không suy đoán URL từ hash. Tất cả45 có URL gốc nhưng chưa xác minh từng trang hiện còn hoạt động. `raw/MedQuAD_LICENSE.txt` giữ CC BY4.0 của dataset; ghi attribution và điều khoản trang nguồn riêng. Raw tar/XML ở `raw/` được Git ignore; JSON/JSONL nhỏ đã cho phép versioning có chọn lọc. Có script tải lại đúng commit và SHA trong `artifacts/llm_v2/phase1/acquisition.json`.

## Lọc và chia đoạn

Chọn các nguồn NIH tổng quát NIDDK/MedlinePlus/NHLBI/NINDS/SeniorHealth. Loại diabetes insipidus, phần chỉ hỗ trợ tài chính và hai nhóm nguồn GARD/GHR ở lượt lọc này; bài NIDDK về dạng đơn gen vẫn có thể được giữ. Chi tiết included/excluded ở `selection.json`; không dùng ranking hay lỗi held-out để chọn.

Giữ full câu hỏi/trả lời trong `qa_context.jsonl`, reference vị trí ký tự trên chuỗi normalized. Chunk mục tiêu mềm1600 ký tự, ranh giới câu, overlap một câu; câu dài giữ nguyên thay vì cắt đứt. Sau dedup text chính xác, giữ mọi `source_refs`. ChunkID hash content; index phải thêm fingerprint model/config/corpus. Character offsets không phải vị trí byte trong XML.

Phân bố tài liệu: NIDDK27, MedlinePlus14, SeniorHealth2, NHLBI1, NINDS1. Chunk min71/max2579/trung bình1102,52 ký tự. Đây là phân bố nguồn/độ dài, không nhãn phân loại hoặc mức phổ biến bệnh. Nguồn NIDDK trội và một số QA lặp lại giữa bài; dedup chunk không loại hết gần trùng về ý.

`examples.json` cho ba mẫu thật, chọn theo chunkID đã sort, gồm content/section/title/offset/URL. Ví dụ quan hệ dễ hiểu: nguồn về thận nói đường huyết cao lâu dài có thể làm tổn thương thận; seed giữ đúng chiều đó và trỏ về câu trích. Không diễn giải đảo chiều hoặc nhận đồ thị là ontology nhân quả.

## Giới hạn

Snapshot MedQuAD lịch sử chứa thống kê, mốc sàng lọc và khuyến nghị có thể đã cũ; không trình bày như hướng dẫn lâm sàng2026. Không chọn benchmark kê liều, ngưỡng điều trị hay lịch tập cá nhân. Câu liên quan thông tin hiện tại phải nêu thiếu nguồn. Một số bảng/list XML đã flatten thành văn bản, có lỗi nối từ; giữ full QA để tránh mất điều kiện nhưng không nhận đã sửa toàn bộ chất lượng nguồn.

Corpus tiếng Anh; câu hỏi/demo tiếng Việt, cần pre-retrieval song ngữ và kiểm không đổi phủ định/chiều quan hệ. RAG không bảo đảm đúng chỉ nhờ citation. Review seed và gold do trợ lý thực hiện, chưa có bác sĩ kiểm. Qrels chưa đầy đủ; nhận các nguồn khác thực sự hỗ trợ. Held-out không gửi model trước freeze; chưa có output/chất lượng đo được. Không dùng bộ này để tuyên bố chẩn đoán hay hiệu quả điều trị.
