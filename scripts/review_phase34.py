"""AST/Ruff/entrypoint review for new Phase34 files only."""

import ast
import json
import subprocess
import sys

from scripts.build_phase34 import BASE, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json

FILES = [
    "scripts/phase34_editor.py",
    "scripts/build_phase34.py",
    "scripts/prepare_phase34.py",
    "scripts/verify_phase34.py",
    "scripts/review_phase34.py",
    "tests/report34/test_editor.py",
    "tests/report34/test_publication.py",
    "tests/report34/test_audit.py",
]


def review():
    parser = read_json(BASE / "powershell_parser.json")
    if parser["status"] != "PASS":
        raise ValueError("PowerShell parser failed")
    for relative in FILES:
        ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    for action in [["check"], ["format", "--check"]]:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", *action, *FILES],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    write_once(
        BASE / "lint-r3.json",
        {
            "status": "PASS",
            "ast": "PASS",
            "ruff": "PASS",
            "format": "PASS",
            "powershell_parser": ref(BASE / "powershell_parser.json"),
            "source": [ref(ROOT / name) for name in FILES] + [parser["source"]],
            "static_type_checker": "not_configured",
            "scope": "Phase34 new code only; no inference imports executed",
        },
    )
    print(json.dumps({"status": "PASS", "python_files": len(FILES)}))


if __name__ == "__main__":
    review()
