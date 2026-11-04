"""Validate and summarize saved episode logs; no agents or model forward passes."""

import numpy as np

from .controlled import integer


def moving_average(values, window):
    integer(window, 'window', 1)
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or len(array) < window or not np.isfinite(array).all():
        raise ValueError('Moving average requires a finite vector at least window long')
    return np.convolve(array, np.ones(window)/window, mode='valid')


def validate_rows(rows, *, episodes, steps):
    if len(rows) != episodes:
        raise ValueError('Wrong number of episode rows')
    for index, row in enumerate(rows):
        scalar_fields = ['rl_episode_reward', 'rule_episode_reward', 'rl_mean_reward_per_step',
                         'rule_mean_reward_per_step', 'epsilon', 'alpha']
        if row['episode'] != index+1 or not np.isfinite([row[key] for key in scalar_fields]).all():
            raise ValueError('Episode order or finite scalar contract failed')
        counts = np.asarray(row['action_counts'])
        if (counts.shape != (2, 2) or not np.issubdtype(counts.dtype, np.integer)
                or (counts < 0).any() or not (counts.sum(axis=1) == steps).all()):
            raise ValueError('Action count mismatch')
        for name in ('rl', 'rule'):
            if not np.isclose(row[name+'_episode_reward']/steps, row[name+'_mean_reward_per_step']):
                raise ValueError('Mean reward denominator mismatch')


def analyze_rows(rows, *, steps=20, window=100):
    validate_rows(rows, episodes=len(rows), steps=steps)
    result = {'training_seeds_per_track': 1, 'episodes': len(rows), 'window': window,
              'unit': 'simulated profit per market step', 'uncertainty_band': None}
    for name in ('rl', 'rule'):
        raw = np.array([row[name+'_mean_reward_per_step'] for row in rows])
        smooth = moving_average(raw, window)
        result[name] = {'first_window_mean': float(smooth[0]), 'last_window_mean': float(smooth[-1]),
                        'window_min': float(smooth.min()), 'window_max': float(smooth.max()),
                        'raw_episode_mean_std_ddof1': float(raw.std(ddof=1)),
                        'last_window_minus_first': float(smooth[-1]-smooth[0])}
    return result
