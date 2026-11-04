# Biên bản nghiệm thu Phase30 — hợp nhất KG–RAG V3

Ngày:20/10/2026. Phạm vi: Chương5, không thực hiện Phase31, HTTP/React V3 hoặc DOCX.
COMPLETE chỉ có hiệu lực khi `artifacts/manifests/phase30/experiment_lock.json` đã tạo
và `scripts/check_phase30.ps1 -Distribution Ubuntu` kiểm toàn bộ hash PASS.

## Kết quả chính

Source mới tại `src/ch05_knowledge_rag/` là adapter tối thiểu trên pure retrieval functions
và serialized index cũ. Không di chuyển/format implementation đã khóa, không re-fit,
rebuild corpus/graph/index, reserialize pickle hay đổi namespace serialized class.
`term_paper/__init__.py` vẫn là bridge. Không sửa source/evidence Phase26–29.

Catalog có3 dataset-tab descriptor: MedQuAD diabetes, FinQA và Wikidata snapshot. Hai
tab QA hỗ trợ B0–B4; tab Wikidata duyệt entity/revision/provenance, không bịa benchmark
QA thứ ba.15 pipeline contract slot gồm10 QA available và5 unavailable structural.
Registry `reused_registry.json` phân biệt index fit từ trước với model V3 vừa train,
không thay initialized registry Phase25.

Model schema Phase22 chỉ mô tả mạng neural. Extension có phiên bản
`phase30.retrieval_pipeline.1` mô tả logical function input/output, signature, vai trò,
corner case, composition và config refs; layer/parameter neural null vì không áp dụng.
API request/job/chapter/citation vẫn kiểm bằng schema V3 gốc, không sửa spec lock.

## Bảo toàn và dữ liệu

Đối chiếu inventory Phase20 trước migration:11.345 raw file Ch5,7config/23metric,
10 prediction TEST đều giữ hash; status COMPLETE và TEST run_count1 giữ nguyên byte.
Snapshot Phase30 bảo toàn11.490 asset, SHA-256:
`481071f65b2c01b8d132532bdaccaa08ff760b153b908bbf1906e72d2f1c310a`.
Dependency Phase22/24/25 đã kiểm31/294/219 file; V2/env/uv.lock và Phase29 lock giữ hash.
Raw cache upstream FinQA14 file không bị dọn; không tải dataset hoặc gọi dịch vụ ngoài.

CSV/JSON Phase15 được đối chiếu exact precision và identity/citation của6.045 prediction
đã lưu (62medical +1.147finance, mỗi miền5 cấu hình). Đây là saved-output audit, không
gọi evaluator, model construction hoặc forward TEST. Source raw/corpus/config/result
Phase11–19 giữ lại, manuscript/citation cũ không bị viết đè. Bản thảo mới giữ nguyên tập
literature citation keys của Chương5 cũ.

## Local demo và tương thích

Ba notebook mỏng trong `experiments/notebooks/v3/ch05_knowledge_rag/` đã chạy generator-owned
code qua runpy:10 QA slot và10 entity snapshot (2.056claim) PASS. Không chạy notebook do
bên ngoài gửi lên; chưa kiểm Jupyter UI/kernel picker. QA dùng cùng input giữa5 slot,
giữ B2 sparse0,75, B4 sparse/dense/graph0,6/0,1/0,3 và RRF60. Loader nạp đúng4 class
`term_paper.tools.phase14_rag.BM25Index/DenseLSAIndex` từ6 artifact68.393.687 byte.
Actual Python3.11.17/NumPy2.4.6/SciPy1.17.1/sklearn1.9.0; không nâng dependency/backend.

Bundle có762medical +86.421finance chunk,203 anchor. Cold load exporter quan sát4,04045s;
RSS high-water toàn process439.406.592byte (~419MiB), gồm matplotlib/exporter, không
phải peak mỗi request hoặc cam kết vừa tier cloud. Retrieval CPU, không import framework
GPU; không dùng GPU chỉ vì wrapper chọn venv torch.

Demo free-question tìm toàn corpus compact không có split metadata; benchmark lịch sử
giới hạn candidate theo split và dùng query-ID/full adjacency. Không so output hoặc
latency demo như TEST tái hiện. Timing demo cộng component dùng chung và answer, loại
cold load/serialize, không phải5 process benchmark độc lập/HTTP p95. Corpus URL/locator
raw từng chunk bị lược khỏi bundle không được bịa lại: citation V3 trỏ chunk container
SHA và chunk/document locator, URL cấp dataset. Citation tồn tại không chứng minh answer đúng.

## Report, visual QA và revision r2

Manuscript hiện hành **`report/sections/v3/ch05_knowledge_rag_r2.md`**, chọn qua
`artifacts/manifests/phase30/active_report.json`. Có data cards/mẫu/phân bố/giới hạn,
bảng hàm/hợp hàm dễ hiểu, một công thức RRF có giải thích và ví dụ, kết quả/nhận xét âm
được giữ nguyên. Agent cũ chỉ còn cầu nối ngắn sang Chương6; deploy là mục ngắn cuối chương.

Ba hình QA mới và4 hình r2 PNG300dpi/SVG đã xem đủ7 PNG và visual QA PASS. R2 sửa lỗi font,
nhãn ablation chật, sơ đồ node thiếu cạnh và phạm vi error-label; giữ r1/hình/metric/prediction
cũ nguyên byte. JSON `error_category_counts` gốc cộng TEST+challenge: entity linking8/1.061;
CSV lọc TEST cho0/1.053 và challenge8/8 medical/finance. Giữ đúng hai phạm vi, không sửa số
để làm chúng bằng nhau. Bảng graph_schema cũ còn một dòng nói lấy entity từ gold document;
đã đối chiếu extractor và mục chống leakage: anchor lấy longest exact phrase từ question,
fallback gold chỉ cấp provenance. Ghi chú minh bạch ở caption mới, không rebuild graph/TEST.

Kết quả cũ: medical Recall@5 B4=0,580645 so B2/B0=0,403226; finance B4=0,479512 so
B2=0,442895 nhưng B0=0,531822 cao hơn. Answer FinQA gần0, chưa có reasoning program;
không kết luận KG–RAG giải được bài toán số hoặc đủ an toàn y khoa/tài chính.

## Kiểm thử và rà soát

**341 test duy nhất PASS/0skip:78 Phase30 +263 regression V3.** XML nghiệm thu là
`final-tests-r2.xml` và `regression-tests.xml`; không cộng trùng các XML RED/development/
final65 test trước đó. Fixture package/snapshot synthetic chỉ tồn tại trong thư mục temp,
không được công bố làm dataset hoặc metric thật.

Coverage package `src/ch05_knowledge_rag/` gộp unit, producer CPU/report và kiểm bảo toàn:
**89,2791% dòng+nhánh**, statement92,1376%, branch80,5970%;407 statement. Source verifier/
CLI/builder được lint và chạy thật, không gộp giả vào mẫu số coverage package. Giữ lượt
coverage trước81,5157% và development79,6407% (dưới80 dù display làm tròn80) như lịch sử.
Ruff toàn source/test/script mới PASS; PowerShell wrapper parser PASS. Không cấu hình
static type checker; shape/schema kiểm runtime, không tự gọi đó là static-type-check PASS.

Regression giữ4 warning sklearn SimpleImputer/StandardScaler/Pipeline/ColumnTransformer
V2 (serialization1.9.1/runtime1.9.0). Đó không phải4 index KG–RAG (serialized sklearn1.9.0).
Không sửa artifact hoặc nâng env để che warning.

Security-review tập trung path containment/role allowlist/hash/size/budget trước joblib;
constructor I/O-free, safe unavailable job, input/domain/length whitelist, bounded evidence
trace và guardrail trước load. Hai điểm thực thi cần kiểm đã được giới hạn: joblib chỉ4
index local manifest pin SHA cứng; runpy chỉ code notebook do generator tạo. Không thêm
shell/eval/exec path, network call hoặc credentials. Scan secret-pattern chỉ source mới,
không tự nhận audit toàn Git history hoặc dependency vulnerability scan online.

## Bàn giao

Xem `docs/phase30_operations.md`, `docs/phase30_contract_extension.md` và
`docs/phase30_presentation_revision_r2.md`. Sau phát hành chỉ kiểm hash bằng wrapper;
không chạy coverage/producer vào file đã khóa. Đổi sau phát hành cần revision giữ evidence.
Không commit/reset/cleanup user data hoặc đổi môi trường trong phase này.

API contract local PASS không có nghĩa HTTP/React/Render V3 đã live. Chưa sửa web/API live
hoặc build/render DOCX; các bước đó thuộc32–35. Tiếp theo **Phase31 — hệ đa tác tử**,
chỉ khi người dùng yêu cầu.
