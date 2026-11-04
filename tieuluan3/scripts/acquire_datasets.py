"""Phase23: bounded official downloads with persistent receipts, no extraction."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from urllib.parse import urlsplit

import requests

from src.common.acquisition import AcquisitionError, download_file, download_ranged_file, file_digest
from src.common.contracts import ROOT, read_json

CATALOG = ROOT / "experiments/configs/v3/acquisition_sources.json"
RECEIPTS = ROOT / "artifacts/manifests/phase23/receipts"


def acquire(dataset_id, offline=False):
    catalog = read_json(CATALOG)
    spec = catalog["sources"][dataset_id]
    receipt_path = RECEIPTS / f"{dataset_id}.json"
    prior = read_json(receipt_path) if receipt_path.exists() else None
    if prior and (prior["path"] != spec["path"] or prior["url"] != spec["url"]):
        raise AcquisitionError("Source changed: create a versioned snapshot instead of overwriting")
    if offline and (not prior or not (ROOT / spec["path"]).is_file()):
        raise AcquisitionError(f"No trusted receipt for offline reuse: {dataset_id}")
    allowed = {urlsplit(spec["url"]).hostname}
    if dataset_id == "ch3_cifar10":
        allowed.add("cave.cs.toronto.edu")
    if dataset_id == "ch1_imagenet_history":
        allowed.add("image-net.org")
    if dataset_id == "ch3_cifar10" and not (ROOT / spec["path"]).exists():
        result = download_ranged_file(
            "https://cave.cs.toronto.edu/kriz/cifar-10-binary.tar.gz",
            ROOT / spec["path"],
            total_bytes=170052171,
            allowed_hosts=allowed,
            expected_md5=spec["md5"],
            reserve_bytes=catalog["reserve_bytes"],
        )
    else:
        result = download_file(
            spec["url"],
            ROOT / spec["path"],
            max_bytes=spec["max_bytes"],
            expected_sha256=prior["sha256"] if prior else None,
            expected_md5=spec.get("md5"),
            allowed_hosts=allowed,
            reserve_bytes=catalog["reserve_bytes"],
        )
    if result["action"] == "downloaded":
        RECEIPTS.mkdir(parents=True, exist_ok=True)
        receipt = {
            **result,
            "url": spec["url"],
            "dataset_id": dataset_id,
            "path": spec["path"],
            "accessed_at": datetime.now(UTC).isoformat(),
            "catalog_sha256": file_digest(CATALOG),
        }
        # No receipt exists on first install. A failed/changed snapshot is never silently adopted.
        with receipt_path.open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    print(f"{dataset_id}: {result['action']} {result['size_bytes']} bytes {result['sha256']}", flush=True)
    return {"dataset_id": dataset_id, **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", action="append", choices=read_json(CATALOG)["sources"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Require receipts; never call network")
    args = parser.parse_args()
    ids = list(read_json(CATALOG)["sources"]) if args.all else args.dataset
    if not ids:
        parser.error("Choose --all or --dataset")
    errors, results = [], []

    def run(dataset_id):
        try:
            return acquire(dataset_id, args.offline)
        except (ValueError, OSError, requests.RequestException) as error:
            # Continue other independent sources; CLI still fails if any source fails.
            return {"dataset_id": dataset_id, "error": f"{type(error).__name__}: {error}"}

    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(run, ids):
            results.append(result)
            if "error" in result:
                errors.append(result)
                print(result, flush=True)
    directory = ROOT / "artifacts/manifests/phase23"
    directory.mkdir(parents=True, exist_ok=True)
    name = "offline_reuse.json" if args.offline else "acquisition_run.json"
    (directory / name).write_text(
        json.dumps(
            {"at": datetime.now(UTC).isoformat(), "results": results, "status": "FAIL" if errors else "PASS"},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
