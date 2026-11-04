"""Frozen-policy and claim-once contracts, using fixture seeds and tiny budgets."""

import copy

import numpy as np
import pytest

from agent02_assignment.code.controlled import LearningConfig, MarketConfig, QAgent
from agent02_assignment.code.evaluation.final_v1 import evaluate_tapes, native_reference, policy_hash
from agent02_assignment.code.evaluation.journal_v1 import ConsumedClaimError, claim_evaluate, job_key
from agent02_assignment.code.reference_adapter import load_reference
from agent02_assignment.code.training import TrainSession


def test_q_and_training_rng_are_unchanged_and_exploration_is_disabled(monkeypatch):
    run = TrainSession(MarketConfig(), LearningConfig(episodes=2), 11)
    run.run_chunk(2)
    before = copy.deepcopy(run.checkpoint())
    original = QAgent.act
    calls = []
    def checked(agent, state, epsilon, *, explore=True):
        assert epsilon == 0 and explore is False and agent.q.flags.writeable is False
        calls.append(1)
        return original(agent, state, epsilon, explore=explore)
    monkeypatch.setattr(QAgent, 'act', checked)
    monkeypatch.setattr(QAgent, 'learn', lambda *a, **k: pytest.fail('evaluation must not learn'))
    result = evaluate_tapes(run.agent.q, MarketConfig(), episodes=3, scenario_seed=910011, role=0)
    assert result['q_hash_before'] == result['q_hash_after']
    assert before == run.checkpoint() and len(calls) == 60


def test_same_policy_and_role_use_identical_tapes_and_rows():
    q = np.zeros((2, 2, 2))
    first = evaluate_tapes(q, MarketConfig(), episodes=3, scenario_seed=910022, role=1)
    assert first == evaluate_tapes(q, MarketConfig(), episodes=3, scenario_seed=910022, role=1)
    assert sum(sum(row['learner_action_counts']) for row in first['rows']) == 60
    assert sum(first['state_visits']) == 60


def test_role_swap_symmetric_controls_cancel_within_match_sales_noise():
    left = evaluate_tapes(None, MarketConfig(), episodes=4, scenario_seed=910033, role=0, kind='rule')
    right = evaluate_tapes(None, MarketConfig(), episodes=4, scenario_seed=910033, role=1, kind='no_discount')
    assert left['total_reward'] == right['opponent_total_reward']
    assert right['total_reward'] == left['opponent_total_reward']
    assert left['learner_action_counts'] == right['learner_action_counts'] == [80, 0]


@pytest.mark.parametrize('kwargs', [{'episodes': 0}, {'episodes': 501}, {'role': 2}, {'kind': 'unknown'}])
def test_invalid_evaluation_scope_is_rejected(kwargs):
    args = {'episodes': 2, 'scenario_seed': 910011, 'role': 0, **kwargs}
    with pytest.raises(ValueError):
        evaluate_tapes(np.zeros((2, 2, 2)), MarketConfig(), **args)


def test_native_wrapper_preserves_original_evaluate_pair_and_rng_input():
    teacher = load_reference()
    agent = teacher.QLearningAgent(seed=123)
    agent.q[:] = 0  # Force genuine ties so the native policy RNG is exercised.
    rng = copy.deepcopy(agent.rng.bit_generator.state)
    expected, rows = teacher.evaluate_pair(teacher.Config(), agent, episodes=3, seed=910042)
    guards = []
    actual = native_reference(agent.q, rng, episodes=3, scenario_seed=910042, guard=lambda: guards.append(1))
    assert [row['learner_reward'] for row in actual['rows']] == [row['rl_reward'] for row in rows]
    assert actual['total_reward'] == expected[0]['total_reward']
    assert actual['learner_action_counts'] == [expected[0]['no_discount_actions'], expected[0]['discount_actions']]
    assert rng != agent.rng.bit_generator.state
    assert actual['policy_rng_before'] == rng and actual['q_hash_before'] == actual['q_hash_after']
    assert len(guards) == 3


def fixture_job():
    return {'study_id': 'fixture_only', 'policy_sha256': policy_hash(None, 'rule'),
            'scenario_sha256': 'fixture-scenario', 'role': 0, 'job_id': 'fixture-rule'}


def test_claim_key_includes_policy_scenario_and_role_not_display_alias():
    job = fixture_job()
    assert job_key(job) == job_key({**job, 'job_id': 'another-display-alias'})
    assert job_key(job) != job_key({**job, 'role': 1})
    assert job_key(job) != job_key({**job, 'scenario_sha256': 'changed'})


def test_completed_claim_reuses_saved_output_without_callback(tmp_path):
    calls = []
    def callback():
        calls.append(1)
        return {'fixture': True, 'rows': [{'episode': 1, 'reward': 2.}]}
    result = claim_evaluate(tmp_path, fixture_job(), 'fixture-proof', callback)
    repeated = claim_evaluate(tmp_path, fixture_job(), 'fixture-proof', lambda: pytest.fail('must reuse'))
    assert result == repeated and len(calls) == 1
    with pytest.raises(ValueError):
        claim_evaluate(tmp_path, fixture_job(), 'changed-proof', lambda: pytest.fail('must refuse'))


def test_failed_consumed_claim_is_never_silently_replayed(tmp_path):
    calls = []
    def failing():
        calls.append(1)
        raise RuntimeError('fixture failure after claim')
    with pytest.raises(RuntimeError):
        claim_evaluate(tmp_path, fixture_job(), 'fixture-proof', failing)
    with pytest.raises(ConsumedClaimError):
        claim_evaluate(tmp_path, fixture_job(), 'fixture-proof', failing)
    assert len(calls) == 1


def test_episode_guard_and_saved_output_integrity(tmp_path):
    guards = []
    result = evaluate_tapes(None, MarketConfig(), episodes=2, scenario_seed=910044, role=0,
                            kind='no_discount', guard=lambda: guards.append(1))
    assert len(guards) == 2
    saved = claim_evaluate(tmp_path, fixture_job(), 'fixture-proof', lambda: result)
    result_path = next(item['path'] for item in saved['files'] if item['path'].endswith('result.json'))
    (tmp_path/result_path).write_text('{}')
    with pytest.raises(ValueError, match='hash'):
        claim_evaluate(tmp_path, fixture_job(), 'fixture-proof', lambda: pytest.fail('must not forward'))
