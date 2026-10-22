"""AST/lint/safe Blueprint checks on new Phase33 sources, no model inference."""

import ast
import json
import subprocess
import sys

import yaml

from scripts.verify_phase33 import ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json

if __name__ == "__main__":
    files = sorted([*ROOT.glob("scripts/*phase33.py"), *ROOT.glob("tests/ui33/*.py")])
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"))
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *[str(path) for path in files], "--output-format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    if json.loads(result.stdout):
        raise ValueError("Ruff findings")
    blueprint = yaml.safe_load((ROOT / "deploy/web-v3/render.yaml").read_text())["services"][0]
    if (
        blueprint["runtime"] != "static"
        or blueprint["rootDir"] != "apps/web"
        or blueprint["routes"] != [{"type": "rewrite", "source": "/*", "destination": "/index.html"}]
    ):
        raise ValueError("Static deployment contract mismatch")
    entrypoints = read_json(ROOT / "artifacts/manifests/phase33/entrypoint_verification.json")
    if entrypoints["status"] != "PASS":
        raise ValueError("Entrypoints not checked")
    write_once(
        ROOT / "artifacts/manifests/phase33/python_review_r2.json",
        {
            "status": "PASS",
            "ast": "PASS",
            "ruff": "PASS",
            "source": [ref(path) for path in files],
            "prior_review": ref(ROOT / "artifacts/manifests/phase33/python_review.json"),
            "prior_source_snapshot": ref(ROOT / "artifacts/manifests/phase33/python_review_r1_source.zip"),
            "entrypoints": ref(ROOT / "artifacts/manifests/phase33/entrypoint_verification.json"),
            "blueprint_yaml_semantic_check": "PASS; not cloud/Render CLI validation",
            "historical_test_evaluation_executed": False,
        },
    )
    print(json.dumps({"status": "PASS", "files": len(files)}))
