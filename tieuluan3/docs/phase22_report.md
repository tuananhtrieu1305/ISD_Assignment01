# Biên bản Phase 22 — khóa SRS và hợp đồng V3

Ngày: 2026-10-17. Trạng thái: **COMPLETE**. Đây là nghiệm thu đặc tả và guard,
không phải nghiệm thu các mô hình, API/UI V3 hoặc DOCX cuối cùng.

## Đầu ra đã hoàn thành

- `docs/srs_v3.md`: mục tiêu, actors, phạm vi, invariants, quyền sở hữu, lifecycle,
  API/UI, safety, giới hạn Render và handoff có thể thực hiện.
- `docs/traceability_v3.csv`: **54 yêu cầu** từ thầy/người dùng/chất lượng, mỗi yêu
  cầu có phase, spec artifact, planned artifact và acceptance test. Trạng thái
  implementation tương lai được ghi rõ, không nhận đã hoàn thành từ schema tests.
- `report/outline_v3.json`: sáu chương, ba dataset/benchmark/view mỗi chương;
  page budget và deploy chỉ là mục ngắn cuối Ch2–6.
- `experiments/configs/v3/protocol_v3.json`: target, split, preprocessing, kiến trúc,
  seed/subset/budget, metric, timing, TEST seal, các thông tin phải đo ở phase sau.
- `docs/report_style_v3.md`: lý thuyết cơ bản, ví dụ/sơ đồ trước công thức;
  checklist giải thích ký hiệu, lý do và mapping code; toán mở rộng xuống phụ lục.
- Chín JSON Schemas và chín ví dụ synthetic; OpenAPI 3.1.1 với 16 path thiết kế;
  schema/reference được kiểm tra offline, chưa thêm endpoint vào Flask.
- Bốn ADR, Mermaid architecture diagram và risk register 16 mục.
- `src/common/contracts.py`, `tests/contracts/test_v3_contracts.py`,
  `scripts/verify_phase22.py`: semantic guards, test và content-hash lock.

## Các điểm đã chốt để phase sau không hiểu lệch

1. Scratch = NumPy forward/loss/backward/BPTT/optimizer tự viết, không autograd.
   Keras hiện dùng TensorFlow độc lập, PyTorch là adapter trực tiếp. Không tự đổi backend.
2. MLP 6 Dense; CNN 5 Conv + 2 Dense; RNN/LSTM 3 recurrent + 3 Dense. Pooling,
   normalization, activation, time step và cổng LSTM không được tính để đủ độ sâu.
3. Canonical shape/weights/bias/gate/optimizer convention và cùng subset/budget;
   3 seed × 4 family × 3 dataset × 3 implementation = **108 neural run dự kiến**.
   Số này chưa phải số run đã train. Bảng full-data không trộn với matched-subset.
4. Dataset CDC chốt binary theo bảng biến UCI; Phase 23 phải kiểm raw và license.
   Bank dùng bank-full, bỏ duration cho bài toán trước cuộc gọi. Giữ EuroSAT hợp lý
   như benchmark đối chứng; không thay dataset chỉ vì tên mới.
5. Chuỗi chia theo target time/horizon, transform fit TRAIN, không nội suy tương lai.
   BIS/World Bank latest snapshot được gọi là hindcast, không nhận là real-time forecast.
6. **RNN Phase 28 chỉ validation; TEST RNN/LSTM mở chung ở Phase 29** sau khi khóa
   tất cả configs/seeds. Ch5 giữ seal cũ, run_count=1; không reset sau crash hoặc tuning.
7. Model/run giữ preprocessing/dataset/config/protocol/source hashes. Job run-all
   có cùng input hash; chỉ comparison_valid khi cùng comparison-group hash.
8. React có top-level knowledge tabs + ba dataset subtabs + RNN/LSTM toggle;
   schema/API là hợp đồng cho Phase 32/33, không phải UI mới đã được implement.
9. Render CPU inference phải đo khả năng chạy backend thật; không tự dùng dịch vụ
   trả phí hoặc đổi sang NumPy export rồi ghi là timing TensorFlow/PyTorch.

## Kiểm chứng đã chạy

- TDD: test trước code, quan sát RED vì module chưa có; bổ sung negative tests cho
  safe checkpoint/agent trace/dataset family rồi quan sát các lỗi trước khi sửa.
- **121/121 test PASS**: 75 contract + 31 API + 12 environment + 3 NumPy scratch.
- Coverage `src/common/contracts.py` (statement + branch): **90,27%**, gate ≥80%.
  Đây không phải coverage toàn repository hoặc toàn bộ CLI/frontend.
- Ruff lint và format check: PASS; Python AST/preservation verifier: PASS;
  diff whitespace và secret-pattern scan trong phạm vi thay đổi không phát hiện lỗi.
- Schema meta-validation, chín ví dụ, OpenAPI local-reference audit, 54 requirement
  IDs và ma trận 18 dataset: PASS. Không cài thêm full OpenAPI meta-validator;
  live request/response integration và frontend E2E vẫn thuộc Phase 32/33.
- Khóa **31 file** tại `artifacts/manifests/phase22/spec_lock.json`; tạo khóa lần
  đầu rồi chạy lại verifier không `--lock` thành công. Không tự ghi đè khóa khi spec đổi.
- So hash trực tiếp **7 config và 23 metric file Ch5** với inventory trước dọn: PASS.
  Raw Ch5, V2, predictions TEST được kiểm bằng preservation verifier; TEST không chạy lại.
- `uv.lock` và environment lock hash Phase 21 giữ nguyên; không cài package/env mới.
- Bốn cảnh báo sklearn V2 1.9.1 vs 1.9.0 vẫn như Phase 21, không sửa artifact cũ
  hoặc coi các cảnh báo đó là bằng chứng tương thích tuyệt đối.

Không build frontend/DOCX hoặc chạy lại GPU doctor trong phase này vì không thay
UI, report builder, dependency hay backend model. Không cấu hình static type checker
mới; file Python được lint, parse và test. Không commit/reset hay rewrite Git history.

Skill `product-capability` giúp tách chính sách cố định, quyết định kiến trúc và
những số phải đo; mẫu đi kèm không có trong máy nên dùng cấu trúc SRS của skill.
Các nguyên tắc API/schema-first giúp khóa job/error/backend labels mà không sửa
app sớm; TDD/verification giữ các giới hạn có thể kiểm tra bằng test.

## Evidence và lệnh kiểm tra lại

Evidence: `artifacts/manifests/phase22/{verification.json,spec_lock.json,tests.xml,coverage.json,preservation.json}`.

```powershell
.\scripts\run_experiment.ps1 -Framework torch -Module scripts.verify_phase22
.\scripts\run_experiment.ps1 -Framework torch -Module pytest tests/contracts -q
```

## Handoff Phase 23

Đọc SRS/protocol/outline/registry schema và kiểm khóa đặc tả trước khi tải. Kiểm
dung lượng **host và VHD**, nguồn/license/điều khoản và kích thước giải nén dự kiến.
Sau đó tạo registry/downloader/provenance và manual drop IDRiD nếu cần. Ghi số đo
vào registry/manifests/data cards mới, không sửa ngược file đặc tả đã khóa để chứa
kết quả. Không nhân bản Ch5 raw cho Ch6. Các gate access/metadata/Render được giao
đúng phase, không có câu hỏi sản phẩm đang chặn việc bắt đầu Phase 23.
