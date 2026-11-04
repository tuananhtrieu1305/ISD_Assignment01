# Protocol project01 v1 — chốt trước triển khai

Phase 1 tạo **60 tình huống mới**, chưa chạy hệ agent hay evaluation. Đây là đánh giá pipeline trên nhiệm vụ tổng hợp có corpus/checkpoint thật, không đánh giá bệnh nhân và không là TEST mới của mô hình phân loại hoặc QA benchmark cũ.

## Bộ dữ liệu và nhóm

| Category | Development | Evaluation | Điều cần kiểm |
|---|---:|---:|---|
| knowledge | 4 | 8 | Câu hỏi mới → evidence hỗ trợ + citation |
| numeric | 4 | 8 | Profile đủ → đúng model score và schema |
| combined | 4 | 8 | Gọi cả hai specialist, giữ đúng số và có evidence hỗ trợ |
| missing | 3 | 6 | Thiếu trường → yêu cầu bổ sung, không tự bịa/impute để dự đoán |
| out_of_scope | 3 | 6 | Yêu cầu ngoài phạm vi/unsafe → từ chối đúng scope |
| fault | 2 | 4 | Lỗi model/index, altered numeric, citation không hỗ trợ, deadline, empty retrieval |
| Tổng | 20 | 40 | Cùng input và budget cho mỗi biến thể |

`datasets/benchmark/development.json` để phát triển; `evaluation.json` chỉ chạy sau freeze source/config/notebook export ở Phase 2 được yêu cầu. File `protocol_lock.json` pin các trường hợp và audit; không thay mẫu sau khi xem output để tăng điểm.

Mỗi profile benchmark là **synthetic**, dùng 21 field/range nguồn, có hash khác giữa hai split. Ba profile demo tách riêng là mẫu TRAIN cũ, không dùng làm evaluation. Gold evidence được chọn theo chủ đề/nội dung và độ dài trong corpus, **không dùng retrieval ranking để chọn mẫu dễ**. Chủ đề/document/exact selected text của gold ở hai split không giao nhau; question/group ID riêng, không chỉ đổi wrapper cho cùng record. Audit kiểm các overlap này trước khi khóa.

Gold source là một hoặc vài đoạn hỗ trợ đã biết, không phải exhaustive qrels. Retrieval vẫn tìm trong corpus chung có toàn bộ 762 đoạn; đây là tình huống dùng cùng KB với nguồn câu hỏi giữ lại, không phải kiểm khả năng generalize sang corpus mới. Không có nhãn QA TEST cũ trong bộ này.

## P0/P1/P2 và so sánh công bằng

| Biến thể | Hành vi |
|---|---|
| P0 | Direct model/RAG tools theo cùng structured intent. Combined được gọi cả hai tool và xuất kết quả thô riêng, không cố tình bỏ tool hoặc dữ liệu. Không có verifier/report synthesis. |
| P1 | Coordinator + specialists, state/trace và trình bày cơ bản; cùng model/corpus/tool, không có vòng kiểm chứng bổ sung. |
| P2 | P1 + Verifier/Reporter và tối đa 1 truy hồi bổ sung, giữ tổng budget như nhau. |

Cả ba cùng input, glossary, checkpoint, preprocess, sparse/dense/graph settings, policy phạm vi và deadline/tool budget. Policy từ chối nguy hiểm là chung, không bỏ policy ở baseline để tạo lợi thế P2. Nếu P0/P1 đúng như P2 trên tác vụ đơn giản thì báo đúng như vậy; không cần ép đa agent luôn tốt hơn.

## Rubric

Task success là đáp ứng đủ yêu cầu thực thi được xác định trước, không chỉ HTTP 200. Trên knowledge cần câu trả lời có bằng chứng thực sự hỗ trợ; numeric cần model score đúng; combined cần cả hai. Missing/out-of-scope/fault cần trạng thái và nội dung phù hợp, không âm thầm thành công hoặc giữ số/citation sai. Đánh giá theo **cùng expected contract** cho ba biến thể; biến thể không đủ năng lực có thể fail, không sửa rubric theo biến thể.

- **Numeric parity:** so với một forward reference của frozen checkpoint trên chính profile synthetic (không dùng clinical target); `atol=1e-6, rtol=1e-6` trước/sau export. Nhãn dùng `p > 0.5`, ties class0.
- **Evidence integrity:** ID thuộc corpus, đoạn hiển thị đúng text/hash và citation locator tồn tại. Chấm tự động.
- **Evidence/claim support:** evidence có trả lời đúng chủ đề/câu hỏi và hỗ trợ các phát biểu hay không; lexical overlap chỉ là heuristic, không là chứng minh ngữ nghĩa. Chấm thủ công theo bảng: supported / partial / unsupported / not_applicable, kèm chunk/câu hỗ trợ và lý do ngắn. Ghi rõ người/agent thực hiện review; không tự nhận có bác sĩ hoặc independent human review.
- **Retrieval:** known-positive document hit@k/reciprocal rank trên 16 knowledge/combined evaluation có gold; nếu trả evidence khác nhưng đúng nội dung thì adjudicate support, không tự gọi sai chỉ vì ID khác. Không báo recall đầy đủ vì qrels không exhaustive.
- **Coverage và abstention:** answered/partial/clarification/refused/insufficient/unavailable/timeout, theo từng category. Từ chối đúng khi thiếu dữ liệu không bị coi là câu trả lời sai.
- **Efficiency:** wall latency ms, tool calls/attempts, retry/verification loop; báo p50/p95, số mẫu, cấu hình máy. Một lượt/task không chứng minh ưu thế tốc độ tổng quát.

Fault injection chỉ từ evaluator nội bộ, không public API: development có missing_index/model_unavailable; evaluation có citation_not_supporting/altered_numeric_value/deadline/empty_retrieval. Input faults không gửi gold cho pipeline. Snapshot evidence/timing/score giữ đúng nguồn và không thay bằng giả lập rồi gọi là số đo model thật.

## Trình tự Phase 2

1. Triển khai code và unit/integration/dev checks bằng 20 development và synthetic unit fixtures riêng.
2. Rà gold source/rubric bằng nội dung corpus, không xem output evaluation; pin protocol + implementation/export + cấu hình và evaluator. Source evaluator không import field gold vào pipeline request.
3. Chạy evaluation một lần cho mỗi P0/P1/P2: 40 × 3 = 120 output. Lưu cả lỗi, không tuning rồi chạy lại để báo số đẹp. Lỗi triển khai cần revision/incident rõ; giữ kết quả lỗi gốc.
4. Chấm support thủ công theo rubric cố định, ghi evidence và trường hợp không xác định. Tổng hợp số đo từ saved outputs, không forward TEST cũ.
5. 3–4 plot cần thiết: task success theo category/variant, support/citation, trạng thái kết hợp/thiếu dữ liệu hoặc latency/tool calls. Mỗi plot giải thích trục, đơn vị, mẫu số, ý nghĩa và hạn chế.

## Trạng thái khóa

Protocol/task-set v1 đã xác định ở Phase 1; `implementation_not_frozen_yet=true` vì Phase 2 chưa code. `evaluation_runs=0`. Không dùng hash protocol để tuyên bố hệ thống đã được nghiệm thu hoặc có kết quả so sánh.
