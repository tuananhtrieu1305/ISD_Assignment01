# ch6_gold_tasks — Giá vàng

100 task synthetic-template trên nguồn thật;60/20/20 theo nhóm. Không phải100 người bệnh/căn nhà mới.

| Parent | Link snapshot | Điều khoản/citation | Raw parent bytes (không copy) |
|---|---|---|---|
| ch4_gold_pink_sheet | https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx | World Bank Commodity Prices - History and Projections catalog: CC BY 4.0. https://datacatalog.worldbank.org/search/dataset/0038238/commodity-prices-history-and-projections . Attribute World Bank and preserve unit/source notes. Not a real-time vintage. | 586099 |

Task set dùng chung3 miền: `artifacts/manifests/phase31/taskset_v2.json`, 401318 byte, SHA-256 `8741c1165c77fe8d67ba262a193ddebdd044b45eebf3a8bc0318255123ee23ab`.
Catalog canonical input/evidence dùng chung:60 record/miền (40 numeric +20 evidence). Không nhân bản raw.

Schema: request(task_id, domain_hint, question, record_id, operation); split/group/source_group/fault/gold chỉ harness. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có20 task, mỗi split12/4/4. Group nguyên template và source/document, overlap0.

| Task | Input câu hỏi (synthetic) | Output số thật từ tool | Trích output tool/evidence |
|---|---|---|---|
| gold_numeric_f1_1 | giá vàng: tính đầu ra checkpoint cho bản ghi gold_numeric_000. | [34.041584925525314, 32.72447998441302, 35.20187368605272] | Frozen NumPy CPU tool output: 34.041585, 32.72448, 35.201874 |
| gold_numeric_f1_2 | giá vàng: tính đầu ra checkpoint cho bản ghi gold_numeric_001. | [34.118522988282535, 32.64269480383689, 35.25670174007024] | Frozen NumPy CPU tool output: 34.118523, 32.642695, 35.256702 |
| gold_numeric_f1_3 | giá vàng: tính đầu ra checkpoint cho bản ghi gold_numeric_002. | [34.12954819479691, 32.675810153854, 35.27241514250787] | Frozen NumPy CPU tool output: 34.129548, 32.67581, 35.272415 |
| gold_evidence_f1_1 | giá vàng: tìm bằng chứng snapshot cho mã gold_evidence_000. | [35.0] | TRAIN origin 1965-04-01T00:00:00: 35 USD/troy oz. |
| gold_evidence_f1_2 | giá vàng: tìm bằng chứng snapshot cho mã gold_evidence_001. | [35.0] | TRAIN origin 1965-05-01T00:00:00: 35 USD/troy oz. |

Không thiếu task/gold. Numeric dùng parent TRAIN; Gold window có thể chồng context. MedQuAD chỉ corpus evidence, không QA TEST label. Policy/challenge là ca tổng hợp đã gắn nhãn, không phân bố nhu cầu thực. Gold numeric parity là khớp tool, không predictive accuracy.

Nhận xét: thiết kế cân bằng thuận tiện kiểm pipeline nhưng nhỏ, rule/ID-bound, không chứng minh hiểu ngôn ngữ tự do. Ames là USD giá bán lịch sử; BIS là chỉ số danh nghĩa2010=100, không so trực tiếp hai đơn vị. CDC probability không phải chẩn đoán; Pink Sheet không phải giá giao dịch hiện tại. Citation hash kiểm local container, URL cấp nguồn.
