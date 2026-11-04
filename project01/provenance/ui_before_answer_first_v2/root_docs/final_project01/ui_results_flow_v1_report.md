# UI revision results_flow_v1 — 01/11/2026

Người dùng nhận thấy tab Kết quả & nguồn gần như không đổi khi chuyển P0/P1/P2. Revision này bổ sung giải thích và quan sát luồng xử lý ngay tại tab đó, giữ giao diện xanh/trắng hiện hành.

## Thay đổi

- Tiêu đề và giải thích riêng cho P0 gọi trực tiếp, P1 điều phối và P2 kiểm chứng/tổng hợp.
- Năm khối vai trò lấy từ trace thực: bước đã ghi nhận, bước không chạy/chưa nhận trace, số lần tìm kiếm, truy hồi bổ sung và thời gian.
- Các tiêu chí Verifier từ `verification.checks`, không tự gán P2 là đã kiểm chứng nếu tác vụ bị từ chối trước bước đó.
- Đối chiếu score/nhãn, câu trả lời và citation giữa ba kết quả; chỉ so sánh khi có cùng `input_sha256`. Không có đầu ra hoặc chưa đủ kết quả được nêu riêng.
- Bảng mở rộng đối chiếu Coordinator, Verifier, Reporter, lượt tìm lại và số bước; nút chuyển tới trace đầy đủ không chạy lại pipeline.
- Diễn giải công khai rằng cùng checkpoint/truy hồi có thể cho cùng đầu ra. Không tạo câu trả lời khác, sửa score, thêm lỗi giả hay khẳng định P2 tốt hơn.

## Phạm vi bảo toàn

Chỉ sửa entry React `web/frontend/src/main.jsx`, thêm `ProcessingSummary.jsx`/`processing.css`, build dist mới. `style.css` gốc không đổi. Các notebook, backend đã export, model, preprocessing, corpus, graph, index, evaluator và 120 kết quả evaluation đều giữ nguyên.

Năm file UI đã được Phase 2 acceptance ghi nhận có bản lưu nguyên hash tại `project01/provenance/ui_before_results_flow_v1/`; bản đồ ở `project01/artifacts/ui_revisions/results_flow_v1/preservation.json`. Không sửa acceptance/freeze/handoff Phase 2. Các asset dist cũ có thể được build thay tên; verifier revision đối chiếu bản archive gốc thay vì yêu cầu asset cũ là active.

## Kiểm tra

- Vite production build PASS.
- 26 kiểm tra trình duyệt PASS với API thật, không mock: đổi P0/P1/P2, ba phép kiểm P2 ở combined, thiếu Verifier P0/P1, score/trích đoạn/citation giống nhau, bảng trace, điều hướng, knowledge-only, thiếu BMI, từ chối ngoài phạm vi, mobile và không lỗi JavaScript.
- Ảnh desktop P0/P2 và mobile P2 được lưu; đã xem ảnh P2 desktop/mobile, không cắt chữ hoặc tràn trang.
- Các lượt trình duyệt dùng ví dụ demo và kiểm hành vi, không chạy lại bộ evaluation. Không train hoặc mở lại predictive TEST cũ.
- Máy chủ kiểm tra cổng 8041 đã dừng; không dừng máy chủ người dùng ở cổng 8031.

Ảnh và proof: `project01/artifacts/ui_revisions/results_flow_v1/`. Verifier hiện hành cho project sau revision: `project01/scripts/verify_results_flow_v1.py`; verifier này giữ nguyên script Phase 2 và resolve đúng hash UI archive khi audit lịch sử. `release.json` pin file revision; `verification.json` là kết quả audit mới. Verifier Phase 2 cũ chạy trực tiếp sẽ báo thay đổi UI đã được chủ đích tạo revision; không cập nhật lại bằng chứng lịch sử để che thay đổi.

## Chạy bản mới

Dist đã build. Nếu máy chủ local đang chạy, chỉ cần refresh bằng Ctrl+F5 và chạy lại ví dụ để có kết quả trong phiên trình duyệt mới. Nếu chưa có máy chủ, dùng `project01/scripts/run_web.ps1` qua PowerShell rồi mở `http://127.0.0.1:8031`.

Đây là điều chỉnh trình bày sau Phase 2, không mở Phase 3, không thay kết luận benchmark và không commit/push/deploy.
