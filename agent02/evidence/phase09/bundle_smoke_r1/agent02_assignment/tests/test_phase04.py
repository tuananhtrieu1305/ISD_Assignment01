"""Sweep selection, reuse, factor isolation and seed-aware aggregation contracts."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from agent02_assignment.code.baseline_runs import execute_run
from agent02_assignment.code.controlled import LearningConfig, MarketConfig
from agent02_assignment.code.sweep_analysis import aggregate_curves, paired_deltas, validate_factors
from agent02_assignment.phase04 import BASELINE_ID, select_specs, train_one

BASE = Path(__file__).resolve().parents[1]


def protocol():
    return json.loads((BASE/'docs/protocol_v1.json').read_text())


def test_exact_25_cells_include_one_reused_baseline_and_24_new_runs():
    specs = select_specs(protocol())
    assert len(specs) == len({row['run_id'] for row in specs}) == 25
    assert len([row for row in specs if row['run_id'] != BASELINE_ID]) == 24
    assert {row['seed'] for row in specs} == {11, 22, 33, 44, 55}
    assert {row['phase'] for row in specs} == {3, 4}


def test_factor_contract_rejects_simultaneous_gamma_or_market_changes():
    data = protocol()
    validate_factors(data)
    bad = copy.deepcopy(data)
    bad['controlled_configs']['alpha_low']['gamma'] = .5
    with pytest.raises(ValueError):
        validate_factors(bad)
    bad = copy.deepcopy(data)
    bad['controlled_configs']['unexpected'] = copy.deepcopy(bad['controlled_configs']['baseline'])
    with pytest.raises(ValueError):
        validate_factors(bad)
    bad = copy.deepcopy(data)
    bad['controlled_configs']['epsilon_low_fixed']['alpha'] = .5
    with pytest.raises(ValueError):
        validate_factors(bad)


def test_selection_rejects_missing_duplicate_or_foreign_core_cell():
    for mutation in ('missing', 'duplicate', 'foreign', 'phase'):
        data = protocol()
        if mutation == 'missing':
            data['training_runs'] = [row for row in data['training_runs'] if row['run_id'] != BASELINE_ID]
        elif mutation == 'duplicate':
            data['training_runs'].append(copy.deepcopy(select_specs(data)[0]))
        elif mutation == 'foreign':
            next(row for row in data['training_runs'] if row['run_id'] == BASELINE_ID)['seed'] = 999
        else:
            next(row for row in data['training_runs'] if row['run_id'] == BASELINE_ID)['phase'] = 4
        with pytest.raises(ValueError):
            select_specs(data)


def test_curve_variation_is_sample_std_between_five_training_seeds():
    values = np.array([[seed]*4 for seed in (1, 2, 3, 4, 5)], dtype=float)
    result = aggregate_curves(values, window=2)
    np.testing.assert_array_equal(result['mean'], [3, 3, 3])
    np.testing.assert_allclose(result['std'], np.sqrt(2.5))
    np.testing.assert_array_equal(result['episode'], [2, 3, 4])
    assert result['n_seeds'] == 5 and result['ddof'] == 1


@pytest.mark.parametrize('values', [np.zeros((1, 3)), np.full((5, 3), np.nan), np.zeros(3)])
def test_aggregate_rejects_invalid_replicate_shape_or_nonfinite(values):
    with pytest.raises(ValueError):
        aggregate_curves(values, window=2)


def test_paired_delta_joins_by_seed_not_input_order():
    baseline = {11: 10., 22: 20., 33: 30., 44: 40., 55: 50.}
    changed = {55: 55., 11: 11., 44: 44., 22: 22., 33: 33.}
    result = paired_deltas(baseline, changed)
    assert result['seeds'] == [11, 22, 33, 44, 55]
    assert result['deltas'] == [1, 2, 3, 4, 5] and result['mean'] == 3
    assert result['std'] == pytest.approx(np.sqrt(2.5))
    with pytest.raises(ValueError):
        paired_deltas(baseline, {11: 1})
    with pytest.raises(ValueError):
        paired_deltas(baseline, {**changed, 11: float('nan')})


def test_baseline_reuse_never_calls_training_or_changes_registration(tmp_path, monkeypatch):
    import agent02_assignment.code.sweep_runs as runner

    data = protocol()
    for config in data['controlled_configs'].values():
        config['episodes'] = 2
    spec = next(row for row in select_specs(data) if row['run_id'] == BASELINE_ID)
    existing = execute_run(tmp_path, spec, MarketConfig(), LearningConfig(episodes=2), 'phase3-lock')
    monkeypatch.setattr(runner, 'execute_run', lambda *args, **kwargs: pytest.fail('baseline must reuse'))
    result = train_one(tmp_path, spec, data, 'phase4-lock', 'phase3-lock')
    assert result['q_sha256'] == existing['q_sha256']
    assert result['reused_from_phase3'] is True
    with pytest.raises(ValueError, match='registration'):
        train_one(tmp_path, spec, data, 'phase4-lock', 'wrong-phase3-lock')


def test_new_run_uses_its_single_factor_config_and_reuses_done(tmp_path):
    data = protocol()
    for config in data['controlled_configs'].values():
        config['episodes'] = 2
    spec = next(row for row in select_specs(data) if row['config_id'] == 'alpha_low' and row['seed'] == 22)
    result = train_one(tmp_path, spec, data, 'phase4-lock', 'phase3-lock')
    manifest = json.loads((tmp_path/'artifacts/runs'/spec['run_id']/'manifest.json').read_text())
    assert manifest['learning']['alpha'] == .01 and manifest['learning']['gamma'] == .9
    assert result['reused_from_phase3'] is False
    assert train_one(tmp_path, spec, data, 'phase4-lock', 'phase3-lock')['q_sha256'] == result['q_sha256']
