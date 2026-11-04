# FINAL Phase 1 — hoàn tất nền project01

Ngày 01/11/2026, Asia/Bangkok. Kế hoạch: `FINAL_PROJECT01_EXECUTION_PLAN.md`.

## Kết quả

Đã tạo `project01/` với datasets/notebooks/web và các thư mục hỗ trợ. Có catalog/path/hash nguồn dùng lại, schema hồ sơ, kiến trúc 5 vai trò, quyết định ngôn ngữ và protocol/bộ tình huống mới. Agent end-to-end, web và evaluation chưa làm trong phase này.

### Nguồn và mô hình đã kiểm

| Thành phần | Kết quả |
|---|---|
| DOCX nền | `tieuluan3/releases/v3/Tieu_luan_AI_6_chuong.docx`, 11.508.758 byte, SHA `5daf2aa5b5f587be5f61ecf7a2c6d32dc131c9ae2efe5df8630b4a23387060a5`; bản đã phát hành có 202 trang theo manifest cũ |
| Manuscript nền | `tieuluan3/report/phase34/manuscript.md`, xác định bằng release/active manuscript pointer, không lấy candidate tạm làm bản chính |
| CDC | 253.680 raw row, 21 feature; binary0=no diabetes, 1=prediabetes or diabetes; thống kê TRAIN/duplicate/missing từ EDA đã lưu |
| Model | Scratch seed42, checkpoint 40.022 byte, Dense64/64/32/32/16/1; preprocessing TRAIN-only và canonical feature order giữ nguyên |
| Probe model | Kernel WSL thật, 1 mẫu matched TRAIN `row_0048946`, tensor `(1,21)`, score `0.3955201804637909`; không chấm accuracy hoặc chạy TEST |
| KB | 762 medical chunk, 247 document, tiếng Anh; repository/commit + local locator, không có raw URL riêng từng document trong container |
| Graph | 62 concept anchor → chunk, tất cả ID hợp corpus; lexical graph phục vụ candidate/ranking, không ontology hoặc causal medical KG |
| Index | BM25/LSA tải được; hai index cùng đúng 762 ID; real query có kết quả hữu hạn, không nạp finance indexes |

Giữ 28 reference hash trong `baseline/inventory.json` cho các tài nguyên thực sự dùng lại và báo cáo/source nền. Không nhân bản raw/venv. Không rehash toàn bộ 31.848 file lịch sử trong Phase 1; scope này bổ sung cho bằng chứng read-back/handoff đã niêm trước đó, không thay thế chúng.

## Ngôn ngữ

Ba nhóm probe: physical activity, kidney disease, retinopathy. Raw tiếng Việt có 0/3 top3 ID giao với query tiếng Anh ở cả ba nhóm; sau ánh xạ cụm từ hữu hạn thì cả ba đạt 3/3. Đây là diagnostic lexical, không phải QA accuracy hoặc đánh giá dịch.

Chốt: UI tiếng Việt; retrieval/citation và trích đoạn tiếng Anh; cho nhập tiếng Anh và hỗ trợ tiếng Việt giới hạn bằng glossary có hiển thị normalized query. Không gọi là hiểu tiếng Việt tự do. Chưa cần API/LLM hoặc môi trường mới.

## Thiết kế và đánh giá

5 vai trò: Coordinator, Risk Agent, Knowledge Agent, Verifier, Reporter. Combined phải gọi cả model và RAG thật. Verifier kiểm nội dung hỗ trợ, không chỉ hash; có thể yêu cầu retrieval bổ sung một lần. Budget 30s/request, ≤8 tool attempts, retry/loop đều tính chung.

Protocol v1: 60 task tổng hợp mới = 20 development + 40 evaluation. Sáu nhóm: knowledge, numeric, combined, missing, out_of_scope, fault. Profiles là synthetic theo mã nguồn, gold evidence chọn theo nội dung corpus, không theo ranking. Không đọc QA TEST label cũ hoặc chạy mô hình trên parent TEST.

Audit PASS: không giao exact profile hash, gold document, selected evidence text hash hoặc group ID giữa hai split; profile bounds/schema hợp lệ; gold chunk/document/text khớp corpus. Câu hỏi vẫn là template có kiểm soát, không là khảo sát hành vi/ngôn ngữ thực tế; gold support chưa phải exhaustive qrels.

P0 được gọi trực tiếp cả hai tool trong combined, không cố tình làm yếu; P1 thêm coordinator/specialists, P2 thêm verifier/reporter và retrieval lại có giới hạn. Phase 2 đóng băng code/evaluator sau development rồi mới chạy 120 output (40×3). `evaluation_runs=0` hiện tại. Review hỗ trợ nội dung cần ghi người/agent chấm, không tự gọi là review lâm sàng hoặc human study.

## Runtime, runner và bảo toàn

Runner riêng: `project01/scripts/run.ps1` → `run.py`, dùng Ubuntu/user tuananh, Python3.11.17 .venv-torch CPU. Không sửa PROJECTS registry, runner/config hay notebook của 11 bài cũ. Runtime view tiểu luận3 chỉ để tương thích class/module serialized; ghi output sang project01/artifacts.

Probe kernel đã chạy thành công và lưu notebook mới ở `project01/artifacts/notebook_runs/`. Package import thực: NumPy2.4.6, SciPy1.17.1, scikit-learn1.9.0, joblib1.6.0, pandas3.0.6; loader/query PASS trong runtime hiện tại. Giữ serialization provenance của index cũ, không đổi nhãn version hoặc rebuild để khớp; deployment cần smoke riêng ở Phase 2.

Verifier hiện hành cho FINAL: `scripts/verify_final_project01.py`. Nó chạy verifier inline-v1 nguyên byte, chỉ resolve record AGENTS/README root lịch sử sang archive đã được cho phép, khớp đúng path/hash; các record còn lại phải qua kiểm bình thường. Root README đã thêm project01 và kế hoạch hiện hành. Không sửa handoff/verifier/lock cũ, không che drift file khác. Vì AGENTS/README hiện theo FINAL mới, không dùng verifier lịch sử trực tiếp trên root thay cho verifier revision này.

## Sản phẩm xem ngay

- `project01/README.md`: lệnh inspect/probe và cấu trúc.
- `project01/docs/architecture.md`: vai trò, input/output, hợp các hàm, API/state dự kiến.
- `project01/docs/evaluation_protocol.md`: rubric, split, biến thể và freeze/evaluation.
- `project01/docs/data_sources.md`, `language_scope.md`: nguồn/điều khoản/giới hạn.
- `project01/datasets/catalog.json`, `assets.json`, `profile_schema.json`, `query_glossary.json`.
- `project01/datasets/benchmark/{development,evaluation,audit,protocol_lock}.json`.
- Ba notebook: notebook01 chạy kiểm nền; notebook02/03 hiện là khung minh bạch cho Phase 2, chưa phải implementation agent/evaluator. Không dùng trạng thái Phase 1 COMPLETE để gọi toàn project COMPLETE.

## Nghiệm thu và phần tiếp theo

Probe kernel thật PASS; static notebook/schema/profile/gold/split/hash audit PASS; Ruff F/E9 PASS. Verifier FINAL xác nhận handoff REORG/inline-v1 và 28 tài nguyên dùng lại giữ nguyên. Training steps mới=0, historical TEST forward mới=0, project evaluation runs=0. Không đổi env, không deploy, không commit/push.

Phase 2 cần làm: full source trong notebook, query/graph/fusion + phối hợp model, verifier support/retrieval loop, export backend parity, React UI, đóng gói medical-only, development/freeze/evaluation/plots và smoke local. Không cần tải dataset mới, API key hay dựng GPU để bắt đầu.
