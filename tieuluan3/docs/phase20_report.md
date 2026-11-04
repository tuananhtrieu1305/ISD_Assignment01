# Biên bản Phase 20 — 2026-10-16

Phase 20 hoàn thành. Source đã được gom về cấu trúc V3 và có bằng chứng khôi phục theo từng file.

| Nội dung | Kết quả |
|---|---|
| Kiểm kê trước dọn | 105.995 file; 3.638.109.790 byte, chưa tính `.git` và thư mục manifest kiểm kê |
| Working tree sau dọn | Khoảng 329 MB, tính cả manifest nén; khoảng 12 nghìn file, phần lớn là raw Ch5 local |
| Tiết kiệm | Khoảng 3,31 GB, tương đương 91% working tree ban đầu |
| Git store | 1.954.131.896 byte, khoảng 1,82 GiB; giữ lịch sử |
| DOCX V2 | Khớp SHA-256 `d7286dd4867e6216f197414e42fc112a3759621c017839fa9b1491b7c5dbfa51` |
| Source snapshot | 998 thành viên được kiểm tra hash; gồm source có thay đổi chưa commit |
| Notebook nguồn | 26 notebook hợp lệ, giữ trong `experiments/notebooks/legacy/` |
| Raw Ch5 | 11.345 file khớp hash gốc |
| Public TEST Ch5 | 10 prediction khớp hash; run count vẫn bằng 1 |

Các nguồn được giữ và đường dẫn mới nằm trong [repository_manifest.md](repository_manifest.md).
Danh sách di chuyển/xóa nằm trong `artifacts/manifests/phase20/operations.csv`; bảng kết quả
cho toàn bộ file ban đầu nằm trong `file-outcomes.csv.gz` cùng thư mục.

## Xác minh

| Kiểm tra | Kết quả |
|---|---|
| Regression API sau di chuyển | 31/31 đạt; JUnit `api-tests.xml` |
| Scratch MLP/CNN/RNN | 3/3 đạt; forward, gradient hữu hạn, save/load parity; JUnit `scratch-tests.xml` |
| React helpers sau di chuyển | 10/10 đạt |
| TypeScript | `tsc --noEmit` đạt trước di chuyển |
| Production web build | Vite build đạt trước di chuyển; dependency/build output đã được dọn sau đó |
| KG–RAG bundle thật | 2 miền medical/finance trả HTTP 200; `runtime-smoke.json` |
| Python source | AST parse đạt trên source được giữ; không cần cài framework mới |
| Preservation verifier | `python -B scripts/phase20_verify.py` đạt |
| Deploy verifier | `python -B scripts/phase20_verify.py --deploy` đạt |
| Git diff whitespace | Đạt trên các file cấu hình/README/kế hoạch được sửa |

Các kiểm tra này không chạy huấn luyện dataset thật và không mở lại evaluator public TEST.
Coverage toàn dự án chưa được đo lại vì đây là phase migration; test GPU/framework thuộc Phase 21–29.

## Những phần đã dọn

Đã gỡ venv, `node_modules`, cache local, render QA, dữ liệu/mô hình/output thừa của A05/A06,
pipeline cũ và ứng dụng mobile. Notebook/source/metrics cần đối chiếu được giữ trực tiếp hoặc
đóng băng trong source snapshot. Các model nhỏ phục vụ bốn demo hiện hữu được giữ thành một bundle.

Private `.env` được giữ local; không đưa giá trị vào archive hay log. Helper Black formatter của
VS Code đang giữ venv cũ đã được dừng để xóa môi trường. Phase 21 sẽ cấu hình interpreter mới.

## Điều chỉnh và giới hạn chuyển tiếp

- Namespace `term_paper` được giữ bằng cầu nối để load joblib Ch5; source thật nằm trong `src/`.
- Các notebook/runner/report builder lịch sử còn đường dẫn V2 và được chuyển ở Phase 25/30/34.
- Đã thử chọn các test NumPy từ suite legacy nhưng collection còn phụ thuộc framework và cấu trúc
  package cũ. Smoke NumPy độc lập đã thay thế kiểm tra migration; không đánh dấu toàn bộ suite legacy đạt.
- Verifier phát hiện 14 file cache thuộc upstream FinQA bị dọn. Đã tải lại từ commit đã khóa,
  xác nhận hash và bổ sung ngoại lệ bất biến cho `data/raw/`.
- Bundle Ch5 có cảnh báo sklearn 1.9.0 → 1.9.1 khi load trong env cũ; demo đạt. Phase 21/30 phải
  khóa đúng phiên bản hoặc rebuild bundle tương thích mà không tuning/rerun TEST.
- Git vẫn hiển thị nhiều deletion/migration chưa commit. Không tạo commit và không viết lại history.

Bước tiếp theo: `làm phase 21`.
