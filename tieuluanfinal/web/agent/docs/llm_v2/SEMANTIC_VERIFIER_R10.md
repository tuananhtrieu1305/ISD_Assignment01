# R10 — Risk mặc định bật, Verifier dùng Gemini

Theo yêu cầu mới nhất ngày03/11/2026, quy tắc3generation của r7–r9 trở thành lịch sử. Một cặp hoàn tất hợp lệ dùng **4 generation request**: direct1, Coordinator1, Reporter1, Verifier1. Embedding truy vấn dùng quota riêng. Reranker, checkpoint CDC và kiểm integrity vẫn local.

## Nguyên nhân đã kiểm từ lượt chạy thật

Job `16c2b50c-6948-4bda-b96e-ddb77770c87b` có `profile_present=false`, Risk stage skipped, Reporter input `risk_tool_summary=null`. Risk không bị lỗi inference; form chưa gửi hồ sơ. Reporter thực tế đã trả lời và có nguồn, không phải cũng trả “chưa đủ bằng chứng”. Kết quả cuối bị thay bởi thông báo chung vì Verifier báo `unsupported_numeric_claim`.

Quy tắc cũ đòi mọi chữ số trong claim xuất hiện nguyên văn ở các đoạn được trích. Nó không hiểu quy đổi, diễn đạt “hơn một nửa”, khoảng hay việc ghép các điều kiện nghiên cứu. Tuy vậy một số lỗi citation/số thực sự vẫn có thể tồn tại; không coi mọi bản nháp bị chặn là đúng.

## Risk được sửa thế nào

- UI mặc định **Đủ 5 agent · kèm hồ sơ TRAIN**, khởi tạo từ hồ sơ có sẵn `row_0048946`. Người dùng gõ câu hỏi khác vẫn giữ chế độ/hồ sơ, không bắt buộc bấm preset.
- Có nút riêng **Chỉ hỏi kiến thức · bỏ Risk**. Chỉ khi chủ động chọn chế độ này thì Risk mới được bỏ qua theo thiết kế.
- Thiếu/sai một trong21trường thì UI ghi tên trường và chặn chạy. Backend từ chối `combined` mà không có hồ sơ trước khi tạo job/API; không tự bịa field còn thiếu.
- Profile thật vẫn không gửi Gemini; model CDC tính local và chỉ đoạn kết quả công cụ được chuyển tới Reporter/Verifier. Không đổi checkpoint, scaler hoặc threshold.

## Verifier mới làm gì

1. Kiểm cứng bằng code: claim/citation IDs, source metadata, ký hiệu nguồn kể cả dạng `[Nguồn 1, 6]`, score CDC phải khớp chính xác.
2. **Một call Gemini cùng model** đọc câu hỏi, bản nháp, các evidence thật và phần kết quả công cụ. Prompt ở `project01/config/prompts/semantic_verifier_vi.txt`.
3. Gemini kiểm toàn câu trả lời và từng claim: ý nghĩa, điều kiện, đối tượng, thời gian, số và đơn vị. Cho phép phép quy đổi có nguồn hỗ trợ; không mặc định duyệt Reporter.
4. Nếu evidence đủ để sửa, Gemini có thể trả `corrected_draft` ngay trong cùng call. Không thêm repair call hoặc truy hồi mới.
5. Code kiểm lại bản cuối: schema, coverage đầy đủ của claim_reviews, citations thuộc đúng claim, score bất biến và các cờ kiểm phải hợp lệ. `approved=true` nhưng claim unsupported/thiếu review vẫn không được phát hành.
6. Chỉ phát hành bản đã duyệt. Trace giữ bản Reporter ban đầu, nhận xét và bản sửa nếu có. Thất bại thì hiển thị lý do cụ thể; không gán chung rằng KB không có bằng chứng.

Đây là cùng Gemini tự đánh giá/có thể tự sửa, không phải thẩm định độc lập hay bảo đảm y khoa. Nguồn thiếu hoặc bản nháp sai thực sự vẫn có thể bị từ chối. Prompt baseline/tiêu chuẩn nguồn dùng chung r9 không bị làm yếu để ép kết quả so sánh.

## Cách chạy trong Git Bash

Dừng terminal backend cũ bằng Ctrl+C, rồi:

```bash
cd /c/DATA/assign
bash project01/scripts/run_web.sh
```

Mở <http://127.0.0.1:8031>, Ctrl+F5. Runtime mới phải là `semantic-verifier-r10`; UI báo nếu còn backend cũ. Ở trang nhập, giữ **Đủ 5 agent**, kiểm dòng đã kèm đủ21trường, gõ câu hỏi và bấm so sánh đúng một lần. Cần còn ít nhất4generation slot. `/ready` không gọi API. Lượt cũ đang chờ quota dùng revision khác không được tự tiếp bằng code mới; vẫn giữ nguyên kết quả cũ.

Ở tab03, Risk phải complete nếu đã gửi hồ sơ; Verifier phải ghi **Gemini + kiểm integrity** và ngân sách tổng4. Kết quả lịch sử vẫn hiển thị công cụ/ngân sách của chính lượt cũ, không bị tô thành kết quả r10.

## Đã kiểm và chưa kiểm

- 14 unit/contract check mới: tái hiện false rejection phép30×5=150, semantic review giả lập một call, citation sai/score đổi vẫn bị chặn, bản sửa có kiểm, không được xóa hết claim để giả duyệt, phản hồi thiếu/sai bị từ chối, hồ sơ combined bắt buộc và budget4.
- 28 regression PASS; source/export vẫn3notebook/16module. Thuật toán sửa ở notebook02 rồi export; không sửa backend riêng.
- Full pipeline offline có Risk TRAIN thật, BM25/KG/reranker/integrity thật; generation và nhận xét semantic là test double, dense tắt. Đủ7bước complete,4generation giả lập; rawprofile không xuất hiện trong prompt.
- Browser build thật có API local intercept: gõ câu mới vẫn gửi21field không cần preset, hiển thị đủ7bước, Risk complete, Verifier Gemini, budget4; thiếu BMI chặn trước job;3slot không cho tạo lượt mới.
- **Không có request Gemini hoặc embedding mới trong lượt triển khai này.** Chưa xác nhận chất lượng semantic trên một cặp live r10; không gọi mock là kết quả model thật.

Bản trước ở `project01/provenance/before_semantic_verifier_r10/`. Không thay output/provider ledger/jobs khoa học cũ, không train/TEST/commit/push/deploy. Phase2 vẫn đang thực hiện; held-out/freeze/Phase3 chưa mở. Với4generation/cặp,40câu×2nhánh cần khoảng160generation request, tối thiểu9ngày theo cap local18RPD nếu không có request khác.
