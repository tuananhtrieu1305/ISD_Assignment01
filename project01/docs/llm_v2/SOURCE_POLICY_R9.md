# Quy tắc kiểm chứng nguồn dùng chung — r9

File chỉnh prompt: `project01/config/prompts/source_verification_vi.txt`.

Cùng nguyên văn quy tắc được đưa vào prompt LLM trực tiếp và system message của Reporter. Quy tắc yêu cầu phân biệt kiến thức nhớ được với nguồn đã thực sự truy xuất/đối chiếu, nêu điều kiện của kết luận định lượng và không tự tạo citation. Không có điều kiện theo câu hỏi, con số cụ thể hay đáp án ép sẵn; baseline vẫn được trả lời theo kiến thức sẵn có nếu ghi đúng giới hạn.

Ví dụ: direct có thể nhớ nghiên cứu DPP nhưng phải nói chưa kiểm chứng nguồn trong lượt không có công cụ; Reporter có thể dẫn nguồn được retrieval cung cấp nếu nội dung thực sự hỗ trợ kết luận. Đây là thay đổi tiêu chuẩn trả lời của cả hai nhánh, không phải bằng chứng mới rằng pipeline tốt hơn.

## Cách thử bằng Git Bash

Dừng backend hiện tại bằng Ctrl+C, sau đó:

```bash
cd /c/DATA/assign
bash project01/scripts/run_web.sh
```

Mở <http://127.0.0.1:8031> và Ctrl+F5. Bấm **Demo đủ 5 agent · Đi bộ & 58%**, có thể sửa câu thành “Đi bộ có giúp tôi giảm hơn 50% nguy cơ tiểu đường không?” rồi bấm so sánh đúng một lần. Nút preset vẫn kèm hồ sơ TRAIN đủ21field để Risk được thực thi. Runtime phải là `source-verification-r9`; UI báo rõ nếu backend còn bản cũ.

Sửa file prompt xong cũng khởi động lại backend để hai nhánh cùng nạp một bản. Mỗi output mới ghi `source_policy_sha256`, tính từ văn bản UTF-8 đã strip ở hai đầu; có thể đối chiếu hai nhánh dùng cùng policy. Prompt thuật toán vẫn có trong notebook02; loader đọc văn bản cấu hình, không import implementation bí mật từ file ngoài notebook.

Mỗi cặp vẫn3generation: direct, Coordinator, Reporter. Query embedding dùng quota riêng. Không gọi Gemini hoặc embedding mới khi chuẩn bị/kiểm thử r9. Chưa có kết quả Gemini thật cho policy này; không hứa model sẽ từ chối câu hỏi hoặc thua pipeline.

## Giữ bản trước

R8 source/notebook/UI/dist/checkpoint trước thay đổi nằm trong `project01/provenance/before_source_policy_r9/` kèm SHA256. Không sửa receipt/evaluation/model/corpus/index cũ. Không đổi reranker, Risk, Verifier, provider hoặc hạn mức. Không train/TEST, commit/push/deploy.
