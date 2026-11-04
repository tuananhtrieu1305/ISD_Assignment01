"""Preserve originals, create notebook bootstrap revisions and declare runtime aliases."""
from __future__ import annotations
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/reorganization"
P2=OUT/"phase2"
PROJECTS=["A01","A02","A03","A04","A05","A06","tieuluan1","tieuluan2","tieuluan3","agent01","agent02"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+".migration-tmp")
    temporary.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temporary.replace(path)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def bootstrap(project, framework):
    return f'''# Migration r2: select this assignment's original logical paths, preserving frozen source.
from pathlib import Path as _Path
import sys as _sys
_repo = next(p for p in (_Path.cwd(), *_Path.cwd().parents) if (p / 'ASSIGN_REORGANIZATION_EXECUTION_PLAN.md').exists())
_sys.path.insert(0, str(_repo / '_shared'))
from assignment_runtime import activate as _activate
_migration = _activate({project!r}, {framework!r})
_migration
'''


def main():
    assert load(P2/"relocation_native_complete.json")["status"]=="COMPLETE"
    if (P2/"runtime_view_map.json").exists():
        raise RuntimeError("Setup already declared; inspect existing revisions before rerunning")
    rows=load(P2/"relocation_map_r2.json")["files"]
    revisions=[]
    by_project={p:[] for p in PROJECTS}
    for row in rows:
        canonical=ROOT/row["target"]
        old=row["old_path"]
        project=row["project"]
        if old.endswith(".ipynb") or canonical.name in {"README.md","AGENTS.md"} and canonical.parent==ROOT/project:
            original=ROOT/project/"provenance/originals"/old
            original.parent.mkdir(parents=True,exist_ok=True)
            if not original.exists():
                shutil.copyfile(canonical,original)
            assert sha(original)==row["sha256"]
            row["baseline_path"]=original.relative_to(ROOT).as_posix()
        by_project[project].append(row)
    audit=load(OUT/"notebook_static_audit.json")
    audit_by_sha={r["sha256"]:r for r in audit["notebooks"]}
    for project, items in by_project.items():
        primary=[]
        for row in items:
            if not row["target"].endswith(".ipynb") or not row["target"].startswith(project+"/notebooks/"):
                continue
            target=ROOT/row["target"]
            original=ROOT/row["baseline_path"]
            doc=load(original)
            text="\n".join("".join(c.get("source",[])) for c in doc["cells"] if c["cell_type"]=="code")
            framework="keras" if project=="A05" or project=="A06" and "Keras_" in target.name else "torch"
            newcell={"cell_type":"code","execution_count":None,"metadata":{"migration_revision":"r2"},"outputs":[],"source":bootstrap(project,framework).splitlines(keepends=True),"id":"migration-bootstrap-r2"}
            intro={"cell_type":"markdown","metadata":{},"id":"migration-notes-r2","source":["**Bản đường dẫn r2.** Notebook gốc và output được giữ trong provenance. Kernel: Python3.11 WSL "+("TensorFlow/Keras" if framework=="keras" else "NumPy/PyTorch")+". Không Run All pipeline huấn luyện chỉ để xem kết quả đã lưu.\n"]}
            doc["cells"]=[intro,newcell]+doc["cells"]
            # A05 comparison's executable guard is a local-path check, not model logic.
            if project=="A05":
                for cell in doc["cells"]:
                    if cell["cell_type"]=="code":
                        source="".join(cell.get("source",[]))
                        source=source.replace('Path("C:/Users/anhca/anaconda3/envs/tf312/python.exe")','Path(sys.executable)')
                        cell["source"]=source.splitlines(keepends=True)
            doc["metadata"]["kernelspec"]={"display_name":"Python3.11 WSL "+("Keras-TensorFlow" if framework=="keras" else "NumPy-PyTorch"),"language":"python","name":"python3"}
            doc["metadata"].pop("vscode",None)
            doc["metadata"]["migration"]={"revision":"r2","original_sha256":row["sha256"],"original_path":row["baseline_path"],"project":project,"framework":framework}
            save(target,doc)
            diffpath=ROOT/project/"provenance/notebook_diffs"/(target.name+".diff")
            diffpath.parent.mkdir(parents=True,exist_ok=True)
            diffpath.write_text("".join(difflib.unified_diff(original.read_text(encoding="utf-8").splitlines(keepends=True),target.read_text(encoding="utf-8").splitlines(keepends=True),fromfile=row["baseline_path"],tofile=row["target"])),encoding="utf-8")
            info=audit_by_sha.get(row["sha256"],{})
            descriptor={"path":target.relative_to(ROOT/project).as_posix(),"framework":framework,"role":info.get("role","historical reference"),"mixed_framework":info.get("mixed_tensorflow_torch_imports",False),"original_sha256":row["sha256"],"revision_sha256":sha(target)}
            primary.append(descriptor)
            revisions.append({"project":project,**descriptor,"baseline_path":row["baseline_path"]})
        cwd="A05" if project=="A05" else "A06" if project=="A06" else "."
        config={"project":project,"runtime_root":"provenance/runtime/assign","working_directory":cwd,"default_framework":"keras" if project=="A05" else "torch","datasets_catalog":"datasets/catalog.json","notebooks":primary,"migration_revision":"r2","train_or_TEST_executed_in_migration":False}
        save(ROOT/project/"project.json",config)
    # Own logical aliases are declared from original byte paths, not revised notebooks.
    aliases={}
    def add(project, old, source, digest, size):
        target=f"{project}/provenance/runtime/assign/{old}"
        key=target.casefold()
        record={"project":project,"logical_path":old,"source":source,"target":target,"sha256":digest,"bytes":size}
        if key in aliases:
            assert aliases[key]["sha256"]==digest,(project,old)
        else:
            aliases[key]=record
    for row in rows:
        add(row["project"],row["old_path"],row["baseline_path"],row["sha256"],row["bytes"])
    # Tiểu luận1's original raw/scaler roots are genuinely shared with old assignments.
    for row in rows:
        project=row["project"]
        old=row["old_path"]
        borrow=project in {"A05","A06"} or project=="A03" and (old.startswith("datasets/") or old.startswith("pipeline/"))
        if borrow:
            add("tieuluan1",old,row["baseline_path"],row["sha256"],row["bytes"])
    # The agent assignment records7parent assets. Include only its declared read-only references.
    parent=load(ROOT/"agent02/evidence/phase01/preparation.json")
    parent_paths=set()
    def collect(value):
        if isinstance(value,dict):
            for key,v in value.items():
                if key=="path" and isinstance(v,str) and v.startswith(("data/","artifacts/","uv.lock")):
                    parent_paths.add(v)
                collect(v)
        elif isinstance(value,list):
            for v in value: collect(v)
    collect(parent)
    parent_paths.update(["data/raw/ch4/gold/CMO-Historical-Data-Monthly.xlsx","data/splits/v3/ch4_gold_pink_sheet/split_contract.json"])
    for row in rows:
        if row["project"]=="tieuluan3" and row["old_path"] in parent_paths:
            add("agent02",row["old_path"],row["baseline_path"],row["sha256"],row["bytes"])
    # V3 legacy root marker is used by generator-owned demo notebooks.
    for project in ["tieuluan1","tieuluan3"]:
        if project=="tieuluan1":
            continue
        for row in rows:
            if row["project"]==project and row["old_path"]=="TIEU_LUAN_AI_V3_EXECUTION_PLAN.md":
                add(project,row["old_path"],row["baseline_path"],row["sha256"],row["bytes"])
    save(P2/"canonical_map.json",{"files":rows,"original_paths_preserved":True,"runtime_compatibility_is_generated":True})
    save(P2/"notebook_revisions.json",{"revision":"r2","notebooks":revisions,"full_training_executed":False})
    save(P2/"runtime_view_map_base.json",{"files":list(aliases.values()),"count":len(aliases),"symlink_required":False,"mutable_source_policy":"canonical revisions are atomic replacements; old logical views use immutable original bytes"})
    print(f"Setup: {len(revisions)}notebook revisions; {len(aliases)}base runtime aliases; derived tieuluan2 next")


if __name__=="__main__":
    main()
