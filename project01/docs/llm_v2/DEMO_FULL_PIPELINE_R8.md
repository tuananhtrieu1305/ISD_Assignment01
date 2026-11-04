# Demo một câu hỏi chạy đủ năm agent

Câu được chọn từ KB ngày 03/11/2026:

> Đi bộ có giúp tôi giảm 58% nguy cơ tiểu đường không?

## Vì sao câu này đáng demo

Trong KB có đoạn `m2c-39c6512524216aa32b22`, tài liệu **Am I at Risk for Type 2 Diabetes? Taking Steps to Lower Your Risk of Getting Diabetes**. Đoạn này nói mức giảm tương đối 58% trong 3 năm ở nhóm thay đổi lối sống, có giảm cân; không nói mỗi cá nhân chỉ đi bộ sẽ giảm đúng 58%.

Nguồn trong snapshot: <http://www.niddk.nih.gov/health-information/health-topics/Diabetes/type-2-diabetes-taking-steps-lower-your-risk-diabetes/Pages/index.aspx>. Đây là vị trí nguồn đã lưu trong MedQuAD, không khẳng định trang hiện tại vẫn giữ văn bản như snapshot.

Một câu trả lời có căn cứ cần phân biệt kết quả nghiên cứu trên nhóm với lời hứa cho cá nhân; tác động của cả chương trình với riêng đi bộ; score phân loại CDC với xác suất mắc mới trong tương lai. Không được nhân score CDC với 42% rồi gọi đó là nguy cơ sau can thiệp.

KG có cạnh `activity → SUPPORTS → healthy_weight` và `activity → SUPPORTS → glucose`, có nguồn tại `m2c-670a97431189b868aa1c`. Chúng giải thích vì sao truy hồi thông tin vận động hữu ích, không chứng minh con số 58% cho một cá nhân. Con số nghiên cứu phải lấy từ đúng đoạn DPP, không từ cạnh KG này.

LLM trực tiếp có thể nhớ DPP và trả lời đúng. **Chưa có một cặp Gemini thật mới cho câu này, vì vậy chưa thể hứa LLM thuần sẽ trả lời sai.** Lợi thế cần quan sát là pipeline tính được checkpoint, giữ đúng ý nghĩa score, lấy đúng nguồn và phân biệt các điều kiện của 58%. Nếu direct cũng trả lời đúng thì ghi nhận là đúng; việc không có tool output không phải một lỗi kiến thức y khoa.

## Chạy bằng Git Bash

Dừng backend cũ bằng `Ctrl+C` ở terminal của nó, rồi:

```bash
cd /c/DATA/assign
bash project01/scripts/run_web.sh
```

Mở <http://127.0.0.1:8031>, nhấn `Ctrl+F5`.

1. Vào **01 Câu hỏi & hồ sơ**, bấm **Demo đủ 5 agent · Đi bộ & 58%**. Nút chỉ chuẩn bị câu hỏi và bật hồ sơ; chưa gọi Gemini.
2. Nút này chọn hồ sơ TRAIN có sẵn `row_0048946`, đầy đủ 21 trường. Có thể mở phần hồ sơ để xem. Không nhập dữ liệu sức khỏe định danh thật cho demo.
3. Bấm **So sánh hai câu trả lời** đúng một lần, khi còn ít nhất ba generation slot. Một cặp vẫn cần đúng ba generation: direct, pre-retrieval, Reporter. Query embedding dùng quota riêng; reranker, Risk và Code Verifier chạy local.
4. Đọc kết quả hai nhánh. Nhánh pipeline phải có kết quả công cụ CDC ở đầu câu trả lời, sau đó là giải thích có citation. Score mẫu đã kiểm local là `0.3955201956477639`, được trình bày sáu chữ số thập phân; không phải 39,55% nguy cơ mắc trong năm tới.
5. Mở **03 Luồng xử lý** và kiểm output từng bước theo bảng dưới. Nếu API lỗi/quota/thiếu hồ sơ, bước không hoàn tất phải giữ đúng trạng thái; không tự gắn xanh để trình diễn.

## Từng bước phải đưa gì cho bước sau

| Bước | Output cần thấy |
|---|---|
| Coordinator/pre-retrieval | Câu gốc, truy vấn Anh–Việt, intent và entity thật do lượt đó tạo |
| Risk Agent | Check đủ 21 trường → score, nhãn, hash checkpoint; không gọi API |
| Knowledge/retrieval | Candidate có ID, rank dense/BM25/KG và neighborhood có nguồn |
| Reranking local | Điểm từng candidate, thứ hạng trước/sau, giữ/loại và số evidence thật |
| Reporter | Input gồm ID evidence và `risk_tool_summary`; bản nháp có score công cụ và giải thích có nguồn |
| Code Verifier | Kiểm citation/provenance/số trong claim, kiểm score prefix đúng tuyệt đối; không gọi LLM |
| Release | Phát hành nguyên bản nháp đã được duyệt; không sửa score sau kiểm |

Raw profile vẫn chỉ tính local. Reporter chỉ nhận đoạn kết quả công cụ đã kiểm, không nhận 21 giá trị hồ sơ. Phần score được code ghép vào bản nháp trước cổng Verifier để model không tự làm tròn/chuyển nghĩa nó.

## Đã xác minh đến đâu

- Offline unit: kiểm nghĩa score, lớp, calibration flag, Reporter context, raw-profile exclusion và từ chối score bị sửa.
- Offline tích hợp trong env WSL thật: dùng checkpoint CDC, BM25, KG, reranker và Code Verifier thật; generation giả lập có nhãn riêng, dense tắt để không tạo request embedding. Đủ bảy bước complete, 20 candidate, 6 evidence; đoạn DPP được giữ lại.
- KG lookup offline tìm thấy 11 quan hệ, nhưng **0 candidate giữ lại có KG rank** ở cấu hình sparse-only của kiểm thử này. Không đổi trọng số để ép graph lọt top-k và không nhận đây là phép đo dense/hybrid live.
- Frontend build và browser fixture kiểm nút preset gửi đủ hồ sơ, Risk complete, Reporter nhận output, claim hiện đúng và không phát sinh request provider.
- Chưa gọi Gemini mới cho câu này; số generation/embedding API mới trong lượt chuẩn bị là 0. Đây là ứng viên demo đã kiểm kỹ thuật, không phải kết quả chứng minh ưu thế đã đo.

Bản r7 giữ ở `project01/provenance/before_full_demo_r8/`; source thuật toán r8 sửa trong notebook 02 rồi export một chiều. Không sửa prompt baseline để ép nó thua; không mở held-out hoặc chạy nhiều câu để tìm output đẹp.
