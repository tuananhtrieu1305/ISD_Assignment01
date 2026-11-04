# Phase34 — tích hợp nội dung tiểu luận sáu chương

Hoàn thiện nội dung ngày22/10/2026; trạng thái phát hành có hiệu lực ở
`artifacts/manifests/phase34/checkpoint.json` và `verification.json` sau khi khóa và
verify PASS. Không coi sự tồn tại của bản thảo là DOCX đã nghiệm thu.

## Nội dung đã tích hợp

Nguồn hiện hành chọn qua `report/active_manuscript_v3.json`. Bản liền mạch
`report/phase34/manuscript.md` gồm Mở đầu, sáu chương, Kết luận, references và bốn
phụ lục. Front matter/tóm tắt/từ viết tắt riêng, publication_order trong manifest
hướng dẫn ghép Word không nhân đôi nội dung. Danh mục nội dung/hình/bảng chưa gán
số trang giả.

Mở đầu và Kết luận viết mới theo V3. Ch1 giữ mạch lịch sử V2, cập nhật phạm vi và
thêm ba benchmark. Ch2–6 dùng đúng bản thảo đã nghiệm thu: Ch3 r2, Ch4 hợp nhất,
Ch5 r2, Ch6 active_report_r2. Không sửa đè bản gốc. Triển khai được cập nhật theo
API32/UI33 đã kiểm local, là mục cuối Ch2–6; không có chương deploy riêng.

Mỗi chương có ba dataset/corpus/task view. Có18hồ sơ nguồn/link/size/schema/mẫu/
phân bố/nhận xét và hạn chế, cùng36model contract của12kiến trúc neural. ImageNet
chỉ metadata, không bịa đủ ba ảnh/mẫu hoặc phân bố full data. Task Ch6 kế thừa
parent thật với câu hỏi template tổng hợp, không tải bản raw trùng.

Lý thuyết theo ví dụ, trực giác và flow/shape rồi mới tới công thức tối thiểu.
Hợp hàm và từng hàm lấy từ cùng contract dùng trên API/UI. Phụ lục B giải thích
shape/tham số/mapping; Phụ lục D trích5method nguyên văn từ source scratch/Keras/
PyTorch, có dòng/hash. Không chèn vòng train dài vào thân chương hoặc gán metric
cũ cho một đoạn mô hình minh họa mới.

## Nghiệm thu nội dung

6chương,58mục đánh số cấp hai;67bảng thân chương và76bảng phụ lục, tổng143caption;
37hình được liên kết nguyên từ nguồn;43citation được hợp nhất theo lần xuất hiện.
43bảng gốc của Ch2–6 giữ nguyên nội dung số. Các bảng mới từ data card/EDA/contract
được pin theo hash. Source code trích bằng AST, không import/construct model.

Ma trận54yêu cầu liên kết locator và bằng chứng trước. Trạng thái không đánh đồng
“đã có nội dung/bằng chứng local” với “đã xong Word/cloud end-to-end”. Outline
extension phase34.integration.1 map các mục dự kiến sang heading thực tế, giữ
outline/spec22 nguyên byte/hash; không đổi dataset/họ mô hình/protocol.

38test nghiệm thu r3 PASS/0skip gồm parser/citation/path, count contract, assembler
idempotency, manuscript audit và synthetic release packaging. Coverage ba module
editor/assembler/auditor92,75%; từng module trên80%. Không cộng XML RED/development/
r1/r2 hoặc test khoa học cũ. Integration r3 chỉ ghi fixture tạm riêng đã kiểm phạm vi,
không ghi publication, kể cả khi test được chạy ở phase sau.
Lint/format/AST8file Python mới và PowerShell
wrapper parser PASS. Static type checker chưa cấu hình; không gọi AST là type check.

Audit parent trước/sau11khóa bảo vệ31.772file phải PASS trước release; check sau
phát hành chỉ hash. Không train/tuning/forward validation/TEST hoặc đổi env/uv.lock,
namespace/load index. Không sửa metric/checkpoint/Power failed seal hay TESTcount1.

## Các giới hạn được giữ trong nội dung

MLP không luôn vượt baseline; IDRiD có chất lượng thấp; LSTM không mặc định thắng
RNN/last-value. Ch4 giữ cost null của orphan Power và mẫu số n2 riêng qualityn3.
Ch5 không coi citation hợp lệ là answer đúng, không gọi Wikidata là QA benchmark
thứ ba. Ch6 gain A2 là containment trong challenge xác định, không tăng predictive
accuracy hoặc chứng minh suy luận mở. CPU portable/nativeGPU/cloud là các phạm vi
khác nhau. Không dùng output làm lời khuyên chuyên môn.

## Bàn giao Phase35

Reference A06 được trích văn bản/style/section XML read-only. Typography và geometry
được ghi ở `report/phase34/artifact.md`, nhưng chưa render reference hoặc DOCX mới.
Kỹ năng documents yêu cầu render gate; dependency loader/bundled renderer chưa có
trong tool hiện hành, nên Phase34 không tạo một DOCX chưa kiểm rồi gọi là hoàn tất.
Full distillation, font/table/figure/code layout, TOC/SEQ/REF/PAGE và từng trang là35.

Article-writing/brand-voice giúp giữ giọng A06: ví dụ trước, cơ chế và bằng chứng sau,
không đưa công thức trang trí. Documents skill giữ yêu cầu theo mẫu và tách structural
evidence khỏi visual QA. TDD/verification tạo gate số bảng/hình/link/citation, bảo toàn
và phát hành chỉ từ bằng chứng cuối.

Đọc `docs/phase34_operations.md`; sau release kiểm bằng:

```powershell
.\scripts\check_phase34.ps1 -Distribution Ubuntu
```

Không commit/reset/cleanup hoặc tự bắt đầu35. DOCX cuối chỉ phát hành sau khi người
dùng yêu cầu35 và toàn bộ gate Word/render thực sự PASS.
