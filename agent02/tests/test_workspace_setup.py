"""Workspace safeguards first; no scientific training or reference import here."""

import hashlib
import json

import pytest

from agent02_assignment import workspace


def checksum(value):
    return hashlib.sha256(value).hexdigest()


def test_relative_target_stays_inside_workspace(tmp_path):
    assert workspace.inside(tmp_path, 'sources/a.txt') == tmp_path / 'sources/a.txt'


@pytest.mark.parametrize('relative', ['../outside', '/tmp/outside', 'C:\\outside', '..\\outside', ''])
def test_invalid_target_is_rejected(tmp_path, relative):
    with pytest.raises(ValueError):
        workspace.inside(tmp_path, relative)


def test_symlink_escape_is_rejected(tmp_path):
    base = tmp_path / 'base'
    base.mkdir()
    (base / 'escape').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        workspace.inside(base, 'escape/outside')


def test_source_copy_is_byte_identical_and_idempotent(tmp_path):
    source = tmp_path / 'teacher.tex'
    content = b'print("not executed")\r\n'
    source.write_bytes(content)
    base = tmp_path / 'workspace'
    first = workspace.copy_verified(source, base, 'sources/provided/teacher.tex', checksum(content))
    second = workspace.copy_verified(source, base, 'sources/provided/teacher.tex', checksum(content))
    assert first['operation'] == 'copied'
    assert second['operation'] == 'reused'
    assert (base / first['path']).read_bytes() == source.read_bytes() == content


def test_bad_source_hash_creates_no_target(tmp_path):
    source = tmp_path / 'teacher.tex'
    source.write_bytes(b'wrong')
    base = tmp_path / 'workspace'
    with pytest.raises(ValueError, match='Source hash'):
        workspace.copy_verified(source, base, 'a.py', checksum(b'expected'))
    assert not base.exists()


def test_existing_different_target_is_never_overwritten(tmp_path):
    source = tmp_path / 'teacher.tex'
    source.write_bytes(b'correct')
    base = tmp_path / 'workspace'
    base.mkdir()
    destination = base / 'a.py'
    destination.write_bytes(b'user changes')
    with pytest.raises(FileExistsError):
        workspace.copy_verified(source, base, 'a.py', checksum(b'correct'))
    assert destination.read_bytes() == b'user changes'


def test_missing_source_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        workspace.copy_verified(tmp_path / 'missing', tmp_path / 'base', 'a.py', '0' * 64)


def test_inspection_compiles_but_never_executes(tmp_path):
    marker = tmp_path / 'should_not_exist'
    source = tmp_path / 'teacher.py'
    source.write_text(f'raise RuntimeError("must not run")\nopen({str(marker)!r}, "w")\n'
                      'class Config:\n    episodes: int = 5000\n'
                      'def main():\n    pass\n', encoding='utf-8')
    receipt = workspace.inspect_python(source)
    assert receipt['syntax_valid'] and receipt['execution_performed'] is False
    assert receipt['classes'] == ['Config']
    assert receipt['functions'] == ['main']
    assert receipt['config_defaults']['episodes'] == 5000
    assert not marker.exists()


def test_invalid_python_fails_inspection(tmp_path):
    source = tmp_path / 'teacher.py'
    source.write_text('def invalid(:\n', encoding='utf-8')
    with pytest.raises(SyntaxError):
        workspace.inspect_python(source)


def test_no_config_class_is_not_fabricated(tmp_path):
    source = tmp_path / 'teacher.py'
    source.write_text('x = 1\n', encoding='utf-8')
    assert workspace.inspect_python(source)['config_defaults'] == {}


def test_prepare_sources_validates_manifest_size(tmp_path):
    source_root = tmp_path / 'teacher'
    source_root.mkdir()
    (source_root / 'teacher.tex').write_bytes(b'x=1\n')
    manifest = [{'name': 'teacher.tex', 'sha256': checksum(b'x=1\n'), 'bytes': 99}]
    with pytest.raises(ValueError, match='size'):
        workspace.prepare_sources(source_root, tmp_path / 'workspace', manifest)


def test_empty_or_unsafe_manifest_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        workspace.prepare_sources(tmp_path, tmp_path / 'workspace', [])
    with pytest.raises(ValueError):
        workspace.prepare_sources(tmp_path, tmp_path / 'workspace',
                                  [{'name': '../bad', 'bytes': 1, 'sha256': '0' * 64}])


def test_prepare_sources_creates_reference_without_importing(tmp_path):
    source_root = tmp_path / 'teacher'
    source_root.mkdir()
    text = b'raise RuntimeError("must not run")\r\n'
    (source_root / 'agent02_code.tex').write_bytes(text)
    manifest = [{'name': 'agent02_code.tex', 'bytes': len(text), 'sha256': checksum(text)}]
    base = tmp_path / 'workspace'
    receipt = workspace.prepare_sources(source_root, base, manifest)
    assert receipt['reference']['sha256'] == checksum(text)
    assert (base / 'code/agent02_experiment.py').read_bytes() == text


def test_prepare_sources_rejects_hash_mismatch_before_copying(tmp_path):
    source_root = tmp_path / 'teacher'
    source_root.mkdir()
    (source_root / 'teacher.tex').write_bytes(b'x=1\n')
    with pytest.raises(ValueError, match='Source hash'):
        workspace.prepare_sources(source_root, tmp_path / 'workspace',
                                  [{'name': 'teacher.tex', 'bytes': 4, 'sha256': '0' * 64}])
    assert not (tmp_path / 'workspace').exists()


def test_runtime_mismatch_is_not_silently_accepted():
    expected = {'python': '3.11.17', 'packages': {'numpy': '2.4.6'}}
    actual = {'python': '3.11.17', 'packages': {'numpy': '0.0'}}
    with pytest.raises(ValueError, match='numpy'):
        workspace.validate_runtime(actual, expected)


def test_matching_runtime_passes():
    expected = {'python': '3.11.17', 'packages': {'numpy': '2.4.6'}}
    assert workspace.validate_runtime(expected, expected) is None


def test_python_mismatch_is_rejected():
    with pytest.raises(ValueError, match='Python'):
        workspace.validate_runtime({'python': '3.12', 'packages': {}}, {'python': '3.11.17'})


def test_generated_json_is_not_overwritten_with_different_contents(tmp_path):
    workspace.write_receipt(tmp_path, 'evidence/a.json', {'a': 1})
    workspace.write_receipt(tmp_path, 'evidence/a.json', {'a': 1})
    with pytest.raises(FileExistsError):
        workspace.write_receipt(tmp_path, 'evidence/a.json', {'a': 2})
    assert json.loads((tmp_path / 'evidence/a.json').read_text()) == {'a': 1}
