# R8 — một câu demo có hồ sơ, đầy đủ năm vai trò

Ngày 03/11/2026. Theo yêu cầu tìm câu hỏi ngắn để so sánh Gemini trực tiếp với pipeline và chạy đủ mọi bước, đặc biệt Risk Agent. Không chạy API để tìm baseline trả lời sai.

## Câu chọn và căn cứ

**Đi bộ có giúp tôi giảm 58% nguy cơ tiểu đường không?**

Đoạn KB `m2c-39c6512524216aa32b22` nói kết quả giảm nguy cơ tương đối58% trong3năm thuộc nhóm thay đổi lối sống có giảm cân trong DPP; không bảo đảm hiệu quả cá nhân của riêng đi bộ. Các cạnh activity→healthy_weight/glucose có nguồn nhưng không tự hỗ trợ con số58%. Hướng dẫn đầy đủ ở `project01/docs/llm_v2/DEMO_FULL_PIPELINE_R8.md`.

Đây là ứng viên development/demo. Chưa gọi hai nhánh Gemini thật cho câu này, chưa có bằng chứng baseline sai. Direct có thể biết nghiên cứu và trả lời đúng. Không đổi prompt baseline để ép nó mơ hồ hoặc sai; không lấy khả năng truy cập checkpoint riêng làm điểm accuracy y khoa. Không mở held-out.

## Thay đổi

1. Nút **Demo đủ 5 agent · Đi bộ & 58%** chọn câu hỏi, kèm hồ sơ TRAIN `row_0048946` đủ21trường. Bấm preset không gọi API; bấm So sánh mới tạo job.
2. Phát hiện và sửa thiếu kết nối: r7 có chạy Risk khi có profile nhưng Reporter không nhận output. R8 truyền bản tóm tắt score/ý nghĩa công cụ sang Reporter; không gửi raw21field.
3. Code ghép kết quả công cụ vào bản nháp trước Verifier. Verifier kiểm prefix khớp chính xác score/class/unit/calibration; score không là xác suất mắc bệnh năm tới. Không sửa câu sau khi qua cổng.
4. Trace ghi Risk input21field, score/model hash, Reporter input có `risk_tool_summary`. Tab Luồng sửa lỗi hiển thị claim dùng sai tên field: nay hiện `text_vi`, ID và citation. Lượt lịch sử không bị gắn nhãn đã truyền Risk khi chưa có record.
5. Runtime revision `full-demo-r8`; vẫn3generation: direct+Coordinator+Reporter. Reranker/Verifier/Risk local, embedding quota tách riêng. Không thêm repair hoặc model mới.

Source thuật toán sửa tại notebook02 rồi export một chiều; vẫn3notebook/16module. Notebook01/03, corpus/KG/index, checkpoint CDC và output khoa học giữ nguyên. Bản trước37file ở `project01/provenance/before_full_demo_r8/`; resolver mới đối chiếu11pin r7 về bản archive chính xác, không sửa receipt lịch sử.

## Nghiệm thu và giới hạn

- 11 kiểm tra unit mới PASS: format/meaning score, metadata sai, Reporter nhận tool context không nhận profile, một generation Reporter, score bị sửa bị chặn, knowledge-only không lẫn score.
- 28 regression hiện có PASS trong serving env WSL, không request provider.
- 16 contract check r7 PASS: rerank/verifier local, không repair, ngân sách tối thiểu3call giữ nguyên.
- Offline tích hợp: Risk chạy checkpoint thật trên TRAIN, score `0.3955201956477639`; BM25/KG/rerank/Verifier thật. Generation dùng test double, dense tắt. Đủ7bước complete,20candidate/6evidence, nguồn DPP được giữ. Graph lookup11cạnh;0candidate có KG rank trong top20sparse-only. Không gọi kết quả này là hybrid dense live hoặc chứng minh KG cải thiện câu trả lời.
- Frontend build19module PASS. 13 browser check PASS trên build thật với API local bị intercept: preset bật đủprofile, mộtjob,7bước, Risk complete, Reporter nhận score, claim hiện đúng, mobile390px, không JS error. Screenshot/fixture có nhãn engineering, không là output Gemini thật.
- Export parity PASS3notebook/16module. Không cài dependency, train, mở TEST, commit/push/deploy. Số call Gemini/embedding mới=0.

Backend người dùng đang chạy ở8031 cần Ctrl+C và khởi động lại launcher để nạp code r8, rồi Ctrl+F5. Không tự dừng process người dùng. Cần ít nhất3generation slot nếu người dùng chạy một cặp thật; không tự chạy hộ lượt thật trong lần tìm câu này. Phase2 vẫn IN_PROGRESS; freeze/evaluation/Phase3 chưa bắt đầu.
