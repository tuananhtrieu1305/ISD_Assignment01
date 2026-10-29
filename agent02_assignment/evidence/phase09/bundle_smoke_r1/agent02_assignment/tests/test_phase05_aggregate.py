"""Role average first, seed uncertainty second; only synthetic numerical fixtures."""

import copy

import pytest

from agent02_assignment.code.evaluation.aggregate_v1 import aggregate_evaluations
from agent02_assignment.code.sweep_analysis import CONFIG_IDS


def fixtures():
    records = []
    def add(group, config, seed, role, value):
        rows = [{'episode': ep+1, 'learner_reward': value*20, 'opponent_reward': 40.,
                 'learner_action_counts': [20, 0], 'opponent_action_counts': [20, 0]} for ep in range(2)]
        records.append({'job': {'group': group, 'config_id': config, 'train_seed': seed, 'role': role},
                        'result': {'episodes': 2, 'steps': 40, 'rows': rows, 'total_reward': value*40,
                        'opponent_total_reward': 80., 'mean_reward': value, 'opponent_mean_reward': 2.,
                        'learner_action_counts': [40, 0], 'opponent_action_counts': [40, 0]}})
    for offset, config in enumerate(CONFIG_IDS):
        for index, seed in enumerate((11, 22, 33, 44, 55)):
            for role in (0, 1):
                add('core', config, seed, role, float(index+offset+2+(1 if role == 0 else -1)))
    for kind in ('rule', 'no_discount'):
        for seed in (11, 22, 33, 44, 55):
            for role in (0, 1):
                add('control', kind, seed, role, 2.)
    add('reference_native', 'reference_native', 42, 0, 9.)
    return records


def test_aggregate_uses_five_role_averaged_values_not_ten_roles_or_episodes():
    result = aggregate_evaluations(fixtures())
    assert len(result['multi_seed']) == 25 and len(result['config_summary']) == 5
    baseline = result['config_summary'][0]
    assert baseline['n_training_seeds'] == 5
    assert baseline['target_mean'] == 4 and baseline['target_std'] == pytest.approx(2.5**.5)
    assert baseline['within_match_delta_mean'] == 2
    assert result['config_summary'][1]['paired_delta_baseline_mean'] == 1
    assert result['config_summary'][1]['paired_delta_baseline_std'] == 0
    assert result['reference_native']['target_mean'] == 9


@pytest.mark.parametrize('mutation', ['missing_role', 'duplicate', 'reward', 'actions'])
def test_incomplete_or_inconsistent_saved_outputs_are_rejected(mutation):
    records = copy.deepcopy(fixtures())
    if mutation == 'missing_role':
        records.pop(0)
    elif mutation == 'duplicate':
        records[1] = copy.deepcopy(records[0])
    elif mutation == 'reward':
        records[0]['result']['total_reward'] += 1
    else:
        records[0]['result']['learner_action_counts'] = [39, 0]
    with pytest.raises(ValueError):
        aggregate_evaluations(records)
