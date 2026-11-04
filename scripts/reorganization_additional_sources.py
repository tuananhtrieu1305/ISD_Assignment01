"""Keep historical mobile sources as reference without their build environments."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/reorganization"
records = []
for project, ref in [("A01", "be8442eff"), ("A02", "0c27b1d2f"), ("A03", "d68985ea4"), ("A04", "3be831e88")]:
    command = ["git", "-C", str(ROOT)]
    commit = subprocess.check_output(command + ["rev-parse", ref], text=True).strip()
    tree = subprocess.check_output(command + ["ls-tree", "-rlz", commit, "mobile"])
    for item in tree.split(b"\0"):
        if not item:
            continue
        header, rawpath = item.split(b"\t", 1)
        mode, kind, oid, size = header.decode().split()
        path = rawpath.decode()
        if any(p in {"node_modules", ".expo", "dist", "build", ".git"} for p in Path(path).parts):
            continue
        if Path(path).name.startswith(".env"):
            continue
        payload = subprocess.check_output(command + ["show", f"{commit}:{path}"])
        assert len(payload) == int(size)
        assert hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest() == oid
        target = OUT / "staging" / project / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == payload
        else:
            target.write_bytes(payload)
        records.append({"project": project, "commit": commit, "path": path, "oid": oid, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "staging_path": target.relative_to(ROOT).as_posix(), "role": "historical-mobile-reference-not-active-web"})
(OUT / "supplementary_manifest.json").write_text(json.dumps({"files": records, "count": len(records), "bytes": sum(r["bytes"] for r in records), "reason": "preserve original assignment mobile source; no Expo/npm install, execution or mobile app rewrite"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Additional historical mobile sources preserved: {len(records)} files")
