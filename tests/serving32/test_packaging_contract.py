"""Build-time checker and fully local OpenAPI references."""

import json
import types

import pytest

from apps.api.v3 import check_bundle
from apps.api.v3.openapi import specification
from src.common.artifact_core import sha256_file


def test_all_openapi_refs_are_local():
    document = specification()

    def visit(value):
        if isinstance(value, dict):
            if "$ref" in value:
                ref = value["$ref"]
                assert ref.startswith("#/")
                target = document
                for name in ref[2:].split("/"):
                    target = target[name.replace("~1", "/").replace("~0", "~")]
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(document)


def test_package_checker_rejects_tamper(tmp_path, monkeypatch, capsys):
    path = tmp_path / "asset.json"
    path.write_text("{}", encoding="utf-8")
    manifest = {"files": [{"path": "asset.json", "sha256": sha256_file(path), "size_bytes": 2}]}
    (tmp_path / "bundle_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(check_bundle, "ROOT", tmp_path)
    monkeypatch.setattr(
        check_bundle, "Registry", lambda: types.SimpleNamespace(components=lambda: [{"status": "ready"}])
    )
    check_bundle.main()
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        check_bundle.main()
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        check_bundle,
        "Registry",
        lambda: types.SimpleNamespace(components=lambda: [{"status": "unavailable"}]),
    )
    with pytest.raises(ValueError):
        check_bundle.main()
