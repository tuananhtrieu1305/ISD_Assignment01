"""Generate a minimal CPU-only deployment project and dependency hash lock."""

import argparse
import ast
import hashlib
import json
import tomllib
import zipfile
from importlib import metadata

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from apps.api.v3.registry import Registry
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT

BASE = ROOT / "artifacts/manifests/phase32"


def source_path(module):
    if module == "term_paper":
        return ROOT / "term_paper/__init__.py"
    base = ROOT / (
        "src/" + module.replace(".", "/") if module.startswith("term_paper.") else module.replace(".", "/")
    )
    return base.with_suffix(".py") if base.with_suffix(".py").is_file() else base / "__init__.py"


def source_closure():
    pending = [
        "apps.api.v3.server",
        "apps.api.v3.worker",
        "apps.api.v3.native",
        "apps.api.v3.check_bundle",
        "src.ch05_knowledge_rag.structural",
        "src.ch06_multi_agent.service",
        "src.ch06_multi_agent.executor",
        "src.ch06_multi_agent.tools",
    ]
    found, modules = set(), set()
    while pending:
        module = pending.pop()
        if module in modules:
            continue
        modules.add(module)
        path = source_path(module)
        if not path.is_file():
            continue
        found.add(path)
        for ancestor in path.relative_to(ROOT).parents:
            initializer = ROOT / ancestor / "__init__.py"
            if initializer.is_file():
                found.add(initializer)
        if module.startswith("term_paper"):
            found.add(ROOT / "term_paper/__init__.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
            if isinstance(node, ast.Import):
                pending.extend(
                    alias.name
                    for alias in node.names
                    if alias.name.startswith(("apps.", "src.", "term_paper"))
                )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(("apps.", "src.", "term_paper"))
            ):
                pending.append(node.module)
                pending.extend(node.module + "." + alias.name for alias in node.names)
    return sorted(found)


def cpu_requirements():
    pinned = tomllib.loads((ROOT / "uv.lock").read_text())["package"]
    pending = [
        "Flask",
        "gunicorn",
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "joblib",
        "Pillow",
        "jsonschema",
        "referencing",
        "threadpoolctl",
    ]
    packages, env = {}, {**default_environment(), "extra": ""}
    while pending:
        name = canonicalize_name(pending.pop())
        if name in packages:
            continue
        distribution = metadata.distribution(name)
        matches = [
            p for p in pinned if canonicalize_name(p["name"]) == name and p["version"] == distribution.version
        ]
        if len(matches) != 1:
            raise ValueError("Installed package not uniquely in uv.lock: " + name)
        item = matches[0]
        hashes = {w["hash"] for w in item.get("wheels", [])}
        if item.get("sdist"):
            hashes.add(item["sdist"]["hash"])
        if not hashes or name in {"torch", "tensorflow", "keras"}:
            raise ValueError("CPU dependency hash/backend policy")
        packages[name] = f"{name}=={distribution.version} " + " ".join("--hash=" + h for h in sorted(hashes))
        for expression in distribution.requires or []:
            requirement = Requirement(expression)
            if requirement.marker is None or requirement.marker.evaluate(env):
                pending.append(requirement.name)
    return (
        "# Exact subset of unchanged uv.lock; generated from locked runtime metadata.\n"
        + "\n".join(packages[n] for n in sorted(packages))
        + "\n"
    )


def copy_verified(source, destination):
    payload = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != payload:
            raise ValueError("Package target differs: " + str(destination))
    else:
        with destination.open("xb") as stream:
            stream.write(payload)


def build(version):
    if not version.isalnum():
        raise ValueError("Version must be alphanumeric")
    destination = ROOT / "dist/phase32" / ("render-project-" + version)
    if destination.exists():
        raise FileExistsError("Use a new package version; old evidence retained")
    registry = Registry()
    for record in registry.files.values():
        registry.checked(record)
    requirements = ROOT / "deploy/v3/requirements-cpu.lock"
    encoded = cpu_requirements().encode()
    if requirements.exists() and requirements.read_bytes() != encoded:
        raise ValueError("CPU lock differs; version the change")
    if not requirements.exists():
        with requirements.open("xb") as stream:
            stream.write(encoded)
    files = {ROOT / name for name in registry.files}
    files.update(source_closure())
    files.add(registry.path)
    files.update(
        ROOT / name
        for name in [
            "docs/contracts/v3/openapi.json",
            "deploy/v3/render.yaml",
            "deploy/v3/README.md",
            "deploy/v3/requirements-cpu.lock",
            "uv.lock",
        ]
    )
    manifest = []
    for path in sorted(files):
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("Unsafe package source")
        name = path.relative_to(ROOT).as_posix()
        copy_verified(path, destination / name)
        manifest.append({"path": name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    document = {
        "version": version,
        "files": manifest,
        "size_bytes": sum(r["size_bytes"] for r in manifest),
        "models_retrained": 0,
        "historical_test_evaluation_executed": False,
        "runtime": "Python3.11.17 CPU NumPy; no native framework dependencies",
    }
    write_once(destination / "bundle_manifest.json", document)
    archive = ROOT / "dist/phase32" / ("api-bundle-" + version + ".zip")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(
                    path.relative_to(destination).as_posix(), date_time=(2000, 1, 1, 0, 0, 0)
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                stream.writestr(info, path.read_bytes())
    write_once(
        BASE / f"package_{version}.json",
        {
            "project": destination.relative_to(ROOT).as_posix(),
            "archive": {
                "path": archive.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(archive),
                "size_bytes": archive.stat().st_size,
            },
            "manifest_sha256": sha256_file(destination / "bundle_manifest.json"),
            "file_count": len(manifest),
            "expanded_bytes": document["size_bytes"],
            "requirements_sha256": hashlib.sha256(encoded).hexdigest(),
        },
    )
    print(
        json.dumps(
            {
                "project": str(destination),
                "files": len(manifest),
                "bytes": document["size_bytes"],
                "zip_bytes": archive.stat().st_size,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    build(parser.parse_args().version)
