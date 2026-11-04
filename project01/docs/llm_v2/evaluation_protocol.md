# Protocol đánh giá v1 — chốt trước development/held-out

Ngày 02/11/2026. Chạy chỉ ở Phase 2 sau khi freeze thực tế. **Chưa có output benchmark LLM mới.**

## Bộ câu hỏi

`datasets/llm_v2/evaluation_v1/`: 20 development + 40 held-out; mỗi split có questions và reference riêng. Development gồm 10 direct/4 relation/2 multi/2 insufficient/2 outside; held-out 20/8/4/4/4. Tác giả reference là trợ lý đọc nguồn, không phải bác sĩ. Held-out chưa được chạy qua pipeline nhưng tác giả curation đã biết câu hỏi; không mô tả là mù với tác giả. Đây là benchmark nội bộ nhỏ, không đo hiệu quả lâm sàng.

60 fact-family riêng; tách giữa dev/held-out theo ý cần trả lời, không chỉ đổi chữ. Dùng chung KB là hợp lệ. Một số câu chung chủ đề nhưng hỏi sự kiện khác (VD cấu trúc mạch võng mạc so với bốn giai đoạn). Không lấy câu lỗi thận đã biết làm held-out. Authoring dựa QA gốc, không dựa ranking. Qrels gồm các chunk chứa quote chính xác, có thể nhiều tài liệu trùng; chưa exhaustive. Nguồn khác đúng vẫn được chấp nhận khi review ẩn nhánh, ghi bổ sung chứ không sửa raw result hoặc dùng để tune.

Không nạp `held_out_reference`/câu held-out trong index builder, query planner, reranker, prompt, demo hoặc development. Seed KG chọn theo phạm vi nguồn trước bộ câu hỏi. Không mở thêm tài liệu/cạnh hoặc sửa prompt sau khi xem kết quả held-out để báo lại cùng score. Nếu đổi, giữ baseline và công bố revision/new evaluation riêng.

## Hai nhánh và lượt chạy

`llm_direct` và `agentic_rag` dùng cùng **gemini-3.8-flash**, cùng version trả về, câu gốc tiếng Việt, temperature 0, thinking low, giới hạn answer 768 output tokens và hướng dẫn hữu ích/an toàn tương đương. Direct dùng kiến thức model, không corpus/search ngoài, không bắt bịa citation. RAG có evidence/claim verification. Cùng câu hỏi nhưng không chia sẻ đáp án giữa nhánh.

Mặc định một output/câu/nhánh: 40×2=80. Bốc thứ tự nhánh cân bằng bằng seed cố định 20261102; lưu order trước gọi. Freeze gồm hash corpus/chunk/KG/index + embedding model/dim/task, group source port/notebook/export, model/SDK/prompt/schema/rerank/config/evaluator/rubric. Model alias/version thay đổi giữa nhiều ngày phải báo incident; không âm thầm gộp thành một model bất biến.

Claim journal append-only, unique `(freeze_id,question_id,variant,repeat=1)`, trạng thái planned/claimed/complete/failed/unknown. Ghi attempt trước API; output thành công không chạy lại. Timeout hoặc mất mạng sau gửi có thể đã tiêu thụ quota: giữ unknown, không tự replay để chọn câu đẹp. Retry 429 theo phút có Retry-After tối đa 2 lần trong deadline, mỗi attempt ghi riêng; hết quota ngày dừng và resume claim chưa dùng. Auth/404/schema/model mismatch không retry vô hạn. API error giữ trong mẫu số 40/80, báo completion rate riêng. Reviewer không được loại câu trả lời kém.

## Quota / chi phí / lịch

Giữ lựa chọn người dùng: model này, nhiều ngày, trả phí 0 USD. Quota user xác nhận: 5 RPM/250k TPM/20 RPD; embedding 100 RPM/30k TPM/1000 RPD. Conservative cap serving 4 RPM/18 RPD và 60 RPM/900 RPD; cập nhật mức dùng ngoài app đầu phiên. Khi quota hết: checkpoint + next eligible time, không tiến trình ngủ nhiều ngày. Không dùng nhiều key né hạn mức.

Ước tính mỗi cặp: direct1 + RAG4 =5 call; nếu feedback thêm3 →8 call/cặp. Evaluation 200–320 generation call, ít nhất10–16 ngày nếu dùng hết20 RPD, hoặc12–18 ngày theo cap18. Development đủ20 cặp thêm100–160 call (6–9 ngày cap18), smoke/retry chưa tính. Có thể dùng subset development để ưu tiên luồng demo, ghi rõ subset thực chạy. Không giảm 40 held-out.

Ước input mỗi cặp: direct1k + plan1k + rerank6k + reporter5k + verifier5k ≈18k tokens; 40 câu ≈720k input. Output cap 768 direct +512 plan +768 rerank +768 reporter +768 verifier =3584/cặp,143.360/40 cặp, chưa overhead thinking/feedback/retry. Đây là dự trù thô, không usage thực. Feedback có thể thêm khoảng19k input/2304 output mỗi cặp. Corpus316 chunk có tổng348.397 ký tự, không lấy ký tự gọi thành tokens. Embed corpus316 request đơn tối đa, query ≤3×40 nếu không cache, tách quota embedding. Phase 2 có thể gộp nhiều text trong request standard nếu API xác nhận, không dùng paid Batch API. Index cache theo hash, không rebuild mỗi ngày.

Ghi actual provider input/output/thought/cache usage nếu trả về, null nếu không; latency end-to-end bao gồm retrieval/queue/retry/feedback, thời gian compute và chờ tách riêng. Giá free0 theo cấu hình+tài liệu, không nói đã kiểm hóa đơn. Chi phí không dùng giá paid giả tính thành hóa đơn. Judge API ngoài output80 là request riêng, chỉ dùng nếu có quota/free được khai báo; mặc định review thủ công bằng trợ lý, không thêm call judge để đốt quota.

## Rubric ẩn nhánh

Xuất câu trả lời A/B, cân bằng vị trí, che tên nhánh/model/trace khi chấm chung; giữ citation marker trung tính khi có. Chấm xong mới mở mapping. Không nói người chấm hoàn toàn không đoán được RAG từ citation. Không dùng Verifier tự chấm mình như đánh giá độc lập. Reviewer trợ lý phải ghi tên/role, người dùng review subset khi sẵn sàng; chưa có người dùng review thì báo rõ.

Mỗi mục 0–2 (tổng 0–8):

| Mục | 0 | 1 | 2 |
|---|---|---|---|
| Đúng trọng tâm | Lạc đề/đảo câu hỏi | Có trả lời nhưng rườm rà/thiếu trực tiếp | Trả lời đúng câu được hỏi |
| Đúng nội dung | Sai trọng yếu/đảo chiều/bịa số | Ý chính đúng, còn lỗi nhỏ | Các phát biểu chính khớp reference hoặc nguồn hợp lệ |
| Đủ ý | Thiếu phần chính | Đủ một phần | Bao phủ các expected points |
| Biết giới hạn | Chẩn đoán/liều/bảo đảm vô căn cứ | Còn quá chắc hoặc giới hạn chung chung | Phân biệt risk/diagnosis, thiếu nguồn, historical scope đúng |

Task success khai báo trước: tổng ≥6/8 **và** nội dung=2, không critical error. Với insufficient/outside, câu giới hạn hữu ích có thể thành công; từ chối mọi câu answerable bị mất điểm đủ ý/trọng tâm. Direct không có citation nội bộ không tự động sai nội dung. Nếu direct trả kiến thức hiện hành khác nguồn lịch sử, review cẩn thận với nguồn chính thức cập nhật, công bố phạm vi khác biệt thay vì ưu tiên snapshot một cách máy móc.

RAG riêng: citation validity (ID/URL tồn tại), support theo claim (supported/partial/unsupported/contradicted), coverage = claims cần chứng cứ có nguồn hỗ trợ / claims cần chứng cứ; không có claim thì N/A, không gán1. Báo fraction numerator/denominator. Retrieval Recall@6 trên qrels có sẵn, MRR, n answerable eligible; qrels chưa đầy đủ nên không gọi precision tuyệt đối. Đánh dấu direction error, unsupported number, historical guidance presented as current, prompt injection, timeout/quota/provider fail.

## Bảng/hình sau đánh giá

Điểm/tỉ lệ thành công hai nhánh, paired win/tie/loss theo tổng rubric, completion/errors; retrieval/support riêng RAG; latency median/p90 và total calls/tokens/queue-wait. Với n=40 báo count/mẫu số và khoảng bất định khi phù hợp; không suy ý nghĩa lâm sàng/thống kê lớn. Tối đa3–4 hình, giải thích trục/đơn vị/mẫu số/ý nghĩa. Không nhận RAG thắng trước khi có số đo.
