"""Baseline parity, persistent recovery and reuse contracts before implementation."""

import json
from dataclasses import replace

import numpy as np
import pytest

from agent02_assignment.code.baseline_runs import execute_run, summarize, verify_run
from agent02_assignment.code.controlled import LearningConfig, MarketConfig
from agent02_assignment.code.reference_adapter import load_reference
from agent02_assignment.code.reference_training import ReferenceSession
from agent02_assignment.code.training import digest


@pytest.mark.parametrize('seed,episodes', [(42, 17), (11, 9), (55, 3)])
def test_instrumented_reference_is_exactly_faithful_to_original(seed, episodes):
    teacher = load_reference()
    expected, rows = teacher.train_rl_against_rule(teacher.Config(episodes=episodes), seed)
    actual = ReferenceSession(MarketConfig(), LearningConfig(episodes=episodes), seed)
    actual.run_chunk(episodes, trace_limit=20)
    np.testing.assert_array_equal(actual.agent.q, expected.q)
    assert [{key: row[key] for key in rows[0]} for row in actual.rows] == rows
    assert actual.agent.rng.bit_generator.state == expected.rng.bit_generator.state
    assert actual.visits.sum() == episodes * 20


def test_reference_split_resume_and_logging_leave_rng_unchanged():
    learning = LearningConfig(episodes=9)
    whole = ReferenceSession(MarketConfig(), learning, 42)
    whole.run_chunk(9, trace_limit=20)
    split = ReferenceSession(MarketConfig(), learning, 42)
    split.run_chunk(4, trace_limit=20)
    saved = json.loads(json.dumps(split.checkpoint()))
    restored = ReferenceSession.from_checkpoint(saved)
    restored.run_chunk(5, trace_limit=20)
    assert digest(restored.checkpoint()) == digest(whole.checkpoint())
    no_log = ReferenceSession(MarketConfig(), learning, 42)
    no_log.run_chunk(9)
    np.testing.assert_array_equal(no_log.agent.q, whole.agent.q)


def test_reference_budget_hash_and_guard_are_enforced():
    run = ReferenceSession(MarketConfig(), LearningConfig(episodes=2), 42)
    with pytest.raises(ValueError):
        run.run_chunk(3)
    with pytest.raises(RuntimeError):
        run.run_chunk(1, guard=lambda: (_ for _ in ()).throw(RuntimeError('reserve')))
    assert run.completed == 0
    saved = run.checkpoint()
    saved['seed'] = 43
    with pytest.raises(ValueError):
        ReferenceSession.from_checkpoint(saved)


@pytest.mark.parametrize('track', ['REF', 'CONTROLLED'])
def test_run_writes_auditable_outputs_and_reuses_done_without_training(tmp_path, track, monkeypatch):
    spec = {'run_id': track.lower() + '/fixture/s0042', 'track': track, 'seed': 42}
    result = execute_run(tmp_path, spec, MarketConfig(), LearningConfig(episodes=3), 'fixture-lock', interval=2)
    assert result['summary']['market_steps'] == 60
    assert result['summary']['episodes'] == 3
    assert sum(result['summary']['rl_action_counts']) == 60
    assert result['summary']['partition'] == 'training'
    assert verify_run(tmp_path, spec['run_id']) == result
    monkeypatch.setattr('agent02_assignment.code.baseline_runs.new_session',
                        lambda *args: pytest.fail('DONE must never train again'))
    assert execute_run(tmp_path, spec, MarketConfig(), LearningConfig(episodes=3), 'fixture-lock') == result
    target = tmp_path / 'artifacts/runs' / spec['run_id'] / 'q_table.json'
    target.write_text('[]')
    with pytest.raises(ValueError, match='hash'):
        verify_run(tmp_path, spec['run_id'])


def test_incomplete_claim_requires_explicit_resume_and_keeps_old_claim(tmp_path, monkeypatch):
    import agent02_assignment.code.baseline_runs as runner
    spec = {'run_id': 'controlled/fixture/s0011', 'track': 'CONTROLLED', 'seed': 11}
    learning = LearningConfig(episodes=4)
    original = runner.disk_guard
    calls = []
    def guard(base):
        calls.append(1)
        if len(calls) == 4:
            raise RuntimeError('disk reserve fixture')
        return original(base)
    monkeypatch.setattr(runner, 'disk_guard', guard)
    with pytest.raises(RuntimeError):
        execute_run(tmp_path, spec, MarketConfig(), learning, 'lock', interval=2)
    claim = tmp_path / 'artifacts/runs' / spec['run_id'] / 'claim.json'
    before = claim.read_bytes()
    monkeypatch.setattr(runner, 'disk_guard', original)
    with pytest.raises(FileExistsError):
        execute_run(tmp_path, spec, MarketConfig(), learning, 'lock')
    result = execute_run(tmp_path, spec, MarketConfig(), learning, 'lock', resume=True, interval=2)
    assert result['summary']['episodes'] == 4 and claim.read_bytes() == before
    assert result['resumed'] is True


def test_changed_registration_and_path_escape_are_rejected(tmp_path):
    spec = {'run_id': 'ref/fixture/s0042', 'track': 'REF', 'seed': 42}
    learning = LearningConfig(episodes=1)
    execute_run(tmp_path, spec, MarketConfig(), learning, 'lock')
    with pytest.raises(ValueError):
        execute_run(tmp_path, spec, MarketConfig(), replace(learning, alpha=.5), 'lock')
    with pytest.raises(ValueError):
        execute_run(tmp_path, {**spec, 'run_id': '../../../escape'}, MarketConfig(), learning, 'lock')


def test_summary_uses_all_steps_not_average_of_different_units():
    rows = [{'episode': 1, 'rl_episode_reward': 40., 'rule_episode_reward': 20.,
             'rl_mean_reward_per_step': 2., 'rule_mean_reward_per_step': 1.,
             'epsilon': .2, 'action_counts': [[15, 5], [18, 2]]}]
    result = summarize(rows, 20)
    assert result['rl_total_reward'] == 40 and result['rl_mean_reward_per_step'] == 2
    assert result['rule_total_reward'] == 20 and result['rule_action_counts'] == [18, 2]
