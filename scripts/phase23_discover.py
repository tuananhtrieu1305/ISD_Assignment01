"""Read official source metadata and HEAD responses; never downloads large data."""

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "uci_diabetes_metadata": ("GET", "https://archive.ics.uci.edu/api/dataset?id=891"),
    "ames_tree": ("GET", "https://api.github.com/repos/topepo/AmesHousing/git/trees/master?recursive=1"),
    "ames_description": ("GET", "https://raw.githubusercontent.com/topepo/AmesHousing/master/DESCRIPTION"),
    "eurosat_metadata": ("GET", "https://zenodo.org/api/records/7711810"),
    "cdc_license_metadata": (
        "GET",
        "https://www.kaggle.com/api/v1/datasets/view/alexteboul/diabetes-health-indicators-dataset",
    ),
    "worldbank_page": ("GET", "https://www.worldbank.org/en/research/commodity-markets"),
    "bis_page": ("GET", "https://data.bis.org/bulkdownload"),
    "iris_zip": ("HEAD", "https://archive.ics.uci.edu/static/public/53/iris.zip"),
    "cdc_csv": ("HEAD", "https://archive.ics.uci.edu/static/public/891/data.csv"),
    "bank_zip": ("HEAD", "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"),
    "power_zip": (
        "HEAD",
        "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip",
    ),
    "bis_zip": ("HEAD", "https://data.bis.org/static/bulk/WS_SPP_csv_col.zip"),
    "ames_original": ("HEAD", "https://jse.amstat.org/v19n3/decock/AmesHousing.txt"),
    "mnist": ("HEAD", "https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz"),
    "cifar_binary": ("HEAD", "https://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz"),
    "idrid": (
        "HEAD",
        "https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid",
    ),
}


def probe(item):
    name, (method, url) = item
    result = {"name": name, "url": url, "method": method}
    try:
        with requests.request(
            method,
            url,
            stream=True,
            timeout=(15, 45),
            headers={"User-Agent": "AI-Term-Paper-V3 academic source verifier"},
            allow_redirects=True,
        ) as response:
            result.update(
                status=response.status_code,
                final_url=response.url,
                headers={
                    key: response.headers.get(key)
                    for key in ("Content-Length", "Content-Type", "Last-Modified", "ETag")
                },
            )
            if method == "GET":
                content = bytearray()
                for chunk in response.iter_content(65536):
                    content.extend(chunk)
                    if len(content) > 2 * 1024**2:
                        raise ValueError("Metadata exceeds 2 MiB")
                result["body_sha256"] = hashlib.sha256(content).hexdigest()
                text = content.decode("utf-8", errors="replace")
                result["body"] = (
                    json.loads(text) if "json" in response.headers.get("Content-Type", "") else text
                )
    except (requests.RequestException, ValueError) as error:
        result["error"] = str(error)
    return result


def main():
    directory = ROOT / "artifacts/manifests/phase23"
    if (directory / "source_discovery.json").exists():
        print(
            "Existing source-discovery evidence preserved; no network. Use a new versioned snapshot for refresh."
        )
        return
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(probe, TARGETS.items()))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "source_discovery.json").write_text(
        json.dumps({"at": datetime.now(UTC).isoformat(), "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for result in results:
        print(result["name"], result.get("status"), result.get("headers"), result.get("error", ""))
        body = result.get("body")
        if result["name"] == "ames_tree" and isinstance(body, dict):
            print(
                "tree",
                body.get("sha"),
                [row["path"] for row in body.get("tree", []) if row["path"].startswith("data-raw")],
            )
        elif result["name"] == "ames_description":
            print(body)
        elif result["name"] == "uci_diabetes_metadata" and isinstance(body, dict):
            print(json.dumps(body.get("data", {}), ensure_ascii=False)[:2200])
        elif result["name"] == "eurosat_metadata" and isinstance(body, dict):
            print("files", body.get("files"), "license", body.get("metadata", {}).get("license"))
        elif result["name"] == "cdc_license_metadata" and isinstance(body, dict):
            print({key: value for key, value in body.items() if "license" in key.lower()})
        elif result["name"] in {"worldbank_page", "bis_page"} and isinstance(body, str):
            print(re.findall(r"(?:href|src)=[\"\']([^\"\']+(?:xlsx|WS_SPP|Pink|pink)[^\"\']*)", body)[:30])


if __name__ == "__main__":
    main()
