import io
import tarfile

import pytest

from scripts.phase35_tdf import deb_members


def archive_with_names(names):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for name in names:
            entry = tarfile.TarInfo(name)
            entry.size = 3
            archive.addfile(entry, io.BytesIO(b"abc"))
    stream.seek(0)
    return tarfile.open(fileobj=stream, mode="r")


def test_selects_regular_debs_without_extracting_other_entries():
    with archive_with_names(["package/README", "package/DEBS/a.deb"]) as archive:
        assert [m.name for m in deb_members(archive)] == ["package/DEBS/a.deb"]


@pytest.mark.parametrize(
    "names", [["../DEBS/a.deb"], ["/DEBS/a.deb"], ["package/README"], ["a/DEBS/a.deb", "b/DEBS/a.deb"]]
)
def test_archive_rejects_escape_empty_and_duplicate_targets(names):
    with archive_with_names(names) as archive, pytest.raises(ValueError):
        deb_members(archive)
