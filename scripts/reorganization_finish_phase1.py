"""Finalize the Phase1 handoff only after independent payload and live hash checks."""
from __future__ import annotations
import ast
import collections
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/reorganization"


def read(name):
    return json.loads((OUT/name).read_text(encoding="utf-8-sig"))


def write(name, doc):
    (OUT/name).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def role(row):
    path = row["path"]
    name = Path(path).name.lower()
    if "discovering_ai_agent/notebooks/" in path:
        return "actual Q-learning training and plots; do not RunAll during migration"
    if "agent02_assignment/notebooks/" in path:
        return "read-only sealed results/source/figures, no training"
    if "experiments/notebooks/v3/" in path:
        return "checkpoint/results demo, not original training runner"
    if "comparison" in name:
        return "read saved comparisons/results; inspect guard/write behavior before RunAll"
    if "fundamentals" in name:
        return "fundamentals and toy/data demonstrations"
    if "_data.ipynb" in name:
        return "EDA and preprocessing"
    return "historical training/evaluation pipeline; static check only"


def main():
    for script in (ROOT / "scripts").glob("reorganization_*.py"):
        ast.parse(script.read_text(encoding="utf-8-sig"))
    verification = read("phase1_verification.json")
    preservation = read("live_preservation_receipt.json")
    assert verification["status"] == preservation["status"] == "PASS"
    assert verification["failures"] == [] and preservation["mismatches"] == []
    cp = read("checkpoint.json")
    assert cp["phases"]["1"]["status"] == "IN_PROGRESS", "Already finalized or wrong phase"
    inventory = read("source_inventory.json")
    audit = read("notebook_static_audit.json")
    for row in audit["notebooks"]:
        row["role"] = role(row)
        row["mixed_tensorflow_torch_imports"] = {"tensorflow", "torch"}.issubset(row["imports"])
        row["primary_notebook"] = not ("/A04/pipeline/" in row["path"] or "/A01/Assignment01_" in row["path"] or "experiments/notebooks/v3/ch04_rnn/" in row["path"])
    write("notebook_static_audit.json", audit)
    by_path = {r["path"]: r for r in audit["notebooks"]}
    for project in inventory["projects"]:
        project["notebooks"] = [by_path[r["path"]] for r in project["notebooks"]]
        project["primary_notebook_count"] = sum(r["primary_notebook"] for r in project["notebooks"])
    inventory["phase1_source_inventory_status"] = "COMPLETE"
    inventory["runtime_acceptance_status"] = "NOT_STARTED_PHASE2"
    write("source_inventory.json", inventory)
    restores = read("restoration_manifest.json")["files"] + read("supplementary_manifest.json")["files"]
    groups = collections.defaultdict(list)
    for row in restores:
        path = row["path"]
        if "/datasets/" in path or path.startswith("datasets/") or path in {"diabetes.csv", "vietnam_housing_dataset.csv"}:
            groups[row["sha256"]].append(row)
    candidates = []
    for sha, rows in groups.items():
        if len({r["project"] for r in rows}) > 1:
            candidates.append({"sha256": sha, "bytes_each": rows[0]["bytes"], "copies": [{"project": r["project"], "staging_path": r["staging_path"]} for r in rows], "action": "Phase2 may share physical bytes; keep each project's split/preprocessor separate"})
    write("dataset_dedup_candidates.json", {"groups": candidates, "rule": "exact SHA256 only; same filename or same dataset name is not enough", "dedup_applied": False})
    project_lines = []
    for item in inventory["projects"]:
        count = item["primary_notebook_count"]
        project_lines.append(f"| {item['project']} | {item['file_count']:,} | {count} | {item['source_kind']} |")
    free = shutil.disk_usage(ROOT).free
    report = f"""# Phase1 COMPLETE — kiểm kê và phục hồi nguồn

Ngày nghiệm thu:30/10/2026. Kế hoạch: `ASSIGN_REORGANIZATION_EXECUTION_PLAN.md`.

## Kết quả

- Inventory đủ11bài; source A01–A06/tieuluan1 lấy từ full commit SHA lưu trong `source_inventory.json`.
- Đã phục hồi{inventory['restored_files']:,}file/{inventory['restored_bytes']:,}byte (~{inventory['restored_bytes']/1024**3:.3f}GiB) vào staging, gồm74file mobile-reference.
- Mỗi file phục hồi được kiểm Git blob identity khi lấy và được đọc lại đối chiếu SHA256 độc lập.
- Sao lưu57file vào ZIP, kiểm hash từng member;{verification['uncommitted_web_files_unchanged']}file của hai web-demo còn nguyên, gồm payload ignored và metadata Git riêng.
- Kiểm hash trước/sau: {preservation['file_count']:,}file source/data/model/metrics/predictions/report hiện hành giữ nguyên.
- Đã static-parse{audit['notebook_count']}notebook ({audit['restored_notebook_count']}phục hồi,20hiện tại) và{audit['python_source_count']}file Python:0lỗi AST,0error-output lịch sử.
- Bản đồ đề xuất{verification['mapped_file_count']:,}file:0xung đột đích. Catalog24nhóm dữ liệu phủ11bài.
- Phân loại notebook train/EDA/fundamentals/results/demo đã lưu. Chưa chạy notebook hoặc model.
- Đã đọc metadata2runtime WSL; không cài package/import framework. Ổ C còn khoảng{free/1024**3:.2f}GiB tại nghiệm thu.

## Nguồn đã có

| Bài | File đã kiểm kê | Notebook chính | Loại nguồn |
|---|---:|---:|---|
{chr(10).join(project_lines)}

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
"""
    (OUT / "phase1_report.md").write_text(report, encoding="utf-8")
    handoff_names = ["source_inventory.json", "migration_map.json", "dataset_catalog.json", "dataset_dedup_candidates.json", "notebook_static_audit.json", "restoration_manifest.json", "supplementary_manifest.json", "backup_manifest.json", "live_baseline_manifest.json", "live_preservation_receipt.json", "phase1_verification.json", "selection.json", "phase1_preflight.json", "runtime_torch_metadata.json", "runtime_keras_metadata.json", "web_matrix.md", "runtime_matrix.md", "dependency_audit.md", "phase1_report.md"]
    write("phase1_handoff.json", {"status": "COMPLETE", "date": "2026-10-30", "files": [{"path": "docs/reorganization/"+name, "sha256": digest(OUT/name), "bytes": (OUT/name).stat().st_size} for name in handoff_names], "staging_and_backup": "local ignored payloads; use restoration/backup manifests for per-file hashes", "next_phase": 2, "mutable_control_files_excluded": ["checkpoint.json", "ASSIGN_REORGANIZATION_EXECUTION_PLAN.md", "AGENTS.md", "README.md"], "change_policy": "Phase2 creates new revision for changes to handoff manifests; do not rewrite Phase1 evidence"})
    cp.update(status="IN_PROGRESS", active_phase=None, next_phase=2, completed_phases=[1], last_action="Phase1 COMPLETE: historical payload restored/hash-verified,11-project map and dataset/runtime/web catalogs ready; current source unchanged.", next_action="Await user request: làm phase 2. Read plan/checkpoint/handoff and dependency audit; perform relocation and compatibility revisions.", active_processes=[])
    cp["phases"]["1"].update(status="COMPLETE", report="docs/reorganization/phase1_report.md", evidence="docs/reorganization/phase1_handoff.json")
    write("checkpoint.json", cp)
    print(json.dumps({"phase": 1, "status": "COMPLETE", "restored_files": inventory["restored_files"], "preserved_live_files": preservation["file_count"], "next_phase": 2}, ensure_ascii=False))


if __name__ == "__main__":
    main()
