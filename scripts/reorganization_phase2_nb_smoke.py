"""Run only readers, TRAIN demo notebooks and guarded dry-run variants, one kernel at a time."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
P2=ROOT/"docs/reorganization/phase2"
PROJECTS=["A01","A02","A03","A04","A05","A06","tieuluan1","tieuluan2","tieuluan3","agent01","agent02"]


def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",action="append",choices=PROJECTS)
    args=parser.parse_args()
    log=P2/"notebook_execution_journal.jsonl"
    previous=[]
    if log.exists(): previous=[json.loads(line) for line in log.read_text().splitlines() if line]
    completed={(r["project"],r["path"],r["input_sha256"]):r for r in previous if r["status"]=="PASS"}
    rows=[]
    for project in args.project or PROJECTS:
        config=load(ROOT/project/"project.json")
        for entry in config["notebooks"]:
            path=ROOT/project/entry["path"]
            role=entry.get("role","").lower()
            allowed=(project in {"tieuluan1","tieuluan2","tieuluan3","agent02"} or project=="A04" or project=="A05" and ("comparison" in path.name.lower() or "fundamentals" in path.name.lower()) or project=="A06" and "fundamentals" in path.name.lower())
            record={"project":project,"path":entry["path"],"framework":entry["framework"],"input_sha256":sha(path),"role":role,"training_executed":False,"scientific_TEST_forward":False}
            if not allowed:
                record.update(status="STATIC_AND_MODEL_SMOKE_ONLY",reason="historical training/EDA; no full RunAll authorized or necessary for migration")
                rows.append(record)
                continue
            doc=load(path)
            for cell in doc["cells"]:
                if cell["cell_type"]=="code": ast.parse("".join(cell["source"]))
            if project=="A04" and "/training/" in entry["path"]:
                assignments=[node for cell in doc["cells"] if cell["cell_type"]=="code" for node in ast.parse("".join(cell["source"])).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="RUN_TRAINING" for t in node.targets)]
                assert assignments and all(isinstance(n.value,ast.Constant) and n.value.value is False for n in assignments)
            key=(project,entry["path"],record["input_sha256"])
            if key in completed:
                record.update(completed[key])
                record["reused"]=True
                rows.append(record)
                print("REUSE",project,entry["path"],flush=True)
                continue
            # Reuse the already completed AG02 notebook from the manually verified runner.
            existing=sorted((ROOT/project/"notebooks/executed").glob(path.stem+"-*.ipynb")) if project=="agent02" else []
            if existing:
                executed=load(existing[-1])
                cells=[c for c in executed["cells"] if c["cell_type"]=="code"]
                assert all(c["execution_count"] is not None for c in cells)
                assert not any(o.get("output_type")=="error" for c in cells for o in c.get("outputs",[]))
                record.update(status="PASS",output=existing[-1].relative_to(ROOT).as_posix(),code_cells=len(cells),reused=True)
            else:
                started=time.monotonic()
                process=subprocess.run(["bash",str(ROOT/"scripts/run_assignment.sh"),entry["framework"],"--project",project,"--cpu","--notebook",entry["path"]],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=360,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
                record.update(status="PASS" if process.returncode==0 else "FAIL",elapsed_seconds=time.monotonic()-started,return_code=process.returncode,stdout=process.stdout[-5000:],stderr=process.stderr[-12000:])
                if process.returncode==0:
                    out=next(Path(line) for line in reversed(process.stdout.splitlines()) if line.endswith(".ipynb"))
                    executed=load(out)
                    cells=[c for c in executed["cells"] if c["cell_type"]=="code"]
                    assert all(c["execution_count"] is not None for c in cells)
                    assert not any(o.get("output_type")=="error" for c in cells for o in c.get("outputs",[]))
                    record.update(output=out.relative_to(ROOT).as_posix(),code_cells=len(cells))
            with log.open("a",encoding="utf-8") as handle: handle.write(json.dumps(record,ensure_ascii=False)+"\n")
            rows.append(record)
            print(record["status"],project,entry["path"],flush=True)
            if record["status"]!="PASS":
                print(record.get("stderr",""),flush=True)
                (P2/"notebook_execution_partial.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                raise SystemExit(1)
    (P2/"notebook_execution_summary.json").write_text(json.dumps({"notebooks":rows,"run_all_pass":sum(r["status"]=="PASS" for r in rows),"static_model_smoke_only":sum(r["status"]!="PASS" for r in rows),"training_steps":0,"scientific_TEST_forward":0},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Notebook execution batch complete",flush=True)


if __name__=="__main__": main()
