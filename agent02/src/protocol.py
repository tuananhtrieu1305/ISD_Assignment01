"""A priori protocol builder; no model execution, raw-price parsing or TEST access."""

import json
from dataclasses import asdict, replace
from pathlib import Path

from .code.controlled import LearningConfig, MarketConfig
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent


def build_protocol():
    seeds = [11, 22, 33, 44, 55]
    default = LearningConfig()
    configs = {'baseline': asdict(default), 'alpha_low': asdict(replace(default, alpha=.01)),
               'alpha_high': asdict(replace(default, alpha=.50)),
               'epsilon_low_fixed': asdict(replace(default, epsilon_start=.05, epsilon_min=.05, epsilon_decay=1)),
               'epsilon_high_fixed': asdict(replace(default, epsilon_start=.30, epsilon_min=.30, epsilon_decay=1))}
    runs = [{'run_id': 'ref/baseline/s0042', 'track': 'REF', 'phase': 3, 'seed': 42,
             'config_id': 'baseline', 'kernel_id': 'iid', 'learners': 1, 'status': 'declared_not_started'}]
    for config_id in configs:
        for seed in seeds:
            runs.append({'run_id': f'controlled/iid/{config_id}/s{seed:04d}', 'track': 'CONTROLLED',
                         'phase': 3 if config_id == 'baseline' and seed == 11 else 4,
                         'seed': seed, 'config_id': config_id, 'kernel_id': 'iid', 'learners': 1,
                         'status': 'declared_not_started'})
    groups = [('two_learners', ('iid',), 6, 2), ('retrain', ('persistent', 'gold'), 6, 1),
              ('augmented', ('iid', 'persistent', 'gold'), 7, 1)]
    for group, kernels, phase, learners in groups:
        for kernel in kernels:
            for seed in seeds:
                runs.append({'run_id': f'controlled/{kernel}/{group}/s{seed:04d}', 'track': 'CONTROLLED',
                             'phase': phase, 'seed': seed, 'config_id': group, 'kernel_id': kernel,
                             'learners': learners, 'status': 'declared_not_started'})
    split_path = BASE.parent / 'data/splits/v3/ch4_gold_pink_sheet/split_contract.json'
    split = json.loads(split_path.read_text())
    cutoff = next(item['target_end'][:7] for item in split['partitions'] if item['name'] == 'train')
    return {
        'schema_version': 'ag02.protocol.1', 'local_date': '2026-10-24', 'device': 'CPU NumPy float64',
        'scope': 'Agent02 only; no LLM/MAS project, web or V3 TEST replay',
        'market': asdict(MarketConfig()), 'controlled_configs': configs, 'train_seeds': seeds,
        'training_runs': runs,
        'budget': {'train_episodes': 5000, 'steps_per_episode': 20,
                   'final_evaluation_episodes_per_role': 500, 'declared_market_runs': 56,
                   'declared_train_market_steps': 5600000, 'declared_learner_instances': 61,
                   'minimum_free_disk_bytes': 5 * 1024**3, 'trace_rows_per_run': 20,
                   'checkpoint_interval_episodes': 100, 'maximum_parallel_train_writers': 1},
        'rng': {'controlled_training': 'PCG64 SeedSequence([train_seed, channel]); channels demand=0,sales=1,2,policy=3',
                'policy_seed_derivation': 'int(SeedSequence([seed,3]).generate_state(1)[0])',
                'reference': 'Original single env RNG seed; action RNG seed+10000; reference code unchanged',
                'tapes': 'PCG64 SeedSequence([scenario_seed,episode,channel]); demand=0,customer_uniforms=1',
                'evaluation_ties': 'PCG64 int(SeedSequence([scenario_seed,4]).generate_state(1)[0])',
                'near_ties': {'rule': 'random among np.isclose to max', 'rtol': 1e-5, 'atol': 1e-8},
                'tape_sampling': 'Count independent uniforms < conversion for N customers; Binomial marginal'},
        'evaluation': {'roles': [0, 1], 'development_scenario_seeds': [1000000+s for s in seeds],
                       'final_scenario_seeds': [2000000+s for s in seeds],
                       'reference_native_final_seed': 500042, 'reference_native_final_phase': 5,
                       'final_evaluation_authorized_in_phase2': False, 'final_gate_phase': 5,
                       'future_variant_gate_phase': 6, 'future_improved_gate_phase': 7,
                       'fixed_opponent': 'Original rule; rule-vs-rule and no-discount diagnostics',
                       'paired_scenarios': 'Same scenario seed and episode tape across configs; both physical roles',
                       'frozen': 'Copy Q read-only, no learn, explore=False; verify source Q hash and RNG unchanged',
                       'aggregation': 'mean and sample std(ddof=1) across 5 training seeds after averaging roles',
                       'uncertainty': 'Report seed-level paired deltas; if CI used, resample seed pairs, not steps',
                       'selection': 'Report all preregistered configs; never tune/select on final results',
                       'journal_key': '(study_id,policy_sha256,scenario_spec_sha256,role); reuse identical saved output',
                       'recovery': 'Retain failed/partial claims; investigate/version, do not silently replay final'},
        'future_variants': {
            'persistent': {'kernel': [[.9, .1], [.1, .9]], 'initial_demand': 'Bernoulli(0.5)'},
            'gold': {'calibration_status': 'deferred_to_phase6', 'last_allowed_month': cutoff,
                     'source_path': 'data/raw/ch4/gold/CMO-Historical-Data-Monthly.xlsx',
                     'source_sha256': 'ea1c350827878ea3bbe30e3cda16a13fd3bd5b409b8458940dc94a36b5a33154',
                     'parent_split_path': str(split_path.relative_to(BASE.parent)),
                     'parent_split_sha256': sha256_file(split_path),
                     'regime': '1 if gold[t] > gold[t-1] else 0; consecutive observed calendar months only',
                     'transition_estimator': '(count_ij+1)/(sum_j count_ij+2)',
                     'smoothing_pseudocount': 1, 'initial_demand': 'Bernoulli(0.5)',
                     'missing_policy': 'Do not impute or bridge a missing month; record exclusions',
                     'real_demand_measurement': False, 'interpretation': 'synthetic demand proxy, not causality or investment'}},
        'improved_design': {'implementation_phase': 7, 'state': ['demand', 'own_previous', 'competitor_previous',
                                                              'remaining_steps'],
                            'q_entries': 320, 'remaining_steps': '1..20, zero future value at terminal',
                            'learning_parameters': asdict(default), 'reward': 'unchanged profit',
                            'oracle': 'optional exact finite-horizon known-model/fixed-rule check, never train labels'},
        'smoke': {'episodes_per_track': 100, 'steps_per_episode': 20, 'reference_seed': 730042,
                  'controlled_seed': 730011, 'development_scenario_seed': 1730011,
                  'development_episodes_per_role': 3, 'use_as_report_results': False},
        'outputs_per_run': ['manifest.json', 'episode_rewards.csv', 'checkpoint_eNNNNNN.json',
                            'q_table.json', 'policy.json', 'visits.json', 'trace_sample.json'],
        'figure_policy': {'format': 'black/grayscale', 'moving_average_episodes': 100,
                          'interpretation_notes_required': True, 'notes_template': 'docs/figure_explanation_template.md',
                          'required_notes': ['purpose', 'data_source', 'axes_and_units', 'legend', 'aggregation_and_n',
                                             'observations', 'quantitative_comparison', 'limitations']},
        'test_plan': ['8 state-action pairs and 4 simultaneous joint actions', 'all rule branches and reward margins',
                      'Q=4.65 calculation, terminal update, epsilon/ties', 'independent demand/sales/policy RNG',
                      'frozen DEV evaluation and forbidden final CLI', 'resume/logging exact parity',
                      'hash/source/disk/path guards and unchanged Phase1/V3 inputs'],
    }
