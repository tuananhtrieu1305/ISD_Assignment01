"""Recompute train-only tables from all 25 saved trajectories, with no policy calls."""

import numpy as np

from .baseline_analysis import validate_rows
from .baseline_runs import summarize
from .sweep_analysis import CONFIG_IDS, aggregate_curves, paired_deltas

SEEDS = (11, 22, 33, 44, 55)


def summarize_matrix(records, *, window=100):
    by_cell = {(record['spec']['config_id'], record['spec']['seed']): record for record in records}
    expected = {(config, seed) for config in CONFIG_IDS for seed in SEEDS}
    if len(records) != 25 or set(by_cell) != expected:
        raise ValueError('Require 25 unique cells from five configs and five seeds')
    episodes = len(records[0]['rows'])
    seed_summary, config_summary, curve_rows, paired = [], [], [], {}
    for config in CONFIG_IDS:
        group = [by_cell[config, seed] for seed in SEEDS]
        for record in group:
            validate_rows(record['rows'], episodes=episodes, steps=20)
            summary = summarize(record['rows'], 20)
            if summary != record['result']['summary']:
                raise ValueError('Saved summary differs from raw episode log')
            seed_summary.append({'config_id': config, 'seed': record['spec']['seed'],
                'run_id': record['spec']['run_id'], **summary,
                'train_cpu_seconds': record['result']['train_cpu_seconds'],
                'train_wall_seconds': record['result']['train_wall_seconds']})
        curves = {agent: aggregate_curves([[row[agent+'_mean_reward_per_step'] for row in record['rows']]
                                          for record in group], window=window) for agent in ('rl', 'rule')}
        values = {'config_id': config, 'n_training_seeds': 5, 'partition': 'training', 'std_ddof': 1}
        for agent in ('rl', 'rule'):
            all_means = np.array([record['result']['summary'][agent+'_mean_reward_per_step'] for record in group])
            first = [np.mean([row[agent+'_mean_reward_per_step'] for row in record['rows'][:window]]) for record in group]
            last = [np.mean([row[agent+'_mean_reward_per_step'] for row in record['rows'][-window:]]) for record in group]
            values.update({agent+'_train_mean': float(all_means.mean()),
                           agent+'_train_std': float(all_means.std(ddof=1)),
                           agent+'_first_window_mean': float(np.mean(first)),
                           agent+'_last_window_mean': float(np.mean(last)),
                           agent+'_last_window_std': float(np.std(last, ddof=1))})
        values['train_cpu_seconds_mean'] = float(np.mean([r['result']['train_cpu_seconds'] for r in group]))
        values['train_wall_seconds_mean'] = float(np.mean([r['result']['train_wall_seconds'] for r in group]))
        config_summary.append(values)
        for index, episode in enumerate(curves['rl']['episode']):
            curve_rows.append({'config_id': config, 'episode': episode, 'n_training_seeds': 5,
                'rl_mean': curves['rl']['mean'][index], 'rl_std': curves['rl']['std'][index],
                'rule_mean': curves['rule']['mean'][index], 'rule_std': curves['rule']['std'][index]})
    baseline = {seed: by_cell['baseline', seed]['result']['summary']['rl_mean_reward_per_step'] for seed in SEEDS}
    for config in CONFIG_IDS[1:]:
        paired[config] = paired_deltas(baseline, {seed: by_cell[config, seed]['result']['summary']['rl_mean_reward_per_step']
                                                for seed in SEEDS})
    return {'seed_summary': seed_summary, 'config_summary': config_summary, 'curve_rows': curve_rows,
            'paired': paired, 'window': window, 'partition': 'training', 'n_training_seeds_per_config': 5}
