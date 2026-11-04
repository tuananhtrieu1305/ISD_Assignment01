"""Read-only dependency audit, inventory and reference extraction for Phase34."""

import argparse
import json
import xml.etree.ElementTree as ET
import zipfile

from scripts.prepare_phase33 import LOCKS
from src.common.artifact_core import sha256_file, write_once
from src.common.contracts import ROOT, read_json

BASE = ROOT / "artifacts/manifests/phase34"
PARENTS = [*LOCKS, "artifacts/manifests/phase33/experiment_lock.json"]


def preserve(name):
    members, refs = {}, []
    for relative in PARENTS:
        path = ROOT / relative
        refs.append({"path": relative, "sha256": sha256_file(path)})
        for row in read_json(path)["files"]:
            if row["path"] in members and members[row["path"]] != row["sha256"]:
                raise ValueError("Conflicting frozen hash " + row["path"])
            members[row["path"]] = row["sha256"]
    for index, (name_file, expected) in enumerate(sorted(members.items()), 1):
        path = ROOT / name_file
        if not path.resolve().is_relative_to(ROOT) or path.is_symlink() or sha256_file(path) != expected:
            raise ValueError("Protected file changed " + name_file)
        if index % 5000 == 0:
            print(f"Protected {index}/{len(members)}", flush=True)
    proof = {
        "status": "PASS",
        "locks": refs,
        "unique_protected_files": len(members),
        "historical_test_evaluation_executed": False,
    }
    write_once(BASE / (name + ".json"), proof)
    print(json.dumps(proof), flush=True)


def reference():
    path = ROOT / "releases/v2/references/A06_Assignment_Report.docx"
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
        styles = ET.fromstring(archive.read("word/styles.xml"))
        samples = ["".join(p.itertext()) for p in document.findall("./w:body/w:p", namespace)]
        selected = [p for p in samples if len(p) > 100][:12]
        evidence = {
            "source": {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)},
            "sections_xml": [
                ET.tostring(s, encoding="unicode") for s in document.findall(".//w:sectPr", namespace)
            ],
            "styles_xml": [
                ET.tostring(s, encoding="unicode")
                for s in styles.findall("w:style", namespace)
                if s.get("{" + namespace["w"] + "}styleId") in {"Normal", "Heading1", "Heading2", "Caption"}
            ],
            "paragraph_samples": selected,
            "scope": "Read-only OOXML typography/text evidence, not rendered layout QA. No DOCX authored in Phase34; distillation/render gate remains Phase35.",
        }
    write_once(BASE / "reference_style_evidence.json", evidence)
    print("Reference XML extracted without modification")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["preserve-before", "preserve-after", "reference"])
    stage = parser.parse_args().stage
    if stage == "reference":
        reference()
    else:
        preserve(stage.replace("-", "_"))
