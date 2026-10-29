# Chạy notebook và dựng lại tài liệu AG02

Môi trường code dùng lại WSL Ubuntu, user tuananh, Python 3.11.17 ở
`/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
Package/version đã đối chiếu ở `evidence/phase09/notebook_execution.json`;
không cài dependency mới hoặc sửa runtime GPU. Tài liệu dùng environment riêng
đã có `/home/tuananh/.local/share/ai-term-paper-docs-v1/.venv/bin/python`.

## Xem và chạy notebook

Mở `notebooks/AG02_Code_and_Results.ipynb`, chọn kernel Python WSL đã có rồi Run All.
Nếu giải nén ZIP, giữ nguyên cây `agent02_assignment/`, không di chuyển notebook
ra riêng. Notebook tự tìm thư mục gốc từ vị trí hiện tại và các thư mục cha.
Mọi kết quả/hình nằm trong bundle; không cần mạng hay dataset download.

44 ô code chỉ kiểm hash và trình bày 12 bảng kết quả,8 đoạn code,20 hình kèm giải
thích. Một ô tính Q=4,65/margin5/3 từ giả định đề. Đoạn thuật toán được hiển thị
bằng `IPython.display.Code`, không chạy để tạo lại mô hình. Run All không train,
không update Q,không gọi evaluator hoặc ghi vào input. Notebook có sẵn output thật.

Muốn sinh notebook mới trong full workspace, chọn output chưa tồn tại:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.make_phase09_notebook -ModuleArguments @('--output','notebooks/AG02_readonly_r2.ipynb')
```

## Bản thảo và tài liệu

`report/active_report.json` chọn manuscript v1 và matrix r2. Đủ 9 phần/10 câu,
12 bảng số liệu và2 bảng mô tả,20 hình,8 source excerpt. DOCX có chữ đen,code đen,
bảng native và ảnh grayscale. Bìa cá nhân/tên file đã được chủ bài xác nhận ở Phase9.

Chỉ trong full workspace, tạo một candidate revision mới:

```powershell
.\scripts\run_docs_v3.ps1 -Module agent02_assignment.build_phase09 -Arguments @('--revision','r3')
.\scripts\run_docs_v3.ps1 -Script 'C:/Users/anhca/.codex/plugins/cache/openai-primary-runtime/documents/26.1022.11436/skills/documents/render_docx.py' -Arguments @('agent02_assignment/report/build/candidate-r3/agent02_D23CTPM01_TrieuTuanAnh.docx','--output_dir','agent02_assignment/report/qa/phase09/r3','--emit_pdf','--dpi','125')
```

Đường renderer phụ thuộc máy; hash/toolchain thực đã dùng ghi trong evidence Phase9.
Không cài LibreOffice hoặc package vào env GPU. Renderer dùng wrapper soffice riêng
trong docs runtime,không tự dùng Word/LibreOffice đang mở của người dùng. Sau thay
đổi layout phải render và xem lại mọi trang; không dùng XML để kết luận bố cục đẹp.
Ứng viên không đồng nghĩa bản đã phát hành cuối; Phase10 kiểm rubric và mọi trang.

## Source, dữ liệu và phạm vi ZIP

ZIP giữ source Python,PowerShell launcher nội bộ,tests,protocol,GoldTRAINprefix,
input70file của báo cáo,notebook đã chạy,bảng/hình tổng hợp và khóa provenance.
`BUNDLE_MANIFEST.json` ghi hash/bytes từng file. Không đóng gói runtime,hàng GB
trajectory/checkpoint trung gian hoặc dataset V3; không sửa hoặc phân phối file V3.
Các khóa lịch sử vẫn liệt kê đầy đủ file của workspace gốc,không phải mọi file đó
đều có trong ZIP. Audit scientific toàn bộ cần full workspace ban đầu. Run All
notebook và test publication có đủ input trong ZIP; không coi ZIP là full raw archive.

Cây chính:

```text
agent02_assignment/
  code/                    # mô hình gốc,core,runner helpers,read-only publication
  docs/                    # protocol,thiết kế và diễn giải
  data/derived/            # Gold prefix TRAIN/kernel
  artifacts/metrics/      # saved aggregate CSV/JSON
  artifacts/figures/      # PNG và notes
  notebooks/              # notebook đọc kết quả
  report/phase08/         # manuscript,table/code/figure/input index
  report/build/           # DOCX ứng viên (ngoài source ZIP)
  report/qa/              # PDF/PNG kiểm trang (ngoài source ZIP)
  evidence/               # locks và receipts chọn lọc
```

Trong full workspace, kiểm chỉ đọc:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module pytest -ModuleArguments @('agent02_assignment/tests','-q','-p','no:cacheprovider')
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase08
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase08_presentation_r2
```

Training/evaluation đã hoàn tất trong Phase3–7. Các launcher `run_agent02_phase03`
đến07 có lệnh status/declare/train/evaluate lịch sử để đọc implementation,không
phải checklist cần chạy lại. Không gọi `agent02_experiment.py` trực tiếp; main thầy
chạy nhiều thí nghiệm và có output tương đối. Muốn nghiên cứu mới phải khai báo
study/revision và output/gate riêng trước train; không reset claim hoặc ghi đè
final đã consumed. Kiểm hash/đọc số liệu không cần model forward.
