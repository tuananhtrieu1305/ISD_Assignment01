# Dataset card — MedQuAD

## Nhận dạng và nguồn

- Dataset ID: `ch5_medquad`.
- Chương/bài toán: Chương 5, truy hồi và trả lời câu hỏi y khoa; Phase 12 mới lọc tập con liên quan đái tháo đường.
- Nguồn chính thức: <https://github.com/abachaa/MedQuAD>.
- Snapshot: commit `577bd37b96c02d1833b2c9eed2de9f96964e96cb`, truy cập 2026-10-12.
- License: CC BY 4.0, được nêu trong `readme.txt` và phân phối kèm `LICENSE.txt`.
- Local: `term_paper/knowledge_rag/data/raw/medquad`; 37.183.352 byte; 11.278 file; manifest SHA-256 `89cfd03f8a21adfc2fc530a5b8bf54ee7b5e9dad632bc3a118d0aee5fda1f5fa`.

## Kích thước và schema đo từ snapshot

- 11.274 XML đọc thành công, tổng cộng 47.441 QA; không có lỗi parse.
- README upstream công bố 47.457 QA, cao hơn số đếm local 16 QA. Báo cáo sử dụng số đo có thể tái lập từ commit đã khóa và công khai sai lệch này.
- 16.407 QA có answer; 31.034 QA không có answer. Ba thư mục MedlinePlus mà tác giả chủ động gỡ answer chứa 31.029 QA; pipeline tuyệt đối không crawl hoặc khôi phục nội dung đã gỡ.
- Metadata gồm document/source URL, focus, question type, UMLS CUI, semantic type, question và answer. Snapshot có 39 nhãn `qtype` quan sát được; 47.427 QA có focus, 31.417 có CUI và 31.375 có semantic type.
- Question ID chỉ mang ý nghĩa cục bộ theo nguồn: kiểm tra toàn corpus thấy 17.355 lần lặp ID, nên Phase 12 phải ghép source path/document ID để tạo khóa ổn định.

## Phân bố sơ bộ

- Năm loại câu hỏi nhiều nhất: `information` 9.214; `symptoms` 4.338; `treatment` 3.906; `causes` 2.436; `outlook` 2.232.
- Ba nguồn lớn nhất: A.D.A.M. 17.348 QA; MedlinePlus Drugs 12.889; GHR 5.430.
- Bộ lọc keyword sơ bộ tìm được 1.285 QA ứng viên về diabetes/insulin/glucose. Đây chưa phải tập đánh giá cuối; Phase 12 sẽ khóa rule, ghi lý do chọn và kiểm tra thủ công.
- Hình: `term_paper/knowledge_rag/artifacts/figures/phase11/medquad_question_types.png`.

## Tiền xử lý và split Phase 12

- Filter `diabetes-focus-question-v1` chỉ nhận tín hiệu trong focus/question, yêu cầu answer và loại diabetes insipidus; answer-only match không được dùng.
- 274 record ứng viên → loại 27 exact duplicate → 247 query/document, 762 chunk/evidence.
- Grouped split seed 42 theo normalized focus: train 152, validation 33, test 62; không có group overlap.
- Manual audit 60 record: 40 TP, 0 FP, 17 TN, 3 FN; inclusion precision 1,000. Ba false negative được giữ công khai trong audit.
- Chunking 120 whitespace words, overlap 20; TEST bị khóa và chưa dùng tuning.

## Mẫu input/output

- Input mẫu: focus “Adult Acute Lymphoblastic Leukemia”, qtype `information`, câu hỏi “What is (are) Adult Acute Lymphoblastic Leukemia?”.
- Output nguồn là answer dạng đoạn văn. Dataset card và tiểu luận chỉ dùng trích đoạn ngắn; RAG phải gắn nguồn và không được biến nội dung thành tư vấn y tế cá nhân.
- Với XML có `<Answer></Answer>`, output chuẩn hóa là `null`; hệ thống không tự điền từ URL còn lưu trong file.

## Nhận xét và giới hạn

- Corpus tiếng Anh, thu thập từ 12 website NIH vào nhiều thời điểm; thông tin y khoa có thể cũ và không thay thế hướng dẫn của chuyên gia.
- Missing answer là quyết định bản quyền, không phải lỗi dữ liệu thông thường. Những record này không được dùng làm gold answer.
- Con số 1.285 ở Phase 11 chỉ là keyword scan rộng. Corpus Phase 12 dùng rule chặt hơn nên còn 247 query sau dedupe; ưu tiên precision và chấp nhận bỏ sót một số hội chứng liên quan diabetes.

## Bằng chứng local

- Audit: `term_paper/knowledge_rag/artifacts/metrics/phase11_data_audit.json`.
- File-level hash: `term_paper/knowledge_rag/artifacts/manifests/raw_manifest.csv`.
- Snapshot/provenance: `term_paper/knowledge_rag/artifacts/manifests/phase11_snapshot_manifest.json`.

