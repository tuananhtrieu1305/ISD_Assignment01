# Demo hiện hành: hỏi đáp 4 agent + tab KG

Theo yêu cầu mới nhất, bản `four-agent-r11` bỏ Risk/hồ sơ khỏi demo. Lượt trước tự lấy21trường từ hồ sơ TRAIN mẫu `row_0048946`; các trường đó không được trích từ câu hỏi. Luồng mới chỉ gửi câu hỏi người dùng nhập, không gọi checkpoint CDC.

## Một pipeline duy nhất

```text
Câu hỏi
  → Coordinator: Gemini lập truy vấn
  → Knowledge Agent: BM25 + embedding + KG → RRF → rerank local
  → Reporter: Gemini tạo bản nháp có nguồn
  → Verifier: Gemini kiểm/sửa cùng một call + code kiểm integrity
  → Câu trả lời đã duyệt
```

Sơ đồ trên UI có đúng4ô và phần chi tiết có đúng4agent tương ứng. Retrieval/rerank là hai công đoạn bên trong Knowledge, còn phát hành là công đoạn sau kiểm chứng. Backend lưu6stage để không mất input/output thật;6stage không được vẽ thành pipeline thứ hai cạnh pipeline4agent.

Nhánh LLM trực tiếp vẫn đặt cạnh câu trả lời của pipeline như trước. Giữ nguyên prompt kiểm nguồn dùng chung và Verifier Gemini r10. Một cặp hợp lệ vẫn4generation (1direct+Coordinator+Reporter+Verifier); embedding có quota riêng, reranker local. Không thêm call để vẽ KG.

## Bốn tab

1. **Câu hỏi**: một ô nhập, một nút Trả lời. Không hồ sơ, preset, bảng đánh giá, lựa chọn agent hoặc dữ liệu huấn luyện. UI không fetch examples/summary/development nữa.
2. **Câu trả lời**: giữ hai câu trả lời, nguồn dẫn và nhận xét Verifier.
3. **Luồng xử lý**: một sơ đồ4agent và input/output thực của cùng các agent đó.
4. **Đồ thị tri thức**: thay tab So sánh & đánh giá bằng mini-KG đang dùng cho retrieval.

## KG nhẹ, dùng dữ liệu thật

- Endpoint GET `/api/v2/knowledge-graph` lấy các thực thể và assertion đã được `MiniKG` kiểm quote/source. Hiện35node/35assertion; không tạo triple mới để trang trí.
- Giao diện SVG/React, layout lực có giới hạn và xác định được, không thêm dependency, Neo4j, database server, CDN hoặc request LLM.
- Kéo nút/kéo nền, cuộn hoặc bấm+/− để zoom, tìm thực thể tiếng Việt, bấm nút hoặc cạnh, chọn chỉ vùng lân cận. Tên quan hệ mặc định chỉ nổi khi được chọn để giảm rối; có thể bật toàn bộ.
- Bấm cạnh xem chiều quan hệ, điều kiện, câu trích, chunkID và URL gốc. Nguồn theo snapshot MedQuAD; không tự nhận đã cập nhật guideline.
- Đây là mini-KG có kiểm nguồn hỗ trợ kho316chunk, không phải toàn bộ sự kiện y khoa trong KB. Quan hệ lexical MENTIONS không bị biến thành assertion nhân quả.

## Chạy trong Git Bash

Dừng backend cũ bằng Ctrl+C, rồi:

```bash
cd /c/DATA/assign
bash project01/scripts/run_web.sh
```

Mở <http://127.0.0.1:8031>, Ctrl+F5 và gửi câu hỏi mới. Runtime mới là `four-agent-r11`. Lượt cũ có Risk được giữ nguyên trong artifacts, không tự viết lại kết quả; không tiếp claim revision cũ bằng code mới.

Tab KG có thể mở độc lập khi có dữ liệu dù Gemini hết quota; GET graph không gọi model. Muốn so sánh câu trả lời vẫn cần đủ4generation slot và key backend.

## Kiểm chứng

-10backend check PASS: endpoint35/35có provenance, Risk endpoint không còn hoạt động, profile payload bị từ chối, question-only API,4slot và4role.
- Full pipeline offline PASS:6stage complete,4generation giả lập, Risk0call. BM25/KG/reranker/integrity chạy thật; generation/semantic review mock và dense tắt. Đây là kiểm kỹ thuật, không phải kết quả chất lượng mới.
-20browser/layout check PASS trên build thật vớiAPI local intercept: form chỉinput+nút, payload chỉquestion, một sơ đồ4agent, KG35/35, zoom, kéo node, nguồn chính xác, tìm tiếng Việt, hàng xóm, mobile không tràn và khôngJSerror.
- Build22module và notebook-export parity3notebook/16module PASS. Không cài dependency hoặc thay env GPU.
- Số request Gemini/embedding mới trong lượt sửa này=0; chưa chạy cặp live r11. Các prompt/logic generation và semantic verification được giữ từ bản đã hoạt động.

Source r10 trước sửa giữ ở `project01/provenance/before_four_agent_r11/` kèmSHA. Model CDC, notebook/mẫu dữ liệu/kết quả cũ được giữ cho lịch sử; chúng không tham gia request mới. Không xóa dataset/checkpoint/receipt, train, TEST, commit/push/deploy. Phase2 vẫn chưa đóng; bỏ tab đánh giá chỉ là đổiUI, không giả nhận benchmark đã xong.
