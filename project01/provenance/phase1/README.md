# Project01 — hệ đa agent cho tiểu đường

Project riêng phát triển từ phần KB/KG/RAG và model CDC của tiểu luận3. Trạng thái hiện tại: **Phase 1 — nền dữ liệu và thiết kế**. Agent end-to-end, web và bảng so sánh sẽ được thực hiện ở Phase 2; chưa có kết quả evaluation mới.

Ba thư mục chính: `datasets/`, `notebooks/`, `web/`. Có thêm `docs/`, `scripts/`, `artifacts/`, `report/`, `tests/` khi cần. Không chứa venv hoặc bản sao raw lớn.

| Notebook | Vai trò hiện tại |
|---|---|
| [01_Data_KB_RAG.ipynb](notebooks/01_Data_KB_RAG.ipynb) | Chạy kiểm hash/schema, load model, forward một mẫu TRAIN, load index/corpus/graph và probe query/ngôn ngữ |
| [02_Diabetes_Multi_Agent.ipynb](notebooks/02_Diabetes_Multi_Agent.ipynb) | Khung cho implementation agent Phase 2, chưa có code agent hoặc kết quả mới |
| [03_Evaluation.ipynb](notebooks/03_Evaluation.ipynb) | Khung evaluator Phase 2, chưa chạy evaluation |

Phase 2 phải bổ sung implementation thuật toán đầy đủ trong cell, rồi export một chiều cho backend; không dùng các notebook khung này để nhận là project hoàn chỉnh. Toàn bộ cây notebooks luôn tối đa 4 file. Notebook chạy mới nằm ở `artifacts/notebook_runs/`.

## Chạy nền hiện có

Từ root `C:\DATA\assign` trong PowerShell:

```powershell
./project01/scripts/run.ps1 -Inspect
./project01/scripts/run.ps1 -Probe
./project01/scripts/run.ps1 -Notebook 01_Data_KB_RAG.ipynb
```

Runner riêng dùng WSL **Ubuntu**, user `tuananh`, `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`. Nó không sửa runner/config của 11 bài cũ, không cài dependency, không dùng GPU train. Trong VS Code mở repository qua WSL và chọn interpreter này; mỗi bài dùng kernel mới.

Mẫu số liệu đã kiểm: CDC 253.680 dòng/21 feature; model scratch seed42 với 6 Dense. MedQuAD snapshot có 762 chunk, 247 document và 62 concept anchor. Chi tiết nguồn/path/hash: [catalog](datasets/catalog.json), [assets](datasets/assets.json), [data card](docs/data_sources.md).

Hồ sơ dùng mã đúng dataset: `age` là nhóm 1–13, không phải số tuổi; nhãn dương gộp **prediabetes or diabetes**. Score model có class weights không phải xác suất mắc bệnh tương lai đã hiệu chuẩn. Thiếu trường thì pipeline Phase 2 phải yêu cầu bổ sung, không tự điền median để giả đủ dữ liệu.

Corpus và trích đoạn trả lời là tiếng Anh. Probe cho thấy truy hồi tiếng Việt trực tiếp lệch so với query tiếng Anh; từ điển cụm từ hữu hạn khắc phục ba ví dụ đã thử. UI Phase 2 sẽ là tiếng Việt, cho xem query đã ánh xạ và đoạn tiếng Anh, không nhận là hiểu tiếng Việt tự do hay dịch máy hoàn chỉnh. Xem [quyết định ngôn ngữ](docs/language_scope.md).

## Thiết kế và bằng chứng

- [Kiến trúc và hợp các hàm](docs/architecture.md).
- [Protocol đánh giá 20 development / 40 evaluation mới](docs/evaluation_protocol.md).
- [Kế hoạch đang hoạt động](../FINAL_PROJECT01_EXECUTION_PLAN.md), [checkpoint](../docs/final_project01/checkpoint.json).
- [Probe kernel thật](artifacts/phase1/probe.json), [biên bản Phase 1](../docs/final_project01/phase1_report.md).

Tài nguyên hiện tham chiếu file canonical trong `tieuluan3`. Sao chép riêng thư mục project01 chưa mang theo raw/model/index. Phase 2 thêm packaging medical-only và source export; không tải joblib từ URL/user upload. Chỉ deserialize artifact local đã kiểm đúng SHA-256.

Các phần web hiện là thư mục chuẩn bị, chưa có server/UI chạy được. Cấu hình Render và hướng dẫn deploy thuộc Phase 2; chưa deploy online.
