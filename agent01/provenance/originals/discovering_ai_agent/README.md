# DISCOVERING AI Agent

Bài độc lập, không bổ sung vào tiểu luận AI V3 và không thay đổi web/Render.

## Sản phẩm nộp

`output/DISCOVERING_AI_Agent.docx`: 14 trang A4, gồm đúng 6 trang lý thuyết tiếng Việt,
7 trang thực hành với 9 ảnh code và output thực, và 1 trang tài liệu tham khảo.
Chữ, tiêu đề, chú thích và code đều màu đen; biểu đồ chỉ dùng sắc xám.
Phân trang đã kiểm trên bản render LibreOffice; Word khác phiên bản có thể phân trang khác.

Lý thuyết tổng hợp ba nguồn Google Cloud, IBM và McKinsey, có trích dẫn [1]–[3].
Các tình huống họp nhóm, thư viện và lịch thi là ví dụ giả định được ghi rõ trong bài.
URL [4] rút gọn đã được người dùng xác nhận là bài Q-learning mê cung 10×10 của
GeeksforGeeks. URL đầy đủ và ngày truy cập nằm trong `sources/manifest.json`.

## Notebook và kết quả

`notebooks/Discovering_AI_Agent.ipynb` tự chứa toàn bộ mã và đã thực thi đủ 9 cell.
Mê cung, hành động, phần thưởng và lịch epsilon theo [4]. Mã được tổ chức lại;
bổ sung seed 42, giới hạn bước an toàn, cập nhật terminal đúng, kiểm tra greedy
không che hướng va tường và BFS độc lập sau huấn luyện. Những thay đổi này được
ghi trong phần thực hành và cuối tài liệu, không trình bày như bản sao nguyên mã nguồn.

Sau 5.000 lượt, đường greedy hợp lệ dài 24 bước, bằng độ dài tối thiểu BFS,
tổng thưởng không chiết khấu 27. Trong 1.000 lượt huấn luyện cuối vẫn có khám phá,
tỷ lệ tới đích là 87,6%, thưởng trung bình 20,951. Không suy diễn kết quả một seed
trên một mê cung thành khả năng tổng quát hóa.

Ảnh trong DOCX là ảnh Chromium chụp bản HTML xuất từ notebook đã chạy, không phải
ảnh giả giao diện Jupyter và không lấy output của website. CSS đen và grayscale,
tắt LCD subpixel antialiasing để tránh pixel viền chữ có màu. Hash ở
`evidence/screenshot_manifest.json`. HTML chỉ phục vụ chụp ảnh, trình duyệt chặn HTTP.

## Chạy lại bằng môi trường hiện có

Từ thư mục gốc `C:\DATA\assign`, PowerShell:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module discovering_ai_agent.make_notebook
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module pytest -ModuleArguments @('discovering_ai_agent/tests','-q','-p','no:cacheprovider')
```

Lệnh đầu thực thi lại notebook và ghi lại notebook/kết quả của riêng bài này;
không chạy TEST hay model của V3. Bài dùng NumPy CPU, không cần GPU.
Runtime code là Python 3.11.17/NumPy 2.4.6 đã có trong WSL Ubuntu, user tuananh.
Không cài thêm package, không đổi dependency hoặc môi trường GPU.

`build_report.py` dùng toolchain tài liệu riêng có sẵn của Phase 35, được người dùng
đồng ý dùng lại. Muốn tạo ứng viên mới, dùng revision chưa tồn tại:

```powershell
.\scripts\run_docs_v3.ps1 -Module discovering_ai_agent.build_report -Arguments @('--revision','r4')
```

Sau bất kỳ thay đổi nào cần xuất HTML/chụp ảnh nếu code đổi, build DOCX,
render bằng `report/tools/documents_vendor_26_1020/render_docx.py`, kiểm tra đủ từng
trang rồi mới thay bản nộp. `qa/final/` là bản render nội bộ, không phải sản phẩm nộp.
`qa/r1/`, `qa/r2/` giữ lịch sử sửa phân trang/định dạng; không dùng làm bản cuối.

## Bằng chứng

`evidence/results.json` lưu kết quả thực; `final_tests.xml` và `final_coverage.json`
lưu kiểm thử cuối. Coverage được tính cho thuật toán `experiment.py`, không đại diện
cho toàn bộ pipeline Word/browser. `evidence/verification.json` ghi hash sản phẩm và
kiểm tra phân trang, màu, ảnh và QA từng trang. Không sửa kế hoạch/khóa/artifact V3.
