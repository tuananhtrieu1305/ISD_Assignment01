# Probe model đúng bản tham khảo — 02/11/2026

Người dùng yêu cầu thử đúng model có trong `RAG_KG_Tham_khao/`.

- `chatbot/app/core/config.py:51`, `chatbot/.env.example`, `README.md:35` đều ghi `gemini-2.5-flash`; không thấy model 3.1 trong cấu hình bản tham khảo hiện có. Không có file `.env` thực tế trong cây tham khảo đã kiểm. Biến môi trường của một máy chạy khác chưa được kiểm, nên không suy model họ đã chạy ở ngoài repository.
- Code tham khảo dùng `ChatGoogleGenerativeAI`. Probe dùng SDK Google đã cài qua đường API chuẩn `v1beta/models/gemini-2.5-flash:generateContent`, cùng model và temperature=0. Không import app nhóm, cài thêm wrapper hoặc dùng key của nhóm. Output được giới hạn 64 token cho chẩn đoán; không giả nhận chạy nguyên app/LangChain của nhóm.
- **Một SDK attempt, không retry**, timeout45s/trần55s. Kết quả thực: **HTTP404/NOT_FOUND sau0,764s**. Provider nói rõ model `models/gemini-2.5-flash` không còn khả dụng cho người dùng mới và đề nghị dùng3.8Flash. Không nhận được câu trả lời; usage chưa biết. Claim và lỗi giữ trong journal chung; không replay claim Phase1 đã bị404.
- Google hiện công bố2.5model chỉ phục vụ người dùng đã sử dụng trước đây: https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash . Bảng giá vẫn có standard free tier: https://ai.google.dev/gemini-api/docs/pricing . Có giá free không đồng nghĩa project/key hiện tại được quyền truy cập.
- Không đổi model/prompt/config của pipeline đang chạy sang2.5, không sửa nguồn tham khảo, không đổi key/tier hoặc bật billing. Giữ lỗi503 của3.8và404của2.5riêng; không quy404là hết quota.
- Receipt: `project01/artifacts/llm_v2/phase2/development/reference_model_probe_v1/result.json`. Phase2vẫnIN_PROGRESS;0held-outoutput, chưafreeze/Phase3.
