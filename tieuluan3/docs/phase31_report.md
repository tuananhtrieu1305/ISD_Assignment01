# Biên bản Phase31 — Hệ đa tác tử và benchmark ba miền

Ngày thực hiện:20/10/2026 (Asia/Bangkok). Chỉ COMPLETE khi checkpoint/experiment_lock
và verify-lock PASS; đây là biên bản nội dung nghiệm thu, không thay trạng thái runtime.

## Phạm vi đã thực hiện

Core offline nhiều vai trò: A0 direct, A1 router/specialist, A2 thêm verifier/reporter;
3 specialist theo miền diabetes/house/gold, state/trace tách theo task, dùng skeleton
chung và tool khác nhau. Không LLM/API key/network; không tự chủ mở/thương lượng hay học
phối hợp. Model tool là scratch seed42 đã khóa: CDC/Ames MLP và Gold LSTM, serving
NumPy CPU. Evidence là MedQuAD exact chunk lookup/BIS và Gold observation lookup.
Không tái tạo RAG/QA TEST hoặc biến lookup theo ID thành benchmark hiểu ngôn ngữ tự do.

Ba task view mới100 câu/miền,300 tổng. Mỗi miền60/20/20 theo template/source groups;
5 category ×20task, mỗi group4 câu.40 numeric canonical input +20 evidence record/miền,
180record tổng; không clone raw. Câu hỏi/challenge là synthetic-template; số/evidence/
checkpoint từ parent thật. Window TRAIN Gold có thể chồng context; numeric parity không
predictive accuracy. MedQuAD corpus không có QA split metadata, không đọc nhãn TEST cũ.

V1 giữ trong taskset.json/results/ như lịch sử. V2 khắc phục group unsafe theo ý định
gốc và path trace apps/ bằng preservation-index indirection; taskset_v2/results_v2 active.
Tất cả sửa phát triển trước declaration/TEST; không tuning bằng TEST tác tử.

## Bằng chứng định lượng

- Declaration SHA **b05d6003eabe626caa75bccc269805ac1e3c6ede94f70e8b86863cfe8271619a**,
  trước TEST. Task set SHA **8741c1165c77fe8d67ba262a193ddebdd044b45eebf3a8bc0318255123ee23ab**,
  401.318byte dùng chung3 miền. Source và rubric pin, không sửa sau declaration.
-720 result TRAIN/dev;180 TEST tác tử (60 task ×3variant), batch count1;900 unique pair.
  Auditor kiểm trace schema/DAG/input-output hash, matrix đầy đủ và tái tính metric từ saved
  output. Không gọi model/evaluator trong audit; không thêm batch TEST các chương trước.
- TEST mỗi miền: A0/A1 task_success18/20=90%;A2 20/20=100%. Benign8/8 ở cả9ô miền/variant.
  Đây là ID-bound đơn giản, không tuyên bố100% hiểu ngôn ngữ hoặc đúng chuyên môn.
- Challenge12task/miền: A0/A1 10/12,A2 12/12. Lợi ích chỉ ở2 ca tamper numeric/citation;
  A2 abstain đúng rubric, không tạo đáp án thay thế. Answer completion toàn TEST A0/A1
 11/20=55%,A2 9/20=45%; cần đọc cùng correctness, không coi nhiều output luôn tốt hơn.
- Unsupported claim challenge: A0/A1 2/12=16,67%,A2 0/12; unsafe cases đều được từ chối
  bởi chính sách chung. Rule hữu hạn, không chứng nhận an toàn với mọi biểu đạt/attack.
  Receipt chỉ bảo vệ trusted tool channel; worker sửa cả payload+receipt ngoài threat model.
- p50/p95 toàn TEST (ms): diabetes A0 7,72/23,84;A1 10,20/18,76;A2 9,17/16,92;
  house A0 6,61/9,87;A1 7,23/13,80;A2 7,98/12,42;
  gold A0 10,70/16,61;A1 9,50/18,12;A2 8,66/19,47.
  Một lượt/task, gồm mix từ chối và tool, không kết luận A2 luôn nhanh hơn/chậm hơn.
- Cold catalog TEST459,57ms, parent high-water222.760.960byte. Child RSS riêng từng run,
  gồm shared fork pages; không cộng thành peak đồng thời/private memory hay Render budget.

## Test, trình bày và bảo toàn

80 pretest/0skip; coverage dòng+nhánh **91,5294117647%** (đọc totals artifact để dùng
giá trị chính xác), namespace core301statement.263 regression/0skip, giữ4 warning sklearn
preprocessorV2 1.9.1/runtime1.9.0.6 report aggregate test;3 packaging test riêng. Tổng
nghiệm thu352 unique testcase đã PASS, không cộng XML RED/development cũ.
Không cài/nâng dependency hoặc chạy Windows Python; runtime Ubuntu/user tuananh giữ nguyên.

29.004 protected file trong8 khóa22/24/25/26/27/28/29/30 đã kiểm trước phát triển;
final release kiểm lại toàn bộ. Raw Ch5/V2/config/metric/prediction/seal cũ giữ hash,
Ch5 count1; Power failed seal/null telemetry Phase29 không đổi. Không train hoặc TEST
lại Ch2–5; không commit/reset/cleanup hay xóa source/dataset/môi trường người dùng.

Bản thảo Ch6 dễ hiểu, một hợp hàm tối thiểu có giải thích;9 function contract cho3miền
×3variant, layers/parameters null;3 data card đủ link/bytes/sample/distribution/comment;
2 CSV metric/5 PNG300dpi+SVG đã xem;3 notebook thực thi9slot CPU TRAIN-only. Notebook
generator-owned subprocess smoke, không tuyên bố Jupyter UI đã kiểm. HTTP/React32–33,
DOCX34–35 chưa làm. Deploy chỉ mục6.7 ngắn cuối chương.

## Đường dẫn bàn giao

- Source: `src/ch06_multi_agent/`; benchmark `scripts/phase31_benchmark.py` frozen.
- Frozen auditor `scripts/verify_phase31.py`; release-only packager
  `scripts/release_phase31.py` thêm closure report/bibliography, không sửa evaluator.
- Manifest active: `artifacts/manifests/phase31/`; metric `artifacts/metrics/phase31/`.
- Manuscript: `report/sections/v3/ch06_multi_agent_r2.md`; chọn qua `active_report_r2.json`.
  R1/manuscript/figure giữ nguyên; r2 chỉ giải thích node timing0 chưa instrument và
  trình bày kết quả containment90%/100%. Không đổi metric, trace hoặc template sau TEST.
- Vận hành và điều kiện worker/API: `docs/phase31_operations.md`.
- Kiểm chỉ đọc: `scripts/check_phase31.ps1 -Distribution Ubuntu`.

Phase tiếp theo32 chỉ khi được yêu cầu. Không gọi core local là HTTP/React/Render live.
