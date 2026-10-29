"""Saved-output analysis: average physical roles, then dependent learners within a pair."""

import numpy as np

from .evaluation.aggregate_v1 import SEEDS, mean_std, role_average, validate_result


def aggregate(records):
    if len(records) != 160:
        raise ValueError('Require160 Phase6 claims')
    indexed = {}
    for record in records:
        validate_result(record['result'])
        j = record['job']
        key = (j['group'], j['kernel_id'], j['policy_id'], j['seed'], j['role'])
        if key in indexed or j['seed'] not in SEEDS:
            raise ValueError('Duplicate identity or unexpected seed')
        indexed[key] = record
    def pair(group, kernel, policy, seed):
        try:
            return role_average([indexed[group, kernel, policy, seed, role] for role in (0, 1)])
        except KeyError as error:
            raise ValueError('Missing role/group/policy/seed') from error
    variant, deltas, summary = [], [], []
    for kernel in ('persistent', 'gold'):
        for seed in SEEDS:
            values = {}
            for policy in ('baseline_iid', 'retrained', 'rule', 'no_discount'):
                values[policy] = pair('variant', kernel, policy, seed)
                variant.append({'kernel': kernel, 'policy': policy, 'seed': seed, **values[policy]})
            deltas.append({'kernel': kernel, 'seed': seed,
                'retrained_minus_baseline': values['retrained']['target_mean']-values['baseline_iid']['target_mean'],
                'retrained_minus_rule': values['retrained']['target_mean']-values['rule']['target_mean'],
                'baseline_minus_rule': values['baseline_iid']['target_mean']-values['rule']['target_mean']})
        for policy in ('baseline_iid', 'retrained', 'rule', 'no_discount'):
            rows = [r for r in variant if r['kernel']==kernel and r['policy']==policy]
            mean, std = mean_std([r['target_mean'] for r in rows])
            summary.append({'kernel': kernel, 'policy': policy, 'target_mean': mean, 'target_std': std,
                'n_seed_or_scenario_panels': 5, 'n_means_trained_replicates': policy not in ('rule', 'no_discount'),
                'std_ddof': 1})
    learners, pairs, q8summary = [], [], []
    for checkpoint in (0, 1000, 2500, 5000):
        for seed in SEEDS:
            pairvalues = []
            for learner in (0, 1):
                values = pair('q8', 'iid', f'learner{learner}_e{checkpoint:06d}', seed)
                learners.append({'checkpoint_episode': checkpoint, 'seed': seed, 'learner': learner, **values})
                pairvalues.append(values['target_mean'])
            pairs.append({'checkpoint_episode': checkpoint, 'seed': seed,
                          'target_mean': float(np.mean(pairvalues)), 'learner_gap_absolute': abs(pairvalues[1]-pairvalues[0])})
        selected = [r for r in pairs if r['checkpoint_episode']==checkpoint]
        mean, std = mean_std([r['target_mean'] for r in selected])
        q8summary.append({'checkpoint_episode': checkpoint, 'target_mean': mean, 'target_std': std,
                         'n_independent_pair_seeds': 5, 'roles_then_learners_averaged_first': True, 'std_ddof': 1})
    return {'variant_seed': variant, 'variant_deltas': deltas, 'variant_summary': summary,
            'q8_learner': learners, 'q8_pair': pairs, 'q8_summary': q8summary}
