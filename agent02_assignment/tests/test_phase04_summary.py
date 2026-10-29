"""Single-factor sweep reporting from stored logs with explicit seed replication."""

import copy

import pytest

from agent02_assignment.code.baseline_runs import summarize
from agent02_assignment.code.sweep_analysis import CONFIG_IDS
from agent02_assignment.code.sweep_summary import summarize_matrix


def fixture_records():
    records = []
    for offset, config in enumerate(CONFIG_IDS):
        for index, seed in enumerate([11, 22, 33, 44, 55]):
            profit = float(index+offset+1)
            rows = [{'episode': i+1, 'rl_episode_reward': 20*profit, 'rule_episode_reward': 40.,
                     'rl_mean_reward_per_step': profit, 'rule_mean_reward_per_step': 2.,
                     'epsilon': .2, 'alpha': .1, 'action_counts': [[15, 5], [18, 2]]} for i in range(3)]
            records.append({'spec': {'config_id': config, 'seed': seed, 'run_id': f'fixture/{config}/{seed}'},
                            'rows': rows, 'result': {'summary': summarize(rows, 20),
                            'train_cpu_seconds': .1, 'train_wall_seconds': .2}})
    return records


def test_summary_does_not_treat_episodes_as_independent_training_seeds():
    output = summarize_matrix(fixture_records(), window=2)
    assert len(output['seed_summary']) == 25 and len(output['config_summary']) == 5
    assert len(output['curve_rows']) == 10
    first = output['config_summary'][0]
    assert first['n_training_seeds'] == 5
    assert first['rl_train_mean'] == 3 and first['rl_train_std'] == pytest.approx(2.5**.5)
    assert first['rule_train_std'] == 0
    assert output['paired']['alpha_low']['deltas'] == [1]*5


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'length', 'metric'])
def test_matrix_rejects_missing_cells_mixed_lengths_or_inconsistent_metrics(mutation):
    records = copy.deepcopy(fixture_records())
    if mutation == 'missing':
        records.pop()
    elif mutation == 'duplicate':
        records[-1] = records[0]
    elif mutation == 'length':
        records[-1]['rows'].pop()
    else:
        records[-1]['result']['summary']['rl_total_reward'] = 999
    with pytest.raises(ValueError):
        summarize_matrix(records, window=2)
