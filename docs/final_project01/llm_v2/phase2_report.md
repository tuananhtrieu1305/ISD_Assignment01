# Phase2 v2 — IN_PROGRESS / WAITING_PROVIDER

Ngày02/11/2026. **Chưa hoàn tất Phase2.** Code/index/UI đã triển khai; Gemini trả timeout/HTTP503 nên chưa có một câu trả lời RAG hoàn chỉnh. Không mở held-out hoặc freeze để lấy điểm khi development chưa đạt. Đã dừng mọi worker/server local của lượt này, không có queue chạy nền.

## Phần đã làm và kiểm

- Bảo toàn33 file notebook/web/README/runner cũ trước sửa;502 pin lịch sử resolve đúng archive,120 output P0/P1/P2 giữ nguyên;167 file handoffPhase1 khớp hash. Không train/TEST/evaluation cũ.
- Port core nhóm vào đúng3 notebook, export một chiều16 module `project01_llm_v2`. Bản đồ actual_reuse.json có45 symbol khớp AST và30 symbol được adapter; namespace và import mới không cần folder tham khảo/provenance. Cả7 helper inference CDC và predict giữ logic gốc, không load pickle retrieval cũ.
- Env serving WSL Python3.11.17 riêng,91 entry trong lock/88 package cài tương thích; kernel **Project01 Gemini serving (WSL3.11)**. Hai env GPU giữ nguyên. Notebook/plot tách dependency-group khỏi requirementsRender.
- Index mới đủ316 chunk, embedding-001/768 chiều/L2, cache/metadata/hash; KG35 assertion có nguồn và graph candidate đi vào RRF. Group cache/normalize/aggregate/PyVis đã port; seed curated đủ dùng nên chưa gọi extractor tự động. HTML graph hiện hành: `project01/artifacts/llm_v2/kg/neighborhood_development_r3.html`.
- Queue chung, durable call IDs/cache, lưu claim trước gửi, không tự replay unknown, cap18 generation/day, không paid fallback. Tắt SDK continuation/retry ẩn trong code hiện hành; ghi riêng SDK attempts và cache. API health không gọi LLM, `/ready` chỉ data/config và trạng thái call gần nhất.
- 28 kiểm tra chức năng PASS, API thật trong kiểm tra=0: RRF/KG/quote/vector, thiếuBMI, chặn citation/số bịa, schema/CORS, guard503/unknown/quota. Mock chỉ dùng tái hiện lỗi, không là nghiệm thu câu trả lời LLM.
-3 notebook chạy source với API/train/TEST/evaluation tắt, có output thật/đọc saved output;16 module source-export parity PASS.
- React build PASS; desktop/mobile layout6 check và saved partial-output8 check PASS, không mock. Hai thẻ câu trả lời đứng cạnh nhau, markdown được render dưới dạng text an toàn; nguồn/trace nằm dưới. Saved development giữ trạng thái lỗi và nhãn saved, không giả thành live/complete.
- Copy độc lập chỉ có project01: index/KG/Risk/Flask/WSGI PASS, network bị chặn, không key/provenance/folder tham khảo. React build trong copy PASS. Đây là **source-only proof**, chưa chứng minh fresh live RAG end-to-end.
- Đã chuẩn bị README/local/GitBash/kernel và blueprint2service Render CPU; chưa commit/push/deploy. Package/freeze phát hành cuối còn chờ live acceptance.

## API thật đã chạy

Phase2 có **50 logical SDK attempt** (chi tiết theo kind/status ở progress_20261102.json). Đây không là lời khẳng định đã đo riêng mọi wire HTTP request. Embedding index và query chạy thành công. Generation đã có câu direct thật, query plan JSON thật và rerank JSON thật; Reporter còn lỗi, Verifier live chưa được nghiệm thu. **0/2 cặp development hoàn chỉnh;0/80 held-out output.**

Các lỗi giữ nguyên:
- `d203e69833611dba8ebe032b903e4cdbd2b6a1fb5cdaf733d0d3cd292b3abd17`: APITimeoutError / HTTPNone.
- `964c4decd183c30c976685f98f6c23ea79e3b505ddda5239b9e42d28a605cd23`: APITimeoutError / HTTPNone.
- `357370b4016ff179d0d059a91bf34ea5253e4586c143ff7359391e5b9d5d06e4`: InternalServerError / HTTP503.
- `931d01c6e25c415cdb51d0d6911ff2eea405a1f74de0c72e42e4f443baa19452`: APITimeoutError / HTTPNone.

Unknown sau timeout có thể đã xử lý ở provider; usage chưa biết, không điền0tokens. HTTP503 là lỗi provider được quan sát, không tự quy là hết quota hoặc thiếu key. Ngân sách trả phí0USD, không bật billing/đổi model/đổi key; chưa kiểm hóa đơn.

Developmentr2 tăng timeout90→180s, deadline1500s và giữ claim lỗi cũ; rerank:r2 đã trả JSON. R3 quan sát đúng câu đảo chiều: tất cả candidate chỉ0,1–0,4; đặt evidence gate≥0,5 trước held-out và Reporter80–120từ/tối đa3claim. Điểm này không là xác suất relevance đã hiệu chuẩn. Reporter ngắn hơn vẫn nhận503. Không coi threshold/guard code là chứng minh câu trả lời cuối đã đúng. Chưa kết luận nhánh nào thắng; direct development chưa được thẩm định lâm sàng.

## Tiếp tục đúng bước

Gõ **làm tiếp task đang dở** để tiếp Phase2. Đọc plan/checkpoint/report này, kiểm lại khả năng đáp ứng Gemini và quota free bằng một probe mới có giới hạn. Không tự gửi lại các claim unknown cũ hoặc xóa ledger. Khi API ổn, ghi revision development mới, dùng runner `--claim-revision development-r4` (chưa chạy) cho hai câu đã khai báo; giữ phiên cũ làm lịch sử. Code câu trả lời/prompt còn được sửa ở notebook trước freeze, cần lưu revision tương ứng.

Sau khi hai cặp development và fresh live API/UI đạt, khóa corpus/index/KG/model/prompt/code/evaluator/rubric rồi mới chạy40×2 theo journal nhiều ngày. Review ẩn nhánh và3 biểu đồ đã có code trong notebook03 nhưng **chưa sinh chart chất lượng vì chưa có80 output/review**. Không mở Phase3/DOCX hoặc xóa `RAG_KG_Tham_khao/` trong trạng thái này.

Checkpoint: `docs/final_project01/llm_v2/checkpoint.json`. Chi tiếtAPI: `project01/artifacts/llm_v2/phase2/api_calls/`. Source snapshot bảo toàn: `project01/provenance/llm_v2_phase2_checkpoint_20261102/`. Cách chạylocal: `project01/docs/llm_v2/RUN_LOCAL.md`. Secret scan221 file PASS; key vẫn chỉ ở ignored.env.
