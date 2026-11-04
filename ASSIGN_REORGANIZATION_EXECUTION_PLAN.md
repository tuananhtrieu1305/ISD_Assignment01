# Kế hoạch gom các assignment và tiểu luận — 3 phase

Ngày lập: 30/10/2026. Workspace: `C:\DATA\assign`.
Trạng thái: Phase1–3 COMPLETE. 11bài/33folder,11web local/build/E2E và cleanup đã nghiệm thu; chưa commit/push/deploy.

## 1. Mục tiêu và cách nhận lệnh

Đây là kế hoạch đang hoạt động cho việc sắp xếp repository theo yêu cầu mới của người dùng.
Lệnh **`làm phase 1`**, **`làm phase 2`**, **`làm phase 3`** lần lượt thực hiện các phase trong file này.
Có thể dùng `làm REORG phase N` để chỉ rõ ngữ cảnh. `làm tiếp task đang dở` tiếp tục phase
IN_PROGRESS trong `docs/reorganization/checkpoint.json`, không tự chạy phase sau.

Trước mỗi lượt: đọc toàn bộ file này, AGENTS liên quan, checkpoint, nhật ký và Git status;
kiểm tra process thật, dependency và đầu ra đã có. Phase đã COMPLETE chỉ kiểm tra và báo kết quả,
không tự làm lại. Nếu phase sau thiếu dependency, hoàn tất dependency cần thiết trong kế hoạch,
ghi rõ trong nhật ký; không đoán rằng phase trước đã xong. Chỉ đánh dấu COMPLETE khi đạt nghiệm thu.
Lưu checkpoint khi bị ngắt: việc đã xong, file đã đổi, lỗi, process còn sống và bước tiếp theo.

Kế hoạch V3 phase20–35 và AG02 phase0–10 giữ vai trò lịch sử/bằng chứng. Lệnh có tiền tố
`AG02` vẫn thuộc kế hoạch AG02; không nhầm với phase1–3 sắp xếp source này.

## 2. Cấu trúc đích

```text
assign/
├── A01/                 # Assignment01
├── A02/                 # Assignment02
├── A03/                 # Assignment03
├── A04/                 # Assignment04
├── A05/                 # Assignment05 – CNN
├── A06/                 # Assignment06 – RNN
├── tieuluan1/           # Khôi phục bản tiểu luận1 từ Git
├── tieuluan2/           # Dẫn xuất từ tiểu luận3, bỏ chương hệ đa agent
├── tieuluan3/           # Tiểu luận6 chương hiện tại
├── agent01/             # discovering_ai_agent hiện tại
├── agent02/             # agent02_assignment hiện tại
├── docs/reorganization/ # Bản đồ nguồn, checkpoint, bằng chứng migration
├── scripts/             # Lệnh quản lý/chạy/kiểm tra chung cần thiết
├── _shared/             # Chỉ tài nguyên thực sự dùng chung, nếu cần
└── ...                 # Git, cấu hình và file điều phối ở root
```

Mỗi bài đều có ba thư mục **thật**, dễ tìm:

```text
<bai>/
├── datasets/            # Dataset hoặc catalog + resolver có thể mở/materialize
├── notebooks/           # Notebook chính, phân biệt train và xem kết quả
├── web/                 # Demo riêng của bài
├── src/                 # Khi notebook/web cần Python module
├── artifacts/           # Checkpoint, metrics, predictions, figures cần giữ
├── report/              # Báo cáo và tài liệu đầu ra đã có
├── tests/               # Kiểm tra phù hợp
├── provenance/          # Commit gốc, manifest và thay đổi tương thích
└── README.md            # Đường dẫn dataset, kernel, chạy notebook/web
```

Thư mục phụ có thể khác nhau giữa các bài. Root không còn các source hoạt động rải rác hoặc
hai tên agent cũ sau nghiệm thu; các đường dẫn tương thích bắt buộc phải được kê khai, không
giữ hai bản source hoạt động độc lập. Không gom mất danh tính từng bài vào một notebook chung.

Web A01–A06/agent01/agent02: HTML/CSS/JS đơn giản theo demo mê cung hiện có, ưu tiên chạy local
bằng static server, ít phụ thuộc; hiển thị dữ liệu mẫu, mô hình/phương pháp, kết quả thật và giải
thích biểu đồ. Tiểu luận1–3 giữ UI demo tổng hợp theo chương của đúng phiên bản, cùng backend
Python cần thiết. Không biến các web tiểu luận thành trang tĩnh chỉ có ảnh/kết quả.

## 3. Khảo sát đã làm để lập kế hoạch

Git local có đủ 13 commit từ `38b445e08` đến `73305eea7`; không cần tải cả repository khác
hoặc checkout đè lên cây làm việc. HEAD khi khảo sát: `73305eea7` (`agent01 & agent02`).
Các commit dưới đây là ứng viên đã kiểm cây; Phase1 sẽ khóa SHA đầy đủ và dependency closure.

| Bài đích | Nguồn ưu tiên | Đã thấy trong Git/source |
|---|---|---|
| A01 | Chọn `A01_CT_anhtt.053.ipynb` tại `0c27b1d2f`; giữ bản `be8442eff` làm lịch sử | Bản sau107cell/48code-output, phần feature analysis đầy đủ hơn; model diabetes/house không đổi |
| A02 | `0c27b1d2f` | `A02_CT_anhtt.053.ipynb`, datasets, artifact/backend/web thời điểm đó |
| A03 | `d68985ea4`, đối chiếu `8b3ba0254` | 3 notebook trong `pipeline/`: diabetes, house_price, customer_behavior; commit sau sửa header |
| A04 | `3be831e88` | 5 notebook trong `pipeline04/`: 3 tabular + MNIST/CIFAR-10 |
| A05 | `431f9f3c0` | 5 notebook `A05/notebooks/`: fundamentals, EuroSAT, Oxford Pets, CDC, comparison |
| A06 | `f1ff9c6a1` | 8 notebook `A06/notebooks/`: fundamentals, customer/stock, PyTorch/Keras, comparison |
| tieuluan1 | `e7cf49bce`, đối chiếu `a63bcb623` | Bản `tieu-luan-1` và bản sửa artifact hash portable; có `term_paper/`, backend/web |
| tieuluan2 | Dẫn xuất mới từ tieuluan3 | Chương1–5 của V3; không tuyên bố khôi phục từ commit chưa tồn tại |
| tieuluan3 | Source hiện tại, baseline `a3f4bcf09`/HEAD | `apps/`, `src/`, `experiments/`, `report/`, data/artifact/deploy và bản6 chương |
| agent01 | `discovering_ai_agent/` hiện tại | Notebook, maze NumPy Q-learning, DOCX, kết quả, `web-demo/dist/` |
| agent02 | `agent02_assignment/` hiện tại | Notebook đọc kết quả, simulation source, output/evidence và `web-demo/` |

Các điểm phải xử lý:

- Git status lúc khảo sát có hai thư mục untracked `discovering_ai_agent/web-demo/` và
  `agent02_assignment/web-demo/`. Phải giữ cả file ignored trong chúng; không chỉ sao phần Git tracked.
- `discovering_ai_agent/web-demo/` có `.git` riêng và `.openai`; đây là metadata dự án con,
  không nhập nó thành Git repository/submodule lồng bên trong `agent01/web/`.
  Sao lưu nguyên trạng metadata trước khi gom, chỉ đưa payload web cần thiết vào source chính.
- Riêng cây `A05/` ở commit cũ có53.080file. Phase1 xác minh phần lớn là ảnh/annotation,
  không phát hiện venv trong payload được chọn; giữ ảnh phân loại và nhãn cần thiết, kê riêng
  mask segmentation/XML/AppleDouble không dùng. Không phục hồi toàn bộ repo/venv một cách mù quáng.
- `.gitignore` hiện bỏ qua `**/dist/`, raw và nhiều checkpoint. Payload web agent01 đang ở
  `web-demo/dist/`; phải chuyển source HTML/JS/CSS cần giữ ra `web/` và cập nhật ignore có chọn lọc.
- Web V3 có catalog chương6/family `multi_agent` và route `/agents`. Tiểu luận2 phải loại bỏ
  cả menu, catalog, API/registry/payload phụ thuộc chương6; KG–RAG chương5 vẫn giữ nguyên.
- Render hiện trỏ `apps/web` và `scripts/render_v3.py`, có ZIP API bundle riêng.
  Sau migration phải cập nhật đường dẫn và kiểm bundle/source đồng bộ; không chỉ đổi tên folder.
- Ổ C đo bằng .NET DriveInfo còn khoảng21,42GiB khi khảo sát. Phase1 đo lại và lập budget;
  không lấy giá trị Free=0 của PSDrive trong sandbox làm kết luận dung lượng thật.

## 4. Quy tắc migration chung

1. Đây là phục hồi/sắp xếp và làm demo, không phải dự án train lại. Giữ byte/hash raw,
   notebook/output gốc, checkpoint, metrics, predictions, báo cáo và khóa nghiệm thu.
   Không scientific TEST/claim mới, không tuning, không bịa kết quả hoặc đổi thuật toán để dễ chạy.
2. Git là nguồn lấy file bằng object/commit, không reset, checkout cả cây, cherry-pick hàng loạt,
   rewrite history, commit/push hoặc tự sửa service Render. Không đọc/in giá trị `.env` hay secret.
3. Chọn lọc code + dataset + artifact cần dùng theo dependency, không mang venv, node_modules,
   cache, metadata Git lồng, binary build thừa. Mọi loại trừ có lý do; dữ liệu không nằm trong
   Git phải được tìm trong local/snapshot trước, thiếu thì ghi rõ nguồn/cách lấy, không tạo file giả.
4. Dùng runtime WSL Ubuntu/user tuananh đã khóa; Python torch:
   `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.
   TensorFlow dùng env riêng và library paths đã có; không đổi backend, tạo Windows env hoặc
   cài/nâng dependency vào env GPU. Probe thực tế khả năng chạy code cũ trước khi sửa tương thích.
   Nếu thật sự cần dependency khác, ghi lock/version và phương án riêng rồi xử lý theo quyền hiện có.
5. File đã khóa không sửa trực tiếp. Bản chạy sau migration là revision mới nếu cần đổi import/path.
   Giữ bản gốc bất biến và manifest `old logical path → new physical path → SHA256`.
   Audits mới dùng mapping kiểm file gốc; không sửa seal/lock cũ để làm PASS.
6. Dataset lớn dùng một bản vật lý khi thực sự cùng SHA256, catalog trong mỗi `datasets/`
   ghi rõ nơi lưu, nguồn, schema, split, quyền truy cập và lệnh resolver/materialize.
   Dữ liệu nhỏ có thể copy trực tiếp. Không để folder datasets rỗng hoặc chỉ có README chung chung;
   không phụ thuộc junction/symlink Windows để chạy được trên WSL/Linux/Render.
   Dùng chung file không có nghĩa dùng chung split/preprocessor giữa các bài khác nhau.
7. Không xóa source cũ trước khi bản mới đã được đối chiếu và smoke test. Di chuyển bằng journal
   theo từng nhóm, kiểm absolute path nằm trong workspace, hash trước/sau và có rollback.
   Việc dọn source cũ trùng lặp thuộc phạm vi yêu cầu này sau các gate; không xóa dữ liệu cá nhân,
   env, dữ liệu khoa học duy nhất, `.git` root hoặc tài nguyên ngoài workspace.
8. Giữ báo cáo đã phát hành nguyên byte. Việc viết lại nội dung tiểu luận/DOCX không thuộc lần gom
   source; tieuluan2 có thể dẫn xuất source/report text nhưng không gán DOCX6 chương là bản5 chương.
   Nếu cần dựng DOCX mới về sau phải có revision và render/QA riêng.

## Phase 1 — Kiểm kê, khóa nguồn và phục hồi vào staging

Trạng thái: COMPLETE (30/10/2026). Dependency: không có.
Bằng chứng: `docs/reorganization/phase1_report.md`, `phase1_handoff.json`,
`phase1_verification.json` và `live_preservation_receipt.json`.

**Mục tiêu:** xác định chính xác mỗi bài lấy những file nào, đủ dữ liệu/phụ thuộc để chạy và
có bản phục hồi kiểm chứng trước khi thay cấu trúc source đang dùng.

**Thực hiện:**

1. Chụp Git HEAD/status, full commit SHA, tracked/untracked/ignored cần giữ; kiểm process,
   dung lượng thật và tổng kích cỡ dự kiến. Tạo manifest/hash và backup chọn lọc của file chưa
   commit; source đã commit khôi phục được từ Git nên không cần nhân bản nguyên ổ dữ liệu.
2. Đọc README, notebook imports/cell nguồn, config, backend/routes và artifact metadata của
   từng mốc. Chọn A01 từ hai bản theo độ đầy đủ/output và ghi quyết định; A03 dùng header fix
   nếu thực sự chỉ sửa trình bày; tiểu luận1 giữ bản portable fix phù hợp.
3. Lập bảng từng bài: dataset thật, số notebook, vai trò notebook (train/EDA/demo/results),
   model/artifact, report, web/API, dependency và path hardcode. Liệt kê phần thiếu/ignored/LFS
   pointer/nguồn download nếu có; không gọi pointer là dataset/model.
4. Khôi phục file chọn lọc vào staging theo từng bài, bằng Git blob/archive allowlist.
   Không execute notebook hoặc code lịch sử chưa đọc; không restore env/cache từ A05.
   Tìm data/model cũ trong local và `releases/v2/source_snapshot.zip` trước khi tải mới.
5. Khóa bản đồ11 bài và kế hoạch relocation: file giữ, nơi đến, dùng chung, loại trừ,
   cách bảo toàn lock/namespace, cặp agent mới/cũ, đường dẫn source serving và Render.
6. Lập ma trận web: tab/bài toán/mô hình cần giữ từng bài, loại live inference hay replay,
   input/output hợp lệ và ca smoke. Ghi rõ dùng sample/replay khi không có trained artifact.

**Đầu ra:**

- `docs/reorganization/source_inventory.json`:11 bài + SHA/nguồn/size/dependency.
- `docs/reorganization/migration_map.json`: old/new path, hash, action và lý do.
- `docs/reorganization/dataset_catalog.json`: dataset, phiên bản, storage, split, tình trạng.
- `docs/reorganization/web_matrix.md`, `runtime_matrix.md`, `phase1_report.md`.
- `docs/reorganization/staging/` (ignored nếu lớn) và manifest phục hồi có kiểm hash.
- Backup chọn lọc, ignore rules cho staging/backup, checkpoint và nhật ký.

**Nghiệm thu:** đủ11 bài trong inventory; A01–A06/tieuluan1 có full commit và file thực đã
phục hồi; agent web chưa commit được giữ đủ; tieuluan2 ghi là derived; nguồn hiện hành chưa
bị thay/di chuyển; staging parse được notebook/source; mọi thiếu hụt có kế hoạch cụ thể.
Thiếu đầu vào trọng yếu không được đánh dấu nguồn đó complete hoặc âm thầm thay bằng bài khác.

## Phase 2 — Tổ chức11 bài và làm đường chạy notebook/dataset

Trạng thái: COMPLETE (31/10/2026). Dependency: Phase1 COMPLETE.

**Mục tiêu:**11 folder đích có datasets/notebooks/web rõ ràng; source và notebook tìm đúng
dataset/checkpoint bằng đường dẫn mới, không phụ thuộc tên agent cũ hoặc working directory tình cờ.

**Thực hiện:**

1. Tạo skeleton11 bài; chuyển payload từ staging và source hiện tại theo migration_map.
   Gom V3 về `tieuluan3/`, bao gồm source/API/UI/report/artifact và config cần thiết.
   Đổi hai folder agent sang `agent01/`, `agent02/`; giữ tài liệu/output/evidence, không chỉ notebook.
2. Đặt notebook chính vào `notebooks/`, dataset/catalog vào `datasets/`.
   Giữ notebook gốc/output; bản sửa path là migration revision
   có diff. Cập nhật imports, root discovery, resource URL, model lookup và download notebook.
3. Với code đã khóa/serialized class: bảo toàn source gốc, dùng adapter/path resolver và
   namespace tương thích có phiên bản. Kiểm `term_paper` và `agent02_assignment` trước khi đổi
   module name; không unpickle artifact từ nguồn không được tin cậy.
4. Tổ chức data nhỏ/trùng/lớn theo catalog và resolver; cập nhật ignore theo11 folder.
   Chỉ bundle input mẫu/model phục vụ inference cần thiết cho web; không publish raw lớn/secret.
5. Dựng `tieuluan1` theo phiên bản Git đã khóa. Dựng `tieuluan2` bằng bản sao chọn lọc/revision
   từ tieuluan3: giữ Ch1–5/RNN–LSTM/KG–RAG, bỏ Ch6 multi-agent khỏi source hoạt động, notebook,
   datasets/taskset, catalog, routes, registry phục vụ, tests/build và tài liệu hướng dẫn.
   Giữ provenance trỏ bản gốc; không xóa mã agent của tieuluan3 hoặc hai bài agent riêng.
6. Gom env/wrapper dùng chung: mỗi bài có hướng dẫn kernel và lệnh chạy với project root rõ.
   Wrapper resolve từ vị trí script, không hardcode path Windows của máy. Không cài lại runtime.
7. Kiểm import/compile, notebook schema, tồn tại dataset/hash/schema, load checkpoint + sample
   inference nếu có; notebook kết quả được Run All read-only khi đã xác nhận không gọi train/TEST.
   Notebook train lịch sử chỉ static check + smoke tách riêng trên fixture/TRAIN sample, ghi rõ
   chưa full Run All/train lại. So golden output cũ ở tolerance đã khai báo trước kiểm tra.
8. Cập nhật README từng bài/root, manifest repository, AGENTS phù hợp tên mới và mapping;
   giữ lịch sử kế hoạch/lock cũ, không làm chúng trỏ lẫn bài.

**Đầu ra:**11 folder, mỗi folder có datasets/notebooks/web; resolver/runner mới nếu cần;
`provenance/` từng bài; `docs/reorganization/phase2_report.md`, `notebook_smoke.json`,
`relocation_receipts.json`, `checkpoint.json` và hướng dẫn chạy thực tế.

**Nghiệm thu:** tồn tại đủ33 folder bắt buộc; data/checkpoint cần dùng resolve được từ path mới;
hash khoa học/report gốc giữ nguyên; notebook có kernel đúng và phân loại rõ; smoke phù hợp
PASS từng bài; tieuluan2 không expose/đòi chạy Ch6; tieuluan3 còn đủ6 chương.
Web lúc này có source/payload đúng nơi nhưng chỉ nghiệm thu đầy đủ giao diện ở Phase3.

## Phase 3 — Hoàn thiện11 web, kiểm thử và dọn source cũ

Trạng thái: COMPLETE (31/10/2026). Dependency: Phase2 COMPLETE.

**Mục tiêu:** mỗi bài có web chạy được,11 dự án dễ mở/chạy, source root gọn và sẵn sàng commit.

**Thực hiện:**

1. Agent01: tái sử dụng maze demo hiện có, chuyển source khỏi dist, sửa URL notebook/data.
   Agent02: giữ demo hiện có và kết quả sealed, thêm thiếu sót cần thiết theo style agent01.
2. A01–A06: làm web HTML/CSS/JS nhỏ theo mẫu agent01. Mỗi dataset/bài toán có lựa chọn rõ;
   hiển thị sample, output/model comparison và biểu đồ thật có giải thích ngắn (trục, đơn vị,
   nguồn và kết luận). Cho nhập/chọn mẫu khi có backend/checkpoint đã hoạt động; nếu chỉ
   replay thì ghi rõ, không mô phỏng ngẫu nhiên rồi gắn là model inference hay training live.
3. Web tiểu luận1: giữ UI tổng hợp theo chương của phiên bản đã phục hồi. Web tiểu luận3:
   giữ React/Python, style, chapter/subtab, so sánh và hành vi hiện tại. Web tiểu luận2:
   giữ UI cùng kiểu tiểu luận3 nhưng chỉ Ch1–5; API catalog và serving bundle đồng bộ.
4. Mỗi `web/` có README, `.env.example` khi cần, lệnh build/serve và port/API riêng có cấu hình;
   không cứng hóa tất cả về API V3 đang deploy. Không public `.env` hoặc key.
   Static web ưu tiên vanilla; backend nhỏ chỉ khi inference thật cần Python.
5. Cập nhật Render entrypoints/path filters/build/start/bundle manifest cho source sau relocation.
   Giữ root Render mặc định phục vụ tieuluan3 để tiếp nối hai service hiện có; cấu hình mẫu
   cho tieuluan1/2 và static demos riêng nếu cần. Nêu rõ YAML không tự thay Dashboard thủ công.
   Chỉ chuẩn bị và test local; việc tạo service/deploy/push sẽ làm khi người dùng yêu cầu.
6. Build3 web tiểu luận; kiểm8 static demo bằng server local. Kiểm navigation, sample/output,
   chart/caption, notebook download, đường dẫn assets, request API, lỗi input, CORS/readiness
   và màn hình hẹp. E2E tập trung ca thực tế, không mở scientific TEST để tạo bằng chứng.
7. Đối chiếu inventory/hash trước/sau, kiểm11 folder và33 thư mục chính, scan tham chiếu cũ
   phân biệt active code với tài liệu lịch sử. Kiểm migration từ clean checkout bằng artifact
   fetch/materialize được kê khai; ghi rõ phần local-only và artifact lớn chưa có trên Git.
8. Khi bản mới đạt gate, dọn các bản source cũ trùng lặp/staging/build thừa theo map/journal.
   Baseline duy nhất, raw/model duy nhất và evidence không được mất; lưu phần bất biến cần thiết
   trong provenance/archive có catalog. Nested Git metadata được bảo quản ngoài payload hoạt động.
   Kiểm `.gitignore` để không commit nhầm raw/venv nhưng vẫn theo dõi đủ demo/notebook/source.
9. Bàn giao README root11 bài, bảng dataset/notebook/kernel/lệnh chạy, bản đồ folder cũ→mới,
   checklist Render cần đổi và trạng thái Git. Không tự commit/push, gửi bài hoặc sửa account.

**Đầu ra:**11 web riêng; config/runtime/deploy path đã cập nhật; screenshots và smoke/E2E receipts;
`docs/reorganization/phase3_report.md`, `final_inventory.json`, `verification.json`,
`rollback.md`; README/AGENTS/checkpoint cuối cùng.

**Nghiệm thu:**11 web chạy đúng bài;8 demo đơn giản,3 UI tổng hợp; tieuluan2 bỏ đúng Ch6 còn
tieuluan3 giữ Ch6; no broken notebook/data/model link; golden output/hash không đổi; build/smoke
PASS hoặc giới hạn được ghi cụ thể, không gọi overall COMPLETE nếu mất tính năng bắt buộc.
Root không còn source cũ hoạt động song song ngoài danh sách compatibility đã kê khai.
Không có train/TEST lại, không reset Git, không mất nội dung web chưa commit.

## 5. Trạng thái và nhật ký

| Phase | Trạng thái | Bước tiếp theo |
|---|---|---|
| 1 | COMPLETE | Phục hồi37.786file, kiểm tĩnh50notebook/128Python, bảo toàn42.939file hiện hành |
| 2 | COMPLETE | 11bài/33folder, source/hash/nb/runtime smoke PASS; xem phase2_report.md |
| 3 | COMPLETE | 11web/3build/3source-only checkout PASS; xem phase3_report.md |

30/10/2026: đã khảo sát Git local/cấu trúc hiện tại, xem quy tắc bảo toàn, kiểm web-demo và
nguồn các assignment; chỉ tạo kế hoạch/điều phối. Chưa phục hồi payload, di chuyển source,
train, cài env, sửa web hoặc Render. Lệnh bắt đầu: **`làm phase 1`**.

30/10/2026 — Phase1 COMPLETE: inventory11bài; staging37.786file/~1,982GiB;57file backup
bao gồm52web-demo file chưa commit. Read-back SHA256 payload và42.939file hiện hành PASS;
50notebook/128Python AST PASS,0error-output lịch sử; map80.818file không xung đột đích.
Catalog24nhóm data; CIFAR10 A04 còn thiếu Python-format gốc, binary V3 có sẵn và phương án
resolve đã ghi rõ. Runtime Torch và TensorFlow vẫn tách biệt, chưa kiểm chứng chạy notebook cũ.
Chưa di chuyển/xóa source, train/TEST, chạy web, sửa env/Render hoặc commit/push.
Phase2 giữ nguyên Phase1 handoff; sửa manifest cần revision mới. Lệnh tiếp: **`làm phase 2`**.

31/10/2026 — REORG Phase2 COMPLETE: xem docs/reorganization/phase2_report.md và phase2_handoff.json. Không train/TEST lại, đổi env, commit/push/deploy. Tiếp Phase3 chỉ khi được yêu cầu.

31/10/2026 — REORG Phase3 COMPLETE:11web,22browser groups/22screenshots,11helper tests,3build/3source-only serving checkout PASS; source/hash giữ nguyên, dọn theo gate. Không commit/push/deploy.
