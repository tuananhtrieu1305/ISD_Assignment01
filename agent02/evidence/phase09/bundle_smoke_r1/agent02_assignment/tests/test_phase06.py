"""Small synthetic fixtures only; scientific phase6 runs are never triggered here."""

import json
from dataclasses import replace

import numpy as np
import pytest

from agent02_assignment.code.controlled import LearningConfig, MarketConfig, MarketEnv, Tape
from agent02_assignment.code.evaluation.phase06_journal import claim_once, key_for, read_claim
from agent02_assignment.code.gold_regime import estimate_regimes, month_number, prefix_records
from agent02_assignment.code.pair_training import PairSession, execute_pair
from agent02_assignment.code.training import TrainSession, digest


def test_month_and_prefix_does_not_access_future_price():
    class Future:
        def __getitem__(self, index):
            if index == 0:
                return '2006M09'
            raise AssertionError('Future price accessed')
    assert month_number('2006-08') + 1 == month_number('2006M09')
    assert prefix_records([('2006M08', 600), Future()], 1, '2006-08') == [('2006-08', 600)]


@pytest.mark.parametrize('bad', ['abc', '2006-00', '2006-13'])
def test_invalid_month(bad):
    with pytest.raises(ValueError):
        month_number(bad)


def test_regime_counts_smoothing_ties_and_gap():
    # States Jan->Feb=1, Feb->Mar=0, Mar->Apr=0; gap breaks chain before Jun.
    rows = [('2000-01', 10), ('2000-02', 11), ('2000-03', 11), ('2000-04', 10),
            ('2000-06', 15), ('2000-07', 16), ('2000-08', 17)]
    result = estimate_regimes(rows)
    assert result['transition_counts'] == [[1, 0], [1, 1]]
    np.testing.assert_allclose(result['kernel'], [[2/3, 1/3], [1/2, 1/2]])
    assert result['regime_counts'] == [2, 3]
    assert result['gap_pairs_excluded'] == 1
    assert result['missing_months'] == ['2000-05']


def test_missing_prices_not_imputed_or_bridged():
    result = estimate_regimes([('2000-01', 10), ('2000-02', None), ('2000-03', 12),
                               ('2000-04', 13), ('2000-05', 14)])
    assert result['transition_counts'] == [[0, 0], [0, 1]]
    assert result['invalid_price_months'] == ['2000-02']


@pytest.mark.parametrize('rows', [[], [('2000-01', 1)], [('2000-01', 1), ('2000-01', 2)],
    [('2000-02', 1), ('2000-01', 2)]])
def test_bad_gold_history(rows):
    with pytest.raises(ValueError):
        estimate_regimes(rows)


def test_pair_resume_is_exact_and_rngs_independent():
    market, learning = MarketConfig(steps=3), LearningConfig(episodes=7)
    full = PairSession(market, learning, 991011)
    full.run_chunk(7, trace_limit=20)
    partial = PairSession(market, learning, 991011)
    partial.run_chunk(3, trace_limit=20)
    saved = partial.checkpoint()
    resumed = PairSession.from_checkpoint(saved)
    resumed.run_chunk(4, trace_limit=20)
    assert resumed.checkpoint() == full.checkpoint()
    assert saved['rng']['agents'][0] != saved['rng']['agents'][1]
    assert full.visits.shape == (2, 2, 2, 2)
    assert full.visits.sum(axis=(1, 2, 3)).tolist() == [21, 21]
    assert full.rows[0]['action_counts'][0] != []
    assert len(full.trace) == 20


def test_pair_selects_both_actions_before_learning():
    run = PairSession(MarketConfig(steps=1), LearningConfig(episodes=1), 991022)
    calls = []
    for i in (0, 1):
        run.agents[i].act = lambda state, epsilon, i=i: (calls.append(('act', i, state)) or i)
        run.agents[i].learn = lambda *args, i=i: calls.append(('learn', i, args[-1]))
    run.run_chunk(1)
    assert [c[:2] for c in calls] == [('act', 0), ('act', 1), ('learn', 0), ('learn', 1)]
    assert calls[0][2] == calls[1][2]
    assert calls[2][-1] is True and calls[3][-1] is True


@pytest.mark.parametrize('kind', ['hash', 'count', 'visits', 'q', 'schema'])
def test_pair_rejects_invalid_checkpoint(kind):
    run = PairSession(MarketConfig(steps=2), LearningConfig(episodes=2), 991033)
    run.run_chunk(1)
    saved = run.checkpoint()
    if kind == 'hash':
        saved['seed'] += 1
    else:
        if kind == 'count':
            saved['completed'] = 3
        elif kind == 'visits':
            saved['visits'][0][0][0][0] += 1
        elif kind == 'q':
            saved['q'][0] = [0]
        else:
            saved['schema'] = 'wrong'
        saved['sha256'] = digest({k: v for k, v in saved.items() if k != 'sha256'})
    with pytest.raises(ValueError):
        PairSession.from_checkpoint(saved)


def test_pair_budget_and_guard():
    run = PairSession(MarketConfig(), LearningConfig(episodes=1), 991044)
    with pytest.raises(ValueError):
        run.run_chunk(2)
    with pytest.raises(ValueError):
        run.run_chunk(0)
    with pytest.raises(RuntimeError):
        run.run_chunk(1, guard=lambda: (_ for _ in ()).throw(RuntimeError('disk')))
    assert run.completed == 0


def test_variant_changes_only_kernel_and_resume():
    market = replace(MarketConfig(steps=3), kernel=((1, 0), (0, 1)))
    tape = Tape.generate(market, 991055, 0)
    assert len(set(tape.demand)) == 1
    env = MarketEnv(market, 1)
    states = env.reset(tape)
    demand = states[0][0]
    for _ in range(3):
        assert env.step((0, 0)).states[0][0] == demand
    learning = LearningConfig(episodes=4)
    full = TrainSession(market, learning, 991055)
    full.run_chunk(4)
    partial = TrainSession(market, learning, 991055)
    partial.run_chunk(2)
    resumed = TrainSession.from_checkpoint(partial.checkpoint())
    resumed.run_chunk(2)
    assert full.checkpoint() == resumed.checkpoint()


def test_pair_persistence_and_completed_reuse(tmp_path):
    spec = {'run_id': 'fixture/pair', 'seed': 991066, 'learners': 2}
    market, learning = MarketConfig(steps=2), LearningConfig(episodes=3)
    result = execute_pair(tmp_path, spec, market, learning, 'proof', interval=2)
    assert result['status'] == 'COMPLETE'
    assert result['summary']['market_steps'] == 6
    assert result == execute_pair(tmp_path, spec, market, learning, 'proof', interval=2)
    with pytest.raises(ValueError):
        execute_pair(tmp_path, spec, market, learning, 'other-proof', interval=2)


def test_pair_resume_claim_preserves_rng(tmp_path, monkeypatch):
    from agent02_assignment.code import pair_training as module
    spec = {'run_id': 'fixture/pause', 'seed': 991077, 'learners': 2}
    market, learning = MarketConfig(steps=2), LearningConfig(episodes=4)
    guard = module.disk_guard
    calls = []
    def stop(base):
        calls.append(1)
        if len(calls) == 4:
            raise RuntimeError('disk reserve')
        return guard(base)
    monkeypatch.setattr(module, 'disk_guard', stop)
    with pytest.raises(RuntimeError):
        execute_pair(tmp_path, spec, market, learning, 'proof', interval=2)
    monkeypatch.setattr(module, 'disk_guard', guard)
    with pytest.raises(FileExistsError):
        execute_pair(tmp_path, spec, market, learning, 'proof', interval=2)
    result = execute_pair(tmp_path, spec, market, learning, 'proof', interval=2, resume=True)
    assert result['resumed'] is True
    saved = json.loads((tmp_path/'artifacts/runs/fixture/pause/checkpoint_e000004.json').read_text())
    fresh = PairSession(market, learning, 991077)
    fresh.run_chunk(4, trace_limit=20)
    assert digest(saved) == digest(fresh.checkpoint())


def test_phase6_journal_reuse_and_tamper(tmp_path):
    job = {'study_id': 'fixture', 'policy_sha256': 'q', 'scenario_sha256': 's', 'role': 0}
    calls = []
    def callback():
        calls.append(1)
        return {'rows': [{'episode': 1, 'value': 2}]}
    record = claim_once(tmp_path, job, 'proof', callback)
    assert claim_once(tmp_path, job, 'proof', callback) == record
    assert calls == [1]
    with pytest.raises(ValueError):
        read_claim(tmp_path, job, 'other')
    path = tmp_path/'artifacts/evaluation/phase06/journal'/key_for(job)/'result.json'
    path.write_text('{}')
    with pytest.raises(ValueError):
        read_claim(tmp_path, job, 'proof')


def test_phase6_consumed_failure_never_replayed(tmp_path):
    job = {'study_id': 'fixture', 'policy_sha256': 'q', 'scenario_sha256': 's', 'role': 1}
    def fail():
        raise RuntimeError('fixture failure')
    with pytest.raises(RuntimeError, match='fixture failure'):
        claim_once(tmp_path, job, 'proof', fail)
    with pytest.raises(RuntimeError, match='consumed'):
        claim_once(tmp_path, job, 'proof', lambda: pytest.fail('Must not replay'))


def test_key_includes_all_identity_fields():
    job = {'study_id': 'f', 'policy_sha256': 'q', 'scenario_sha256': 's', 'role': 0}
    assert len({key_for(job), *(key_for({**job, k: v}) for k, v in
        [('study_id', 'f2'), ('policy_sha256', 'q2'), ('scenario_sha256', 's2'), ('role', 1)])}) == 5
