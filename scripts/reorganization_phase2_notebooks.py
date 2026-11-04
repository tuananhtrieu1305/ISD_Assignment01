"""Framework-specific historical training views plus safe saved-result entry points."""
from __future__ import annotations
import ast
import copy
import json
from pathlib import Path
import textwrap

from reorganization_phase2_setup import bootstrap

ROOT=Path(__file__).resolve().parents[1]
P2=ROOT/"docs/reorganization/phase2"


def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def save(p,doc):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+".migration-tmp")
    t.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    t.replace(p)


def code(source,index): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"id":f"reorg-code-{index}","source":source.splitlines(keepends=True)}
def markdown(source,index): return {"cell_type":"markdown","metadata":{},"id":f"reorg-md-{index}","source":[source]}


def foreign_names(framework):
    tf={"tf","tensorflow","keras","layers"}
    torch={"torch","nn","F","DataLoader","TensorDataset","DEVICE"}
    return tf if framework=="torch" else torch if framework=="keras" else tf|torch


def trim_import_setup(source,framework):
    foreign=foreign_names(framework)
    tree=ast.parse(source)
    body=[]
    for node in tree.body:
        if isinstance(node,ast.Import):
            node.names=[x for x in node.names if x.name.split(".")[0] not in foreign]
            if node.names: body.append(node)
        elif isinstance(node,ast.ImportFrom):
            if (node.module or "").split(".")[0] not in foreign: body.append(node)
        elif isinstance(node,ast.Assign) and isinstance(node.value,ast.Dict):
            pairs=[(k,v) for k,v in zip(node.value.keys,node.value.values) if not any(isinstance(n,ast.Name) and n.id in foreign for n in ast.walk(v))]
            node.value.keys=[p[0] for p in pairs]
            node.value.values=[p[1] for p in pairs]
            body.append(node)
        elif not any(isinstance(n,ast.Name) and n.id in foreign for n in ast.walk(node)):
            body.append(node)
    tree.body=body
    return ast.unparse(ast.fix_missing_locations(tree))+"\n"


def definitions_and_constants(source,framework):
    foreign=foreign_names(framework)
    kept=[]
    safe_functions=set()
    for node in ast.parse(source).body:
        if any(isinstance(n,ast.Name) and n.id in foreign for n in ast.walk(node)):
            continue
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
            kept.append(node)
            if isinstance(node,ast.FunctionDef) and not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {"fit","step","save","to_csv","train_batch"} for n in ast.walk(node)):
                safe_functions.add(node.name)
        elif isinstance(node,ast.Assign):
            try:
                ast.literal_eval(node.value)
                kept.append(node)
            except (ValueError,TypeError):
                if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id in safe_functions:
                    kept.append(node)
    return ast.unparse(ast.Module(body=kept,type_ignores=[]))+"\n" if kept else ""


def cifar_loader():
    return '''# Explicit format adapter: the V3 archive is binary, not the historical Python pickle.
from assignment_runtime.cifar import read_binary, CLASS_NAMES
CIFAR10_PATH = _repo / 'tieuluan3/datasets/raw/ch3/cifar10/cifar-10-binary.tar.gz'
x_train_full, y_train_full, x_test_raw, y_test = read_binary(CIFAR10_PATH, include_test=True)
label_names = CLASS_NAMES
display(pd.DataFrame({'ClassIndex': np.arange(10), 'LabelName': label_names}))
print({'source_format': 'CIFAR10 binary; explicit adapter', 'train_shape': x_train_full.shape, 'test_shape': x_test_raw.shape})
'''


def main():
    mapping=load(P2/"canonical_map.json")["files"]
    config=load(ROOT/"A04/project.json")
    records=[]
    for row in mapping:
        if row["project"]!="A04" or not row["target"].startswith("A04/notebooks/"): continue
        original=load(ROOT/row["baseline_path"])
        name=Path(row["target"]).name
        task=name.replace("_pipeline04.ipynb","").replace("_cnn_pipeline.ipynb","")
        cnn=task in {"cifar10","mnist"}
        recipes={"keras":{1,4,7,10,13,16,31,34,37} if cnn else {1,4,7,10,13,16,19,22,25,28,31,34,49,52,55,58,61},"torch":{1,4,7,10,13,19,40,43,46,52} if cnn else {1,4,7,10,13,16,22,25,37,40,43}}
        if cnn: recipes["scratch"]={1,4,7,10,13,22,25,28,49}
        for framework,selected in recipes.items():
            safe_imports="\n".join(ast.unparse(n) for n in ast.parse("".join(original["cells"][1]["source"])).body if isinstance(n,(ast.Import,ast.ImportFrom)))+"\n"
            if not cnn:
                safe_imports += "PROJECT_ROOT = Path(_migration['logical_root'])\n"
            cells=[markdown(f"# A04 {task} — {framework}\n\nMã huấn luyện tách từ notebook gốc, giữ tham số/thuật toán. Mặc định `RUN_TRAINING=False`: Run All chỉ kiểm imports/path và xem số liệu đã lưu; không fit/TEST. Muốn thực nghiệm mới phải tự bật cờ; mọi output legacy path được chuyển vào một thư mục `notebooks/executed/artifacts/` mới, không ghi đè kết quả gốc.\n",0),code(bootstrap("A04","torch" if framework=="scratch" else framework),0),code("RUN_TRAINING = False\nif RUN_TRAINING:\n    from assignment_runtime import enable_training_output_overlay\n    enable_training_output_overlay()\n"+safe_imports,1)]
            for index,cell in enumerate(original["cells"]):
                if cell["cell_type"]=="markdown":
                    cells.append(markdown("".join(cell.get("source",[])),index+10))
                    continue
                source="".join(cell.get("source",[]))
                if index==4:
                    source=trim_import_setup(source,framework)
                    cells.append(code(source,index+10))
                    continue
                if task=="cifar10" and index==7: source=cifar_loader()
                if index in selected:
                    body=source
                else:
                    body=definitions_and_constants(source,framework)
                if body.strip():
                    cells.append(code("if RUN_TRAINING:\n"+textwrap.indent(body,"    "),index+10))
            cells.append(code(f"from IPython.display import display\nimport pandas as pd\n_saved = _repo / 'A04/artifacts/pipeline04/{task}/metrics'\nfor _file in sorted(_saved.glob('*comparison*.csv')):\n    print(_file.name)\n    display(pd.read_csv(_file))\n",1000))
            doc={"nbformat":4,"nbformat_minor":5,"metadata":{"kernelspec":{"name":"python3","language":"python","display_name":"Python3.11 WSL "+framework},"migration":{"derived_from":row["baseline_path"],"framework":framework,"original_algorithm_preserved":True,"run_training_default":False}},"cells":cells}
            path=ROOT/"A04/notebooks/training"/(task+"_"+framework+".ipynb")
            save(path,doc)
            records.append({"path":path.relative_to(ROOT/"A04").as_posix(),"framework":"torch" if framework=="scratch" else framework,"role":"read-only default; opt-in new-run historical training source","source_notebook":row["baseline_path"],"selected_original_cells":sorted(selected)})
        # Combined notebook is now a useful cross-framework results entry point.
        cells=[markdown(f"# A04 — {task}: dữ liệu và so sánh đã lưu\n\nCác framework dùng hai môi trường WSL riêng. Mã huấn luyện ở `training/{task}_keras.ipynb` và `training/{task}_torch.ipynb`"+(f", cùng `training/{task}_scratch.ipynb`" if cnn else "")+". Notebook này đọc kết quả gốc; Run All không train/TEST. Toàn bộ notebook huấn luyện nguyên byte và output cũ nằm trong provenance.\n",0),code(bootstrap("A04","torch"),0)]
        for i,cell in enumerate(original["cells"]):
            if cell["cell_type"]=="markdown": cells.append(markdown("".join(cell.get("source",[])),i+10))
        cells.append(code(f"import pandas as pd\nfrom IPython.display import display, Image\n_folder = _repo / 'A04/artifacts/pipeline04/{task}/metrics'\nfor _file in sorted(_folder.glob('*comparison*.csv')):\n    print(_file.name)\n    display(pd.read_csv(_file))\n",1000))
        for candidate in (ROOT/f"A04/artifacts/pipeline04/{task}/figures").glob("*training_curves.png"):
            cells.append(code("display(Image(filename=str(_repo / "+repr(candidate.relative_to(ROOT).as_posix())+")))\n",1100+len(cells)))
        doc=copy.deepcopy(original)
        doc["cells"]=cells
        doc["metadata"]["kernelspec"]={"name":"python3","language":"python","display_name":"Python3.11 WSL NumPy-PyTorch"}
        doc["metadata"]["migration"]={"role":"saved results comparison; training separated by framework","original":row["baseline_path"]}
        save(ROOT/row["target"],doc)
        for entry in config["notebooks"]:
            if entry["path"]=="notebooks/"+name:
                entry.update(role="read-only saved cross-framework comparisons",mixed_framework=False)
    incoming={r["path"] for r in records}
    config["notebooks"]=[r for r in config["notebooks"] if r["path"] not in incoming]+records
    save(ROOT/"A04/project.json",config)
    # RNN fundamentals have independent toy examples, so each kernel gets exactly its own branch.
    row=next(r for r in mapping if r["project"]=="A06" and r["old_path"]=="A06/notebooks/01_RNN_Fundamentals.ipynb")
    original=load(ROOT/row["baseline_path"])
    a06=load(ROOT/"A06/project.json")
    for framework,skip in [("torch",{18}),("keras",{16,25})]:
        doc=copy.deepcopy(original)
        cells=[markdown(f"# RNN cơ bản — {framework} kernel\n\nVí dụ toy từ notebook gốc; nhánh framework còn lại nằm trong notebook tương ứng. Không train lại checkpoint hoặc dùng dataset TEST.\n",0),code(bootstrap("A06",framework),0)]
        for index,cell in enumerate(original["cells"]):
            if index in skip: continue
            cell=copy.deepcopy(cell)
            cell["id"]=f"rnn-{framework}-{index}"
            if cell["cell_type"]=="code":
                source="".join(cell.get("source",[]))
                if index==2: source=trim_import_setup(source,framework)
                cell["source"]=source.splitlines(keepends=True)
                cell["outputs"]=[]
                cell["execution_count"]=None
            cells.append(cell)
        doc["cells"]=cells
        doc["metadata"]["kernelspec"]={"name":"python3","language":"python","display_name":"Python3.11 WSL "+framework}
        path=ROOT/"A06/notebooks"/("01_RNN_Fundamentals.ipynb" if framework=="torch" else "01_RNN_Fundamentals_Keras.ipynb")
        save(path,doc)
        if framework=="keras":
            relative=path.relative_to(ROOT/"A06").as_posix()
            a06["notebooks"]=[r for r in a06["notebooks"] if r["path"]!=relative]
            a06["notebooks"].append({"path":relative,"framework":"keras","role":"fundamentals and toy forward demonstration"})
        else:
            a06["notebooks"][0].update(role="fundamentals and toy forward demonstration",mixed_framework=False)
    save(ROOT/"A06/project.json",a06)
    save(P2/"framework_notebook_split.json",{"A04_training_variants":records,"A06_fundamentals_kernels":["torch","keras"],"original_source_and_outputs_preserved":True,"training_executed":False,"scientific_TEST_forward":False,"frameworks_installed_together":False})
    print(f"A04:5readers + {len(records)}framework-specific training notebooks; A06:2isolated fundamentals notebooks")


if __name__=="__main__": main()
