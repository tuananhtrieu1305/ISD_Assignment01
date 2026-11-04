"""Validate the user-supplied IDRiD Disease Grading release without extraction."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd
from PIL import Image

from src.common.acquisition import archive_members, file_digest
from src.common.contracts import ROOT
from src.common.source_inspection import require

MANUAL = ROOT / "data/raw/ch3/idrid/manual"


def official_split(name):
    matches = [
        split
        for split, word in (("train", "train(?:ing)?"), ("test", "test(?:ing)?"))
        if re.search(rf"(?<![a-z]){word}(?![a-z])", str(name).lower())
    ]
    require(len(matches) == 1, f"Cannot establish unambiguous official split of {name}")
    return matches[0]


def inspect_idrid(directory=MANUAL):
    files = (
        sorted(path for path in Path(directory).rglob("*") if path.is_file())
        if Path(directory).exists()
        else []
    )
    files = [path for path in files if path.suffix.lower() in {".zip", ".csv"}]
    if not files:
        return {
            "status": "pending_user_download",
            "files": [],
            "records": None,
            "reason": "User chose to download IDRiD later; no replacement dataset or fabricated counts.",
        }
    images, labels, split_counts, manifests = set(), {}, Counter(), []
    shapes, license_files, image_members = set(), [], {}

    def consume_csv(content, name):
        frame = pd.read_csv(io.BytesIO(content))
        required = {"Image name", "Retinopathy grade"}
        if not required.issubset(frame.columns):
            return
        split = official_split(name)
        for _, row in frame.iterrows():
            image_name = Path(str(row["Image name"])).stem
            key = f"{split}/{image_name}"
            grade = row["Retinopathy grade"]
            require(
                pd.notna(grade) and float(grade).is_integer() and int(grade) in range(5), "Invalid DR grade"
            )
            require(key not in labels, f"Duplicate image label {key}")
            labels[key] = {"grade": int(grade), "official_split": split, "image_name": image_name}
            split_counts[split] += 1

    for path in files:
        require(not path.is_symlink(), "Manual input cannot be a symlink")
        require(path.stat().st_size <= 4 * 1024**3, "Manual archive exceeds 4 GiB bound")
        manifests.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": file_digest(path),
                "size_bytes": path.stat().st_size,
            }
        )
        if path.suffix.lower() == ".csv":
            require(path.stat().st_size < 2 * 1024**2, "IDRiD CSV too large")
            consume_csv(path.read_bytes(), path.name)
            continue
        # Validate every member before inspecting images/CSVs. No archive extraction.
        list(archive_members(path, max_expanded_bytes=12 * 1024**3, max_members=5000))
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if Path(name).name.lower() in {"license.txt", "cc-by-4.0.txt"}:
                    require(archive.getinfo(name).file_size < 65536, "License file too large")
                    raw = archive.read(name)
                    text = " ".join(raw.decode("utf-8-sig").split())
                    declaration = (
                        "IDRiD dataset" in text
                        and "Creative Commons Attribution 4.0 International License" in text
                    )
                    full_text = (
                        Path(name).name.lower() == "cc-by-4.0.txt"
                        and "Creative Commons" in text
                        and "4.0" in text
                    )
                    if declaration or full_text:
                        license_files.append(
                            {
                                "archive": path.relative_to(ROOT).as_posix(),
                                "member": name,
                                "sha256": hashlib.sha256(raw).hexdigest(),
                                "size_bytes": len(raw),
                                "role": "dataset_declaration" if declaration else "full_license_text",
                            }
                        )
                if name.lower().endswith(".csv"):
                    require(archive.getinfo(name).file_size < 2 * 1024**2, "IDRiD CSV too large")
                    consume_csv(archive.read(name), name)
                elif re.fullmatch(r"IDRiD_\d+\.(jpg|jpeg)", Path(name).name, re.IGNORECASE):
                    key = f"{official_split(name)}/{Path(name).stem}"
                    require(key not in images, f"Duplicate image {key}")
                    with archive.open(name) as handle, Image.open(handle) as picture:
                        picture.load()
                        shapes.add((picture.width, picture.height, picture.mode))
                    image_members[key] = {"archive": path.relative_to(ROOT).as_posix(), "member": name}
                    images.add(key)
    require(
        split_counts == {"train": 413, "test": 103},
        f"Require grading 413/103 labels, got {dict(split_counts)}",
    )
    require(images == set(labels) and len(images) == 516, "Images do not match the 516 grading labels")
    return {
        "status": "ready",
        "files": manifests,
        "records": 516,
        "official_split_counts": dict(split_counts),
        "labels": labels,
        "image_members": image_members,
        "identity_policy": "official_split/image_stem",
        "native_image_shapes": [list(shape) for shape in sorted(shapes)],
        "license_status": "approved"
        if {row["role"] for row in license_files} == {"dataset_declaration", "full_license_text"}
        else "pending",
        "license_identifier": "CC-BY-4.0" if license_files else None,
        "license_evidence": license_files,
        "checks": [
            "all_member_hashes",
            "safe_archive_paths",
            "image_decode",
            "label_image_identity",
            "official_413_103_split",
            "grade_0_to_4",
        ],
    }


def inspection_summary(result):
    return {
        **{
            key: value
            for key, value in result.items()
            if key not in {"labels", "image_members", "files", "status"}
        },
        "features": None,
        "unit": "fundus RGB images; official 413 train + 103 test",
        "columns": [
            {"name": "image_id", "dtype": "string", "role": "id"},
            {"name": "official_split", "dtype": "category", "role": "group"},
            {"name": "dr_grade", "dtype": "integer", "role": "target"},
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    result = inspect_idrid()
    directory = ROOT / "artifacts/manifests/phase23"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "idrid_manual.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: value for key, value in result.items() if key not in {"labels", "image_members"}}, indent=2
        )
    )
    return args.require_ready and result["status"] != "ready"


if __name__ == "__main__":
    raise SystemExit(main())
