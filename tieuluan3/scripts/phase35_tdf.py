"""Rootless TDF fallback, authenticated by the upstream locked SHA-256."""

import json
import os
from pathlib import Path
import resource
import shlex
import shutil
import subprocess
import tarfile

from scripts.phase35_runtime import ROOT, RUNTIME, checked_relative, digest, download, write_once_json

BASE = ROOT / "artifacts/manifests/phase35/local_toolchain_r2"


def deb_members(archive):
    members = []
    for member in archive.getmembers():
        path = Path(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe archive path")
        if member.isfile() and "DEBS" in path.parts and path.suffix == ".deb":
            members.append(member)
    if not members or len({Path(m.name).name for m in members}) != len(members):
        raise ValueError("Missing or duplicate DEB targets")
    if sum(m.size for m in members) > 500 * 1024**2:
        raise ValueError("Archive expanded DEB budget exceeded")
    return members


def install():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    lock = json.loads((BASE / "tdf_lock.json").read_text())
    target = RUNTIME / "tdf"
    if str(target) != lock["root"] or shutil.disk_usage(ROOT).free < 5 * 1024**3:
        raise RuntimeError("Target or disk guard failed")
    target.mkdir(exist_ok=True)
    packages = target / "packages"
    packages.mkdir(exist_ok=True)
    path = download(lock, packages)
    sysroot = target / "sysroot"
    sysroot.mkdir(exist_ok=True)
    package_rows = []
    with tarfile.open(path, "r:gz") as archive:
        for member in deb_members(archive):
            destination = checked_relative(packages, Path(member.name).name)
            with archive.extractfile(member) as source, destination.open("wb") as out:
                shutil.copyfileobj(source, out)
            package_rows.append(
                {"name": destination.name, "sha256": digest(destination), "bytes": destination.stat().st_size}
            )
            subprocess.run(
                ["dpkg-deb", "--extract", str(destination), str(sysroot)], check=True, capture_output=True
            )
    for directory, dirs, files in os.walk(sysroot, followlinks=False):
        for name in dirs + files:
            link = Path(directory) / name
            if link.is_symlink() and os.readlink(link).startswith("/"):
                original = os.readlink(link)
                new = checked_relative(sysroot, original.lstrip("/"))
                link.unlink()
                link.symlink_to(os.path.relpath(new, link.parent))
    program = sysroot / "opt/libreoffice26.2/program"
    binary = program / "soffice"
    wrapper = RUNTIME / "bin/soffice"
    old_hash = digest(wrapper)
    libraries = str(program) + ":" + str(RUNTIME / "sysroot/usr/lib/x86_64-linux-gnu")
    content = (
        "#!/bin/sh\nset -eu\nulimit -c 0\nunset URE_BOOTSTRAP UNO_PATH\n"
        f"export LD_LIBRARY_PATH={shlex.quote(libraries)}\n"
        f"export FONTCONFIG_FILE={shlex.quote(str(RUNTIME / 'fonts.conf'))}\n"
        f"export XDG_CACHE_HOME={shlex.quote(str(RUNTIME / 'cache'))}\n"
        "export SAL_USE_VCLPLUGIN=svp\nexport SAL_DISABLE_OPENCL=1\n"
        f'exec {shlex.quote(str(binary))} "$@"\n'
    )
    wrapper.write_text(content, encoding="utf-8")
    wrapper.chmod(0o755)
    probe = subprocess.run(
        [str(wrapper), "--headless", "--version"], capture_output=True, text=True, timeout=60
    )
    print(probe.stdout + probe.stderr, flush=True)
    write_once_json(
        BASE / "probe.json",
        {
            "exit_code": probe.returncode,
            "stdout": probe.stdout,
            "stderr": probe.stderr,
            "archive_sha256": digest(path),
            "deb_files": package_rows,
            "binary": str(binary),
            "wrapper_before_sha256": old_hash,
            "wrapper_sha256": digest(wrapper),
            "system_install_performed": False,
        },
    )
    probe.check_returncode()


if __name__ == "__main__":
    install()
