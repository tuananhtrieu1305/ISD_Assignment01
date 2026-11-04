"""Training, resume and evaluation contracts declared before code exists."""

import copy

import numpy as np
import pytest

from agent02_assignment.code.controlled import LearningConfig, MarketConfig
from agent02_assignment.code.evaluation.frozen import evaluate_dev
from agent02_assignment.code.training import TrainSession


def test_checkpoint_resume_matches_uninterrupted_run_exactly():
    config = LearningConfig(episodes=7)
    whole = TrainSession(MarketConfig(), config, 11)
    whole.run_chunk(7, trace_limit=8)
    first = TrainSession(MarketConfig(), config, 11)
    first.run_chunk(3, trace_limit=8)
    second = TrainSession.from_checkpoint(first.checkpoint())
    second.run_chunk(4, trace_limit=8)
    assert second.checkpoint() == whole.checkpoint()
    assert sum(sum(row['action_counts'][0]) for row in second.rows) == 140
    assert int(second.visits.sum()) == 140


def test_logging_does_not_consume_rng_or_change_q():
    first = TrainSession(MarketConfig(), LearningConfig(episodes=3), 11)
    second = TrainSession(MarketConfig(), LearningConfig(episodes=3), 11)
    first.run_chunk(3, trace_limit=20)
    second.run_chunk(3, trace_limit=0)
    np.testing.assert_array_equal(first.agent.q, second.agent.q)
    assert first.rows == second.rows


def test_disk_guard_stops_at_episode_boundary_with_resumable_state():
    run = TrainSession(MarketConfig(), LearningConfig(episodes=3), 11)
    calls = []
    def guard():
        calls.append(True)
        if len(calls) == 2:
            raise RuntimeError('disk reserve')
    with pytest.raises(RuntimeError, match='disk reserve'):
        run.run_chunk(3, guard=guard)
    assert run.completed == 1
    restored = TrainSession.from_checkpoint(run.checkpoint())
    restored.run_chunk(2)
    assert restored.completed == 3


def test_chunk_budget_and_checkpoint_integrity_are_enforced():
    run = TrainSession(MarketConfig(), LearningConfig(episodes=3), 11)
    with pytest.raises(ValueError):
        run.run_chunk(4)
    bad = run.checkpoint()
    bad['q'][0][0][0] = float('nan')
    with pytest.raises(ValueError):
        TrainSession.from_checkpoint(bad)
    bad = run.checkpoint()
    bad['schema'] = 'wrong'
    with pytest.raises(ValueError):
        TrainSession.from_checkpoint(bad)


def test_dev_evaluation_is_frozen_deterministic_and_role_swapped():
    run = TrainSession(MarketConfig(), LearningConfig(episodes=3), 11)
    run.run_chunk(3)
    before = copy.deepcopy(run.checkpoint())
    result = evaluate_dev(run.agent.q, MarketConfig(), episodes=3, scenario_seed=810001, role=0)
    repeat = evaluate_dev(run.agent.q, MarketConfig(), episodes=3, scenario_seed=810001, role=0)
    reverse = evaluate_dev(run.agent.q, MarketConfig(), episodes=3, scenario_seed=810001, role=1)
    assert run.checkpoint() == before and result == repeat
    assert result['q_hash_before'] == result['q_hash_after']
    assert result['steps'] == reverse['steps'] == 60
    assert sum(result['learner_action_counts']) == 60
    assert result['mean_reward'] == pytest.approx(result['total_reward'] / 60)


def test_phase_two_evaluator_rejects_final_partition_and_excessive_dev_budget():
    q = np.zeros((2, 2, 2))
    with pytest.raises(PermissionError):
        evaluate_dev(q, MarketConfig(), episodes=1, scenario_seed=1, role=0, partition='final')
    for kwargs in ({'episodes': 501, 'role': 0}, {'episodes': 0, 'role': 0}, {'episodes': 1, 'role': 2}):
        with pytest.raises(ValueError):
            evaluate_dev(q, MarketConfig(), scenario_seed=1, **kwargs)
