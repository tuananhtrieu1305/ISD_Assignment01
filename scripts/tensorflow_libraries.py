"""Repair wheel-local library discovery as documented by TensorFlow's pip guide.

Only add symlinks INSIDE the selected project venv; never install a system driver.
Do not overwrite any existing path (uv cache contents may be hardlinked).
"""

import sys
from pathlib import Path

site = Path(sys.prefix) / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
if sys.argv[1:] == ["--library-path"]:
    print(":".join(str(path) for path in sorted((site / "nvidia").glob("*/lib"))))
    raise SystemExit(0)
target = site / "tensorflow"
if sys.argv[1:] == ["--cleanup"]:
    # Remove only links created by this helper, never framework-owned files.
    nvidia_root = (site / "nvidia").resolve()
    candidates = list(target.glob("*.so*")) + [Path(sys.prefix) / "bin/ptxas"]
    for candidate in candidates:
        if candidate.is_symlink() and candidate.resolve().is_relative_to(nvidia_root):
            candidate.unlink()
    if target.is_dir() and not any(target.iterdir()):
        target.rmdir()
    print("Removed only project-created NVIDIA library links")
    raise SystemExit(0)
if not target.is_dir():
    raise SystemExit("TensorFlow is not installed in the selected interpreter")
count = 0
for library in sorted((site / "nvidia").glob("*/lib/*.so*")):
    link = target / library.name
    if not link.exists() and not link.is_symlink():
        link.symlink_to(library)
        count += 1
ptxas = sorted((site / "nvidia").glob("*/bin/ptxas"))
link = Path(sys.prefix) / "bin/ptxas"
if ptxas and not link.exists() and not link.is_symlink():
    link.symlink_to(ptxas[0])
print(f"Configured {count} wheel-local CUDA library symlinks; ptxas present: {link.exists()}")
