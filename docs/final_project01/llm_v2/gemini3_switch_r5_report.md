# Gemini 3 Flash — model switch và một cặp development thành công

Ngày02/11/2026. Phase2vẫnIN_PROGRESS; chưa mởPhase3/freeze/held-out.

## Kết quả thực

- Người dùng yêu cầu thử Gemini3Flash. Mã đúng theo tài liệu Google là `gemini-3-flash-preview` (https://ai.google.dev/gemini-api/docs/models/gemini-3-flash-preview); standard text có free tier (https://ai.google.dev/gemini-api/docs/pricing).
- Một probe không RAG trả `OK.` trong **2.043s**, đúng model được trả về. Có dấu chấm nên không nhận là tuân thủ tuyệt đối lệnh “exactly OK”; API vẫn phản hồi thành công.
- Đã chuyển active generation sang model này qua **v1beta/generateContent**, dùng chung cho direct/planner/rerank/Reporter/Verifier. Embedding/index/KG/CDC giữ nguyên. UI đọc model từ backend/kết quả, không gắn nhãn3.8cho output3Flash. Source trong3notebook, export16module.
- Câu development đã khai báo `v2-dev-05`: “Vận động có ích gì cho cân nặng và đường huyết?”. Cuối revisionr5d, hai nhánh đều complete; RAG có **4citation**, Verifier cùng model approved=true, code_errors=[]. Không phải thẩm định y khoa độc lập hoặc kết luận RAG tốt hơn.
- Revision cuối chạy khoảng13.69s, **4call live/6cache observation**; đây là lượt tiếp từ cache, không là latency cold của pipeline hoàn toàn mới. Mọi lượt dùng live/API/cache đều còn journal riêng.

## Lỗi phát hiện và sửa trước khi phát hành

1. Budget768/512 cũ bị phần thinking tiêu hao, provider trảMAX_TOKENS và JSON/đáp án bị cắt. Giữ outputs r5; đổi minimal thinking và floor2048 output budget cho cả hai nhánh. Adapter từ chối phát hành response chưaSTOP, giữ final text chẩn đoán, không lưu nội dung suy nghĩ.
2. Reporter trả claimID số nguyên. Chuẩn hóa riêng identifier int→str; không đổi văn bản/citation/số liệu y khoa, không chấp nhận bool/float/object thayID. Verifier dùng cùng canonicalID.
3. Bản repair có JSON thiếu dấu đóng dù STOP. Giữ raw lỗi, không “vá” medical output; bật native JSON mode cho Reporter/Verifier/repair và dùng request hash mới. Giữ cache các bước không đổi; không replay unknown claim.
4. UI chặn gửi mới nếu backend còn chạy revision/model/endpoint cũ, hiển thị yêu cầu restart. Saved result bịMAX_TOKENS không được mô tả là đáp án hoàn chỉnh. Saved các revision đều giữ lineage/model/trạng thái.

## Kiểm chứng và bảo toàn

- 13adapter check và28core regression PASS, không API thật trong bộ mô phỏng. Notebook-export parity16PASS, React buildPASS.
- 7saved-output UIcheck PASS, desktop/mobile; nguồn là response thật r5d, GETready/development được route tới snapshot local, không submitcompare/gọiLLM thêm. Đây là kiểm render output đã lưu, chưa là fresh browser→live backend→LLM acceptance.
- 127pin trước các revision/source checkpoint đọc lại đúnghash. Source trước switch và trước từng sửa được giữ trong provenance; declaration r5/r5b/r5c/r5d và source_manifest mới nằm tại `project01/artifacts/llm_v2/phase2/development/gemini3_switch_r5/`.
- Không train/TEST cũ, không đổi env/key/tier, không commit/push/deploy. Model/quota3.8không được tự xem là quota của3Flash; actualRPM/TPM/RPD của model mới chưa được người dùng xác nhận. Appcap4RPM/18RPD vẫn bảo thủ và dùng chung mọi model, gặp429sẽdừng/chờ, khôngpaidfallback.

## Chạy demo

Tại terminal server cũ: Ctrl+C. Từ root chạy `bash project01/scripts/run_web.sh` (GitBash) hoặc `.\project01\scripts\run_web.ps1` (PowerShell), rồi Ctrl+F5 tại http://localhost:8031 . Nếu chỉ muốn xem kết quả vừa chạy mà không gọi API mới, mở “Xem development đã lưu”, chọn câu vận động mang nhãnGemini3Flash vàHoàn tất.

Còn thiếu: câu đảo chiều `v2-dev-11`, fresh live UI và clean-start của source mới, xác nhận quota mới, freeze và40×2evaluation/review. Không gọiPhase2COMPLETE chỉ vì một câu đã chạy tốt. Không xóa thư mục tham khảo hoặc tự mởPhase3.
