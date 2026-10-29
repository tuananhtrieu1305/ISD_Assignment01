"""Seed/pair-level aggregation contracts, without training or final forwards."""

import copy

import pytest

from agent02_assignment.code.phase06_analysis import aggregate


def fixture_records():
    records = []
    def add(group, kernel, policy, seed, role, value, learner=None, checkpoint=None):
        result = {'episodes': 1, 'steps': 20, 'total_reward': value*20, 'mean_reward': value,
            'opponent_total_reward': 200., 'opponent_mean_reward': 10.,
            'learner_action_counts': [20, 0], 'opponent_action_counts': [20, 0],
            'rows': [{'learner_reward': value*20, 'opponent_reward': 200.,
                      'learner_action_counts': [20, 0], 'opponent_action_counts': [20, 0]}]}
        job = {'group': group, 'kernel_id': kernel, 'policy_id': policy, 'seed': seed, 'role': role,
               'learner': learner, 'checkpoint_episode': checkpoint}
        records.append({'job': job, 'result': result})
    for seed in (11, 22, 33, 44, 55):
        for role in (0, 1):
            for kernel in ('persistent', 'gold'):
                for policy, value in [('baseline_iid', 30), ('retrained', 32), ('rule', 35), ('no_discount', 35)]:
                    add('variant', kernel, policy, seed, role, value+role)
            for checkpoint in (0, 1000, 2500, 5000):
                for learner in (0, 1):
                    add('q8', 'iid', f'learner{learner}_e{checkpoint:06d}', seed, role,
                        20+learner*2+role+checkpoint/1000, learner, checkpoint)
    return records


def test_role_first_pair_first_aggregate():
    result = aggregate(fixture_records())
    assert len(result['variant_seed']) == 40
    assert len(result['variant_summary']) == 8
    assert len(result['q8_learner']) == 40
    assert len(result['q8_pair']) == 20
    assert result['variant_deltas'][0]['retrained_minus_baseline'] == 2
    assert result['q8_summary'][0]['target_mean'] == 21.5
    assert result['q8_summary'][-1]['target_mean'] == 26.5
    assert result['q8_summary'][-1]['n_independent_pair_seeds'] == 5


@pytest.mark.parametrize('kind', ['missing', 'duplicate', 'totals', 'seed'])
def test_incomplete_or_corrupt_aggregates_fail(kind):
    records = copy.deepcopy(fixture_records())
    if kind == 'missing':
        records.pop()
    elif kind == 'duplicate':
        records[-1] = records[0]
    elif kind == 'totals':
        records[0]['result']['total_reward'] += 1
    else:
        records[0]['job']['seed'] = 99
    with pytest.raises(ValueError):
        aggregate(records)
