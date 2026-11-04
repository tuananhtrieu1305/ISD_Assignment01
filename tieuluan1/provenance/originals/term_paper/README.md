# Term Paper Workspace

Thư mục này chứa toàn bộ nội dung mới của tiểu luận AI/ML/CNN/RNN. Các assignment gốc trong `pipeline/`, `A05/` và `A06/` được xem là nguồn chỉ đọc; không ghi đè notebook, dataset, model, metric, figure hoặc report hiện có.

## Source of truth

Kế hoạch và trạng thái phase nằm tại:

- `../TIEU_LUAN_AI_EXECUTION_PLAN.md`

Khi thực hiện một phase, phải cập nhật bảng trạng thái và nhật ký trong file trên.

## Phase 0 artifacts

- `artifacts/manifests/source_inventory.json`: inventory tổng hợp, số lượng artifact và trạng thái Git ban đầu.
- `artifacts/manifests/source_hashes.csv`: SHA-256 của notebook, raw data quan trọng, model, metrics, predictions và reports.
- `artifacts/manifests/notebook_audit.csv`: cấu trúc, execution metadata, error output và framework signal của 16 notebook.
- `artifacts/manifests/folder_manifests/`: manifest deterministic theo path/kích cỡ/mtime cho kho ảnh, processed arrays và figure folders.
- `artifacts/manifests/gap_analysis.md`: gap analysis và mapping kết luận → artifact nguồn.

## Rebuild and verify Phase 0

Chạy từ workspace root bằng Windows PowerShell:

```powershell
& '.\term_paper\tools\build_phase0_inventory.ps1' -WorkspaceRoot 'C:\DATA\assign'
& '.\term_paper\tools\verify_phase0_inventory.ps1' -WorkspaceRoot 'C:\DATA\assign'
```

Script build chỉ đọc nguồn và chỉ ghi vào `term_paper/artifacts/manifests/`.

## Current status

- Phase 0–9: COMPLETE; DOCX release 73 trang đã qua kiểm tra accessibility, metric–artifact, link/citation, metadata, phân trang và QA trực quan.
- Artifact cuối: `report/Tieu_luan_AI_ML_CNN_RNN.docx`.
- Trạng thái chính thức và nhật ký chi tiết luôn nằm trong execution plan.

## Rebuild and verify Phase 8

Build nguồn DOCX có thể chạy lại từ `report/manuscript.md` và `report/assets/`:

```powershell
& 'C:\Users\anhca\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.\term_paper\report\build_report.py' --page-map '.\term_paper\report\qa_phase8\word_page_map_final.json'
& '.\term_paper\report\word_paginate_export.ps1' -DocumentPath '.\term_paper\report\Tieu_luan_AI_ML_CNN_RNN.docx' -BuildLogPath '.\term_paper\report\build_log.json' -PageMapPath '.\term_paper\report\qa_phase8\word_page_map_final.json'
& 'C:\Users\anhca\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.\term_paper\report\validate_report.py'
```

Artifact: `report/Tieu_luan_AI_ML_CNN_RNN.docx`. Build log và kết quả kiểm tra lần lượt ở `report/build_log.json` và `report/report_validation.json`.

## Verify Phase 9 release

```powershell
& 'C:\Users\anhca\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.\term_paper\report\verify_phase9.py'
```

Release audit và các log QA nội bộ nằm trong `report/qa/phase9/`. Bản DOCX trong `report/` là artifact duy nhất dùng để nộp.

## Rebuild and verify Phase 3

Chạy từ workspace root bằng Windows PowerShell với môi trường `tf312`:

```powershell
& 'C:\Users\anhca\anaconda3\envs\tf312\python.exe' -m term_paper.src.common.run_ch2_experiments
& 'C:\Users\anhca\anaconda3\envs\tf312\python.exe' -m term_paper.src.common.ch2_reporting
& '.\term_paper\tools\verify_phase3.ps1'
```

Notebook đã execute nằm tại `notebooks/ch2_ml_framework_comparison.ipynb`; chương viết nằm tại `report/sections/02_ml_co_ban.md`.

## Rebuild and verify Phase 4

```powershell
& 'C:\Users\anhca\anaconda3\envs\tf312\python.exe' -m term_paper.src.common.run_ch3_experiments
& 'C:\Users\anhca\anaconda3\envs\tf312\python.exe' -m term_paper.src.common.ch3_reporting
& '.\term_paper\tools\verify_phase4.ps1'
```

Notebook đã execute nằm tại `notebooks/ch3_cnn_framework_comparison.ipynb`; chương viết nằm tại `report/sections/03_cnn.md`.

## Rebuild and verify Phase 5

```powershell
& 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe' -m term_paper.src.common.run_ch4_experiments
& 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe' -m term_paper.src.common.ch4_reporting
& '.\term_paper\tools\verify_phase5.ps1'
```

Notebook đã execute nằm tại `notebooks/ch4_rnn_framework_comparison.ipynb`; chương viết nằm tại `report/sections/04_rnn.md`. Track matched dùng hidden size 32 và ba seed; customer dùng fixed subset 30.000/8.000/8.000 từ split A06, còn AAPL dùng toàn bộ processed arrays.

## Run and verify Phase 6

```powershell
& '.\backend\.venv\Scripts\python.exe' -m backend.app
cd web
npm run dev
```

Kiểm thử backend và frontend từ workspace root:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest backend\tests -q
cd web
npm test
npm run build
cd ..
& '.\term_paper\tools\verify_phase6.ps1'
```

Ứng dụng public nằm trong `../backend/` và `../web/`; Blueprint/hướng dẫn Render
nằm tại `../render.yaml` và `../RENDER_DEPLOY.md`. Runtime mô hình, bản server
Phase 6 nguyên gốc và hướng dẫn Docker vẫn nằm trong `deployment/`. Phần 5 nằm
tại `report/sections/05_trien_khai.md` và ảnh chụp nằm tại
`report/assets/deployment/`.

## Rebuild and verify Phase 7

```powershell
& '.\term_paper\tools\verify_phase7.ps1'
```

Script dựng lại `report/manuscript.md`, `report/references_ordered.md`, `report/report_manifest.json`, đồng bộ figure Chương 2–4 vào `report/assets/`, rồi kiểm tra dataset, citation, bibliography, page estimate, hash/provenance, numbering và cross-reference. Bản thảo hiện có 29.779 từ, 18 hình, 16 bảng và 44 tài liệu tham khảo; page estimate là 65 trang trước phụ lục.
