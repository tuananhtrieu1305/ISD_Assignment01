"""Record manual PNG review witnesses; this is NOT automatic visual QA."""

import argparse
import json
import re
from scripts.phase35_runtime import ROOT, digest, write_once_json


def record(start, end, notes, candidate="candidate-r7"):
    if not re.fullmatch(r"candidate-r\d+", candidate):
        raise ValueError("Invalid candidate name")
    build = ROOT / "report/build/phase35" / f"{candidate}.build.json"
    directory = ROOT / "report/qa35" / candidate
    total = len(list(directory.glob("page-*.png")))
    if not 1 <= start <= end <= total:
        raise ValueError("Invalid reviewed range")
    base = ROOT / "artifacts/manifests/phase35/visual_batches" / candidate
    previous = []
    if base.exists():
        for p in sorted(base.glob("*.json")):
            previous.extend(json.loads(p.read_text())["pages"])
    if start != (max((r["page"] for r in previous), default=0) + 1):
        raise ValueError("Review must be sequential and not duplicated")
    pages = [
        {
            "page": number,
            "path": str((directory / f"page-{number}.png").relative_to(ROOT)),
            "sha256": digest(directory / f"page-{number}.png"),
        }
        for number in range(start, end + 1)
    ]
    receipt = {
        "candidate": candidate,
        "docx_sha256": json.loads(build.read_text())["sha256"],
        "reviewer": "assistant manual inspection via original PNG view_image",
        "automatic_visual_qa": False,
        "status": "PASS",
        "notes": notes,
        "pages": pages,
    }
    write_once_json(base / f"{start:03d}-{end:03d}.json", receipt)
    print(json.dumps({"reviewed": [start, end], "of": total, "status": "PASS"}))


def carry(source, destination):
    if source == destination or not all(re.fullmatch(r"candidate-r\d+", x) for x in [source, destination]):
        raise ValueError("Invalid review transfer")
    base = ROOT / "artifacts/manifests/phase35/visual_batches"
    witnesses = sorted((base / source).glob("*.json"))
    rows = []
    for witness in witnesses:
        evidence = json.loads(witness.read_text())
        if evidence["status"] != "PASS":
            raise ValueError("Cannot transfer failed review")
        rows.extend(evidence["pages"])
    if not rows or [r["page"] for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("Source review is not a contiguous prefix")
    for row in rows:
        target = ROOT / "report/qa35" / destination / f"page-{row['page']}.png"
        if digest(ROOT / row["path"]) != row["sha256"] or digest(target) != row["sha256"]:
            raise ValueError("PNG differs; manual reinspection required")
    record(
        1,
        len(rows),
        f"Carried from individually viewed {source} PNGs only after exact SHA-256 equality of every source/target page. Source witnesses: "
        + ",".join(p.name for p in witnesses),
        destination,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="candidate-r8")
    parser.add_argument("--carry-from")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    if args.carry_from:
        carry(args.carry_from, args.candidate)
    elif args.start and args.end and args.notes:
        record(args.start, args.end, args.notes, args.candidate)
    else:
        parser.error("Supply carry-from, or start/end/notes")


if __name__ == "__main__":
    main()
