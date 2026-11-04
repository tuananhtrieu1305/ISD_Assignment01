# Phase35 — biên bản xuất bản tiểu luận V3

Ngày: 22-10-2026. Phạm vi: xuất bản Word từ bản thảo và thực nghiệm đã khóa Phase34,
kiểm tra trình bày, kiểm thử công cụ xuất bản và smoke API/React production local.
Biên bản này chỉ xác nhận phát hành khi `releases/v3/release_manifest.json` có status PASS
và `scripts/check_phase35.ps1 -Distribution Ubuntu` kiểm hash đạt. Không cloud deploy.

## Sản phẩm

File chính: `releases/v3/Tieu_luan_AI_6_chuong.docx`,11.508.758byte, SHA-256
`5daf2aa5b5f587be5f61ecf7a2c6d32dc131c9ae2efe5df8630b4a23387060a5`.
PDF đối chiếu nội bộ: `releases/v3/Tieu_luan_AI_6_chuong_QA.pdf`,9.740.444byte,
SHA-256 `fa260dbd84f148eafde8efa4e464544c5a69c0f2194a16534f3e3682fce3d6c1`.
Ứng viên nguồn là candidate-r12; bản release là bản copy kiểm hash, không Word Save As.

202trang gồm bìa, tóm tắt/quy ước, mục lục/danh mục, mở đầu, sáu chương, kết luận,
43tài liệu tham khảo và phụ lục A–D. Chương4 là RNN–LSTM, Chương5 KG–RAG, Chương6 hệ
đa tác tử. Deploy chỉ là mục ngắn cuối chương thực nghiệm, hướng dẫn dài ở Phụ lục C.
Bìa giữ Triệu Tuấn Anh/B23DCCN053/D23CTPM01/PGS.TS Trần Đình Quế/PTIT và học kỳ của mẫu,
đúng xác nhận người dùng. Không đưa tên/thông tin cá nhân khác vào bìa.

144bảng Word native:143bảng có caption và1bảng từ viết tắt;37hình nội dung cộng logo
bìa;180caption có SEQ,180REF và256PAGEREF;549bookmark duy nhất;12OMML native.
Mở đầu4trang(11–14), các chương chính từ15–126; kết luận127–128; references129–132;
phụ lục133–202. Không tuyên bố202trang đều là lý thuyết hoặc cố ép số trang bằng trang trắng.

MLP/RNN/LSTM có6lớp học được, CNN7lớp. Thân chương có trực giác, hợp hàm và giải thích
input/output/từng phép tính; Phụ lục B giữ12kiến trúc/36contract theo dataset/family/
implementation, Phụ lục D trích5method thật. Code scratch không gọi autodiff framework;
Keras giữ TensorFlow riêng, PyTorch native riêng. Notebook/source/models không train lại
trong Phase35. Lý thuyết từ Phase34 được giữ theo chính sách cơ bản/dễ hiểu/formula-minimal.

## Cổng nghiệm thu và bằng chứng

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| Dependency Phase34 | PASS226file, read-only | checkpoint35/preflight |
| Bảo toàn khoa học | PASS31.848unique file/12khóa cha | `artifacts/manifests/phase35/preserve_after.json` |
| Cấu trúc và pagination | PASS202trang,256cache target đúng, không bbox overflow | `structure_candidate-r12.json`, `report/qa35/candidate-r12/inspection.json` |
| Word desktop | Word16 read-only PASS,202trang/144table/549bookmark/1section, Fields.Update lỗi đầu tiên0, file không đổi | `word_open_candidate_r12_r2.json` |
| Rà trang | Đủ202/202;131trang carry chỉ khi PNG byte/hash-identical,71trang cuối xem riêng | `visual_batches/candidate-r12/` và chuỗi witness r10/r11 |
| Unit/integration công cụ |82PASS/0fail/0skip | `final_tests_r2.xml` |
| Coverage8module Python mới |84,8925% combined;86,8259%statement;80,4270%branch | `final_coverage_r2.json` |
| Lint/cú pháp | Ruff17file PASS;4PowerShell parser PASS;3shell bash-n PASS | log cuối; source được khóa trong release closure |
| API/React production local |23/23E2E PASS/0retry/0skip | `ui-r2.xml`, `ui-r2.json`, `compact_bundle_r2.json` |
| Vendor Documents audits |6helper chạy exit0, source không đổi | `vendor_audits_candidate-r12.json` |
| Fidelity mẫu A06 | Giữ canonical style/section và60part gốc byte-identical; rà mẫu32trang và bản mới202trang | `report/phase35/artifact.md`, template_inventory, fidelity-r12 |

Đường dẫn artifact ở bảng không có prefix nằm trong `artifacts/manifests/phase35/`.
Không cộng test development/RED thành test nghiệm thu. Final_tests.xml r1 giữ79PASS/1FAIL
do giả định fixture idempotence sai; r2 sửa test đúng semantics, không nới guard hoặc
ghi đè evidence. Coverage là phạm vi8module công cụ xuất bản, không coverage toàn repository
hay đo lại các phase khoa học.82test đã chạy ở doc venv riêng; không có model inference.

Vendor style lint báo5.023run/4.261paragraph có direct formatting, bao gồm bìa gốc,
cell/code/field/inline formatting có chủ đích. Không diễn giải số này là0warning. Các
heading-like không dùng Heading trong ví dụ là bìa, không navigation bị mất; heading audit
nhận13H1/63H2/120H3. Image audit nhận38inline gồm logo, không floating/external image.
Content controls không có. Field audit đúng256PAGEREF/180REF/180SEQ/PAGE/NUMPAGES.
So sánh pixel A06/new có202trang khác là dự kiến do toàn bộ nội dung và footer thay;
không gọi đó là pixel-identical. Dùng đồng thời kiểm package và visual theo mẫu.

## Các sửa lỗi chỉ ở tầng xuất bản

Giữ original A06/V2/Phase34 nguyên byte/hash. Builder patch ZIP selective parts, append
style, không save qua thư viện làm mất opaque parts. Đã sửa caption alt bị thiếu,
bookmark REF chỉ số caption, caption Ch6 nhiều dòng, wrap hợp hàm LSTM, row-flow bảng,
phân biệt tensor[32]/[16]/[1] với citation và chuẩn hóa hẹp8tên tác giả có TeX escape.
Công thức RRF và set membership Ch5 chuyển sang OMML/Unicode; không đổi công thức/metric.
Timeline dùng Chromium offline raster CSS từ SVG đã khóa vì importer trước làm card đen.
SourceSVG không sửa; receipt pin source/output hash. Cả bản lỗi và RED test được giữ.

Link audit là tính toàn vẹn local/bookmark/citation target43reference, không crawl lại
mọi URL external hoặc xác nhận website luôn còn truy cập. TOC là linked materialized
REF/PAGEREF với cache thực, không trường TOC tự thêm heading. Chi tiết bảo trì ở operations.

## Phạm vi smoke và các giới hạn giữ nguyên

React typecheck/Vite production build dùng source Phase33 nguyên vẹn. Lượt r1 fullrepo
NTFS khi chạy đồng thời hash audit có20PASS/3timeout, được giữ lịch sử; không kết luận
chắc nguyên nhân duy nhất. R2 stage đúng frozen compact ZIP Phase32 lên Linux ext4:
808payloadfile/87.996.158byte cộng selfmanifest thành809file/88.165.986byte. SHA ZIP
`1f38247bf5b2a4a1b1a8036d234e8e1bcfb34931a59d4c41655e6d5da319db54` giữ nguyên.
Check bundle PASS;23ca E2E bao gồm18live comparison/60slot,55success+5Wikidata QA
unavailable đúng contract, parity neural TRAIN và desktop/mobile/a11y/error paths.
Không TEST forward, không thay deadline hay sửa API/UI để qua test.

Đây là production-build local smoke trên bundle với environment pinned hiện có, không
fresh CPU-only install, load benchmark/SLA hay deploy Render. Blueprint/chỉ dẫn đã có;
V3 cloud/live URL/header chưa được nghiệm thu. Không sửa tài khoản hoặc service cloud.

ImageNet chỉ metadata, không bịa local ảnh/accuracy; Ch5 chỉ2QAbenchmark và Wikidata
structural, không benchmark thứ ba. Ch6 là3taskview tổng hợp trên nguồn thật, điều phối
xác định/ID-bound, không LLM hoặc agent tự chủ mở. Power failed_sealed/count1 và null
telemetry gốc giữ nguyên; seedqualityn3/costn2 không bị thay bằng0. Demo không dùng để
chẩn đoán, định giá hiện tại hoặc khuyến nghị đầu tư. Không che kết quả chất lượng thấp.

## Bàn giao

`docs/demo_v3.md` có lệnh chạy/kịch bản demo; `docs/phase35_operations.md` có kiểm hash,
môi trường tài liệu, quy tắc revision và phân biệt nguồn/bản nộp. Runtime GPU/uv.lock/
metadata cũ không đổi; môi trường doc riêng được người dùng phê duyệt. Không commit,
reset, dọn source, viết lại lịch sử Git hoặc xóa dữ liệu trong phase xuất bản.

Lưu ý tác dụng phụ minh bạch: hai probe Word đầu đặt UpdateLinksAtOpen=False mà thiếu
before snapshot; tùy chọn ứng dụng có thể còn tắt. Script cuối đã bỏ thao tác; không
tự đoán giá trị khôi phục. Người dùng nên kiểm lại nếu trước đây bật tùy chọn này.
Mọi probe Word đóng không lưu, file được kiểm hash giữ nguyên.
