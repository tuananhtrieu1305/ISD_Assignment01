# ch6_diabetes_tasks — Tiểu đường

100 task synthetic-template trên nguồn thật;60/20/20 theo nhóm. Không phải100 người bệnh/căn nhà mới.

| Parent | Link snapshot | Điều khoản/citation | Raw parent bytes (không copy) |
|---|---|---|---|
| ch2_cdc_diabetes | https://archive.ics.uci.edu/static/public/891/data.csv | UCI directs licensing to upstream Kaggle; public Kaggle API confirms CC0: Public Domain. https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset . Not assumed to inherit UCI's default CC BY license. | 13494568 |
| ch5_medquad_diabetes | https://github.com/abachaa/MedQuAD | CC BY 4.0; original license evidence and bytes preserved; do not re-download. Follow original restrictions and source attribution. Some copyrighted upstream answers were removed by MedQuAD; empty answers must not be reconstructed from another source. | 37183352 |

Task set dùng chung3 miền: `artifacts/manifests/phase31/taskset_v2.json`, 401318 byte, SHA-256 `8741c1165c77fe8d67ba262a193ddebdd044b45eebf3a8bc0318255123ee23ab`.
Catalog canonical input/evidence dùng chung:60 record/miền (40 numeric +20 evidence). Không nhân bản raw.

Schema: request(task_id, domain_hint, question, record_id, operation); split/group/source_group/fault/gold chỉ harness. Mỗi loại numeric/evidence/OOD/unsafe/tool_failure có20 task, mỗi split12/4/4. Group nguyên template và source/document, overlap0.

| Task | Input câu hỏi (synthetic) | Output số thật từ tool | Trích output tool/evidence |
|---|---|---|---|
| diabetes_numeric_f1_1 | tiểu đường: tính đầu ra checkpoint cho bản ghi diabetes_numeric_000. | [0.25386870685992713] | Frozen NumPy CPU tool output: 0.25386871 |
| diabetes_numeric_f1_2 | tiểu đường: tính đầu ra checkpoint cho bản ghi diabetes_numeric_001. | [0.18886305152266863] | Frozen NumPy CPU tool output: 0.18886305 |
| diabetes_numeric_f1_3 | tiểu đường: tính đầu ra checkpoint cho bản ghi diabetes_numeric_002. | [0.5895465273834898] | Frozen NumPy CPU tool output: 0.58954653 |
| diabetes_evidence_f1_1 | tiểu đường: tìm bằng chứng snapshot cho mã diabetes_evidence_000. | [] | - If you have diabetes, you are at least twice as likely as other people to have heart disease or a stroke. - Controlling the ABCs of diabetesA1C (blood glucose |
| diabetes_evidence_f1_2 | tiểu đường: tìm bằng chứng snapshot cho mã diabetes_evidence_001. | [] | are key to a healthy diet. Make healthy food choices. What you eat has a big impact on your weight and overall health. By developing healthy eating habits you c |

Không thiếu task/gold. Numeric dùng parent TRAIN; Gold window có thể chồng context. MedQuAD chỉ corpus evidence, không QA TEST label. Policy/challenge là ca tổng hợp đã gắn nhãn, không phân bố nhu cầu thực. Gold numeric parity là khớp tool, không predictive accuracy.

Nhận xét: thiết kế cân bằng thuận tiện kiểm pipeline nhưng nhỏ, rule/ID-bound, không chứng minh hiểu ngôn ngữ tự do. Ames là USD giá bán lịch sử; BIS là chỉ số danh nghĩa2010=100, không so trực tiếp hai đơn vị. CDC probability không phải chẩn đoán; Pink Sheet không phải giá giao dịch hiện tại. Citation hash kiểm local container, URL cấp nguồn.
