"""Predeclared two-run scope and exclusive writer gate."""

import json

import pytest

from agent02_assignment.phase03 import assert_declaration, phase3_specs, writer_lock
from agent02_assignment.workspace import sha256_file


def test_only_two_phase3_runs_are_selected():
    specs = phase3_specs()
    assert [(row['track'], row['seed']) for row in specs] == [('REF', 42), ('CONTROLLED', 11)]
    assert all(row['phase'] == 3 and row['config_id'] == 'baseline' for row in specs)


def test_exclusive_writer_is_released_even_on_error(tmp_path):
    with pytest.raises(RuntimeError, match='fixture'), writer_lock(tmp_path):
        with pytest.raises(BlockingIOError), writer_lock(tmp_path):
            pytest.fail('second writer entered')
        raise RuntimeError('fixture')
    with writer_lock(tmp_path):
        pass


def test_declaration_gate_detects_modified_source(tmp_path):
    source = tmp_path / 'fixture.py'
    source.write_text('x=1')
    declaration = tmp_path / 'evidence/phase03/declaration.json'
    declaration.parent.mkdir(parents=True)
    declaration.write_text(json.dumps({'files': [{'path': 'fixture.py', 'sha256': sha256_file(source)}]}))
    assert assert_declaration(tmp_path)['files'][0]['path'] == 'fixture.py'
    source.write_text('x=2')
    with pytest.raises(ValueError, match='hash'):
        assert_declaration(tmp_path)
