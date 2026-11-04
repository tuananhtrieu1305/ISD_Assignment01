# Bản đồ repository sau REORG Phase2

Source chính: `A01`–`A06`, `tieuluan1`–`tieuluan3`, `agent01`, `agent02`. Mỗi folder có datasets/catalog, notebooks, web và README. `_shared/assignment_runtime` cùng `scripts/run_assignment.*` là bộ điều phối dùng chung.

| Trước | Sau |
|---|---|
| `src/`, `artifacts/`, `report/`, `experiments/`, `requirements/`, `deploy/`, `releases/`, `tests/` V3 | `tieuluan3/<tên cũ>/` |
| `data/` V3 | `tieuluan3/datasets/` |
| `apps/api/`, `apps/web/` | `tieuluan3/web/backend/`, `tieuluan3/web/frontend/` |
| `scripts/` thí nghiệm V3, docs và plan lịch sử | `tieuluan3/scripts/`, `tieuluan3/docs/`, `tieuluan3/provenance/plans/` |
| `discovering_ai_agent/` | `agent01/`, Python ở src, data ở datasets, web-demo/dist payload ở web |
| `agent02_assignment/` | `agent02/`, Python ở src, data ở datasets, web-demo ở web |
| Assignment cũ từ commit đã khóa | `A01`–`A06`, bản notebook/source gốc ở provenance |
| Tiểu luận1 Git portable-fix | `tieuluan1/` |
| Tiểu luận2 chưa có commit riêng | `tieuluan2/`, revision Ch1–5, parent scientific assets từ tieuluan3 |

Chi tiết từng file và hash: `docs/reorganization/phase2/canonical_map.json` (`baseline_path` là bản gốc); alias có thể tái dựng: `runtime_view_map.json`. Giữ immutable Phase1 handoff và các lock V3/AG02. Không dùng đường dẫn cũ trong biên bản lịch sử làm source canonical mới.

`apps/web/node_modules`, build/cache cũ và staging/backup tạm vẫn giữ cho Phase3 kiểm/dọn theo gate. Không coi chúng là entry point. Root render.yaml và các deploy command cũ chờ Phase3 cập nhật; không deploy ngay từ cấu hình cũ. Nested Git Agent01 được giữ trong provenance/nested_web_metadata, ngoài web payload.

## Sau Phase3

11web đã nghiệm thu; source/cache trùng root apps/dist và staging đã dọn. Service module tiểu luận1 ở src/term_paper/deployment/app. Runtime source overlay hiện hành: docs/reorganization/phase3/runtime_source_overlay.json, materialize_assignment.py. Xem final_inventory.json (manifest hợp thành) và phase3_runtime.md. Root Render phục vụ tiểu luận3; cấu hình mới cần cập nhật Dashboard thủ công một lần. Không còn source cũ hoạt động song song ở root.
