"""Pre-registration and REF/CONTROLLED boundaries; no full experiment here."""

from pathlib import Path

import numpy as np
import pytest

from agent02_assignment.code.reference_adapter import load_reference, reference_smoke
from agent02_assignment.protocol import build_protocol

BASE = Path(__file__).resolve().parents[1]


def test_protocol_declares_exactly_56_unique_runs_and_five_core_configs():
    protocol = build_protocol()
    assert len(protocol['training_runs']) == 56
    assert len({run['run_id'] for run in protocol['training_runs']}) == 56
    assert len(protocol['controlled_configs']) == 5
    assert protocol['train_seeds'] == [11, 22, 33, 44, 55]
    assert all(run['status'] == 'declared_not_started' for run in protocol['training_runs'])
    assert protocol['budget']['train_episodes'] == 5000
    assert protocol['budget']['steps_per_episode'] == 20
    assert protocol['budget']['final_evaluation_episodes_per_role'] == 500


def test_development_and_final_seed_namespaces_are_disjoint():
    evaluation = build_protocol()['evaluation']
    assert not set(evaluation['development_scenario_seeds']) & set(evaluation['final_scenario_seeds'])
    assert not set(evaluation['development_scenario_seeds']) & {11, 22, 33, 44, 55, 42}
    assert evaluation['final_evaluation_authorized_in_phase2'] is False
    assert evaluation['final_gate_phase'] == 5
    assert evaluation['roles'] == [0, 1]


def test_configuration_sweeps_change_only_the_declared_factor():
    configs = build_protocol()['controlled_configs']
    baseline = configs['baseline']
    for name in ('alpha_low', 'alpha_high'):
        assert {key for key in baseline if baseline[key] != configs[name][key]} == {'alpha'}
    for name in ('epsilon_low_fixed', 'epsilon_high_fixed'):
        assert {key for key in baseline if baseline[key] != configs[name][key]} == {
            'epsilon_start', 'epsilon_min', 'epsilon_decay'}


def test_gold_rule_is_locked_but_no_measured_kernel_is_fabricated():
    gold = build_protocol()['future_variants']['gold']
    assert gold['calibration_status'] == 'deferred_to_phase6'
    assert gold['last_allowed_month'] == '2006-08'
    assert gold['smoothing_pseudocount'] == 1
    assert 'estimated_kernel' not in gold
    assert gold['real_demand_measurement'] is False


def test_teacher_smoke_matches_direct_reference_without_running_main():
    teacher = load_reference()
    direct, rows = teacher.train_rl_against_rule(teacher.Config(episodes=3), seed=730003)
    wrapped = reference_smoke(episodes=3, seed=730003)
    np.testing.assert_array_equal(wrapped['q'], direct.q)
    assert wrapped['rows'] == rows
    assert wrapped['purpose'] == 'smoke_only_not_experimental_result'
    assert not (BASE.parent / 'agent02_results').exists()


@pytest.mark.parametrize('episodes', [0, 101, 5000])
def test_reference_smoke_cannot_launch_full_training(episodes):
    with pytest.raises(ValueError):
        reference_smoke(episodes=episodes, seed=730003)


def test_reference_loader_rejects_wrong_path_or_hash(tmp_path):
    wrong = tmp_path / 'not_a_reference.py'
    wrong.write_text('raise RuntimeError("must not run")', encoding='utf-8')
    with pytest.raises(ValueError):
        load_reference(wrong)
