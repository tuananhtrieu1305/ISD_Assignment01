# Phase35 — vận hành và tái kiểm bản phát hành

Ngày thực hiện: 22-10-2026. Nguồn hiện hành là bản thảo đã khóa Phase34,
không phải outline V2 hay file DOCX ứng viên trong build. File bàn giao chỉ có hiệu lực
khi release manifest và cổng verify PASS; xem `docs/phase35_report.md`.

## Đường dẫn cần giữ

- `releases/v3/Tieu_luan_AI_6_chuong.docx`: bản Word nộp, sáu chương và phụ lục A–D.
- `releases/v3/Tieu_luan_AI_6_chuong_QA.pdf`: bản phân trang đối chiếu nội bộ.
- `releases/v3/release_manifest.json`: SHA-256, counts, test và runtime references.
- `artifacts/manifests/phase35/release_lock.json`: closure source/QA/evidence phát hành.
- `docs/demo_v3.md`: hướng dẫn chạy và trình bày giao diện.
- `report/phase34/`: bản thảo khóa, không sửa/format; `report/phase35/artifact.md` là
  hợp đồng distillation mẫu và vùng được phép sửa trong OOXML.
- `report/qa35/candidate-r12/`: PDF, 202 PNG120dpi, inspection và page map.
  `artifacts/manifests/phase35/visual_batches/candidate-r12/` là chứng cứ từng trang.
- `report/build/phase35/`: ứng viên/development history, không phải file nộp.
  Không tự dọn các bản này trước khi có snapshot/revision được phê duyệt.

## Kiểm tra chỉ đọc

Tại PowerShell `C:\DATA\assign`:

```powershell
.\scripts\check_phase35.ps1 -Distribution Ubuntu
```

Lệnh đọc hash closure và 12 khóa cha, không thực thi mô hình. Audit toàn bộ31.848file
khoa học được ghi trong `preserve_after.json`; verify nhanh chỉ tái kiểm hash chính
các file khóa cha, không giả rằng vừa đọc lại toàn bộ member khi chỉ kiểm lock.
Nếu cần kiểm cả member, đọc runner/receipt bảo toàn trước khi tạo receipt mới;
không ghi đè receipt phát hành hay chạy producer/coverage của phase cũ.

## Toolchain tài liệu riêng

Môi trường do người dùng chấp thuận ở
`/home/tuananh/.local/share/ai-term-paper-docs-v1/`, distro Ubuntu.
Python3.11.17 với site-packages riêng; lock dependency tại
`experiments/environment/docs35/requirements.lock`. LibreOffice TDF26.2.6.3 và
Poppler24.02.0 rootless, font Windows có giấy phép được copy riêng ngoài repository.
Không phân phối lại font. Python base cũ chỉ được dùng đọc; hai venv GPU, root uv.lock
và metadata môi trường không đổi. Không chạy lại installer/bootstrap/doctor cũ.

Wrapper `scripts/run_docs_v3.ps1`/`.sh` chọn đúng venv và thư viện LO; không cần bật GPU.
Hai cảnh báo embedded Python prefix của LO còn ghi trong log; conversion exit0 và
PDF/PNG đã kiểm. Chúng không được che khỏi evidence hoặc dùng để hợp thức hóa lỗi render.

## Sửa nội dung hoặc dựng revision mới

Không sửa release đã khóa hoặc `report/phase34`. Trước hết tạo deviation/revision cho
nguồn cần đổi, giữ output/hash cũ và chỉ dựng ra tên file mới chưa tồn tại. Ví dụ sau khi
revision nguồn được phép, build qua `scripts.phase35_docx` với output mới, rồi dùng
packaged `report/tools/documents_vendor_26_1020/render_docx.py --emit_pdf --dpi 120`.
Chạy `scripts.phase35_inspect` để lấy page_map; build lại cache bằng page_map/page_count
thực, render lại tới khi tất cả256target ổn định. Bộ build từ chối ghi đè output.

Mỗi trang cuối phải được xem riêng bằng ảnh gốc. Chỉ carry review khi mọi PNG liên quan
khớp SHA-256 chính xác; không so vùng bị mask, không lấy contact sheet thay mọi trang.
Word desktop được mở bằng phiên riêng ẩn, read-only, cập nhật fields trong bộ nhớ,
đóng không lưu và kiểm hash trước/sau. Probe bị từ chối trong sandbox được giữ FAIL,
probe có quyền phiên Windows riêng ở receipt suffix r2; không ghi đè để giấu lịch sử.

Mục lục là các dòng materialized có REF/PAGEREF native, không trường TOC tự sinh;
F9 không tự thêm mục khi chèn heading. Native bảng/OMML/field có thể chỉnh trong bản
copy làm việc, nhưng bất kỳ thay đổi nào cũng cần render/QA và hash revision mới.
Pagination có thể khác khi người xem thiếu font hoặc dùng printer/Word khác; PDF QA
là mốc đối chiếu, không khẳng định mọi máy đều202trang sau khi tự cập nhật/lưu.

Các công cụ vendor được giữ nguyên byte. So sánh A06/new DOCX đương nhiên có202trang
khác vì đổi nội dung/footer; không gọi diff này là pixel-identical. Fidelity dựa đồng
thời vào style/section canonical,60opaque-part byte-identical và rà trang theo mẫu.

## Những việc không làm lại

Không train/tuning/TEST Ch2–5 hoặc TEST agents để đổi báo cáo. Không đổi Power failed
seal/count1/null telemetry, không biến Wikidata thành QA dataset, không gọi agents là
LLM. Không đổi registry initialized thành trained. Source/apps/model/data tham chiếu
qua các khóa khoa học và registry serving Phase32, không copy raw vào DOCX bundle.
Không commit/reset/clean hay tự viết lại lịch sử Git. Không tự deploy cloud.

Lưu ý tùy chọn Word: probe đầu có thể đã để UpdateLinksAtOpen=False mà không có before
snapshot; script cuối không đổi tùy chọn này và không tự đoán cách hoàn nguyên. Hướng
dẫn demo có thông báo để chủ máy kiểm tra lựa chọn mong muốn.
