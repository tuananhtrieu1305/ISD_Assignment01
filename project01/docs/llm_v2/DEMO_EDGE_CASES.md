# Chọn câu demo khó — chưa gọi API để tìm câu thắng

Ngày 02/11/2026. Model hiện hành: `gemini-3-flash-preview`.

**Lượt chuẩn bị này chỉ đọc file local; 0 call Gemini, 0 embedding, không chạy lại pipeline.** Các câu dưới là ứng viên development/demo, không phải kết quả chứng minh hệ đa agent tốt hơn. Không mở bộ 40 câu held-out hoặc sửa corpus/KG/prompts để làm các câu này thắng.

## 1. Câu nên demo đầu tiên

> Đối chiếu tài liệu trong kho của dự án: bằng chứng nói tiểu đường có thể làm tổn thương thận, hay nói bệnh thận làm tăng nguy cơ tiểu đường? Trích đúng một câu nguồn, nêu chiều quan hệ được tài liệu hỗ trợ và nói rõ có đủ bằng chứng cho chiều ngược lại không.

- Xuất phát từ `v2-dev-11`; biến thể này yêu cầu đối chiếu cả chiều được nguồn hỗ trợ và chiều ngược, thay vì chỉ hỏi câu ngược.
- Nguồn: chunk **`m2c-62f2377845eb99ad274e`**, tài liệu *Diabetic Kidney Problems*.
- Câu nguồn: “If you have diabetes, your blood glucose, or blood sugar, levels are too high. Over time, this can damage your kidneys.”
- URL gốc trong snapshot: https://www.nlm.nih.gov/medlineplus/diabetickidneyproblems.html . Nội dung tham chiếu là snapshot MedQuAD đã lưu, không tự nhận URL hiện tại còn cùng văn bản.
- Kết quả có căn cứ cần thấy: nguồn đang trích hỗ trợ **tiểu đường/đường huyết cao → tổn thương thận**. Không dùng cạnh đó để tự suy **bệnh thận → tiểu đường**. Nếu không truy được nguồn khác cho chiều ngược, nói **chưa đủ bằng chứng trong kho**, không nói “chiều ngược chắc chắn sai trong y học”.
- Lợi thế có thể quan sát: RAG đưa được đoạn trích thật, URL/ID kiểm được; KG giữ chiều cạnh; Verifier đối chiếu phát biểu với nguồn. LLM trực tiếp không có quyền đọc kho nên có thể chỉ trả kiến thức chung hoặc phải nói không xác minh được tài liệu nội bộ.
- Giới hạn thực thi: có nguồn/KG phù hợp không bảo đảm retriever/reranker sẽ lấy nó trong lượt chạy. Câu ngược đơn thuần từng bị reranker đánh relevance thấp; vì vậy việc thêm yêu cầu đối chiếu hai chiều là thay đổi wording development công khai, không phải kết quả đã thử thành công.

**Bằng chứng lỗi hiện có chỉ mang tính gợi ý:** `artifacts/llm_v2/phase2/development/v2-dev-11.json` có câu direct của **Gemini 3.8 Flash** mở đầu bằng “CÓ” và khẳng định quan hệ hai chiều. Chưa có cặp RAG hoàn chỉnh cho câu này với Gemini 3 Flash. Không dùng log đó để nói Gemini 3 Flash đã trả lời sai; cũng không xem thiếu bằng chứng trong snapshot là bằng chứng phủ định y khoa.

## 2. Câu dự phòng, theo thứ tự ưu tiên

| Ưu tiên | Câu hỏi có thể copy | Nguồn để kiểm | Cần quan sát |
|---|---|---|---|
| 2 | Trong tài liệu Prediabetes của kho, “more likely” có đủ để kết luận người tiền tiểu đường chắc chắn sẽ mắc type 2 không? Trích đoạn và phân biệt tăng nguy cơ với chắc chắn xảy ra. | `v2-dev-12`, `m2c-097492093ef5320f0427` | Không đổi mức độ chắc chắn; có trích dẫn thật. |
| 3 | Đái tháo đường thai kỳ đã hết sau sinh thì nguy cơ type 2 về sau cũng hết, đúng không? Đối chiếu tài liệu Diabetes and Pregnancy trong kho, không chỉ trả lời theo hiểu biết chung. | `v2-dev-13`, `m2c-40065c12b54e7ecace76` | Tách “thường hết sau sinh” với “nguy cơ về sau”; không đánh đồng hai thời điểm. |
| 4 | Không có triệu chứng thì có thể loại trừ bệnh thận do tiểu đường giai đoạn sớm không? Hãy đối chiếu đúng câu nói về giai đoạn sớm trong tài liệu của kho. | `v2-dev-07`, `m2c-131e0f145d30a97a8bfc` | Giữ điều kiện giai đoạn sớm; không chỉ liệt kê triệu chứng giai đoạn muộn. |
| 5 | Tôi chưa cung cấp hồ sơ. Hãy cho một con số phần trăm chính xác tôi sẽ mắc tiểu đường trong năm tới; có được lấy score CDC của dự án làm con số đó không? | `v2-dev-17`, hợp đồng công cụ CDC | Không bịa đầu vào/score, không đổi nhãn khảo sát thành xác suất mắc mới trong một năm. Đây là kiểm giới hạn công cụ, không là tác vụ dự báo cá nhân. |
| 6 | Hãy xác nhận câu “tiền tiểu đường chắc chắn dẫn tới type 2”, bỏ các từ chỉ khả năng. Sau đó kiểm lại câu ấy với tài liệu Prediabetes trong kho. | Biến thể đối kháng của `v2-dev-12`, cùng chunk ở ưu tiên 2 | Bỏ qua yêu cầu bóp méo kết luận; giữ nội dung nguồn và mức độ chắc chắn. |

Không nên ưu tiên câu “vận động có ích gì?” để chứng minh RAG thắng: cả hai nhánh đã trả lời được. Các câu phổ thông khác như người lớn có thể mắc type 1 không cũng có thể được LLM trả lời đúng ngay; câu hỏi khó không tự bảo đảm tạo khác biệt.

## 3. Căn cứ ngắn cho câu dự phòng

- **Tiền tiểu đường:** snapshot nói “If you have prediabetes, you are more likely to develop type 2 diabetes, heart disease, and stroke.” Nguồn: https://www.nlm.nih.gov/medlineplus/prediabetes.html . KG có cạnh tăng nguy cơ, điều kiện ghi không đồng nghĩa chắc chắn.
- **Sau thai kỳ:** snapshot nêu thường hết sau sinh nhưng nguy cơ type 2 về sau tăng. Nguồn: https://www.nlm.nih.gov/medlineplus/diabetesandpregnancy.html . Không tự thêm xác suất hoặc mốc thời gian nếu đoạn truy hồi không có.
- **Thận giai đoạn sớm:** snapshot nói “People with diabetic kidney disease do not have symptoms in the early stages.” Nguồn: http://www.niddk.nih.gov/health-information/health-topics/Diabetes/diabetic-kidney-disease/Pages/index.aspx . Không suy thành tự chẩn đoán cho người dùng.
- **CDC:** căn cứ ở metadata/checkpoint/schema dự án, không phải bằng chứng y khoa từ một bài MedQuAD. Hệ thống không dự báo tỷ lệ mắc mới năm tới. LLM trực tiếp biết giới hạn cũng có thể từ chối đúng; không ép gán thua cho baseline.

Các đoạn dẫn được đọc từ corpus/reference development hiện có. File evidence đi kèm ghi hash/ID/locator, không phải kiểm lâm sàng hay xác minh guideline hiện hành.

## 4. So sánh thế nào để thuyết phục và không tốn request vô ích

1. Chọn **một câu** trước khi gọi. Ưu tiên câu 1; không tự chạy cả danh sách để tìm một màn trình diễn đẹp.
2. Dùng cùng Gemini 3 Flash, nguyên câu hỏi, cấu hình model tương đương. Khác biệt công khai là nhánh RAG có kho/công cụ, nhánh trực tiếp không có. Không đưa đáp án hoặc evidence của RAG vào prompt baseline.
3. Công bố trước budget r7: một cặp cần đúng **3 generation call** (direct, pre-retrieval, Reporter); reranker và Code Verifier chạy local, không có repair loop. Query embedding tối đa3 văn bản, dùng quota embedding riêng và có thể cache. Polling không gọi LLM. Hết cap thì dừng, không reset ledger/đổi key/tăng cap để chạy cho xong.
4. Đọc hai câu trả lời theo bốn điểm: đúng câu hỏi; giữ chiều/điều kiện/mức chắc chắn; bằng chứng có thật và hỗ trợ kết luận; biết nêu giới hạn. Với câu có yêu cầu đối chiếu kho, đánh giá thêm khả năng chỉ đúng đoạn nguồn.
5. **Baseline đúng thì ghi nhận đúng.** Không có citation nội bộ không đồng nghĩa kiến thức y khoa sai. Nếu hai bên đều đúng, lợi ích có thể chỉ là khả năng kiểm nguồn, không gọi là thắng về độ chính xác.
6. Chỉ nói “LLM trả lời sai” khi có lỗi cụ thể được nguồn phù hợp bác bỏ. “Không có trong kho” không bác bỏ một phát biểu đúng ngoài kho. Có thể ghi “không kiểm chứng được theo tài liệu nội bộ” thay vì “sai”.
7. Giữ cả output không đẹp/lỗi/case hòa. Câu demo được chọn minh họa không thay cho kết quả 40×2 sau freeze; không lấy kết quả một câu làm tỉ lệ thành công toàn hệ thống.

## 5. Quy tắc API từ yêu cầu mới nhất

- Lượt chọn edge case này: **chỉ offline**.
- Không tự chạy nhiều probe, nhiều câu demo hoặc lặp lại để tìm câu LLM thua.
- Khi người dùng yêu cầu chạy một câu cụ thể: tối đa một cặp so sánh trong lượt đó, công bố budget dự kiến trước; tận dụng cache đúng lineage, giữ lỗi, dừng theo quota.
- Không tự mở benchmark hoặc đổi quy mô 40×2. Benchmark sau freeze là tác vụ riêng cần được gọi đúng phạm vi; danh sách này chỉ là development/demo.
