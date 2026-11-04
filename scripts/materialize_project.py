"""Portable logical-path view builder; hardlink optimization, verified copy fallback."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def checked_path(root,relative):
    path=(root/relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("Path outside repository")
    return path


def checksum(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()


def materialize(root,rows,*,copy_only=False):
    count=0
    verified={}
    for row in rows:
        source=checked_path(root,row["source"])
        target=checked_path(root,row["target"])
        if source not in verified:
            if not source.is_file() or checksum(source)!=row["sha256"]:
                raise ValueError("Missing or changed canonical source: "+row["source"])
            verified[source]=row["sha256"]
        if verified[source]!=row["sha256"]: raise ValueError("Conflicting source identity")
        if target.exists():
            if checksum(target)!=row["sha256"]: raise FileExistsError("Refuse different view target")
            continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if copy_only:
            shutil.copyfile(source,target)
        else:
            try: os.link(source,target)
            except OSError: shutil.copyfile(source,target)
        count+=1
    return count


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",required=True)
    parser.add_argument("--copy-only",action="store_true")
    args=parser.parse_args()
    recipe=json.loads((ROOT/"docs/reorganization/phase2/runtime_view_map.json").read_text())
    rows=[r for r in recipe["files"] if r["project"]==args.project]
    if not rows: raise ValueError("Unknown/unmaterialized project")
    print({"project":args.project,"created":materialize(ROOT,rows,copy_only=args.copy_only),"symlinks_required":False})


if __name__=="__main__": main()
