# Vận hành và bàn giao AG02 Phase 8

Content source hiện hành: `report/phase08/source_template.md`, compiler
`compile_phase08.py`. Bản ghép: `report/phase08/manuscript.md`, đủ9phần/10câu,
12bảng/20hình/8codeexcerpt. Không build DOCX/PDF hoặc chạy notebook ởPhase8.

Từ root repo, kiểm chỉ đọc trong runtime Ubuntu/user tuananh đã khóa:

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Distribution Ubuntu -Module agent02_assignment.verify_phase08
```

Auditor kiểm hash đầu vào/khóaPhase1–7, tái dựng nội dung từ source-bound tokens,
đối chiếu codeAST/range/hash, question matrix,citation,20caption và phép tính từ
savedCSV. Không import runner để train/forward; không mở TEST hoặc tạo lại policy.
Nó đọc nhiều checkpoint qua DrvFS để bảo toàn nguồn nên có thể chậm. Một writer
dùng chung flockPhase3; không chạy pipeline thứhai hoặc coverage vào file đã khóa.

## Các file phục vụ Phase 9

- `manuscript.md`: nội dung hoàn chỉnh, không có token chưa điền. Heading9phần
  theo đề, mục6 có10câu theo thứtự. Hình liên kết tới PNG đã khóa, không copy/tô màu lại.
- `question_evidence_matrix.json` và `report/question_evidence_matrix.md`:10câu,
  locatorcode thật, table/figure IDs, nguồn và artifact. Không gọi dữ liệu schema
  ví dụ hoặc phép tính giả định là kết quả đo.
- `numeric_claims.json`,`tables.json`,`input_index.json`: số gốc,filter/field/
  operation,mẫu số,hash và bảng. Mean/std được đối chiếu savedseedrows,khôngforward.
- `code_excerpt_index.json`:8đoạn exactsource,rangeline,fullsourceSHA/excerptSHA.
  Code trong bản thảo phải giữ terminal branch;không reformat nguồn frozen đểchènWord.
- `figure_catalog.json`:20PNG/hash,caption mới,originalnotes. PixelQA từPhase3–7
  được reuse;Phase8review ýnghĩa/trục/đơnvị/n/quan sát/giới hạn.Cần xem mọi trang
  sau render ởPhase9–10,không coi caption audit là DOCX/PDF visualQA.
- `calculation_checks.json`:Q3=4,65/margin5và3;baseline rawcumulative totals/means,
  std5seed,pairedvalues,kernelGold. Toàn bộ từsavedoutput hoặc số giả định đề.
- `submission_metadata.json`:knownstudent/class,administrative metadata còn cần
  xác nhận trướcfilename PDF cuối. Không bịa team/instructor để lấp cover.

Sau release, compiler chỉ kiểm khóa và reuse, không ghi đè content. Nếu Phase9 cần
sửa chữ/số/caption phải tạo revision/version mới giữ nội dung Phase8/hash cũ. Tách
sửa presentation Word khỏi source scientific; không sửa bảng/Q/prediction đểqua QA.
`report/active_report.json` là navigation mutable ngoài khóa, trỏ content đã nghiệm thu.

## Các ranh giới cần giữ khi dựng tài liệu

REF/native táchCONTROLLED n5. Gộp role trướcstd5trainingseed;Q8gộp learner trongpair
trước5pairseed. Rule n5 làscenario panel. 60reference Phase7 reuse không thành
60forward mới. Giữ cả scorebấtlợi củaretrain/state320Q vàkhôngclaimrobusthơn từstd nhỏ.
Within-matchdelta khácpolicyqualitydelta;F10trái/phải đã ghi rõ. Q3làhypothetical,
Q-valuekhôngprofit/bước;oracleknown-modeltáchmodel-free vàγ1profit/bướctáchγ0,9total.
Gold chỉprefixTRAIN1960–08/2006,proxy demand từhướnggiá,không demand/investment thật.

Lý thuyết ngắn,đủý,dễhiểu. Giữ Q-update,phép tính bắtbuộc,margin vàmean reward;
không thêm dẫnxuấtBellman/gradient hoặc chươngLLM/MAS riêng. ChữDOCXđen,codeđen,
bảngnative,ảnhgrayscale khiPhase9build. Không dùng màu hyperlink mặc định nếu vi phạm
yêu cầu chữđen. NotebookRunAll đọc savedoutput,không train56run hoặc đánhgiá lại261claim.
Không tự nộp bài/commit/push/deploy. Tiếp **làm AG02 phase9** chỉ khi được yêu cầu.
