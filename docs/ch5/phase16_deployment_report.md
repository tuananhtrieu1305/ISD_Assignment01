# Phase 16 — Agent KG–RAG, API, React UI và Render

## 1. Kết quả

Phase 16 đã đóng gói cấu hình B4 khóa ở Phase 15 thành một ứng dụng CPU-only chạy hoàn toàn cục bộ, không dùng API key, GPU hay Neo4j server. Agent chỉ có hai tool trong allow-list: `medical_retriever` và `finance_retriever`.

Gói deploy có artifact version `phase16-b4-560c671a3920`, gồm 87.183 chunk, 203 graph anchor và bốn index BM25/LSA. Tổng kích thước là 68.393.687 byte (65,23 MiB), thấp hơn ngân sách 192 MiB. Manifest lưu SHA-256 và kích thước của cả sáu file; endpoint `/ready` kiểm tra toàn vẹn trước khi báo sẵn sàng.

## 2. Luồng xử lý

```text
React /rag
  → POST /api/agent/query
  → validate + rate limit + safety guard
  → router: medical | finance | abstain
  → BM25 + LSA + graph expansion
  → weighted RRF B4 (0,6 / 0,1 / 0,3)
  → grounded extractive answer
  → answer + citation + evidence + graph path + artifact version
```

Không có nhánh thực thi shell, `eval`, `exec` hoặc tool do người dùng tự đặt tên. Câu hỏi ngoài miền, prompt injection, yêu cầu liều dùng/chẩn đoán cá nhân và khuyến nghị mua bán đầu tư đều bị từ chối trước khi load index.

## 3. API contract

Request duy nhất:

```json
{
  "question": "What are common complications of diabetes?",
  "domain": "auto"
}
```

`domain` chỉ nhận `auto`, `medical`, `finance`; `question` sau chuẩn hóa phải dài 3–500 ký tự. Response luôn công khai các trường `answer`, `domain`, `citations`, `evidence`, `route`, `graph_path`, `abstained`, `abstention_reason`, `latency_ms`, `artifact_version`, `warning` và `request_id`. Lỗi trả mã an toàn 400/413/429/503/504; không trả traceback hoặc đường dẫn local.

## 4. UI và kiểm thử E2E

Trang `/rag` kế thừa hệ thiết kế của web hiện tại và bổ sung domain switch, câu hỏi mẫu, badge miền/tool, grounded answer, graph path, danh sách citation, evidence drawer và cảnh báo y khoa/tài chính.

E2E chạy Edge headless ở viewport 1440×1200 trên hai server local. Kết quả PASS: route `medical`, tool `medical_retriever`, 1 citation, 5 evidence, 4 graph node, không abstain và đúng artifact version. Ảnh bằng chứng:

![Agent KG–RAG trả lời có citation và graph path](../report/assets/ch5_knowledge_rag/phase16_agent_medical.png)

Log máy đọc được: `artifacts/e2e/phase16_e2e.json`.

## 5. Chạy local

Terminal 1:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m backend.app
```

Terminal 2:

```powershell
cd web
npm ci
npm run dev
```

Mở `http://localhost:5173/rag`. Backend mặc định ở `http://127.0.0.1:5000`.

Các lệnh xác minh:

```powershell
& '.\backend\.venv\Scripts\python.exe' -m pytest backend\tests term_paper\tests\test_phase16_runtime.py -q -p no:cacheprovider
& '.\backend\.venv\Scripts\python.exe' -m term_paper.tools.verify_phase16
cd web
npm test
npm run type-check
npm run build
npm audit --audit-level=moderate
```

## 6. Deploy Render

`render.yaml` định nghĩa đúng hai service:

- `isd-assignment01-api`: Python 3.12.14, cài `backend/requirements.txt`, chạy verifier hash/config khi build, khởi động bằng một Gunicorn worker bốn thread và health check `/ready`;
- `isd-assignment01-web`: static site build bằng `npm ci && npm run build`, rewrite SPA về `index.html`, nhận hostname API bằng `VITE_API_BASE_URL` và đặt security headers.

Render yêu cầu web service lắng nghe `$PORT`; start command hiện tại là `gunicorn backend.app:app --bind 0.0.0.0:$PORT`. HTTP health check phải trả 2xx/3xx trong 5 giây; `/ready` chỉ hash-check package và cache kết quả, không load toàn bộ hai index. Blueprint dùng các trường `buildCommand`, `startCommand`, `healthCheckPath`, `staticPublishPath`, `headers` và `routes` theo tài liệu chính thức:

- https://render.com/docs/deploy-flask
- https://render.com/docs/blueprint-spec
- https://render.com/docs/health-checks
- https://render.com/docs/python-version

Các tài liệu trên được đối chiếu ngày 2026-10-13. Khi dùng hai service đã tạo thủ công thay vì tạo Blueprint mới, cần copy đúng build/start command và biến môi trường trong `render.yaml`; không tạo thêm bản service trùng tên.

## 7. Giới hạn vận hành

- Index Phase 14 được serialize bằng scikit-learn 1.9.0; backend và Render ghim 1.9.1 để tương thích với model legacy. Smoke thực tế trên 1.9.1 đã PASS cho cả hai domain, nhưng scikit-learn phát cảnh báo minor-version khi load KG index. Manifest ghi rõ hai version để không che giấu rủi ro persistence.
- Cold query đầu tiên phải load 65,23 MiB artifact và có thể chậm hơn; E2E local ghi 2.606,6 ms. Query sau dùng bundle trong RAM.
- Finance dùng extractive answer, chưa có program generator/calculator; không diễn giải kết quả thành tư vấn đầu tư.
- Medical dùng corpus học thuật và chỉ trả đoạn trích; không thay thế chẩn đoán hoặc tư vấn chuyên môn.

## 8. Bằng chứng hoàn thành

- Backend + Phase 16 regression: 36 test, sau khi giữ nguyên root API contract đạt PASS.
- Frontend: 10/10 unit test PASS; TypeScript PASS; Vite 8.3.4 production build PASS.
- Dependency audit: 0 vulnerability.
- Runtime verifier: 8/8 PASS, gồm hash, lock Phase 15, allow-list, Render config, React route và real-runtime smoke.
- Core service coverage: 95%.
- Phase 15 public TEST không chạy lại; manifest vẫn `COMPLETE`, `run_count=1`.
