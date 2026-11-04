# Phase 2 — trace input/output r6

Ngày: 02/11/2026. Trạng thái: **development, chưa freeze, chưa mở held-out**.

## Thay đổi

- Câu hỏi mặc định được rút gọn thành: **“Bệnh thận có làm tăng nguy cơ tiểu đường không?”**.
- Thêm quy tắc cân chỉnh mức chắc chắn dùng chung: thiếu hoặc mâu thuẫn bằng chứng thì nói rõ chưa đủ căn cứ; có căn cứ rõ thì vẫn trả lời thẳng. Quy tắc không chứa câu hỏi bệnh thận và không ép nhánh LLM trực tiếp phải mơ hồ.
- Thêm tab **03 · Luồng xử lý**, đẩy tab so sánh thành số04. Tab mới trình bày input/output thực của pre-retrieval, Risk Agent, retrieval, reranking, Reporter, Verifier, vòng sửa nếu có và kết quả phát hành.
- Retrieval ghi số ứng viên theo truy vấn, ứng viên có đóng góp KG và các cạnh KG. Reranking ghi rank trước/sau, điểm thật, ngưỡng và lý do giữ/loại; `null` hiển thị “—”, không đổi thành0.
- Backend lưu `pipeline_trace` ngay trong khi job chạy và đưa snapshot vào `GET /api/v2/jobs/<id>`. Trace chỉ chứa dữ liệu công khai phục vụ giải thích; không lưu API key, chain-of-thought hoặc nội dung exception nội bộ.
- Kết quả cũ được tái dựng từ các trường đã lưu và mang nhãn **Kết quả lịch sử**. Bản nháp Reporter không tồn tại trong receipt cũ được hiển thị “không được ghi lại”, không dùng câu trả lời cuối để giả làm bản nháp.
- Tab luồng chỉ đọc state/receipt và không gửi request model.

## Nguồn thuật toán

Notebook vẫn là nguồn duy nhất cho thuật toán. Hai notebook được sửa rồi export một chiều:

- `project01/notebooks/01_Data_KB_RAG.ipynb`: báo cáo reranker.
- `project01/notebooks/02_Diabetes_Multi_Agent.ipynb`: calibration, recorder, pipeline và transport.

`notebooks.py check`: **PASS, 16 module / 3 notebook**.

## Kiểm chứng không dùng API

- `check_trace_io_r6.py`: **12/12 PASS**, API call =0.
- `check_units.py`: **28/28 PASS**, API call =0; lỗi503/quota là fixture.
- React production build: **PASS**,18 module.
- `ui_trace_io_r6.mjs`: **11/11 PASS**, desktop/mobile, không lỗi JavaScript, không POST compare/resume, API call =0.
- Visual QA: `pipeline-saved-desktop.png`, `pipeline-saved-mobile.png`.
- Bảo toàn trước revision:31/31 file archive đúng SHA-256.

UI test dùng cặp development Gemini3 r5d đã lưu để kiểm cách trình bày; đây không phải lần suy luận mới và không phải bằng chứng rằng RAG tốt hơn LLM trực tiếp.

## Giới hạn còn lại

- Prompt `calibration-r6` và trace live mới **chưa được thử với Gemini thật** trong revision này, theo yêu cầu không đốt quota tự động.
- Cặp r5d dùng prompt cũ và chỉ được giữ làm dữ liệu lịch sử/fixture UI.
- Chưa có kết luận so sánh chất lượng cho câu hỏi bệnh thận. Nếu chạy sau này, hai nhánh phải cùng model, cùng câu hỏi và giữ nguyên protocol; không chạy lặp đến khi tìm được trường hợp RAG thắng.
- Phase2 vẫn `IN_PROGRESS`; freeze,40×2 held-out và Phase3 chưa bắt đầu.

## Khởi động lại

Backend đang chạy trước revision sẽ thiếu `runtime_revision=trace-io-r6`. Dừng terminal bằng `Ctrl+C`, chạy lại `project01/scripts/run_web.ps1` (PowerShell) hoặc `bash project01/scripts/run_web.sh` (Git Bash), sau đó `Ctrl+F5` ở trình duyệt.

