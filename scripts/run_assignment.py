"""One project/framework per process; pinned environments, no dependency installer."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import runpy
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"_shared"))
from assignment_runtime import PROJECTS, activate, project_config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",required=True,choices=PROJECTS)
    parser.add_argument("--framework",choices=["torch","keras","scratch"],default="torch")
    parser.add_argument("--inspect",action="store_true")
    parser.add_argument("--list-datasets",action="store_true")
    parser.add_argument("--cpu",action="store_true")
    parser.add_argument("--notebook")
    parser.add_argument("--module")
    parser.add_argument("--script")
    args,extra=parser.parse_known_args()
    if args.cpu: os.environ["CUDA_VISIBLE_DEVICES"]="-1"
    config=project_config(args.project)
    if args.list_datasets:
        catalog=json.loads((ROOT/args.project/config["datasets_catalog"]).read_text())
        print(json.dumps([{k:r[k] for k in ("dataset_id","name","status")} for r in catalog["datasets"]],ensure_ascii=False,indent=2))
        return
    context=activate(args.project,args.framework)
    if args.inspect or not any([args.notebook,args.module,args.script]):
        print(json.dumps(context,ensure_ascii=False,indent=2))
    elif args.notebook:
        match=next((r for r in config["notebooks"] if r["path"]==args.notebook),None)
        if not match: raise ValueError("Notebook is not in this project's entry-point catalog")
        if "training" in match.get("role","").lower() and "read" not in match.get("role","").lower():
            raise ValueError("Training pipeline is not auto-executed; use read-only comparison notebook or explicit new-run training notebook")
        import nbformat
        from nbclient import NotebookClient
        from jupyter_client import KernelManager
        notebook=nbformat.read(ROOT/args.project/args.notebook,as_version=4)
        manager=KernelManager()
        manager.kernel_spec.argv=[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"]
        client=NotebookClient(notebook,timeout=240,km=manager,resources={"metadata":{"path":context["cwd"]}})
        try:
            client.execute(cleanup_kc=True)
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
        # Keep notebooks/ limited to the project's <=4 source entry points.
        out=ROOT/args.project/"artifacts/notebook_runs"/(Path(args.notebook).stem+"-"+str(int(time.time()))+".ipynb")
        out.parent.mkdir(parents=True,exist_ok=True)
        nbformat.write(notebook,out)
        print(str(out))
    elif args.module:
        sys.argv=[args.module,*extra]
        runpy.run_module(args.module,run_name="__main__")
    else:
        path=(ROOT/args.script).resolve()
        if not path.is_relative_to(ROOT): raise ValueError("Script outside workspace")
        sys.argv=[str(path),*extra]
        runpy.run_path(str(path),run_name="__main__")


if __name__=="__main__": main()
