# Vận hành/bàn giao Phase31 — hệ đa tác tử xác định

Runtime: WSL distro **Ubuntu**, user tuananh, Python3.11.17/venv Torch đã khóa.
Wrapper bắt buộc `-Distribution Ubuntu`. Không dùng Python Windows, không doctor/
bootstrap cũ, không nâng package hoặc chạy thêm training/TEST các chương trước.

## Demo cục bộ

```powershell
.\scripts\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase31 -ModuleArguments @('--domain','diabetes')
.\scripts\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase31 -ModuleArguments @('--domain','house')
.\scripts\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase31 -ModuleArguments @('--domain','gold')
```

Ba lệnh chỉ dùng record numeric000 từ parent TRAIN. Trả A0/A1/A2, values, citation và
trace; serving NumPy CPU, không native framework GPU hoặc LLM. Không API key, network,
paid service. So câu hỏi tùy chọn phải chứa một `record=<domain>_numeric_000` hoặc
`record=<domain>_evidence_000` đã có trong catalog; ID000–039 numeric,000–019 evidence.
Không truyền bệnh án/secret. Không có record → unsupported; sai miền/ID/trường lạ →
từ chối/lỗi rõ. Đây là demo ID-bound, không chatbot hiểu ngôn ngữ tổng quát.

MedQuAD exact chunk lookup, không gọi BM25/LSA hoặc evaluator QA cũ. Evidence text
không có quyền gọi tool/policy. CDC probability không chẩn đoán; Ames USD lịch sử
khác BIS chỉ số danh nghĩa2010=100; Gold không là giá trực tiếp/khuyến nghị đầu tư.

## Notebook

`experiments/notebooks/v3/ch06_multi_agent/` có3 notebook,9 variant slot đã chạy bằng
code generator-owned qua subprocess. Chọn kernel WSL ai-v3-torch. Không gọi trực tiếp
fork executor trong thread Jupyter/web. Notebook demo không mở agent TEST hoặc đánh giá
model TEST. Chưa kiểm Jupyter UI/kernel picker; receipt nói đúng phạm vi code smoke.

## Task benchmark đã khóa — không chạy lại

- Active `taskset_v2.json`, `input_views_v2.json`, `results_v2/`. V1/results/ là lịch sử
  development, không cộng vào900 kết quả nghiệm thu. Không xóa/ghi đè bằng chứng cũ.
-300 task/3 miền, mỗi miền100;60/20/20 nhóm template/source. Policy intents nguyên nhóm,
  window Gold có thể chồng context; parent TRAIN không là predictor holdout mới.
-720 result TRAIN/dev và180 result TEST tác tử. `agent_test.claimed.json` có count1;
  không gọi lại `scripts.phase31_benchmark --stage test`, reset claim, tuning bằng TEST,
  sửa task/gold/source hoặc build lại parent TEST cache.
- Declaration SHA-256 **b05d6003eabe626caa75bccc269805ac1e3c6ede94f70e8b86863cfe8271619a**.
  Source16 file (xem declaration thực), protocol/unit XML/coverage/input refs đã pin.
  Không sửa/format source/evaluator/auditor/tests trong declaration sau TEST.
- Rubric: đúng status; answer đúng tool numeric/text/citation. Numeric rtol1e-6,
  atol1e-8. Không dùng correctness của verifier như gold. Fault injection có4 loại,
  cùng fault cho3 variant, tách challenge khỏi benign. Không có sample dùng null+n0.
- Timeout: process local terminate/join,15s/task, retry1 chỉ transient, max8call;
  thực tế core≤2 attempt/tool. Không có quyền shell/URL/path động từ câu hỏi.

## Kiểm chỉ đọc sau phát hành

```powershell
.\scripts\check_phase31.ps1 -Distribution Ubuntu
```

Wrapper chỉ hash tất cả member của experiment_lock; không model construction/forward,
không gọi benchmark, coverage writer hoặc producer. Nếu cần so900 output bằng rubric:
`scripts.verify_phase31 --stage audit` chỉ đọc saved output, nhưng không ghi đè bằng
chứng nghiệm thu đã khóa. Không nhầm `--stage release` lịch sử trong frozen auditor
với packager hiện hành `scripts.release_phase31` (release-only reference closure).

Packager mới giữ frozen evaluator/auditor byte/hash, bổ sung closure của mọi report
reference và bibliography vào cùng lock; không sửa metric, status hoặc rubric. Sau
release mọi source/report/ảnh/XML/coverage/member bất biến; sửa cần revision có phiên bản.
`checkpoint.json` COMPLETE chỉ sau audit+lock+verify thực. Không resume session/PID cũ.

## Bàn giao API/UI và báo cáo

- `catalog.json`:3 tab descriptor, overlay vào catalog đã khóa, không sửa `data/catalog_v3.json`.
- `function_contracts.json`:9 contract, hợp hàm/giải thích từng hàm; non-neural extension
  `phase31.agent_pipeline.1`, layers/parameter_count=null; không gọi9 cấu hình là9 mạng train.
- Request `api#agent_task` và trace `agent` dùng schema3.0.0. Adapter local nhận request
  chuẩn và trả3 output; HTTP/job store/worker/CORS/Render vẫn Phase32, React trace Phase33.
- Executor chỉ driver single-threaded WSL; API cần worker process riêng, không fork từ
  gunicorn threaded handler. Giữ hard15s, rate/queue/artifact budget khi tích hợp.
- Loader API tương lai phải pin catalog/registry ngay startup; không cho client sửa refs,
  upload pickle hoặc fault injection. Fault chỉ harness nội bộ, không public request.
- Parent RSS là high-water process gồm preload; child RSS chứa shared copy-on-write,
  không PSS/private unique RAM. Không cộng parent+max child làm peak đồng thời; cold load
  ghi riêng. Latency benchmark không gồm cold catalog và không là HTTP/cloud SLA.
- Active manuscript `report/sections/v3/ch06_multi_agent_r2.md`, chọn qua `active_report_r2.json`;
  root `active_report.json`/`report_generation.json` giữ r1 lịch sử.5 hình PNG300dpi/SVG đã xem,
 3 data card/5 mẫu mỗi miền. Tham khảo mới ở `report/references/ch06_sources_v3.bib`;
  Phase34 ghép bibliography/active pointer và outline locked target alias, không ghi V2.
- DOCX6 chương build/render vẫn Phase34–35. Không tự bắt đầu32 khi người dùng chưa yêu cầu.

Presentation r2 chỉ ghi rõ router/reporter duration0 là default chưa instrument, không
phải số đo0ms; latency tổng wall-time vẫn giữ nguyên. Figure trace mới và manuscript r2
giữ r1/metric/output byte/hash. Không cộng duration node để suy tổng request time.
