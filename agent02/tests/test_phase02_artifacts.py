"""Smoke persistence and single-claim safety, using tiny isolated fixtures only."""

import json

import pytest

from agent02_assignment.phase02 import disk_guard, execute_smoke, main, save_json, verify_smoke
from agent02_assignment.protocol import build_protocol


def tiny_protocol():
    protocol = build_protocol()
    protocol['smoke']['episodes_per_track'] = 2
    protocol['smoke']['development_episodes_per_role'] = 1
    return protocol


def test_artifact_path_and_no_overwrite_guards(tmp_path):
    save_json(tmp_path, 'outputs/a.json', {'a': 1})
    save_json(tmp_path, 'outputs/a.json', {'a': 1})
    with pytest.raises(FileExistsError):
        save_json(tmp_path, 'outputs/a.json', {'a': 2})
    with pytest.raises(ValueError):
        save_json(tmp_path, '../escape.json', {})
    save_json(tmp_path, 'outputs/tuple.json', {'kernel': ((.5, .5), (.5, .5))})
    save_json(tmp_path, 'outputs/tuple.json', {'kernel': [[.5, .5], [.5, .5]]})


def test_disk_guard_enforces_reserve_without_deleting(tmp_path, monkeypatch):
    monkeypatch.setattr('agent02_assignment.phase02.shutil.disk_usage', lambda _: (100, 99, 1))
    with pytest.raises(RuntimeError, match='reserve'):
        disk_guard(tmp_path)
    assert not list(tmp_path.iterdir())


def test_smoke_saved_outputs_are_reused_and_tampering_is_detected(tmp_path, monkeypatch):
    protocol = tiny_protocol()
    receipt = execute_smoke(tmp_path, protocol)
    assert receipt['training_market_steps'] == 80
    assert receipt['development_market_steps'] == 40
    assert receipt['full_training_started'] is False
    assert receipt['charts_generated'] == 0
    assert receipt['checkpoint_roundtrip_exact'] is True
    assert receipt['source_files'] and receipt['protocol_sha256']
    assert verify_smoke(tmp_path) == receipt
    monkeypatch.setattr('agent02_assignment.phase02.reference_smoke', lambda **_: pytest.fail('must reuse'))
    assert execute_smoke(tmp_path, protocol) == receipt
    target = tmp_path / 'evidence/phase02/smoke/controlled/q_table.json'
    target.write_text('[]')
    with pytest.raises(ValueError, match='hash'):
        verify_smoke(tmp_path)


def test_partial_claim_is_not_replayed(tmp_path):
    save_json(tmp_path, 'evidence/phase02/smoke/claim.json', {'status': 'claimed'})
    with pytest.raises(FileExistsError, match='claim'):
        execute_smoke(tmp_path, tiny_protocol())


def test_changed_protocol_cannot_reuse_completed_smoke(tmp_path):
    protocol = tiny_protocol()
    execute_smoke(tmp_path, protocol)
    protocol['smoke']['controlled_seed'] += 1
    with pytest.raises(ValueError, match='protocol'):
        execute_smoke(tmp_path, protocol)


def test_serialized_checkpoint_contains_rng_not_only_q(tmp_path):
    execute_smoke(tmp_path, tiny_protocol())
    saved = json.loads((tmp_path / 'evidence/phase02/smoke/controlled/checkpoint_e000002.json').read_text())
    assert set(saved['rng']) == {'demand', 'sales', 'agent'}
    assert len(saved['rng']['sales']) == 2
    assert saved['completed'] == len(saved['rows']) == 2


def test_cli_json_roundtrip_is_canonical_and_full_training_is_not_exposed(tmp_path, monkeypatch, capsys):
    import agent02_assignment.phase02 as runner

    protocol = build_protocol()
    monkeypatch.setattr(runner, 'BASE', tmp_path)
    monkeypatch.setattr(runner, 'preflight', lambda: {'status': 'PASS'})
    monkeypatch.setattr(runner, 'build_protocol', lambda: protocol)
    monkeypatch.setattr('sys.argv', ['phase02', 'status'])
    main()
    assert json.loads(capsys.readouterr().out)['full_training_started'] is False
    monkeypatch.setattr('sys.argv', ['phase02', 'write-protocol'])
    main()
    main()
    capsys.readouterr()
    monkeypatch.setattr(runner, 'execute_smoke', lambda base, saved: {'status': 'PASS'})
    monkeypatch.setattr('sys.argv', ['phase02', 'smoke'])
    main()
    assert json.loads(capsys.readouterr().out)['status'] == 'PASS'
    protocol['smoke']['controlled_seed'] += 1
    with pytest.raises(ValueError, match='Protocol differs'):
        main()
    monkeypatch.setattr(runner, 'verify_smoke', lambda base: {'status': 'PASS'})
    monkeypatch.setattr('sys.argv', ['phase02', 'verify-smoke'])
    main()
    capsys.readouterr()
    monkeypatch.setattr('sys.argv', ['phase02', 'train'])
    with pytest.raises(SystemExit):
        main()
