# ch6_house_tasks — Giá nhà

100 task synthetic-template trên nguồn thật;60/20/20 theo nhóm. Không phải100 người bệnh/căn nhà mới.

| Parent | Link snapshot | Điều khoản/citation | Raw parent bytes (không copy) |
|---|---|---|---|
| ch2_ames_housing | https://jse.amstat.org/v19n3/decock/AmesHousing.txt | Author-published teaching/research dataset accompanying JSE article; retain attribution; no explicit SPDX license on original TXT. GPL-2 in topepo/AmesHousing applies to that package, not automatically to this original source. Local academic analysis only; no raw redistribution. | 960807 |
| ch4_bis_house_prices | https://data.bis.org/static/bulk/WS_SPP_csv_col.zip | BIS Terms of permitted use of statistics, not CC BY assumed. https://www.bis.org/about/legal/permitted-use-statistics ; attribute BIS and original national sources, label own calculations, do not imply endorsement. No raw redistribution in this repo. | 135216 |

Task set dùng chung3 miền: `artifacts/manifests/phase31/taskset_v2.json`, 401318 byte, SHA-256 `8741c1165c77fe8d67ba262a193ddebdd044b45eebf3a8bc0318255123ee23ab`.
Catalog canonical input/evidence dùng chung:60 record/miền (40 numeric +20 evidence). Không nhân bản raw.

Schema: request(task_id, domain_hint, question, record_id, operation); split/group/source_group/fault/gold chỉ harness. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có20 task, mỗi split12/4/4. Group nguyên template và source/document, overlap0.

| Task | Input câu hỏi (synthetic) | Output số thật từ tool | Trích output tool/evidence |
|---|---|---|---|
| house_numeric_f1_1 | giá nhà: tính đầu ra checkpoint cho bản ghi house_numeric_000. | [118115.72406888881] | Frozen NumPy CPU tool output: 118115.72 |
| house_numeric_f1_2 | giá nhà: tính đầu ra checkpoint cho bản ghi house_numeric_001. | [177813.23670143556] | Frozen NumPy CPU tool output: 177813.24 |
| house_numeric_f1_3 | giá nhà: tính đầu ra checkpoint cho bản ghi house_numeric_002. | [253889.1433285652] | Frozen NumPy CPU tool output: 253889.14 |
| house_evidence_f1_1 | giá nhà: tìm bằng chứng snapshot cho mã house_evidence_000. | [80.8486] | BIS series Q.AT.N.628; TRAIN origin 2004-10-01T00:00:00: 80.8486 index. |
| house_evidence_f1_2 | giá nhà: tìm bằng chứng snapshot cho mã house_evidence_001. | [69.5063] | BIS series Q.AU.N.628; TRAIN origin 2004-10-01T00:00:00: 69.5063 index. |

Không thiếu task/gold. Numeric dùng parent TRAIN; Gold window có thể chồng context. MedQuAD chỉ corpus evidence, không QA TEST label. Policy/challenge là ca tổng hợp đã gắn nhãn, không phân bố nhu cầu thực. Gold numeric parity là khớp tool, không predictive accuracy.

Nhận xét: thiết kế cân bằng thuận tiện kiểm pipeline nhưng nhỏ, rule/ID-bound, không chứng minh hiểu ngôn ngữ tự do. Ames là USD giá bán lịch sử; BIS là chỉ số danh nghĩa2010=100, không so trực tiếp hai đơn vị. CDC probability không phải chẩn đoán; Pink Sheet không phải giá giao dịch hiện tại. Citation hash kiểm local container, URL cấp nguồn.
