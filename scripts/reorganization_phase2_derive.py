"""Derive the five-chapter paper without changing its six-chapter scientific parent."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
P2=ROOT/"docs/reorganization/phase2"
DEST=ROOT/"tieuluan2"


def load(path): return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".migration-tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)


def forbidden(path):
    return bool(re.search(r"ch06_multi_agent|ch06_|ch6_|(^|/)phase31(/|_)|agent_catalog|agent_taskset|agent_tool|/AgentTrace",path))


def main():
    if (P2/"derivation_complete.json").exists(): raise RuntimeError("Derived revision exists; inspect before rerunning")
    base=load(P2/"runtime_view_map_base.json")
    canonical=load(P2/"canonical_map.json")["files"]
    originals={r["old_path"]:r for r in canonical if r["project"]=="tieuluan3"}
    aliases={r["target"].casefold():r for r in base["files"]}
    changes=[]
    own={}

    def add(old,source,digest,size):
        target=f"tieuluan2/provenance/runtime/assign/{old}"
        aliases[target.casefold()]={"project":"tieuluan2","logical_path":old,"source":source,"target":target,"sha256":digest,"bytes":size}

    def own_file(old,target,content=None):
        source=ROOT/originals[old]["baseline_path"]
        path=DEST/target
        path.parent.mkdir(parents=True,exist_ok=True)
        if content is None: shutil.copyfile(source,path)
        else: path.write_text(content,encoding="utf-8")
        entry={"old_path":old,"path":path.relative_to(ROOT).as_posix(),"sha256":sha(path),"bytes":path.stat().st_size,"parent_sha256":originals[old]["sha256"]}
        own[old]=entry
        add(old,entry["path"],entry["sha256"],entry["bytes"])
        return path

    for old,row in originals.items():
        if forbidden(old): continue
        # Historical releases/whole-paper assembly belong exclusively to paper3.
        if old.startswith(("releases/","report/build/","report/qa","artifacts/manifests/phase34/","artifacts/manifests/phase35/","artifacts/manifests/phase31/")):
            continue
        if old.startswith("src/"):
            own_file(old,old)
        elif old.startswith("apps/api/"):
            own_file(old,"web/backend/"+old[len("apps/api/"):])
        elif old.startswith("apps/web/"):
            if "/tests/" in old or ".test." in old or "AgentTrace" in old:
                continue
            own_file(old,"web/frontend/"+old[len("apps/web/"):])
        elif old.startswith("experiments/notebooks/v3/") and not old.startswith("experiments/notebooks/v3/ch04_rnn/"):
            tail=old[len("experiments/notebooks/v3/"):]
            own_file(old,"notebooks/"+tail)
        elif old.startswith("report/sections/v3/") or old.startswith("report/references/"):
            add(old,row["baseline_path"],row["sha256"],row["bytes"])
        else:
            add(old,row["baseline_path"],row["sha256"],row["bytes"])
    # Build catalog/registry revision; drop every task/model/component from chapter6.
    registry_old="artifacts/manifests/phase32/registry_v3.json"
    registry=load(ROOT/originals[registry_old]["baseline_path"])
    registry.pop("agent_catalog",None)
    registry.pop("agent_taskset_sha256",None)
    registry["chapters"]=[r for r in registry["chapters"] if r["chapter"]<=5]
    registry["models"]=[r for r in registry["models"] if r["chapter"]<=5]
    registry["datasets"]=[r for r in registry["datasets"] if r["chapter"]<=5]
    registry["components"]=[r for r in registry["components"] if r["id"]!="agents"]
    registry["files"]=[r for r in registry["files"] if not forbidden(r["path"])]
    for key in ("public_artifacts","runs","result_indexes"):
        value=registry[key]
        if isinstance(value,dict):
            registry[key]={k:v for k,v in value.items() if not forbidden(k) and not isinstance(v,dict) or not forbidden(k) and not forbidden(str(v.get("path",""))) and v.get("chapter",0)<=5 and not str(v.get("dataset_id","")).startswith("ch6_")}
        elif isinstance(value,list):
            registry[key]=[v for v in value if v.get("chapter",0)<=5 and not forbidden(str(v.get("path",""))) and not str(v.get("dataset_id","")).startswith("ch6_")]
    sample_old=registry["samples"]["path"]
    samples=load(ROOT/originals[sample_old]["baseline_path"])
    samples={k:v for k,v in samples.items() if not k.startswith("ch6_")}
    sample_path=DEST/sample_old
    save(sample_path,samples)
    new_sample={"path":sample_old,"sha256":sha(sample_path)}
    registry["samples"]=new_sample
    for row in registry["files"]:
        if row["path"]==sample_old:
            row.update(sha256=new_sample["sha256"],size_bytes=sample_path.stat().st_size)
    for key,value in list(registry["public_artifacts"].items()):
        if value.get("path")==sample_old: registry["public_artifacts"][key]=dict(new_sample)
    add(sample_old,sample_path.relative_to(ROOT).as_posix(),sha(sample_path),sample_path.stat().st_size)
    registry["registry_version"]="reorganization-paper2-r1"
    registry["derivation"]={"parent_registry_sha256":originals[registry_old]["sha256"],"allowed_chapters":[1,2,3,4,5],"models_retrained":0,"historical_TEST_replayed":False}
    registry_path=DEST/registry_old
    save(registry_path,registry)
    add(registry_old,registry_path.relative_to(ROOT).as_posix(),sha(registry_path),registry_path.stat().st_size)
    pin_old="apps/api/v3/pins.py"
    pin=DEST/"web/backend/v3/pins.py"
    pin.write_text('"""Registry pin for the derived five-chapter paper, no change to parent."""\nREGISTRY_SHA256 = '+repr(sha(registry_path))+"\n",encoding="utf-8")
    own[pin_old].update(sha256=sha(pin),bytes=pin.stat().st_size)
    add(pin_old,pin.relative_to(ROOT).as_posix(),sha(pin),pin.stat().st_size)

    # Remove the executable multi-agent branches, not merely their menu entry.
    inference=DEST/"web/backend/v3/inference.py"
    tree=ast.parse(inference.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name=="decode_input":
            for stmt in node.body:
                if isinstance(stmt,ast.If) and ast.unparse(stmt.test)=="request['chapter'] >= 5":
                    stmt.test=ast.parse("request['chapter'] == 5",mode="eval").body
                    body=[]
                    for child in stmt.body:
                        if isinstance(child,ast.If) and ast.unparse(child.test)=="request['chapter'] == 5": body.extend(child.body)
                        else: body.append(child)
                    stmt.body=body
        if isinstance(node,ast.FunctionDef) and node.name=="compare":
            cut=next(i for i,s in enumerate(node.body) if isinstance(s,ast.ImportFrom) and s.module and s.module.startswith("src.ch06_multi_agent"))
            node.body=node.body[:cut]+[ast.Raise(exc=ast.Call(func=ast.Name(id="ValueError",ctx=ast.Load()),args=[ast.Constant("Unsupported chapter in five-chapter paper")],keywords=[]),cause=None)]
    inference.write_text(ast.unparse(ast.fix_missing_locations(tree))+"\n",encoding="utf-8")
    assert "ch06_multi_agent" not in inference.read_text()
    server=DEST/"web/backend/v3/server.py"
    server.write_text(server.read_text().replace("range(1, 7)","range(1, 6)"),encoding="utf-8")
    catalog=DEST/"web/frontend/src/v3/catalog.ts"
    source=catalog.read_text()
    source=re.sub(r'  \{\n    route: "/agents",.*?\n  \},\n',"",source,flags=re.S)
    source="\n".join(line for line in source.splitlines() if not re.match(r"\s*ch6_",line))+"\n"
    assert "multi_agent" not in source and 'chapter: 6' not in source
    catalog.write_text(source,encoding="utf-8")
    runner=DEST/"web/frontend/src/v3/ModelRunner.tsx"
    source=runner.read_text().replace('import AgentTrace from "./AgentTrace";\n',"")
    source=re.sub(r'overview.chapter === 6\s*\? "Tác vụ có record ID \(giữ ID của mẫu\)"\s*:\s*',"",source)
    source=re.sub(r'\{overview.chapter === 6\s*\? "So sánh A0/A1/A2 xác định, không hỏi đáp tự do\."\s*:\s*"Demo compact khác benchmark QA lịch sử; Wikidata chỉ duyệt đồ thị\."\}', '"Demo compact khác benchmark QA lịch sử; Wikidata chỉ duyệt đồ thị."',source)
    source=re.sub(r': overview.chapter === 6\s*\? "So sánh A0 / A1 / A2"\s*:',":",source)
    source=source.replace('{details && overview.chapter === 6 && <AgentTrace details={details} />}','')
    assert "AgentTrace" not in source and "overview.chapter === 6" not in source
    runner.write_text(source,encoding="utf-8")
    app=DEST/"web/frontend/src/v3/App.tsx"
    app.write_text(app.read_text().replace('v3-version">/ 03','v3-version">/ 02'),encoding="utf-8")
    for old,entry in own.items():
        path=ROOT/entry["path"]
        entry.update(sha256=sha(path),bytes=path.stat().st_size)
        add(old,entry["path"],entry["sha256"],entry["bytes"])
        if entry["sha256"]!=entry["parent_sha256"]: changes.append(entry)
    # A simple root marker replaces the six-chapter execution-plan contents in this view.
    marker=DEST/"provenance/legacy_root_marker.md"
    marker.write_text("# Logical root marker for paper2 (chapters1–5 only)\n",encoding="utf-8")
    add("TIEU_LUAN_AI_V3_EXECUTION_PLAN.md",marker.relative_to(ROOT).as_posix(),sha(marker),marker.stat().st_size)
    config=load(DEST/"project.json")
    config["allowed_chapters"]=[1,2,3,4,5]
    config["parent_project"]="tieuluan3"
    config["notebooks"]=[]
    # Own notebook revisions will be bootstrapped to paper2, not imported from paper3.
    from reorganization_phase2_setup import bootstrap
    for old,entry in own.items():
        if not old.endswith(".ipynb"): continue
        path=ROOT/entry["path"]
        original=path.read_bytes()
        backup=DEST/"provenance/originals"/old
        backup.parent.mkdir(parents=True,exist_ok=True)
        backup.write_bytes(original)
        doc=json.loads(original)
        doc["cells"].insert(0,{"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"id":"paper2-bootstrap-r1","source":bootstrap("tieuluan2","torch").splitlines(keepends=True)})
        doc["metadata"]["kernelspec"]={"display_name":"Python3.11 WSL NumPy-PyTorch","language":"python","name":"python3"}
        save(path,doc)
        config["notebooks"].append({"path":path.relative_to(DEST).as_posix(),"framework":"torch","role":"Ch1–5 checkpoint/results demo"})
        # Original logical notebook identity remains the parent's frozen original.
        add(old,backup.relative_to(ROOT).as_posix(),sha(backup),backup.stat().st_size)
    save(DEST/"project.json",config)
    save(DEST/"provenance/derivation.json",{"parent_project":"tieuluan3","parent_head":load(P2/"declaration.json")["head"],"allowed_chapters":[1,2,3,4,5],"registry_sha256":sha(registry_path),"changed_source_files":changes,"models_retrained":False,"scientific_TEST_replayed":False,"reports":"no six-chapter DOCX mislabeled as five-chapter paper"})
    save(P2/"derived_registry_summary.json",{"chapters":len(registry["chapters"]),"datasets":len(registry["datasets"]),"models":len(registry["models"]),"components":len(registry["components"]),"files":len(registry["files"]),"removed_family":"multi_agent","registry_sha256":sha(registry_path)})
    save(P2/"runtime_view_map.json",{"files":list(aliases.values()),"count":len(aliases),"symlinks_required":False,"copy_fallback":True})
    save(P2/"derivation_complete.json",{"status":"COMPLETE","own_source_files":len(own),"changed_files":len(changes),"runtime_aliases":len(aliases),"scientific_evaluation_executed":False})
    print(f"Derived paper2:5chapters/{len(registry['datasets'])}datasets/{len(registry['models'])}model slots;{len(own)}own source files;{len(aliases)}runtime aliases")


if __name__=="__main__": main()
