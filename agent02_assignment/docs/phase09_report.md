# AG02 Phase 9 — notebook và bản tài liệu ứng viên

Ngày 24/10/2026. Notebook và ứng viên DOCX/PDF đã hoàn tất, chưa phát hành bản nộp
cuối. Phạm vi chỉ Agent02. Không train, cập nhật Q hoặc thêm scientific final claim.
Đầu vào khoa học của Phase3–7, bản thảo Phase8 và các bài khác giữ nguyên.

## Sản phẩm

- `notebooks/AG02_Code_and_Results.ipynb`:108 cell,44 code cell đã thực thi;12 bảng
  kết quả,8 đoạn code exact-source,20 ảnh output kèm phần giải thích từ Phase8 và
  phần trả lời đủ10câu. Run All chỉ đọc/kiểm hash/hiển thị,không chạy model. Phép
  tính Q=4,65 vàmargin5/3 là ví dụ giả định được ghi rõ.
- `report/build/candidate-r3/agent02_D23CTPM01_TrieuTuanAnh.docx` và PDF cùng tên:
  28 trang A4,14 bảng Word native (12 bảng dữ liệu,2 bảng mô tả),20 hình,8 source
  excerpt giữ nguyên text. Body Times New Roman12,5pt;code Consolas9pt có wrap
  thị giác;references11,5pt. Chữ và field đều đen,ảnh grayscale. DOCX sửa được.
- `output/AG02_Source_and_Notebook_r1.zip`:255 file payload,15.746.858byte ZIP,
  23.987.843byte payload chưa nén;CRC vàhash từng file PASS. Kèm manifest và
  hướng dẫn. Không đóng gói runtime hay hàng GBtrajectory/checkpoint trung gian.
  Full scientific audit cần workspace gốc;ZIP đủ input đểRunAllnotebook.
- `docs/phase09_reproduction.md`:lệnh,cây thư mục,dependency và giới hạn tái lập.

Chủ bài xác nhận nộp cá nhân,Triệu Tuấn Anh/B23DCCN053/D23CTPM01 và filename
`agent02_D23CTPM01_TrieuTuanAnh.pdf`. Bản xác nhận ởevidence Phase9;metadata
Phase8 đã khóa vẫn giữ nguyên. Không tự suy tên nhóm/giảng viên hoặc nộp bài.

## Bố cục và kiểm tra

R1 có30trang. R2 có29trang sau giữ bảng/code/giải thích hình liền khối và bỏ một
số ngắt trang cứng. R3 có28trang,đưa references về1trang và xửlý đúng italic thay
vì đểdấu Markdown. Giữứngviên/QA r1–r2 làm lịch sử,không dùng làm bản hiện hành.
Nội dung khoa học,ảnh vàsource excerpt không bị sửa đểđạt bố cục. Kết luận ngắn
ởtrang27 cókhoảngtrắng hợp lý;không thêm lý thuyết chỉ đểlấp trang.

Đã mở và xem riêng tất cả28PNG r3 ởđộ phân giải gốc125dpi:không clipping/overlap,
không missingglyph,nhãn vàlegend đọc được,bảng không mất dòng. Kiểm PDF thực có
20image placement và10heading câu hỏi;không dùng resource list dùng chung đểđếm
ảnh mỗi trang. Textcolor PDF=0/DOCX=000000;RGB mọi page đều grayscale. So sánh
8 đoạn code với paragraphtext DOCX exact PASS,kểcảterminal. Đây là QA ứngviên;
Phase10 vẫn kiểm rubric/toàn bộtrang và phát hành đúng bản cuối. Word phiên bản
khác có thể phân trang khác;chưa claim đã kiểm nativeWord.

245test duy nhất/0skip PASS,coverage98,8889% chỉ `code/publication_v1.py`;
statement98,3871%,branch100%. Không phải coverage vănxuôi,builder/renderer/CLI
hoặc toàn project. Lưu final_tests_r3.xml/final_coverage_r3.json. Attempt1 của
helper fail vì test kỳ vọng15bảng,trong khi nguồn thực có14;đãđốichiếu vàsửa test,
không bỏ bảng khỏi manuscript. Ruff phát hiện aliasre.M,đã sửa thànhre.MULTILINE.
Không ghi đè bằng chứng các attempt cũ. Ruff vàCLI checks cuối PASS.

Notebook được chạy thật bằng nbclient/kernel runtime cũ,không dựngoutput giả.
RunAll lần nữa từZIP đãgiảinén,trongcwd notebooks của bản giải nén,44cell PASS;
255payload hash trước/sau không đổi,không import project ngoàiZIP. Nhân Jupyter
được đóng sau chạy;không mở server public hoặc hạ secure_write. Runtimecode và
toolchain tài liệu riêng cósẵn được reuse,không cài/sửaGPUenv. Các marker docx/pdf
đã chạy trước lần tạo đầu. Renderer lookup sai subpath ởlần đầu thất bại trước
render,r1 dùng vendor cũ; r2–r3 dùng render_docx.py ởroot skill hiện hành. Không
coi lỗi đườngdẫn làdependency thiếu; khôngcài thêm phầnmềm. Chi tiết ởtoolchain.json.

Parent Phase8 audit trước/sau PASS:101phép đối chiếu số học,7.501protectedfiles/
7parentasset giữhash. Originalmanuscript/matrixr2/code/metric/Q khôngđổi.
Seal ởevidence/phase09/. Không tựchạyPhase10,nộpLMS,email,commit,push hoặcdeploy.
