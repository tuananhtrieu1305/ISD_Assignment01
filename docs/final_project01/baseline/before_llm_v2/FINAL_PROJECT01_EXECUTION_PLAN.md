# Kế hoạch hiện hành — tiểu luận final và project01

Phiên bản 1.0 — 01/11/2026, múi giờ Asia/Bangkok.
Checkpoint: `docs/final_project01/checkpoint.json`.
Ưu tiên: hoàn thành khẩn trương với đúng **3 phase**, tận dụng tài nguyên đã có.

## 1. Mục tiêu và cách gọi phase

Hai sản phẩm cần hoàn thành:

1. **Tiểu luận final** phát triển từ `tieuluan3`: đủ sáu chương, lý thuyết + code notebook + kết quả + web demo. Chương 6 giải thích đúng hệ đa agent và bổ sung ứng dụng KB/KG/RAG vào bài toán tiểu đường.
2. **`project01/` độc lập về chức năng**, chuyên về hệ đa agent hỗ trợ tìm hiểu bệnh tiểu đường: nhận câu hỏi/hồ sơ có cấu trúc, dùng mô hình dự đoán và tri thức truy hồi khi phù hợp, kiểm chứng rồi trả lời có nguồn. Có notebook, web và báo cáo riêng; dùng chung runtime hiện có.

Từ thời điểm lập kế hoạch này:

- `làm phase 1` / `làm FINAL phase 1`: thực hiện Phase 1 dưới đây.
- `làm phase 2` / `làm FINAL phase 2`: thực hiện Phase 2, sau khi Phase 1 COMPLETE.
- `làm phase 3` / `làm FINAL phase 3`: thực hiện Phase 3, sau khi Phase 2 COMPLETE.
- `làm tiếp task đang dở`: đọc checkpoint, xác minh process thực rồi tiếp tục đúng bước còn thiếu.
- `kiểm tra phase đã xong chưa`: đối chiếu sản phẩm/nghiệm thu; không tự chạy lại train hoặc TEST cũ.
- Tiền tố `REORG`, `AG02` hoặc `V3` gọi kế hoạch lịch sử tương ứng; lệnh không tiền tố ưu tiên kế hoạch FINAL này. Không tự làm lại ba phase REORG.

Đọc **toàn bộ file này** và checkpoint trước mỗi phase. Khi thực hiện: cập nhật IN_PROGRESS, ghi việc đã xong/đang làm/cần tiếp tục; chỉ COMPLETE khi đủ điều kiện nghiệm thu. Không tự chuyển sang phase sau nếu chưa được yêu cầu. Không tạo thêm phase nếu chỉ là bước triển khai nội bộ.

## 2. Điểm xuất phát đã kiểm tra

- `tieuluan3` có sáu chương, bốn notebook inline và web tổng hợp theo chương.
- Chương 5 có KB/KG và truy hồi theo câu hỏi: sparse, dense LSA, fusion, graph; lớp trả lời hiện là **trích xuất**, không dùng LLM bên ngoài.
- Chương 6 hiện có A0 direct, A1 router/specialist và A2 thêm verifier/reporter; ba miền diabetes/house/gold.
- `retrieve_medical` của Chương 6 đang trả trích đoạn MedQuAD từ catalog theo `record_id`. Chưa gọi RAG theo câu hỏi, chưa kết hợp numeric + evidence trong cùng phản hồi. Không được mô tả trạng thái cũ là hệ đã tích hợp RAG đầy đủ.
- Có sẵn CDC diabetes, MedQuAD, model MLP và các index/checkpoint có thể tái sử dụng sau khi kiểm tra schema/hash/điều khoản. `project01/` chưa tồn tại khi lập kế hoạch.
- Notebook revision inline-v1 và REORG đều COMPLETE; raw/model/metric/prediction/report/lock cũ phải được bảo toàn.

## 3. Các quyết định để làm nhanh

- Dùng lại hai env WSL Ubuntu/user `tuananh`: `.venv-torch` và `.venv-keras` dưới `/home/tuananh/.local/share/ai-term-paper-v3/`. Không cài lại GPU, không cài trộn framework, không chạy bootstrap/doctor cũ ghi đè evidence.
- Baseline project dùng **NumPy CPU + các index truy hồi hiện có**, không huấn luyện lại mô hình và không phụ thuộc API trả phí. Không thêm framework điều phối agent, vector database server hoặc microservice nếu chưa có nhu cầu thực tế.
- Đây là hệ nhiều agent điều phối theo luật với nhiệm vụ/quyền công cụ/đầu vào/đầu ra riêng và cơ chế phản hồi kiểm chứng; không gắn nhãn LLM-agent. Thêm LLM chỉ là hướng mở rộng, không là hạng mục bắt buộc hay lý do chặn tiến độ khi thầy chưa yêu cầu.
- Dataset chính của project: **CDC diabetes** cho dự đoán và **MedQuAD diabetes** cho hỏi đáp. Benchmark tình huống mới là sản phẩm đánh giá riêng, không gọi thành raw dataset y khoa thứ ba. Chỉ bổ sung tài liệu nếu corpus hiện tại thiếu rõ ràng, có nguồn/giấy phép; không mặc định tải bộ ảnh lớn hoặc dữ liệu mới không phục vụ mục tiêu.
- Không làm lại các chương ML/CNN/RNN–LSTM hoặc các thí nghiệm cũ. Rà soát và sửa cách giải thích, trình bày, liên kết notebook/demo; kết quả khoa học cũ giữ nguyên.
- Lý thuyết ngắn, cơ bản, dễ hiểu, đủ ý; ưu tiên ví dụ và sơ đồ. Công thức chỉ giữ khi cần; giải thích hợp các hàm và từng hàm bằng input → xử lý → output.
- Mỗi cây `notebooks/` tối đa 4 file. Code thuật toán thật có ngay trong cell, không chỉ import `.py`, `%run` hoặc hiển thị đoạn source. Có thể dùng cùng quy ước `%%inline_module` hiện hành. Source backend tạo từ notebook theo một chiều có khai báo nguồn; chỉnh thuật toán trong notebook, không duy trì hai implementation độc lập.
- Dùng React + Python cho web; tận dụng style tiểu luận3, làm một ứng dụng tập trung vào tiểu đường. Cấu hình local và Render có thể dùng cùng repo; chỉ chuẩn bị/check cấu hình, không tự deploy.
- Không dùng profile/số đo CDC để tự nhận là chẩn đoán hoặc nguy cơ mắc mới đã được hiệu chuẩn. Trình bày đúng nhãn/output của model; thiếu trường thì chỉ trả lời tri thức, không tự điền số.

## 4. Cấu trúc sản phẩm

```text
project01/
  README.md
  AGENTS.md
  datasets/
    catalog.json                 # nguồn + schema + path dữ liệu dùng lại
    benchmark/                   # tình huống và rubric mới của project
  notebooks/
    01_Data_KB_RAG.ipynb          # đọc dữ liệu, KB/KG, code truy hồi
    02_Diabetes_Multi_Agent.ipynb # các agent, tool dự đoán, điều phối, demo
    03_Evaluation.ipynb           # code đánh giá, bảng/plot và giải thích
  web/
    frontend/                    # React
    backend/                     # Python; implementation export từ notebook
    deploy/                      # hướng dẫn/config, không chứa secret
  artifacts/                     # output/checkpoint tham chiếu mới, không sửa bản cũ
  report/
    Project01_Report.md           # mô tả ngắn, kết quả, hình và cách tái lập
    figures/
  tests/                         # kiểm tra tích hợp thực sự cần thiết

tieuluan3/
  notebooks/                     # vẫn 4 notebook, thay đổi có revision giữ bản trước
  web/                           # vẫn demo tổng hợp sáu chương
  report/final/
    Tieu_Luan_AI_Final.docx       # giữ bản DOCX cũ nguyên trạng
    sections/                    # bản thảo sửa mới
    figures/

docs/final_project01/
  checkpoint.json
  baseline/                      # danh sách/hash và original của file thực sự đổi
  phase1_report.md
  phase2_report.md
  phase3_report.md
```

Không nhân bản raw dataset lớn hoặc venv. Catalog phải phân biệt nguồn dữ liệu thuộc repository khác với file được đóng gói trong project; công cụ export/package được khai báo rõ để chuyển máy vẫn có đường chạy. Project có README và báo cáo Markdown ngắn; phần trình bày học thuật nằm trong case study của DOCX final, không làm thêm DOCX thứ hai khi chưa được yêu cầu.

## Phase 1 — Chốt đầu vào và dựng nền project

**Mục tiêu:** có một thiết kế nhỏ, rõ và dữ liệu dùng được, bắt tay code ngay ở Phase 2.

### Công việc

1. Đọc checkpoint; xác định DOCX/manuscript hiện hành và inventory các thành phần cần lấy từ tiểu luận3. Ghi hash baseline, giữ bản trước khi sửa; không sao chép lại toàn repository. Xử lý dispatcher/verifier bằng revision nhỏ để thay AGENTS và các file entry point không làm mất khả năng đối chiếu handoff cũ; không sửa handoff/lock đã khóa. Bản AGENTS trước khi lập plan đã nằm ở `baseline/AGENTS_before_final_plan.md`.
2. Tạo skeleton `project01` theo cấu trúc trên, hướng dẫn và checkpoint. Probe import/runtime + artifact load vừa đủ, không train/TEST, không đổi env. Tạo runner riêng hoặc mở rộng runner hiện hành bằng revision để nhận `project01`; bảo đảm 11 bài cũ vẫn chạy theo cấu hình cũ.
3. Kiểm nguồn CDC, tập feature/target và preprocessing đúng checkpoint; kiểm MedQuAD corpus/index, ngôn ngữ, coverage câu hỏi và metadata citation. Chọn sẵn dữ liệu demo từ TRAIN/corpus được phép, không mở TEST cũ. Ghi link, giấy phép, kích cỡ, số mẫu, phân bố, ví dụ và hạn chế. Không coi index LSA là embedding neural.
4. Chốt phạm vi hỏi đáp: MedQuAD chủ yếu tiếng Anh; kiểm thử vài câu tiếng Việt sớm. UI có thể tiếng Việt nhưng phải công khai ngôn ngữ truy hồi. Chỉ thêm chuẩn hóa/từ điển song ngữ hữu hạn có kiểm chứng nếu cần; không hứa hiểu tiếng Việt tự do khi chưa đo.
5. Chốt 5 vai trò: **Coordinator**, **Risk Agent**, **Knowledge Agent** (KB/KG + RAG), **Verifier**, **Reporter**. Ghi input/output, quyền gọi tool, trạng thái và điều kiện chuyển bước. Verifier có thể yêu cầu truy hồi lại tối đa một lần khi thiếu bằng chứng. Tách rõ bài toán chỉ hỏi kiến thức, chỉ dự đoán, và kết hợp cả hai.
6. Khóa thiết kế/rubric benchmark project trước khi chạy: mục tiêu **60 tình huống mới = 20 development + 40 evaluation**, chia theo nhóm câu hỏi/nguồn tài liệu/hồ sơ để tránh bản diễn đạt lại nằm ở cả hai tập. Có các nhóm kiến thức, dự đoán, kết hợp, thiếu dữ liệu, ngoài phạm vi và tool/evidence lỗi. Không dùng lại bộ TEST cũ làm development. Mẫu và hồ sơ tổng hợp phải ghi synthetic, không gọi bệnh án thật; gold trả lời tham chiếu phải có nguồn.

### Sản phẩm và nghiệm thu

- Skeleton, catalog dữ liệu, `docs/architecture.md`, `docs/evaluation_protocol.md` trong project; `phase1_report.md` nêu rõ những gì tái sử dụng và giới hạn.
- Tải/đọc được đúng model + index; schema feature và một luồng query từ dữ liệu development/corpus được kiểm tra. Không cần benchmark/train lại để nghiệm thu nền.
- Có danh sách thiếu thực sự, quyết định ngôn ngữ/KB/KG rõ và rubric đánh giá trước triển khai.
- Checkpoint Phase 1 COMPLETE, Phase 2 READY. **Không bắt đầu build toàn web hay DOCX ở Phase 1.**

## Phase 2 — Làm project01 chạy hoàn chỉnh và đánh giá

**Mục tiêu:** demo thực sự nối model + KB/KG/RAG, có đầu ra và số đo mới đáng giải thích.

### Công việc

1. Viết code đầy đủ trong ba notebook đã định. Knowledge Agent nhận **nội dung câu hỏi** để truy hồi từ corpus, không yêu cầu người dùng nhập chunk/record ID. Dùng sparse/dense/fusion/graph sẵn có có kiểm tra tương thích; nếu đồ thị chỉ hỗ trợ liên kết thực thể thì công khai phạm vi đó. Mọi đoạn/chuyến đi graph được sử dụng phải truy được về bằng chứng nguồn.
2. Risk Agent chuẩn hóa hồ sơ theo đúng feature order/preprocessing và gọi checkpoint CDC. Coordinator quyết định gọi một hoặc cả hai specialist; lưu kết quả trung gian riêng. Verifier kiểm nguồn, mức hỗ trợ của câu trả lời, giá trị số/đơn vị và thiếu thông tin; kiểm hash chỉ là integrity, không thay kiểm nội dung. Reporter kết hợp dự đoán + bằng chứng khi tác vụ cần cả hai, giữ nguyên số model, không suy thành chẩn đoán. Mỗi agent phải có quyết định/hợp đồng cụ thể, không chỉ đặt tên cho các hàm nối tiếp.
3. Thêm shared state/trace có request ID, agent, tool, input/output, nguồn, timing thật và lỗi. Giới hạn một yêu cầu ≤30 giây, ≤8 tool call, ≤1 lần yêu cầu truy hồi bổ sung; dừng rõ khi không đủ bằng chứng, không lặp vô hạn. Không ghi chain-of-thought hoặc thông tin cá nhân không cần thiết.
4. Export implementation từ notebook cho Python backend, gắn hash/version và kiểm parity. Làm React UI gồm **Câu hỏi & hồ sơ**, **Kết quả & nguồn**, **Luồng agent**, **So sánh phương pháp**; có ví dụ bấm chạy, loading, lỗi/thiếu artifact và nhãn ngôn ngữ rõ. Tối thiểu chạy được hỏi kiến thức, profile + câu hỏi kết hợp và thiếu dữ liệu. UI và API phải thực sự gọi pipeline mới.
5. Development để sửa lỗi và chốt code, rồi đánh giá riêng **40 tình huống evaluation mới đúng một lần cho mỗi biến thể đã khóa**: P0 model/RAG độc lập; P1 điều phối + specialists; P2 thêm verifier + reporter + truy hồi bổ sung có giới hạn. P0 được dùng cùng dữ liệu/tool và định dạng đầu vào, không cố tình làm yếu; tiêu chí kết hợp phản ánh năng lực từng cấu hình. Nếu lỗi triển khai thì giữ output lỗi và sửa bằng revision công khai, không âm thầm xóa/chạy lại để chọn kết quả đẹp.
6. Đo task completion/correctness theo rubric, citation đúng và hỗ trợ phát biểu, xử lý thiếu dữ liệu, latency và tool calls; retrieval metric chỉ tính trên subset có gold evidence. Đánh giá này đo **pipeline**, không phải TEST predictive accuracy mới của MLP hay kết quả lâm sàng. Một phần kiểm hỗ trợ nội dung cần bảng chấm thủ công có tiêu chí; phân biệt tự động/thủ công và các trường hợp không có gold. Plot chỉ 3–4 hình hữu ích và giải thích trục, đơn vị, mẫu số, thông điệp, giới hạn.
7. Test tập trung vào nhánh kết hợp hai specialist, query thực, thiếu hồ sơ, citation không hỗ trợ, timeout và notebook/backend parity; smoke web/API. Chuẩn bị requirements CPU tối thiểu, env mẫu, model/index packaging và hướng dẫn Render có `/health`, `/ready`; không đóng gói dư model house/gold hoặc GPU dependency.

### Sản phẩm và nghiệm thu

- `project01` chạy end-to-end local bằng lệnh README, ba notebook chứa code thật và output được phân biệt development/evaluation; backend khớp source notebook.
- Một câu hỏi mới thật sự dẫn đến search/rank evidence; một case kết hợp có cả kết quả model + tài liệu và trace; không dùng exact lookup để giả thành RAG.
- Bảng so sánh P0/P1/P2 trên cùng 40 tình huống đã chốt; saved output + rubric + plot có giải thích. Không khẳng định P2 tốt hơn khi dữ liệu không cho thấy điều đó.
- Web, các ca lỗi chính và source parity PASS; báo cáo project có bản thảo ngắn cùng ảnh thật. Checkpoint Phase 2 COMPLETE, Phase 3 READY.

## Phase 3 — Hoàn thiện tiểu luận final và bàn giao

**Mục tiêu:** có DOCX final và hai demo dùng được, nội dung khớp code/kết quả.

### Công việc

1. Tạo bản final trong `tieuluan3/report/final/`, giữ DOCX/manuscript cũ. Sáu chương: (1) Lịch sử AI; (2) ML; (3) CNN; (4) RNN–LSTM; (5) KB/KG/RAG; (6) Đa agent và case study tiểu đường. Rút gọn lý thuyết dài/khó, giải thích thuật ngữ bằng ví dụ, giữ công thức thật cần thiết. Deployment là mục ngắn cuối mỗi chương, không tạo chương riêng.
2. Rà soát yêu cầu thầy ở các chương thực nghiệm: dataset/card/link/kích cỡ/mẫu/phân bố/nhận xét; Scratch/Keras/PyTorch, CNN/RNN/LSTM trên 5 layer theo quy ước đếm công bố; hợp các hàm, giải thích từng hàm và so sánh mô hình. Sửa trình bày từ evidence có sẵn; nếu thiếu kết quả thật thì ghi thiếu và đề xuất xử lý cụ thể, không tạo số liệu hoặc tự train lại TEST đã khóa.
3. Nối Chương 5 → 6 bằng mô tả và sơ đồ luồng KB/KG/RAG vào Knowledge Agent. Giữ benchmark A0/A1/A2 cũ đúng phạm vi, thêm mục case study `project01` với P0/P1/P2 và dữ liệu đánh giá mới; không thay thế/nhập nhằng metric cũ hoặc gọi benchmark tình huống là độ chính xác chẩn đoán.
4. Cập nhật notebook Ch6 và demo tổng hợp tiểu luận3 bằng revision giữ bản trước, vẫn tối đa 4 notebook. Case study trên tab Ch6 dùng pipeline `project01` thật với adapter/phiên bản rõ, không chỉ là hyperlink hoặc replay khoác nhãn live. Web riêng `project01` tiếp tục chạy độc lập theo README. Các tab/chương cũ giữ đường chạy đã có; nếu backend/serving source đổi thì tạo bundle revision mới, không âm thầm phục vụ archive cũ.
5. Xuất `Tieu_Luan_AI_Final.docx`. Dùng thông tin bìa đã xác nhận của Triệu Tuấn Anh/B23DCCN053/D23CTPM01 và giảng viên; giữ style tiểu luận3. Yêu cầu chữ đen của bài Discovering riêng không tự áp sang bài này. Tuân thủ skill tài liệu có sẵn và authorization toolchain thực sự áp dụng; render, xem toàn bộ trang, kiểm ảnh/bảng/caption/mục lục/nguồn và sửa lỗi layout. PDF chỉ thêm như bản đọc/QA nếu công cụ có sẵn, DOCX là sản phẩm chính. Chốt README và `Project01_Report.md` ngắn cho project riêng, tránh viết trùng toàn bộ lý thuyết.
6. Kiểm tra clean-start bằng runtime có sẵn, notebook count/source, local API/UI của project và tab tích hợp, link dataset/citation, serving source parity và tài nguyên deploy. Ghi lệnh chạy, đường dẫn model/data, giới hạn ngôn ngữ, trạng thái đo/không đo và hướng dẫn Render chính xác. Không tự commit/push/deploy; không coi chuẩn bị cấu hình là đã triển khai online.

### Sản phẩm và nghiệm thu

- DOCX final hoàn chỉnh mở được, render/visual QA PASS; nội dung lý thuyết/code/hình/kết quả thống nhất. Project có README, báo cáo Markdown ngắn và ảnh/kết quả đi kèm.
- Tiểu luận3 final có sáu chương và demo từng chương; `project01` có demo riêng chuyên tiểu đường, trace và so sánh.
- Danh sách file bàn giao + biên bản Phase 3 + checkpoint COMPLETE; liệt kê rõ giới hạn và việc triển khai online chưa làm.
- Dataset/checkpoint/metric/prediction/TEST/lock cũ không đổi; không cần tạo mới môi trường GPU.

## 5. Quy tắc tiếp tục và giữ tiến độ

- Không bắt đầu Phase 1 trong lượt chỉ yêu cầu lập plan. Trạng thái ban đầu là READY, `next_phase=1`.
- Mỗi phase chỉ tạo một biên bản ngắn và evidence cần để kiểm lại. Không thêm nhiều tầng manifest/gate/phases cho việc nhỏ. Hash chỉ dùng để bảo toàn bản cũ, liên kết source–export–output và định danh đánh giá.
- Được sửa notebook/path/config/UI mới theo phase đã được người dùng gọi; giữ bản trước của file đã khóa. Các hạn chế lịch sử về tên folder không được ngăn yêu cầu mới, nhưng không được làm mất evidence hay chạy lại TEST cũ.
- Benchmark evaluation của `project01` là bộ mới, được phép chạy trong Phase 2 đã được gọi. Đây không phải ủy quyền mở lại TEST CDC/MedQuAD/A0–A2 cũ hoặc tune bằng chúng.
- Không dùng GPU train cho project nếu không có thiếu sót cụ thể khiến checkpoint không dùng được. Khi gặp thiếu artifact, báo đúng trạng thái và xử lý theo scope phase, không tự sinh metric thay thế hoặc gọi bộ khởi tạo là model đã train.
- Cần thông tin không thể suy ra (ví dụ yêu cầu LLM/API mới từ thầy) thì hỏi ngắn và tiếp tục phần độc lập; không để tùy chọn nâng cấp làm chậm baseline đã chốt.
- Nếu gián đoạn, ghi `current_step`, `completed_steps`, `remaining_steps`, process thật, output đã có và bước tiếp theo. Không dùng PID lịch sử để tự resume.
