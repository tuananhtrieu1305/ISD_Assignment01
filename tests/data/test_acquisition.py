"""Synthetic transport/archive fixtures only; no network access in unit tests."""

import hashlib
import io
import tarfile
import zipfile

import pytest

from src.common.acquisition import (
    AcquisitionError,
    _hash_stream,
    archive_members,
    download_file,
    download_ranged_file,
    safe_member_name,
    storage_required,
)


@pytest.mark.parametrize(
    "name", ["../escape", "/etc/passwd", "C:/escape", "a/../../escape", "a\\evil", "a/../bad"]
)
def test_archive_paths_cannot_escape(name):
    with pytest.raises(AcquisitionError):
        safe_member_name(name)


def test_normal_member_name_is_accepted():
    assert safe_member_name("folder/file.csv") == "folder/file.csv"


def test_storage_budget_includes_reserved_space():
    assert storage_required(100, 200, reserve_bytes=300) == 600
    with pytest.raises(ValueError):
        storage_required(-1, 0)


def test_zip_members_measured_without_extracting(tmp_path):
    path = tmp_path / "sample.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("table.csv", "x,y\n1,2\n")
    rows = list(archive_members(path, max_expanded_bytes=100))
    assert rows[0]["sha256"] == hashlib.sha256(b"x,y\n1,2\n").hexdigest()
    assert not (tmp_path / "table.csv").exists()


def test_zip_traversal_is_rejected(tmp_path):
    path = tmp_path / "sample.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../evil", "bad")
    with pytest.raises(AcquisitionError):
        list(archive_members(path, max_expanded_bytes=100))


def test_archive_expansion_budget_is_enforced(tmp_path):
    path = tmp_path / "sample.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("huge.txt", "A" * 1000)
    with pytest.raises(AcquisitionError):
        list(archive_members(path, max_expanded_bytes=100))


def test_tar_link_is_rejected(tmp_path):
    path = tmp_path / "sample.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("bad_link")
        member.type = tarfile.SYMTYPE
        member.linkname = "/etc/passwd"
        archive.addfile(member)
    with pytest.raises(AcquisitionError):
        list(archive_members(path, max_expanded_bytes=100))


def test_existing_good_hash_skips_network(tmp_path):
    path = tmp_path / "data.csv"
    path.write_bytes(b"already here")
    result = download_file(
        "https://example.org/data.csv",
        path,
        expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        max_bytes=100,
        allowed_hosts={"example.org"},
        opener=lambda *_args, **_kwargs: pytest.fail("Network must not be called"),
    )
    assert result["action"] == "reused"


def test_existing_bad_hash_is_never_overwritten(tmp_path):
    path = tmp_path / "data.csv"
    path.write_bytes(b"user bytes")
    with pytest.raises(AcquisitionError):
        download_file(
            "https://example.org/data.csv",
            path,
            expected_sha256="a" * 64,
            max_bytes=100,
            allowed_hosts={"example.org"},
        )
    assert path.read_bytes() == b"user bytes"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org/file",
        "file:///etc/passwd",
        "https://evil.example/file",
        "https://user:password@example.org/file",
    ],
)
def test_unapproved_urls_are_rejected(tmp_path, url):
    with pytest.raises(AcquisitionError):
        download_file(url, tmp_path / "file", max_bytes=100, allowed_hosts={"example.org"})


class FakeResponse:
    def __init__(self, body=b"abc", status=200, headers=None):
        self.body, self.status_code, self.headers = body, status, headers or {}
        self.closed = False

    def iter_content(self, _chunk_size):
        yield b""
        yield self.body

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def fetch(tmp_path, response, **kwargs):
    return download_file(
        "https://example.org/data",
        tmp_path / "data",
        max_bytes=100,
        allowed_hosts={"example.org"},
        opener=lambda *a, **k: response,
        reserve_bytes=0,
        **kwargs,
    )


def test_stream_download_and_official_md5(tmp_path):
    response = FakeResponse(headers={"Content-Length": "3", "ETag": "v1"})
    result = fetch(tmp_path, response, expected_md5=hashlib.md5(b"abc").hexdigest())
    assert (tmp_path / "data").read_bytes() == b"abc"
    assert result["sha256"] == hashlib.sha256(b"abc").hexdigest()
    assert result["etag"] == "v1" and response.closed
    assert not list(tmp_path.glob("*.part"))


@pytest.mark.parametrize(
    "body,status,headers,extra",
    [
        (b"abc", 404, {}, {}),
        (b"abc", 200, {"Content-Length": "200"}, {}),
        (b"a" * 101, 200, {}, {}),
        (b"abc", 200, {"Content-Length": "5"}, {}),
        (b"", 200, {}, {}),
        (b"abc", 200, {}, {"expected_sha256": "0" * 64}),
        (b"abc", 200, {}, {"expected_md5": "0" * 32}),
        (b"", 302, {"Location": "https://evil.example/file"}, {}),
        (b"", 302, {}, {}),
        (b"", 302, {"Location": "/loop"}, {}),
    ],
)
def test_failed_download_never_installs_or_leaves_partial(tmp_path, body, status, headers, extra):
    with pytest.raises(AcquisitionError):
        fetch(tmp_path, FakeResponse(body, status, headers), **extra)
    assert not list(tmp_path.iterdir())


def test_safe_relative_redirect(tmp_path):
    responses = iter([FakeResponse(status=302, headers={"Location": "/v2"}), FakeResponse()])
    result = download_file(
        "https://example.org/v1",
        tmp_path / "data",
        max_bytes=100,
        allowed_hosts={"example.org"},
        opener=lambda *a, **k: next(responses),
        reserve_bytes=0,
    )
    assert result["final_url"] == "https://example.org/v2"


def test_storage_shortage_rejects_before_network(tmp_path, monkeypatch):
    from collections import namedtuple

    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr("src.common.acquisition.shutil.disk_usage", lambda _: usage(1, 1, 0))
    with pytest.raises(AcquisitionError):
        fetch(tmp_path, FakeResponse())


def test_tar_regular_member(tmp_path):
    path = tmp_path / "regular.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        archive.addfile(tarfile.TarInfo("directory/"))
        info = tarfile.TarInfo("regular.txt")
        info.size = 3
        archive.addfile(info, io.BytesIO(b"abc"))
    rows = list(archive_members(path, max_expanded_bytes=10))
    assert rows[-1]["sha256"] == hashlib.sha256(b"abc").hexdigest()


def test_zip_case_collision_and_member_count(tmp_path):
    path = tmp_path / "collision.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("a.csv", "x")
        archive.writestr("A.csv", "x")
    for limit in (1, 10):
        with pytest.raises(AcquisitionError):
            list(archive_members(path, max_expanded_bytes=10, max_members=limit))


@pytest.mark.parametrize("content,expected_size", [(b"xx", 1), (b"x", 2)])
def test_member_size_mismatch_rejected(content, expected_size):
    with pytest.raises(AcquisitionError):
        _hash_stream(io.BytesIO(content), expected_size)


def test_exact_range_download_reassembles_and_checks_hash(tmp_path):
    payload = b"123456789"

    def opener(_url, **kwargs):
        start, end = map(int, kwargs["headers"]["Range"].split("=")[1].split("-"))
        return FakeResponse(payload[start : end + 1], 206, {"Content-Range": f"bytes {start}-{end}/9"})

    result = download_ranged_file(
        "https://example.org/data",
        tmp_path / "data",
        total_bytes=9,
        block_bytes=4,
        allowed_hosts={"example.org"},
        expected_md5=hashlib.md5(payload).hexdigest(),
        reserve_bytes=0,
        opener=opener,
    )
    assert result["sha256"] == hashlib.sha256(payload).hexdigest()
    assert (tmp_path / "data").read_bytes() == payload


@pytest.mark.parametrize(
    "body,headers,md5",
    [
        (b"abc", {}, "0" * 32),
        (b"abc", {"Content-Range": "bytes 0-2/3"}, "0" * 32),
        (b"ab", {"Content-Range": "bytes 0-2/3"}, "0" * 32),
        (b"abcd", {"Content-Range": "bytes 0-2/3"}, "0" * 32),
    ],
)
def test_bad_range_transport_never_installs(tmp_path, body, headers, md5):
    with pytest.raises(AcquisitionError):
        download_ranged_file(
            "https://example.org/data",
            tmp_path / "data",
            total_bytes=3,
            allowed_hosts={"example.org"},
            expected_md5=md5,
            reserve_bytes=0,
            opener=lambda *a, **k: FakeResponse(body, 206, headers),
        )
    assert not list(tmp_path.iterdir())
