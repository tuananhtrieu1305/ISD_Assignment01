"""Select the preregistered 5x5 matrix and preserve the original baseline claim."""

from dataclasses import asdict

from .baseline_runs import execute_run, verify_run
from .controlled import LearningConfig, MarketConfig
from .sweep_analysis import CONFIG_IDS, validate_factors
from .training import digest

BASELINE_ID = 'controlled/iid/baseline/s0011'


def select_specs(protocol):
    validate_factors(protocol)
    specs = [row for row in protocol['training_runs'] if row['track'] == 'CONTROLLED'
             and row['kernel_id'] == 'iid' and row['config_id'] in CONFIG_IDS]
    seeds = [11, 22, 33, 44, 55]
    expected = {(name, seed) for name in CONFIG_IDS for seed in seeds}
    actual = {(row['config_id'], row['seed']) for row in specs}
    if len(specs) != 25 or actual != expected or len({row['run_id'] for row in specs}) != 25:
        raise ValueError('Incomplete, duplicate or foreign core matrix cell')
    for row in specs:
        canonical = f'controlled/iid/{row["config_id"]}/s{row["seed"]:04d}'
        if (row['run_id'] != canonical or row['learners'] != 1
                or row['phase'] != (3 if canonical == BASELINE_ID else 4)):
            raise ValueError('Core cell identity or phase differs from registration')
    return sorted(specs, key=lambda row: (CONFIG_IDS.index(row['config_id']), row['seed']))


def train_one(base, spec, protocol, declaration_sha256, baseline_declaration_sha256, *, resume=False):
    market = MarketConfig(**protocol['market'])
    learning = LearningConfig(**protocol['controlled_configs'][spec['config_id']])
    reused = spec['run_id'] == BASELINE_ID
    if reused:
        result = verify_run(base, BASELINE_ID)
        registration = {'spec': spec, 'market': asdict(market), 'learning': asdict(learning),
                        'declaration_sha256': baseline_declaration_sha256}
        if result['registration_sha256'] != digest(registration):
            raise ValueError('Original Phase3 baseline registration changed')
    else:
        result = execute_run(base, spec, market, learning, declaration_sha256, resume=resume, interval=100)
    return {**result, 'reused_from_phase3': reused,
            'source_declaration_sha256': baseline_declaration_sha256 if reused else declaration_sha256}
