# AG02 Phase 8 — bản thảo đủ10câu và bằng chứng

Ngày24/10/2026. Sản phẩm là bản thảo nội dung hoàn chỉnh ở
`report/phase08/manuscript.md`, chưa phải PDF/DOCX đã dựng. Phase9–10 tiếp nhận
để làm notebook/tài liệu và kiểm toàn bộ trang. Phase8 không train hoặc thêm
final claim;56market run/61learner instance và mọi score cũ được giữ nguyên.

## Nội dung đã viết

Đủ9phần theo đề: thông tin bìa đã biết; mở đầu/mục tiêu; môi trường và agents;
thiết lập/code; kết quả;10câu trả lời; thảo luận/giới hạn/cải tiến; kết luận; nguồn.
Bản thảo có12bảng sinh từ artifact,20hình gốc kèm giải thích,8codeexcerpt đúng
source/rangeline/hash. Wordcount tách theo khoảng trắng8.047 ở bản nghiệm thu;
đây không phải số từ ngôn ngữ học hoặc pagecount. Số trang chỉ đo sau render.

Lý thuyết được gói trong phần nền và những câu cần dùng. Không thêm dẫn xuất
Bellman/gradient/DQN hoặc chươngLLM/MAS. Giữ Q-update và5bước tính4,65; margin5/3;
meanreward đúng mẫu số. Q3 được ghi là ví dụ giả định từ đề, không empirical score.
Ví dụ nhà/tiểu đường chỉ giúp so policyrule/RL trong tác vụ phù hợp, không biến
bảng nhãn cũ thành môi trường RL điều trị/giao dịch.

Các kết quả bất lợi vẫn báo đủ: Qcore không vượt rulecontrol về mean;retrain chưa
cải thiện hai kernel;state320Q chưa vượt matchedbaseline/rule trên3kernel. Không
coi std nhỏ hơn làrobust hơn khi mứcprofit thấp;không chọnseed/checkpoint hoặc
tune saufinal. Within-matchdelta táchpolicyqualitydelta,REFnative táchCONTROLLEDn5,
pairQ8 làreplicate,chứ không10learner độc lập. Gold làproxy demand từprefixTRAIN,
oracleknown-model táchlearner model-free vàγ1profit/bướctáchγ0,9discountedtotal.

## Truy vết và biên tập

`report/question_evidence_matrix.md` và `report/phase08/question_evidence_matrix.json`
đủ10hàng,mỗi hàng cóđịnhvị câu,claim,codeAST/range,bảng,hình,nguồn vàartifact.
Compiler đọc70fileinput cóhash;88numeric token được đưa vào văn,các bảng lưugiátrị
gốc/field/filter/operation trong numeric_claims.json và tables.json. Code8đoạn có
fullsourceSHA/excerptSHA trongcode_excerpt_index.json,khôngreformatcodefrozen.

Codecompiler không import runner thí nghiệm. Tests kiểm sốhữu hạn,format số,
sourceexact,terminal,cấu trúc9phần/10câu/20hình,placeholdervàgiữID họcthuật/student.
Trongbiên tập đãgiữ B23DCCN053/D23CTPM01,arXiv:2501.06322v1 vàDOI nguyênvẹn;
không để xửlý khoảngtrắng tách sai mã. S2được trích đúngtên tài liệu cungcấp.

PixelQA của20PNG từPhase3–7 được kiểm lạihash vàreuse. Phase8 review cả20caption
vềtrục/đơnvị,legend,n/aggregation,quan sátđịnhlượng,đốichứng vàgiới hạn. F03/F10
được mở lại đểđốichiếu nghĩa. Không tuyên bốđã render/xem trangDOCX/PDF.

Nhận xét REF trong bảnthảocũ đãkhớpQ-table: state(0,1)/(1,1)chọn1,CONTROLLED11
chọn0ở4state. Một commentary banđầu đãnhậnđịnhnhầm vềbảnthảocũ;đãđínhchínhsau
đọcđủnguồn. Không sửa source/ảnh/metric hoặc tạo “sửa lỗi số liệu” không có thật.
F10bản mới ghi trực tiếp paneltrái làdelta soQbaseline,panelphải làdelta trongtrận,
giúp tránh hiểu nhầm từ cách diễnđạt rútgọn. Sốđo cũ không đổi.

## Kiểm tra và giới hạn nghiệm thu

234test/0skip PASS. Coveragecombined96,7213% chỉhelperreport_assets;statement97,6744%,
branch94,4444%. Không gọi đó làcoverage vănxuôi/compiler/auditor/scientificcode
hoặc toànproject. Evidence active final_tests_r2.xml/final_coverage_r2.json;giữ
các attempt cũ. Ruff vàCLIhelp đạt. Các kiểm tra số học đọc savedCSV:rawcumulative
baseline/mean,std5seed,pairedvalues,kernelLaplace vàphép tính bắtbuộc;khôngforward.

Khóa cũPhase1–7,source thầy/7parentasset được kiểmhash sau biênsoạn. Contentreview
vàrelease/verification ởevidence/phase08/. Sửa content đãkhóa cầnrevisiongiữbảncũ;
compiler khi córelease chỉkiểm/reuse,khôngghiđè. report/active_report.json là
navigationmutable trỏnội dungđãnghiệmthu,khôngthaythếkhóa.

Metadata cá nhân/nhóm vàteam_name chofilename PDF vẫn làhànhchính cầnxácnhận trước
phát hànhcuối,khôngchặnviếtnội dung. Bảnthảo dùngthông tin sinhviên đãbiết,không
bịa tênnhóm/giảngviên. Phần màuđen/bảngnative/codelayout sẽkiểm thật khiPhase9build.

Tiếp theo **làm AG02 phase9** khiđượcyêucầu: đọcmanifestinput,cácràngbuộc nguồn,
làmnotebookread-only,buildDOCX/PDFứngviên,renderđểPhase10nghiệmthu. Không tự
nộpbài/commit/push/deploy hoặctrain/evaluate lại đểghép báo cáo.
