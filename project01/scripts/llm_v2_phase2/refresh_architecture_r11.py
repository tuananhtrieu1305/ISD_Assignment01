"""Present the active four-agent architecture; keep previous design as history."""
from pathlib import Path
P=Path(__file__).resolve().parents[2];path=P/'docs/llm_v2/architecture.md'
old=path.read_text(encoding='utf-8')
assert not old.startswith('# Kiến trúc hiện hành r11'),'Already revised'
current='''# Kiến trúc hiện hành r11 — hỏi đáp 4 agent

Theo yêu cầu mới nhất của người dùng, request chỉ có câu hỏi, không tự kèm hồ sơ TRAIN và không chạy Risk Agent. Xem [hướng dẫn hiện hành](FOUR_AGENT_R11.md).

```text
question
  ├─ LLM trực tiếp: Gemini (1 generation)
  └─ Coordinator: pre-retrieval (1 generation)
       → Knowledge Agent: BM25 + embedding + mini-KG + RRF + reranker local
       → Reporter: câu trả lời từ evidence (1 generation)
       → Verifier: Gemini kiểm/sửa một lần (1 generation) + code kiểm integrity
       → phát hành bản đã duyệt
```

Pipeline có4agent; retrieval/rerank là bước bên trong Knowledge, phát hành nằm sau Verifier. UI chỉ vẽ một sơ đồ4agent. Toàn cặp4generation, query embedding dùng hạn mức riêng; reranker và đồ thị local. Không có repair call thêm.

Input: POST `/api/v2/compare` nhận `{question}` duy nhất. Profile/mode cũ bị từ chối, không âm thầm bỏ qua. Tab graph dùng GET `/api/v2/knowledge-graph` trả35node/35assertion có quote/nguồn theo đúng MiniKG đang hỗ trợ retrieval. VẽSVG/React trong browser, không Neo4j/server graph/CDN hoặc generation extraction khi mở tab.

Giữ prompt kiểm nguồn chung, Gemini generation và semantic Verifier từ r10. Không đổi provider/key/hạn mức hay đánh giá lại held-out. Checkpoint/model/dataset/output Risk cũ được giữ lịch sử, không tham gia luồng demo mới.

<details>
<summary>Thiết kế r7–r10 trước yêu cầu bỏ Risk (chỉ tham khảo lịch sử)</summary>

'''
path.write_text(current+old+'\n</details>\n',encoding='utf-8')
