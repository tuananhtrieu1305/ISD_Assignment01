"""Versioned workspace path/bootstrap helpers; never trains or evaluates a model."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import builtins
import io
import time

REPOSITORY = Path(__file__).resolve().parents[2]
PROJECTS = ("A01","A02","A03","A04","A05","A06","tieuluan1","tieuluan2","tieuluan3","agent01","agent02")
_ORIGINAL_OPEN=builtins.open
_ORIGINAL_IO_OPEN=io.open
_ORIGINAL_REPLACE=os.replace
_ORIGINAL_RENAME=os.rename
_WRITE_CONTEXT={}


def _redirect_path(file, mode):
    if not _WRITE_CONTEXT or not isinstance(file,(str,os.PathLike)):
        return file
    path=Path(file).absolute()
    view=_WRITE_CONTEXT["view"]
    if path.is_relative_to(view):
        target=_WRITE_CONTEXT["output"]/path.relative_to(view)
        if any(flag in mode for flag in "wax+"):
            target.parent.mkdir(parents=True,exist_ok=True)
            return target
        if _WRITE_CONTEXT.get("overlay") and target.exists():
            return target
    return file


def _install_write_redirect(view,project):
    _WRITE_CONTEXT.update(view=view,output=REPOSITORY/project/"notebooks/executed/artifacts"/str(time.time_ns()),overlay=False)
    def opened(file,mode="r",*args,**kwargs):
        return _ORIGINAL_OPEN(_redirect_path(file,mode),mode,*args,**kwargs)
    def io_opened(file,mode="r",*args,**kwargs):
        return _ORIGINAL_IO_OPEN(_redirect_path(file,mode),mode,*args,**kwargs)
    builtins.open=opened
    io.open=io_opened
    def replace(source,target,*args,**kwargs):
        return _ORIGINAL_REPLACE(_redirect_path(source,"r"),_redirect_path(target,"w"),*args,**kwargs)
    def rename(source,target,*args,**kwargs):
        return _ORIGINAL_RENAME(_redirect_path(source,"r"),_redirect_path(target,"w"),*args,**kwargs)
    os.replace=replace
    os.rename=rename


def enable_training_output_overlay():
    """Opt-in new output session; read new weights after save, leaving baseline untouched."""
    if not _WRITE_CONTEXT:
        raise RuntimeError("Activate a project first")
    _WRITE_CONTEXT["overlay"]=True
    return str(_WRITE_CONTEXT["output"])


def project_config(project: str) -> dict:
    if project not in PROJECTS:
        raise ValueError("Unknown assignment")
    return json.loads((REPOSITORY/project/"project.json").read_text(encoding="utf-8"))


def activate(project: str, framework: str | None = None) -> dict:
    """Select a logical original layout backed by canonical files, not OS symlinks."""
    config = project_config(project)
    view = REPOSITORY/project/config["runtime_root"]
    if not view.is_dir():
        raise RuntimeError("Runtime view missing; run scripts/materialize_project.py for this project")
    selected = framework or config["default_framework"]
    expected = ".venv-keras" if selected == "keras" else ".venv-torch"
    if sys.platform != "linux" or expected not in sys.executable:
        raise RuntimeError(f"Choose pinned WSL {expected} Python kernel; actual: {sys.executable}")
    for key in ("src", "apps", "models", "agent02_assignment", "term_paper"):
        module = sys.modules.get(key)
        source = getattr(module, "__file__", None)
        if source and REPOSITORY in Path(source).parents and view not in Path(source).parents:
            raise RuntimeError("Another project's module is loaded; restart the kernel before switching assignments")
    sys.path.insert(0, str(view))
    cwd = view / config.get("working_directory", ".")
    if cwd != view:
        sys.path.insert(0,str(cwd))
    os.chdir(cwd)
    os.environ["PYTHONPATH"] = str(view) + os.pathsep + str(REPOSITORY/"_shared")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["KERAS_BACKEND"] = "tensorflow" if selected == "keras" else "torch"
    os.environ["ASSIGNMENT_PROJECT"] = project
    _install_write_redirect(view,project)
    return {"project":project,"canonical_root":str(REPOSITORY/project),"logical_root":str(view),"cwd":str(cwd),"framework":selected,"python":sys.executable}


def resolve_dataset(project: str, dataset_id: str, *, verify: bool = False) -> dict:
    config = project_config(project)
    catalog = json.loads((REPOSITORY/project/config["datasets_catalog"]).read_text(encoding="utf-8"))
    row = next((r for r in catalog["datasets"] if r["dataset_id"] == dataset_id), None)
    if row is None:
        raise KeyError(dataset_id)
    resolved = []
    for item in row.get("files", []):
        path = (REPOSITORY/item["path"]).resolve()
        if not path.is_relative_to(REPOSITORY) or not path.is_file():
            raise FileNotFoundError(str(path))
        if verify and item.get("sha256"):
            import hashlib
            with path.open("rb") as stream:
                assert hashlib.file_digest(stream, "sha256").hexdigest() == item["sha256"]
        resolved.append(str(path))
    return {**row, "resolved_files":resolved}
