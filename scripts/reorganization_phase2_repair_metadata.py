"""Preserve an original data README before its new catalog-facing presentation revision."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
P2=ROOT/"docs/reorganization/phase2"
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
mapping=load(P2/"canonical_map.json")
views=load(P2/"runtime_view_map.json")
changes=[]
for row in mapping["files"]:
    if row["target"]!=row["project"]+"/datasets/README.md": continue
    target=ROOT/row["target"]
    if hashlib.sha256(target.read_bytes()).hexdigest()==row["sha256"]: continue
    original=ROOT/row["project"]/"provenance/originals"/row["old_path"]
    payload=subprocess.check_output(["git","-C",str(ROOT),"show","HEAD:"+row["old_path"]])
    assert hashlib.sha256(payload).hexdigest()==row["sha256"], "Cannot restore exact original metadata"
    original.parent.mkdir(parents=True,exist_ok=True)
    original.write_bytes(payload)
    old_source=row["baseline_path"]
    row["baseline_path"]=original.relative_to(ROOT).as_posix()
    for alias in views["files"]:
        if alias["source"]==old_source and alias["sha256"]==row["sha256"]:
            alias["source"]=row["baseline_path"]
    changes.append({"old_path":row["old_path"],"original_sha256":row["sha256"],"recovered_from":"HEAD Git blob, exact SHA256 match","baseline_path":row["baseline_path"],"active_presentation":row["target"],"reason":"data README presentation was changed before separate preservation; view verifier refused it; original restored before any model execution"})
save(P2/"canonical_map.json",mapping)
save(P2/"runtime_view_map.json",views)
with (P2/"runtime_views.tsv").open("w",encoding="utf-8",newline="\n") as out:
    for row in views["files"]:
        out.write(f"{row['source']}\t{row['target']}\t{row['sha256']}\t{row['bytes']}\n")
save(P2/"metadata_preservation_correction.json",{"files":changes,"original_bytes_recovered":True,"scientific_execution":False})
print(f"Metadata original recovered/verified: {len(changes)}file")
