# Bàn giao AG02 từ Phase 9 sang Phase 10

Đọc `AG02_EXECUTION_PLAN.md`,checkpoint và `report/active_candidate.json` trước
khi tiếp tục. Phase9 chỉ đưa ra candidate đã kiểm; chưa phát hành bản nộp cuối.

## Đường dẫn hiện hành

- DOCX/PDF: `report/build/candidate-r3/agent02_D23CTPM01_TrieuTuanAnh.*`.
- Render gốc và28PNG:`report/qa/phase09/r3/`;structure.json và
  `evidence/phase09/visual_review_r3.json` ghihash từngpage.
- Notebook:`notebooks/AG02_Code_and_Results.ipynb`,44 codecell đã chạy.
- ZIP:`output/AG02_Source_and_Notebook_r1.zip`;255payloadfiles,không fullrawarchive.
- Metadata đã đượcuser xác nhận:`evidence/phase09/submission_metadata.json`.
  Nộpcánhân,TriệuTuấnAnh/B23DCCN053/D23CTPM01;filenameđãchốt. Không hỏi lại
  những thông tin này trừ khi user đổi;không ghi đè sidecar Phase8đãkhóa.
- Content vẫn làmanuscriptPhase8v1/matrixr2,`report/active_report.json`giữcontent
  pointer;`active_candidate.json` lànavigationmutablechọncandidatePhase9.

## Bất biến

Không sửa/format filetrong `evidence/phase09/experiment_lock.json`;cầnrevision
mới nếu thay builder,notebook,guide,DOCX/PDF,QA hoặccodehelper đãkhóa. Giữr1/r2,
testattempts và mọi evidencePhase1–8. Không rerender ghiđèPNG củar3. Nếu sửa
presentation,buildcandidate-r4,QAphase10/r4 vàgiữ nội dung cũ. Sửa khoa học phải
cócontentrevision,không sửa outputđãđo đểkhớp luậnđiểm. Không train/final lại.

245test/0skip/coverage98,8889%chỉpublicationhelper;không ghiđèfinal_tests_r3.xml,
final_coverage_r3.json. AuditorPhase9 chỉhash/AST/notebookoutputs/QA/ZIP,saveddata;
khôngtrainhoặcforward. Kiểm chỉđọc bằng runtime codeUbuntu/tuananh:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase09
```

Không thêm`--seal`. Sourcebundle đãchạyRunAlltừbản giải nén màkhôngprojectimport,
không coi ZIPlàfullworkspaceđểchạy lại mọiscientificauditor. Đọcguide reproduction.

## Việc Phase 10 còn phải làm

Kiểm R01–R16/U01–U02 vớiđề,10câu,phép tính/citation/mẫusố/phạmvi kếtluận;đốichiếu
28trangvàđủcaption,hình,code. Cóthểkiểm Wordreadonlybằnghelpercũ nếu cần nhưng
khônggắn/tắtWord đang mởcủauser. Mọicandidate sửa phải render vàxem lại đủtrang.
ChốtPDF/DOCXcuối vàhash/bytes/pagecount,release manifest/hướngdẫnnộp;khôngtựsubmit.
Không bootstrap/doctor,pip install,đổidependency hoặcchạyTEST V3/bàicũ.
