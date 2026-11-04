"""Runtime safety contracts; no DOCX authoring or model execution."""

import hashlib
from pathlib import Path

import pytest

from scripts.phase35_runtime import (
    checked_relative,
    digest,
    parse_apt_uris,
    relocate_configuration,
    select_metadata,
    write_once_json,
)


def test_uri_records_are_https_and_budgeted():
    result = parse_apt_uris(
        "Reading package lists...\n"
        "'http://archive.ubuntu.com/ubuntu/pool/a/a_1_amd64.deb' a_1_amd64.deb 12 MD5Sum:abc\n"
    )
    assert result == [
        {
            "url": "https://archive.ubuntu.com/ubuntu/pool/a/a_1_amd64.deb",
            "filename": "a_1_amd64.deb",
            "bytes": 12,
        }
    ]


@pytest.mark.parametrize(
    "line",
    [
        "'https://evil.invalid/a.deb' a.deb 12 abc",
        "'file:///etc/passwd' a.deb 12 abc",
        "'https://archive.ubuntu.com/a.deb' ../a.deb 12 abc",
        "'https://archive.ubuntu.com/a.deb' a.deb 0 abc",
    ],
)
def test_uri_rejects_unapproved_source_or_unsafe_target(line):
    with pytest.raises(ValueError):
        parse_apt_uris(line)


def test_uri_requires_unique_nonempty_records():
    with pytest.raises(ValueError):
        parse_apt_uris("No downloads")
    line = "'https://archive.ubuntu.com/a.deb' a.deb 12 abc\n"
    with pytest.raises(ValueError):
        parse_apt_uris(line + line)


def test_metadata_requires_exact_filename_size_and_sha():
    row = {"filename": "a.deb", "bytes": 12}
    sha = "a" * 64
    metadata = f"Package: a\nVersion: 1\nFilename: pool/a.deb\nSize: 12\nSHA256: {sha}\n"
    assert select_metadata(row, metadata) == {"package": "a", "version": "1", "sha256": sha}
    assert select_metadata(row, metadata + "\n" + metadata) == select_metadata(row, metadata)
    for broken in [metadata.replace("12", "13"), metadata.replace(sha, "invalid"), ""]:
        with pytest.raises(ValueError):
            select_metadata(row, broken)


def test_metadata_url_encoding_and_conflicting_repository_entries():
    row = {
        "filename": "a_1%3a2_amd64.deb",
        "bytes": 12,
        "url": "https://archive.ubuntu.com/a_2%2bb_amd64.deb",
    }
    metadata = (
        "Package: a\nVersion: 1:2\nFilename: pool/a_2+b_amd64.deb\nSize: 12\nSHA256: " + "a" * 64 + "\n"
    )
    assert select_metadata(row, metadata)["version"] == "1:2"
    with pytest.raises(ValueError):
        select_metadata(row, metadata + "\n" + metadata.replace("a" * 64, "b" * 64))


def test_relative_path_rejects_escape_and_symlink(tmp_path):
    assert checked_relative(tmp_path, "a/b") == tmp_path / "a/b"
    for name in ["../outside", str(tmp_path.parent / "absolute")]:
        with pytest.raises(ValueError):
            checked_relative(tmp_path, name)
    (tmp_path / "link").symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(ValueError):
        checked_relative(tmp_path, "link/something")


def test_write_once_is_idempotent_but_never_overwrites(tmp_path):
    path = tmp_path / "record.json"
    write_once_json(path, {"a": 1})
    before = path.read_bytes()
    write_once_json(path, {"a": 1})
    assert path.read_bytes() == before
    with pytest.raises(FileExistsError):
        write_once_json(path, {"a": 2})
    assert path.read_bytes() == before


def test_stream_hash(tmp_path):
    path = Path(tmp_path) / "content"
    path.write_bytes(b"abc")
    assert digest(path) == hashlib.sha256(b"abc").hexdigest()


def test_relocates_only_libreoffice_specific_absolute_roots():
    text = "BRAND_BASE_DIR=file:///usr/lib/libreoffice\nx=file:///etc/libreoffice/registry\ny=/var/lib/libreoffice/cache\nz=/usr/lib/other\n"
    actual = relocate_configuration(text, Path("/private/sysroot"))
    assert "file:///private/sysroot/usr/lib/libreoffice" in actual
    assert "file:///private/sysroot/etc/libreoffice/registry" in actual
    assert "/private/sysroot/var/lib/libreoffice/cache" in actual
    assert "z=/usr/lib/other" in actual
    assert relocate_configuration(actual, Path("/private/sysroot")) == actual
