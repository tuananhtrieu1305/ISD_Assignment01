"""One-factor contracts and training-seed statistics; no model execution."""

import numpy as np

from .baseline_analysis import moving_average

CONFIG_IDS = ('baseline', 'alpha_low', 'alpha_high', 'epsilon_low_fixed', 'epsilon_high_fixed')


def validate_factors(protocol):
    configs = protocol['controlled_configs']
    if set(configs) != set(CONFIG_IDS):
        raise ValueError('Exactly five core configurations are required')
    baseline = configs['baseline']
    for name in CONFIG_IDS[1:]:
        changed = {key for key in baseline if baseline[key] != configs[name][key]}
        expected = {'alpha'} if name.startswith('alpha') else {'epsilon_start', 'epsilon_min', 'epsilon_decay'}
        if changed != expected or set(configs[name]) != set(baseline):
            raise ValueError('Sweep must change only its declared factor')


def aggregate_curves(values, *, window=100):
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[0] != 5 or not np.isfinite(array).all():
        raise ValueError('Expected five finite training-seed trajectories')
    smooth = np.array([moving_average(row, window) for row in array])
    return {'episode': np.arange(window, array.shape[1]+1).tolist(), 'mean': smooth.mean(axis=0).tolist(),
            'std': smooth.std(axis=0, ddof=1).tolist(), 'n_seeds': 5, 'ddof': 1, 'window': window}


def paired_deltas(baseline, changed):
    if set(baseline) != set(changed) or len(baseline) != 5:
        raise ValueError('Paired training comparisons require the same five seed IDs')
    seeds = sorted(baseline)
    deltas = np.array([changed[seed]-baseline[seed] for seed in seeds], dtype=float)
    if not np.isfinite(deltas).all():
        raise ValueError('Paired deltas must be finite')
    return {'seeds': seeds, 'deltas': deltas.tolist(), 'mean': float(deltas.mean()),
            'std': float(deltas.std(ddof=1)), 'n_seeds': 5, 'ddof': 1, 'partition': 'training'}
