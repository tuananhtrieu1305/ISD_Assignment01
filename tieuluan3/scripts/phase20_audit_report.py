"""Summarize per-file cleanup outcomes and compress the immutable audit inventories."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "artifacts/manifests/phase20"


def read_csv(path):
    source = path.open(encoding="utf-8-sig", newline="") if path.exists() else gzip.open(str(path) + ".gz", "rt", encoding="utf-8-sig", newline="")
    with source as handle:
        return list(csv.DictReader(handle))


def compressed_copy(path):
    target = Path(str(path) + ".gz")
    if not path.exists() and target.exists():
        return target
    with path.open("rb") as source, target.open("wb") as sink:
        with gzip.GzipFile(filename="", mode="wb", fileobj=sink, mtime=0) as stream:
            while block := source.read(1024 * 1024):
                stream.write(block)
    return target


def main():
    before = read_csv(AUDIT / "before-files.csv")
    after = {row["path"]: row for row in read_csv(AUDIT / "after-files.csv")}
    archived = {row["path"] for row in read_csv(ROOT / "releases/v2/source_snapshot_manifest.csv")}
    operations = read_csv(AUDIT / "operations.csv")
    moves = [(row["source"].replace("\\", "/"), row["destination"].replace("\\", "/")) for row in operations if row["action"] == "MIGRATE"]
    outcomes = []
    for row in before:
        original = row["path"]
        current = original
        for source, destination in moves:
            if current == source or current.startswith(source + "/"):
                current = destination + current[len(source):]
        if current in after:
            identical = row["sha256"] == after[current]["sha256"]
            disposition = "RETAINED_IDENTICAL" if identical else "RETAINED_UPDATED"
            recovery = current
        elif original in archived:
            disposition = "ARCHIVED_SOURCE"
            recovery = "releases/v2/source_snapshot.zip:" + original
        elif row["git_state"] == "tracked":
            disposition = "REMOVED_GIT_RECOVERABLE"
            recovery = "Git HEAD from git-head-before.txt:" + original
        else:
            disposition = "REMOVED_REGENERATABLE"
            recovery = row["reason"]
        outcomes.append({
            "original_path": original,
            "current_path": current if current in after else "",
            "bytes_before": row["bytes"],
            "sha256_before": row["sha256"],
            "outcome": disposition,
            "recovery": recovery,
        })
    outcome_path = AUDIT / "file-outcomes.csv"
    with outcome_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(outcomes[0]))
        writer.writeheader()
        writer.writerows(outcomes)
    counts = Counter(row["outcome"] for row in outcomes)
    compressed = []
    for filename in ("before-files.csv", "after-files.csv", "keep-list-before.csv", "file-outcomes.csv"):
        path = compressed_copy(AUDIT / filename)
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        compressed.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest})
    summary = {"outcomes": dict(counts), "files_before": len(before), "files_after": len(after), "compressed_manifests": compressed}
    (AUDIT / "outcomes-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
