"""Capture the existing V2 demo inputs before retiring their source datasets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from term_paper.deployment.app.model_service import ModelService


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    service = ModelService(root)
    output = root / "data/processed/v2/demos"
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for use_case in ("diabetes", "eurosat", "customer", "aapl"):
        demo = service.demo(use_case)
        path = output / f"{use_case}.json"
        path.write_text(json.dumps(demo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest.append({
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
            "source": "V2 ModelService.demo; frozen before Phase 20 cleanup",
        })
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"demos": len(manifest), "output": str(output)}))


if __name__ == "__main__":
    main()
