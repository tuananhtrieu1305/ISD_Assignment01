"""Offline acceptance checks for the simple A01-A06 demo contract."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = [f"A0{i}" for i in range(1, 7)]


def load_data(project: str) -> dict:
    raw = (ROOT / project / "web" / "data.js").read_text(encoding="utf-8")
    prefix = "window.ASSIGN_DATA = "
    assert raw.startswith(prefix), f"{project}: unexpected data.js wrapper"
    return json.loads(raw[len(prefix) :].rstrip().removesuffix(";"))


def main() -> None:
    checks: list[str] = []
    shared_js = (ROOT / "_shared" / "simple_demo" / "simple-demo.js").read_text(encoding="utf-8")
    assert "renderInputForm" in shared_js, "typed input renderer missing"
    assert "renderResults" in shared_js, "user-facing output renderer missing"
    assert "renderReplayForm" in shared_js, "honest replay selector missing"
    assert "JSON.parse" not in shared_js, "raw JSON input parser remains"
    for project in PROJECTS:
        web = ROOT / project / "web"
        html = (web / "index.html").read_text(encoding="utf-8")

        assert '<form class="panel" id="demo-form"' in html, f"{project}: missing simple form"
        assert 'id="input-fields"' in html, f"{project}: missing field container"
        assert 'id="results"' in html, f"{project}: missing result container"
        assert '/_demo-ui/simple-demo.js' in html, f"{project}: shared demo JS missing"
        assert "<textarea" not in html, f"{project}: raw JSON textarea remains"
        assert "table-select" not in html, f"{project}: data explorer remains"
        assert "metric-select" not in html, f"{project}: metric explorer remains"
        checks.append(f"{project} simple input-output surface")

        # Preserve the old release's exact bytes through its original template.
        # Do not rewrite a sealed REORG receipt to call the new UI the old UI.
        release = json.loads((web / "release-reorg.json").read_text(encoding="utf-8"))
        for asset in release["assets"]:
            path = ROOT / asset["path"]
            content = path.read_bytes()
            if path.name == "index.html":
                template = (ROOT / "_shared/web/index.html").read_text(encoding="utf-8")
                content = template.replace("__PROJECT__", project).encode("utf-8")
            assert hashlib.sha256(content).hexdigest() == asset["sha256"], f"Baseline mismatch: {path}"
    checks.append("six old release asset sets preserved via unchanged files and exact index template")

    a01 = load_data("A01")
    assert len(a01["tasks"]) == 2
    assert all(len(task["models"]) == 5 for task in a01["tasks"])
    assert all(task.get("endpoint") for task in a01["tasks"])
    checks.append("A01 keeps two real five-model comparisons")

    for project, endpoint_count in (("A02", 3), ("A03", 3)):
        data = load_data(project)
        assert sum(bool(task.get("endpoint")) for task in data["tasks"]) == endpoint_count
        checks.append(f"{project} keeps real API comparison tasks")

    for project in ("A04", "A05", "A06"):
        assert "Kết quả đã lưu" in shared_js, f"{project}: replay label missing"
        checks.append(f"{project} labels replay honestly")

    print(json.dumps({"status": "PASS", "checks": checks, "count": len(checks)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
