"""Synthetic fixtures for memory/time Q, exact resume, frozen evaluation and model oracle."""

import copy
import json

import numpy as np
import pytest

from agent02_assignment.code.augmented import (
    AugmentedAgent,
    AugmentedSession,
    alias_witness,
    augmented_hash,
    observe,
    state_index,
)
from agent02_assignment.code.augmented_runs import execute_augmented
from agent02_assignment.code.controlled import LearningConfig, MarketConfig, MarketEnv
from agent02_assignment.code.evaluation.augmented_final import evaluate_augmented
from agent02_assignment.code.evaluation.phase07_journal import claim_once, key_for, read_claim
from agent02_assignment.code.market_oracle import policy_value, solve
from agent02_assignment.code.training import digest


def test_alias_witness_same_old_observation_different_rule_action():
    witness = alias_witness()
    assert witness['old_observation_a'] == witness['old_observation_b'] == [1, 0]
    assert witness['rule_current_actions'] == [0, 1]
    assert witness['expected_reward_keep_price'] == pytest.approx([55., 45.])
    assert witness['new_observation_a'] != witness['new_observation_b']


def test_state_has_320_entries_and_time_decrements():
    agent = AugmentedAgent(LearningConfig(), 971011)
    assert agent.q.shape == (2, 2, 2, 20, 2) and agent.q.size == 320
    env = MarketEnv(MarketConfig(), 971011)
    env.reset()
    assert observe(env, 0)[-1] == 20
    env.step((1, 0))
    assert observe(env, 0)[1:] == (1, 0, 19)
    assert observe(env, 1)[1:] == (0, 1, 19)
    assert state_index((1, 0, 1, 20)) == (1, 0, 1, 19)


@pytest.mark.parametrize('state', [(0, 0), (0, 0, 0, 0), (0, 0, 0, 21), (2, 0, 0, 1), (0, True, 0, 1), 'bad'])
def test_invalid_state(state):
    with pytest.raises(ValueError):
        state_index(state)


def test_q_update_time_and_terminal():
    agent = AugmentedAgent(LearningConfig(), 971022)
    agent.q[state_index((1, 0, 0, 2))+(0,)] = 4
    agent.q[state_index((0, 0, 0, 1))] = [5, 3]
    agent.learn((1, 0, 0, 2), 0, 6, (0, 0, 0, 1), False)
    assert agent.q[state_index((1, 0, 0, 2))+(0,)] == 4.65
    agent.learn((0, 0, 0, 1), 0, 6, None, True)
    assert agent.q[state_index((0, 0, 0, 1))+(0,)] == 5.1
    with pytest.raises(ValueError):
        agent.learn((1, 0, 0, 2), 0, 6, (0, 0, 0, 2), False)
    with pytest.raises(ValueError):
        agent.learn((1, 0, 0, 2), 0, 6, None, True)


def test_exploration_ties_and_nonfinite():
    agent = AugmentedAgent(LearningConfig(), 971033)
    actions = [agent.act((0, 0, 0, 1), 0, explore=False) for _ in range(50)]
    assert set(actions) == {0, 1}
    assert {agent.act((0, 0, 0, 1), 1) for _ in range(50)} == {0, 1}
    with pytest.raises(ValueError):
        agent.act((0, 0, 0, 1), -1)
    agent.q[0, 0, 0, 0] = [np.nan, 0]
    with pytest.raises(ValueError):
        agent.act((0, 0, 0, 1), 0)
    with pytest.raises(ValueError):
        augmented_hash(agent.q)
    with pytest.raises(ValueError):
        augmented_hash(np.zeros((2, 2, 2)))


def test_exact_resume_and_observation_trace():
    market, learning = MarketConfig(steps=3), LearningConfig(episodes=5)
    run = AugmentedSession(market, learning, 971044)
    run.run_chunk(5, trace_limit=20)
    partial = AugmentedSession(market, learning, 971044)
    partial.run_chunk(2, trace_limit=20)
    resumed = AugmentedSession.from_checkpoint(partial.checkpoint())
    resumed.run_chunk(3, trace_limit=20)
    assert resumed.checkpoint() == run.checkpoint()
    assert run.visits.sum() == 15 and len(run.trace) == 15
    assert run.trace[0]['augmented_state_before'][-1] == 3
    assert run.trace[2]['terminal'] is True
    assert run.trace[2]['augmented_state_after'] is None
    with pytest.raises(ValueError):
        run.run_chunk(1)
    with pytest.raises(ValueError):
        run.run_chunk(0)


@pytest.mark.parametrize('field', ['sha256', 'schema', 'completed', 'visits', 'q'])
def test_checkpoint_rejects_corruption(field):
    run = AugmentedSession(MarketConfig(steps=2), LearningConfig(episodes=2), 971055)
    run.run_chunk(1)
    saved = run.checkpoint()
    if field == 'sha256':
        saved['seed'] += 1
    else:
        if field == 'schema':
            saved['schema'] = 'bad'
        elif field == 'completed':
            saved['completed'] = 3
        elif field == 'visits':
            saved['visits'][0][0][0][0][0] += 1
        else:
            saved['q'] = [0]
        saved['sha256'] = digest({k:v for k,v in saved.items() if k!='sha256'})
    with pytest.raises(ValueError):
        AugmentedSession.from_checkpoint(saved)


def test_no_oracle_labels_used_in_training(monkeypatch):
    from agent02_assignment.code import market_oracle
    monkeypatch.setattr(market_oracle, 'solve', lambda *a, **k: pytest.fail('No oracle in learner training'))
    run = AugmentedSession(MarketConfig(steps=1), LearningConfig(episodes=1), 971066)
    run.run_chunk(1)
    assert run.completed == 1


def test_persist_and_reuse(tmp_path):
    spec = {'run_id':'fixture/augmented', 'seed':971077}
    result = execute_augmented(tmp_path, spec, MarketConfig(steps=2), LearningConfig(episodes=3), 'proof', interval=2)
    assert result['summary']['market_steps'] == 6
    assert result == execute_augmented(tmp_path, spec, MarketConfig(steps=2), LearningConfig(episodes=3), 'proof', interval=2)
    with pytest.raises(ValueError):
        execute_augmented(tmp_path, spec, MarketConfig(steps=2), LearningConfig(episodes=3), 'changed')


def test_disk_pause_explicit_resume(tmp_path, monkeypatch):
    from agent02_assignment.code import augmented_runs as module
    spec = {'run_id':'fixture/pause', 'seed':971088}
    market, learning = MarketConfig(steps=2), LearningConfig(episodes=4)
    original = module.disk_guard
    calls = []
    def guard(base):
        calls.append(1)
        if len(calls)==4:
            raise RuntimeError('disk guard fixture')
        return original(base)
    monkeypatch.setattr(module, 'disk_guard', guard)
    with pytest.raises(RuntimeError):
        execute_augmented(tmp_path, spec, market, learning, 'proof', interval=2)
    monkeypatch.setattr(module, 'disk_guard', original)
    with pytest.raises(FileExistsError):
        execute_augmented(tmp_path, spec, market, learning, 'proof', interval=2)
    result = execute_augmented(tmp_path, spec, market, learning, 'proof', interval=2, resume=True)
    assert result['resumed'] is True
    saved = json.loads((tmp_path/'artifacts/runs/fixture/pause/checkpoint_e000004.json').read_text())
    fresh = AugmentedSession(market, learning, 971088)
    fresh.run_chunk(4, trace_limit=20)
    assert digest(saved) == digest(fresh.checkpoint())


@pytest.mark.parametrize('role', [0, 1])
def test_frozen_eval_preserves_training_rng_and_correct_role(monkeypatch, role):
    run = AugmentedSession(MarketConfig(), LearningConfig(episodes=2), 971099)
    run.run_chunk(2)
    before = copy.deepcopy(run.checkpoint())
    monkeypatch.setattr(AugmentedAgent, 'learn', lambda *a: pytest.fail('No learning in eval'))
    result = evaluate_augmented(run.agent.q, run.market, episodes=3, scenario_seed=1971099, role=role)
    assert run.checkpoint() == before
    assert result['q_hash_before'] == result['q_hash_after'] == augmented_hash(run.agent.q)
    assert result['role'] == role and result['exploration'] is False
    assert len(result['rows'])==3 and result['steps']==60
    assert sum(result['state_visits'])==60 and len(result['state_visits'])==160
    assert all(sum(r['learner_action_counts'])==20 for r in result['rows'])
    assert result == evaluate_augmented(run.agent.q, run.market, episodes=3, scenario_seed=1971099, role=role)


@pytest.mark.parametrize('episodes,role', [(501, 0), (0, 0), (1, 2)])
def test_eval_budget_rejected(episodes, role):
    with pytest.raises(ValueError):
        evaluate_augmented(np.zeros((2,2,2,20,2)), MarketConfig(), episodes=episodes, scenario_seed=1971011, role=role)


def test_oracle_one_step_expected_margin_and_no_terminal_bootstrap():
    solved = solve(MarketConfig(steps=1), gamma=.9)
    assert solved['q'][0,0,0,0].tolist() == pytest.approx([15.,13.5])
    assert solved['reset_expected_return'] == pytest.approx(35.)
    assert policy_value(MarketConfig(steps=1), kind='rule', gamma=1)['reset_expected_return'] == pytest.approx(35.)


@pytest.mark.parametrize('gamma', [0., .9, 1.])
def test_oracle_dominates_frozen_policy_and_horizon(gamma):
    market = MarketConfig(steps=3, kernel=((.9,.1),(.1,.9)))
    optimum = solve(market, gamma=gamma)
    for kind, q in [('rule', None), ('partial', np.zeros((2,2,2))), ('augmented', np.zeros((2,2,2,20,2)))]:
        value = policy_value(market, q=q, kind=kind, gamma=gamma)
        assert value['reset_expected_return'] <= optimum['reset_expected_return']+1e-10
    result = policy_value(market, q=optimum['q'], kind='augmented', gamma=gamma)
    assert result['reset_expected_return'] == pytest.approx(optimum['reset_expected_return'])


def test_oracle_rejects_bad_gamma_and_policy():
    with pytest.raises(ValueError):
        solve(MarketConfig(), gamma=-1)
    with pytest.raises(ValueError):
        policy_value(MarketConfig(), kind='bad')


def test_phase7_claim_reuse_and_consumed_failure(tmp_path):
    job = {'study_id':'fixture', 'policy_sha256':'q', 'scenario_sha256':'s', 'role':0}
    calls=[]
    def callback():
        calls.append(1)
        return {'rows':[{'episode':1,'reward':2}]}
    value = claim_once(tmp_path, job, 'proof', callback)
    assert claim_once(tmp_path, job, 'proof', callback)==value and calls==[1]
    with pytest.raises(ValueError):
        read_claim(tmp_path, job, 'bad-proof')
    path=tmp_path/'artifacts/evaluation/phase07/journal'/key_for(job)/'result.json'
    path.write_text('{}')
    with pytest.raises(ValueError):
        read_claim(tmp_path, job, 'proof')
    failed={**job,'role':1}
    with pytest.raises(RuntimeError,match='fixture failure'):
        claim_once(tmp_path, failed, 'proof', lambda: (_ for _ in ()).throw(RuntimeError('fixture failure')))
    with pytest.raises(RuntimeError,match='consumed'):
        claim_once(tmp_path, failed, 'proof', lambda: pytest.fail('No replay'))
