"""Create usable per-project catalogs, namespace maps, READMEs and portable view recipe."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/reorganization"
P2=OUT/"phase2"
PROJECTS=["A01","A02","A03","A04","A05","A06","tieuluan1","tieuluan2","tieuluan3","agent01","agent02"]


def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    temporary=p.with_name(p.name+".migration-tmp")
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temporary.replace(p)


def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()


def atomic_text(p,text):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+".migration-tmp")
    tmp.write_text(text,encoding="utf-8")
    tmp.replace(p)


def main():
    canonical=load(P2/"canonical_map.json")["files"]
    aliases=load(P2/"runtime_view_map.json")["files"]
    alias_index={r["target"].casefold():r for r in aliases}
    by_old={(r["project"],r["old_path"]):r for r in canonical}
    by_staging={r["physical_source"]:r for r in canonical if r.get("source_kind")=="git-restored"}
    # A copied bundle-smoke notebook is evidence, not a primary notebook. Restore its bytes.
    revisions=load(P2/"notebook_revisions.json")
    correction=[]
    valid=[]
    for row in revisions["notebooks"]:
        if not row["path"].startswith("notebooks/"):
            path=ROOT/row["project"]/row["path"]
            tmp=path.with_name(path.name+".restore-original")
            shutil.copyfile(ROOT/row["baseline_path"],tmp)
            tmp.replace(path)
            correction.append({"path":path.relative_to(ROOT).as_posix(),"restored_sha256":sha(path),"reason":"scientific evidence retained original; not a notebook entry point"})
        else: valid.append(row)
    revisions["notebooks"]=valid
    save(P2/"notebook_revisions.json",revisions)
    save(P2/"setup_corrections.json",{"files":correction,"scientific_execution":False})
    # Complete the7 parent paths recorded by AG02; the logical view receives original bytes.
    parent=load(ROOT/"agent02/evidence/phase01/preparation.json")
    for record in parent["preservation_after"]:
        matches=[r for r in canonical if r["old_path"]==record["path"]]
        if not matches: raise RuntimeError("Missing AG02 parent mapping: "+record["path"])
        row=next(r for r in matches if r["sha256"]==record["sha256"])
        target="agent02/provenance/runtime/assign/"+record["path"]
        alias_index[target.casefold()]={"project":"agent02","logical_path":record["path"],"source":row["baseline_path"],"target":target,"sha256":row["sha256"],"bytes":row["bytes"]}
    # Root documentation is a migration revision; old README/AGENTS remain in provenance.
    global_catalog=load(OUT/"dataset_catalog.json")["datasets"]
    for project in PROJECTS:
        config=load(ROOT/project/"project.json")
        config["notebooks"]=[r for r in config["notebooks"] if r["path"].startswith("notebooks/")]
        datasets=[]
        for ordinal,item in enumerate([r for r in global_catalog if r["project"]==project],1):
            if "datasets" in item and project.startswith("tieuluan"):
                for entry in item["datasets"]:
                    original=entry["source_manifest"]["path"]
                    mapping=by_old[("tieuluan3",original)]
                    datasets.append({"dataset_id":entry["dataset_id"],"name":entry["dataset_id"],"chapter":entry["chapter"],"status":"available","files":[{"path":mapping["target"],"sha256":mapping["sha256"],"bytes":mapping["bytes"]}],"storage":"shared immutable V3 raw/splits; original paths via runtime view","source_contract":mapping["target"],"split_policy":"reuse original locked split/scaler; no TEST replay"})
                continue
            files=[]
            for f in item.get("files",[]):
                if f["path"] in by_staging:
                    row=by_staging[f["path"]]
                    path=row["target"]
                else:
                    match=next((r for r in canonical if r["old_path"]==f["path"]),None)
                    path=match["target"] if match else f["path"]
                files.append({"path":path,"sha256":f["sha256"],"bytes":f["bytes"] if "bytes" in f else (ROOT/path).stat().st_size})
            status="available"
            if item.get("availability")=="MISSING_ORIGINAL_FORMAT":
                status="available_binary_adapter"
                f=ROOT/"tieuluan3/datasets/raw/ch3/cifar10/cifar-10-binary.tar.gz"
                files=[{"path":f.relative_to(ROOT).as_posix(),"sha256":sha(f),"bytes":f.stat().st_size}]
            if project=="agent01":
                f=ROOT/"agent01/src/experiment.py"
                files=[{"path":f.relative_to(ROOT).as_posix(),"sha256":sha(f),"bytes":f.stat().st_size}]
            if project=="tieuluan1" and not files:
                # Dataset cards enumerate raw dependencies and exact sizes; include real raw files.
                for r in canonical:
                    if r["project"]=="A03" and r["old_path"].startswith("datasets/") and r["old_path"].endswith(".csv"):
                        files.append({"path":r["target"],"sha256":r["sha256"],"bytes":r["bytes"]})
            datasets.append({"dataset_id":f"{project.lower()}_{ordinal:02}","name":item["dataset"],"status":status,"files":files,"source":item.get("source_reference",item.get("source","see original source cards")),"note":item.get("note",""),"schema":item.get("csv_observations",{}),"split_policy":item.get("split_policy","preserve original experiment state")})
        save(ROOT/project/"datasets/catalog.json",{"project":project,"datasets":datasets,"physical_path_base":"repository root","resolver":"scripts/datasets.py","raw_modified":False})
        atomic_text(ROOT/project/"datasets/README.md",f"# Dataset của {project}\n\nDanh sách, kích cỡ, schema/hash và đường dẫn vật lý: `catalog.json`.\n\nTừ repository root, chạy `scripts/run_assignment.ps1 -Project {project} -ListDatasets` hoặc dùng `scripts/datasets.py`. Dữ liệu dùng chung trỏ đến file thật trong workspace; không yêu cầu symlink/junction. Giữ split/scaler riêng từng bài. Không gọi model trên TEST để kiểm migration.\n")
        save(ROOT/project/"project.json",config)
        lines=["| Notebook | Kernel/framework | Vai trò |","|---|---|---|"]
        for notebook in config["notebooks"]:
            lines.append(f"| `{notebook['path']}` | {notebook['framework']} | {notebook.get('role','reference')} |")
        atomic_text(ROOT/project/"README.md",f"# {project}\n\nSource đã sắp xếp ở revision REORG r2. Ba thư mục chính: `datasets/`, `notebooks/`, `web/`.\n\n- Dataset: `datasets/catalog.json` có đường dẫn thật, hash và schema.\n- Notebook gốc/bằng chứng giữ trong `provenance/originals/`; notebook chính có bootstrap WSL.\n- Kernel Torch: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python`.\n- Kernel Keras: `/home/tuananh/.local/share/ai-term-paper-v3/.venv-keras/bin/python`.\n- Từ `C:\\DATA\\assign`: `.\\scripts\\run_assignment.ps1 -Project {project} -Inspect`.\n- Đường dẫn tương thích trong `provenance/runtime/assign/` được tạo từ manifest; không tự sửa.\n- Không train/TEST lại để xem kết quả. Training notebook chỉ kiểm tĩnh và smoke trên mẫu TRAIN trong migration.\n\n"+"\n".join(lines)+"\n\nWeb source/payload được giữ theo đúng bài; hoàn thiện giao diện/build/Render thuộc Phase3. Không coi checkpoint `initialized_only` là model đã train.\n")
        atomic_text(ROOT/project/"AGENTS.md",f"# Quy tắc {project} sau migration\n\nKế hoạch đang hoạt động: `../ASSIGN_REORGANIZATION_EXECUTION_PLAN.md`; checkpoint ở `../docs/reorganization/checkpoint.json`. User đã cho phép REORG đổi path và dùng runtime WSL hiện có, thay các chỉ dẫn Anaconda/tên folder cũ trong lịch sử. Không train/TEST lại, không cài/nâng dependency hoặc sửa evidence/raw/checkpoint đã khóa.\n\nMã gốc/README/AGENTS và notebook cũ nằm trong provenance, còn `project.json` và README mô tả đường chạy mới. Runtime view là alias được tạo bằng hardlink hoặc copy có kiểm hash, không là bản source được chỉnh độc lập. Sửa code đã khóa cần revision và giữ original.\n\nKhông tự commit/push/deploy. Phần web tích hợp thuộc Phase3; không đổi nội dung/byte báo cáo đã nộp.\n")
    # One TSV feeds the native alias writer without serializing145k PowerShell objects.
    viewrows=list(alias_index.values())
    save(P2/"runtime_view_map.json",{"files":viewrows,"count":len(viewrows),"symlinks_required":False,"copy_fallback":True})
    tsv=P2/"runtime_views.tsv"
    with tsv.open("w",encoding="utf-8",newline="\n") as out:
        for r in viewrows:
            assert all("\t" not in str(r[k]) and "\n" not in str(r[k]) for k in ("source","target","sha256","bytes"))
            out.write(f"{r['source']}\t{r['target']}\t{r['sha256']}\t{r['bytes']}\n")
    print(f"Catalogs/README/AGENTS ready for11projects; {len(viewrows)}runtime aliases; {len(correction)}evidence notebook restored")


if __name__=="__main__": main()
