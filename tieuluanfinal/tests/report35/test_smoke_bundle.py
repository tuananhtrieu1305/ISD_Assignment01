import io
import zipfile
import pytest
from scripts.phase35_smoke_bundle import checked_members


def test_bundle_rejects_traversal_and_unexpected_count():
    for name in ["../outside", "/absolute", "C:\\outside"]:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as z:
            z.writestr(name, b"x")
        stream.seek(0)
        with zipfile.ZipFile(stream) as z, pytest.raises(ValueError):
            checked_members(z, 1, 1)


def test_bundle_requires_size_and_duplicate_safe():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("apps/api/x.py", b"123")
    stream.seek(0)
    with zipfile.ZipFile(stream) as z:
        assert len(checked_members(z, 1, 3)) == 1
        with pytest.raises(ValueError):
            checked_members(z, 2, 3)


def test_frozen_package_payload_count_excludes_self_manifest():
    import json
    from scripts.phase35_runtime import ROOT

    metadata = json.loads((ROOT / "artifacts/manifests/phase32/package_v2.json").read_text())
    with zipfile.ZipFile(ROOT / metadata["archive"]["path"]) as z:
        self_bytes = len(z.read("bundle_manifest.json"))
        assert (
            len(checked_members(z, metadata["file_count"] + 1, metadata["expanded_bytes"] + self_bytes))
            == 809
        )
