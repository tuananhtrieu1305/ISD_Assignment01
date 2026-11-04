"""Bounded HTTPS acquisition and archive hashing; never extracts or unpickles data."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tarfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit

import requests

RESERVE_BYTES = 5 * 1024**3


class AcquisitionError(ValueError):
    """Untrusted input, failed integrity check, or insufficient storage."""


def file_digest(path, algorithm="sha256"):
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_member_name(name):
    path = PurePosixPath(name)
    if not name or "\\" in name or "\x00" in name or ":" in name or path.is_absolute() or ".." in path.parts:
        raise AcquisitionError(f"Unsafe archive member: {name!r}")
    return path.as_posix()


def storage_required(download_bytes, expanded_bytes, reserve_bytes=RESERVE_BYTES):
    if min(download_bytes, expanded_bytes, reserve_bytes) < 0:
        raise ValueError("Storage estimates must be nonnegative")
    return download_bytes + expanded_bytes + reserve_bytes


def _url_allowed(url, allowed_hosts):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed_hosts
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise AcquisitionError("Only credential-free HTTPS on approved source hosts is allowed")


def download_file(
    url,
    path,
    *,
    max_bytes,
    allowed_hosts,
    expected_sha256=None,
    expected_md5=None,
    opener=None,
    reserve_bytes=RESERVE_BYTES,
):
    """Never overwrites an existing file; trusted hashes make repeat calls offline."""
    _url_allowed(url, allowed_hosts)
    path = Path(path)
    if path.is_symlink():
        raise AcquisitionError("Download destination cannot be a symlink")
    if path.exists():
        if not expected_sha256 or file_digest(path) != expected_sha256:
            raise AcquisitionError(f"Existing file lacks a matching trusted SHA-256: {path}")
        return {"action": "reused", "sha256": expected_sha256, "size_bytes": path.stat().st_size}
    if max_bytes <= 0:
        raise AcquisitionError("Download must have a positive size bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(path.parent).free < storage_required(max_bytes, 0, reserve_bytes):
        raise AcquisitionError("Insufficient host free space including safety reserve")
    opener = opener or requests.get
    response = None
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.part")
    try:
        current = url
        for _ in range(6):
            _url_allowed(current, allowed_hosts)
            response = opener(
                current,
                stream=True,
                timeout=(20, 120),
                allow_redirects=False,
                headers={
                    "User-Agent": "AI-Term-Paper-V3 academic dataset acquisition",
                    "Accept-Encoding": "identity",
                },
            )
            if response.status_code not in (301, 302, 303, 307, 308):
                break
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise AcquisitionError("Redirect lacks Location")
            current = urljoin(current, location)
        else:
            raise AcquisitionError("Too many redirects")
        if response.status_code != 200:
            raise AcquisitionError(f"Source returned HTTP {response.status_code}")
        length = response.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            raise AcquisitionError("Source exceeds configured byte budget")
        sha256, md5, count = hashlib.sha256(), hashlib.md5(), 0
        with temporary.open("xb") as handle:
            for chunk in response.iter_content(1024**2):
                if not chunk:
                    continue
                count += len(chunk)
                if count > max_bytes or shutil.disk_usage(path.parent).free < reserve_bytes + len(chunk):
                    raise AcquisitionError("Stream exceeded byte/storage budget")
                handle.write(chunk)
                sha256.update(chunk)
                md5.update(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        if count == 0 or (length and count != int(length)):
            raise AcquisitionError("Empty or truncated response")
        if expected_sha256 and sha256.hexdigest() != expected_sha256:
            raise AcquisitionError("Downloaded SHA-256 mismatch")
        if expected_md5 and md5.hexdigest() != expected_md5:
            raise AcquisitionError("Official MD5 mismatch")
        # Hard-link installation is atomic AND no-clobber, unlike os.replace.
        os.link(temporary, path)
        return {
            "action": "downloaded",
            "sha256": sha256.hexdigest(),
            "md5": md5.hexdigest(),
            "size_bytes": count,
            "url": url,
            "final_url": current,
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }
    finally:
        if response is not None:
            response.close()
        temporary.unlink(missing_ok=True)


def _hash_stream(handle, expected_size):
    digest, count = hashlib.sha256(), 0
    for chunk in iter(lambda: handle.read(1024**2), b""):
        count += len(chunk)
        if count > expected_size:
            raise AcquisitionError("Archive member exceeds declared size")
        digest.update(chunk)
    if count != expected_size:
        raise AcquisitionError("Truncated archive member")
    return digest.hexdigest()


def archive_members(path, *, max_expanded_bytes, max_members=100000):
    """Hash every regular member without extraction; reject links and unsafe paths."""
    seen, total, count = set(), 0, 0

    def check(name, size):
        nonlocal total, count
        normalized = safe_member_name(name)
        key = normalized.casefold()
        total += size
        count += 1
        if key in seen or count > max_members or total > max_expanded_bytes or size < 0:
            raise AcquisitionError("Duplicate archive path or member/expanded-size budget exceeded")
        seen.add(key)
        return normalized

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                name = check(info.filename, info.file_size)
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or info.flag_bits & 1:
                    raise AcquisitionError("Links/special/encrypted ZIP members are not accepted")
                if info.is_dir():
                    continue
                with archive.open(info) as handle:
                    digest = _hash_stream(handle, info.file_size)
                yield {"name": name, "size_bytes": info.file_size, "sha256": digest}
    else:
        with tarfile.open(path, "r:*") as archive:
            for info in archive:
                name = check(info.name, info.size)
                if info.isdir():
                    continue
                if not info.isfile():
                    raise AcquisitionError("Only regular files/directories accepted in TAR")
                with archive.extractfile(info) as handle:
                    digest = _hash_stream(handle, info.size)
                yield {"name": name, "size_bytes": info.size, "sha256": digest}


def download_ranged_file(
    url,
    path,
    *,
    total_bytes,
    allowed_hosts,
    expected_md5,
    expected_sha256=None,
    block_bytes=4 * 1024**2,
    reserve_bytes=RESERVE_BYTES,
    opener=None,
):
    """Bounded four-connection Range transport for slow official large-file servers.

    Ranges are written into ONE private temporary file. Every response must be 206
    with the exact requested Content-Range; final published MD5 is mandatory.
    """
    from concurrent.futures import ThreadPoolExecutor

    _url_allowed(url, allowed_hosts)
    path = Path(path)
    if path.exists() or path.is_symlink():
        return download_file(
            url,
            path,
            max_bytes=total_bytes,
            allowed_hosts=allowed_hosts,
            expected_sha256=expected_sha256,
            opener=opener,
            reserve_bytes=reserve_bytes,
        )
    if total_bytes <= 0 or block_bytes <= 0 or not expected_md5:
        raise AcquisitionError("Range transport needs positive bounds and official MD5")
    path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(path.parent).free < storage_required(total_bytes, 0, reserve_bytes):
        raise AcquisitionError("Insufficient storage for range download")
    opener = opener or requests.get
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.part")

    def block(start):
        end = min(start + block_bytes, total_bytes) - 1
        with opener(
            url,
            stream=True,
            timeout=(20, 60),
            allow_redirects=False,
            headers={
                "Range": f"bytes={start}-{end}",
                "Accept-Encoding": "identity",
                "User-Agent": "AI-Term-Paper-V3 academic range download",
            },
        ) as response:
            if (
                response.status_code != 206
                or response.headers.get("Content-Range") != f"bytes {start}-{end}/{total_bytes}"
            ):
                raise AcquisitionError("Source did not honor the exact bounded range")
            count = 0
            with temporary.open("r+b") as handle:
                handle.seek(start)
                for chunk in response.iter_content(65536):
                    count += len(chunk)
                    if count > end - start + 1 or shutil.disk_usage(path.parent).free < reserve_bytes + len(
                        chunk
                    ):
                        raise AcquisitionError("Range response exceeds byte/storage bound")
                    handle.write(chunk)
            if count != end - start + 1:
                raise AcquisitionError("Truncated range response")
        return count

    try:
        with temporary.open("xb") as handle:
            handle.truncate(total_bytes)
        with ThreadPoolExecutor(max_workers=4) as pool:
            for _ in pool.map(block, range(0, total_bytes, block_bytes)):
                pass
        digest = file_digest(temporary)
        if file_digest(temporary, "md5") != expected_md5 or (expected_sha256 and digest != expected_sha256):
            raise AcquisitionError("Full-file range checksum mismatch")
        os.link(temporary, path)
        return {
            "action": "downloaded",
            "sha256": digest,
            "md5": expected_md5,
            "size_bytes": total_bytes,
            "url": url,
            "final_url": url,
            "transport": "verified_exact_ranges_4_connections",
        }
    finally:
        temporary.unlink(missing_ok=True)
