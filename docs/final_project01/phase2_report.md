# FINAL Phase 2 — project01 end-to-end và đánh giá

Ngày 01/11/2026, Asia/Bangkok. Kế hoạch `FINAL_PROJECT01_EXECUTION_PLAN.md`.

## Sản phẩm

- `project01` có 3 notebook đầy đủ code thật và output kernel: foundation/model/retrieval, agents/API, evaluation/plot. Backend gồm4 module export từ cell; source checksum bỏ output nên có thể cập nhật cache output mà không đổi code đã freeze.
- Pipeline thực nhận câu hỏi → sparse/LSA/lexical graph → fusion → trích xuất; combined có cả score CDC và evidence. Năm vai trò có hợp đồng, validation, state/trace, verifier và retrieval loop hữu hạn. Hệ theo luật, không LLM hoặc reasoning mở.
- React UI giữ style tiểu luận3,4 khu: câu hỏi/hồ sơ, kết quả/nguồn, trace, so sánh. Bấm chạy thực thi P0/P1/P2 cùng đầu vào. Hồ sơ không bị impute khi thiếu; knowledge-only không phụ thuộc field profile. Benchmark table đọc kết quả đã lưu.
- Medical package v1:4.772.359 byte,762 chunk/247 document/62 anchors, không finance, không fitting/train. Standalone serving clone chỉ chứa project sources/package/notebooks và JSON demo đã chạy được model+RAG, không có tieuluan3/runtime view.
- Node lock tối thiểu47 package từ dependency đã có; không cài/nâng GPU env. Python requirements chỉ CPU. Render template và build/start/check entrypoint có health/ready/source parity, chưa tạo service/deploy.

## Nghiệm thu triển khai

18 integration tests PASS: model parity với frozen implementation trên3 TRAIN sample, real query/graph, nhánh combined5roles, missing/invalid/age codes, glossary/policy, semantic-support heuristic ngoài hash, numeric consistency, retry, timeout thật không còn worker, package tamper, API input/CORS/oversize/privatefault, readiness source drift và baseline-rubric fairness.

Index parity với code gốc PASS3 query×2 index:top10 ID giống nhau,score difference≤1e-6. Đây là query mới/development, không QA TEST cũ. Ba notebook chạy Jupyter kernel thật; output nằm ngoài notebooks rồi copy cache về canonical với source hash không đổi.

UI kiểm bằng Chromium không mock:15 checks trước freeze,18 checks ở bản cuối gồm desktop/mobile, live model/evidence,10 candidates,5roles, ba biến thể, thiếu BMI, glossary, saved reviewed table, không page overflow/uncaught JS. Ba plot đã xem; chỉnh font/bounding-box bằng style wrapper gọi đúng hàm frozen notebook03 để hết cắt tiêu đề. Bản hình đầu và lineage giữ trong provenance.

## Freeze và evaluation mới

`project01/artifacts/phase2/freeze.json` pin26 file source/evaluator/config/package/task set và3 notebook source hash trước evaluation. Sau khi nhìn output evaluation không đổi pipeline/evaluator hoặc chạy lại để tăng điểm. 40 case×3variant=120 claim/raw output; controller finished,pid=null. Task set Phase1 giữ nguyên, evaluation_runs thực tế1/cặp.

`evaluation/raw_results/` giữ nguyên bytes ban đầu. `evaluation/results/` là revision dẫn xuất chỉ bổ sung review/task labels, mỗi file có `derived_from` path/hash; audit kiểm result payload/score/citation/trace/timing bằng đúng raw. 54 review answer/citation do **Codex assistant**, không independent human hoặc clinical validation. Không coi citation đúng hash là câu trả lời đủ nghĩa.

| Variant | Automatic checks | Task success sau review | Support | Known-positive doc hit@10 | p50/p95(ms) |
|---|---:|---:|---:|---:|---:|
| P0 |38/40|33/40=82,5%|11/18|2/16|18,79/44,49|
| P1 |38/40|33/40=82,5%|11/18|2/16|16,99/48,97|
| P2 |40/40|33/40=82,5%|11/18|2/16|18,21/55,48|

P2 chặn numeric tamper/phục hồi citation, nhưng lớp trích xuất có fragment, thiếu ngữ cảnh subtype, câu sai trọng tâm hoặc chỉ “Learn more”. Vì vậy automatic checks tốt hơn chưa thành task success tổng thể cao hơn; giữ nguyên số liệu và nêu rõ giới hạn. Benign numeric/combined có48/48 numeric parity, không là predictive accuracy. Known-positive hit12,5% không phải full recall vì qrels chưa exhaustive. Tool mean dùng39 request có telemetry/variant, timeout unknown không gán0. Phân tích trục/đơn vị/mẫu số từng plot ở `project01/report/Project01_Report.md`.

## Bảo toàn và thao tác tiếp tục

Verifier Phase2 đọc saved outputs, tái tính metric/review/summary, kiểm raw lineage/freeze/package/notebook/export và120unique pair. Verifier FINAL kiểm28 tài nguyên tái sử dụng + handoff REORG/inline/Phase1 qua archive dispatcher/README đúng hash. Không sửa source/raw/checkpoint/metric/prediction/TEST cũ, không đổi env, không train, không commit/push/deploy.

Source authority là notebook; giữ draft Phase1 và authoring đầu trong provenance, không seed lại. Dùng `notebook_source.py check` hoặc `verify_phase2.py`, không gọi `experiment.py evaluation` nữa. Thay thuật toán sau freeze cần revision/thử nghiệm mới; không tune bộ evaluation này.

Chạy local từ root:

```powershell
./project01/scripts/build_web.ps1
./project01/scripts/run_web.ps1
```

Mở http://127.0.0.1:8031. Tiếp theo Phase3 khi người dùng yêu cầu: đưa case study vào chương6, nối với chương5, tích hợp tab demo tiểu luận3 và xuất DOCX final. Chưa tự bắt đầu Phase3 và chưa sửa tiểu luận3 đã phát hành.
