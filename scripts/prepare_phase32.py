"""Build an immutable serving registry from frozen models; TRAIN examples only."""

import copy
import json
from pathlib import Path

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase32"


def prepare():
    if (BASE / "registry_v1.json").exists():
        raise FileExistsError("Registry already prepared; do not overwrite")
    files, public, models, runs, samples = {}, {}, [], [], {}

    def add(path, expected=None, *, expose=False):
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        digest = sha256_file(path)
        if expected and digest != expected:
            raise ValueError("Frozen input mismatch: " + str(path))
        name = path.relative_to(ROOT).as_posix()
        record = {"path": name, "sha256": digest}
        files[name] = {**record, "size_bytes": path.stat().st_size}
        if expose:
            public["asset_" + digest[:24]] = record
        return record

    def linked(record, *, expose=False):
        return add(record["path"], record["sha256"], expose=expose)

    def save(name, document):
        path = BASE / name
        write_once(path, document)
        return add(path, expose=True)

    catalog = read_json(ROOT / "data/catalog_v3.json")
    protocol = read_json(ROOT / "experiments/configs/v3/protocol_v3.json")
    outline = read_json(ROOT / "report/outline_v3.json")
    datasets, chapters = [], []
    for item in catalog["datasets"]:
        dataset = item["dataset_id"]
        spec = next(r for r in protocol["datasets"] if r["dataset_id"] == dataset)
        descriptor = copy.deepcopy(item)
        descriptor["source_manifest"] = linked(item["source_manifest"], expose=True)
        descriptor["data_card"] = linked(item["data_card"], expose=True)
        descriptor["eda"] = linked(item["eda"], expose=True)
        descriptor["task"] = spec["task"]
        datasets.append(descriptor)
    for item in outline["chapters"]:
        chapter = item["chapter"]
        chapters.append(
            {
                "chapter": chapter,
                "title": item["title"],
                "route": f"/chapters/{chapter}",
                "dataset_ids": item["dataset_ids"],
                "families": {
                    1: [],
                    2: ["mlp"],
                    3: ["cnn"],
                    4: ["rnn", "lstm"],
                    5: ["kg_rag"],
                    6: ["multi_agent"],
                }[chapter],
                "sections": ["data", "theory", "run", "results", "deployment"]
                if chapter > 1
                else ["data", "theory"],
            }
        )
    # Only 36 fixed seed42 main neural checkpoints are deployed. No rolling checkpoints.
    phases = [
        (26, "mlp", "artifacts/manifests/phase26/revisions/r2"),
        (27, "cnn", "artifacts/manifests/phase27"),
        (28, "rnn", "artifacts/manifests/phase28"),
        (29, "lstm", "artifacts/manifests/phase29"),
    ]
    components = []
    for phase, family, folder in phases:
        release = read_json(ROOT / folder / "release.json")
        for entry in release["runs"]:
            if (
                entry["seed"] != 42
                or entry["method"] not in {"scratch", "keras", "pytorch"}
                or entry.get("fold") is not None
            ):
                continue
            selected = read_json(ROOT / folder / "runs" / entry["run_id"] / "selection.json")
            config = read_json(ROOT / entry["config"]["path"])
            adapter = read_json(ROOT / config["adapter"]["path"])
            assets = [
                linked(entry["config"]),
                linked(config["adapter"]),
                linked(adapter["preprocessing"]),
                linked(selected["checkpoint"]),
                linked(selected["checkpoint_metadata"]),
                linked(entry["model_contract"], expose=True),
            ]
            spec = {
                "model_id": entry["run_id"],
                "dataset_id": entry["dataset_id"],
                "family": family,
                "implementation": entry["method"],
                "backend": "numpy",
                "chapter": 2 if phase == 26 else 3 if phase == 27 else 4,
                "contract": entry["model_contract"],
                "config": entry["config"],
                "checkpoint": selected["checkpoint"],
                "checkpoint_metadata": selected["checkpoint_metadata"],
                "comparison_group_sha256": entry["comparison_group_sha256"],
                "assets": assets,
                "status": "ready",
                "reason": None,
                "lifecycle": "trained_validation_selected",
            }
            models.append(spec)
        # Historical metrics are read-only, not regenerated from TEST inputs.
        for path in sorted((ROOT / f"artifacts/metrics/phase{phase}").glob("*/*.json")):
            record = read_json(path)
            if "run_id" in record and "metrics" in record and "split" in record:
                runs.append(
                    {
                        "run_id": record["run_id"] + "_" + record["split"],
                        "original_run_id": record["run_id"],
                        "dataset_id": record["dataset_id"],
                        "chapter": 2 if phase == 26 else 3 if phase == 27 else 4,
                        "record": add(path, expose=True),
                    }
                )
    for dataset in {r["dataset_id"] for r in models}:
        assets = {a["path"]: a for m in models if m["dataset_id"] == dataset for a in m["assets"]}
        components.append({"id": dataset, "assets": list(assets.values())})
    for dataset in [r["dataset_id"] for r in datasets if r["chapter"] == 2]:
        document = read_json(ROOT / f"artifacts/manifests/phase26/revisions/r2/data/{dataset}_demo.json")
        samples[dataset] = {
            "input_split": "train",
            "sample_id": document["ids"][0],
            "request": {
                "schema_version": "3.0.0",
                "chapter": 2,
                "dataset_id": dataset,
                "family": "mlp",
                "implementations": ["scratch", "keras", "pytorch"],
                "input": {"kind": "tabular", "features": document["input_features"][0]},
            },
        }
    from scripts.demo_phase27 import sample_request as cnn_sample
    from scripts.demo_phase29 import sample_request as recurrent_sample

    for dataset in [r["dataset_id"] for r in datasets if r["chapter"] in {3, 4}]:
        request, key = cnn_sample(dataset) if dataset.startswith("ch3_") else recurrent_sample(dataset)
        samples[dataset] = {"input_split": "train", "sample_id": key, "request": request}
    from src.ch05_knowledge_rag.catalog import pipeline_contract
    from src.ch05_knowledge_rag.service import sample_request as rag_sample

    kg_assets = [add(p) for p in sorted((ROOT / "apps/api/models").glob("kg_*"))]
    kg_assets.extend(
        [
            add("experiments/configs/ch5/phase14_locked.json"),
            add("experiments/configs/ch5/phase15_locked.json"),
        ]
    )
    for dataset in [r["dataset_id"] for r in datasets if r["chapter"] == 5]:
        samples[dataset] = {
            "input_split": "demo_not_benchmark",
            "sample_id": None,
            "request": rag_sample(dataset),
        }
        for method in ["B0", "B1", "B2", "B3", "B4"]:
            contract = pipeline_contract(dataset, method)
            models.append(
                {
                    "model_id": contract["model_id"],
                    "dataset_id": dataset,
                    "chapter": 5,
                    "family": "kg_rag",
                    "implementation": method,
                    "backend": "numpy",
                    "contract": save(f"contracts/{contract['model_id']}.json", contract),
                    "status": "ready" if contract["available"] else "unavailable",
                    "reason": None if contract["available"] else "structural_only",
                    "assets": kg_assets,
                    "lifecycle": contract["lifecycle"],
                }
            )
    # Small ten-entity browser closure. No full raw corpus is packaged.
    index = add("data/raw/ch5/wikidata/snapshot_index.json")
    structural_assets = [index]
    for item in read_json(ROOT / index["path"])["entities"]:
        structural_assets.append(add("data/raw/ch5/" + item["entity_relative_path"], item["entity_sha256"]))
    components.extend(
        [{"id": "kg_rag", "assets": kg_assets}, {"id": "wikidata", "assets": structural_assets}]
    )
    from src.ch06_multi_agent.service import pipeline_contract as agent_contract
    from src.ch06_multi_agent.service import sample_request as agent_sample

    views = read_json(ROOT / "artifacts/manifests/phase31/input_views_v2.json")
    agent_catalog = read_json(ROOT / views["catalog"]["path"])
    agent_assets = [
        linked(views["catalog"]),
        linked(views["taskset"]),
        add("artifacts/manifests/phase30/preserved_snapshot.json"),
    ]
    for record in agent_catalog["records"].values():
        agent_assets.extend(linked(r) for r in record["artifact_refs"])
    for spec in agent_catalog["models"].values():
        agent_assets.extend(linked(spec[k]) for k in ("config", "checkpoint", "checkpoint_metadata"))
    overlay = read_json(ROOT / "artifacts/manifests/phase31/catalog.json")
    for item in overlay["datasets"]:
        dataset, domain = item["dataset_id"], item["domain"]
        descriptor = next(r for r in datasets if r["dataset_id"] == dataset)
        descriptor["derived_view"] = item
        descriptor["data_card"] = linked(item["data_card"], expose=True)
        agent_request = agent_sample(domain)
        request = {
            "schema_version": "3.0.0",
            "chapter": 6,
            "dataset_id": dataset,
            "family": "multi_agent",
            "implementations": agent_request["variants"],
            "input": {"kind": "question", "text": agent_request["question"], "domain": domain},
        }
        samples[dataset] = {
            "input_split": "parent_train",
            "sample_id": domain + "_numeric_000",
            "request": request,
        }
        for variant in ["A0", "A1", "A2"]:
            identity = f"{dataset}_{variant.lower()}"
            models.append(
                {
                    "model_id": identity,
                    "dataset_id": dataset,
                    "chapter": 6,
                    "family": "multi_agent",
                    "implementation": variant,
                    "backend": "numpy",
                    "contract": save(f"contracts/{identity}.json", agent_contract(domain, variant)),
                    "status": "ready",
                    "reason": None,
                    "assets": agent_assets,
                    "lifecycle": "reused_frozen_tools",
                }
            )
    components.append({"id": "agents", "assets": list({r["path"]: r for r in agent_assets}.values())})
    # Config/schemas and serving source are packaged separately; never link a raw training cache.
    add("experiments/configs/v3/protocol_v3.json")
    for path in sorted((ROOT / "src/common/schemas/v3").glob("*.json")):
        add(path)
    for path in (ROOT / "artifacts/metrics/phase31").glob("grouped_metrics.*"):
        add(path, expose=True)
    save("samples.json", samples)
    # Deduplicate model TEST/validation run IDs by actual metric run_id; fail ambiguity.
    if len({r["run_id"] for r in runs}) != len(runs):
        raise ValueError("Ambiguous historical run IDs")
    document = {
        "registry_version": "phase32.1",
        "seed": 42,
        "models": models,
        "runs": runs,
        "datasets": datasets,
        "chapters": chapters,
        "components": components,
        "files": sorted(files.values(), key=lambda r: r["path"]),
        "public_artifacts": public,
        "samples": {
            "path": "artifacts/manifests/phase32/samples.json",
            "sha256": sha256_file(BASE / "samples.json"),
        },
        "agent_catalog": views["catalog"],
        "agent_taskset_sha256": views["taskset"]["sha256"],
        "historical_test_evaluation_executed": False,
        "models_retrained": 0,
    }
    write_once(BASE / "registry_v1.json", document)
    print(
        json.dumps(
            {
                "registry_sha256": sha256_file(BASE / "registry_v1.json"),
                "models": len(models),
                "runs": len(runs),
                "files": len(files),
                "bytes": sum(r["size_bytes"] for r in files.values()),
            }
        )
    )


if __name__ == "__main__":
    prepare()
