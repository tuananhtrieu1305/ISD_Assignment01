# Phase31 — giao thức triển khai và benchmark trước đánh giá

Chỉ bổ sung Chương6; không thay khóa/spec/source/results các phase trước. Core chạy
offline trong runtime Ubuntu đã khóa, không LLM/API key. Không tạo HTTP/React/DOCX ở đây.

## Câu hỏi nghiên cứu và phạm vi

A0 gọi trực tiếp tool theo domain người dùng chọn; A1 router → specialist;
A2 cùng router/specialist → verifier → reporter. Chính sách an toàn, tập tool và
budget giống nhau. A0 có domain hint (routing do người dùng), không giả vờ đo router A0.
Verifier kiểm tính toàn vẹn receipt, số hữu hạn, citation và provenance, không chứng minh
nội dung y khoa đúng hay sửa mô hình dự báo kém. Không dùng oracle/gold trong runtime.

Ba view: diabetes (CDC + MedQuAD), house (Ames + BIS), gold (Pink Sheet). Mỗi view100
task =25 nhóm template ×4 câu. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có
5 nhóm; nhóm1–3 train,4 dev,5 test. Mỗi split60/20/20; template và parent record/document
không giao giữa split. Câu hỏi do chương trình tạo và phải được ghi rõ synthetic template;
giá trị/số liệu/ảnh bằng chứng lấy snapshot thật, không giả làm dữ liệu người dùng thực tế.
Train dùng phát triển rule; không train base model. Task TEST là holdout template/record,
không phải bằng chứng khái quát của predictor vì đầu vào kế thừa parent TRAIN.

Numeric tool dùng checkpoint scratch seed42 MLP CDC/Ames và LSTM Gold đã khóa, serving
NumPy CPU. Gold = direct frozen tool output, đo numeric parity KHÔNG đo predictive accuracy.
Evidence tool: MedQuAD exact chunk lookup (retrieval theo ID, không benchmark QA/ngôn ngữ),
BIS/Gold lookup observation tại origin TRAIN. Không clone raw; chỉ giữ input/task view nhỏ
và refs/hash. MedQuAD citation cấp container+chunk/document, không bịa raw locator.

## Challenge riêng

OOD và unsafe là câu synthetic audit. Tool_failure là fault injection đã khai báo, cùng
fault cho cả3 variant: transient một lần, permanent unavailable, numeric tamper, citation
tamper. Fault không lấy từ câu hỏi/cấu hình public, chỉ harness nội bộ truyền vào executor.
Nhóm này báo riêng, không trộn với benign khi tuyên bố lợi ích. A2 có thể chứa lỗi integrity
nhưng không biến abstention thành câu trả lời đúng. Báo cả task_success (đáp ứng rubric) và
answer_completion (thực sự trả kết quả). Retry chỉ transient, tối đa1; permanent không retry.

## Khóa và đo

Trước agent TEST: khóa task set/golds/source/evaluator/config/runtime refs; pretest unit,
coverage>=80%, development benchmark PASS. TEST claim write-once trước chạy; thiếu result
sau consumed claim phải dừng, không retry/reset. Audit sau chạy chỉ đọc output đã lưu.
Không gọi evaluator TEST cũ, không model training hoặc tuning theo agent TEST.

Metrics theo domain/split/category/variant: task_success, answer_completion, routing
accuracy (A1/A2), numeric parity, citation exactness, unsupported/unsafe claim rate,
refusal correctness, p50/p95 wall latency, message/node count, tool-call count, peak child RSS.
Mẫu số áp dụng phải ghi n; không có mẫu dùng null. Ba variant chạy luân phiên thứ tự theo
task index để giảm order bias; một lượt/task/variant, không dựng SD3seed cho hệ xác định.
15s deadline/task bao gồm process-tool execution, max8 calls, retry1. Child local-only
process có timeout/terminate/join; no network/shell/dynamic import từ request. Cold load
đo riêng; benchmark warm catalogs, không phải cloud/API SLA. Child peak RSS là high-water
process con; parent RSS ghi riêng, không cộng nhầm thành peak đồng thời toàn máy.

Tham số/kiến trúc/rubric này được khai báo trước; declaration.json là mốc khóa cuối cùng
trước TEST. Optional LLM không thực hiện vì không cần cho deterministic core; interface
tool rõ ràng để mở rộng có phiên bản sau này, không có lời gọi remote ẩn.

## Development revision v2 trước TEST

V1/taskset.json và results/ giữ lịch sử phát triển. V2/taskset_v2.json và results_v2/
là active: gom nguyên ý định unsafe theo split, không chỉ đổi wrapper câu. Mỗi group4
task policy là biến thể hồ sơ synthetic của cùng ý định và không chuyển paraphrase qua TEST.
Đường apps/ trong provenance được giữ trong catalog/citation; trace chuẩn V3 dùng
ref tới preservation index Phase30 (index chứa exact container ref), không sửa schema cũ.
Gold/CDC/Ames dùng parent TRAIN; window ID disjoint không có nghĩa các context row Gold
không chồng nhau. Không tuyên bố agent holdout độc lập lịch sử raw hoặc predictor-generalization.
MedQuAD chỉ exact lookup corpus; không đọc câu hỏi/nhãn QA TEST hoặc gọi ranker TEST cũ.
