# Hiểu project01 trước khi chạy demo

Tài liệu dành cho người mới xem project, mô tả đúng bản Phase 2 hoàn tất ngày 01/11/2026. Không cần đọc code trước. Các đường dẫn bên dưới tính từ thư mục gốc `C:\DATA\assign` nếu không ghi khác.

## 1. Ta đang xây dựng và demo cái gì?

**Project01 là một ứng dụng học thuật về tiểu đường, kết hợp mô hình phân loại dữ liệu khảo sát với tìm kiếm kiến thức có dẫn nguồn, được tổ chức thành các vai trò agent.**

Người dùng có thể yêu cầu một trong ba việc:

| Việc muốn làm | Đưa gì vào? | Nhận gì ra? |
|---|---|---|
| **Chỉ kiến thức** | Một câu hỏi về tiểu đường | Trích đoạn tài liệu liên quan và nguồn để đối chiếu |
| **Chỉ mô hình** | Hồ sơ khảo sát đủ 21 trường; giao diện vẫn yêu cầu ô câu hỏi có nội dung | Điểm và nhãn phân loại từ mô hình đã huấn luyện |
| **Kết hợp cả hai** | Câu hỏi và hồ sơ đủ 21 trường | Cả đầu ra mô hình lẫn kiến thức liên quan đến câu hỏi, trong cùng một lượt xử lý |

Ví dụ xuyên suốt: **“Explain physical activity and diabetes.”** — “Giải thích về vận động thể chất và bệnh tiểu đường.”

- Chọn **Chỉ kiến thức**: hệ thống tìm tài liệu nói về vận động và tiểu đường. Không cần hồ sơ, không chạy mô hình.
- Chọn **Kết hợp cả hai**: hệ thống vừa chạy mô hình trên hồ sơ mẫu, vừa tìm tài liệu cho câu hỏi trên.
- Chọn **Chỉ mô hình**: hệ thống chỉ dùng hồ sơ để tính điểm; câu hỏi không trở thành đặc trưng đầu vào của mô hình.

**Mục tiêu demo:** cho thấy hệ thống chọn đúng công cụ, xử lý dữ liệu, truy hồi nguồn, kiểm tra đầu ra và ghi lại từng bước phối hợp.

Đây chưa phải ứng dụng khám bệnh, kê đơn hay đưa ra phác đồ cá nhân. Trong chế độ kết hợp, mô hình và truy hồi là hai nhánh bổ sung: hệ thống **chưa dùng điểm mô hình hoặc hồ sơ để suy ra tư vấn điều trị cá nhân**.

## 2. “Kiến thức · vận động” nghĩa là gì?

Đó chỉ là **tên nút điền nhanh một ví dụ**, không phải tên dataset, tên agent hay tên mô hình.

Khi bấm nút này, web tự điền:

```text
Chế độ: Chỉ kiến thức
Câu hỏi: Explain physical activity and diabetes.
Ngôn ngữ truy hồi: Tiếng Anh
```

“Vận động” ở đây là hoạt động thể chất như đi bộ, tập thể dục. Ta chọn chủ đề này vì kho MedQuAD có nội dung liên quan để minh họa việc tìm tài liệu.

Ba nút thử nhanh hiện tại:

| Nút trên web | Nó tự chọn điều gì? | Dùng để trình bày điều gì? |
|---|---|---|
| **Kiến thức · vận động** | Chỉ kiến thức, câu hỏi tiếng Anh về vận động và tiểu đường | Một câu hỏi đi qua bộ tìm kiếm, tạo ra trích đoạn có nguồn |
| **Kết hợp model + kiến thức** | Kết hợp cả hai, cùng câu hỏi tiếng Anh trên | Một yêu cầu gọi được cả mô hình CDC lẫn kho kiến thức |
| **Tiếng Việt · phạm vi glossary** | Chỉ kiến thức, câu hỏi “Bệnh thận tiểu đường” | Ánh xạ một số cụm tiếng Việt sang từ khóa tiếng Anh để truy hồi |

Bạn có thể sửa câu hỏi sau khi chọn mẫu. Các nút này không chạy một bộ dataset hoặc bài huấn luyện mới.

## 3. Ta có những dữ liệu nào?

### 3.1. CDC Diabetes: dữ liệu dạng bảng cho mô hình phân loại

- Nguồn: CDC BRFSS 2015, bản Diabetes Health Indicators. Thông tin nguồn được ghi tại [UCI dataset 891](https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators).
- Bản dữ liệu đang dùng có **253.680 dòng và 21 đặc trưng đầu vào**.
- Mỗi dòng là thông tin khảo sát sức khỏe, không phải một đoạn kiến thức để đọc trả lời câu hỏi.
- Nhãn đích: **0 = không tiểu đường; 1 = tiền tiểu đường hoặc tiểu đường** theo bản binary của dữ liệu.

Các trường đầu vào được chia nhóm để dễ hình dung:

| Nhóm | Trường trong dữ liệu | Ý nghĩa ngắn |
|---|---|---|
| Chỉ số và tiền sử sức khỏe | `high_bp`, `high_chol`, `chol_check`, `bmi`, `stroke`, `heart_diseaseor_attack` | Huyết áp cao, cholesterol cao/kiểm tra cholesterol, BMI, tiền sử đột quỵ/bệnh tim |
| Thói quen sinh hoạt | `smoker`, `phys_activity`, `fruits`, `veggies`, `hvy_alcohol_consump` | Hút thuốc, vận động, ăn trái cây/rau, uống rượu nhiều |
| Tiếp cận chăm sóc | `any_healthcare`, `no_docbc_cost` | Có chăm sóc/bảo hiểm y tế; từng không đi khám vì chi phí |
| Tình trạng sức khỏe | `gen_hlth`, `ment_hlth`, `phys_hlth`, `diff_walk` | Sức khỏe chung, số ngày sức khỏe tinh thần/thể chất không tốt, khó đi lại |
| Thông tin nền | `sex`, `age`, `education`, `income` | Mã giới tính, nhóm tuổi, trình độ học vấn, nhóm thu nhập |

Đọc đúng mã dữ liệu:

- `age` là **nhóm tuổi 1–13**, không phải nhập trực tiếp 20, 40 hay 60 tuổi.
- `bmi` là giá trị BMI thực; các trường khác có thể là mã 0/1 hoặc mức thứ bậc.
- `ment_hlth` và `phys_hlth` là số ngày 0–30.
- Nên giữ **hồ sơ mẫu** trong lần demo đầu để tránh nhầm mã. Schema chính xác nằm ở [profile_schema.json](../project01/datasets/profile_schema.json).

**Dữ liệu được dùng như thế nào?** Mô hình đã được huấn luyện ở tiểu luận3; project01 dùng lại checkpoint scratch/NumPy seed42, không huấn luyện lại khi bấm chạy web.

```text
21 trường hồ sơ
    → kiểm đủ trường và đúng miền giá trị
    → chuẩn hóa bằng tham số TRAIN đã lưu
    → mạng 6 lớp Dense: 64 → 64 → 32 → 32 → 16 → 1
    → score trong [0, 1] và nhãn phân loại
```

Nếu thấy score khoảng `0.3955`, hãy gọi là **điểm đầu ra mô hình**, không diễn giải thành “người này có 39,55% khả năng mắc bệnh”. Mô hình dùng trọng số lớp và chưa hiệu chuẩn thành xác suất mắc bệnh cá nhân. Nhãn 1 cũng không tách riêng tiền tiểu đường với tiểu đường.

Tập TRAIN đã lưu có 152.760 dòng lớp 0 và 24.745 dòng lớp 1: lớp 0 chiếm đa số. Tổng kích cỡ raw không đồng nghĩa toàn bộ đều được dùng để fit checkpoint này; có quy trình chia tập và chọn matched TRAIN từ tiểu luận3.

### 3.2. MedQuAD: dữ liệu văn bản cho kho kiến thức

- Nguồn: [MedQuAD](https://github.com/abachaa/MedQuAD/tree/577bd37b96c02d1833b2c9eed2de9f96964e96cb), bộ hỏi đáp y khoa gốc thu thập từ các website thuộc NIH.
- **Phần đang đóng gói cho project01** có **247 tài liệu, chia thành 762 đoạn văn bản tiếng Anh**. Đây là kích cỡ subset đang sử dụng, không phải toàn bộ MedQuAD gốc.
- “Document” là tài liệu; “chunk” là một đoạn được chia nhỏ từ tài liệu để thuận tiện tìm kiếm.
- Nội dung gồm các chủ đề liên quan đến tiểu đường như vận động, đường huyết, biến chứng, thận, bàn chân…

Một đoạn ví dụ trong snapshot nói rằng bắt đầu chương trình vận động có thể hỗ trợ kiểm soát cân nặng và đường huyết, đồng thời cần trao đổi với đội ngũ chăm sóc sức khỏe trước khi bắt đầu. Đây là **nội dung tài liệu để truy hồi**, không phải kết quả mô hình tạo ra từ hồ sơ CDC.

Ta không ghép từng dòng CDC với một tài liệu MedQuAD thành cặp bệnh nhân–bài tư vấn. Hai nguồn phục vụ hai công cụ khác nhau.

### 3.3. Bộ tình huống đánh giá: kiểm tra hệ thống có làm đúng việc không

Project còn có **60 tình huống viết riêng: 20 development và 40 evaluation**.

Ví dụ các nhóm: chỉ hỏi kiến thức, chỉ chạy mô hình, kết hợp, thiếu trường hồ sơ, câu hỏi ngoài phạm vi, công cụ/bằng chứng gặp lỗi. Hồ sơ của benchmark là dữ liệu tổng hợp, không phải bệnh án mới.

Đây là **bộ kiểm tra pipeline**, không phải một dataset y khoa thứ ba để huấn luyện. Mỗi tình huống evaluation đã chạy qua 3 cách P0/P1/P2, tạo 120 đầu ra được lưu. Web chỉ đọc bảng tổng hợp; không tự chạy lại bộ evaluation.

### 3.4. Dữ liệu và model nằm ở đâu?

| Vị trí từ root | Nội dung |
|---|---|
| `tieuluan3/datasets/raw/ch2/cdc_diabetes/data.csv` | Dữ liệu CDC raw được tái sử dụng; không nhân bản sang project01 |
| `project01/datasets/catalog.json` | Danh mục nguồn, kích cỡ, đường dẫn và hash |
| `project01/datasets/demo_profiles.json` | 3 hồ sơ mẫu lấy từ TRAIN cũ để demo, không phải bệnh nhân mới |
| `project01/datasets/profile_schema.json` | Tên, thứ tự và miền giá trị 21 trường |
| `project01/datasets/query_glossary.json` | Từ điển cụm từ tiếng Việt → tiếng Anh có giới hạn |
| `project01/datasets/benchmark/` | 20 development và 40 evaluation đã khóa |
| `project01/artifacts/package/v1/` | Gói chạy web: model, preprocessing, đoạn MedQuAD, graph và hai index tìm kiếm |
| `project01/artifacts/phase2/evaluation/raw_results/` | 120 đầu ra đánh giá gốc đã lưu |

Web cần gói serving nhỏ ở `artifacts/package/v1/`; không cần đọc lại toàn bộ CSV hay huấn luyện lại để xử lý mỗi câu hỏi.

## 4. KB, KG và RAG khác nhau thế nào?

Hãy hình dung một thư viện:

| Khái niệm | Trong ví dụ thư viện | Trong project01 |
|---|---|---|
| **KB — Knowledge Base** | Những trang sách đang có | 762 đoạn MedQuAD cùng mã tài liệu và thông tin nguồn |
| **KG — Knowledge Graph** | Sơ đồ nối chủ đề với những trang liên quan | 62 nút neo từ/cụm từ, liên kết tới các đoạn văn bản |
| **RAG — truy hồi rồi tạo đầu ra dựa trên bằng chứng** | Tìm trang liên quan, đọc rồi trích ý có nguồn | Tìm/xếp hạng đoạn văn, chọn trích đoạn làm câu trả lời, gắn citation |

Luồng tìm kiến thức thực tế:

```text
Câu hỏi
   ↓
Chuẩn hóa từ khóa
   ↓
┌ BM25: tìm theo từ khóa xuất hiện trong văn bản
├ LSA: tìm theo biểu diễn thống kê nội dung văn bản
└ Graph: tìm chủ đề khớp và những đoạn được liên kết
   ↓
Gộp các danh sách xếp hạng → chọn tối đa 10 đoạn ứng viên
   ↓
Chọn trích đoạn phù hợp → câu trả lời + mã đoạn + nguồn
```

Ví dụ minh họa graph: `chủ đề vận động → đoạn tài liệu nói về vận động`. Trên web, **Đường graph** cho biết đường neo–đoạn của ứng viên nếu có. Một đoạn tìm được bằng BM25/LSA vẫn có thể không có đường graph.

Graph ở đây hỗ trợ **tìm và xếp hạng bằng chứng**. Nó chưa có đầy đủ quan hệ kiểu bệnh → thuốc → liều, và không suy ra một người mắc bệnh thông qua đường đi graph.

Lưu ý về chữ “tạo” trong RAG: bản này **chọn/trích xuất nội dung từ tài liệu**, chưa gọi LLM để viết một bài trả lời mới. LSA cũng là TF–IDF/SVD, chưa phải mô hình embedding neural hiện đại.

Nguồn trên web xác định repository/commit MedQuAD và mã tài liệu/đoạn trong snapshot. Snapshot hiện tại không giữ URL gốc riêng của từng bài; nút nguồn không mặc nhiên mở đúng trang bài viết NIH ban đầu.

## 5. Từng agent làm gì?

“Agent” trong bản này là **vai trò phần mềm được giao nhiệm vụ, có công cụ và quy tắc xử lý riêng**. Không phải mỗi agent là một chatbot hay một mô hình neural được huấn luyện riêng. Đây là hệ điều phối theo luật, chạy không cần LLM/API key.

| Agent | Nhận gì? | Làm gì cụ thể? | Trả gì? |
|---|---|---|---|
| **Coordinator — điều phối** | Chế độ, câu hỏi, hồ sơ | Dựa vào chế độ người dùng chọn để quyết định cần model, truy hồi hay cả hai; kiểm các mẫu yêu cầu ngoài phạm vi | Kế hoạch gọi công cụ hoặc trạng thái từ chối |
| **Risk Agent — mô hình khảo sát** | Hồ sơ 21 trường | Kiểm dữ liệu; nếu hợp lệ thì chuẩn hóa và gọi checkpoint CDC | Điểm/nhãn mô hình; nếu thiếu dữ liệu thì danh sách cần bổ sung |
| **Knowledge Agent — tìm kiến thức** | Câu hỏi và ngôn ngữ | Chuẩn hóa, tìm KB bằng BM25/LSA/graph, gộp thứ hạng, trích nội dung | Trích đoạn trả lời, các đoạn ứng viên, nguồn, đường graph |
| **Verifier — kiểm chứng** | Đầu ra mô hình và tri thức đã lấy | Kiểm số có nhất quán không; citation có khớp văn bản không; trích đoạn có từ khóa chủ đề không; có thể yêu cầu tìm lại một lần | Kết quả kiểm tra; chặn phần không hợp lệ hoặc yêu cầu thêm bằng chứng |
| **Reporter — trình bày** | Kết quả được phép hiển thị và trạng thái lỗi/thiếu | Gom thành các phần rõ ràng, giữ nguyên điểm model, nêu nguồn và phần chưa làm được | Phản hồi cuối có cấu trúc |

Coordinator hiện dựa vào lựa chọn **Chỉ kiến thức / Chỉ mô hình / Kết hợp**, không dùng LLM để tự hiểu mọi ý định từ câu hỏi. Reporter dùng mẫu trình bày, không tự viết lời khuyên y khoa mới.

Verifier hiện dùng kiểm tra số, tính toàn vẹn và luật đối chiếu đoạn/từ khóa. Dòng **“Đã qua kiểm tra pipeline”** chỉ có nghĩa vượt qua các kiểm tra đó, không phải chuyên gia y khoa đã xác nhận nội dung đầy đủ, đúng cho mọi trường hợp.

## 6. P0, P1, P2 là gì? Vì sao phải có ba cách?

**P0/P1/P2 là ba cấu hình tổ chức xử lý cùng một yêu cầu để so sánh vai trò của điều phối và kiểm chứng.**

| Cấu hình | Luồng chính | Câu hỏi mà cách này giúp trả lời |
|---|---|---|
| **P0 — Công cụ độc lập** | Gọi trực tiếp công cụ cần thiết, đóng gói đầu ra | Nếu chỉ gọi model/tìm kiếm trực tiếp thì kết quả ra sao? |
| **P1 — Điều phối + specialists** | Coordinator → Risk/Knowledge theo việc cần làm → đầu ra | Việc chia vai trò và điều phối thể hiện ra sao? |
| **P2 — Kiểm chứng + tổng hợp** | Coordinator → Risk/Knowledge → Verifier → Reporter; có thể tìm lại một lần | Thêm bước kiểm tra và phản hồi có phát hiện/chặn được lỗi không? |

Để so sánh công bằng, cả ba dùng **cùng hồ sơ, câu hỏi, checkpoint và kho kiến thức**. P0 cũng được gọi cả model lẫn tìm kiếm khi chọn Kết hợp; không bị cắt mất một công cụ để làm yếu baseline.

Trong implementation hiện tại, P0/P1 vẫn dùng chung hàm kiểm hồ sơ, công cụ và hàm đóng gói. Vì vậy trace P0 có thể vẫn hiện tên Risk/Knowledge ở bước công cụ, nhưng không có quy trình Verifier/Reporter của P2. P1 và P0 có thể cho đầu ra giống nhau vì công cụ và kế hoạch theo chế độ giống nhau.

**Đừng nhầm hai trục lựa chọn:**

```text
Chỉ kiến thức / Chỉ mô hình / Kết hợp = cần làm VIỆC GÌ?
P0 / P1 / P2                         = tổ chức làm việc đó THEO CÁCH NÀO?
```

P0/P1/P2 không phải Scratch/Keras/PyTorch, không phải ba dataset, cũng không phải ba mức nguy cơ bệnh. Trong project này, cả ba cùng gọi một checkpoint CDC khi cần mô hình.

Nút **“Chạy P0, P1 và P2”** tự gửi cùng đầu vào qua ba cấu hình lần lượt. Sau đó bạn đổi tab P0/P1/P2 để xem từng kết quả.

## 7. Kiến trúc tổng thể

```text
Trình duyệt — React
  Câu hỏi + chế độ + hồ sơ
            │
            ▼
Python / Flask API
  Kiểm request và gói dữ liệu/model sẵn sàng
            │
            ▼
Pipeline của cấu hình được chọn (P0, P1 hoặc P2)
  P2 đầy đủ:
  Coordinator
     │
     ├── Nếu cần mô hình:
     │     Risk Agent → kiểm hồ sơ → chuẩn hóa → checkpoint CDC
     │
     └── Nếu cần kiến thức:
           Knowledge Agent → BM25 + LSA + graph → bằng chứng
     │
     ▼
  Verifier ── nếu bằng chứng chưa đạt → tìm lại tối đa 1 lần
     │
     ▼
  Reporter → kết quả có cấu trúc + trace
            │
            ▼
React hiển thị điểm, kiến thức, nguồn, luồng và bảng so sánh
```

Hai nhánh trong sơ đồ là hai loại nhiệm vụ; code hiện gọi chúng tuần tự trong mỗi yêu cầu, không phải hai process agent chạy song song. Mỗi cấu hình có thời hạn tối đa 30 giây và giới hạn 8 lần thử gọi công cụ. Web gọi ba cấu hình lần lượt.

**Trace** là nhật ký có cấu trúc: agent nào gọi công cụ nào, trạng thái và thời gian. Mục đích là kiểm tra luồng thực thi, không phải hiển thị suy nghĩ nội bộ của AI.

Code đầy đủ nằm trong ba notebook; backend là bản export từ notebook:

1. [01_Data_KB_RAG.ipynb](../project01/notebooks/01_Data_KB_RAG.ipynb): xử lý hồ sơ, mô hình, KB/graph, tìm kiếm và trích xuất.
2. [02_Diabetes_Multi_Agent.ipynb](../project01/notebooks/02_Diabetes_Multi_Agent.ipynb): điều phối, các vai trò, kiểm chứng, giới hạn và API.
3. [03_Evaluation.ipynb](../project01/notebooks/03_Evaluation.ipynb): code chấm điểm, tổng hợp kết quả và biểu đồ.

## 8. Bây giờ demo từng bước như thế nào?

### Bước 0 — Mở ứng dụng

Nếu đang dùng Git Bash, tại root repository chạy:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./project01/scripts/run_web.ps1
```

Nếu đang dùng PowerShell:

```powershell
.\project01\scripts\run_web.ps1
```

Giữ terminal mở, truy cập **http://127.0.0.1:8031**, chờ trạng thái **CPU sẵn sàng**. Ctrl+C trong terminal để dừng sau khi demo.

### Bước 1 — Hiểu nhánh chỉ tìm kiến thức

1. Vào **01 Câu hỏi & hồ sơ**.
2. Bấm **Kiến thức · vận động**. Đọc câu hỏi tiếng Anh vừa được điền; xác nhận chế độ là **Chỉ kiến thức**.
3. Bấm **Chạy P0, P1 và P2**.
4. Tại **02 Kết quả & nguồn**, xem P2, đọc trích đoạn và mở đoạn **Được trích dẫn**.

**Cần quan sát:** có câu trả lời từ tài liệu, query truy hồi và bằng chứng. Phần mô hình không có score vì lần này không yêu cầu chạy model. Đây là hành vi đúng.

**Cách giải thích:** “Em đang minh họa việc lấy bằng chứng cho câu hỏi về vận động và tiểu đường. Nội dung được trích từ kho MedQuAD, không phải mô hình CDC tự viết ra.”

### Bước 2 — Hiểu nhánh chạy cả mô hình và kiến thức

1. Quay lại **01 Câu hỏi & hồ sơ**.
2. Chọn **Kết hợp model + kiến thức**, bấm **Khôi phục mẫu** để có hồ sơ đủ trường.
3. Chạy và xem **02 Kết quả & nguồn**.

**Cần quan sát:** bên mô hình có score/nhãn; bên kiến thức có trích đoạn và nguồn. Hồ sơ mẫu đầu có score khoảng `0.3955`; đây là điểm kiểm tra tham khảo cho mẫu nguyên trạng, không phải mục tiêu phải đạt khi bạn thay hồ sơ.

**Cách giải thích:** “Một yêu cầu gọi hai công cụ khác nhau: checkpoint xử lý hồ sơ số, còn RAG tìm tài liệu theo câu hỏi. Hai kết quả được trình bày cùng nhau.”

### Bước 3 — Xem năm vai trò thật sự làm gì

1. Mở **03 Luồng agent**, chọn **P2**.
2. Đọc lần lượt Coordinator, Risk Agent, Knowledge Agent, Verifier, Reporter.
3. Mở **Kết quả bước xử lý** nếu muốn xem dữ liệu trung gian.
4. Đổi sang P0/P1 để so sánh cách tổ chức bước xử lý.

**Cần quan sát:** P2 có bước kiểm chứng; không phải chỉ thay nhãn P0 thành P2. Nếu bằng chứng đã qua kiểm tra ngay, không cần xuất hiện bước tìm lại; đây là hành vi bình thường.

Ngay tại **02 Kết quả & nguồn**, phần **KHÁC NHAU Ở CÁCH XỬ LÝ** cũng hiển thị các vai trò đã chạy, tiêu chí kiểm chứng và đối chiếu đầu ra của ba cấu hình. Chuyển P0/P1/P2 để xem các khối này thay đổi; mở **Đối chiếu các bước P0 / P1 / P2 của lượt chạy này** để so sánh cùng bảng. Thông tin lấy từ trace thật. Nếu score, trích đoạn và citation giống nhau, phần này sẽ nói rõ chúng giống nhau.

### Bước 4 — Thử thiếu dữ liệu

1. Về phần nhập, giữ chế độ **Kết hợp cả hai**.
2. Xóa giá trị BMI rồi chạy.

**Cần quan sát:** không có điểm mô hình cho hồ sơ thiếu BMI; hệ thống báo thiếu trường. Phần kiến thức vẫn có thể được trả về, nên trạng thái có thể là kết quả một phần. Sau đó bấm **Khôi phục mẫu**.

**Cách giải thích:** “Hệ thống không tự đoán BMI để ép mô hình chạy. Phần nào đủ đầu vào thì làm, phần còn thiếu phải yêu cầu bổ sung.”

### Bước 5 — Đọc bảng so sánh đúng ý nghĩa

Mở **04 So sánh phương pháp**:

- **Bảng trên:** kết quả ba cấu hình của đầu vào vừa demo, gồm trạng thái, score, bằng chứng, số lần gọi công cụ và thời gian.
- **Bảng dưới:** kết quả 40 tình huống đánh giá đã lưu cho mỗi cấu hình, không phải phép đánh giá vừa chạy lại.

Với đầu vào bình thường, P0/P1/P2 có thể trả cùng score và cùng trích đoạn vì dùng cùng công cụ. Điểm khác biệt cần nhìn là bước điều phối/kiểm tra và cách xử lý lỗi, không phải kỳ vọng P2 phải luôn cho số lớn hơn.

Các ca cố ý làm sai citation/score đã có trong benchmark nội bộ; giao diện public không cung cấp nút tiêm lỗi đó. Không cần tạo lỗi giả trên web để demo bước kiểm chứng.

### Bước 6 — Tùy chọn: thử tiếng Việt có giới hạn

Chọn **Tiếng Việt · phạm vi glossary**, chạy rồi nhìn **QUERY ĐƯỢC DÙNG** và dòng ánh xạ. Cụm “bệnh thận” và “tiểu đường” được chuyển thành từ khóa tiếng Anh tương ứng.

Trích đoạn vẫn là tiếng Anh. Đây là từ điển hữu hạn, không chứng minh hệ thống hiểu mọi câu tiếng Việt tự do. Nên dùng tiếng Anh cho lượt trình bày chính.

## 9. Kết quả hiện tại nói lên điều gì?

- Sau chấm nội dung theo rubric, cả P0/P1/P2 đều hoàn thành **33/40 tình huống = 82,5%**.
- P2 vượt qua nhiều kiểm tra tự động hơn nhờ chặn/khôi phục một số lỗi số liệu và citation.
- Tuy nhiên, phần chọn trích đoạn còn có trường hợp thiếu ngữ cảnh hoặc chỉ lấy câu dẫn “Learn more…”. Thêm Verifier chưa làm tỷ lệ hoàn thành cuối cùng tăng lên trong bộ này.
- Việc chấm hỗ trợ nội dung do trợ lý Codex thực hiện theo rubric, chưa có chuyên gia y khoa/nhóm đánh giá độc lập xác nhận.

**82,5% là tỷ lệ hoàn thành tác vụ của pipeline, không phải độ chính xác chẩn đoán tiểu đường.** Thời gian hiển thị là số đo chạy local, không phải hiệu năng Render đã kiểm chứng.

## 10. Những điều cần phân biệt khi trình bày

| Dễ hiểu nhầm | Cách hiểu đúng |
|---|---|
| “Vận động” là một mô hình hoặc dataset mới | Là chủ đề của câu hỏi mẫu |
| P0/P1/P2 là ba loại mạng neural | Là ba cách tổ chức cùng các công cụ |
| Có 5 agent nghĩa là có 5 LLM | Là 5 vai trò phần mềm, baseline không dùng LLM |
| Graph tự suy bệnh và chỉ định thuốc | Graph hiện hỗ trợ tìm đoạn theo chủ đề |
| Model đọc câu hỏi để trả lời kiến thức | Model đọc 21 trường số; Knowledge Agent đọc câu hỏi |
| Score 0,8 nghĩa là chắc chắn 80% mắc bệnh | Là điểm phân loại chưa hiệu chuẩn lâm sàng |
| Verifier passed nghĩa là nội dung đã được bác sĩ xác nhận | Chỉ vượt qua các kiểm tra pipeline hiện có |
| P2 phải luôn trả lời khác hoặc hay hơn P0 | Có thể cùng đầu ra; khác biệt ở bước kiểm tra và xử lý lỗi |

Sau khi nắm các ý trên, bạn có thể trình bày project bằng một câu: **“Em tái sử dụng mô hình khảo sát CDC và kho kiến thức MedQuAD, tổ chức thành hệ nhiều vai trò để chạy mô hình, tìm bằng chứng, kiểm tra và trình bày kết quả; đồng thời so sánh ba cách phối hợp trên cùng đầu vào.”**

Tài liệu đối chiếu: [README project01](../project01/README.md), [báo cáo kết quả và giải thích biểu đồ](../project01/report/Project01_Report.md), [danh mục dữ liệu](../project01/datasets/catalog.json). Tài liệu này chỉ bổ sung hướng dẫn; không thay code, dữ liệu, kết quả đã khóa hoặc tự bắt đầu Phase 3.
