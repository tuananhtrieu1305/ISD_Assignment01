# Phase34 — phạm vi tích hợp bản thảo

Đọc toàn bộ kế hoạch V3, dependency24–33 và AGENTS trước thực thi. Giữ dirty worktree
của người dùng (5 modified/55.860 deletion/24 untracked root trước bắt đầu), không commit,
reset hoặc cleanup. Không model construction, training, validation forward hay TEST forward.

Bản tích hợp mới ở `report/phase34/`; nguồn chương đã khóa chỉ đọc. Ch1 giữ mạch lịch sử
V2, sửa phạm vi RNN–LSTM/CNN và bổ sung Iris/MNIST/ImageNet metadata. Ch2–6 dùng đúng
active revision, không bản cũ. Mở đầu/Kết luận viết mới theo kết quả thực.

Các mục triển khai cập nhật API32/UI33, phân biệt NumPyCPU với nativeGPU và cloud chưa
deploy. Không chương deploy riêng. Giữ nguyên bảng số/hình gốc, thêm caption/citation/
cross-reference và phần mẫu dữ liệu từ nguồn đã khóa. Phụ lục giải thích hàm lấy cùng
contract API/UI; initialized contract chỉ là mô tả cấu trúc, không phải model vừa train.

Gate nội dung: 6chương/18dataset, heading phân cấp/caption liên tục, nguồn citation có
thật, mọi local image/link tồn tại, table metric gốc giữ nguyên giá trị, 54requirement
có locator/bằng chứng/trạng thái rõ. Các gate page count/Word/render/cloud chưa thực hiện
phải ghi deferred, không tự gọi end-to-end COMPLETE cho toàn dự án.

TDD cho bộ parser/assembler/auditor bằng synthetic fixture; integration kiểm bản thảo
và nguồn khóa, coverage>=80% cho code mới. Audit parent trước/sau11khóa; release lock mới.
Không ghi đè XML RED/GREEN/coverage lịch sử, không sửa file frozen để qua kiểm.

Documents skill dùng cho đọc mẫu A06 và chuẩn bị handoff Word. Workspace dependency
loader/bundled renderer không có trong tool hiện hành; Phase34 chỉ trích XML read-only,
không author hoặc giao DOCX. Render/distillation đầy đủ của Phase35 chưa được chứng nhận.
Không cài env/package/system office để giả vượt gate này. Article-writing/brand-voice
dùng giọng học thuật trực tiếp của12 đoạn A06: ví dụ → cơ chế → kết quả → giới hạn;
không vay mượn môi trường hoặc số đo A06 làm kết quả V3.
