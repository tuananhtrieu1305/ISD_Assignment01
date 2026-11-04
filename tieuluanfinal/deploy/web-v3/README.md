# React V3 — Static Site contract (chưa deploy cloud)

Source chính `apps/web/src/v3/`. API là frozen Phase32, không API V2.
Root `render.yaml` cũ và `deploy/v3/` backend giữ nguyên hash.

Render Static Site trong **repo hiện tại**: Root Directory `apps/web`, build
`npm ci --no-fund --no-audit && npm run build`, Publish Directory `dist`,
NODE_VERSION=22.23.4. Đặt VITE_API_BASE_URL thành origin HTTPS API V3 thật,
không `/api/v3`, path, query, mật khẩu hoặc slash dư. Đây là biến public đã đóng
vào JS khi build, tuyệt đối không để secret/API key vào biến VITE_*.

Blueprint tùy chọn `deploy/web-v3/render.yaml`. Phải có rewrite `/* → /index.html`
status200 cho BrowserRouter/deep link; đổi env xong phải build lại.
Backend đặt AI_CORS_ORIGINS đúng origin frontend, không wildcard/slash cuối.
Không thay Blueprint backend đã khóa; cấu hình account/service cần owner thực hiện.

Nếu tách frontend thành repo riêng, đưa nội dung apps/web thành root và bỏ rootDir
trong bản Blueprint riêng, không sửa contract đã khóa ngầm. Source-test fixtures
ở artifacts/manifests/phase33 cần để chạy unit/E2E, không cần cho production build.
Public build không import fixtures/labels TEST hoặc checkpoint.

Gói dist local nghiệm thu dùng API127.0.0.1:5000, không dùng nguyên gói đó cho
người dùng Internet. Build lại với URL Render API của bạn. Không có cloud service
hoặc tài khoản nào được tạo/push bởi Phase33, không tự nâng gói trả phí.

SessionStorage giữ capability tạm, request credentials=omit. Trace/video E2E off
để không lưu owner header. App không nhận bệnh án/secret, không chẩn đoán/đầu tư.
CSP cho phép HTTPS connect (URL API cấu hình lúc build); tightening origin cụ thể
ở hosting là bước operator. Không coi local preview là kiểm chứng cloud headers/SLA.

Tham khảo: [Vite static deploy](https://vite.dev/guide/static-deploy.html),
[Render redirects/rewrites](https://render.com/docs/redirects-rewrites).
