# Phương án local Phase 35 đã được đồng ý

Ngày 22/10/2026, sau khi được hỏi có đồng ý cấu hình bộ dựng Word/PDF local riêng,
khóa phiên bản và không thay môi trường GPU hay không, người dùng trả lời “có”.
Đây là đồng ý thực hiện phương án thay thế cho workspace artifact runtime chưa được
cấp trong phiên này, không phải đồng ý bỏ qua render/visual QA hoặc nghiệm thu Word.

Phạm vi triển khai:

- Tạo toolchain riêng trong WSL Ubuntu, dưới
  `/home/tuananh/.local/share/ai-term-paper-docs-v1/`.
- Dùng Python 3.11.17 đã có làm base chỉ đọc, tạo venv tài liệu riêng với requirements
  có phiên bản và hash; không pip install vào hai venv GPU hoặc sửa uv.lock của dự án.
- Tải gói LibreOffice headless/Poppler chính thức theo metadata Ubuntu đã kiểm chứng,
  khóa version/SHA-256 rồi giải nén vào sysroot riêng; không apt install/upgrade hệ thống.
- Dùng bản sao font đã có trên máy chỉ để render local; không phát hành font Microsoft
  cùng source hoặc release. Ghi hash và font substitution nếu có.
- Sử dụng renderer của kỹ năng Documents với executable local đã xác minh, profile
  tạm riêng; không dùng Office/LibreOffice desktop của người dùng hoặc lưu ngược mẫu.
- Vẫn giữ mọi gate template distillation, fidelity, field/navigation, render và xem
  tất cả trang. Khác biệt giữa LibreOffice-render và Word-open/field-refresh phải ghi rõ.

Không nằm trong đồng ý này: nâng dependency GPU, sửa TEST/model/metric/source đã khóa,
thay nội dung khoa học để đẹp kết quả, xóa dữ liệu, push/commit, cloud deploy, API key,
tài khoản/gói trả phí hoặc gửi dữ liệu báo cáo ra dịch vụ ngoài.

Đây là deviation `phase35.local-toolchain.1`, không gọi runtime tự cấu hình là Codex
bundled runtime. Bằng chứng preflight cũ vẫn giữ; receipt mới lưu riêng trong
`artifacts/manifests/phase35/local_toolchain_r1/`.
