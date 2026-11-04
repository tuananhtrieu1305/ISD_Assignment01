# Phase 1 v2 — COMPLETE, 02/11/2026

Đầu vào đã sẵn sàng để port pipeline ở Phase 2. **Chưa đổi web/notebook/backend, chưa chạy benchmark LLM mới.**

## Kết quả nghiệm thu

| Hạng mục | Kết quả / bằng chứng |
|---|---|
| Copy source nhóm |36 file local,21 file không cần dùng có lý do;57 original hash và36 copied hash khớp;63 internal import được resolve tĩnh. `project01/provenance/group_rag_kg_source/transfer_manifest.json` |
| Bản đồ port |16 thành phần: strategy/RRF/retriever/BM25/chunking/indexer/embedding/vector/rerank/generation/prompt/schema/pipeline/config/logging/KG; original→copy→cell/export dự kiến trong `project01/docs/llm_v2/reuse_map.json`. **Copied, chưa port** |
| Gemini generation |`gemini-3.8-flash`, Interactions `store=false`, probe PASS;8 total tokens provider trả (7 input/1 output), latency29.282ms. Receipt `gemini_interactions_preflight.json` |
| Embedding |`gemini-embedding-001`, RETRIEVAL_DOCUMENT/768 chiều, finite/nonzero PASS;624ms; provider không trả usage, ghi null. Không tạo index; receipt `gemini_embedding_preflight.json` |
| Quota |Người dùng xác nhận generation5 RPM/250k TPM/20 RPD; embedding100 RPM/30k TPM/1000 RPD; chọn giữ model, chạy nhiều ngày. `quota_user_confirmation.json` |
| Key |Đã lưu đúng yêu cầu vào ignored `project01/.env`, không tracked/không in lại; scan83 file mới/source chuyển không chứa giá trị key |
| Corpus |Tải đúng MedQuAD commit/hash;45 tài liệu/210 QA/316 chunk/409 source refs,45 URL gốc,348.397 ký tự; kiểm toàn bộ offsets/hash/dedup PASS |
| KG seed r2 |35 entity,35 assertion,20 source chunk từ17 document; toàn bộ quote/endpoints/direction/conditions/review kiểm PASS;31 entity có cạnh,4 alias-only. Bản seed đầu giữ nguyên |
| Protocol |20 dev+40 held-out,60 fact-family;không trùng exact question held-out với40 câu cũ; chưa gọi model trên câu nào. Reference có quote/qrels nhiều chunk, chưa exhaustive |
| Runtime |Audit env hiện có; khóa72 package serving riêng bằng WSL Python3.11.17/uv. **Chưa cài/smoke env serving**; hai env GPU không đổi |
| Bảo toàn |Hai verifier chỉ đọc `verify_final_project01.py` và `verify_answer_first_v2.py` PASS;29 notebook/11 bài,3 notebook project01/export4 module,26 file frozen và120 output cũ giữ nguyên |

Receipt tổng: `project01/artifacts/llm_v2/phase1/acceptance.json`. Handoff/hash đầu vào: `phase1_handoff.json` cùng thư mục báo cáo. Verifier lịch sử đọc receipt cũ, không chạy lại browser/model/TEST; số integration/browser trong output là bằng chứng lịch sử được đối chiếu.

## API đã gọi thật

Tổng **5 HTTP request**:1 list models,3 generation attempt,1 embedding. Generation gồm:

1. `gemini-3.8-flash` qua generateContent: timeout40s; usage phía provider không biết. Receipt lỗi giữ nguyên.
2. Compatibility probe `gemini-2.5-flash` qua generateContent:404; không chọn làm model chính. Receipt giữ nguyên.
3. `gemini-3.8-flash` qua Interactions: PASS.

Không ghi nhận output benchmark từ các probe này. Free tier do người dùng xác nhận và đối chiếu [bảng giá chính thức](https://ai.google.dev/gemini-api/docs/pricing); ngân sách trả phí0 USD, không bật billing/chuyển model trả phí. Không khẳng định đã xem hóa đơn. SDK bridge Interactions và semantic query/index còn cần smoke ở Phase2; preflight HTTP không tự chứng minh toàn pipeline đã chạy.

## Vì sao đánh giá phải chia nhiều ngày?

80 output =40 câu×2 nhánh, nhưng RAG thông thường cần4 call (planner/rerank/reporter/verifier), direct cần1. Dự trù200 generation call; nếu mọi câu cần1 feedback thì320, chưa retry/development. Với20 RPD, evaluation cần tối thiểu10–16 ngày nếu dành toàn quota; cap ứng dụng18 RPD là12–18 ngày. Development đầy đủ20 cặp có thể thêm100–160 call; ưu tiên vài development case để sớm có demo, không tự cắt held-out. Người dùng đã chọn giữ Gemini3.8Flash và chấp nhận nhiều ngày.

Queue/deadline/quota ledger là contract ở Phase1, implementation ở Phase2. Đầu mỗi phiên phải refresh usage ngoài app; hết ngày dừng/checkpoint, không tiến trình ngủ dài. Không dùng thêm key né quota hoặc tự chạy evaluation nền khi người dùng chưa gọi Phase2.

## Chất lượng dữ liệu và giới hạn

Corpus phục hồi từ XML gốc có đủ QA/URL, thay vì đoạn rời thiếu ngữ cảnh. Chọn theo nguồn/phạm vi, không ranking hoặc lỗi held-out. KG là curation trợ lý, chưa gọi extractor và chưa có thẩm định y khoa. R2 bổ sung8 QA nguồn so với seed đầu, giữ cả hai revision. Không dùng số cạnh làm confidence; cạnh có điều kiện phải đọc kèm full QA, ví dụ đường huyết **an toàn** hỗ trợ bảo vệ thần kinh, không phải đường huyết cao.

MedQuAD là snapshot lịch sử; một số bảng/list flatten và thông tin sàng lọc/thống kê có thể cũ. Bộ câu hỏi tránh kê liều hoặc lời khuyên số cá nhân; không tuyên bố nguồn là guideline2026. Held-out do trợ lý tự soạn và đã biết khi viết reference, nhưng chưa dùng development hay gọi model; không gọi là benchmark độc lập mù với tác giả hoặc chất lượng lâm sàng. Semantic split review thủ công theo fact-family, kiểm tự động chỉ xác nhận family/exact question; không nhận đã chứng minh mọi paraphrase độc lập tuyệt đối.

## File được thay và cách tiếp Phase2

Chỉ thêm nhánh `llm_v2`, scripts vận hành chuẩn bị dữ liệu/config/probe, source snapshot chọn lọc và serving lock. `project01/.gitignore` thêm allowlist cho corpus/QA JSON nhỏ; bản gốc ở `project01/provenance/before_llm_v2_phase1/project01.gitignore` (SHA256 `5999a314699a92666945de201fc9fc77495ded92fd2748cbeab30834a048ced8`). Raw tar/XML, env/key vẫn ignored. Metadata/hash nhỏ cho phép versioning; chưa commit.

Phase2 phải đọc plan/checkpoint/biên bản/handoff này, quy tắc revision notebook và lưu bản gốc3 notebook/UI/backend trước sửa. Port từ snapshot **trong project01** vào notebook, export namespace riêng; không runtime import provenance. Tạo serving env riêng từ lock; probe SDK bridge/query embedding; làm luồng dọc thật trước UI; KG→RRF/rerank→citation rồi agents/Verifier. Freeze trước evaluation, journal resume nhiều ngày. Phiên này không mở Phase2, không xóa folder tham khảo, train/TEST, commit/push/deploy hoặc tạo DOCX.
