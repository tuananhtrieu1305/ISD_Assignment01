# Phase33 — biên bản nghiệm thu React UI V3

Ngày 21/10/2026. Frontend hiện hành ở `apps/web/src/v3/`, dùng API V3 đã khóa
ở Phase32. Bằng chứng phát hành cuối cùng nằm tại
`artifacts/manifests/phase33/verification.json` và `experiment_lock.json`;
chỉ coi phát hành hoàn tất khi verifier và kiểm hash đều PASS.

## Phần đã thực hiện

- Sáu tab Tổng quan, ML, CNN, RNN–LSTM, KG–RAG và Multi-Agent; mỗi chương có
  ba dataset. RNN/LSTM có lựa chọn riêng, giữ dataset khi chuyển họ mô hình.
- Chương2–6 có Dữ liệu, Hợp hàm & lý thuyết, Chạy so sánh, Kết quả đã lưu và
  Triển khai. Chương1 là case study lịch sử, không giả lập mô hình đã train.
- Dataset card dùng nguồn/link/kích cỡ/mẫu/phân bố/nhận xét thật. Phần lý thuyết
  diễn giải cơ bản, thể hiện hợp hàm, từng hàm, shape và parameter từ contract;
  KG/Agent không bị mô tả như mạng neural có learnable layers.
- Một input/job so sánh toàn bộ implementation: ba neural, B0–B4 hoặc A0–A2.
  Có input validation, upload ảnh, polling, hủy job, phục hồi sau refresh,
  lỗi có cấu trúc, backend/device/hash, citation và agent trace.
- Kết quả khoa học chỉ đọc artifact đã khóa, có filter theo dataset/họ/split/
  seed/unit/horizon. Không tính lại accuracy hoặc chọn checkpoint theo TEST.
  Null cost và failed seal Power RNN/PyTorch seed17 giữ nguyên.
- UI sáng/xanh lam kế thừa web cũ, tách component theo chức năng, hỗ trợ mobile,
  URL trực tiếp, keyboard/focus và reduced motion. Source UI cũ giữ làm tham chiếu;
  snapshot trước sửa nằm ở `web_before.zip`, không xóa dữ liệu người dùng.

## Bằng chứng kiểm thử cuối

Active candidate: `acceptance-v3` và `acceptance-e2e-v3`.
Source fingerprint:
`622536a29e86a67dd5f149d1c1f252f7b236e98cb625a7dfd2d3eeb2fda3fb50`.

101 test duy nhất PASS, không skip: 60 Vitest, 10 legacy regression,
23 Playwright và 8 Python auditor. Các XML RED/development và candidate cũ giữ
riêng, không cộng vào số nghiệm thu. Coverage chỉ áp dụng source UI V3:
statements97,06%, branches88,72%, functions95,51%, lines97,52%; không phải coverage
của toàn repository hoặc các model đã khóa.

Lint, TypeScript, production build, Python AST/Ruff, parser năm PowerShell
entrypoint và semantic check Blueprint YAML PASS. npm audit snapshot ghi nhận
0 vulnerability cho toàn dependency tree tại thời điểm kiểm. Kiểm này không
thay thế audit Git history hoặc bảo đảm dependency tương lai an toàn.

Playwright Chromium headless: 23/23 PASS, retries0, không flaky/skip. Có 18 lượt
demo thực qua API: 12 neural TRAIN, 3 agent `parent_train` và 3 KG
`demo_not_benchmark`. Tổng 60 slot: 36 neural, 10 QA available, 9 agent thành công;
5 QA Wikidata unavailable đúng contract. Neural prediction/checkpoint hash/backend/
device khớp reference CPU Phase32; đây không phải phép đánh giá chất lượng mới.
Đọc `phase33_scope_clarification.md` để phân biệt nhãn template TRAIN-only cũ
với marker input_split thật; không viết lại receipt để đổi scope.

Bundle HTML/JS/CSS thực được browser tải khớp byte/hash build copy nghiệm thu:
HTML640byte, JS222.620byte, CSS15.634byte. Build snapshot và ZIP riêng nằm dưới
`dist/phase33/`; không dùng thư mục build mutable làm bằng chứng duy nhất.

Bảy PNG cuối đã được xem trực tiếp và seal trong `visual_qa.json`: CNN IDRiD,
RNN vàng, LSTM vàng, KG MedQuAD, tác tử tiểu đường, mobile tổng quan và mobile CNN.
Không thấy chồng lấn/card tràn trang; JSON dài thu gọn, citation/hash wrap và node
duration0 ghi rõ chưa instrument. Axe, keyboard và kiểm width có bằng chứng
riêng; không tuyên bố chứng nhận WCAG đầy đủ hay kiểm Safari/Firefox/device thật.

## Bảo toàn và giới hạn

Audit trước/sau PASS 31.641 file được bảo vệ qua 10 khóa dependency. Không sửa
source/model/checkpoint/metric/TEST Phase22–32, không train lại, không mở lại
TEST hay đổi seal. Backend Python vẫn runtime Ubuntu/user tuananh đã khóa;
frontend dùng Node22.23.4 portable với checksum chính thức, không cài hệ thống.

API CPU chạy NumPy portable cho weights đã train bằng scratch/Keras/PyTorch;
timing demo không phải tốc độ native framework hay benchmark accuracy.
KG demo compact không tương đương benchmark candidate-per-split lịch sử;
Wikidata chỉ structural browser. Tác tử là công cụ deterministic ID-bound,
không LLM/tác tử suy luận tự do. Không dùng dự đoán cho chẩn đoán hay đầu tư.

Capability lưu sessionStorage theo API origin, không URL/localStorage/log;
refresh chỉ GET, không tự gửi lại POST. Không giữ input riêng tư. Upload chỉ
PNG/JPEG có guard, Markdown escaped, không raw HTML hoặc request path/pickle.
Trace/video Playwright tắt để không ghi capability header. Job ephemeral, TTL30phút;
không có hệ tài khoản hay bảo toàn job sau redeploy.

TDD/frontend/security/E2E skills đã dẫn đến test native-fetch/cross-realm abort,
guard token/upload/URL, sửa contrast và cải thiện mobile JSON. Các lần FAIL và
snapshot source auditor trước sửa scope vẫn được giữ, không che bằng kết quả cuối.

## Bàn giao

Hướng dẫn hai terminal tại `docs/phase33_operations.md`. Kiểm hash sau phát hành:

```powershell
.\scripts\check_phase33.ps1 -Distribution Ubuntu
```

Static Site Blueprint và hướng dẫn Render ở `deploy/web-v3/`, không sửa Blueprint
backend/root cũ. Build nghiệm thu trỏ API local127.0.0.1:5000; deploy thật phải build
lại với API HTTPS và CORS frontend chính xác. Chưa tạo/push/deploy service cloud,
chưa kiểm Render headers thực tế hoặc nâng gói trả phí. Chưa tích hợp DOCX;
Phase34–35 chỉ bắt đầu khi người dùng yêu cầu.
