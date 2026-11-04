# Vận hành/bàn giao Phase30 KG–RAG

Runtime hiện hành: WSL distro **Ubuntu**, user tuananh, Python3.11.17 tại
`/home/tuananh/.local/share/ai-term-paper-v3/`. Dùng wrapper với `-Distribution Ubuntu`.
Không chạy doctor/bootstrap cũ hoặc sửa metadata Phase21; không dùng Python Windows,
venv tạm, đổi dependency/backend hay rebuild bundle để phục vụ migration này.

## Kiểm chỉ-đọc sau phát hành

```powershell
.\scripts\check_phase30.ps1 -Distribution Ubuntu
```

Lệnh chỉ so hash khóa Phase30. Không gọi evaluator, fit model, sinh prediction TEST,
ghi XML/coverage hoặc chạy producer vào artifact đã khóa. Root checkpoint/experiment_lock
là trạng thái thật; các XML RED/development dưới Phase30 là lịch sử, không cộng vào test
count cuối. Thay source/report/ảnh/contract sau phát hành cần revision mới giữ bản cũ.

## Chạy demo CPU local

```powershell
.\scripts\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase30 -ModuleArguments @('--dataset','ch5_medquad_diabetes')
.\scripts\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase30 -ModuleArguments @('--dataset','ch5_finqa')
.\scripts\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase30 -ModuleArguments @('--dataset','ch5_wikidata_subgraphs','--qid','Q12206')
```

`-Framework torch` chọn venv công cụ chung; inference KG–RAG thực tế NumPy/CPU,
không import/train PyTorch, TensorFlow hoặc Keras. Câu hỏi tùy chọn truyền bằng
`--question` là string, tối đa500 ký tự sau chuẩn hóa; không truyền đường dẫn, command
hoặc URL để loader tải. Wikidata chỉ nhận10 QID trong snapshot, không nhận URL/filename.
Không đưa bệnh án cá nhân/secret vào demo; nó không phải tư vấn y khoa/tài chính.

Demo B0–B4 tìm trên cùng corpus compact và input, dùng index/rule/trọng số đã khóa.
Graph free-question/anchor compact và corpus không có split metadata khác evaluator
query-ID/candidate-per-split lịch sử; không so demo output như kết quả TEST mới.
Timing cộng component dùng chung và answer, loại cold load/serialize, không phải5
process benchmark độc lập hoặc HTTP p95. Guardrail là finite rule, không chứng nhận an toàn.

Notebook mỏng ở `experiments/notebooks/v3/ch05_knowledge_rag/`. Generator đã chạy code
do chính nó tạo bằng runpy, ghi output vào notebook/receipt. Chưa kiểm Jupyter UI/kernel
picker; khi mở Jupyter phải chọn kernel trong runtime WSL khóa, không kernel Windows.
Chạy notebook chỉ demo, không đánh giá benchmark hoặc gọi mạng.

## Contract và artifact

- `artifacts/manifests/phase30/catalog.json`:3 dataset-tab descriptor để Phase33 dựng UI.
  Hai QA tab MedQuAD/FinQA và một Wikidata structural browser; chưa phải React live.
- `reused_registry.json`:15 slot contract,10 QA available và5 Wikidata unavailable cho QA;
  index fit từ trước, không gọi đây là15 model V3 vừa train. Không thay registry Phase25.
- `contracts/*/*/model_contract.json`:extension non-neural có phiên bản; API request/job/
  chapter/citation vẫn dùng schema V3 gốc. Xem `docs/phase30_contract_extension.md`.
- `runtime_compatibility.json`:4 class BM25/LSA load đúng namespace `term_paper.tools...`,
  actual Python3.11.17/NumPy2.4.6/SciPy1.17.1/sklearn1.9.0. Đây là smoke tương thích thực tế,
  không khẳng định tất cả version serialization cũ đều bằng runtime mới.
- `active_report.json`:chọn manuscript **`report/sections/v3/ch05_knowledge_rag_r2.md`**.
  R1 và manuscript/hình cũ vẫn nguyên byte; presentation r2 chỉ sửa font/layout/scope.

Manifest runtime cứng SHA8b58e70d... trỏ sáu file68.393.687 byte; loader kiểm role/path/
size/hash/budget trước khi deserialize bốn joblib allowlist. Không nhận uploaded pickle,
không reserialize index cũ hoặc bỏ hash guard để vượt lỗi. Constructor không đọc bundle;
runtime không sẵn sàng trả5 slot unavailable, không lộ filesystem path trong job.
Citation V3 ghi source_sha256 của local chunk container và locator chunk/document ID;
URL là nguồn cấp dataset. Không ngụ ý đã phục hồi raw URL/locator từng chunk bị lược đi.

## Những phần không được chạy lại

Public TEST Phase15 run_count1 và10 prediction file,7config/23metric/raw Ch5 giữ nguyên.
Không chạy `build_phase15_experiments.py` hoặc các build/verify lịch sử bằng đường dẫn cũ.
Mọi phân tích mới chỉ đọc saved outputs; không tuning bằng TEST. Snapshot raw cache14 file
FinQA là dữ liệu upstream, không dọn. Phase26–29 source/model/TEST cũng không được chỉnh.

RSS419MiB là high-water của **toàn exporter** có matplotlib, không peak riêng request hoặc
cam kết vừa tier cloud. Chưa smoke Render/HTTP/React V3 trong Phase30; xử lý budget/lazy load/
health/API32 và UI33 riêng. DOCX vẫn34–35. Tiếp theo Phase31 chỉ khi người dùng yêu cầu.
