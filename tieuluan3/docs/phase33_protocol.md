# Phase33 — phạm vi và giao thức nghiệm thu UI

Giữ toàn bộ source/API/model/metric/TEST đã khóa22–32. Snapshot UI trước thay
entrypoint: artifacts/manifests/phase33/web_before.zip và web_before.json.
Parent audit10khóa/31.641unique file trước/sau; không mở TEST hoặc train.

Runtime frontend portable Node22.23.4 Windows, checksum ZIP chính thức
cbc74b5e0982c9dbb41525fd8fb5dcd32fbee237863f7829072f4639a1ce5f20;
cache/dependency/browser trong .local và apps/web/node_modules, không cài hệ thống.
Python giữ Ubuntu/user tuananh/2venv đã khóa; không bootstrap/doctor cũ.

## Các gate trước COMPLETE

1. React topnav Tổng quan/ML/CNN/RNN–LSTM/KG–RAG/Multi-Agent;3dataset mỗi chương,
  5section ở chương2–6, history chỉ data/theory. URL query theo SRS; sai input
  route có cảnh báo, refresh/back/forward giữ selection. RNN/LSTM toggle giữ dataset.
2. Data card nguồn/size/sample/distribution/comment; theory đọc contract thật, hợp
  hàm/từng hàm/shape/parameter/mapping. Không tự thêm công thức phức tạp.
3. Một input/job chạy mọi implementation; actual_backend/device/hash/timing riêng;
  CPU portable không là native TensorFlow/PyTorch timing. Agent message/trace/evidence,
  node duration0 chưa instrument không0ms đo. Wikidata unavailable QA là đúng.
4. Historical results chỉ GET saved metric/table; filter dataset/family/split/seed/
  unit/horizon. Null không thay0. Không tính lại metric khoa học trong React;
  chart chỉ biểu diễn giá trị có sẵn, trục0 và không bỏ metric âm khỏi bảng.
5. Vitest unit/integration coverage statements/branches/functions/lines>=80%,
  no skip/only; TypeScript production build; lint/security/dependency check riêng.
6. Playwright Chromium headless:18demo request (12neural TRAIN gồm
  RNN+LSTM,3KG demo_not_benchmark,3agent parentTRAIN); compare checkpoint SHA/prediction neural với CPU smoke32,
  không accuracy hoặc TEST mới. Ch6 là parentTRAIN; Ch5 fixed free-question demo
  không historical benchmark equivalence. Unit mocks là fixture, không model mới.
7. E2E cả18data card/function/results/deploy; URL/refresh/error; viewport desktop1440
  và mobile390; Axe WCAG2A/AA/2.1AA, keyboard/focus, ảnh thật phải xem trước khóa.
  Không tuyên bố full WCAG certification, Safari/Firefox/device thật nếu chưa test.
8. Capability24random byte hex48 trong sessionStorage theo API origin, không cookie/
  localStorage/URL/log. Job ID riêng dataset/family, refresh GET-only, không re-POST.
  Không uploadSVG/URL/path/pickle. Escaped React Markdown, không raw HTML.
  Playwright trace/video off để không lưu owner headers; screenshot chỉ TRAIN demo.
9. Final evidence tên mới, không ghi đè RED/development hoặc file32. Build và E2E
  final cùng source fingerprint; preservation_after, docs, release lock và hash verify.

## Lịch sử phát triển giữ riêng

- TDD RED App chưa tồn tại; cancellation body thừa schema_version bị bắt và sửa
  theo OpenAPI frozen. Không sửa backend để hợp fixture.
- Browser devv1: gọi Window.fetch với this=ApiClient gây Illegal invocation; native
  direct fetch200 nhưng object-method fail. Dừng đúng cây Playwright PID24956 sau
  chẩn đoán, giữ failed screenshots/log; không đủ suite cuối, không coi PASS.
- Native fetch regression RED→GREEN, bind global receiver. Cross-realm DOMException
  AbortError được giữ đúng loại, không đánh đồng network failure.
- Devv2:18livecase PASS/21of22E2E PASS; Axe phát hiện contrast thấp ở số thứ tự
  dataset do opacity. Sửa opacity/color, giữ ngưỡng accessibility, không tắt rule.
- Coverage devv1 thiếu các runner/trace nhánh; bổ sung tests thay vì loại source
  khỏi coverage. Redundant-zero node test sửa locator all vì2node thực chưa đo riêng.
- Presentation v2 thu gọn fenced JSON, cuộn tab active vào viewport mobile; không
  đổi data/model/metric/backend. V3 sửa caption áp dụng riêng neural weights,
  không gán B0–B4/A0–A2 là3framework thần kinh hoặc có learnable layer count.
  Các candidate v1/v2 giữ nguyên làm lịch sử; active acceptance-v3/e2e-v3.

Tài liệu chính thức đã đối chiếu: [React effects](https://react.dev/reference/react/useEffect),
[Vite](https://vite.dev/guide/), [Playwright](https://playwright.dev/docs/intro).
Context7 không khả dụng. Chưa cloud deploy/push/tính phí hoặc DOCX34–35.
