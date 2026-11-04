"""Read-only parent audit and frontend migration snapshot. No model construction/TEST."""

import argparse
import json
import tempfile
import zipfile
from pathlib import Path

from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase33"
LOCKS = [
    "artifacts/manifests/phase22/spec_lock.json",
    "artifacts/manifests/phase24/data_lock.json",
    "artifacts/manifests/phase25/core_lock.json",
    "artifacts/manifests/phase26/revisions/r2/experiment_lock.json",
    *[f"artifacts/manifests/phase{n}/experiment_lock.json" for n in range(27, 33)],
]


def preserve(name):
    members, refs = {}, []
    for name_lock in LOCKS:
        path = ROOT / name_lock
        refs.append({"path": name_lock, "sha256": sha256_file(path)})
        for row in read_json(path)["files"]:
            if row["path"] in members and members[row["path"]] != row["sha256"]:
                raise ValueError("Conflicting parent hash")
            members[row["path"]] = row["sha256"]
    for index, (name_file, expected) in enumerate(sorted(members.items()), 1):
        path = ROOT / name_file
        if not path.resolve().is_relative_to(ROOT) or path.is_symlink() or sha256_file(path) != expected:
            raise ValueError("Protected file changed: " + name_file)
        if index % 5000 == 0:
            print(f"Protected {index}/{len(members)}", flush=True)
    write_once(
        BASE / (name + ".json"),
        {
            "status": "PASS",
            "locks": refs,
            "unique_protected_files": len(members),
            "historical_test_evaluation_executed": False,
        },
    )
    print(json.dumps({"status": "PASS", "files": len(members)}), flush=True)


def snapshot():
    BASE.mkdir(parents=True, exist_ok=True)
    files = [
        p
        for p in (ROOT / "apps/web").rglob("*")
        if p.is_file()
        and not any(
            s in {"node_modules", "dist", ".vite", "coverage", "test-results", "playwright-report"}
            for s in p.parts
        )
        and (not p.name.startswith(".env") or p.name == ".env.example")
    ]
    destination = BASE / "web_before.zip"
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(ROOT).as_posix())
    write_once(
        BASE / "web_before.json",
        {
            "archive_sha256": sha256_file(destination),
            "files": [
                {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p)} for p in sorted(files)
            ],
        },
    )


def fixtures():
    from apps.api.v3.server import create_app

    registry = read_json(ROOT / "artifacts/manifests/phase32/registry_v3.json")
    result = {}
    with tempfile.TemporaryDirectory(prefix="phase33-contract-") as temporary:
        app = create_app(database=Path(temporary) / "jobs.db", start_worker=False)
        client = app.test_client()
        paths = ["/api/v3/chapters", "/api/v3/datasets", "/api/v3/models?page_size=100"]
        for dataset in registry["datasets"]:
            paths.extend([f"/api/v3/datasets/{dataset['dataset_id']}/overview"])
            if dataset["chapter"] > 1:
                paths.append(f"/api/v3/datasets/{dataset['dataset_id']}/results")
        for model in registry["models"]:
            paths.append(f"/api/v3/models/{model['model_id']}/contract")
        for path in paths:
            response = client.get(path)
            if response.status_code != 200:
                raise ValueError(path)
            result[path] = response.json
    write_once(BASE / "contract_fixtures.json", result)
    print(json.dumps({"status": "PASS", "catalog_gets": len(paths), "inference_executed": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", required=True, choices=["preserve-before", "preserve-after", "snapshot", "fixtures"]
    )
    stage = parser.parse_args().stage
    if stage.startswith("preserve-"):
        preserve(stage.replace("-", "_"))
    elif stage == "snapshot":
        snapshot()
    else:
        fixtures()
