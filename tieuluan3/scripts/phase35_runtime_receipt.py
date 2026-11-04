"""Read-only receipt of the authorized isolated document toolchain."""

import importlib.metadata as md
import json
import platform
import subprocess
import sys
from scripts.phase35_runtime import ROOT, RUNTIME, digest, write_once_json


def main():
    packages = {
        x: md.version(x)
        for x in [
            "python-docx",
            "pdf2image",
            "Pillow",
            "PyMuPDF",
            "markdown-it-py",
            "pytest",
            "pytest-cov",
            "ruff",
            "lxml",
        ]
    }
    tools = {}
    for executable, arguments in [
        ("soffice", ["--headless", "--version"]),
        ("pdfinfo", ["-v"]),
        ("pdftoppm", ["-v"]),
    ]:
        probe = subprocess.run(
            [str(RUNTIME / "bin" / executable), *arguments],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        tools[executable] = {
            "stdout": probe.stdout.strip(),
            "stderr": probe.stderr.strip(),
            "wrapper_sha256": digest(RUNTIME / "bin" / executable),
        }
    helpers = {
        str(p.relative_to(ROOT)): digest(p)
        for p in sorted((ROOT / "report/tools/documents_vendor_26_1020").rglob("*"))
        if p.is_file()
    }
    inputs = {
        str(p.relative_to(ROOT)): digest(p)
        for p in [
            ROOT / "uv.lock",
            ROOT / "artifacts/manifests/environment.json",
            ROOT / "experiments/environment/docs35/requirements.lock",
        ]
    }
    receipt = {
        "python": platform.python_version(),
        "executable": sys.executable,
        "prefix": sys.prefix,
        "packages": packages,
        "tools": tools,
        "helper_sha256": helpers,
        "input_sha256": inputs,
        "gpu_environments_modified": False,
        "system_package_install": False,
        "authorization": "docs/phase35_local_toolchain_authorization.md",
    }
    assert receipt["python"] == "3.11.17"
    assert sys.prefix == str(RUNTIME / ".venv")
    write_once_json(ROOT / "artifacts/manifests/phase35/runtime_ready.json", receipt)
    print(json.dumps({"python": receipt["python"], "packages": packages, "tools": tools}, ensure_ascii=False))


if __name__ == "__main__":
    main()
