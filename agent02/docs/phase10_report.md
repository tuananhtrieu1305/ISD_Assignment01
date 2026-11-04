# Nghiệm thu cuối bài Agent02

Ngày 24/10/2026. Bản được chốt từ ứng viên r3 của Phase9, giữ nguyên byte DOCX/PDF
đã nghiệm thu. Không đổi nội dung khoa học, bảng số liệu, mô hình, ảnh hay source
đã khóa. Sản phẩm chính ở `output/agent02_D23CTPM01_TrieuTuanAnh.pdf`; bản DOCX
sửa được cùng tên. Notebook và source ZIP của Phase9 được giữ nguyên.

## Kiểm tra theo yêu cầu

Đã đối chiếu yêu cầu A–E,10 câu hỏi,cấu trúc báo cáo và rubric trong S1 trang PDF
8–12. `evidence/phase10/rubric_review.json` có18 hàng R01–R16/U01–U02,locators
trang PDF thật cho từng câu và20hình. PDF có bìa và8phần nội dung,đủ9mục của đề.
Đề cho phép selected code extracts;bài có8đoạn exact-source,kèm fullsource riêng.

12bảng số liệu trong Word được so từng ô với headers/rows của artifactPhase8;
8đoạn code so paragraphtext nguyên vẹn,kể cảterminal. Hai bảng mô tả còn lại là
ma trận run vàso rule/RL. Giữ rõ REF42/native khác CONTROLLED n5;gộp role trước
seed;hai learner cùng pair phụ thuộc nhau;whisker làsample std,không phảiCI.
Within-matchdelta không thay policy-qualitydelta. Gold chỉprefixTRAIN vàproxy
nhu cầu giả lập,không backtest đầu tư. Kết quả chưa tốt của retrain/state320Q
được giữ nguyên. Không tăngbudget,chọn lại checkpoint hoặc tune từfinal.

Lý thuyết cơ bản,các công thức giữ lại có ý nghĩa trực tiếp:Q-update và5bước
ra4,65;profit margin5/3;rewardmean đúng mẫu số. Mỗi hình có trục/đơn vị,legend,
n/aggregation,số đo nhận xét vàgiới hạn;không coi curve đẹp là chứng minh hội tụ.
Các ví dụ tiểu đường/nhà chỉ minh họa phạm vi policy phù hợp,không giả thành
trajectory điều trị/giao dịch. SlideMAS chỉ lànguồn tham khảo,không thành bài riêng.

## Kiểm thử và kiểm trang

245test/0skip được chạy lại ởPhase10,XML/coverage mới không ghi đèPhase9.
Coverage98,8889% chỉpublication_v1 parser/pathhelper;statement98,3871%,branch100%.
Không phải coverage vănxuôi/renderer/releaseCLI/toànproject. Script release mới
đã Ruff PASS vàchạy integration trên DOCX/PDF thực,không tạo thêm train/finalclaim.

Đã mở lại vàxem riêng28PNG125dpi ởđộ phân giải gốc. Reuse renderPhase9 vìDOCX/PDF
không đổi byte;không rerender vào evidence đã khóa. Không clipping,overlap hoặc
missingglyph;code wrap thị giác nhưngtext exact;caption vàbảng đọc được. Trang27
chỉ cókết luận ngắn vàkhoảngtrắng chủý,không phải trang trắng hoặc mất nội dung.
Kiểm màu/geometryPhase9 giữhash:chữDOCX000000/PDF0,mọi pagegrayscale,20image
placement,14native table. Phase10 nhận đủ10headingcâu trên PDF thật.

Word16.0 đã mở riêng một instance ẩn,chế độreadonly,tắtmacro;không gắn vào phiên
Word người dùng. Fields.Update không lỗi,28trang/14bảng,sourcehashkhôngđổi và
đóng instance riêng khôngsave. Đây làkiểm compatibility readonly,không tuyên bố
đã xem layout bằng Word cho mọi phiên bản. PDF đãrender làbản bố cục nộp chính.

## Phát hành và bảo toàn

Metadata cá nhân/bìa/tên PDF đã đượcuser xácnhận ởPhase9,không hỏi lại. Release
manifest cóhash/bytes/pagecount vàlink đếnZIP/notebook cũ. Hướngdẫn nộp trong
output/AG02_HUONG_DAN_NOP.md. Không tựsubmitLMS,email,commit,push hoặcdeploy.

KhóaPhase9 được kiểm trước phát hành. FullparentauditPhase8 kiểm lại7.501file
khoa học đãkhóa/7parentasset và101phép đối chiếu saveddata,không forward. Hash
uv.lock vàđầu vào V3/bài cũ được audit qua preflight cũ chỉđọc. Gitstatus ngoài
AG02 giữ như trước:discovering_ai_agent/ làuntracked đã có,không cótrackededit.
Không cài package,đổiGPUenv,doctor/bootstrap hoặc cleanup dữ liệu. Kết quả cuối
ởevidence/phase10/verification.json vàexperiment_lock.json;navigation/checkpoint
được cập nhật sau khi release thành công.
