"""Aggregate saved final results: role-average first, then five trained-seed replicates."""

import numpy as np

from ..sweep_analysis import CONFIG_IDS

SEEDS = (11, 22, 33, 44, 55)


def validate_result(result):
    rows, steps = result['rows'], result['steps']
    if len(rows) != result['episodes'] or steps != result['episodes']*20:
        raise ValueError('Episode/step count differs')
    for prefix, name in [('learner', 'total_reward'), ('opponent', 'opponent_total_reward')]:
        total = sum(row[prefix+'_reward'] for row in rows)
        mean_key = 'mean_reward' if prefix == 'learner' else 'opponent_mean_reward'
        counts = np.array([row[prefix+'_action_counts'] for row in rows])
        if (not np.isfinite(total) or total != result[name] or total/steps != result[mean_key]
                or counts.shape != (len(rows), 2) or (counts < 0).any()
                or not (counts.sum(axis=1) == 20).all()
                or counts.sum(axis=0).tolist() != result[prefix+'_action_counts']):
            raise ValueError('Saved reward/action aggregation inconsistent')


def role_average(records):
    if len(records) != 2 or {record['job']['role'] for record in records} != {0, 1}:
        raise ValueError('Require exactly both roles')
    steps = sum(record['result']['steps'] for record in records)
    target = sum(record['result']['total_reward'] for record in records)
    opponent = sum(record['result']['opponent_total_reward'] for record in records)
    return {'target_mean': target/steps, 'opponent_mean': opponent/steps,
            'target_total_sum_roles': target, 'opponent_total_sum_roles': opponent, 'steps_sum_roles': steps,
            'discount_rate': sum(record['result']['learner_action_counts'][1] for record in records)/steps,
            'episodes_per_role': records[0]['result']['episodes'], 'roles': 2}


def mean_std(values):
    array = np.array(values, dtype=float)
    if len(array) != 5 or not np.isfinite(array).all():
        raise ValueError('Five finite seed-level values required')
    return float(array.mean()), float(array.std(ddof=1))


def aggregate_evaluations(records):
    if len(records) != 71:
        raise ValueError('Require all 71 final claims')
    indexed = {}
    for record in records:
        validate_result(record['result'])
        job = record['job']
        key = (job['group'], job['config_id'], job['train_seed'], job['role'])
        if key in indexed:
            raise ValueError('Duplicate final job identity')
        indexed[key] = record
    def pair(group, config, seed):
        try:
            return role_average([indexed[group, config, seed, role] for role in (0, 1)])
        except KeyError as error:
            raise ValueError('Missing configuration/seed/role') from error
    controls = {(kind, seed): pair('control', kind, seed) for kind in ('rule', 'no_discount') for seed in SEEDS}
    multi = []
    for config in CONFIG_IDS:
        for seed in SEEDS:
            values = pair('core', config, seed)
            multi.append({'config_id': config, 'train_seed': seed, 'partition': 'final', **values,
                'within_match_delta': values['target_mean']-values['opponent_mean'],
                'rule_control_mean': controls['rule', seed]['target_mean'],
                'no_discount_control_mean': controls['no_discount', seed]['target_mean'],
                'delta_vs_rule_policy': values['target_mean']-controls['rule', seed]['target_mean'],
                'delta_vs_no_discount_policy': values['target_mean']-controls['no_discount', seed]['target_mean']})
    baseline = {row['train_seed']: row['target_mean'] for row in multi if row['config_id'] == 'baseline'}
    paired_rows, summaries = [], []
    for config in CONFIG_IDS:
        group = [row for row in multi if row['config_id'] == config]
        result = {'config_id': config, 'n_training_seeds': 5, 'roles_averaged_first': True, 'std_ddof': 1}
        for field in ('target_mean', 'opponent_mean', 'within_match_delta', 'delta_vs_rule_policy',
                      'delta_vs_no_discount_policy', 'discount_rate'):
            mean, std = mean_std([row[field] for row in group])
            stem = field.removesuffix('_mean')
            result[stem+'_mean'], result[stem+'_std'] = mean, std
        deltas = []
        for row in group:
            delta = row['target_mean']-baseline[row['train_seed']]
            deltas.append(delta)
            paired_rows.append({'config_id': config, 'train_seed': row['train_seed'],
                                'delta_vs_baseline': delta, 'delta_vs_rule_policy': row['delta_vs_rule_policy'],
                                'delta_vs_no_discount_policy': row['delta_vs_no_discount_policy'],
                                'within_match_delta': row['within_match_delta']})
        result['paired_delta_baseline_mean'], result['paired_delta_baseline_std'] = mean_std(deltas)
        summaries.append(result)
    reference = indexed.get(('reference_native', 'reference_native', 42, 0))
    if reference is None:
        raise ValueError('Missing native reference')
    native = reference['result']
    return {'multi_seed': multi, 'config_summary': summaries, 'paired_rows': paired_rows,
            'controls': [{'kind': kind, 'scenario_panel': seed, **controls[kind, seed]}
                         for kind in ('rule', 'no_discount') for seed in SEEDS],
            'reference_native': {'target_mean': native['mean_reward'], 'opponent_mean': native['opponent_mean_reward'],
                'target_total': native['total_reward'], 'opponent_total': native['opponent_total_reward'],
                'steps': native['steps'], 'roles': 1, 'n_training_seeds': 1, 'native_rng': True}}
