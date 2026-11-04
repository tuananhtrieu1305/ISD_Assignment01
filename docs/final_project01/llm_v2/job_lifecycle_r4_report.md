# Sửa lỗi chờ kết quả và chẩn đoán API — revision r4

Ngày 02/11/2026, Asia/Bangkok. Phase 2 vẫn **IN_PROGRESS / WAITING_PROVIDER**.

## Kết quả chẩn đoán thật

- Job `29dc3f42-1e5c-4ec1-85c1-06f588fc7d9f` còn JSON `running` sau khi process ban đầu đã dừng. Không có cơ chế phân biệt worker đang chạy với trạng thái sót trên đĩa.
- Job mới `2de9b641-9936-41bb-8bfc-0162b7f51dce` chỉ ghi nhận một claim sinh nội dung ở nhánh trực tiếp; kết thúc bằng `APITimeoutError` khoảng 180 giây. RAG chưa chạy.
- Backend health khoảng 7 ms, đọc job khoảng 3 ms, DNS/TLS tới Google khoảng 255 ms. Đây là kiểm tra local/kết nối cơ bản, không chứng minh model sẵn sàng.
- Một probe mới, prompt chỉ `Reply with exactly OK.`, cùng model `gemini-3.8-flash` và endpoint `v1beta/interactions`, không RAG/KG, trả **HTTP 503** sau khoảng **52,77 giây**. Timeout SDK 45 giây và trần toàn probe 55 giây; khởi tạo/đường gọi có overhead. Không retry hoặc replay claim cũ. Một SDK attempt mới, usage/tokens chưa biết. Không tự quy lỗi thành hết quota/thiếu key khi không có 429/401.
- Các GET `/api/v2/jobs/...` chỉ đọc trạng thái local; không là call Gemini. Counter trong ảnh là snapshot cũ do trước đây chỉ refresh khi bắt đầu/kết thúc.

## Đã sửa

- Lease bằng file lock theo job, giữ từ trước khi khởi chạy thread đến khi worker kết thúc. GET nhận diện job mất worker, giữ nguyên byte JSON cũ trong `jobs/recovery_snapshots/` rồi chuyển sang `interrupted`; không tự gửi lại request.
- Worker lưu lỗi của mọi exception thông thường và giải phóng semaphore trong `finally`. Không đưa nội dung exception/stack/key vào UI.
- Receipt lỗi mới có thời gian đo; UI nhận loại lỗi, HTTP status và thông báo timeout/503 cụ thể. Claim timeout vẫn `unknown`, không reset ledger.
- Trạng thái riêng cho từng nhánh. Khi call trực tiếp lỗi provider, RAG được ghi `skipped`, không tốn thêm bốn call để thử cùng provider đang lỗi và không bị hiển thị là đang sinh câu trả lời.
- UI hiển thị thời gian tổng/bước hiện tại, refresh counter trong lúc chờ, giảm polling từ 2 lên 5 rồi 10 giây. Poll dừng ở trạng thái cuối, request tới backend có timeout 10 giây. Không tự submit lại compare.
- Thuật toán sửa trong cell notebook 01/02 rồi export một chiều. Vẫn ba notebook; model/prompt/corpus/index/KG không đổi. Backend đang chạy ở terminal người dùng chưa tự reload source mới.

## Kiểm chứng và bảo toàn

- 18 kiểm tra vòng đời job: worker đang sống, orphan/backup, exception, timeout, quota, semaphore, giữ kết quả đã xong; PASS, không API thật.
- 28 kiểm tra hồi quy core/gateway/API: PASS, mô phỏng lỗi provider, không API thật.
- 9 kiểm tra UI timeout: dừng spinner/polling, thời gian, trạng thái RAG chưa chạy, mở lại form, desktop/mobile; PASS. POST compare và GET job trong bài UI được intercept bằng lỗi tổng hợp, không dùng để chứng minh chất lượng câu trả lời.
- React build và notebook/export parity 16 module PASS. Đã xem ảnh desktop; mobile kiểm không tràn ngang.
- Bản trước revision cùng hash nằm tại `project01/provenance/before_job_lifecycle_r4/`, declaration/receipt/source manifest mới tại `project01/artifacts/llm_v2/phase2/development/job_lifecycle_r4/`. Source checkpoint cũ và archive giữ nguyên. Secret scan trên file bàn giao revision không chứa giá trị key.
- Không train, mở TEST cũ, chạy held-out, freeze, commit/push/deploy hoặc xóa folder tham khảo. Chưa có câu trả lời RAG live hoàn chỉnh; sửa UI không khắc phục được HTTP503 của provider.

## Chạy bản sửa và bước tiếp

1. Tại terminal đang chạy server, `Ctrl+C`, rồi từ root project chạy `bash project01/scripts/run_web.sh` (Git Bash) hoặc `.\project01\scripts\run_web.ps1` (PowerShell).
2. Mở `http://localhost:8031`, nhấn `Ctrl+F5`. Việc restart/refresh không gọi Gemini. Không tiếp tục chờ các job cũ bị gián đoạn.
3. Không lặp cả pipeline khi probe tối giản vẫn HTTP503. Giữ model/quota theo quyết định hiện hành. Có thể đối chiếu cùng model trong AI Studio để phân biệt khả năng đáp ứng của model với đường API/SDK; kết quả Studio không thay thế probe API thực tế.
4. Khi kiểm tra lại provider đã ổn, chạy probe mới có declaration/claim mới và giới hạn rõ, sau đó mới một câu direct và từng bước RAG. Không chạy lại unknown claim cũ, không tự đổi model hoặc trả phí.
