"""End-to-end acceptance verifier for Phase 6 deployment."""

import json
import re
from pathlib import Path

from PIL import Image

from term_paper.deployment.app.model_service import MODEL_REGISTRY, ModelService, sha256_file


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
TERM_ROOT = WORKSPACE_ROOT / "term_paper"
DEPLOY_ROOT = TERM_ROOT / "deployment"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_registry_and_demos():
    registry = json.loads((DEPLOY_ROOT / "model_registry.json").read_text(encoding="utf-8"))["models"]
    require(set(registry) == set(MODEL_REGISTRY), "registry model IDs")
    service = ModelService(WORKSPACE_ROOT)
    require(service.health()["status"] == "ok", "health status")
    for model_id, runtime in MODEL_REGISTRY.items():
        public = registry[model_id]
        require(public["version"] == runtime["version"], f"version mismatch {model_id}")
        require(public["model_sha256"] == runtime["model_sha256"], f"registry hash {model_id}")
        require(sha256_file(WORKSPACE_ROOT / runtime["model"]) == runtime["model_sha256"], f"model hash {model_id}")
        actual_preprocessors = []
        for item in runtime["preprocessors"]:
            require(sha256_file(WORKSPACE_ROOT / item["path"]) == item["sha256"], f"preprocessor hash {model_id}")
            actual_preprocessors.append(item["sha256"])
        require(public["preprocessor_sha256"] == actual_preprocessors, f"preprocessor registry {model_id}")

    outputs = {
        "diabetes": service.predict_diabetes(service.demo("diabetes")["input"]),
        "eurosat": service.predict_eurosat(service.demo("eurosat")["input"]["image_base64"]),
        "customer": service.predict_customer(service.demo("customer")["input"]["sequence"]),
        "aapl": service.predict_aapl(service.demo("aapl")["input"]["sequence"]),
    }
    require("probability" in outputs["diabetes"], "diabetes demo")
    require(len(outputs["eurosat"]["top_classes"]) == 3, "EuroSAT top-3")
    require("probability" in outputs["customer"], "customer demo")
    require("naive_last_close_usd" in outputs["aapl"], "AAPL baseline")
    require("không phải chẩn đoán" in outputs["diabetes"]["warning"].lower(), "medical warning")
    require("không phải khuyến nghị đầu tư" in outputs["aapl"]["warning"].lower(), "financial warning")
    return len(outputs)


def verify_deployment_files():
    required = [
        "app/server.py", "app/model_service.py", "app/schemas.py", "app/static/index.html",
        "app/static/styles.css", "app/static/app.js", "requirements.txt", "Dockerfile",
        "README.md", "model_registry.json", "coverage_summary.md", "docker_smoke_test.json",
    ]
    for relative in required:
        path = DEPLOY_ROOT / relative
        require(path.is_file() and path.stat().st_size > 0, f"missing deployment file {relative}")
    dockerfile = (DEPLOY_ROOT / "Dockerfile").read_text(encoding="utf-8")
    require("USER modelapp" in dockerfile and "HEALTHCHECK" in dockerfile, "Docker hardening")
    smoke = json.loads((DEPLOY_ROOT / "docker_smoke_test.json").read_text(encoding="utf-8"))
    require(smoke["health"]["status"] == "ok" and smoke["health"]["verified_models"] == 4, "Docker smoke test")
    coverage = (DEPLOY_ROOT / "coverage_summary.md").read_text(encoding="utf-8")
    require("85,3%" in coverage, "deployment coverage evidence")
    server = (DEPLOY_ROOT / "app/server.py").read_text(encoding="utf-8")
    require("Content-Security-Policy" in server and "MAX_JSON_BYTES" in server, "server safeguards")
    require(not re.search(r"LOGGER\.\w+\([^\n]*payload", server), "payload must not be logged")
    return len(required)


def verify_report_and_screenshots():
    chapter = (TERM_ROOT / "report/sections/05_trien_khai.md").read_text(encoding="utf-8")
    words = len(re.findall(r"\b[\wÀ-ỹ–-]+\b", chapter, flags=re.UNICODE))
    require(1300 <= words <= 2600, f"deployment section word count {words}")
    require(len(re.findall(r"^## 5\.[1-6]\.", chapter, flags=re.MULTILINE)) == 6, "section 5 heading coverage")
    require(len(re.findall(r"^!\[", chapter, flags=re.MULTILINE)) == 2, "deployment figure references")
    require("không phải chẩn đoán y khoa" in chapter.lower(), "report medical warning")
    require("không phải khuyến nghị đầu tư" in chapter.lower(), "report financial warning")
    screenshots = [
        TERM_ROOT / "report/assets/deployment/phase6_overview.png",
        TERM_ROOT / "report/assets/deployment/phase6_aapl_result.png",
    ]
    for path in screenshots:
        require(path.is_file() and path.stat().st_size > 20_000, f"missing/small screenshot {path.name}")
        with Image.open(path) as image:
            require(image.width >= 1200 and image.height >= 800, f"small dimensions {path.name}")
    return words, len(screenshots)


def main():
    demos = verify_registry_and_demos()
    files = verify_deployment_files()
    words, screenshots = verify_report_and_screenshots()
    print("PHASE 6 VERIFICATION: PASS")
    print(f"Deterministic demos: {demos}")
    print(f"Deployment files: {files}")
    print(f"Section 5 words: {words}")
    print(f"Screenshots: {screenshots}")


if __name__ == "__main__":
    main()
