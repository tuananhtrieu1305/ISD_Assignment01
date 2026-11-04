"""Saved-log analysis and plot definitions, never model reruns."""

import numpy as np
import pytest

from agent02_assignment.phase03_reporting import analyze_rows, moving_average, validate_rows


def fixture_rows():
    return [{'episode': i+1, 'rl_episode_reward': float(20*i), 'rule_episode_reward': float(40*i),
             'rl_mean_reward_per_step': float(i), 'rule_mean_reward_per_step': float(2*i),
             'epsilon': .2, 'alpha': .1, 'action_counts': [[15, 5], [18, 2]]} for i in range(3)]


def test_moving_average_is_trailing_without_padding_or_future_values():
    result = moving_average([1, 3, 5, 7], 2)
    np.testing.assert_array_equal(result, [2, 4, 6])
    for window in (0, 5):
        with pytest.raises(ValueError):
            moving_average([1, 2], window)


def test_saved_rows_are_checked_against_step_count_and_order():
    rows = fixture_rows()
    validate_rows(rows, episodes=3, steps=20)
    rows[1]['episode'] = 3
    with pytest.raises(ValueError):
        validate_rows(rows, episodes=3, steps=20)


@pytest.mark.parametrize('field,value', [('rl_mean_reward_per_step', 999), ('epsilon', float('nan')),
                                        ('action_counts', [[1, 2], [18, 2]])])
def test_inconsistent_or_nonfinite_log_is_rejected(field, value):
    rows = fixture_rows()
    rows[1][field] = value
    with pytest.raises(ValueError):
        validate_rows(rows, episodes=3, steps=20)


def test_analysis_reports_real_aggregation_and_single_seed_limit():
    result = analyze_rows(fixture_rows(), steps=20, window=2)
    assert result['rl']['first_window_mean'] == .5
    assert result['rl']['last_window_mean'] == 1.5
    assert result['rule']['last_window_mean'] == 3
    assert result['training_seeds_per_track'] == 1
    assert result['rl']['raw_episode_mean_std_ddof1'] == 1
