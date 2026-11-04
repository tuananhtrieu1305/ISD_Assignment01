"""Bounded migration smoke: fixtures/TRAIN only, never fit or scientific TEST."""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import warnings

ROOT=Path(__file__).resolve().parents[1]
P2=ROOT/"docs/reorganization/phase2"
sys.path.insert(0,str(ROOT/"_shared"))


def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def output(project,framework,records):
    p=P2/"smoke"/(project+"_"+framework+".json")
    p.parent.mkdir(parents=True,exist_ok=True)
    doc={"project":project,"framework":framework,"status":"PASS","records":records,"python":sys.executable,"training_steps":0,"scientific_TEST_forward":0,"input_policy":"synthetic fixture or explicitly saved TRAIN/demo input only"}
    p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"project":project,"framework":framework,"status":"PASS","cases":len(records)},ensure_ascii=False),flush=True)


def helpers():
    os.environ["COVERAGE_FILE"]=str(P2/".coverage_helpers_r3")
    import pytest
    code=pytest.main([str(ROOT/"_shared/tests/test_assignment_runtime.py"),"-c",str(ROOT/"_shared/tests/pytest.ini"),"--rootdir="+str(ROOT/"_shared/tests"),"-p","no:cacheprovider","--basetemp="+str(P2/("unit_tmp_"+str(time.time_ns()))),"--junitxml="+str(P2/"helper_tests_r3.xml"),"--cov=assignment_runtime","--cov=materialize_project","--cov-branch","--cov-report=json:"+str(P2/"helper_coverage_r3.json"),"--cov-report=term","-q"])
    raise SystemExit(code)


def legacy(project):
    import numpy as np
    import pandas as pd
    import joblib
    records=[]
    base=ROOT/project
    if project in {"A01","A02"}:
        meta=load(base/"artifacts/diabetes_metadata.json")
        values={"Glucose":120.,"BMI":28.,"Age":35.,"Pregnancies":2.,"BloodPressure":75.,"DiabetesPedigreeFunction":0.5}
        frame=pd.DataFrame([{f:values[f] for f in meta["features"]}])
        for name,item in meta["available_models"].items():
            path=base/"artifacts"/item["artifact"].replace("\\","/")
            with warnings.catch_warnings(record=True) as captured:
                model=joblib.load(path)
                prediction=np.asarray(model.predict(frame))
                probability=np.asarray(model.predict_proba(frame))
            assert prediction.shape==(1,) and np.isfinite(probability).all() and np.allclose(probability.sum(axis=1),1.)
            records.append({"model":name,"prediction":prediction.tolist(),"probability":probability.tolist(),"input_scope":"synthetic6-feature Pima fixture","warnings":[str(w.message) for w in captured]})
    elif project=="A03":
        module=importlib.import_module("backend.app")
        for task in ["diabetes","house_price","customer_behavior"]:
            bundle=module.load_pipeline_bundle(task)
            instance=module.PipelineDnnModel(bundle,bundle["metadata"]["task_type"])
            folder=base/"artifacts/pipeline"/task
            payload=load(folder/"demo_input.json")
            expected=load(folder/"demo_prediction.json")
            frame=pd.DataFrame([payload],columns=bundle["features"])
            prediction=np.asarray(instance.predict(frame))
            assert prediction.shape==(1,) and np.isfinite(prediction).all()
            if bundle["metadata"]["task_type"]=="binary_classification":
                probability=float(instance.predict_proba(frame)[0,1])
                gold=float(expected["probability_class_1"])
                assert abs(probability-gold)<=1e-6,(task,probability,gold)
                detail={"probability":probability,"golden_probability":gold,"absolute_error":abs(probability-gold)}
            else:
                key=next(k for k in expected if k!="model" and isinstance(expected[k],(int,float)))
                gold=float(expected[key])
                assert abs(float(prediction[0])-gold)<=1e-6,(task,prediction,gold)
                detail={"prediction":float(prediction[0]),"golden_prediction":gold,"absolute_error":abs(float(prediction[0])-gold)}
            records.append({"task":task,"input_scope":"original saved demo fixture",**detail})
    elif project=="A04":
        framework="keras" if ".venv-keras" in sys.executable else "torch"
        tasks=["diabetes","house_price","customer_behavior","mnist","cifar10"]
        if framework=="keras":
            import tensorflow as tf
            for task in tasks:
                name="keras_basic_cnn_best.keras" if task in {"mnist","cifar10"} else "m1_basic_mlp_regressor_best.keras" if task=="house_price" else "m1_basic_mlp_best.keras"
                path=base/"artifacts/pipeline04"/task/"models"/name
                model=tf.keras.models.load_model(path,compile=False)
                shape=(1,*model.input_shape[1:])
                value=np.asarray(model(np.zeros(shape,dtype=np.float32),training=False))
                assert value.shape[0]==1 and np.isfinite(value).all()
                records.append({"task":task,"checkpoint":name,"shape":list(shape),"output_shape":list(value.shape),"input_scope":"synthetic tensor matching trained model signature","device":"cpu"})
                tf.keras.backend.clear_session()
        else:
            import torch
            from torch import nn
            import torch.nn.functional as F
            import inspect
            for task in tasks:
                source=base/"provenance/originals/pipeline04"/(task+"_cnn_pipeline.ipynb" if task in {"mnist","cifar10"} else task+"_pipeline04.ipynb")
                doc=load(source)
                classes=[]
                for cell in doc["cells"]:
                    if cell["cell_type"]!="code": continue
                    for node in ast.parse("".join(cell["source"])).body:
                        if isinstance(node,ast.ClassDef) and any(isinstance(n,ast.Name) and n.id=="nn" for n in ast.walk(node)):
                            classes.append(node)
                scope={"__name__":"a04_migration_classes","torch":torch,"nn":nn,"F":F,"np":np,"SEED":42}
                exec(compile(ast.Module(body=classes,type_ignores=[]),str(source),"exec"),scope)
                name="pytorch_basic_cnn_best.pt" if task in {"mnist","cifar10"} else "pytorch_basic_mlp_regressor_best.pt" if task=="house_price" else "pytorch_basic_mlp_best.pt"
                state=torch.load(base/"artifacts/pipeline04"/task/"models"/name,map_location="cpu",weights_only=False)
                if "model_state_dict" in state: state=state["model_state_dict"]
                elif "state_dict" in state: state=state["state_dict"]
                class_name=next(n for n in scope if n.startswith("Torch") and "Residual" not in n and "Block" not in n)
                cls=scope[class_name]
                weight=next(v for k,v in state.items() if k.endswith("weight") and v.ndim>=2)
                parameters=inspect.signature(cls).parameters
                kwargs={k:int(weight.shape[1]) for k in ("input_dim","input_size") if k in parameters}
                model=cls(**kwargs)
                model.load_state_dict(state,strict=True)
                model.eval()
                side=28 if task=="mnist" else 32
                shape=(1,int(weight.shape[1]),side,side) if task in {"mnist","cifar10"} else (1,int(weight.shape[1]))
                with torch.inference_mode(): value=model(torch.zeros(shape)).numpy()
                assert value.shape[0]==1 and np.isfinite(value).all()
                records.append({"task":task,"checkpoint":name,"class":class_name,"shape":list(shape),"output_shape":list(value.shape),"input_scope":"synthetic tensor matching trained model signature","device":"cpu"})
    elif project=="A06":
        if ".venv-keras" in sys.executable:
            import tensorflow as tf
            for task in ("customer","stock"):
                with np.load(base/f"datasets/processed/{task}_train.npz") as data:
                    x=data["X"][:1].astype("float32")
                path=base/f"models/keras/keras_{task}_rnn_best.keras"
                model=tf.keras.models.load_model(path,compile=False)
                value=np.asarray(model(x,training=False))
                assert value.size==1 and np.isfinite(value).all()
                records.append({"task":task,"model":path.name,"input_scope":"first original TRAIN window","output_shape":list(value.shape),"output":value.reshape(-1).tolist(),"device":"cpu"})
                tf.keras.backend.clear_session()
        else:
            import torch
            for task,cls in [("customer","CustomerRNN"),("stock","StockRNN")]:
                module=importlib.import_module("src.pytorch_"+task)
                state=torch.load(base/f"models/pytorch/pytorch_{task}_rnn_best.pt",map_location="cpu",weights_only=False)
                if "model_state_dict" in state: state=state["model_state_dict"]
                elif "state_dict" in state: state=state["state_dict"]
                hidden=state["rnn.weight_hh_l0"].shape[1]
                model=getattr(module,cls)(hidden_size=hidden)
                model.load_state_dict(state,strict=True)
                model.eval()
                with np.load(base/f"datasets/processed/{task}_train.npz") as data:
                    x=data["X"][:1].astype("float32")
                with torch.inference_mode(): value=model(torch.from_numpy(x)).numpy()
                assert value.size==1 and np.isfinite(value).all()
                records.append({"task":task,"input_scope":"first original TRAIN window","output":value.reshape(-1).tolist(),"device":"cpu"})
    elif project=="A05":
        import tensorflow as tf
        for path in sorted((base/"models/checkpoints").glob("*.keras")):
            model=tf.keras.models.load_model(path,compile=False)
            shape=(1,*model.input_shape[1:])
            value=np.asarray(model(np.zeros(shape,dtype=np.float32),training=False))
            assert value.ndim==2 and value.shape[0]==1 and np.isfinite(value).all() and np.allclose(value.sum(axis=1),1.,atol=1e-5)
            records.append({"model":path.name,"input_scope":"synthetic zero tensor in declared model input space","shape":list(shape),"output_shape":list(value.shape),"probability_sum":float(value.sum()),"device":"cpu"})
            tf.keras.backend.clear_session()
    elif project=="agent01":
        spec=importlib.util.spec_from_file_location("maze_migration_fixture",base/"src/experiment.py")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result=load(base/"evidence/results.json")
        route=module.shortest_path(module.MAZE,module.START,module.GOAL)
        assert len(route)-1==result["bfs_moves"]==result["learned_moves"]==24
        assert module.transition(module.MAZE,module.START,1,module.GOAL)==(module.START,-10,True)
        records.append({"fixed_maze_shape":list(module.MAZE.shape),"bfs_moves":len(route)-1,"recorded_greedy_moves":result["learned_moves"],"training_added":0})
    elif project=="tieuluan1":
        from term_paper.deployment.app.model_service import ModelService
        from term_paper.deployment.app.schemas import DIABETES_FEATURES
        service=ModelService(Path.cwd())
        health=service.health()
        assert health["status"]=="ok" and len(health["models"])==4
        payload={name:0. for name in DIABETES_FEATURES}
        payload.update(BMI=28.,Age=4.,GenHlth=2.,Education=5.,Income=4.)
        result=service.predict_diabetes(payload)
        records.append({"models_verified":4,"input_scope":"synthetic CDC21-feature fixture","prediction":result,"health":health["status"]})
    elif project=="agent02":
        doc=load(base/"report/phase08/input_index.json")
        inputs=doc["files"] if isinstance(doc,dict) else doc
        config=load(base/"project.json")
        logical=base/config["runtime_root"]/"agent02_assignment"
        for row in inputs:
            p=logical/row["path"]
            assert hashlib.sha256(p.read_bytes()).hexdigest()==row["sha256"],row["path"]
        records.append({"sealed_notebook_inputs":len(inputs),"policy_forward_added":0,"all_input_hashes":"PASS"})
    else:
        raise ValueError("Use v3 or paper1 smoke for this project")
    output(project,"keras" if ".venv-keras" in sys.executable else "torch",records)


def v3(project,only_rnn=False):
    from apps.api.v3.registry import Registry
    from apps.api.v3.server import create_app
    from apps.api.v3.inference import compare
    registry=Registry()
    expected_chapters=5 if project=="tieuluan2" else 6
    assert len(registry.chapters)==expected_chapters
    app=create_app(start_worker=False,database=str(P2/"smoke"/(project+"_jobs.db")))
    client=app.test_client()
    health=client.get("/health")
    ready=client.get("/ready")
    assert health.status_code==200 and ready.status_code==200,ready.json
    if project=="tieuluan2":
        assert client.get("/api/v3/chapters/6").status_code==404
        assert client.get("/api/v3/datasets/ch6_diabetes_tasks").status_code==404
        assert all(m["family"]!="multi_agent" for m in registry.models.values())
    samples=registry.json(registry.document["samples"])
    records=[{"health":health.status_code,"ready":ready.json["status"],"chapters":expected_chapters,"models":len(registry.models)}]
    chosen=[k for k in samples if not k.startswith("ch6_") or project=="tieuluan3"]
    for dataset in chosen:
        sample=samples[dataset]
        request=sample["request"]
        assert sample.get("input_split") in {"train","TRAIN","train_only","TRAIN-only","parent_train","not_applicable","compact_demo","corpus","demo","demo_not_benchmark"},sample.get("input_split")
        if dataset.startswith("ch1_"): continue
        if only_rnn and request["chapter"]!=4: continue
        families=(["rnn"] if only_rnn else ["rnn","lstm"]) if request["chapter"]==4 else [request["family"]]
        for family in families:
            request=dict(request,family=family)
            result,extras=compare(registry,request,"job_00000000000000000000000000000000","cpu")
            if dataset!="ch5_wikidata_subgraphs": assert result["status"]=="succeeded",(dataset,result)
            else: assert "entity" in extras
            records.append({"dataset":dataset,"family":family,"input_split":sample.get("input_split"),"status":result["status"],"slots":len(result["results"]),"valid":result["comparison_valid"]})
    output(project,"torch_rnn" if only_rnn else "torch",records)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action",choices=["helpers","legacy","v3","v3-rnn","status"],required=True)
    args=parser.parse_args()
    if args.action=="helpers": helpers()
    if args.action=="status":
        processes=[]
        for process in Path('/proc').iterdir():
            if not process.name.isdigit(): continue
            try:
                argv=(process/'cmdline').read_bytes().decode(errors='replace').split('\0')
                tags=[name for name in ['run_assignment.py','reorganization_phase2_smoke.py','ipykernel_launcher'] if any(arg.endswith(name) or arg==name for arg in argv)]
                if tags: processes.append({'pid':process.name,'tags':tags})
            except OSError: pass
        samples=load(ROOT/'tieuluan3/artifacts/manifests/phase32/samples.json')
        print(json.dumps({'processes':processes,'sample_input_splits':sorted({s.get('input_split','') for s in samples.values()}),'agent02_input_type':type(load(ROOT/'agent02/report/phase08/input_index.json')).__name__},ensure_ascii=False))
        return
    project=os.environ["ASSIGNMENT_PROJECT"]
    if args.action=="legacy": legacy(project)
    else: v3(project,only_rnn=args.action=="v3-rnn")


if __name__=="__main__": main()
