# Repository V3 — nguồn được giữ và cách khôi phục

Kế hoạch đang hoạt động: [Phase 20–35](../TIEU_LUAN_AI_V3_EXECUTION_PLAN.md).

## Các đường dẫn chính sau Phase 20

| Đường dẫn | Vai trò | Giai đoạn sử dụng tiếp |
|---|---|---|
| `apps/api/` | Flask API, KG–RAG service và bundle inference cũ nhỏ gọn | Phase 30, 32 |
| `apps/web/` | React UI hiện tại, giữ làm nguồn style và component | Phase 33 |
| `src/term_paper/` | Package V2 được giữ để tái sử dụng scratch/Keras/PyTorch và KG–RAG | Phase 25–30 |
| `term_paper/__init__.py` | Cầu nối import cho namespace đã được lưu trong checkpoint Ch5 | Giữ đến khi đã chuyển đổi serialization có kiểm chứng |
| `src/legacy_a06/` | Code tham chiếu RNN của A06, chưa dùng làm pipeline V3 | Phase 28–29 |
| `src/common/`, `src/ch02_ml/`…`src/ch06_multi_agent/` | Vị trí code V3 theo chương | Phase 25–31 |
| `experiments/notebooks/legacy/` | Notebook nguồn cũ; không chạy lại bằng đường dẫn cũ | Chỉ tham khảo và rút phần cần dùng |
| `experiments/configs/legacy_v2/` | Cấu hình cũ để đối chiếu | Phase 22, 25 |
| `experiments/configs/ch5/` | Cấu hình Ch5 được giữ nguyên byte/hash | Phase 30 |
| `data/raw/ch5/` | Snapshot MedQuAD, FinQA, Wikidata được giữ nguyên | Phase 23, 30 |
| `data/processed/v2/demos/` | Bốn input demo cũ đã chụp trước khi dọn dữ liệu | Chạy UI/API trong thời gian chuyển đổi |
| `artifacts/models/v2/` | Chỉ các model/preprocessor nhỏ thực sự phục vụ API cũ | Thay khi model V3 sẵn sàng |
| `artifacts/{metrics,figures,manifests}/ch5/` | Kết quả và provenance Ch5 đã khóa | Phase 30, 34 |
| `artifacts/predictions/ch5/phase15/` | Dự đoán public TEST đã chạy một lần | Chỉ đọc, không mở lại TEST |
| `report/` | Manuscript, sections, ảnh, bibliography và builder để cập nhật | Phase 34–35 |
| `releases/v2/` | DOCX/PDF baseline, báo cáo mẫu, source snapshot và metrics cũ | Chỉ đọc/khôi phục |
| `tests/api/` | Regression API còn chạy được với bundle nhỏ giữ lại | Phase 20, 32 |
| `tests/legacy_v2/` | Test cũ để tái sử dụng; nhiều test phụ thuộc dữ liệu đã nghỉ | Chọn test phù hợp khi chuyển từng module |

Namespace `term_paper` được duy trì vì các file joblib Ch5 đã lưu tên lớp như
`term_paper.tools.phase14_rag`. Đổi tên trực tiếp sẽ khiến checkpoint không load được. Source
thật nằm trong `src/term_paper/`; thư mục `term_paper/` ở root chỉ có cầu nối import.

## Phần đã nghỉ

Các root `A05/`, `A06/`, `pipeline/`, `pipeline04/`, `datasets/`, `mobile/`, `backend/` và
`web/` được thay bằng các đường dẫn ở bảng trên. Dataset cũ, checkpoint không còn dùng,
render từng trang, output trung gian, venv, cache và `node_modules` được dọn.

V2 source đã được lưu từ working tree, bao gồm thay đổi chưa commit, trong
`releases/v2/source_snapshot.zip`. Mỗi thành viên có SHA-256 trong
`releases/v2/source_snapshot_manifest.csv`; các file nhị phân phát hành có hash riêng trong
`releases/v2/release_manifest.json`.

## Kiểm kê và recovery

- `artifacts/manifests/phase20/before-files.csv.gz`: file, byte size, SHA-256, trạng thái Git và phân loại trước dọn.
- `artifacts/manifests/phase20/migration-plan.csv`: đích di chuyển đã duyệt.
- `artifacts/manifests/phase20/operations.csv`: các thao tác thực tế và nguồn khôi phục.
- `artifacts/manifests/phase20/git-head-before.txt`: commit để khôi phục các file đã tracked.
- `artifacts/manifests/phase20/git-status-before.txt`: thay đổi có sẵn trước khi dọn.
- `artifacts/manifests/phase20/verification.json`: kiểm chứng hash, source, notebook và TEST seal.
- `artifacts/manifests/phase20/after-summary.json`: số liệu sau dọn, tách riêng `.git`.
- `artifacts/manifests/phase20/file-outcomes.csv.gz`: kết quả cuối và nguồn khôi phục cho từng file.

Các bảng CSV lớn được nén gzip để source gọn. `phase20_verify.py` đọc trực tiếp bản nén;
có thể giải nén để xem bảng khi cần.

Khôi phục source chưa commit bằng cách mở ZIP, chọn đúng file theo tên gốc và đưa vào một thư mục
khôi phục riêng để xem lại trước khi chép vào source đang làm. Khôi phục dataset/output đã tracked
bằng `git show <commit>:<đường_dẫn_gốc>` hoặc một checkout riêng của commit trong manifest.
Không dùng lệnh reset cả worktree đang có thay đổi.

Các package/cache có thể cài lại từ lock/requirements; dataset cũ bị thay thế sẽ được thu nhận
lại từ nguồn đã ghi trong notebook/source registry nếu thật sự cần. `.env` local được giữ riêng
và không đưa vào source snapshot hay log.

## Giới hạn của Phase 20

Phase này chuẩn bị cấu trúc và giữ khả năng chạy demo cũ. Các notebook lịch sử và builder báo cáo
cũ còn tham chiếu đường dẫn V2; chỉ chạy trong snapshot V2 đã khôi phục. Phase 25/30/34 sẽ chuyển
runner, KG–RAG pipeline và report builder sang contract V3 trước khi sử dụng lại. Không coi toàn
bộ test thực nghiệm V2 là test nghiệm thu V3.

14 file `__pycache__/*.pyc` thuộc chính snapshot upstream FinQA đã được khôi phục từ đúng commit
`0f16e2867befa6840783e58be38c9efb9229d742` và khớp SHA-256 gốc. Chúng là dữ liệu snapshot chỉ đọc;
quy tắc dọn cache chỉ áp dụng ngoài `data/raw/`.

Smoke KG–RAG phát hiện các index sklearn được tạo bằng 1.9.0 trong khi môi trường cũ dùng 1.9.1.
Hai truy vấn demo vẫn trả HTTP 200. Phase 21/30 cần khóa phiên bản phục vụ artifact cũ hoặc rebuild
bundle tương thích bằng snapshot/config đã khóa; không tuning hoặc chạy lại TEST để xử lý việc này.

