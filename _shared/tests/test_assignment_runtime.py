"""Meaningful guards for namespace isolation, preservation and byte-format adaptation."""
import builtins
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import types

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"_shared"))
sys.path.insert(0,str(ROOT/"scripts"))
import assignment_runtime as runtime
from assignment_runtime.cifar import read_binary
from materialize_project import checked_path,materialize


@pytest.fixture
def project(tmp_path,monkeypatch):
    monkeypatch.setattr(runtime,"REPOSITORY",tmp_path)
    config={"runtime_root":"provenance/runtime/assign","default_framework":"torch","working_directory":".","datasets_catalog":"datasets/catalog.json"}
    root=tmp_path/"A01"
    (root/"datasets").mkdir(parents=True)
    (root/"project.json").write_text(json.dumps(config))
    view=root/config["runtime_root"]
    view.mkdir(parents=True)
    monkeypatch.setattr(sys,"executable","/home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(builtins,"open",runtime._ORIGINAL_OPEN)
    monkeypatch.setattr(io,"open",runtime._ORIGINAL_IO_OPEN)
    monkeypatch.setattr(runtime.os,"replace",runtime._ORIGINAL_REPLACE)
    monkeypatch.setattr(runtime.os,"rename",runtime._ORIGINAL_RENAME)
    monkeypatch.setattr(runtime,"_WRITE_CONTEXT",{})
    monkeypatch.setattr(sys,"path",list(sys.path))
    monkeypatch.setenv("PYTHONPATH","")
    monkeypatch.setenv("KERAS_BACKEND","torch")
    return tmp_path,root,view


def test_unknown_project_rejected():
    with pytest.raises(ValueError): runtime.project_config("../escape")


def test_correct_kernel_required(project,monkeypatch):
    monkeypatch.setattr(sys,"executable","C:/Python/python.exe")
    with pytest.raises(RuntimeError,match="kernel"): runtime.activate("A01")


def test_missing_view_not_silently_created(project):
    _,_,view=project
    view.rmdir()
    with pytest.raises(RuntimeError,match="view missing"): runtime.activate("A01")


def test_cross_project_module_requires_restart(project,monkeypatch):
    root,_,_=project
    module=types.ModuleType("src")
    module.__file__=str(root/"A02/src/__init__.py")
    monkeypatch.setitem(sys.modules,"src",module)
    with pytest.raises(RuntimeError,match="restart"): runtime.activate("A01")


def test_legacy_writes_preserve_baseline_and_optional_overlay(project):
    _,root,view=project
    file=view/"result.txt"
    file.write_text("original")
    runtime.activate("A01")
    file.write_text("new")
    assert runtime._ORIGINAL_OPEN(file).read()=="original"
    assert file.read_text()=="original"
    runtime.enable_training_output_overlay()
    assert file.read_text()=="new"
    assert (root/"datasets").is_dir()


def test_new_run_overlay_requires_activation(project):
    with pytest.raises(RuntimeError): runtime.enable_training_output_overlay()


def test_dataset_checksum_and_escape(project):
    base,root,_=project
    file=root/"datasets/data.csv"
    file.write_text("x\n1\n")
    row={"dataset_id":"one","files":[{"path":"A01/datasets/data.csv","sha256":hashlib.sha256(file.read_bytes()).hexdigest()}]}
    catalog=root/"datasets/catalog.json"
    catalog.write_text(json.dumps({"datasets":[row]}))
    assert runtime.resolve_dataset("A01","one",verify=True)["resolved_files"]==[str(file)]
    file.write_text("corrupt")
    with pytest.raises(AssertionError): runtime.resolve_dataset("A01","one",verify=True)
    with pytest.raises(KeyError): runtime.resolve_dataset("A01","unknown")
    row["files"][0]["path"]="../outside"
    catalog.write_text(json.dumps({"datasets":[row]}))
    with pytest.raises(FileNotFoundError): runtime.resolve_dataset("A01","one")


@pytest.mark.parametrize("copy_only",[True,False])
def test_materialized_views_are_identical_and_reject_collision(tmp_path,copy_only):
    (tmp_path/"source").write_bytes(b"science")
    row={"source":"source","target":"view/file","sha256":hashlib.sha256(b"science").hexdigest()}
    assert materialize(tmp_path,[row],copy_only=copy_only)==1
    assert materialize(tmp_path,[row],copy_only=copy_only)==0
    (tmp_path/"view/file").unlink()
    (tmp_path/"view/file").write_bytes(b"different")
    with pytest.raises(FileExistsError): materialize(tmp_path,[row],copy_only=copy_only)
    with pytest.raises(ValueError): checked_path(tmp_path,"../outside")


def test_changed_source_fails_before_view_write(tmp_path):
    (tmp_path/"source").write_bytes(b"changed")
    with pytest.raises(ValueError): materialize(tmp_path,[{"source":"source","target":"view/file","sha256":"0"*64}])
    assert not (tmp_path/"view/file").exists()


def test_binary_adapter_matches_independent_train_record(tmp_path):
    records=np.zeros((10000,3073),dtype=np.uint8)
    records[0,0]=6
    records[0,1:1025]=11
    records[0,1025:2049]=22
    records[0,2049:]=33
    archive=tmp_path/"cifar.tar.gz"
    with tarfile.open(archive,"w:gz") as tar:
        info=tarfile.TarInfo("cifar-10-batches-bin/data_batch_1.bin")
        payload=records.tobytes()
        info.size=len(payload)
        tar.addfile(info,io.BytesIO(payload))
    x,y,tx,ty=read_binary(archive,train_limit=1)
    assert x.shape==(1,32,32,3) and x[0,0,0].tolist()==[11,22,33]
    assert y.tolist()==[6] and tx is ty is None


def test_binary_adapter_rejects_wrong_batch_size(tmp_path):
    archive=tmp_path/"bad.tar.gz"
    with tarfile.open(archive,"w:gz") as tar:
        info=tarfile.TarInfo("cifar-10-batches-bin/data_batch_1.bin")
        info.size=1
        tar.addfile(info,io.BytesIO(b"x"))
    with pytest.raises(AssertionError): read_binary(archive,train_limit=1)


def test_paper_demo_rejects_unpinned_seed_and_wrong_chapter_before_loading():
    from assignment_runtime import paper_demo
    with pytest.raises(ValueError,match='seed42'):
        paper_demo.infer({'chapter':4},seed=17)
    with pytest.raises(ValueError,match='Chapter3/4'):
        paper_demo.infer({'chapter':6})
    for dataset,family in [('unknown','rnn'),('ch3_eurosat','lstm'),('ch4_gold_pink_sheet','cnn')]:
        with pytest.raises(ValueError): paper_demo.sample_request(dataset,family)


def test_paper_demo_dispatch_keeps_request_and_cpu_backend(monkeypatch):
    from assignment_runtime import paper_demo
    calls=[]
    token=object()
    monkeypatch.setattr(paper_demo,'registry',lambda:token)
    inference=types.ModuleType('apps.api.v3.inference')
    def compare(registry,request,job_id,mode):
        calls.append((registry,request,mode))
        return {'results':['same pinned models']},{}
    inference.compare=compare
    monkeypatch.setitem(sys.modules,'apps.api.v3.inference',inference)
    request={'chapter':4,'input':{'values':[[1.,2.]]}}
    before=json.dumps(request)
    assert paper_demo.infer(request)=={'results':['same pinned models']}
    assert calls==[(token,request,'cpu')] and json.dumps(request)==before
