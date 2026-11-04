# Phase1 COMPLETE — kiểm kê và phục hồi nguồn

Ngày nghiệm thu:30/10/2026. Kế hoạch: `ASSIGN_REORGANIZATION_EXECUTION_PLAN.md`.

## Kết quả

- Inventory đủ11bài; source A01–A06/tieuluan1 lấy từ full commit SHA lưu trong `source_inventory.json`.
- Đã phục hồi37,786file/2,127,660,479byte (~1.982GiB) vào staging, gồm74file mobile-reference.
- Mỗi file phục hồi được kiểm Git blob identity khi lấy và được đọc lại đối chiếu SHA256 độc lập.
- Sao lưu57file vào ZIP, kiểm hash từng member;52file của hai web-demo còn nguyên, gồm payload ignored và metadata Git riêng.
- Kiểm hash trước/sau: 42,939file source/data/model/metrics/predictions/report hiện hành giữ nguyên.
- Đã static-parse50notebook (30phục hồi,20hiện tại) và128file Python:0lỗi AST,0error-output lịch sử.
- Bản đồ đề xuất80,818file:0xung đột đích. Catalog24nhóm dữ liệu phủ11bài.
- Phân loại notebook train/EDA/fundamentals/results/demo đã lưu. Chưa chạy notebook hoặc model.
- Đã đọc metadata2runtime WSL; không cài package/import framework. Ổ C còn khoảng17.28GiB tại nghiệm thu.

## Nguồn đã có

| Bài | File đã kiểm kê | Notebook chính | Loại nguồn |
|---|---:|---:|---|
| A01 | 66 | 1 | git-restored |
| A02 | 80 | 1 | git-restored |
| A03 | 711 | 3 | git-restored |
| A04 | 938 | 5 | git-restored |
| A05 | 34,574 | 5 | git-restored |
| A06 | 247 | 8 | git-restored |
| tieuluan1 | 1,170 | 3 | git-restored |
| tieuluan2 | 0 | 0 | derived |
| tieuluan3 | 34,882 | 15 | live-preserved |
| agent01 | 113 | 1 | live-preserved |
| agent02 | 8,037 | 1 | live-preserved |

`tieuluan2` có0file ở Phase1 là đúng phạm vi: đây là bản sẽ dẫn xuất ở Phase2, không có commit gốc.
Notebook phụ A01 cũ,3notebook A03 làm dependency của A04 và3RNN-only V3 lịch sử được giữ nhưng
không cộng vào số notebook chính. File current-live không bị nhân bản vào staging.

## Những việc còn phải xử lý ở Phase2

1. CIFAR10 A04 thiếu archive Python-format gốc. Binary archive V3 có sẵn, nhưng khác format/hash.
   Phương án đã ghi trong catalog: tải đúng URL notebook hoặc adapter kiểm parity pixel/label/ID.
   Source A04 đã phục hồi đủ; trạng thái dataset này vẫn `MISSING_ORIGINAL_FORMAT`, không gọi ready-to-run.
2. Torch env không có TensorFlow; Keras env không có Torch. A04 và một số cell fundamentals A06
   import cả hai. Cần wrapper/driver theo framework hoặc revision cell phù hợp, không cài trộn env.
3. Guard Anaconda, root discovery, custom pickle namespace và chênh version sklearn/joblib cần
   native-load/golden-input smoke. Static AST PASS không thay cho chứng minh runtime.
4. Đổi tên agent02 phải giữ namespace `agent02_assignment`; namespace `term_paper` cũng cần alias.
   Dataset trùng tên `diabetes.csv` là nhiều nguồn khác nhau; chỉ dedup khi exact SHA256.
5. Di chuyển11bài theo map; dựng tieuluan2 Ch1–5 và bỏ Ch6 đúng source/UI/API/registry; source Render
   và bundle phải đồng bộ trong phase tích hợp. Không sửa service cloud ở lượt này.

## Bằng chứng và tiếp tục

- `phase1_verification.json`: hash payload, backup, số bài, AST, path conflict và Git diff whitelist.
- `live_preservation_receipt.json`: SHA256 read-only cho42.939file hiện hành.
- `restoration_manifest.json` + `supplementary_manifest.json`: full commit/path/OID/SHA256/kích cỡ.
- `migration_map.json`, `dataset_catalog.json`, `notebook_static_audit.json`: đầu vào Phase2.
- `dependency_audit.md`, `web_matrix.md`, `runtime_matrix.md`: quyết định phụ thuộc và nghiệm thu.
- `phase1_handoff.json`: digest các file bàn giao, không ghi đè khi bắt đầu Phase2.

Không di chuyển/xóa source, không đổi scientific lock, không train/TEST, không chạy web server,
không sửa runtime hoặc Render, không commit/push. Lệnh tiếp theo: **`làm phase 2`**.
