"""Version-locked, rootless local document toolchain, authorized by the user.

Never installs into the GPU environments or the system package database.
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import urllib.parse
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/manifests/phase35/local_toolchain_r1"
RUNTIME = Path("/home/tuananh/.local/share/ai-term-paper-docs-v1")
GPU = Path("/home/tuananh/.local/share/ai-term-paper-v3")
PINS = [
    "libreoffice-writer-nogui=4:24.2.7-0ubuntu0.24.04.7",
    "libreoffice-core-nogui=4:24.2.7-0ubuntu0.24.04.7",
    "poppler-utils=24.02.0-1ubuntu9.11",
]


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def checked_relative(root, relative):
    root, relative = Path(root).resolve(), Path(relative)
    path = root / relative
    if relative.is_absolute() or not path.resolve().is_relative_to(root):
        raise ValueError("Unsafe relative path")
    return path


def write_once_json(path, value):
    path = Path(path)
    content = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError("Refusing to overwrite evidence: " + str(path))
        return
    with path.open("xb") as stream:
        stream.write(content)


def parse_apt_uris(text):
    rows = []
    for line in text.splitlines():
        if not line.startswith("'"):
            continue
        parts = shlex.split(line)
        if len(parts) < 3:
            raise ValueError("Incomplete apt URI record")
        uri = urllib.parse.urlparse(parts[0])
        size = int(parts[2])
        if (
            uri.scheme not in {"http", "https"}
            or uri.hostname not in {"archive.ubuntu.com", "security.ubuntu.com"}
            or uri.username
            or uri.password
            or Path(parts[1]).name != parts[1]
            or not parts[1].endswith(".deb")
            or size <= 0
            or size > 200 * 1024 * 1024
        ):
            raise ValueError("Unapproved apt source or target")
        rows.append({"url": uri._replace(scheme="https").geturl(), "filename": parts[1], "bytes": size})
    if not rows or len({row["filename"] for row in rows}) != len(rows):
        raise ValueError("Apt records must be nonempty and unique")
    return rows


def select_metadata(row, text):
    source_name = urllib.parse.unquote(Path(urllib.parse.urlparse(row.get("url", row["filename"])).path).name)
    matches = []
    for paragraph in text.strip().split("\n\n"):
        fields = dict(
            line.split(": ", 1)
            for line in paragraph.splitlines()
            if ": " in line and not line.startswith(" ")
        )
        if Path(fields.get("Filename", "")).name != source_name:
            continue
        if int(fields.get("Size", -1)) != row["bytes"] or not re.fullmatch(
            r"[0-9a-f]{64}", fields.get("SHA256", "")
        ):
            raise ValueError("Bad apt size or SHA-256 metadata")
        match = {"package": fields["Package"], "version": fields["Version"], "sha256": fields["SHA256"]}
        if match not in matches:
            matches.append(match)
    if len(matches) != 1:
        raise ValueError("Expected exact apt metadata match: " + source_name)
    return matches[0]


def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs).stdout


def relocate_configuration(text, sysroot):
    pattern = r"(?<![A-Za-z0-9_/.-])(?P<uri>file://)?(?P<path>/(?:usr/(?:lib|share)|etc|var/(?:lib|spool))/libreoffice)(?=/|\s|$)"
    return re.sub(pattern, lambda m: (m["uri"] or "") + str(sysroot) + m["path"], text)


def relocate_program_configuration():
    sysroot = RUNTIME / "sysroot"
    program = sysroot / "usr/lib/libreoffice/program"
    rows = []
    for path in sorted(program.glob("*rc")):
        text = path.read_text(encoding="utf-8")
        revised = relocate_configuration(text, sysroot)
        if revised != text:
            before = digest(path)
            path.write_text(revised, encoding="utf-8")
            rows.append(
                {
                    "path": str(path.relative_to(sysroot)),
                    "before_sha256": before,
                    "after_sha256": digest(path),
                }
            )
    write_once_json(BASE / "configuration_relocation.json", {"changes": rows, "system_files_modified": False})
    completed = subprocess.run(
        [str(RUNTIME / "bin/soffice"), "--headless", "--version"], capture_output=True, text=True, timeout=60
    )
    print(completed.stdout + completed.stderr, flush=True)
    completed.check_returncode()


def resolve_apt():
    text = run(
        [
            "apt-get",
            "--print-uris",
            "--assume-yes",
            "--download-only",
            "--no-install-recommends",
            "install",
            *PINS,
        ]
    )
    rows = parse_apt_uris(text)
    for row in rows:
        package, version, _ = row["filename"].rsplit("_", 2)
        spec = package + "=" + urllib.parse.unquote(version)
        row.update(select_metadata(row, run(["apt-cache", "show", spec])))
    lock = {
        "deviation": "phase35.local-toolchain.1",
        "distribution": "Ubuntu noble amd64",
        "requested": PINS,
        "packages": rows,
        "system_install_performed": False,
        "root": str(RUNTIME),
    }
    write_once_json(BASE / "apt_lock.json", lock)
    print(json.dumps({"packages": len(rows), "download_bytes": sum(r["bytes"] for r in rows)}), flush=True)


def download(row, directory):
    destination = checked_relative(directory, row["filename"])
    if destination.exists():
        if destination.stat().st_size != row["bytes"] or digest(destination) != row["sha256"]:
            raise ValueError("Existing package hash mismatch")
        return destination
    temporary = destination.with_name(destination.name + "." + uuid.uuid4().hex + ".part")
    try:
        request = urllib.request.Request(row["url"], headers={"User-Agent": "AI-term-paper-phase35/1"})
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open("xb") as stream:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > row["bytes"]:
                    raise ValueError("Package download exceeds locked size")
                stream.write(chunk)
        if temporary.stat().st_size != row["bytes"] or digest(temporary) != row["sha256"]:
            raise ValueError("Downloaded package size/hash mismatch")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    print("Verified " + row["filename"], flush=True)
    return destination


def private_fonts():
    source = Path("/mnt/c/Windows/Fonts")
    target = RUNTIME / "fonts"
    target.mkdir(exist_ok=True)
    names = [
        "calibri.ttf",
        "calibrib.ttf",
        "calibrii.ttf",
        "calibriz.ttf",
        "times.ttf",
        "timesbd.ttf",
        "timesi.ttf",
        "timesbi.ttf",
        "consola.ttf",
        "consolab.ttf",
        "consolai.ttf",
        "consolaz.ttf",
        "cambria.ttc",
        "seguisym.ttf",
    ]
    rows = []
    for name in names:
        path = source / name
        if not path.is_file():
            raise FileNotFoundError("Required licensed local font: " + name)
        shutil.copyfile(path, target / name)
        rows.append({"name": name, "sha256": digest(path), "bytes": path.stat().st_size})
    config = (
        '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
        '<include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
        f"<dir>{target}</dir><cachedir>{RUNTIME / 'font-cache'}</cachedir></fontconfig>\n"
    )
    (RUNTIME / "fonts.conf").write_text(config, encoding="utf-8")
    write_once_json(BASE / "local_fonts.json", {"local_only_not_redistributable": True, "files": rows})


def install_apt():
    lock = json.loads((BASE / "apt_lock.json").read_text())
    if lock["root"] != str(RUNTIME) or RUNTIME == GPU or RUNTIME.is_relative_to(GPU):
        raise ValueError("Toolchain must stay separate from GPU runtime")
    if shutil.disk_usage(ROOT).free < 5 * 1024**3:
        raise RuntimeError("Host reserve below 5 GiB")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    archives = RUNTIME / "packages"
    archives.mkdir(exist_ok=True)
    sysroot = RUNTIME / "sysroot"
    sysroot.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(lambda row: download(row, archives), lock["packages"]))
    for path in paths:
        run(["dpkg-deb", "--extract", str(path), str(sysroot)])
    relocated = []
    for directory, dirs, files in os.walk(sysroot, followlinks=False):
        for name in dirs + files:
            link = Path(directory) / name
            if link.is_symlink() and os.readlink(link).startswith("/"):
                original = os.readlink(link)
                target = checked_relative(sysroot, original.lstrip("/"))
                link.unlink()
                link.symlink_to(os.path.relpath(target, link.parent))
                relocated.append({"path": str(link.relative_to(sysroot)), "original": original})
    private_fonts()
    bin_dir = RUNTIME / "bin"
    bin_dir.mkdir(exist_ok=True)
    libraries = ":".join(
        str(sysroot / name)
        for name in ["usr/lib/x86_64-linux-gnu", "usr/lib/libreoffice/program", "usr/lib/ure/lib"]
    )
    executables = {
        "soffice": sysroot / "usr/lib/libreoffice/program/soffice",
        "pdfinfo": sysroot / "usr/bin/pdfinfo",
        "pdftoppm": sysroot / "usr/bin/pdftoppm",
    }
    for name, binary in executables.items():
        content = (
            "#!/bin/sh\nset -eu\n"
            f"export LD_LIBRARY_PATH={shlex.quote(libraries)}\n"
            f"export FONTCONFIG_FILE={shlex.quote(str(RUNTIME / 'fonts.conf'))}\n"
            f"export XDG_CACHE_HOME={shlex.quote(str(RUNTIME / 'cache'))}\n"
            f'exec {shlex.quote(str(binary))} "$@"\n'
        )
        wrapper = bin_dir / name
        wrapper.write_text(content, encoding="utf-8")
        wrapper.chmod(0o755)
    write_once_json(BASE / "extraction.json", {"packages": len(paths), "absolute_links_relocated": relocated})
    for name in executables:
        args = [str(bin_dir / name), "--version" if name == "soffice" else "-v"]
        completed = subprocess.run(args, check=True, text=True, capture_output=True, timeout=60)
        print(completed.stdout + completed.stderr, flush=True)


def python_setup():
    uv = str(GPU / "bin/uv")
    python = str(GPU / ".venv-torch/bin/python")
    env = {**os.environ, "UV_CACHE_DIR": str(RUNTIME / "uv-cache"), "UV_LINK_MODE": "copy"}
    requirements = ROOT / "experiments/environment/docs35/requirements.in"
    lock = ROOT / "experiments/environment/docs35/requirements.lock"
    if not lock.exists():
        run(
            [
                uv,
                "pip",
                "compile",
                str(requirements),
                "--python",
                python,
                "--generate-hashes",
                "--output-file",
                str(lock),
            ],
            env=env,
        )
        print("Document requirements compiled with hashes", flush=True)
    if not (RUNTIME / ".venv/bin/python").exists():
        print(run([uv, "venv", "--python", python, str(RUNTIME / ".venv")], env=env), flush=True)
    print(
        run(
            [uv, "pip", "sync", "--python", str(RUNTIME / ".venv/bin/python"), "--require-hashes", str(lock)],
            env=env,
        ),
        flush=True,
    )
    print(
        run(
            [
                str(RUNTIME / ".venv/bin/python"),
                "-c",
                "import docx,pdf2image,fitz,markdown_it; print('DOCX/PDF dependencies PASS')",
            ]
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", required=True, choices=["resolve-apt", "install-apt", "python-setup", "relocate-config"]
    )
    stage = parser.parse_args().stage
    {
        "resolve-apt": resolve_apt,
        "install-apt": install_apt,
        "python-setup": python_setup,
        "relocate-config": relocate_program_configuration,
    }[stage]()


if __name__ == "__main__":
    main()
