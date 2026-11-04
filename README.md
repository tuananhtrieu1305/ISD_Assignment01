# Assignment và tiểu luận AI

Repository có 11 bài đã sắp xếp và `project01` đang phát triển. Mỗi bài có `datasets/`, `notebooks/`, `web/`.
Kế hoạch hiện hành: [FINAL và project01, ba phase](FINAL_PROJECT01_EXECUTION_PLAN.md); trạng thái ở [checkpoint FINAL](docs/final_project01/checkpoint.json). [REORG](ASSIGN_REORGANIZATION_EXECUTION_PLAN.md) đã hoàn tất và giữ làm lịch sử.

| Folder | Nội dung | Notebook chính | Nhóm dataset/catalog |
|---|---|---:|---:|
| [A01](A01/README.md) | ML cơ bản – bản A01 | 1 | 2 |
| [A02](A02/README.md) | ML cơ bản – bản A02 | 1 | 3 |
| [A03](A03/README.md) | Ba pipeline DNN | 3 | 3 |
| [A04](A04/README.md) | DNN/CNN đa framework | 3 | 5 |
| [A05](A05/README.md) | CNN | 4 | 3 |
| [A06](A06/README.md) | RNN | 4 | 3 |
| [tieuluan1](tieuluan1/README.md) | Tiểu luận 1 – bốn chương | 3 | 8 |
| [tieuluan2](tieuluan2/README.md) | Tiểu luận 2 – năm chương, dẫn xuất | 4 | 15 |
| [tieuluan3](tieuluan3/README.md) | Tiểu luận 3 – sáu chương | 4 | 18 |
| [agent01](agent01/README.md) | Discovering AI Agent | 1 | 1 |
| [agent02](agent02/README.md) | Agent02 | 1 | 1 |
| [project01](project01/README.md) | Đa agent tiểu đường + KB/KG/RAG — Phase2 hoàn tất | 3, đầy đủ source/output | 2 |

Hai môi trường WSL Ubuntu hiện có được dùng chung: PyTorch/NumPy và Keras/TensorFlow tách riêng. Không nhân bản venv vào từng bài. Xem [kernel, dataset và lệnh chạy](docs/reorganization/phase2_runtime.md), [bản đồ source](docs/repository_manifest.md) và [biên bản Phase2](docs/reorganization/phase2_report.md).

Ví dụ chạy notebook kết quả bằng PowerShell từ root:

```powershell
./scripts/run_assignment.ps1 -Project A04 -Notebook notebooks/01_Tabular_DNN.ipynb -Cpu
./scripts/run_assignment.ps1 -Project agent02 -Notebook notebooks/AG02_Code_and_Results.ipynb -Cpu
```

File đã chạy được lưu mới trong `<bai>/artifacts/notebook_runs/`. Notebook train lịch sử được giữ nguyên nguồn/output trong provenance, có revision đường dẫn; migration không train hoặc mở lại scientific TEST.

`tieuluan2` là bản dẫn xuất Chương1–5 của `tieuluan3`, có RNN–LSTM và Knowledge–RAG, bỏ Chương6. Bản DOCX sáu chương vẫn thuộc `tieuluan3`; không đổi tên thành tiểu luận2.

**Ba phase REORG đã hoàn tất.** 11web đã kiểm local/build/E2E, source trùng đã dọn sau gate. Chạy `./scripts/run_web.ps1 -Project A01` hoặc `-Project tieuluan3`; xem [hướng dẫn11 web](docs/reorganization/phase3_runtime.md). Build React: `./scripts/build_web.ps1 -Project tieuluan3`.

Xem [biên bản Phase3](docs/reorganization/phase3_report.md) và [Settings Render cần đổi một lần](docs/reorganization/render_handoff.md). Chưa commit/push/deploy. Materializer hiện hành sau cleanup: `scripts/materialize_assignment.py`; không dùng riêng recipe/helper Phase2 cũ.

<!-- notebook-inline-v1 -->

**Tổng32 notebook/12 bài, mỗi bài tối đa4 file.** Project01 có full source và output trong3 notebook, web riêng tại http://127.0.0.1:8031; đọc [README project01](project01/README.md). Đọc thêm [hướng dẫn notebook cũ](docs/notebook_revision/v1/README.md) và [biên bản revision](docs/notebook_revision/v1/report.md). Verifier bảo toàn lịch sử: `scripts/verify_final_project01.py`; audit project mới: `project01/scripts/verify_phase2.py`. Handoff REORG/inline-v1 giữ nguyên. Tiểu luận DOCX final và tích hợp case study thuộc FINAL Phase3.
