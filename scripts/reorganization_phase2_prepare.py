"""Declare a reversible relocation revision; no model or notebook execution."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/reorganization"
P2 = OUT / "phase2"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cp = load(OUT/"checkpoint.json")
    assert cp["phases"]["1"]["status"] == "COMPLETE"
    if (P2/"declaration.json").exists():
        raise RuntimeError("Phase2 already declared; inspect checkpoint/journal before resuming")
    handoff = load(OUT/"phase1_handoff.json")
    for row in handoff["files"]:
        assert sha(ROOT/row["path"]) == row["sha256"], row["path"]
    free = shutil.disk_usage(ROOT).free
    assert free > 8*1024**3
    mapped = load(OUT/"migration_map.json")["files"]
    bulk = []
    for name in ["src","artifacts","report","releases","requirements","deploy","experiments","term_paper","tests"]:
        bulk.append({"source":name,"target":"tieuluan3/"+name})
    bulk += [{"source":"data","target":"tieuluan3/datasets"}, {"source":"apps/web","target":"tieuluan3/web/frontend"}, {"source":"apps/api","target":"tieuluan3/web/backend"}, {"source":"discovering_ai_agent","target":"agent01"}, {"source":"agent02_assignment","target":"agent02"}]
    for p in sorted((ROOT/"docs").iterdir()):
        if p.name != "reorganization" and p.is_dir():
            bulk.append({"source":p.relative_to(ROOT).as_posix(),"target":"tieuluan3/"+p.relative_to(ROOT).as_posix()})

    def physical_after_bulk(old):
        matches=[r for r in bulk if old == r["source"] or old.startswith(r["source"]+"/")]
        if not matches:
            return old
        row=max(matches,key=lambda r:len(r["source"]))
        return row["target"]+old[len(row["source"]):]

    transfers=[]
    for row in mapped:
        source=row["physical_source"]
        if row["source_kind"] != "git-restored":
            source=physical_after_bulk(source)
        target=row["new_path"]
        transfers.append({**row,"source_after_bulk":source,"target":target,"operation":"link_or_copy" if row["source_kind"]=="git-restored" else "move", "baseline_path":target})
    for p in sorted((ROOT/"scripts").iterdir()):
        if p.is_file() and not p.name.startswith("reorganization_"):
            if not any(r["old_path"] == p.relative_to(ROOT).as_posix() and r["project"]=="tieuluan3" for r in transfers):
                transfers.append({"project":"tieuluan3","source_kind":"live-extra","old_path":p.relative_to(ROOT).as_posix(),"source_after_bulk":p.relative_to(ROOT).as_posix(),"target":"tieuluan3/scripts/"+p.name,"baseline_path":"tieuluan3/scripts/"+p.name,"operation":"move","sha256":sha(p),"bytes":p.stat().st_size})
    for name in ["TIEU_LUAN_AI_V3_EXECUTION_PLAN.md","TIEU_LUAN_AI_EXECUTION_PLAN.md","CHUONG_5_KNOWLEDGE_RAG_EXECUTION_PLAN.md"]:
        p=ROOT/name
        transfers.append({"project":"tieuluan3","source_kind":"live-extra","old_path":name,"source_after_bulk":name,"target":"tieuluan3/provenance/plans/"+name,"baseline_path":"tieuluan3/provenance/plans/"+name,"operation":"move","sha256":sha(p),"bytes":p.stat().st_size})
    # Root project metadata is a common entry point; preserve it at root and copy to V3.
    for row in transfers:
        if row["old_path"] in {"pyproject.toml","uv.lock",".python-version","render.yaml"} and row["project"]=="tieuluan3":
            row["operation"]="copy"
    save(P2/"relocation_map_r2.json",{"revision":"r2","files":transfers,"bulk_directory_moves":bulk,"phase1_map_sha256":sha(OUT/"migration_map.json"),"runtime_view_policy":"portable materialized logical layout; hardlinks when available, verified byte copies otherwise; no junction or symlink required; views are generated compatibility aliases, not independently edited source"})
    save(P2/"declaration.json",{"status":"DECLARED","date":"2026-10-30","head":subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip(),"phase1_handoff_sha256":sha(OUT/"phase1_handoff.json"),"free_bytes_before":free,"projects":cp["target_projects"],"map_revision":"r2","reason":"Canonical layout follows Phase1 map. Generate an original logical runtime layout to preserve frozen module identity/path/hash without editing scientific source. Notebook path bootstrap and derived five-chapter paper are separate revisions.","tolerances":{"legacy_sklearn_predictions_absolute":1e-6,"native_framework_roundtrip_absolute":1e-5,"cpu_export_parity":"use each existing receipt original tolerance, never loosen"},"training_allowed":False,"scientific_TEST_forward_allowed":False,"dependency_installation_allowed":False,"cloud_deploy_allowed":False})
    cp.update(status="IN_PROGRESS",active_phase=2,next_phase=2,migration_started=True,last_action="Phase2 declared, Phase1 handoff verified; relocation map r2 ready.",next_action="Run native journaled relocation; generate logical compatibility views and notebook revisions.")
    cp["phases"]["2"]["status"]="IN_PROGRESS"
    save(OUT/"checkpoint.json",cp)
    print(f"Phase2 declared: {len(transfers)} file mappings, {len(bulk)} bulk moves, free {free/1024**3:.2f}GiB")


if __name__=="__main__":
    main()
