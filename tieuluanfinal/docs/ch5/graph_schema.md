# Phase 13 graph schema

## Contract chung

Hai đồ thị `medical` và `finance` là property graph có hướng, được xuất đồng thời dưới dạng JSONL, GraphML và adjacency index JSON. Mỗi node có các trường bắt buộc `node_id`, `domain`, `node_type`, `stable_key`, `label`, `provenance`; mỗi edge có `edge_id`, `domain`, `edge_type`, `source_id`, `target_id`, `stable_key`, `directed`, `provenance`. ID là SHA-256 rút gọn sinh từ khóa ổn định, không phụ thuộc thứ tự đọc file.

`provenance` luôn chứa `source_record_id`, `source_path`, `source_sha256`, `extractor_version`, `confidence`. Confidence nằm trong [0, 1]. Không chấp nhận edge có đầu mút không tồn tại.

## Medical KG

| Node type | Nguồn | Ý nghĩa |
|---|---|---|
| `MedicalEntity` | MedQuAD Focus/title | Chủ đề bệnh được chuẩn hóa theo metadata |
| `Document` | Phase 12 document | Câu trả lời/tài liệu MedQuAD |
| `Chunk` | Phase 12 chunk | Đoạn văn truy hồi |
| `Question` | Phase 12 query | Câu hỏi đánh giá |
| `QuestionType` | MedQuAD metadata | Loại câu hỏi |
| `WikidataEntity` | Snapshot Phase 11 | Thực thể ngoài đã khóa revision |

| Edge type | Source → target | Quy tắc |
|---|---|---|
| `DESCRIBES` | Document → MedicalEntity | Focus/title của document |
| `HAS_CHUNK` | Document → Chunk | Quan hệ chunk gốc |
| `ASKS_ABOUT` | Question → MedicalEntity | Kế thừa entity từ gold document |
| `HAS_QUESTION_TYPE` | Document → QuestionType | Metadata MedQuAD |
| `SAME_AS` | MedicalEntity → WikidataEntity | Chỉ exact validated alias duy nhất |

## Finance KG

| Node type | Nguồn | Ý nghĩa |
|---|---|---|
| `Company` | ticker trong `report_id` | Doanh nghiệp phát hành báo cáo |
| `AnnualReport` | `report_id` | Báo cáo theo công ty và năm |
| `ReportPage` | Phase 12 document | Trang báo cáo FinQA |
| `Chunk` | Phase 12 chunk | Đoạn văn/bảng truy hồi |
| `Question` | Phase 12 query | Câu hỏi định lượng/định tính |
| `FinancialConcept` | Từ điển cố định | Khái niệm tài chính xác định |
| `WikidataEntity` | Snapshot Phase 11 | Thực thể ngoài đã khóa revision |

| Edge type | Source → target | Quy tắc |
|---|---|---|
| `HAS_REPORT` | Company → AnnualReport | Parse `report_id` |
| `HAS_PAGE` | AnnualReport → ReportPage | Parse `page_id` |
| `HAS_CHUNK` | ReportPage → Chunk | Quan hệ chunk gốc |
| `MENTIONS` | Question/Chunk → FinancialConcept | Exact lexicon boundary match |
| `SAME_AS` | Company/FinancialConcept → WikidataEntity | Chỉ exact validated alias duy nhất |

## Entity linking

Candidate generation và validation là hai bước tách biệt. Chỉ khi đúng một alias đã xác nhận khớp chính xác mới tạo `SAME_AS`. Match theo từ khóa, không có candidate, hoặc nhiều exact candidate đều được ghi vào audit với `decision=unresolved`; hệ thống không ép liên kết.

## Chống rò rỉ đánh giá

Retrieval graph không chứa `ANSWERED_BY`, `ANSWERED_BY_DOCUMENT`, `GOLD_EVIDENCE` hoặc `GOLD_RELEVANT`. Gold document/chunk chỉ tồn tại trong evaluation artifact của Phase 12 để tính metric sau khi truy hồi. `ASKS_ABOUT` của medical được suy ra bằng longest exact normalized phrase trực tiếp từ nội dung câu hỏi; `MENTIONS` của finance cũng chỉ dùng exact lexicon trên nội dung câu hỏi. Vì vậy TEST không thể đi tắt đến gold evidence qua graph.

## Offline query

`adjacency.json` chứa cả adjacency `out` và `in`, mỗi mục là `[edge_type, neighbor_id, edge_id]`. Vì vậy loader và path query không cần Neo4j hay dịch vụ ngoài.
